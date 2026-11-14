"""stage.py — 법정 '무대' 연출 모듈: 파노라마 법정 배경 + 패럴랙스 카메라 + 오프닝 인트로 + 시선(카메라) 이동 + 타격감 + 판사 대기(줌인).

templates.py 의 VN_TEMPLATE 에 아래 조각들이 끼워집니다. (캐릭터 그림은 characters.py → SPRITES_JS, 여기는 '카메라와 배경'만 담당)

  STAGE_CSS     : 카메라/레이어/인트로/대기 화면 CSS
  LAYER_FAR     : 뒤쪽 두 레이어(원경 벽·유리 천장·바닥 / 중경 문·배너·난간) HTML
  LAYER_NEAR    : 앞쪽 레이어(전경 기둥) HTML
  OVERLAYS      : 입장 문 / 자막 / 스킵 버튼 / 비네팅 등 덮개 HTML
  WAIT_HTML     : 판사 대기 장면(와이드 법정 + 줌인 + 안내 문구) HTML
  STAGE_JS      : 도트 법정 그리기 + 카메라(Stage.make / look / impact / intro / wait)

카메라 조작 값 — 모두 아래 LOOK 표 한 곳에서 고칩니다 (STAGE_JS 안).
  x : -1(검사석) ~ 0(법대) ~ +1(변호사석)    y : -1(위, 법대를 올려다봄) ~ +1(아래)    z : 확대(1=기본)
  dur / ease : 시선이 움직이는 시간(초) / 가속 곡선
"""

