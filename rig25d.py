"""rig25d.py — 서브컬처 일러스트풍 '레이어 분할 2.5D' 캐릭터 엔진 v2 (벡터 셀셰이딩).

v1 의 문제(어깨에 박힌 둥근 덩어리, 튜브형 팔, 뾰족한 턱, 굵은 검은 윤곽선, 과한 3D 회전)를 전부 버리고 다시 만들었습니다.

  ▸ 몸: 어깨→소매가 '한 장의 매끈한 실루엣'으로 이어지는 상반신 일러스트. 팔을 따로 박지 않습니다.
  ▸ 얼굴: 둥글고 작은 턱, 큰 눈(홍채 결·이중 하이라이트·속눈썹), 작은 입, 색 윤곽선(검정 X), 앞머리가 드리운 이마의 '딱 떨어지는 셀 그림자'
  ▸ 입체감: 판을 겹쳐 놓고 아주 약한 원근(패럴랙스)만 줍니다. 고개는 최대 약 20° 만 돌아가므로 일그러지지 않습니다.

  레이어(뒤→앞)  [뒷머리][몸 뒤판][몸통][소매] / 머리: [귀][얼굴][눈][눈썹][입][효과][옆머리][앞머리][장식]

  ▸ 캐릭터 생김새  → characters.py 의 sprite["rig"]    ▸ 표정 → EXPRESSIONS    ▸ 깊이 간격 → 아래 RIG_Z    ▸ 체형 → RIG_BODY
"""

