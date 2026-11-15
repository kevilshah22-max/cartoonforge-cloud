#!/usr/bin/env python3
"""Create a deterministic, narration-synchronised 3D-look blood-science animation."""
import json, subprocess, sys
from pathlib import Path
from html import escape

def main():
    project = Path(sys.argv[1])
    out = Path(sys.argv[2])
    lines_raw = json.loads((project / "data/lines.json").read_text())
    words_raw = json.loads((project / "data/words.json").read_text())
    lines = lines_raw if isinstance(lines_raw, list) else next(
        (lines_raw.get(k) for k in ("lines", "segments", "items", "data") if isinstance(lines_raw.get(k), list)), [])
    words = words_raw if isinstance(words_raw, list) else next(
        (words_raw.get(k) for k in ("words", "segments", "items", "data") if isinstance(words_raw.get(k), list)), [])
    duration = float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(project / "data/narration.wav")
    ], text=True).strip())
    payload = json.dumps({"lines": lines, "words": words}, ensure_ascii=False).replace("</", "<\\/")
    html = r"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=720, initial-scale=1"><title>CartoonForge — Veins and light</title>
<style>
*{box-sizing:border-box}html,body{margin:0;width:720px;height:1280px;overflow:hidden;background:#10070d}canvas{display:block;width:720px;height:1280px}
</style></head><body><canvas id="c" width="720" height="1280"></canvas><script>
const DURATION=__DURATION__, DATA=__DATA__;
const canvas=document.getElementById('c'),ctx=canvas.getContext('2d');
window.DURATION=DURATION;let now=0;
const rnd=(n)=>{let x=Math.sin(n*127.1+311.7)*43758.5453;return x-Math.floor(x)};
function grad(x,y,r,c1,c2){let g=ctx.createRadialGradient(x-r*.3,y-r*.35,r*.03,x,y,r);g.addColorStop(0,c1);g.addColorStop(1,c2);return g}
function cell(x,y,s,rot,alpha=1){ctx.save();ctx.translate(x,y);ctx.rotate(rot);ctx.globalAlpha=alpha;ctx.scale(s,s*.78);
ctx.shadowColor='#ff263d';ctx.shadowBlur=24;ctx.fillStyle=grad(-13,-18,82,'#ffd0c9','#a91530');ctx.beginPath();ctx.ellipse(0,0,59,39,0,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;
let d=ctx.createRadialGradient(-2,-1,2,0,0,34);d.addColorStop(0,'#781126');d.addColorStop(.48,'#b72a43');d.addColorStop(1,'rgba(255,170,174,.06)');
ctx.fillStyle=d;ctx.beginPath();ctx.ellipse(0,0,31,19,0,0,Math.PI*2);ctx.fill();
ctx.strokeStyle='rgba(255,225,218,.7)';ctx.lineWidth=2.2;ctx.beginPath();ctx.ellipse(0,0,56,36,0,0,Math.PI*2);ctx.stroke();
ctx.strokeStyle='rgba(255,235,226,.36)';ctx.lineWidth=3;ctx.beginPath();ctx.ellipse(-7,-12,25,9,-.16,Math.PI*1.08,Math.PI*1.88);ctx.stroke();
ctx.restore()}
function text(str,x,y,size,color='#fff',align='center'){ctx.textAlign=align;ctx.font='700 '+size+'px Arial';ctx.fillStyle=color;ctx.shadowColor='#000';ctx.shadowBlur=12;ctx.fillText(str,x,y);ctx.shadowBlur=0}
function background(t){let g=ctx.createLinearGradient(0,0,720,1280);g.addColorStop(0,'#250710');g.addColorStop(.5,'#520b19');g.addColorStop(1,'#17070f');ctx.fillStyle=g;ctx.fillRect(0,0,720,1280);
ctx.globalAlpha=.17;for(let i=0;i<18;i++){let x=rnd(i)*720,y=(rnd(i+30)*1280+t*22)%1280;ctx.fillStyle='#ff5365';ctx.beginPath();ctx.arc(x,y,2+rnd(i+8)*5,0,7);ctx.fill()}ctx.globalAlpha=1}
function vessel(t){ctx.save();ctx.translate(360,620);ctx.rotate(Math.sin(t*.16)*.025);let g=ctx.createLinearGradient(-270,0,270,0);g.addColorStop(0,'#5b0716');g.addColorStop(.5,'#a20d27');g.addColorStop(1,'#4a0714');ctx.fillStyle=g;ctx.beginPath();ctx.moveTo(-290,-600);ctx.bezierCurveTo(-210,-250,-220,250,-300,650);ctx.lineTo(300,650);ctx.bezierCurveTo(220,250,210,-250,290,-600);ctx.closePath();ctx.fill();ctx.strokeStyle='rgba(255,130,150,.28)';ctx.lineWidth=10;ctx.stroke();ctx.restore()}
function draw(t){now=Math.max(0,Math.min(DURATION,t));background(now);vessel(now);
for(let i=0;i<18;i++){let y=((i*137+now*95)%1500)-100,x=130+rnd(i)*460+Math.sin(now*.7+i)*34;let s=.34+rnd(i+9)*.42;cell(x,y,s,Math.sin(now+i)*.2,.3+rnd(i+4)*.35)}
const p=now/DURATION;
if(p<.2){text('YOUR VEINS LOOK BLUE',360,155,39);text('BUT YOUR BLOOD IS RED',360,207,31,'#ff9b9f');cell(360,650,2.15,Math.sin(now)*.12);text('A closer look inside the body',360,1080,24,'#ffd4d7')}
else if(p<.43){text('MEET HAEMOGLOBIN',360,150,40);cell(360,630,2.25,Math.sin(now)*.1);for(let i=0;i<4;i++){let a=now*.8+i*Math.PI/2;ctx.fillStyle='#ffb3a9';ctx.beginPath();ctx.arc(360+Math.cos(a)*190,630+Math.sin(a)*130,13,0,7);ctx.fill()}text('The protein inside red blood cells',360,1080,25,'#ffd4d7')}
else if(p<.65){text('OXYGEN CHANGES THE SHADE',360,150,34);cell(360,650,2.05,Math.sin(now)*.1);for(let i=0;i<5;i++){let x=100+((i*127+now*70)%520),y=390+Math.sin(now+i)*180;ctx.fillStyle='#83d9ff';ctx.shadowColor='#83d9ff';ctx.shadowBlur=25;ctx.beginPath();ctx.arc(x,y,12,0,7);ctx.fill();ctx.shadowBlur=0}text('Oxygen-rich: brighter red',360,1080,27,'#fff')}
else if(p<.83){text('SO WHY DO VEINS LOOK BLUE?',360,150,34);ctx.fillStyle='#d991a0';ctx.fillRect(70,450,580,280);ctx.fillStyle='#f1b4bc';ctx.fillRect(70,450,580,85);for(let i=0;i<7;i++){ctx.strokeStyle=i%2?'#4b9fd3':'#ffb85e';ctx.lineWidth=5;ctx.beginPath();ctx.moveTo(120+i*75,280);ctx.lineTo(180+i*58,460);ctx.stroke()}cell(360,650,1.15,0);text('Light is absorbed and scattered',360,1080,26,'#fff')}
else{ text('THE REAL TRICK IS LIGHT',360,150,38);for(let i=0;i<8;i++){let x=100+i*75;ctx.strokeStyle=i%2?'#7ed5ff':'#ffbf70';ctx.lineWidth=4;ctx.beginPath();ctx.moveTo(x,350);ctx.lineTo(x+Math.sin(now+i)*25,850);ctx.stroke()}cell(360,650,1.6,0);text('The blood inside is still red.',360,1080,30,'#fff')}
const active=(DATA.lines||[]).find(v=>now>=Number(v.start||v.start_time||0)&&now<=Number(v.end||v.end_time||0));
if(active){
 let cap=String(active.text||active.line||'').trim(), words=cap.split(/\\s+/), rows=[], row='';
 for(const w of words){const test=(row+' '+w).trim();if(test.length>43&&row){rows.push(row);row=w}else row=test}
 if(row)rows.push(row);rows=rows.slice(0,3);
 const boxH=rows.length*30+34, top=1208-boxH;
 ctx.fillStyle='rgba(8,3,8,.78)';ctx.fillRect(28,top,664,boxH);
 rows.forEach((line,i)=>text(line,360,top+30+i*30,21,'#fff'));
}
ctx.fillStyle='rgba(255,255,255,.65)';ctx.fillRect(34,1247,652,4);ctx.fillStyle='#ff7184';ctx.fillRect(34,1247,652*now/DURATION,4);
}
window.seek=(t)=>{draw(t);return true};window.scoreSound=[];window.SFX={render:()=>[]};draw(0);
</script></body></html>"""
    html = html.replace("__DURATION__", str(duration)).replace("__DATA__", payload)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    print(f"Generated topic-specific animated scene timeline: {duration:.2f}s")
if __name__ == "__main__":
    main()
