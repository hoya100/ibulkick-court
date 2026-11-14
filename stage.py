"""stage.py — 법정 '무대' 연출 모듈 v2: 사진 배경 + 곡선(Arc) 카메라 + 오프닝 인트로 + 시선/3/4 각도 + 타격감 + 판사 대기(연속 줌) + 2막 전환.

배경은 court_bg.py 의 법정 사진 한 장입니다. 그 위에 (1) 캐릭터, (2) 책상 모서리, (3) '앞가림막'(난간·판사석 앞면을 같은 사진으로 한 번 더 겹쳐 오려낸 것)을
쌓아서, 캐릭터가 난간·법대 '뒤에' 서 있는 것처럼 보이게 합니다.

  ▸ 위치를 바꾸고 싶다   →  아래 PLACE 표 (사진 기준 % 좌표)
  ▸ 카메라 속도/각도      →  STAGE_JS 안의 LOOK 표 (dur = 이동 시간(초), ease = 가속 곡선, arc = 곡선으로 휘는 정도)
  ▸ 앞가림막 모양         →  OCC (사진 기준 % 다각형)

templates.py 에는 STAGE_CSS / SCENE_HTML / OVERLAYS / WAIT_HTML / STAGE_JS 가 끼워집니다.
"""
import json

from court_bg import COURT_BG, COURT_BG_H, COURT_BG_W

# ---- 사진 위 배치 (x: 가로 중심 %, y: 발/허리 아랫선 %, w: 그림 너비 %) — 사진 가로를 100 으로 본 값 ----
PLACE = {
    "J": {"x": 50, "y": 56.4, "w": 11.2},     # 판사: 멀리, 법대 뒤 가운데 의자
    "P": {"x": 23, "y": 71.0, "w": 13.4},     # 검사: 왼쪽, 난간 뒤
    "L": {"x": 77, "y": 71.0, "w": 13.4},     # 변호사: 오른쪽, 난간 뒤
    "WJ": {"x": 50, "y": 57.6, "w": 16.8},    # 판사 대기 장면(팔·서류까지 그린 큰 그림)
}
# 앞가림막: 난간(y 68.3% 아래 전체) + 판사석 앞면(가운데 x 31~69%, y 54.6% 아래)
OCC = "polygon(0 68.3%,31% 68.3%,31% 54.6%,69% 54.6%,69% 68.3%,100% 68.3%,100% 100%,0 100%)"
# 캐릭터가 서로를 향해 돌아선 각도(도). idle=상대를 볼 때, talk=피고인(플레이어)에게 말을 걸 때 — 옆과 정면의 중간(대각선)
FACE = {"J": {"idle": 0, "talk": 0}, "P": {"idle": 36, "talk": 18}, "L": {"idle": -36, "talk": -18}}