RIG_JS = r"""
/* ============ 서브컬처 2.5D 리그 v2 (rig25d.py) ============ */
const RIG_Z={hairBack:-20,bodyBack:-12,torso:-5,sleeves:6,ears:-4,face:0,shade:1,eyes:3,brows:4,mouth:2,fx:5,side:9,bangs:14,acc:16};
const RIG_BODY={   // sh 어깨 / bu 가슴 / wa 허리 / hip 엉덩이 / bz 곡선 강도 / tp 소매 끝이 안쪽으로 모이는 정도
 curvy:{sh:80,bu:57,wa:40,hip:55,bz:1,tp:11},
 slim:{sh:84,bu:56,wa:42,hip:55,bz:.55,tp:9},
 broad:{sh:92,bu:72,wa:64,hip:72,bz:0,tp:5}};
(function(){const s=document.createElement('style');s.textContent=`
.rig{position:relative;width:100%;aspect-ratio:268/400;perspective:calc(var(--u,1px)*1500);transform-style:preserve-3d;pointer-events:none}
.rig .rb,.rig .rh{position:absolute;inset:0;transform-style:preserve-3d}
.rig .rl{position:absolute;inset:0;transform:translateZ(calc(var(--u,1px)*var(--z,0)))}
.rig svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible;display:block}
`;document.head.appendChild(s)})();

function rigHex(h){h=(h||'#000').replace('#','');if(h.length===3)h=h.split('').map(c=>c+c).join('');return[parseInt(h.slice(0,2),16),parseInt(h.slice(2,4),16),parseInt(h.slice(4,6),16)]}
function rigMix(a,b,t){const A=rigHex(a),B=rigHex(b);return'#'+[0,1,2].map(i=>Math.round(A[i]+(B[i]-A[i])*t).toString(16).padStart(2,'0')).join('')}
let RIG_UID=0;const RIG_LIST=[];let RIG_LOOP=0;

/* 대기·로비 장면용 팔: 소매 천 + 커프스 + 손 (역기구학 결과 S,E,H 를 넣으면 갱신) — 튜브/관절 대신 매끈한 소매 형태 */
function rigArm(parent,cloth,clothL,clothD,skin,wid){
 const NS='http://www.w3.org/2000/svg',w=wid||13,mk=(t,a)=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);parent.appendChild(e);return e};
 const lineC=rigMix(clothD,'#000',.25),sk2=rigMix(skin,'#b06a5c',.35);
 const o1=mk('polyline',{fill:'none',stroke:lineC,'stroke-width':w+1.8,'stroke-linecap':'round','stroke-linejoin':'round'}),
  o2=mk('polyline',{fill:'none',stroke:lineC,'stroke-width':w*.8+1.8,'stroke-linecap':'round','stroke-linejoin':'round'}),
  f1=mk('polyline',{fill:'none',stroke:cloth,'stroke-width':w,'stroke-linecap':'round','stroke-linejoin':'round'}),
  f2=mk('polyline',{fill:'none',stroke:cloth,'stroke-width':w*.8,'stroke-linecap':'round','stroke-linejoin':'round'}),
  hl=mk('polyline',{fill:'none',stroke:clothL,'stroke-width':w*.22,'stroke-linecap':'round','stroke-linejoin':'round',opacity:.55,transform:'translate(-1.6 -1)'}),
  cuff=mk('line',{stroke:'#f2f3f8','stroke-width':w*.82,'stroke-linecap':'butt'}),
  hand=mk('g',{}),
  hp=document.createElementNS(NS,'path'),th=document.createElementNS(NS,'path');
 hp.setAttribute('d','M-4.2,-3.6 C-4.2,-7 3.6,-7.4 4.8,-3.4 C6.6,.4 5.8,5 3,7.2 C.2,9 -3.6,8 -4.8,4.2 C-5.4,1.4 -4.8,-1 -4.2,-3.6Z');hp.setAttribute('fill',skin);hp.setAttribute('stroke',sk2);hp.setAttribute('stroke-width',1);
 th.setAttribute('d','M-3.4,-1.6 C-6.6,-.2 -6.8,3.2 -4.2,4.4');th.setAttribute('fill','none');th.setAttribute('stroke',sk2);th.setAttribute('stroke-width',1);
 hand.appendChild(hp);hand.appendChild(th);
 return{vis:function(v){parent.setAttribute('display',v?'inline':'none')},set:function(S,E,H){const a=S[0].toFixed(1)+','+S[1].toFixed(1),b=E[0].toFixed(1)+','+E[1].toFixed(1),c=H[0].toFixed(1)+','+H[1].toFixed(1);
  o1.setAttribute('points',a+' '+b);f1.setAttribute('points',a+' '+b);hl.setAttribute('points',a+' '+b);
  const dx=H[0]-E[0],dy=H[1]-E[1],d=Math.hypot(dx,dy)||1,ux=dx/d,uy=dy/d,wx=H[0]-ux*5,wy=H[1]-uy*5;   // 손목(커프스) 위치
  o2.setAttribute('points',b+' '+wx.toFixed(1)+','+wy.toFixed(1));f2.setAttribute('points',b+' '+wx.toFixed(1)+','+wy.toFixed(1));
  cuff.setAttribute('x1',(wx-uy*w*.42).toFixed(1));cuff.setAttribute('y1',(wy+ux*w*.42).toFixed(1));cuff.setAttribute('x2',(wx+uy*w*.42).toFixed(1));cuff.setAttribute('y2',(wy-ux*w*.42).toFixed(1));
  const ang=Math.atan2(dy,dx)*180/Math.PI-90;hand.setAttribute('transform','translate('+(H[0]+ux*2).toFixed(1)+' '+(H[1]+uy*2).toFixed(1)+') rotate('+ang.toFixed(1)+')')}}}

function rigBust(el,key,opts){opts=opts||{};
 const C=D.cast[key],P=C.palette,R=Object.assign({body:'slim',hair:'long_wavy',jaw:'soft',outfit:'slim_suit',iris:'#6a4a3a',iris2:'#c99a6a',lash:'#2a1a1a',star:false,tilt:2,eyeW:1,eyeH:1,mouth:'smile',sleepy:0,blushA:.55,rim:'#bfd8ff',pin:null},C.rig||{});
 const B=RIG_BODY[R.body]||RIG_BODY.slim,id='rg'+(RIG_UID++)+'_',CX=134,Z=RIG_Z;
 const skin=P.skin,skS=P.skin_shadow||rigMix(P.skin,'#8a5a50',.25),skD=rigMix(skS,'#8a4a44',.35),blush=P.blush||'#e8a8a4',skLine=rigMix(skS,'#a05a50',.55);
 const hc=P.hair,hl=P.hair_light||rigMix(hc,'#fff',.3),hs=P.hair_shadow||rigMix(hc,'#000',.4),hmid=rigMix(hc,hl,.4),hLine=rigMix(hs,'#000',.25);
 const lash=R.lash,rim=R.rim;
 const U=n=>id+n;
 const svg=(inner,defs)=>'<svg viewBox="0 0 268 400" xmlns="http://www.w3.org/2000/svg">'+(defs?'<defs>'+defs+'</defs>':'')+inner+'</svg>';
 const lg=(n,x1,y1,x2,y2,stops)=>'<linearGradient id="'+U(n)+'" x1="'+x1+'" y1="'+y1+'" x2="'+x2+'" y2="'+y2+'">'+stops.map(s=>'<stop offset="'+s[0]+'" stop-color="'+s[1]+'"'+(s[2]!=null?' stop-opacity="'+s[2]+'"':'')+'/>').join('')+'</linearGradient>';
 const rg=(n,cx,cy,r,stops)=>'<radialGradient id="'+U(n)+'" cx="'+cx+'" cy="'+cy+'" r="'+r+'">'+stops.map(s=>'<stop offset="'+s[0]+'" stop-color="'+s[1]+'"'+(s[2]!=null?' stop-opacity="'+s[2]+'"':'')+'/>').join('')+'</radialGradient>';
 const blur=(n,s)=>'<filter id="'+U(n)+'" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="'+s+'"/></filter>';

 /* ---------- 얼굴 윤곽: 둥글고 작은 턱 (soft 가장 둥근 / tidy 약간 각진 / sharp 갸름) ---------- */
 const J={soft:{hw:53,chin:179,cw:15,cy:168},sharp:{hw:51,chin:181,cw:12,cy:168},tidy:{hw:54,chin:179,cw:17,cy:167}}[R.jaw]||{hw:53,chin:179,cw:15,cy:168};
 const facePath=(()=>{const L=CX-J.hw,Rr=CX+J.hw,c=J.chin,w=J.cw,cy=J.cy;return'M'+L+',102 C'+L+',66 '+(CX-J.hw*.6)+',42 '+CX+',42 C'+(CX+J.hw*.6)+',42 '+Rr+',66 '+Rr+',102 C'+Rr+',130 '+(Rr-4)+',152 '+(CX+w+14)+','+cy+' C'+(CX+w+6)+','+(c-4)+' '+(CX+9)+','+c+' '+CX+','+c+' C'+(CX-9)+','+c+' '+(CX-w-6)+','+(c-4)+' '+(CX-w-14)+','+cy+' C'+(L+4)+',152 '+L+',130 '+L+',102Z'})();

 /* ---------- 머리 모양(뒤/옆/앞) ---------- */
 const HAIR={
  long_wavy:{
   back:'M88,76 C66,84 56,122 56,176 C56,234 36,290 42,346 C44,374 38,392 40,400 L228,400 C230,392 224,374 226,346 C232,290 212,234 212,176 C212,122 202,84 180,76 C168,48 100,48 88,76Z',
   sideL:'M84,100 C72,130 64,170 58,214 C52,252 44,288 52,330 C54,350 48,368 56,388 C64,362 72,326 76,288 C82,246 88,206 88,166 C88,138 86,116 86,100Z',
   sideR:'M184,100 C196,130 204,170 210,214 C216,252 224,288 216,330 C214,350 220,368 212,388 C204,362 196,326 192,288 C186,246 180,206 180,166 C180,138 182,116 182,100Z',
   bangs:'M134,36 C100,36 78,58 74,100 C73,114 76,128 82,140 C82,118 88,100 100,92 C112,86 124,74 134,62 C144,74 156,86 168,92 C180,100 186,118 186,140 C192,128 195,114 194,100 C190,58 168,36 134,36Z',
   hi:'M94,62 C114,46 154,46 176,62',strands:['M110,56 C104,74 100,94 104,122','M124,50 C120,70 124,88 138,72','M158,52 C166,72 172,94 168,120','M98,104 C88,132 82,172 76,214','M172,104 C182,132 188,172 194,214']},
  medium:{
   back:'M88,80 C64,90 56,140 58,196 C60,232 46,262 36,278 C64,288 88,274 98,250 L170,250 C180,274 204,288 232,278 C222,262 208,232 210,196 C212,140 204,90 180,80 C168,50 100,50 88,80Z',
   sideL:'M86,100 C76,134 70,174 64,216 C58,250 46,280 40,308 C62,298 78,268 84,234 C88,200 88,160 88,130 C88,116 88,106 88,100Z',
   sideR:'M182,100 C192,134 198,174 204,216 C210,250 222,280 228,308 C206,298 190,268 184,234 C180,200 180,160 180,130 C180,116 180,106 180,100Z',
   bangs:'M134,38 C100,38 80,60 76,104 C75,118 78,132 84,146 C84,122 90,102 102,94 C114,88 126,76 134,64 C142,76 154,88 166,94 C178,102 184,122 184,146 C190,132 193,118 192,104 C188,60 168,38 134,38Z',
   hi:'M92,64 C114,46 154,46 176,64',strands:['M108,58 C102,78 100,98 104,126','M160,58 C166,78 168,98 164,126','M92,112 C82,152 72,202 64,252','M176,112 C186,152 196,202 204,252']},
  messy:{
   back:'M88,88 C82,58 106,38 134,38 C162,38 186,58 180,88 C184,106 182,124 176,140 C170,120 162,106 134,102 C106,106 98,120 92,140 C86,124 84,106 88,88Z',
   sideL:'M84,96 C78,112 80,132 85,152 C86,134 85,116 87,102Z',
   sideR:'M184,96 C190,112 188,132 183,152 C182,134 183,116 181,102Z',
   bangs:'M80,110 C68,68 94,30 134,28 C176,30 200,68 188,110 C188,100 185,92 181,86 C179,93 177,98 175,101 C171,91 165,84 161,79 C159,88 157,95 153,98 C149,88 143,81 137,75 C135,84 131,92 125,96 C123,89 117,83 111,79 C109,87 105,94 101,98 C99,92 95,88 91,85 C87,94 85,102 80,110Z',
   hi:'M94,54 C118,38 152,38 174,54',strands:['M106,48 C102,62 100,78 102,94','M134,38 C132,54 134,70 132,88','M162,48 C166,62 168,78 166,94']}
 };
 const H=HAIR[R.hair]||HAIR.long_wavy;
 const hairBackSVG=svg(
  '<path d="'+H.back+'" fill="url(#'+U('hb')+')"/>'+
  '<path d="'+H.back+'" fill="url(#'+U('hbs')+')" opacity=".5"/>'+
  H.strands.slice(0,2).map(d=>'<path d="'+d+'" fill="none" stroke="'+hs+'" stroke-width="1.4" opacity=".4" stroke-linecap="round" transform="translate(0 40)"/>').join('')+
  '<path d="'+H.back+'" fill="none" stroke="'+hLine+'" stroke-width="1" opacity=".6"/>',
  lg('hb',0,0,1,1,[[0,hl],[.35,hc],[1,hs]])+lg('hbs',0,0,0,1,[[0,'#000',0],[1,'#000',.5]]));

 /* ---------- 몸: 어깨→소매가 이어진 상반신 ---------- */
 const sh=B.sh,bu=B.bu,wa=B.wa,hip=B.hip,tp=B.tp,bz=B.bz;
 const BY=414,r=(x,y)=>(CX+x)+','+y,l=(x,y)=>(CX-x)+','+y;
 const robe=R.outfit==='judge_robe';
 const cloth=robe?P.robe:(P.suit||P.robe||'#3a3a44'),clothL=robe?P.robe_light:(P.suit_light||rigMix(cloth,'#fff',.2)),clothD=rigMix(cloth,'#000',.45),clothLine=rigMix(cloth,'#000',.6);
 const shirt=P.shirt||'#eef0f6',shirtS=P.shirt_shadow||'#cdd2e0',tie=P.tie||'#222';
 /* 가슴~허리 중심 몸통 (겨드랑이 사이) */
 const torsoPath=()=>'M'+l(21,205)+' C'+l(46,208)+' '+l(sh-16,218)+' '+l(sh-4,240)+' C'+l(sh+2,252)+' '+l(sh-4,266)+' '+l(sh-14,276)+' C'+l(bu+4,296)+' '+l(bu,320)+' '+l(wa+4,352)+' C'+l(wa,372)+' '+l(hip-4,388)+' '+l(hip,BY)+
   ' L'+r(hip,BY)+' C'+r(hip-4,388)+' '+r(wa,372)+' '+r(wa+4,352)+' C'+r(bu,320)+' '+r(bu+4,296)+' '+r(sh-14,276)+' C'+r(sh-4,266)+' '+r(sh+2,252)+' '+r(sh-4,240)+' C'+r(sh-16,218)+' '+r(46,208)+' '+r(21,205)+'Z';
 /* 소매: 어깨 선에서 매끈하게 이어져 아래로 (바깥선은 소매 끝으로 갈수록 살짝 모임) */
 const sleevePath=s=>{const x=v=>(CX+s*v);return'M'+x(sh-30)+',224 C'+x(sh-10)+',226 '+x(sh+10)+',236 '+x(sh+10)+',258 C'+x(sh+12)+',296 '+x(sh+6)+',350 '+x(sh-tp)+','+BY+' L'+x(sh-tp-32)+','+BY+' C'+x(sh-34)+',356 '+x(sh-32)+',314 '+x(sh-22)+',284 C'+x(sh-16)+',268 '+x(sh-16)+',250 '+x(sh-30)+',224Z'};
 const LIFT=s=>s.replace(/(<svg[^>]*>)(<defs>[\s\S]*?<\/defs>)?/,(m,a,b)=>a+(b||'')+'<g transform="translate(0 -10)">').replace(/<\/svg>$/,'</g></svg>');
 const bodyBackSVG0=svg('<path d="'+torsoPath()+'" fill="'+rigMix(clothD,'#000',.4)+'"/><path d="'+sleevePath(1)+'" fill="'+rigMix(clothD,'#000',.4)+'"/><path d="'+sleevePath(-1)+'" fill="'+rigMix(clothD,'#000',.4)+'"/>');
 const bodyBackSVG=LIFT(bodyBackSVG0);
 const lap=robe?{w:62,v:330}:{w:44,v:308};
 const torsoDefs=lg('tc',0,0,1,0,[[0,clothL],[.4,cloth],[.85,clothD],[1,rigMix(clothD,'#000',.3)]])+lg('tsk',0,0,0,1,[[0,skin],[1,skS]])+lg('tfade',0,0,0,1,[[0,'#000',0],[.6,'#000',0],[1,'#000',.32]])+blur('bl3',3)+blur('bl6',6)+
  lg('shirtg',0,0,0,1,[[0,shirt],[1,shirtS]])+rg('bust',.5,.4,.62,[[0,'#fff',.10],[1,'#fff',0]]);
 const bust=bz>0?['-1','1'].map(s=>
   '<ellipse cx="'+(CX+s*24)+'" cy="298" rx="22" ry="17" fill="url(#'+U('bust')+')"/>'+
   '<path d="M'+(CX+s*6)+','+(314+bz*4)+' C'+(CX+s*22)+','+(326+bz*5)+' '+(CX+s*42)+','+(320+bz*4)+' '+(CX+s*50)+','+(304)+'" fill="none" stroke="#000" stroke-opacity="'+(.12+bz*.06)+'" stroke-width="6" stroke-linecap="round" filter="url(#'+U('bl3')+')"/>').join(''):'';
 const waistDart=bz>0?['-1','1'].map(s=>'<path d="M'+(CX+s*30)+',318 C'+(CX+s*34)+',336 '+(CX+s*(wa-2))+',352 '+(CX+s*(wa-4))+',380" fill="none" stroke="'+clothLine+'" stroke-width="1.3" opacity=".5"/>').join(''):'';
 const torsoSVG=LIFT(svg(
  '<path d="M'+(CX-15)+',160 L'+(CX-15)+',208 C'+(CX-8)+',218 '+(CX+8)+',218 '+(CX+15)+',208 L'+(CX+15)+',160Z" fill="url(#'+U('tsk')+')"/>'+
  /* 턱이 목에 드리운 셀 그림자 */
  '<path d="M'+(CX-15)+',176 C'+(CX-6)+',194 '+(CX+6)+',194 '+(CX+15)+',176 L'+(CX+15)+',160 L'+(CX-15)+',160Z" fill="'+skD+'" opacity=".55"/>'+
  '<path d="'+torsoPath()+'" fill="url(#'+U('tc')+')"/>'+
  '<path d="M'+(CX-22)+',205 L'+(CX+22)+',205 L'+(CX+(robe?28:18))+',250 L'+(CX+(robe?18:7))+','+(lap.v-30)+' L'+(CX-(robe?18:7))+','+(lap.v-30)+' L'+(CX-(robe?28:18))+',250Z" fill="url(#'+U('shirtg')+')"/>'+
  '<path d="M'+(CX-20)+',205 C'+(CX-8)+',218 '+(CX+8)+',218 '+(CX+20)+',205 L'+(CX+20)+',212 C'+(CX+6)+',226 '+(CX-6)+',226 '+(CX-20)+',212Z" fill="'+skD+'" opacity=".4"/>'+
  '<path d="M'+(CX-5)+',224 L'+(CX+5)+',224 L'+(CX+3.4)+',234 L'+(CX+8)+',294 L'+CX+','+(lap.v-2)+' L'+(CX-8)+',294 L'+(CX-3.4)+',234Z" fill="'+tie+'"/>'+
  '<path d="M'+(CX-1)+',238 L'+(CX+3.4)+',236 L'+(CX+6)+',290 L'+(CX+1)+',298Z" fill="#fff" opacity=".10"/>'+
  '<path d="M'+(CX-22)+',203 L'+(CX-lap.w)+',262 L'+(CX-lap.w+9)+',282 L'+(CX-9)+','+lap.v+' L'+(CX-6)+',250Z" fill="'+rigMix(cloth,clothL,.35)+'" stroke="'+clothLine+'" stroke-width="1" stroke-linejoin="round"/>'+
  '<path d="M'+(CX+22)+',203 L'+(CX+lap.w)+',262 L'+(CX+lap.w-9)+',282 L'+(CX+9)+','+lap.v+' L'+(CX+6)+',250Z" fill="'+rigMix(cloth,clothD,.2)+'" stroke="'+clothLine+'" stroke-width="1" stroke-linejoin="round"/>'+
  '<path d="M'+(CX-22)+',205 L'+(CX-lap.w+2)+',262" stroke="#fff" stroke-opacity=".2" stroke-width="1.4" fill="none"/>'+
  (robe?'':'<circle cx="'+CX+'" cy="'+(lap.v+14)+'" r="2.6" fill="'+clothD+'"/><circle cx="'+(CX-.6)+'" cy="'+(lap.v+13.4)+'" r="1" fill="#fff" opacity=".4"/>')+
  '<path d="M'+CX+','+(lap.v+4)+' L'+CX+','+BY+'" stroke="'+clothLine+'" stroke-width="1.4" opacity=".5"/>'+
  bust+waistDart+
  (R.pin==='bunny'?'<g transform="translate('+(CX-lap.w+22)+' '+(lap.v-28)+')"><ellipse cx="-2.5" cy="-6" rx="1.8" ry="5" fill="#e8eaf2"/><ellipse cx="2.5" cy="-6" rx="1.8" ry="5" fill="#e8eaf2"/><ellipse cx="0" cy="0" rx="4.6" ry="4.2" fill="#e8eaf2"/><circle cx="-1.6" cy="-.4" r=".8" fill="#222"/><circle cx="1.6" cy="-.4" r=".8" fill="#222"/></g>':'')+
  (R.pin==='scale'?'<g transform="translate('+(CX-lap.w+20)+' '+(lap.v-26)+')" stroke="#f1c75b" stroke-width="1.5" fill="none"><path d="M0,-7 L0,6 M-6,-4 L6,-4 M-6,-4 L-8,2 L-4,2 Z M6,-4 L4,2 L8,2 Z"/></g>':'')+
  '<path d="'+torsoPath()+'" fill="url(#'+U('tfade')+')"/>',torsoDefs));
 const slDefs=lg('sl',0,0,1,0,[[0,clothL],[.5,cloth],[1,clothD]])+lg('sr',1,0,0,0,[[0,clothL],[.5,cloth],[1,clothD]])+blur('bl2',2)+lg('tfade2',0,0,0,1,[[0,'#000',0],[.6,'#000',0],[1,'#000',.32]]);
 const sleeveFx=s=>{const x=v=>(CX+s*v);return''+
  '<path d="'+sleevePath(s)+'" fill="url(#'+U('tfade2')+')"/>'+
  '<path d="M'+x(sh-30)+',226 C'+x(sh-8)+',228 '+x(sh+8)+',238 '+x(sh+8)+',256" fill="none" stroke="#fff" stroke-opacity=".26" stroke-width="3" stroke-linecap="round" filter="url(#'+U('bl2')+')"/>'+   // 어깨 둥근 하이라이트
  '<path d="M'+x(sh-20)+',286 C'+x(sh-26)+',320 '+x(sh-26)+',350 '+x(sh-tp-26)+',394" fill="none" stroke="#000" stroke-opacity=".28" stroke-width="5" filter="url(#'+U('bl2')+')"/>'+   // 팔과 몸 사이 그림자
  '<path d="M'+x(sh-6)+',322 C'+x(sh-14)+',326 '+x(sh-24)+',326 '+x(sh-30)+',322" stroke="'+clothLine+'" stroke-width="1.2" fill="none" opacity=".5"/>'+
  '<path d="M'+x(sh-4)+',344 C'+x(sh-12)+',348 '+x(sh-22)+',348 '+x(sh-28)+',344" stroke="'+clothLine+'" stroke-width="1" fill="none" opacity=".4"/>'+
  '<path d="'+sleevePath(s)+'" fill="none" stroke="'+clothLine+'" stroke-width="1" opacity=".7"/>'};
 const sleevesSVG=LIFT(svg('<path d="'+sleevePath(-1)+'" fill="url(#'+U('sl')+')"/><path d="'+sleevePath(1)+'" fill="url(#'+U('sr')+')"/>'+sleeveFx(-1)+sleeveFx(1),slDefs));

 /* ---------- 머리 레이어 ---------- */
 const earSVG=svg(['-1','1'].map(s=>'<ellipse cx="'+(CX+s*(J.hw+1))+'" cy="124" rx="6" ry="11" fill="'+skS+'"/><ellipse cx="'+(CX+s*(J.hw+2))+'" cy="125" rx="2.8" ry="6.4" fill="'+blush+'" opacity=".5"/>').join(''));
 const faceDefs=lg('fg',0,0,0,1,[[0,rigMix(skin,'#fff',.1)],[.65,skin],[1,rigMix(skin,skS,.7)]])+lg('fside',0,0,1,0,[[0,'#000',0],[.64,'#000',0],[1,'#b0655a',.22]])+
  '<clipPath id="'+U('fc')+'"><path d="'+facePath+'"/></clipPath>'+blur('bl4',4)+rg('cheek',.5,.5,.5,[[0,blush,R.blushA],[1,blush,0]]);
 const faceSVG=svg(
  '<path d="'+facePath+'" fill="url(#'+U('fg')+')"/>'+
  '<g clip-path="url(#'+U('fc')+')">'+
   '<rect x="0" y="30" width="268" height="170" fill="url(#'+U('fside')+')"/>'+
   '<path d="M'+(CX-60)+',150 C'+(CX-40)+',182 '+(CX+40)+',182 '+(CX+60)+',150 L'+(CX+60)+',200 L'+(CX-60)+',200Z" fill="'+skD+'" opacity=".22" filter="url(#'+U('bl4')+')"/>'+
   /* 앞머리가 이마에 드리우는 '딱 떨어지는' 셀 그림자 */
   '<path d="'+H.bangs+'" fill="'+skS+'" opacity=".55" transform="translate(2 9)"/>'+
   '<ellipse cx="'+(CX-34)+'" cy="148" rx="16" ry="9" fill="url(#'+U('cheek')+')"/><ellipse cx="'+(CX+34)+'" cy="148" rx="16" ry="9" fill="url(#'+U('cheek')+')"/>'+
   '<path d="M'+(CX+2)+',141 C'+(CX+4)+',145 '+(CX+3)+',147 '+(CX-1)+',147" fill="none" stroke="'+skLine+'" stroke-width="1.3" stroke-linecap="round" opacity=".6"/>'+
   '<path d="M'+(CX-50)+',106 C'+(CX-48)+',132 '+(CX-40)+',152 '+(CX-26)+',168" fill="none" stroke="#fff" stroke-opacity=".3" stroke-width="2" stroke-linecap="round"/>'+
  '</g>'+
  '<path d="'+facePath+'" fill="none" stroke="'+skLine+'" stroke-width="1.1" opacity=".7"/>',faceDefs);
 /* 눈: 한 번 만들고 속성만 바꿔 표정·시선·깜빡임 */
 const EY=122,EX=25.5,EW=R.eyeW*1.08,EH=R.eyeH*1.16;
 const eyeShape='M-16,3 C-14,-10 -4,-17 6,-16 C13,-15 18,-8 19,-3 C16,7 6,11 -3,10 C-10,9 -15,6 -16,3Z';
 const eyeDefs=rg('iris',.5,.3,.85,[[0,R.iris],[.55,rigMix(R.iris,R.iris2,.4)],[1,R.iris2]])+lg('irisb',0,0,0,1,[[0,'#000',.5],[.5,'#000',0]])+lg('lidg',0,0,0,1,[[0,skS],[1,skin]])+
  '<clipPath id="'+U('ec')+'"><path d="'+eyeShape+'"/></clipPath>';
 const eyeUnit=side=>{const g=side===1?'R':'L';
  return'<g transform="translate('+(CX+side*EX)+' '+EY+') scale('+(side*EW)+' '+EH+')"><g transform="rotate('+(-R.tilt)+')">'+
   '<path d="'+eyeShape+'" fill="#fbfbff"/>'+
   '<g clip-path="url(#'+U('ec')+')">'+
    '<path d="M-18,-18 L22,-18 L22,-3 C10,-6 -6,-6 -18,-3Z" fill="#2a2a50" opacity=".26"/>'+
    '<g class="'+U('iris'+g)+'"><ellipse cx="2" cy="-1" rx="13" ry="15" fill="url(#'+U('iris')+')"/><ellipse cx="2" cy="-1" rx="13" ry="15" fill="url(#'+U('irisb')+')"/>'+
     '<g stroke="'+rigMix(R.iris,'#000',.35)+'" stroke-width=".8" opacity=".5" fill="none"><path d="M2,-1 L-8,-8 M2,-1 L-11,-1 M2,-1 L-8,6 M2,-1 L12,-8 M2,-1 L13,-1 M2,-1 L12,6 M2,-1 L2,-13"/></g>'+
     '<ellipse cx="2" cy="6" rx="8.4" ry="5.6" fill="'+R.iris2+'" opacity=".55"/><ellipse cx="2" cy="-1" rx="5.2" ry="7.4" fill="'+(P.pupil||'#08060a')+'"/>'+
     '<ellipse cx="2" cy="-1" rx="13" ry="15" fill="none" stroke="'+rigMix(R.iris,'#000',.55)+'" stroke-width="1.3"/>'+
     '<ellipse cx="-3" cy="-8.4" rx="4.8" ry="5.4" fill="#fff"/><ellipse cx="7.8" cy="5" rx="2.2" ry="2.2" fill="#fff" opacity=".95"/>'+
     (R.star?'<path d="M6,-5 L7,-2.4 L9.6,-1.6 L7,-.8 L6,1.8 L5,-.8 L2.4,-1.6 L5,-2.4Z" fill="#fff" opacity=".9"/>':'<circle cx="-5.6" cy="1.6" r="1.1" fill="#fff" opacity=".7"/>')+
    '</g>'+
    '<g class="'+U('wet'+g)+'" opacity="0"><path d="M-16,3 C-10,10 -3,11 6,11 C14,11 19,6 20,-3 C15,1 10,4 4,5 C-4,6 -10,5 -16,3Z" fill="#bfe8ff" opacity=".7"/><path d="M-14,4 C-8,9 0,10 8,9 C14,8 17,5 18,2" fill="none" stroke="#fff" stroke-width="1.6" opacity=".9"/><ellipse cx="-8" cy="6" rx="2.6" ry="1.6" fill="#fff" opacity=".9"/><ellipse cx="10" cy="4.6" rx="2" ry="1.3" fill="#fff" opacity=".9"/></g>'+
    '<rect class="'+U('lid'+g)+'" x="-24" y="-30" width="52" height="30" fill="url(#'+U('lidg')+')"/>'+
   '</g>'+
   /* 속눈썹은 검정이 아니라 어두운 갈색·남색으로 가늘게, 바깥 끝만 살짝 길게 */
   '<path class="'+U('lash'+g)+'" d="M-17,3 C-15,-10 -4,-18 6,-17 C14,-16 19,-9 20.6,-3 L18.8,-1.6 C16.8,-8 12.4,-13.6 6,-14.6 C-3,-15.2 -11,-9.4 -14.4,3Z" fill="'+lash+'"/>'+
   '<path d="M17.4,-8 C20.6,-9 23.6,-8.6 26,-11 C25,-6.6 22.6,-2.8 19.4,-.6Z" fill="'+lash+'"/>'+
   '<path d="M-15,5 C-9,10 -2,11.4 6,11 C13,10.6 17.6,6 19.4,0" fill="none" stroke="'+rigMix(lash,'#c08a86',.5)+'" stroke-width=".9" opacity=".7"/>'+
   '<path d="M-14,-19 C-6,-23.6 8,-23.4 17,-16" fill="none" stroke="'+skLine+'" stroke-width="1" opacity=".5"/>'+
   '<path class="'+U('bag'+g)+'" d="M-12,12 C-4,16 8,16 16,10" fill="none" stroke="'+(P.eye_bag||skD)+'" stroke-width="2.2" opacity="0" stroke-linecap="round"/>'+
  '</g></g>'};
 const eyesSVG=svg(eyeUnit(1)+eyeUnit(-1),eyeDefs);
 const browC=rigMix(P.brow||hc,hl,.25);
 const browSVG=svg(['R','L'].map((g,i)=>{const s=i?-1:1;return'<g transform="translate('+(CX+s*EX)+' '+(EY-30)+') scale('+s+' 1)"><g class="'+U('brow'+g)+'"><path d="M-14,3 C-8,-3.4 6,-5.4 17,-1.4 C8,-3 -6,-1.4 -14,3Z" fill="'+browC+'" stroke="'+browC+'" stroke-width="2.2" stroke-linejoin="round"/></g></g>'}).join(''));
 /* 입: 작고 귀엽게 (전체를 .82 배) */
 const mc=P.mouth||'#a85a62',tg=P.tongue||'#e8909a',mcD=rigMix(mc,'#3a1018',.55);
 const MOUTHS={
  smile:'<path d="M122,160 C128,168 140,168 146,160 C140,163.4 128,163.4 122,160Z" fill="'+mc+'"/><path d="M121.4,159.6 C128,165 140,165 146.6,159.6" fill="none" stroke="'+mcD+'" stroke-width="1.5" stroke-linecap="round"/>',
  grin:'<path d="M119,160 C125,158 140,153 151,151 C150,166 126,172 119,160Z" fill="'+mcD+'"/><path d="M121,160 C128,158 142,155 149,153 C146,158 128,162 121,160Z" fill="#fff"/><ellipse cx="136" cy="167" rx="7" ry="3" fill="'+tg+'"/><path d="M119,160 C125,158 140,153 151,151 C150,166 126,172 119,160Z" fill="none" stroke="'+mcD+'" stroke-width="1.4" stroke-linejoin="round"/>',
  smirk:'<path d="M123,162 C129,164 140,163 148,156" fill="none" stroke="'+mcD+'" stroke-width="1.8" stroke-linecap="round"/><path d="M130,163.4 C136,166 142,165 147,159.6 C142,162.6 136,163.4 130,163.4Z" fill="'+mc+'"/>',
  open:'<ellipse cx="134" cy="162" rx="6.6" ry="8.2" fill="'+mcD+'"/><ellipse cx="134" cy="166" rx="4.4" ry="3.2" fill="'+tg+'"/><path d="M128.6,155.8 C132,154 136,154 139.4,155.8" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"/><ellipse cx="134" cy="162" rx="6.6" ry="8.2" fill="none" stroke="'+mcD+'" stroke-width="1.3"/>',
  flat:'<path d="M125,162 C130,163.2 138,163.2 143,162" fill="none" stroke="'+mcD+'" stroke-width="1.9" stroke-linecap="round"/>',
  weary:'<path d="M125,163.6 C130,161.4 138,161.4 143,163.6" fill="none" stroke="'+mcD+'" stroke-width="1.9" stroke-linecap="round"/>',
  hmm:'<path d="M122,164 C125,160.4 128.6,160.4 131,163.4 C133.6,166.6 137,166.6 139.6,163 C141.4,160.6 144.4,161 146,163.8" fill="none" stroke="'+mcD+'" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/>',
  pout:'<path d="M126,163.6 C129,160.8 139,160.8 142,163.6 C139,165.8 129,165.8 126,163.6Z" fill="'+mc+'"/><path d="M126,163.6 C131,162 137,162 142,163.6" fill="none" stroke="'+mcD+'" stroke-width="1.2"/>',
  wail:'<path d="M121,168 C124,157 144,157 147,168 C141,163.6 127,163.6 121,168Z" fill="'+mcD+'"/><path d="M123.6,167 C129,163.6 139,163.6 144.4,167" fill="none" stroke="'+tg+'" stroke-width="2.4" stroke-linecap="round"/><path d="M121,168 C124,157 144,157 147,168" fill="none" stroke="'+mcD+'" stroke-width="1.4" stroke-linecap="round"/>',
  grit:'<path d="M122,158.6 C128,156.4 140,156.4 146,158.6 C146,166 141,168.6 134,168.6 C127,168.6 122,166 122,158.6Z" fill="#fff" stroke="'+mcD+'" stroke-width="1.5" stroke-linejoin="round"/><path d="M123.6,162.6 L144.4,162.6 M129,157.6 V168 M134,157 V168.6 M139,157.6 V168" stroke="'+mcD+'" stroke-width="1" fill="none" opacity=".75"/>'};
 const mouthSVG=svg('<g transform="translate(134 160) scale(.9) translate(-134 -160)">'+Object.keys(MOUTHS).map(k=>'<g class="'+U('m_'+k)+'" style="display:none">'+MOUTHS[k]+'</g>').join('')+'</g>');
 /* 효과 */
 const fxDefs=lg('tear',0,0,0,1,[[0,'#e8f8ff',.95],[1,'#8ccaf2',.85]]);
 const tearPath=s=>'<path d="M'+(CX+s*29)+',134 C'+(CX+s*32)+',144 '+(CX+s*35)+',152 '+(CX+s*33)+',162 C'+(CX+s*32)+',170 '+(CX+s*27)+',170 '+(CX+s*27)+',162 C'+(CX+s*27)+',152 '+(CX+s*25)+',144 '+(CX+s*24)+',134Z" fill="url(#'+U('tear')+')" stroke="#7ab8e6" stroke-width=".9"/><ellipse cx="'+(CX+s*30)+'" cy="152" rx="1.4" ry="3.6" fill="#fff" opacity=".85"/>';
 const fxSVG=svg(
  '<g class="'+U('fx_blush')+'" style="display:none"><g stroke="#e0707a" stroke-width="1.6" stroke-linecap="round" opacity=".7"><path d="M'+(CX-44)+',146 l-3,7 M'+(CX-37)+',148 l-3,7 M'+(CX-30)+',149 l-3,7 M'+(CX+30)+',149 l-3,7 M'+(CX+37)+',148 l-3,7 M'+(CX+44)+',146 l-3,7"/></g><ellipse cx="'+(CX-35)+'" cy="150" rx="17" ry="9" fill="#ff7d86" opacity=".26"/><ellipse cx="'+(CX+35)+'" cy="150" rx="17" ry="9" fill="#ff7d86" opacity=".26"/></g>'+
  '<g class="'+U('fx_tears')+'" style="display:none">'+tearPath(1)+tearPath(-1)+'</g>'+
  '<g class="'+U('fx_gloom')+'" style="display:none" stroke="#3a3a6a" stroke-width="3" stroke-linecap="round" opacity=".45"><path d="M'+(CX-44)+',60 v34 M'+(CX-28)+',56 v40 M'+(CX-12)+',54 v34 M'+(CX+8)+',54 v38 M'+(CX+26)+',56 v40 M'+(CX+42)+',60 v34"/></g>',fxDefs);
 const accSVG=svg(
  '<g class="'+U('fx_sweat')+'" style="display:none"><path d="M'+(CX+52)+',72 C'+(CX+58)+',82 '+(CX+62)+',88 '+(CX+57)+',93 C'+(CX+52)+',97 '+(CX+46)+',91 '+(CX+49)+',84 C'+(CX+50)+',80 '+(CX+51)+',76 '+(CX+52)+',72Z" fill="url(#'+U('tear')+')" stroke="#6fb4e6" stroke-width="1.1"/><ellipse cx="'+(CX+51)+'" cy="87" rx="1.3" ry="2.4" fill="#fff"/></g>'+
  '<g class="'+U('fx_vein')+'" style="display:none" fill="none" stroke="#e23a3a" stroke-width="3" stroke-linecap="round"><path d="M'+(CX+36)+',56 l10,4 M'+(CX+38)+',68 l10,-4 M'+(CX+44)+',58 l-2,12 M'+(CX+52)+',62 l-12,2" transform="translate(2 40) scale(1.1)"/></g>',fxDefs);
 /* 옆머리·앞머리 */
 const hairDefs=lg('hf',0,0,1,1,[[0,hl],[.3,hmid],[.6,hc],[1,hs]])+lg('hfs',0,0,0,1,[[0,'#000',0],[1,'#000',.32]])+lg('ring',0,0,1,0,[[0,hl,0],[.3,'#fff',.55],[.7,'#fff',.5],[1,hl,0]]);
 const sideSVG=svg('<path d="'+H.sideL+'" fill="url(#'+U('hf')+')"/><path d="'+H.sideR+'" fill="url(#'+U('hf')+')"/>'+
  '<path d="'+H.sideL+'" fill="url(#'+U('hfs')+')"/><path d="'+H.sideR+'" fill="url(#'+U('hfs')+')"/>'+
  '<path d="'+H.sideL+'" fill="none" stroke="'+hLine+'" stroke-width="1" opacity=".55"/><path d="'+H.sideR+'" fill="none" stroke="'+hLine+'" stroke-width="1" opacity=".55"/>',hairDefs);
 const bangsSVG=svg(
  '<path d="'+H.bangs+'" fill="url(#'+U('hf')+')"/>'+
  '<path d="'+H.hi+'" fill="none" stroke="url(#'+U('ring')+')" stroke-width="7" stroke-linecap="round" opacity=".85"/>'+
  H.strands.map(d=>'<path d="'+d+'" fill="none" stroke="'+hs+'" stroke-width="1.3" opacity=".4" stroke-linecap="round"/>').join('')+
  '<path d="'+H.bangs+'" fill="none" stroke="'+hLine+'" stroke-width="1.1" opacity=".7" stroke-linejoin="round"/>',hairDefs);

 /* ---------- DOM 조립 ---------- */
 el.innerHTML='';
 const rig=document.createElement('div');rig.className='rig';
 const L=(z,s)=>'<div class="rl" style="--z:'+z+'">'+s+'</div>';
 rig.innerHTML='<div class="rb">'+L(Z.hairBack,hairBackSVG)+L(Z.bodyBack,bodyBackSVG)+L(Z.torso,torsoSVG)+(opts.noArms?'':L(Z.sleeves,sleevesSVG))+'</div>'+
  '<div class="rh">'+L(Z.ears,earSVG)+L(Z.face,faceSVG)+L(Z.eyes,eyesSVG)+L(Z.brows,browSVG)+L(Z.mouth,mouthSVG)+L(Z.fx,fxSVG)+L(Z.side,sideSVG)+L(Z.bangs,bangsSVG)+L(Z.acc,accSVG)+'</div>';
 el.appendChild(rig);const wh=el.closest&&el.closest('.who');if(wh)wh.classList.add('rigged');
 const rb=rig.querySelector('.rb'),rh=rig.querySelector('.rh');
 const q=n=>rig.querySelector('.'+U(n));
 const hairEls=[...rig.querySelectorAll('.rl')].filter((x,i)=>i===0||/hf|ring/.test(x.innerHTML.slice(0,400)));
 const S={lid:0,gx:0,gy:0,brow:0,bs:0,mouth:R.mouth,baseMouth:R.mouth,fx:'',wet:0,talk:false,blink:0,smug:0};
 const F={key:key,state:S,defaultMouth:R.mouth,expr:'neutral',isRig:true,colors:{cloth:cloth,clothL:clothL,clothD:clothD,skin:skin}};
 const cur={yaw:0,pitch:0,tilt:0,byaw:0},tgt={yaw:0,pitch:0,tilt:0,byaw:0};
 function paintEyes(){
  const sleepy=R.sleepy||0,lid=Math.min(1,Math.max(0,S.lid+sleepy)),bl=Math.max(lid,S.blink);
  ['R','L'].forEach(g=>{const lidEl=q('lid'+g),iris=q('iris'+g),wet=q('wet'+g),lashEl=q('lash'+g),bag=q('bag'+g);
   lidEl.setAttribute('y',-16+bl*27-30);
   lashEl.setAttribute('transform','translate(0 '+(bl*13.5)+') scale(1 '+(1-bl*.35)+')');
   iris.setAttribute('transform','translate('+(Math.max(-3.2,Math.min(3.2,S.gx))*1.6)+' '+(Math.max(-3,Math.min(3,S.gy))*1.4)+')');
   wet.setAttribute('opacity',S.wet?1:0);bag.setAttribute('opacity',sleepy>0?.5:0)});
  ['R','L'].forEach((g,i)=>{const b=q('brow'+g),y=S.brow*1.6+(S.smug&&i===0?-3:0),rot=-S.bs*7*(S.smug&&i===0?0:1);b.setAttribute('transform','translate(0 '+y+') rotate('+rot+' 2 2)')});
  Object.keys(MOUTHS).forEach(k=>{const m=q('m_'+k);if(m)m.style.display=(k===S.mouth)?'':'none'});
  ['blush','sweat','tears','vein','gloom'].forEach(k=>{const e=q('fx_'+k);if(e)e.style.display=S.fx.split(',').indexOf(k)>=0?'':'none'});
 }
 F.redraw=paintEyes;
 F.setLid=v=>{S.lid=v};F.setGaze=(a,b)=>{S.gx=a;S.gy=b};F.setBrow=d=>{S.brow=d};F.showMouth=n=>{S.mouth=MOUTHS[n]?n:S.baseMouth};
 F.setExpr=function(name){const E=(D.expr||{})[name]||(D.expr||{}).neutral||{};
  S.baseMouth=(E.mouth&&MOUTHS[E.mouth])?E.mouth:R.mouth;S.mouth=S.talk?'open':S.baseMouth;
  S.brow=E.brow||0;S.bs=(E.bs!=null)?E.bs:((E.brow||0)>0?E.brow*.8:0);S.lid=E.lid||0;S.gx=E.gx||0;S.gy=E.gy||0;
  const fx=E.fx||[];S.fx=fx.join(',');S.wet=fx.indexOf('welling')>=0||fx.indexOf('tears')>=0?1:0;S.smug=E.smug?1:0;
  tgt.tilt=(E.tilt||0);tgt.pitch=(E.pitch||0);F.expr=name;paintEyes()};
 /* 시선 방향: 얼굴은 최대 약 20° 만 돌아가고 몸은 거의 그대로 (일그러짐 방지) */
 F.setYaw=function(deg){tgt.yaw=Math.max(-24,Math.min(24,deg*.55));tgt.byaw=deg*.1};
 F.setPitch=function(d){tgt.pitch=d};F.setTilt=function(d){tgt.tilt=d};
 let tmT=null;
 F.setTalking=function(on){S.talk=!!on;if(on&&!tmT){let o=false;tmT=setInterval(()=>{o=!o;S.mouth=o?'open':S.baseMouth;paintEyes()},210)}else if(!on&&tmT){clearInterval(tmT);tmT=null;S.mouth=S.baseMouth;paintEyes()}};
 const t0=Math.random()*10,bl=(C.motion&&C.motion.blink_s)||4.8;let nextBlink=1.5+Math.random()*bl,blinkT=-1;
 F.tick=function(now){
  const t=now/1000+t0,k=.09;
  cur.yaw+=(tgt.yaw-cur.yaw)*k;cur.byaw+=(tgt.byaw-cur.byaw)*k;cur.pitch+=(tgt.pitch-cur.pitch)*k;cur.tilt+=(tgt.tilt-cur.tilt)*k;
  const br=Math.sin(t*1.5)*.5+.5,talkBob=S.talk?Math.sin(t*14)*.6:0;
  const u=rig.clientWidth/268||1;rig.style.setProperty('--u',u+'px');
  rb.style.transform='translateY('+(br*-1.2*u).toFixed(2)+'px) rotateY('+cur.byaw.toFixed(2)+'deg)';
  rh.style.transformOrigin=(CX/268*100)+'% '+(206/400*100)+'%';
  rh.style.transform='translateY('+((br*-2+talkBob)*u).toFixed(2)+'px) rotateY('+cur.yaw.toFixed(2)+'deg) rotateX('+(cur.pitch*.8+Math.sin(t*.9)*.6).toFixed(2)+'deg) rotateZ('+(cur.tilt+Math.sin(t*.7)*.45).toFixed(2)+'deg)';
  hairEls.forEach((h,i)=>{h.style.transform='translateZ('+(+h.style.getPropertyValue('--z')*u).toFixed(1)+'px) rotateZ('+(Math.sin(t*1.1+i*.9)*.4).toFixed(2)+'deg)'});
  if(blinkT<0&&t>nextBlink)blinkT=0;
  if(blinkT>=0){blinkT+=.034;const p=blinkT/.22;S.blink=p<.5?p*2:Math.max(0,2-p*2);if(blinkT>.22){blinkT=-1;S.blink=0;nextBlink=t+bl*(.6+Math.random()*.9)}paintEyes()}
 };
 rig.__F=F;RIG_LIST.push(F);
 if(!RIG_LOOP){RIG_LOOP=1;const loop=now=>{if(!document.hidden)for(const f of RIG_LIST)f.tick(now);requestAnimationFrame(loop)};requestAnimationFrame(loop)}
 F.rigEl=rig;F.setExpr('neutral');paintEyes();
 if(typeof vrmAttach==='function'&&D.cast&&D.cast[key])vrmAttach(el,F,D.cast[key],opts);
 return F}
"""
