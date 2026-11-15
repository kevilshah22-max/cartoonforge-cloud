#!/usr/bin/env python3
"""Generate a scene-led Bio Glow explainer with distinct scientific compositions."""
import json, subprocess, sys
from pathlib import Path

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
    html = r"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=720, initial-scale=1"><title>CartoonForge Bio Glow — Why veins look blue</title>
<style>*{box-sizing:border-box}html,body{margin:0;width:720px;height:1280px;overflow:hidden;background:#090b18}canvas{display:block;width:720px;height:1280px}</style></head><body>
<canvas id="c" width="1080" height="1920"></canvas><script>
const DURATION=__DURATION__, DATA=__DATA__;
const c=document.getElementById('c'),x=c.getContext('2d');window.DURATION=DURATION;
const TAU=Math.PI*2, clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const rnd=n=>{let z=Math.sin(n*127.1+311.7)*43758.5453;return z-Math.floor(z)};
function radial(px,py,r,stops){let g=x.createRadialGradient(px-r*.28,py-r*.35,r*.02,px,py,r);stops.forEach((s,i)=>g.addColorStop(i/(stops.length-1),s));return g}
function glow(px,py,r,color,alpha=1){x.save();x.globalAlpha=alpha;x.shadowColor=color;x.shadowBlur=r*.7;x.fillStyle=color;x.beginPath();x.arc(px,py,r,0,TAU);x.fill();x.restore()}
function sphere(px,py,r,base,light){x.save();x.fillStyle=radial(px,py,r,[light,base,'#160a20']);x.shadowColor=base;x.shadowBlur=r*.28;x.beginPath();x.arc(px,py,r,0,TAU);x.fill();x.shadowBlur=0;x.strokeStyle='rgba(255,255,255,.26)';x.lineWidth=Math.max(2,r*.035);x.beginPath();x.arc(px-r*.12,py-r*.12,r*.76,Math.PI*1.12,Math.PI*1.78);x.stroke();x.restore()}
function rbc(px,py,r,angle=0,alpha=1){x.save();x.translate(px,py);x.rotate(angle);x.globalAlpha=alpha;
x.shadowColor='#ff345f';x.shadowBlur=r*.35;x.fillStyle=radial(-r*.18,-r*.25,r*1.35,['#ffe0d7','#f57c8b','#b91f46','#54102b']);x.beginPath();x.ellipse(0,0,r,r*.68,0,0,TAU);x.fill();x.shadowBlur=0;
x.fillStyle=radial(0,0,r*.8,['#5b102a','#9f2140','#d95b70']);x.beginPath();x.ellipse(0,0,r*.47,r*.28,0,0,TAU);x.fill();
x.strokeStyle='rgba(255,231,220,.78)';x.lineWidth=Math.max(2,r*.045);x.beginPath();x.ellipse(0,0,r*.94,r*.62,0,Math.PI*1.05,Math.PI*1.92);x.stroke();
x.strokeStyle='rgba(255,255,255,.32)';x.lineWidth=Math.max(2,r*.035);x.beginPath();x.ellipse(-r*.12,-r*.2,r*.38,r*.12,-.12,Math.PI*1.08,Math.PI*1.8);x.stroke();x.restore()}
function bg(top,bottom,stars=true,t=0){let g=x.createLinearGradient(0,0,1080,1920);g.addColorStop(0,top);g.addColorStop(1,bottom);x.fillStyle=g;x.fillRect(0,0,1080,1920);
if(stars){for(let i=0;i<45;i++){let px=rnd(i+10)*1080,py=(rnd(i+70)*1920+t*(10+rnd(i)*20))%1920;x.globalAlpha=.12+rnd(i+3)*.22;x.fillStyle=i%3?'#ff8b9e':'#7cdbff';x.beginPath();x.arc(px,py,2+rnd(i+5)*4,0,TAU);x.fill()}x.globalAlpha=1}}
function label(kicker,headline,sub){x.textAlign='center';x.shadowColor='#05020b';x.shadowBlur=18;x.fillStyle='#ff9eae';x.font='700 27px Arial';x.fillText(kicker.toUpperCase(),540,155);x.fillStyle='#fff7f6';x.font='800 49px Arial';x.fillText(headline,540,222);x.shadowBlur=0;if(sub){x.fillStyle='rgba(255,229,233,.82)';x.font='500 27px Arial';x.fillText(sub,540,270)}}
function pill(txt,px,py,color='#ff8c9f'){x.save();x.font='700 25px Arial';let w=x.measureText(txt).width+44;x.fillStyle='rgba(12,7,20,.78)';x.strokeStyle=color;x.lineWidth=2;x.beginPath();x.roundRect(px-w/2,py-27,w,54,20);x.fill();x.stroke();x.fillStyle='#fff';x.textAlign='center';x.fillText(txt,px,py+8);x.restore()}
function pathGlow(points,color,width=8,alpha=.9){x.save();x.globalAlpha=alpha;x.strokeStyle=color;x.lineWidth=width;x.lineCap='round';x.lineJoin='round';x.shadowColor=color;x.shadowBlur=24;x.beginPath();points.forEach((p,i)=>i?x.lineTo(p[0],p[1]):x.moveTo(p[0],p[1]));x.stroke();x.restore()}
function sceneOne(t,u){
 bg('#10091e','#2b0a24',true,t);label('A visual mystery','Why do veins look blue?','The colour you see is not the colour of the blood');
 // Skin cross-section: layered translucent tissue
 x.save();x.shadowColor='#ff6e91';x.shadowBlur=50;
 let g=x.createLinearGradient(0,510,0,1350);g.addColorStop(0,'#f7b0a9');g.addColorStop(.35,'#d97886');g.addColorStop(1,'#78304f');
 x.fillStyle=g;x.beginPath();x.moveTo(0,650);for(let px=0;px<=1080;px+=90)x.lineTo(px,610+Math.sin(px*.009+t*.7)*24);x.lineTo(1080,1390);x.lineTo(0,1390);x.closePath();x.fill();x.restore();
 // Vessel embedded beneath the skin
 x.save();x.shadowColor='#ff234f';x.shadowBlur=45;x.fillStyle=radial(540,1170,230,['#f27b8d','#9d1740','#3b0926']);x.beginPath();x.ellipse(540,1160,360,150,0,0,TAU);x.fill();x.restore();
 for(let i=0;i<7;i++)rbc(260+i*105,1160+Math.sin(t*1.1+i)*24,39,.1*Math.sin(t+i),.95);
 // Surface light, with cool reflected scatter
 for(let i=0;i<5;i++){let sx=120+i*210;pathGlow([[sx,430],[sx+50,610],[sx+20,820]],i%2?'#8bdfff':'#ffd2a0',5,.5);glow(sx+20,820,8,'#a9e9ff',.7)}
 pill('Skin surface',540,570,'#ffd0ce');pill('Blood vessel below',540,1390,'#ff7b91');
}
function sceneTwo(t,u){
 bg('#080e23','#25102d',true,t);label('Inside a red blood cell','Meet haemoglobin','The oxygen-carrying protein');
 // Cinematic macro cell, tilted and floating
 x.save();x.translate(540,1000);x.rotate(-.16+Math.sin(t*.4)*.025);x.scale(1.35,1.1);
 rbc(0,0,300,-.08,1);x.restore();
 // Protein as four interlocking glossy globules, central iron site
 let cx=540,cy=1000,rr=128;
 [[-80,-58],[-5,-92],[78,-45],[25,43],[-73,52]].forEach((p,i)=>sphere(cx+p[0],cy+p[1],i===2?72:67,['#ff8d8b','#f56e93','#d84b8b','#ff9b74','#c9507c'][i],'#ffe0c6'));
 sphere(cx+8,cy-12,28,'#64dfff','#e2fbff');glow(cx+8,cy-12,12,'#9beeff',1);
 for(let i=0;i<9;i++){let a=t*.35+i*TAU/9,px=cx+Math.cos(a)*420,py=cy+Math.sin(a)*300;sphere(px,py,12,'#73d9ff','#e1fbff')}
 pill('Haemoglobin molecule',540,1435,'#ff9aaf');
}
function sceneThree(t,u){
 bg('#100a24','#310c28',true,t);label('Oxygen loading and release','Still red — two shades','Oxygen changes how bright red blood appears');
 // two floating RBCs side by side
 rbc(300,970,185,.08*Math.sin(t),1);rbc(780,970,185,-.08*Math.sin(t),1);
 // O2 particles approach left, drift away from right
 for(let i=0;i<8;i++){let a=t*1.1+i*TAU/8;let px=300+Math.cos(a)*280,py=970+Math.sin(a)*230;sphere(px,py,17,'#76dfff','#e8fcff');}
 for(let i=0;i<8;i++){let a=-t*.8+i*TAU/8;let px=780+Math.cos(a)*280,py=970+Math.sin(a)*230;sphere(px,py,15,'#76dfff','#e8fcff');}
 pill('Oxygen-rich · brighter red',300,1305,'#8bdfff');pill('After oxygen release · darker red',780,1305,'#ff879c');
 pathGlow([[500,970],[580,970]],'#f9c3d1',5,.7);textArrow(540,930);
}
function textArrow(px,py){x.save();x.strokeStyle='#fff0f4';x.lineWidth=5;x.beginPath();x.moveTo(px-18,py);x.lineTo(px+18,py);x.lineTo(px+5,py-13);x.moveTo(px+18,py);x.lineTo(px+5,py+13);x.stroke();x.restore()}
function sceneFour(t,u){
 bg('#071526','#12152e',true,t);label('The optical illusion','Light meets skin','Wavelengths are absorbed and scattered differently');
 // stacked tissue layers with a clear cross-section
 const layers=[['#f3b5ad',480,130],['#dc8b9b',610,180],['#ad5b7e',790,230],['#653052',1010,310]];
 layers.forEach((v,i)=>{let g=x.createLinearGradient(0,v[1],0,v[1]+v[2]);g.addColorStop(0,v[0]);g.addColorStop(1,['#d88891','#a85b7d','#71385f','#341b42'][i]);x.fillStyle=g;x.fillRect(0,v[1],1080,v[2]);});
 // vessel in deeper tissue
 x.save();x.shadowColor='#ff315d';x.shadowBlur=40;x.fillStyle=radial(540,1110,180,['#ff7889','#9d1c45','#4a102e']);x.beginPath();x.ellipse(540,1110,300,120,0,0,TAU);x.fill();x.restore();
 for(let i=0;i<5;i++)rbc(300+i*120,1110+Math.sin(t+i)*18,35,0,.85);
 // incident light and scattered/reflected rays
 for(let i=0;i<5;i++){let sx=190+i*170;pathGlow([[sx,280],[sx+35,520],[sx+70,740]],'#ffd18a',7,.75);pathGlow([[sx+70,740],[sx+15,570],[sx-35,470]],'#72d8ff',6,.8);glow(sx+70,740,12,'#a5eaff',.9)}
 pill('Light enters tissue',540,405,'#ffd18a');pill('Some light is scattered back',540,1395,'#78dfff');
}
function sceneFive(t,u){
 bg('#090c20','#260b29',true,t);label('The truth','Your blood is red','Blue veins are an optical effect — not blue blood');
 // elegant final hero composition: translucent skin above a bright vessel
 x.save();x.shadowColor='#ff91a4';x.shadowBlur=55;x.fillStyle=radial(540,820,520,['rgba(255,196,192,.95)','rgba(190,91,126,.85)','rgba(74,24,66,.92)']);x.beginPath();x.roundRect(115,430,850,790,120);x.fill();x.restore();
 // vessel runs diagonally with luminous walls
 pathGlow([[220,1100],[410,930],[620,970],[860,750]],'#ff526f',54,.5);
 pathGlow([[220,1100],[410,930],[620,970],[860,750]],'#ffb1b9',9,.85);
 for(let i=0;i<7;i++){let u2=(i/6+((t*.12)%1))%1,px=220+u2*640,py=1100-u2*350+Math.sin(u2*7)*80;rbc(px,py,46,.2,1)}
 // cool reflected light above the red vessel
 for(let i=0;i<8;i++){let px=170+i*105,py=600+Math.sin(t*.7+i)*90;pathGlow([[px,470],[px+20,py],[px+35,py+70]],'#79dfff',4,.55)}
 pill('Blood: always red',540,1390,'#ff8b9f');
}
function draw(t){
 t=clamp(t,0,DURATION);let p=t/DURATION;x.setTransform(1,0,0,1,0,0);
 const scene=p<.19?0:p<.42?1:p<.62?2:p<.83?3:4;
 const start=[0,.19,.42,.62,.83][scene],end=[.19,.42,.62,.83,1][scene],u=clamp((p-start)/(end-start),0,1);
 x.save();let zoom=1+.025*Math.sin(u*Math.PI);x.translate(540,960);x.scale(zoom,zoom);x.translate(-540,-960);
 [sceneOne,sceneTwo,sceneThree,sceneFour,sceneFive][scene](t,u);x.restore();
 // restrained word-by-word karaoke in a dedicated safe band
 const all=Array.isArray(DATA.words)?DATA.words:[];
 const active=all.findIndex(w=>t>=Number(w.s??w.start??0)&&t<=Number(w.e??w.end??0));
 if(active>=0){
  const cur=all[active],group=all.filter(w=>Number(w.line)===Number(cur.line));
  const wi=group.findIndex(w=>w===cur),chunk=group.slice(Math.floor(wi/4)*4,Math.floor(wi/4)*4+4);
  x.save();x.font='700 31px Arial';const labels=chunk.map(w=>String(w.w??w.word??'')),widths=labels.map(s=>x.measureText(s).width),total=widths.reduce((a,b)=>a+b,0)+(chunk.length-1)*22;
  const scale=Math.min(1,930/Math.max(1,total));x.translate(540,1680);x.scale(scale,scale);
  x.fillStyle='rgba(5,5,16,.88)';x.strokeStyle='rgba(255,255,255,.2)';x.lineWidth=2;x.beginPath();x.roundRect(-total/2-28,-48,total+56,88,24);x.fill();x.stroke();
  let xx=-total/2;chunk.forEach((w,i)=>{x.textAlign='left';x.fillStyle=w===cur?'#ffe27c':'#fff';x.shadowColor='#000';x.shadowBlur=7;x.fillText(labels[i],xx,12);x.shadowBlur=0;xx+=widths[i]+22});x.restore();
 }
 // progress indicator, kept separate from all text
 x.fillStyle='rgba(255,255,255,.24)';x.fillRect(60,1848,960,5);x.fillStyle='#ff7995';x.fillRect(60,1848,960*p,5);
}
window.seek=t=>{draw(t);return true};window.scoreSound=[];window.SFX={render:()=>[]};draw(0);
</script></body></html>"""
    html = html.replace("__DURATION__", str(duration)).replace("__DATA__", payload)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    print(f"Generated five distinct animated Bio Glow scenes: {duration:.2f}s")
if __name__ == "__main__":
    main()