# =================================================================
# CSS
# =================================================================
STAGE_CSS = r"""
:root{--bg:url("__BG__")}
/* ===== 사진 무대 + 카메라 ===== */
#scene,#wait{background:linear-gradient(#d6c6a2 0 22%,#6e2a20 52%,#240c10)}
#shk,#brt,#camwrap,#wshk,#wcam{position:absolute;inset:0}
#brt{animation:brt 7s ease-in-out infinite}
@keyframes brt{50%{transform:scale(1.008)}}
#camwrap,#wcam{transform-origin:50% 45%;will-change:transform;backface-visibility:hidden}
.pst{position:absolute;left:0;top:0;transform-origin:0 0;will-change:transform;backface-visibility:hidden}
.pst .pbg,.pst .pfg{position:absolute;inset:0;background:var(--bg) 0 0/100% 100% no-repeat;image-rendering:crisp-edges;image-rendering:pixelated;transform:translateZ(0)}
.pst .pfg{clip-path:__OCC__;z-index:5}
.pst .char{position:absolute;display:block;width:var(--w);left:var(--x);top:var(--y);right:auto;bottom:auto;transform:translate(-50%,-100%);z-index:2}
.pst .who{width:100%;transform:perspective(700px) rotateY(var(--ry,0deg));transform-origin:50% 100%;transition:transform .5s cubic-bezier(.3,.7,.2,1)}
.pst .who canvas,.pst .who svg{display:block;width:100%;height:auto;image-rendering:pixelated;backface-visibility:hidden}
.desk3d{position:absolute;z-index:3;background:linear-gradient(#c2573c 0 34%,#8c3322 34% 62%,#5e2118 62%);box-shadow:inset 0 3px 0 #e58a62}
.desk3d.p{left:7%;top:62.2%;width:34%;height:10%;clip-path:polygon(0 42%,100% 0,100% 46%,0 100%)}
.desk3d.l{left:59%;top:62.2%;width:34%;height:10%;clip-path:polygon(0 0,100% 42%,100% 100%,0 46%)}
.emo{position:absolute;right:-10%;top:-6%;width:34%;image-rendering:pixelated;opacity:0;pointer-events:none;transform-origin:50% 100%}
.emo.on{animation:emo 2.6s ease-out forwards}
@keyframes emo{0%{opacity:0;transform:scale(.2) translateY(10px)}18%{opacity:1;transform:scale(1.25)}30%{transform:scale(1)}80%{opacity:1}100%{opacity:0;transform:translateY(-8px)}}
.who canvas,.hdc{image-rendering:pixelated;transform:translateZ(0);backface-visibility:hidden}
/* ===== 연출 덮개 ===== */
#cover{position:absolute;inset:0;z-index:18;background:#000;opacity:0;pointer-events:none;transition:opacity .7s}
#vig{position:absolute;inset:0;z-index:17;pointer-events:none;opacity:0;background:radial-gradient(ellipse at 50% 50%,#0000 38%,#b3121ccc 100%)}
#dframe{position:absolute;inset:0;z-index:15;pointer-events:none;opacity:0;background:radial-gradient(ellipse 46% 52% at 50% 50%,#0000 60%,#000 100%)}
#doors{position:absolute;inset:0;z-index:16;display:none;pointer-events:none;overflow:hidden}
#doors i{position:absolute;top:0;bottom:0;width:50.4%;transition:transform 1.25s cubic-bezier(.5,0,.2,1);
 background:repeating-linear-gradient(90deg,#6b4423 0 22px,#5a3718 22px 26px);border:6px solid #2b1608;box-shadow:inset 0 0 0 4px #b98450,inset 0 0 60px #000a}
#doors i:after{content:"";position:absolute;top:50%;width:14px;height:44px;margin-top:-22px;background:linear-gradient(90deg,#f1d77a,#a07a2a);border:3px solid #4a2c14}
#doors .dl{left:0}#doors .dr{right:0}#doors .dl:after{right:12px}#doors .dr:after{left:12px}
#doors.open .dl{transform:translateX(-102%)}#doors.open .dr{transform:translateX(102%)}
#cap{position:absolute;left:50%;bottom:9%;z-index:19;transform:translateX(-50%);max-width:88%;padding:9px 20px;background:rgba(6,9,20,.62);border:2px solid #ffffff40;color:#f4ecd0;
 font-size:clamp(13px,3.2vw,18px);letter-spacing:1px;text-align:center;opacity:0;transition:opacity .5s;pointer-events:none;text-shadow:1px 1px 0 #000}
#cap.on{opacity:1}
#skip{position:absolute;left:8px;top:8px;z-index:31;display:none;background:#000a;color:#fff;border:2px solid #fff6;padding:3px 9px;font-size:13px;cursor:pointer}
html.intro #dlg,html.intro #phase,html.intro #hint{opacity:0 !important}
#dlg{transition:opacity .6s}
/* 막 전환 타이틀 */
#actt{position:absolute;left:0;right:0;top:30%;z-index:24;text-align:center;opacity:0;pointer-events:none;color:#f7e9b0;text-shadow:3px 3px 0 #000,0 0 24px #000a}
#actt b{display:block;font-size:clamp(34px,9vw,64px);letter-spacing:12px;font-weight:900}
#actt span{display:block;margin-top:8px;font-size:clamp(13px,3.4vw,20px);letter-spacing:4px;color:#fff;border-top:3px solid #f7e9b0aa;border-bottom:3px solid #f7e9b0aa;display:inline-block;padding:4px 18px}
#actt.on{animation:actt 4.4s ease-out forwards}
@keyframes actt{0%{opacity:0;transform:scale(1.22)}14%{opacity:1;transform:scale(1)}72%{opacity:1}100%{opacity:0;transform:translateY(-12px)}}
/* ===== 판사 대기: 같은 법정 사진에서 이어서 줌 ===== */
#w-cw{position:absolute;display:block;width:var(--w);left:var(--x);top:var(--y);bottom:auto;right:auto;transform:translate(-50%,-100%);animation:none;z-index:2}
#jchara{display:block;position:relative;width:100%;height:auto}
#w-bubble{left:57%;bottom:auto;top:12%;position:absolute;margin-bottom:0}
#w-dust{position:absolute;inset:0;z-index:3;pointer-events:none}
#w-pre{position:absolute;inset:0;z-index:12;background:#05070f;display:flex;align-items:center;justify-content:center;padding:24px;text-align:center;transition:opacity 1s}
#w-pre.off{opacity:0;pointer-events:none}
#w-pre p{color:#f4ecd0;font-size:clamp(15px,3.6vw,22px);line-height:1.9;letter-spacing:1px;white-space:pre-line;text-shadow:2px 2px 0 #000;word-break:keep-all}
#w-box{position:absolute;left:50%;bottom:6%;z-index:11;transform:translate(-50%,12px);width:min(88%,520px);padding:12px 18px;text-align:center;
 background:rgba(6,9,20,.6);border:2px solid #ffffff40;color:#f4ecd0;font-size:clamp(13px,3vw,17px);letter-spacing:.5px;opacity:0;transition:opacity .9s,transform .9s;text-shadow:1px 1px 0 #000}
#w-box.on{opacity:1;transform:translate(-50%,0)}
#w-box b:after{content:"";animation:wdots 1.4s steps(1) infinite}
@keyframes wdots{0%{content:""}25%{content:"."}50%{content:".."}75%{content:"..."}}
"""
STAGE_CSS = STAGE_CSS.replace("__BG__", COURT_BG).replace("__OCC__", OCC)

