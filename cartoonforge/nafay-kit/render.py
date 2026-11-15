#!/usr/bin/env python3
"""Render a Nafay-style animation to MP4 with headless Chrome + ffmpeg, frame by frame.

  python3 scripts/render.py animation.html out.mp4 [options]
  python3 scripts/render.py --project ~/faceless-shorts/<name> out.mp4 [options]

The HTML must expose window.seek(t), window.DURATION and a <canvas> (every Nafay 3D Style Library
file does); audio comes from SFX.render(window.scoreSound, window.DURATION, 48000, {voiceover}) when
present, or from data/mix.wav in --project mode.

Options: --fps 30 · --scale 0.6 (output downscale) · --chrome /path/to/chrome · --vo narration.wav
(mix the style's SFX, ducked, under your voiceover) · --sheet out.jpg 0.5 (contact sheet, a frame
every 0.5 s, time-stamped) · --start 2 --end 10 (render a slice).
"""
import argparse, base64, hashlib, json, os, random, socket, struct, subprocess, sys, tempfile, time
from pathlib import Path

SR = 48000
CHROME_PATHS = [
    os.environ.get('CHROME'),
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
    '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable', '/usr/bin/chromium', '/usr/bin/chromium-browser',
    '/snap/bin/chromium', 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
]


def find_chrome(override):
    for p in [override] + CHROME_PATHS:
        if p and Path(p).exists():
            return p
    sys.exit('Chrome not found: install Google Chrome or pass --chrome /path/to/chrome')


