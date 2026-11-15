#!/usr/bin/env python3
"""CartoonForge's small procedural narration/music mixer (48 kHz stereo)."""
import json, sys
from pathlib import Path
import numpy as np
from scipy import signal
from scipy.io import wavfile

project = Path(sys.argv[1])
data = project / "data"
SR = 48000
cues_doc = json.loads((data / "cues.json").read_text())
script = json.loads((project / "script.json").read_text())
duration = float(cues_doc.get("duration", 34.0))
n = int(duration * SR) + SR // 10
t = np.arange(n) / SR

def lowpass(x, hz):
    b, a = signal.butter(2, hz / (SR / 2), "low")
    return signal.lfilter(b, a, x)

def envelope(length, attack=0.005, release=5):
    e = np.ones(length)
    na = max(1, int(attack * SR))
    e[:na] = np.linspace(0, 1, na)
    if length > na:
        e[na:] = np.exp(-np.linspace(0, release, length - na))
    return e

def tone_sweep(f0, f1, seconds):
    tt = np.arange(int(seconds * SR)) / SR
    freq = f0 * (f1 / f0) ** (tt / seconds)
    return np.sin(2 * np.pi * np.cumsum(freq) / SR)

def effect(kind, seconds=0.38):
    rng = np.random.default_rng(91 + len(kind))
    count = max(1, int(seconds * SR))
    if kind == "pop":
        return lowpass(tone_sweep(560, 240, 0.11) * envelope(int(0.11 * SR), .002, 6), 3000) * .7
    if kind == "shimmer":
        out = np.zeros(int(1.2 * SR))
        for i, f in enumerate([1568, 1976, 2349, 3136]):
            start = int(i * .9 / 4 * SR)
            tone = np.sin(2*np.pi*f*np.arange(int(.35*SR))/SR) * envelope(int(.35*SR), .01, 7) * .2
            out[start:start+len(tone)] += tone
        return lowpass(out, 9000)
    noise = rng.standard_normal(count)
    k = np.sin(np.pi * np.linspace(0, 1, count))
    return lowpass(noise, 1800) * k**1.5 * .18

# Voice track, resampled and normalised without clipping.
sr, raw = wavfile.read(data / "narration.wav")
raw = raw.astype(np.float64) / (32768.0 if raw.dtype == np.int16 else 1.0)
if raw.ndim > 1:
    raw = raw.mean(axis=1)
if sr != SR:
    raw = signal.resample_poly(raw, SR, sr)
voice = np.zeros(n)
voice[:min(n, len(raw))] = raw[:min(n, len(raw))]
voice *= .82 / (np.max(np.abs(voice)) + 1e-9)

# Restrained low-frequency tension bed, automatically ducked beneath speech.
music_name = script.get("music", "tension")
music = np.zeros(n)
if music_name == "tension":
    pulse = .5 + .5*np.sin(2*np.pi*t/3.2)
    music = (.11*np.sin(2*np.pi*55*t) + .044*np.sin(2*np.pi*82.5*t+1.3)
             + .0165*np.sin(2*np.pi*110*t+.4))
    music += .025*np.sin(2*np.pi*58*t) * (np.sin(2*np.pi*t/3.2) > .94)
    music = lowpass(music * pulse, 400)
elif music_name == "bed":
    music = .025*np.sin(2*np.pi*130*t) + .015*np.sin(2*np.pi*196*t)
    music = lowpass(music, 3200)
hop = int(.05*SR)
frames = n//hop
rms = np.sqrt(np.mean(voice[:frames*hop].reshape(frames,hop)**2,axis=1))
duck = np.clip(1-rms/.05,.18,1.0)
music *= np.interp(np.arange(n),np.arange(frames)*hop,duck)

fx = np.zeros(n)
for cue in cues_doc.get("cues", []):
    snd = effect(cue.get("type","whoosh"), float(cue.get("dur",.38)))
    start = int(float(cue.get("t",0))*SR)
    gain = 10**(float(cue.get("gain",-18))/20)
    if cue.get("soft",False):
        gain *= .55
    end = min(n,start+len(snd))
    if start < n and end > start:
        fx[start:end] += snd[:end-start]*gain

mix = np.tanh((voice+music+fx)*1.1)
fade = int(1.2*SR)
mix[-fade:] *= np.linspace(1,0,fade)
stereo = np.stack([mix,mix],axis=1)
wavfile.write(data/"mix.wav",SR,(np.clip(stereo,-1,1)*32767).astype(np.int16))
print(f"data/mix.wav: {duration:.2f}s, 48 kHz stereo, voice + {music_name} bed + {len(cues_doc.get('cues',[]))} cues")