# =================================================================
# HTML
# =================================================================
SCENE_HTML = (
    '<div id="shk"><div id="brt"><div id="camwrap"><div class="pst" id="pst"><div class="pbg"></div>'
    '<div class="char j" data-c="J" data-place="J"><div class="who" id="svgJ"></div></div>'
    '<div class="char p" data-c="P" data-place="P"><div class="who" id="svgP"></div></div>'
    '<div class="char l" data-c="L" data-place="L"><div class="who" id="svgL"></div></div>'
    '<div class="desk3d p"></div><div class="desk3d l"></div><div class="pfg"></div></div></div></div></div>'
)

OVERLAYS = (
    '<div id="vig"></div><div id="cover"></div><div id="dframe"></div>'
    '<div id="doors"><i class="dl"></i><i class="dr"></i></div>'
    '<div id="actt"><b>제 2 막</b><span>변명 공방 &amp; 최후 심문</span></div>'
    '<div id="cap"></div><div id="skip">SKIP ▶</div>'
)

WAIT_HTML = (
    '<div id="wait"><div id="wshk"><div id="wcam"><div class="pst" id="wst"><div class="pbg"></div>'
    '<div id="w-cw" data-place="WJ"><canvas id="jfig"></canvas><svg id="jchara" viewBox="0 0 200 160" shape-rendering="crispEdges"></svg></div>'
    '<div class="pfg"></div></div></div></div>'
    '<div id="w-bubble"></div><div id="w-dust"></div><div id="w-vig"></div>'
    '<div id="w-pre"><p id="w-pre-t"></p></div>'
    '<div id="w-box"><span>잠시만요, 재판 내용을 검토하며 고민 중입니다</span><b></b></div></div>'
)