class WS:
    def __init__(self, host, port, path):
        self.s = socket.create_connection((host, port), timeout=120)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f'GET {path} HTTP/1.1\r\nHost: {host}:{port}\r\nUpgrade: websocket\r\n'
                        f'Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n'
                        f'\r\n').encode())
        resp = b''
        while b'\r\n\r\n' not in resp:
            resp += self.s.recv(4096)
        head = resp.split(b'\r\n\r\n', 1)[0].decode(errors='replace')
        if '101' not in head.split('\r\n')[0]:
            sys.exit(f'websocket handshake failed:\n{head}')
        accept = base64.b64encode(hashlib.sha1((key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()).decode()
        if accept not in head:
            sys.exit('websocket handshake key mismatch')
        self.buf = resp.split(b'\r\n\r\n', 1)[1]

    def _recv(self, n):
        while len(self.buf) < n:
            chunk = self.s.recv(65536)
            if not chunk:
                raise EOFError('socket closed')
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def _frame(self, opcode, payload):
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        header = bytes([0x80 | opcode])
        n = len(payload)
        if n < 126:
            header += bytes([0x80 | n])
        elif n < 65536:
            header += bytes([0x80 | 126]) + struct.pack('>H', n)
        else:
            header += bytes([0x80 | 127]) + struct.pack('>Q', n)
        return header + mask + masked

    def send_text(self, text):
        self.s.sendall(self._frame(0x1, text.encode()))

    def recv_msg(self):
        out = b''
        while True:
            b1, b2 = self._recv(2)
            opcode = b1 & 0x0F
            ln = b2 & 0x7F
            if ln == 126:
                ln = struct.unpack('>H', self._recv(2))[0]
            elif ln == 127:
                ln = struct.unpack('>Q', self._recv(8))[0]
            payload = self._recv(ln) if ln else b''
            if opcode == 0x9:
                self.s.sendall(self._frame(0xA, payload))
                continue
            if opcode == 0x8:
                raise EOFError('websocket closed by peer')
            if opcode in (0x1, 0x2, 0x0):
                out += payload
                if b1 & 0x80:
                    return out.decode(errors='replace')
                continue
            if opcode == 0xA:
                continue


class Page:
    def __init__(self, chrome, url):
        prof = tempfile.mkdtemp(prefix='nafay-chrome-')
        self.chrome = subprocess.Popen(
            [chrome, '--headless=new', '--remote-debugging-port=0', f'--user-data-dir={prof}', '--no-first-run',
             '--no-default-browser-check', '--hide-scrollbars', '--window-size=1080,1920', '--ignore-gpu-blocklist',
             '--enable-unsafe-swiftshader', '--use-angle=swiftshader', '--disable-background-timer-throttling',
             '--disable-renderer-backgrounding', *( ['--no-sandbox'] if os.getuid() == 0 else [] ), 'about:blank'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        port = None
        for _ in range(200):
            try:
                port = (Path(prof) / 'DevToolsActivePort').read_text().split('\n')[0].strip()
                if port:
                    break
            except OSError:
                pass
            time.sleep(0.1)
        if not port:
            self.close()
            sys.exit('Chrome did not start (no DevToolsActivePort)')
        r = subprocess.run(['curl', '-s', '-X', 'PUT', f'http://127.0.0.1:{port}/json/new?{url}'],
                           capture_output=True, text=True)
        try:
            target = json.loads(r.stdout)
        except json.JSONDecodeError:
            r = subprocess.run(['curl', '-s', f'http://127.0.0.1:{port}/json/new?{url}'], capture_output=True, text=True)
            target = json.loads(r.stdout)
        self.ws = WS('127.0.0.1', int(port), target['webSocketDebuggerUrl'].split('localhost', 1)[1])
        self.id = 0
        self.errors = []

    def ev(self, expr):
        self.id += 1
        self.ws.send_text(json.dumps({'id': self.id, 'method': 'Runtime.evaluate',
                                      'params': {'expression': expr, 'returnByValue': True, 'awaitPromise': True}}))
        while True:
            m = json.loads(self.ws.recv_msg())
            if m.get('id') != self.id:
                if m.get('method') == 'Runtime.exceptionThrown':
                    self.errors.append(str(m['params'].get('exceptionDetails', {}).get('exception', '')))
                continue
            if 'error' in m:
                raise RuntimeError(m['error'].get('message', 'CDP error'))
            r = m['result'].get('result', {})
            if r.get('subtype') == 'error' or 'exceptionDetails' in m['result']:
                raise RuntimeError(str(m['result'].get('exceptionDetails', {}).get('exception', r)))
            return r.get('value')

    def wait_ready(self, timeout=120):
        t0 = time.time()
        while time.time() - t0 < timeout:
            st = self.ev('(() => { try { if (window.OP && OP.bootError) return "ERR:" + OP.bootError; '
                         'if (window.OP && OP.ready === true) return true; '
                         'if (typeof window.seek === "function" && typeof window.DURATION === "number" '
                         '&& document.querySelector("canvas")) return true; return false; } catch (e) { return "ERR:" + e; } })()')
            if st is True:
                return
            if isinstance(st, str) and st.startswith('ERR'):
                self.close()
                sys.exit('boot failed: ' + st[4:] + ('\n' + '\n'.join(self.errors) if self.errors else ''))
            time.sleep(0.2)
        self.close()
        sys.exit('boot timeout' + (('\n' + '\n'.join(self.errors)) if self.errors else ''))

    def close(self):
        try:
            self.ws.s.close()
        except Exception:
            pass
        self.chrome.kill()


SEEK_FRAME = ("(async () => {{ window.seek({t}); const c = document.querySelector('canvas'); "
              "return c.toDataURL('image/jpeg', 0.92); }})()")


def seek_frame(page, t):
    data = page.ev(SEEK_FRAME.format(t=t))
    return base64.b64decode(data.split(',', 1)[1])


SEEK_LABELED = ("(async () => {{ window.seek({t}); const c = document.querySelector('canvas'); const x = c.getContext('2d'); "
                "x.setTransform(1,0,0,1,0,0); x.fillStyle = '#000'; x.fillRect(0, 0, 220, 80); x.fillStyle = '#fff'; "
                "x.font = '700 54px sans-serif'; x.fillText('{ts}', 14, 60); return c.toDataURL('image/jpeg', 0.8); }})()")


def ffmpeg_video(out, fps, scale, audio):
    cmd = ['ffmpeg', '-y', '-v', 'error', '-f', 'image2pipe', '-framerate', str(fps), '-i', '-']
    if audio:
        cmd += ['-i', audio]
    vf = f'scale=iw*{scale}:ih*{scale}' if scale != 1 else 'null'
    cmd += (['-vf', vf, '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', '-r', str(fps)]
            + (['-c:a', 'aac', '-b:a', '160k', '-shortest'] if audio else []) + [str(out)])
    return subprocess.Popen(cmd, stdin=subprocess.PIPE)


def render_audio(page, vo_file):
    try:
        floats = page.ev('SFX.render(window.scoreSound, window.DURATION, 48000, { voiceover: %s })' % ('true' if vo_file else 'false'))
    except Exception as e:
        print(f'SFX.render unavailable ({e}); rendering video without the style soundtrack')
        return None
    if not floats or not isinstance(floats, list):
        return None
    import numpy as np
    x = np.array(floats, dtype=np.float32).reshape(-1, 2)
    if vo_file:
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(vo_file), '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                             capture_output=True, check=True).stdout
        vo = np.frombuffer(raw, dtype=np.float32).astype(np.float64)
        vo = vo / (np.abs(vo).max() + 1e-9) * 0.9
        n = max(len(x), len(vo))
        xx = np.zeros((n, 2)); xx[:len(x)] = x
        xx[:len(vo), 0] += vo; xx[:len(vo), 1] += vo
        x = np.clip(xx, -1, 1)
    tmp = Path(tempfile.mkstemp(suffix='.wav')[1])
    import wave
    with wave.open(str(tmp), 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes())
    return tmp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input', nargs='?', help='the animation .html, or omit with --project')
    ap.add_argument('output')
    ap.add_argument('--project')
    ap.add_argument('--fps', type=float, default=30)
    ap.add_argument('--scale', type=float, default=1.0)
    ap.add_argument('--chrome')
    ap.add_argument('--vo')
    ap.add_argument('--sheet', action='store_true')
    ap.add_argument('--step', type=float, default=0.5)
    ap.add_argument('--start', type=float, default=0)
    ap.add_argument('--end', type=float)
    a = ap.parse_args()

    if a.project:
        proj = Path(a.project)
        html = proj / 'index.html'
        mix = proj / 'data/mix.wav'
    else:
        if not a.input:
            ap.error('give an animation .html, or --project <folder>')
        html, mix = Path(a.input), None
    if not html.exists():
        sys.exit(f'not found: {html}')

    chrome = find_chrome(a.chrome)
    url = html.resolve().as_uri() + ('?capture=1' if a.project else '')
    page = Page(chrome, url)
    try:
        page.wait_ready()
        dur = page.ev('window.DURATION')
        end = min(a.end if a.end is not None else dur, dur)
        print(f'DURATION {dur:.2f} s, rendering {a.start:.2f}-{end:.2f} at {a.fps:g} fps')
        if a.sheet:
            times = [a.start + k * a.step for k in range(int((end - a.start) / a.step) + 1)]
            frames = Path(tempfile.mkdtemp(prefix='nafay-sheet-'))
            for i, t in enumerate(times):
                jpeg = base64.b64decode(page.ev(SEEK_LABELED.format(t=t, ts=f'{t:05.2f}')).split(',', 1)[1])
                (frames / f'{i:04d}.jpg').write_bytes(jpeg)
                print(f'  {t:6.2f} s', flush=True)
            cols = 6
            rows = (len(times) + cols - 1) // cols
            subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', '1', '-i', str(frames / '%04d.jpg'),
                            '-vf', f'scale=270:-1,tile={cols}x{rows}', str(a.output)], check=True)
            print(f'{a.output} ({len(times)} frames, one every {a.step} s)')
            return
        audio = str(mix) if (mix and mix.exists()) else render_audio(page, a.vo)
        proc = ffmpeg_video(a.output, a.fps, a.scale, audio)
        n = int((end - a.start) * a.fps)
        for i in range(n + 1):
            t = a.start + i / a.fps
            proc.stdin.write(seek_frame(page, t))
            if i % max(1, a.fps) == 0:
                print(f'  {t:6.2f} / {end:.2f} s', flush=True)
        proc.stdin.close()
        if proc.wait() != 0:
            sys.exit('ffmpeg failed')
        print(f'{a.output} ({n + 1} frames, {end - a.start:.2f} s' + (', with audio' if audio else '') + ')')
    finally:
        page.close()


if __name__ == '__main__':
    main()