# =================================================================
# CSS
# =================================================================
STAGE_CSS = r"""
/* ===== 무대: 카메라 · 패럴랙스 레이어 ===== */
#shk,#brt,#camwrap{position:absolute;inset:0}
#brt{animation:brt 7s ease-in-out infinite}
@keyframes brt{50%{transform:scale(1.012)}}
#camwrap{transform-origin:50% 62%;will-change:transform;backface-visibility:hidden}
.lay{position:absolute;inset:0;pointer-events:none;backface-visibility:hidden}
.lz{position:absolute;inset:0;transform-origin:50% 62%;will-change:transform;transform:translateZ(0);backface-visibility:hidden}
.lp{position:absolute;left:0;top:0;will-change:transform;transform:translateZ(0);backface-visibility:hidden}
canvas.pxl{display:block;width:100%;height:100%;image-rendering:crisp-edges;image-rendering:pixelated;transform:translateZ(0)}
.who canvas,.hdc{image-rendering:pixelated;transform:translateZ(0);backface-visibility:hidden}
#world{width:300%;height:100%;display:flex;transform:none;transition:none}
#world .panel{background:none !important}
#world .wood,#world .pil,#world .floor,#world .seal{display:none}
#scene{perspective:none}
/* 인트로 / 연출 덮개 */
#cover{position:absolute;inset:0;z-index:18;background:#000;opacity:0;pointer-events:none;transition:opacity .7s}
#vig{position:absolute;inset:0;z-index:17;pointer-events:none;opacity:0;background:radial-gradient(ellipse at 50% 50%,#0000 38%,#b3121ccc 100%)}
#doors{position:absolute;inset:0;z-index:16;display:none;pointer-events:none;overflow:hidden}
#doors i{position:absolute;top:0;bottom:0;width:50.4%;transition:transform 1.25s cubic-bezier(.5,0,.2,1);
 background:repeating-linear-gradient(90deg,#6b4423 0 22px,#5a3718 22px 26px);border:6px solid #2b1608;box-shadow:inset 0 0 0 4px #b98450,inset 0 0 60px #000a}
#doors i:after{content:"";position:absolute;top:50%;width:14px;height:44px;margin-top:-22px;background:linear-gradient(90deg,#f1d77a,#a07a2a);border:3px solid #4a2c14}
#doors .dl{left:0}#doors .dr{right:0}
#doors .dl:after{right:12px}#doors .dr:after{left:12px}
#doors.open .dl{transform:translateX(-102%)}#doors.open .dr{transform:translateX(102%)}
#cap{position:absolute;left:50%;bottom:9%;z-index:19;transform:translateX(-50%);max-width:88%;padding:9px 20px;background:rgba(6,9,20,.62);border:2px solid #ffffff40;color:#f4ecd0;
 font-size:clamp(13px,3.2vw,18px);letter-spacing:1px;text-align:center;opacity:0;transition:opacity .5s;pointer-events:none;text-shadow:1px 1px 0 #000}
#cap.on{opacity:1}
#skip{position:absolute;left:8px;top:8px;z-index:31;display:none;background:#000a;color:#fff;border:2px solid #fff6;padding:3px 9px;font-size:13px;cursor:pointer}
html.intro #dlg,html.intro #phase,html.intro #hint{opacity:0 !important}
#dlg{transition:opacity .6s}
/* ===== 판사 대기: 와이드 법정 + 서서히 줌인 ===== */
#wshk,#wcam{position:absolute;inset:0}
#wcam{transform-origin:50% 62%;will-change:transform}
#wworld{width:100%;height:100%}
#w-bench{left:50%;right:auto;transform:translateX(-50%);z-index:2;border:5px solid #3a2210;border-bottom:0;
 background:linear-gradient(#b98450 0 14%,#8a5a34 14% 100%);box-shadow:inset 0 6px 0 #d9b85a66}
#w-bench:before,#w-bench:after{content:"";position:absolute;bottom:0;width:46%;height:62%;background:linear-gradient(#a3703c 0 16%,#6b4423 16%);border:5px solid #3a2210;border-bottom:0}
#w-bench:before{right:100%;margin-right:-5px}#w-bench:after{left:100%;margin-left:-5px}
#w-bench i{position:absolute;left:0;right:0;top:100%;height:14px;background:#4a2c14;border-top:3px solid #b98450;box-shadow:0 14px 0 #3a2210}
#w-cw{z-index:1}
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

# =================================================================
# HTML 조각
# =================================================================
def _layer(i, extra=""):
    return f'<div class="lay" data-l="{i}"><div class="lz"><div class="lp"><canvas class="pxl"></canvas></div></div></div>'


LAYER_FAR = _layer(0) + _layer(1)
LAYER_NEAR = _layer(3)

OVERLAYS = (
    '<div id="vig"></div><div id="cover"></div>'
    '<div id="doors"><i class="dl"></i><i class="dr"></i></div>'
    '<div id="cap"></div><div id="skip">SKIP ▶</div>'
)

WAIT_HTML = (
    '<div id="wait"><div id="wshk"><div id="wcam">'
    + _layer(0) + _layer(1)
    + '<div class="lay" data-l="w"><div class="lz"><div class="lp" id="wworld">'
      '<div id="w-cw"><canvas id="jfig"></canvas><svg id="jchara" viewBox="0 0 200 160" shape-rendering="crispEdges"></svg><div id="w-bubble"></div></div>'
      '<div id="w-bench"><i></i></div></div></div></div>'
    + _layer(3)
    + '</div></div><div id="w-dust"></div><div id="w-vig"></div>'
      '<div id="w-pre"><p id="w-pre-t"></p></div>'
      '<div id="w-box"><span>잠시만요, 재판 내용을 검토하며 고민 중입니다</span><b></b></div></div>'
)

# =================================================================
# JS
# =================================================================
STAGE_JS = r"""
/* ============ Stage: 도트 법정 파노라마 + 패럴랙스 카메라 ============ */
const Stage=(function(){
const $=id=>document.getElementById(id);
const C={wood:'#8a5a34',woodD:'#6b4423',woodL:'#b98450',woodX:'#3a2210',gold:'#d9b85a',goldD:'#a07a2a',stone:'#cfc2a0',stoneD:'#b3a47c',
 glass:'#a9d3f0',glassL:'#e4f3fc',glassD:'#6fa6d2',purple:'#6d2a9c',purpleD:'#4a1b70',blue:'#2f5a8a',blueD:'#1d3a5e',tileL:'#dfe8e1',tileD:'#a9bbb0'};
function mk(w,h){const c=document.createElement('canvas');c.width=w;c.height=h;const x=c.getContext('2d');x.imageSmoothingEnabled=false;return [c,x]}
function rect(x,X,Y,W,H,c,a){if(a!=null)x.globalAlpha=a;x.fillStyle=c;x.fillRect(Math.round(X),Math.round(Y),Math.max(1,Math.round(W)),Math.max(1,Math.round(H)));if(a!=null)x.globalAlpha=1}
function line(x,x0,y0,x1,y1,c){const n=Math.max(Math.abs(x1-x0),Math.abs(y1-y0))||1;for(let i=0;i<=n;i++)rect(x,x0+(x1-x0)*i/n,y0+(y1-y0)*i/n,1,1,c)}
function disc(x,cx,cy,r,c,a){for(let y=-r;y<=r;y++){const w=Math.round(Math.sqrt(r*r-y*y));rect(x,cx-w,cy+y,w*2+1,1,c,a)}}
function rnd(s){return()=>(s=(s*16807)%2147483647)/2147483647}

/* 원경: 유리 천장(채광창) · 돌벽 · 중앙 법대 벽(저울 문양) · 체크무늬 바닥 */
function paintFar(){const [c,x]=mk(256,160),r=rnd(7);
 rect(x,0,0,256,160,C.stone);
 for(let y=0;y<42;y++){const t=y/42,ins=Math.round(46*t);rect(x,ins,y,256-ins*2,1,t<.3?C.glassL:t<.65?C.glass:C.glassD);rect(x,0,y,ins,1,C.woodD);rect(x,256-ins,y,ins,1,C.woodD)}
 for(let k=-9;k<=9;k++)line(x,128+k*5,41,128+k*30,0,C.woodX);
 [6,14,23,33].forEach(y=>{const ins=Math.round(46*y/42);rect(x,ins,y,256-2*ins,2,C.woodD)});
 for(let i=0;i<150;i++)rect(x,Math.floor(r()*256),Math.floor(r()*40),1,1,C.glassL);
 rect(x,0,42,256,5,C.woodD);rect(x,0,42,256,1,C.gold);rect(x,0,46,256,1,C.woodX);
 for(let row=0;47+row*8<96;row++){const y=47+row*8;rect(x,0,y,256,1,C.stoneD);for(let X=(row&1)*8;X<256;X+=16)rect(x,X,y,1,8,C.stoneD)}
 rect(x,0,47,40,49,'#000',.14);rect(x,216,47,40,49,'#000',.14);
 /* 중앙 법대 벽 */
 rect(x,94,56,68,40,C.gold);rect(x,96,58,64,38,C.woodX);rect(x,98,60,60,36,C.woodD);
 for(let y=50;y<58;y++){const dx=Math.round(33*Math.sqrt(1-((58-y)/8)**2));rect(x,128-dx,y,dx*2,1,y<52?C.gold:C.woodD)}
 for(let X=100;X<158;X+=6)rect(x,X,62,2,34,C.wood);
 disc(x,128,68,9,C.goldD);disc(x,128,68,7,C.gold);disc(x,128,68,5,'#f1d77a');
 rect(x,127,60,2,17,C.woodX);rect(x,119,64,18,2,C.woodX);rect(x,118,66,5,1,C.woodX);rect(x,133,66,5,1,C.woodX);rect(x,117,70,7,2,C.woodX);rect(x,132,70,7,2,C.woodX);
 /* 기둥 */
 [40,206].forEach(px=>{rect(x,px,47,12,49,C.stone);rect(x,px,47,2,49,'#fff',.35);rect(x,px+10,47,2,49,'#000',.2);rect(x,px-2,47,16,4,C.gold);rect(x,px-2,92,16,4,C.goldD)});
 rect(x,0,92,256,4,C.woodD);rect(x,0,92,256,1,C.gold);
 /* 바닥: 원근 체크 타일 */
 for(let y=96;y<160;y++){const v=y-84,row=Math.floor(560/v),cw=v*0.6;for(let X=0;X<256;X++){const col=Math.floor((X-128)/cw);rect(x,X,y,1,1,((row+col)&1)?C.tileD:C.tileL)}}
 for(let y=96;y<122;y++)rect(x,0,y,256,1,'#000',.2*(1-(y-96)/26));
 /* 빛줄기 */
 [[30,.10],[104,.08],[176,.10]].forEach(a=>{for(let y=0;y<150;y++)rect(x,a[0]+y*.55,y,16+y*.12,1,'#fff',a[1])});
 return c}

/* 중경: 판자벽 · 양옆 문 · 보라/파랑 배너 · 벽등 · 방청석 난간 */
function paintMid(){const [c,x]=mk(320,160);
 [[0,96],[224,96]].forEach(a=>{const X0=a[0];rect(x,X0,76,96,20,C.wood);for(let i=0;i<96;i+=8)rect(x,X0+i,76,1,20,C.woodD);rect(x,X0,74,96,3,C.woodL);rect(x,X0,73,96,1,C.gold)});
 const door=cx=>{rect(x,cx-22,50,44,46,C.gold);rect(x,cx-20,52,40,44,C.woodX);rect(x,cx-18,56,36,40,C.woodD);
  for(let y=48;y<57;y++){const dx=Math.round(20*Math.sqrt(1-((57-y)/9)**2));rect(x,cx-dx,y,dx*2,1,y<50?C.gold:C.woodX)}
  rect(x,cx-18,57,36,39,C.wood);rect(x,cx,50,1,46,C.woodX);for(let k=0;k<2;k++)[62,80].forEach(py=>rect(x,cx-15+k*17,py,13,13,C.woodD));
  rect(x,cx-4,76,2,4,C.gold);rect(x,cx+2,76,2,4,C.gold);disc(x,cx,44,2,C.gold)};
 door(30);door(290);
 const banner=(bx,col,colD)=>{rect(x,bx-2,36,14,2,C.gold);rect(x,bx,38,10,32,col);rect(x,bx,38,1,32,colD);rect(x,bx+9,38,1,32,colD);for(let i=0;i<5;i++)rect(x,bx+i,70+i,10-2*i,1,col);rect(x,bx+3,48,4,4,C.gold);rect(x,bx+4,53,2,9,C.gold)};
 banner(96,C.purple,C.purpleD);banner(112,C.blue,C.blueD);banner(200,C.blue,C.blueD);banner(216,C.purple,C.purpleD);
 [[78,64],[242,64]].forEach(a=>{for(let r=14;r>=3;r-=3)disc(x,a[0],a[1],r,'#ffd877',.07);rect(x,a[0]-1,a[1],3,8,C.goldD);disc(x,a[0],a[1]-1,2,'#fff1b8')});
 [[0,66],[254,66]].forEach(a=>{rect(x,a[0],84,a[1],3,C.woodL);rect(x,a[0],83,a[1],1,C.gold);for(let X=a[0]+2;X<a[0]+a[1];X+=5)rect(x,X,87,2,10,C.woodD);rect(x,a[0],96,a[1],3,C.woodX)});
 return c}

/* 전경: 계단 난간 기둥(금 장식) + 천장 들보 — 가장 빠르게 움직인다 */
function paintNear(){const [c,x]=mk(600,150);
 rect(x,0,0,600,8,C.woodX);rect(x,0,8,600,2,C.woodD);
 for(let X=0;X<600;X+=120){for(let i=0;i<14;i++)rect(x,X+i,10,14-i,1,C.woodX);for(let i=0;i<14;i++)rect(x,X+120-i-1,10,i+1,1,C.woodX)}
 [18,138,232,368,462,582].forEach(px=>{rect(x,px-11,70,22,80,C.woodD);rect(x,px-11,70,3,80,C.woodL);rect(x,px+8,70,3,80,C.woodX);
  rect(x,px-15,62,30,8,C.woodX);rect(x,px-15,61,30,2,C.gold);rect(x,px-4,56,8,6,C.woodD);disc(x,px,50,7,C.goldD);disc(x,px,50,5,C.gold);rect(x,px-3,46,3,3,'#f9e9a5');
  [82,96,110].forEach(y=>{rect(x,px-2,y,4,1,C.gold);rect(x,px-3,y+1,6,1,C.gold);rect(x,px-2,y+2,4,1,C.gold)})});
 [[40,130],[154,78],[250,118],[380,80],[478,104]].forEach(a=>{rect(x,a[0],126,a[1],5,C.woodL);rect(x,a[0],131,a[1],4,C.woodD);for(let X=a[0]+4;X<a[0]+a[1];X+=7)rect(x,X,135,3,15,C.woodX)});
 return c}

const LAYERS={'0':{paint:paintFar,cw:256,ch:160,hz:96,hf:1.3,wmin:1.4,ky:.04,m:.35},
 '1':{paint:paintMid,cw:320,ch:160,hz:96,hf:1.45,wmin:1.75,ky:.07,m:.6},
 'w':{world:1,ky:.12,m:1},
 '3':{paint:paintNear,cw:600,ch:150,hz:100,hf:1.4,wmin:3.6,ky:.2,m:1.7}};
const HZN=.62;   /* 화면에서 '바닥이 시작되는 높이'(전 레이어 공통) */

/* ---- 카메라: 레이어마다 이동량·확대량이 달라 원근감(패럴랙스)이 생긴다 ---- */
function make(root,opt){opt=opt||{};const cam={st:{x:0,y:0,z:1,roll:0},dur:0,L:[]};
 root.querySelectorAll('.lay').forEach(el=>{const d=LAYERS[el.dataset.l];if(!d)return;const L=Object.assign({},d,{z:el.querySelector('.lz'),p:el.querySelector('.lp'),cv:el.querySelector('canvas.pxl'),kx:0,base:0});
  if(L.paint){const c=L.paint();L.cv.width=c.width;L.cv.height=c.height;const g=L.cv.getContext('2d');g.imageSmoothingEnabled=false;g.drawImage(c,0,0)}cam.L.push(L)});
 let W=1,H=1;
 cam.layout=function(){W=root.clientWidth||0;H=root.clientHeight||0;if(!W||!H)return;
  cam.L.forEach(L=>{if(L.world){L.kx=opt.worldKx==null?W:opt.worldKx;L.base=opt.worldBase==null?-W:opt.worldBase;L.pky=H*L.ky;return}
   let h=H*L.hf,w=h*L.cw/L.ch;if(w<W*L.wmin){w=W*L.wmin;h=w*L.ch/L.cw}
   L.p.style.width=w+'px';L.p.style.height=h+'px';L.p.style.left=((W-w)/2)+'px';L.p.style.top=(H*HZN-L.hz/L.ch*h)+'px';L.kx=(w-W)/2;L.pky=H*L.ky});
  cam.apply(0,'')};
 cam.apply=function(dur,ease){const s=cam.st,tr=dur>0?('transform '+dur+'s '+ease):'none';
  cam.L.forEach(L=>{const sc=1+(s.z-1)*L.m;L.z.style.transition=tr;L.p.style.transition=tr;L.z.style.transform='scale('+sc.toFixed(4)+') translateZ(0)';
   L.p.style.transform='translate3d('+(L.base-s.x*L.kx).toFixed(1)+'px,'+(-s.y*(L.pky||0)).toFixed(1)+'px,0)'});
  root.style.transition=tr;root.style.transform='perspective(1200px) rotateY('+(-s.x*1.8).toFixed(2)+'deg) rotateX('+(s.y*1.4).toFixed(2)+'deg) rotateZ('+s.roll.toFixed(2)+'deg) scale(1.03)'};
 cam.set=function(t,dur,ease){Object.assign(cam.st,t);cam.dur=dur||0;cam.apply(dur||0,ease||'ease')};
 cam.layout();
 if(window.ResizeObserver)new ResizeObserver(()=>cam.layout()).observe(root.parentNode||root);else window.addEventListener('resize',cam.layout);
 return cam}

/* ---- 시선 프리셋: 상황별 속도(dur)·가속(ease)을 여기서 조절한다 ---- */
const LOOK={
 P:{x:-1,y:.02,z:1.02,roll:-.5,dur:.25,ease:'cubic-bezier(.08,.9,.2,1.12)'},      /* 검사: 빠르고 예리한 스냅 */
 L:{x:1,y:0,z:1,roll:.3,dur:.8,ease:'cubic-bezier(.45,.02,.25,1)'},               /* 변호사: 능청스럽게 느긋이 */
 J:{x:-.12,y:-1,z:1.07,roll:-.8,dur:1.0,ease:'cubic-bezier(.35,0,.15,1)'},         /* 판사: 피고인석에서 법대를 대각선 위로 올려다봄 */
 SEAT:{x:0,y:.1,z:.97,roll:0,dur:.6,ease:'ease-in-out'}
};
function look(cam,key){const p=LOOK[key]||LOOK.J;cam.set({x:p.x,y:p.y,z:p.z,roll:p.roll},p.dur,p.ease);return p.dur}

/* ---- 타격감: 화면 흔들림 + 움찔(확대) + 붉은 비네팅 깜빡임('동공 지진') ---- */
function flinch(power){const el=$('shk');if(!el||!el.animate)return;let p=power==null?1:power;if(window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches)p*=.35;
 const f=[[0,0,1],[-18,11,1.09],[15,-13,1.07],[-12,9,1.05],[10,-7,1.035],[-7,5,1.02],[5,-3,1.01],[-3,2,1.004],[0,0,1]].map(a=>({transform:'translate3d('+(a[0]*p)+'px,'+(a[1]*p)+'px,0) scale('+(1+(a[2]-1)*p)+')'}));
 el.animate(f,{duration:520,easing:'linear'});
 const v=$('vig');if(v&&v.animate)v.animate([{opacity:0},{opacity:.95},{opacity:.35},{opacity:.8},{opacity:.2},{opacity:.55},{opacity:0}],{duration:760,easing:'linear'})}
function impact(k){if(k==='F')flinch(1);else if(k==='S')flinch(.35);else flinch(.55)}

/* ---- 오프닝 인트로: 법정 문 → 걸어 들어옴 → 피고인석에 착석 → 법대를 올려다봄 ---- */
function intro(cam,done){const de=document.documentElement,doors=$('doors'),cap=$('cap'),skip=$('skip'),cover=$('cover');let over=false,raf=0;const tm=[];
 const T=(ms,f)=>tm.push(setTimeout(f,ms)),say=s=>{cap.textContent=s;cap.className='on'},B=(f,d,v)=>{try{beep(f,d,v)}catch(e){}};
 function finish(skipped){if(over)return;over=true;cancelAnimationFrame(raf);tm.forEach(clearTimeout);doors.style.display='none';cap.className='';skip.style.display='none';cover.style.transition='none';cover.style.opacity=0;de.classList.remove('intro');cam.set(LOOK.SEAT,0,'');done()}
 de.classList.add('intro');skip.style.display='block';skip.onclick=e=>{e.stopPropagation();finish(true)};
 cam.set({x:0,y:.06,z:.7,roll:0},0,'');doors.className='';doors.style.display='block';cover.style.transition='none';cover.style.opacity=1;void cover.offsetWidth;cover.style.transition='opacity .7s';cover.style.opacity=0;
 say('재판정 문 앞에 선다…');
 T(900,()=>{doors.className='open';say('끼이익— 법정 문이 열린다');B(110,.5,.05);B(160,.4,.04)});
 T(1900,()=>{doors.style.display='none';say('저벅… 저벅…');const t0=performance.now(),WALK=3700;let lastStep=-1;
  (function frame(now){if(over)return;const t=Math.min(1,(now-t0)/WALK),e=t<.5?2*t*t:1-Math.pow(-2*t+2,2)/2,sec=(now-t0)/1000,step=Math.floor(sec/.55);
   if(step!==lastStep){lastStep=step;B(92+(step%2)*14,.08,.05)}
   const bob=Math.abs(Math.sin(sec/.55*Math.PI))*.045;
   cam.set({x:Math.sin(sec*1.1)*.14*(1-t),y:(.04-.2*(1-e))-bob+.0,z:.7+(.97-.7)*e,roll:Math.sin(sec/.55*Math.PI)*.45*(1-t*.6)},0,'');
   if(t<1)raf=requestAnimationFrame(frame)})(t0)});
 T(5700,()=>{say('피고인석에 앉는다.');cam.set({x:0,y:.2,z:.95,roll:0},.38,'cubic-bezier(.4,0,.8,.6)');T(380,()=>{B(70,.14,.07);cam.set({x:0,y:.1,z:.97,roll:0},.5,'cubic-bezier(.2,1.5,.4,1)')})});
 T(6900,()=>{say('모든 시선이 나를 향한다…');cam.set({x:-.1,y:-.7,z:1.0,roll:-.5},1.0,'ease-in-out')});
 T(8300,()=>finish(false))}

/* ---- 판사 대기: 법정 와이드 → 법대 쪽으로 천천히 줌인. 먼저 안내 문구를 띄우고 장면으로 넘어간다 ---- */
const WAIT_PRE={
 p1:'재판관이 접수된 소장을 펼쳐 놓고\n쟁점을 하나씩 짚어 보고 있습니다.',
 p2:'재판관이 방금 들은 1차 변명을 곱씹으며\n다음 심문을 준비하고 있습니다.',
 verdict:'재판관이 모든 변론과 증거를 검토하며\n최종 판결을 깊이 고민하고 있습니다.'};
let waitCam=null;
function wait(kind){const root=$('wcam');waitCam=make(root,{worldKx:0,worldBase:0});waitCam.set({x:0,y:.12,z:1,roll:0},0,'');
 const txt=WAIT_PRE[kind]||WAIT_PRE.p1,pt=$('w-pre-t');let k=0;const iv=setInterval(()=>{k++;pt.textContent=txt.slice(0,k);if(k>=txt.length)clearInterval(iv)},55);
 setTimeout(()=>{$('w-pre').className='off';setTimeout(()=>{$('w-box').className='on'},700);
  waitCam.set({x:0,y:-.45,z:1.55,roll:-.4},18,'cubic-bezier(.22,.6,.3,1)')},Math.max(2600,txt.length*55+700))}
function relayout(){if(waitCam)waitCam.layout()}

return {make:make,look:look,flinch:flinch,impact:impact,intro:intro,wait:wait,relayout:relayout,LOOK:LOOK};
})();
"""