# =================================================================
# JS
# =================================================================
STAGE_JS = r"""
/* ============ Stage v2: 사진 법정 + 곡선 카메라 ============ */
const Stage=(function(){
const $=id=>document.getElementById(id);
const PLACE=__PLACE__,FACE=__FACE__,ASP=__ASP__,FOCUS_Y=.40;
/* 카메라 자세: fx,fy = 사진 위 바라보는 지점(0~1), z = 확대, yaw/pitch/roll = 고개 돌림(도) */
const LOOK={
 WIDE:{fx:.5,fy:.5,z:1,yaw:0,pitch:0,roll:0,dur:1.5,ease:'io',arc:.4},                    /* 법정 전체 샷 */
 J:{fx:.5,fy:.405,z:2.3,yaw:0,pitch:-3,roll:0,dur:1.15,ease:'io',arc:.55},                /* 판사: 피고인석에서 법대를 올려다보며 대각선 위로 */
 JPUSH:{fx:.5,fy:.405,z:2.65,yaw:0,pitch:-3,roll:0,dur:6,ease:'out',arc:0},               /* 막 끝: 판사 쪽으로 천천히 줌인 */
 P:{fx:.26,fy:.53,z:1.85,yaw:-3.5,pitch:0,roll:-.5,dur:.28,ease:'snap',arc:.5},          /* 검사: 빠르고 예리하게 꺾임 */
 L:{fx:.74,fy:.53,z:1.85,yaw:3.5,pitch:0,roll:.5,dur:.9,ease:'io',arc:.75}              /* 변호사: 느긋하게 곡선을 그리며 */
};
const EASE={io:t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2,out:t=>1-Math.pow(1-t,3),snap:t=>{const c=1.1,d=c+1;return 1+d*Math.pow(t-1,3)+c*Math.pow(t-1,2)},lin:t=>t};

function make(o){const cam={p:Object.assign({},LOOK.WIDE),raf:0,W:0,H:0,bw:0,bh:0,view:o.view,pst:o.pst,wrap:o.wrap};
 o.pst.querySelectorAll('[data-place]').forEach(el=>{const q=PLACE[el.dataset.place];if(q){el.style.setProperty('--x',q.x+'%');el.style.setProperty('--y',q.y+'%');el.style.setProperty('--w',q.w+'%')}});
 cam.layout=function(){const W=o.view.clientWidth,H=o.view.clientHeight;if(!W||!H)return;cam.W=W;cam.H=H;
  /* 사진이 화면을 덮도록(가로 화면) / 세로 폰에서는 가로를 1.45배까지만 늘려 법정 전체가 보이게 */
  cam.bw=Math.max(W,Math.min(H*ASP,W*1.45));cam.bh=cam.bw/ASP;o.pst.style.width=cam.bw+'px';o.pst.style.height=cam.bh+'px';cam.apply()};
 cam.apply=function(){const p=cam.p,z=p.z,S=cam.bw*z,Sh=cam.bh*z,W=cam.W,H=cam.H;if(!W)return;
  let tx=W/2-p.fx*S,ty=H*FOCUS_Y-p.fy*Sh;tx=S>=W?Math.min(0,Math.max(W-S,tx)):(W-S)/2;ty=Sh>=H?Math.min(0,Math.max(H-Sh,ty)):(H-Sh)*.45;
  o.pst.style.transform='translate3d('+tx.toFixed(2)+'px,'+ty.toFixed(2)+'px,0) scale('+z.toFixed(4)+')';
  o.wrap.style.transform='perspective(1100px) rotateY('+p.yaw.toFixed(2)+'deg) rotateX('+p.pitch.toFixed(2)+'deg) rotateZ('+p.roll.toFixed(2)+'deg) scale(1.04)'};
 cam.set=function(t){cancelAnimationFrame(cam.raf);Object.assign(cam.p,t);cam.apply()};
 /* 곡선 이동: 시작→도착을 직선으로 밀지 않고, 중간에 살짝 뒤로 물러나며(줌 아웃) 위로 휘는 베지어 곡선 위를 달린다 */
 cam.go=function(t,dur,ease,arc,done){cancelAnimationFrame(cam.raf);const p0=Object.assign({},cam.p),p1=Object.assign({},p0,t);arc=arc==null?.5:arc;
  if(!(dur>0)){cam.set(p1);if(done)done();return}
  const dist=Math.hypot(p1.fx-p0.fx,p1.fy-p0.fy),pull=arc*(.15+dist*.9),dir=(p1.fx-p0.fx)>=0?1:-1;
  const C={fx:(p0.fx+p1.fx)/2,fy:(p0.fy+p1.fy)/2-arc*.04*Math.min(1,dist*3),z:Math.max(.9,Math.min(p0.z,p1.z)-pull)};
  const E=EASE[ease]||EASE.io,t0=performance.now();
  (function fr(now){let k=Math.min(1,(now-t0)/(dur*1000));const u=E(k),a=(1-u)*(1-u),b=2*(1-u)*u,c=u*u;
   cam.p.fx=a*p0.fx+b*C.fx+c*p1.fx;cam.p.fy=a*p0.fy+b*C.fy+c*p1.fy;cam.p.z=a*p0.z+b*C.z+c*p1.z;
   cam.p.yaw=p0.yaw+(p1.yaw-p0.yaw)*u+Math.sin(Math.PI*k)*arc*2.6*dir;cam.p.pitch=p0.pitch+(p1.pitch-p0.pitch)*u;cam.p.roll=p0.roll+(p1.roll-p0.roll)*u;
   cam.apply();if(k<1)cam.raf=requestAnimationFrame(fr);else if(done)done()})(t0)};
 cam.layout();
 if(window.ResizeObserver)new ResizeObserver(()=>cam.layout()).observe(o.view);else window.addEventListener('resize',cam.layout);
 return cam}

function look(cam,key){const p=LOOK[key]||LOOK.J;cam.go({fx:p.fx,fy:p.fy,z:p.z,yaw:p.yaw,pitch:p.pitch,roll:p.roll},p.dur,p.ease,p.arc);return p.dur}
function push(cam){look(cam,'JPUSH')}

/* 몸을 돌려 서로 마주보기: 말하는 사람은 피고인(플레이어) 쪽으로 몸을 돌려(옆과 정면 사이의 대각선), 듣는 사람은 상대를 향한다 */
function face(speaker){document.querySelectorAll('#pst .char').forEach(el=>{const k=el.dataset.c,f=FACE[k]||{idle:0,talk:0};el.style.setProperty('--ry',((k===speaker?f.talk:f.idle))+'deg')})}

/* 감정 아이콘(도트): 표정이 바뀔 때 머리 옆에 잠깐 떠서 감정을 쉽게 읽게 한다 */
const ICON={
 anger:{c:{'r':'#e23a3a','d':'#7a1010'},m:['.........','.r..r....','..r.r.r..','r..rr.r..','..r..r.r.','.r.r.r.r.','r.r..r...','.r.......','.........']},
 exclaim:{c:{'r':'#ffd23f','d':'#a06a00'},m:['....rr...','...rrrr..','...rrrr..','...rrrr..','....rr...','....rr...','.........','....dd...','...dddd..']},
 drop:{c:{'r':'#7ec8ff','d':'#2f7fc0','w':'#ffffff'},m:['....r....','....r....','...rrr...','...rwr...','..rrwrr..','..rrrrr..','..rrrrd..','...rdd...','.........']},
 sparkle:{c:{'r':'#fff2a0','d':'#e0a82e'},m:['....r....','....r....','...rrr...','rrrrdrrrr','...rrr...','....r....','....r....','.........','.........']}};
function iconCanvas(name){const d=ICON[name];if(!d)return null;const c=document.createElement('canvas');c.width=11;c.height=11;c.className='emo';const x=c.getContext('2d');
 [[0,1],[2,1],[1,0],[1,2]].forEach(o=>{x.fillStyle='#2a1020';d.m.forEach((row,y)=>{for(let i=0;i<9;i++)if(row[i]!=='.')x.fillRect(i+o[0],y+o[1],1,1)})});   /* 어두운 테두리 */
 d.m.forEach((row,y)=>{for(let i=0;i<9;i++){const ch=row[i];if(ch!=='.'){x.fillStyle=d.c[ch];x.fillRect(i+1,y+1,1,1)}}});return c}
function emote(el,name){if(!el)return;let c=el.querySelector('.emo');if(c)c.remove();if(!name)return;c=iconCanvas(name);if(!c)return;el.appendChild(c);void c.offsetWidth;c.classList.add('on')}

/* 타격감: 화면 흔들림 + 움찔(확대) + 붉은 비네팅 깜빡임('동공 지진') */
function flinch(power){const el=$('shk');if(!el||!el.animate)return;let p=power==null?1:power;if(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches)p*=.35;
 const f=[[0,0,1],[-18,11,1.09],[15,-13,1.07],[-12,9,1.05],[10,-7,1.035],[-7,5,1.02],[5,-3,1.01],[-3,2,1.004],[0,0,1]].map(a=>({transform:'translate3d('+(a[0]*p)+'px,'+(a[1]*p)+'px,0) scale('+(1+(a[2]-1)*p)+')'}));
 el.animate(f,{duration:520,easing:'linear'});
 const v=$('vig');if(v&&v.animate)v.animate([{opacity:0},{opacity:.95},{opacity:.35},{opacity:.8},{opacity:.2},{opacity:.55},{opacity:0}],{duration:760,easing:'linear'})}
function impact(k){if(k==='F')flinch(1);else if(k==='S')flinch(.35);else flinch(.55)}

/* 막 전환 타이틀: 화면 중앙에 떠올랐다가 스르륵 사라진다 */
function actTitle(big,sub){const a=$('actt');if(!a)return;if(big)a.querySelector('b').textContent=big;if(sub)a.querySelector('span').textContent=sub;a.classList.remove('on');void a.offsetWidth;a.classList.add('on')}

/* 오프닝 인트로: 문 → 걸어 들어옴 → 피고인석 착석 → 법정 전체 샷 */
function intro(cam,done){const de=document.documentElement,doors=$('doors'),cap=$('cap'),skip=$('skip'),cover=$('cover'),fr=$('dframe');let over=false,raf=0;const tm=[];
 const T=(ms,f)=>tm.push(setTimeout(f,ms)),say=s=>{cap.textContent=s;cap.className='on'},B=(f,d,v)=>{try{beep(f,d,v)}catch(e){}};
 function finish(){if(over)return;over=true;cancelAnimationFrame(raf);tm.forEach(clearTimeout);doors.style.display='none';cap.className='';skip.style.display='none';cover.style.transition='none';cover.style.opacity=0;fr.style.opacity=0;de.classList.remove('intro');cam.set(LOOK.WIDE);done()}
 de.classList.add('intro');skip.style.display='block';skip.onclick=e=>{e.stopPropagation();finish()};
 cam.set({fx:.5,fy:.64,z:.84,yaw:0,pitch:2,roll:0});fr.style.transition='none';fr.style.opacity=1;fr.style.transform='scale(1)';
 doors.className='';doors.style.display='block';cover.style.transition='none';cover.style.opacity=1;void cover.offsetWidth;cover.style.transition='opacity .7s';cover.style.opacity=0;
 say('재판정 문 앞에 선다…');
 T(900,()=>{doors.className='open';say('끼이익— 법정 문이 열린다');B(110,.5,.05);B(160,.4,.04)});
 T(1900,()=>{doors.style.display='none';say('(발소리)');const t0=performance.now(),WALK=3700;let lastStep=-1;
  (function frame(now){if(over)return;const t=Math.min(1,(now-t0)/WALK),e=t<.5?2*t*t:1-Math.pow(-2*t+2,2)/2,sec=(now-t0)/1000,step=Math.floor(sec/.55);
   if(step!==lastStep){lastStep=step;B(92+(step%2)*14,.08,.05)}
   const bob=Math.abs(Math.sin(sec/.55*Math.PI))*.006;
   cam.set({fx:.5+Math.sin(sec*1.1)*.012*(1-t),fy:.64-.12*e+bob,z:.84+.16*e,yaw:Math.sin(sec*.9)*1.2*(1-t),pitch:2-2*e,roll:Math.sin(sec/.55*Math.PI)*.45*(1-t*.6)});
   fr.style.transform='scale('+(1+1.8*e).toFixed(3)+')';fr.style.opacity=(1-e).toFixed(3);
   if(t<1)raf=requestAnimationFrame(frame)})(t0)});
 T(5700,()=>{say('피고인석에 앉는다.');cam.go({fy:.54,z:.97},.38,'io',0);T(380,()=>{B(70,.14,.07);cam.go({fy:.5,z:1},.5,'out',0)})});
 T(6800,()=>{say('법정 안의 모든 시선이 나를 향한다…');cam.go(LOOK.WIDE,1.2,'io',.3)});
 T(8300,()=>finish())}

/* 판사 대기: 사진 속 법정에서 판사 쪽으로 서서히 줌. 1막→2막, 2막→판결 사이에는 앞 장면의 마지막 화면(판사 줌)에서 그대로 이어 시작한다 */
const WAIT_PRE={
 p1:'재판관이 접수된 소장을 펼쳐 놓고\n쟁점을 하나씩 짚어 보고 있습니다.',
 p2:'재판관이 방금 들은 1차 변명을 곱씹으며\n다음 심문을 준비하고 있습니다.',
 verdict:'재판관이 모든 변론과 증거를 검토하며\n최종 판결을 깊이 고민하고 있습니다.'};
let waitCam=null;
function wait(kind){waitCam=make({view:$('wait'),pst:$('wst'),wrap:$('wcam')});
 const cont=(kind==='p2'||kind==='verdict');
 if(cont){$('w-pre').style.display='none';waitCam.set(LOOK.JPUSH);setTimeout(()=>{$('w-box').className='on'},500);waitCam.go({z:LOOK.JPUSH.z+.4,fy:.45},26,'out',0);return}
 waitCam.set(LOOK.WIDE);
 const txt=WAIT_PRE[kind]||WAIT_PRE.p1,pt=$('w-pre-t');let k=0;const iv=setInterval(()=>{k++;pt.textContent=txt.slice(0,k);if(k>=txt.length)clearInterval(iv)},55);
 setTimeout(()=>{$('w-pre').className='off';setTimeout(()=>{$('w-box').className='on'},700);waitCam.go(LOOK.JPUSH,18,'out',.35)},Math.max(2600,txt.length*55+700))}
function relayout(){if(waitCam)waitCam.layout()}

return {make:make,look:look,push:push,face:face,emote:emote,flinch:flinch,impact:impact,intro:intro,actTitle:actTitle,wait:wait,relayout:relayout,LOOK:LOOK,PLACE:PLACE};
})();
"""
STAGE_JS = (STAGE_JS.replace("__PLACE__", json.dumps(PLACE)).replace("__FACE__", json.dumps(FACE))
            .replace("__ASP__", f"{COURT_BG_W / COURT_BG_H:.5f}"))
