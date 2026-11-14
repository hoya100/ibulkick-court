"""rig3d.py — 진짜 3D 아바타 뷰어 (Three.js + three-vrm, WebGL).

  ■ 왜 이 방식인가
    서브컬처 3D 게임의 캐릭터는 '코드로 그린 도형'이 아니라, 모델러가 만든 3D 모델(+툰 셰이딩)을 렌더링한 것입니다.
    웹에서 그 표준이 VRM(애니풍 3D 아바타 포맷)입니다. VRoid Studio(무료)로 참고 이미지 같은 얼굴·머리·체형을 마우스로 빚어
    .vrm 파일로 내보내고, 이 뷰어가 불러와서 다음을 해 줍니다.
      · MToon 툰 셰이딩 + 외곽선 + 림라이트 (부드러운 빛과 음영)     · 진짜 3D 머리/목/몸 회전 (종이장 현상 없음)
      · 모델에 들어 있는 표정(웃음/화남/슬픔/놀람/깜빡임/입모양)       · 시선(눈동자가 대상을 따라감), 호흡, 머리카락·옷 물리(SpringBone)
      · 팔 IK (판사가 서류를 드는 장면, 변호사가 손 흔드는 장면)       · 눈물·홍조 이펙트

  ■ 모델 파일 연결 방법 (코드 수정은 characters.py 맨 위 한 줄)
    1) VRoid Studio 에서 캐릭터 3명을 만들고 [내보내기 → VRM] (폴리곤/텍스처 줄이기 옵션 ON 권장, 파일당 20MB 이하)
    2) GitHub 저장소에  assets/models/judge.vrm, prosecutor.vrm, lawyer.vrm  으로 올림
    3) characters.py 의 MODEL_BASE_URL 에 다음 형식의 주소를 넣음
         "https://cdn.jsdelivr.net/gh/<깃허브아이디>/<저장소>@main/assets/models"
         (또는 "https://raw.githubusercontent.com/<깃허브아이디>/<저장소>/main/assets/models")
    → 끝. 모델이 없거나 불러오기에 실패하면 지금의 벡터 캐릭터가 자동으로 대신 나옵니다(게임은 멈추지 않음).
    ※ 사람 얼굴이 닮은 모델·다른 작품 캐릭터는 쓰지 마세요. 직접 만든 모델이나 상업 이용이 허락된(CC0 등) 모델만 쓰세요.

  ■ 라이브러리 버전: 아래 THREE_VER / VRM_VER 만 바꾸면 됩니다 (jsDelivr CDN 에서 브라우저가 직접 받음).
"""

THREE_VER = "0.160.0"
VRM_VER = "2.1.0"

RIG3D_HEAD = (
    '<script>(function(){var L=window.__rig3dLines=[],P=null;window.rig3dLog=function(m,bad){var t=((performance.now()/1000)|0)+"s ";L.push({m:t+m,bad:!!bad});(bad?console.error:console.log)("[rig3d] "+m);window.rig3dRender()};'
    'window.rig3dRender=function(){if(!window.RIG3D_DEBUG||!document.body)return;if(!P){P=document.createElement("div");P.id="rig3d-dbg";P.style.cssText="position:fixed;left:4px;top:4px;z-index:2147483647;max-width:92%;max-height:46%;overflow:auto;background:#000c;color:#9f9;font:11px/1.35 monospace;padding:5px 7px;border-radius:6px;pointer-events:none;white-space:pre-wrap";document.body.appendChild(P)}'
    'P.innerHTML=L.map(function(x){return "<div style=\'color:"+(x.bad?"#ff8a8a":"#9f9")+"\'>"+String(x.m).replace(/</g,"&lt;")+"</div>"}).join("")};'
    'document.addEventListener("DOMContentLoaded",function(){window.rig3dRender()})})()</script>\n'
    '<script type="importmap">{"imports":{'
    f'"three":"https://cdn.jsdelivr.net/npm/three@{THREE_VER}/build/three.module.js",'
    f'"three/addons/":"https://cdn.jsdelivr.net/npm/three@{THREE_VER}/examples/jsm/",'
    f'"three/examples/jsm/":"https://cdn.jsdelivr.net/npm/three@{THREE_VER}/examples/jsm/",'
    f'"@pixiv/three-vrm":"https://cdn.jsdelivr.net/npm/@pixiv/three-vrm@{VRM_VER}/lib/three-vrm.module.min.js"'
    '}}</script>\n'
    '<script type="module">\n'
    "/* 모델이 하나라도 설정돼 있을 때만 3D 라이브러리를 받는다 (진행 상황은 rig3dLog 로 화면/콘솔에 남긴다) */\n"
    "const LOG=window.rig3dLog||console.log;let stage='시작';\n"
    "try{\n"
    " const cast=(typeof D!=='undefined'&&D.cast)?D.cast:{};const ms=Object.values(cast).filter(c=>c.rig&&c.rig.model&&c.rig.model.url);\n"
    " window.RIG3D_DEBUG=ms.some(c=>c.rig.model.debug);window.rig3dRender&&window.rig3dRender();\n"
    " LOG('3D 설정 모델 수: '+ms.length+(ms[0]?'  첫 주소: '+ms[0].rig.model.url:'  (characters.py 의 MODEL_BASE_URL 이 비어 있음 → 벡터 캐릭터)'));\n"
    " if(ms.length){\n"
    "  stage='three 불러오기';const THREE=await import('three');LOG('three 로드 OK (r'+THREE.REVISION+')');\n"
    "  stage='GLTFLoader 불러오기';const {GLTFLoader}=await import('three/addons/loaders/GLTFLoader.js');LOG('GLTFLoader 로드 OK');\n"
    "  stage='three-vrm 불러오기';const V=await import('@pixiv/three-vrm');LOG('three-vrm 로드 OK');\n"
    "  window.VRM3D={THREE:THREE,GLTFLoader:GLTFLoader,VRMLoaderPlugin:V.VRMLoaderPlugin,VRMUtils:V.VRMUtils};window.dispatchEvent(new Event('vrm3d-ready'))}\n"
    " else window.dispatchEvent(new Event('vrm3d-fail'));\n"
    "}catch(e){LOG('라이브러리 실패 ['+stage+']: '+(e&&e.message||e),true);window.dispatchEvent(new Event('vrm3d-fail'))}\n"
    "</script>\n"
)

RIG3D_JS = r"""
/* ============ 3D 아바타 (rig3d.py): VRM → Three.js ============ */
(function(){const s=document.createElement('style');s.textContent=`
.vrm3d{position:absolute;inset:0;pointer-events:none;z-index:3}
.vrm3d canvas{position:absolute!important;inset:0!important;width:100%!important;height:100%!important;image-rendering:auto!important;display:block;transform:none!important}
.vrm3d .v3t{position:absolute;width:5.2%;aspect-ratio:1/2.4;border-radius:50% 50% 55% 55%/28% 28% 72% 72%;background:linear-gradient(#f4fcff,#86c6f0);box-shadow:0 0 0 1px #6fb4e699;opacity:0;transform:translate(-50%,0)}
.vrm3d .v3t.on{animation:v3tear 1.7s ease-in infinite}
@keyframes v3tear{0%{transform:translate(-50%,-40%) scaleY(.4);opacity:0}22%{opacity:.95}100%{transform:translate(-50%,380%) scaleY(1.15);opacity:0}}
.vrm3d .v3b{position:absolute;width:17%;aspect-ratio:2/1;border-radius:50%;background:radial-gradient(#ff7d86aa,#ff7d8600 70%);opacity:0;transform:translate(-50%,-50%);transition:opacity .3s}
.vrm3d .v3b.on{opacity:1}
`;document.head.appendChild(s)})();

let RIG3D_P=null;const RIG3D_LIST=[];let RIG3D_LOOP=0;
function rig3dOn(C){return !!(C&&C.rig&&C.rig.model&&C.rig.model.url)}
function rig3dReady(){
 if(RIG3D_P)return RIG3D_P;
 RIG3D_P=new Promise(res=>{
  if(window.VRM3D)return res(window.VRM3D);
  const to=setTimeout(()=>{(window.rig3dLog||console.warn)('라이브러리 대기 30초 초과',true);res(null)},30000);
  window.addEventListener('vrm3d-ready',()=>{clearTimeout(to);res(window.VRM3D)},{once:true});
  window.addEventListener('vrm3d-fail',()=>{clearTimeout(to);res(null)},{once:true})});
 return RIG3D_P}

/* 표정 → VRM 표정값 (모델이 가진 프리셋 이름: happy/angry/sad/relaxed/surprised/blink/aa/ih/ou/ee/oh) */
const RIG3D_EX={neutral:{},smirk:{relaxed:.55,blink:.2},aggrieved:{sad:1},tears:{sad:1,ou:.45},shock:{surprised:1,oh:.5},angry:{angry:1},pout:{angry:.3,ou:.5},shy:{relaxed:.4,sad:.3}};
const RIG3D_MOUTH={open:{aa:.8},hmm:{ou:.25},grin:{ih:.55},smile:{ih:.25},flat:{},weary:{},smirk:{ih:.2},pout:{ou:.5},wail:{aa:.5},grit:{ee:.6}};
const RIG3D_NAMES=['happy','angry','sad','relaxed','surprised','blink','aa','ih','ou','ee','oh'];

/* host: 캐릭터 그림이 들어가는 칸, F: 벡터 캐릭터 객체(폴백이자 공용 인터페이스), C: 캐릭터 데이터 */
function vrmAttach(host,F,C,opts){
 if(!rig3dOn(C))return null;
 opts=opts||{};
 const M3=C.rig.model,wrap=document.createElement('div');wrap.className='vrm3d';wrap.style.display='none';
 if(getComputedStyle(host).position==='static')host.style.position='relative';
 host.appendChild(wrap);
 const mkd=c=>{const d=document.createElement('div');d.className=c;wrap.appendChild(d);return d};
 const tearL=mkd('v3t'),tearR=mkd('v3t'),blL=mkd('v3b'),blR=mkd('v3b');
 const V={on:false,error:null,exprName:'neutral',fx:'',talk:false,mouthName:null,lid:0,gx:0,gy:0,tilt:0,pitch:0,yaw:0,hands:null,ex:{}};
 F.vrm3d=V;F.vrmOn=false;
 /* 벡터 인터페이스 호출을 3D 쪽에도 그대로 전달 (표정·고개·눈·입·말하기) */
 const fw=(name,fn)=>{const o=F[name];F[name]=function(){const r=o?o.apply(F,arguments):undefined;try{fn.apply(null,arguments)}catch(e){}return r}};
 fw('setExpr',n=>{V.exprName=n;const E=(D.expr||{})[n]||{};V.fx=(E.fx||[]).join(',');V.tilt=E.tilt||0;V.pitch=E.pitch||0;V.ex=RIG3D_EX[n]||{}});
 fw('setYaw',d=>{V.yaw=d});fw('setPitch',d=>{V.pitch=d});fw('setTilt',d=>{V.tilt=d});
 fw('setLid',v=>{V.lid=v});fw('setGaze',(a,b)=>{V.gx=a;V.gy=b});fw('showMouth',n=>{V.mouthName=n});
 fw('setTalking',on=>{V.talk=!!on});
 F.setHands=function(L,R){V.hands=(L&&R)?{L:L,R:R}:null};
 F.setHandsMap=function(m){opts.map=m};

 rig3dReady().then(async M=>{
  if(!M){V.error='라이브러리 없음';(window.rig3dLog||console.warn)('['+C.key+'] 3D 라이브러리를 쓸 수 없어 벡터 캐릭터로 대체 (위 로그 참고)',true);return}
  try{
   const T=M.THREE,loader=new M.GLTFLoader();loader.register(p=>new M.VRMLoaderPlugin(p));
   const LOG=window.rig3dLog||console.log,tag='['+C.key+'] ';
   const urls=(M3.urls&&M3.urls.length)?M3.urls:[M3.url];let buf=null,lastErr='';
   for(const u of urls){
    try{LOG(tag+'모델 요청: '+u);const r=await fetch(u,{mode:'cors'});
     LOG(tag+'응답 '+r.status+' '+(r.statusText||'')+'  크기 '+(r.headers.get('content-length')?Math.round(r.headers.get('content-length')/1048576*10)/10+'MB':'?')+'  형식 '+(r.headers.get('content-type')||'?'));
     if(!r.ok)throw new Error('HTTP '+r.status+(r.status===403?' (jsDelivr 는 20MB 넘는 GitHub 파일을 막습니다 → raw.githubusercontent 주소 사용)':r.status===404?' (파일 이름·폴더·브랜치 확인, 방금 올렸다면 jsDelivr 캐시 지연일 수 있음)':''));
     buf=await r.arrayBuffer();LOG(tag+'다운로드 완료 '+Math.round(buf.byteLength/1048576*10)/10+'MB');
     if(buf.byteLength<2000||String.fromCharCode.apply(null,new Uint8Array(buf.slice(0,4)))==='vers')throw new Error('VRM 이 아닌 파일입니다(Git LFS 포인터이거나 빈 파일). 실제 .vrm 파일을 올렸는지 확인');
     break}catch(e){lastErr=String(e&&e.message||e);buf=null;LOG(tag+'실패: '+lastErr,true)}}
   if(!buf)throw new Error('모든 주소에서 모델을 받지 못함: '+lastErr);
   const gltf=await loader.parseAsync(buf,urls[0].replace(/[^/]*$/,'')),vrm=gltf.userData.vrm;
   LOG(tag+'VRM 해석 OK'+(vrm&&vrm.meta?' ('+(vrm.meta.metaVersion||vrm.meta.version||'?')+')':''));
   if(!vrm)throw new Error('VRM 데이터가 없는 파일입니다 (.vrm 으로 내보냈는지 확인하세요)');
   try{M.VRMUtils.removeUnnecessaryVertices&&M.VRMUtils.removeUnnecessaryVertices(gltf.scene);M.VRMUtils.removeUnnecessaryJoints&&M.VRMUtils.removeUnnecessaryJoints(gltf.scene)}catch(e){}
   M.VRMUtils.rotateVRM0&&M.VRMUtils.rotateVRM0(vrm);
   /* 장면: 투명 배경 + 툰 조명 */
   const renderer=new T.WebGLRenderer({alpha:true,antialias:true,powerPreference:'high-performance'});
   renderer.setClearColor(0x000000,0);wrap.appendChild(renderer.domElement);
   const scene=new T.Scene(),camera=new T.PerspectiveCamera(22,268/400,.1,30);
   const key=new T.DirectionalLight(0xfff4ea,Math.PI*.95);key.position.set(.8,1.1,1.4);scene.add(key);
   const rimL=new T.DirectionalLight(0xbfd8ff,Math.PI*.28);rimL.position.set(-1.2,.6,-1);scene.add(rimL);
   scene.add(new T.AmbientLight(0xffffff,.55));
   scene.add(vrm.scene);vrm.scene.updateMatrixWorld(true);
   const bone=n=>vrm.humanoid.getNormalizedBoneNode(n);
   const head=bone('head'),neck=bone('neck'),spine=bone('spine'),chest=bone('chest')||bone('upperChest')||spine,hips=bone('hips');
   const hp=head.getWorldPosition(new T.Vector3()),k=Math.max(.6,Math.min(1.6,hp.y/1.45));
   /* 상반신 구도: 머리 꼭대기~허리 (모델 키에 비례) */
   const fov=22,H=.80*k/(M3.zoom||1),cy=hp.y-.17*k+(M3.fy||0)*k,dist=(H/2)/Math.tan(fov*Math.PI/360);
   camera.fov=fov;camera.position.set(0,cy,dist);camera.lookAt(0,cy,0);camera.updateProjectionMatrix();
   const lookT=new T.Object3D();lookT.position.set(0,hp.y,2);scene.add(lookT);if(vrm.lookAt)vrm.lookAt.target=lookT;
   const pr=Math.min(3,Math.max(2,(window.devicePixelRatio||1)*2));   // 카메라 줌인에도 선명하도록 넉넉한 해상도
   const resize=()=>{const w=wrap.clientWidth,h=wrap.clientHeight;if(!w||!h)return;renderer.setPixelRatio(pr);renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix()};
   resize();if(window.ResizeObserver)new ResizeObserver(resize).observe(wrap);else window.addEventListener('resize',resize);

   /* 팔 IK 준비: 쉬는 자세의 뼈 방향·길이를 기억 */
   const arms=[];
   ['left','right'].forEach(sd=>{const u=bone(sd+'UpperArm'),l=bone(sd+'LowerArm'),h=bone(sd+'Hand');if(!u||!l||!h)return;
    const pu=u.getWorldPosition(new T.Vector3()),pl=l.getWorldPosition(new T.Vector3()),ph=h.getWorldPosition(new T.Vector3());
    const qp=u.parent.getWorldQuaternion(new T.Quaternion()).invert(),qu=u.getWorldQuaternion(new T.Quaternion()).invert();
    arms.push({u:u,l:l,a:pl.distanceTo(pu),b:ph.distanceTo(pl),s:Math.sign(pu.x)||1,restU:pl.clone().sub(pu).applyQuaternion(qp).normalize(),restL:ph.clone().sub(pl).applyQuaternion(qu).normalize()})});
   const vS=new T.Vector3(),vT=new T.Vector3(),vE=new T.Vector3(),vH=new T.Vector3(),vD=new T.Vector3(),vP=new T.Vector3(),vX=new T.Vector3(),q1=new T.Quaternion(),q2=new T.Quaternion();
   function aim(a,Tw){   // 2관절 IK: 어깨→팔꿈치→손이 목표점에 닿게 (팔꿈치는 뒤·아래·바깥쪽으로 굽힘)
    a.u.getWorldPosition(vS);vD.copy(Tw).sub(vS);let dist=vD.length();vD.divideScalar(dist||1);
    dist=Math.min(a.a+a.b-1e-4,Math.max(Math.abs(a.a-a.b)+1e-4,dist));
    const ang=Math.acos(Math.max(-1,Math.min(1,(a.a*a.a+dist*dist-a.b*a.b)/(2*a.a*dist))));
    vP.set(a.s*.35,-.5,-.6);vP.sub(vX.copy(vD).multiplyScalar(vP.dot(vD))).normalize();
    vE.copy(vS).addScaledVector(vD,a.a*Math.cos(ang)).addScaledVector(vP,a.a*Math.sin(ang));vH.copy(vS).addScaledVector(vD,dist);
    vX.copy(vE).sub(vS).normalize();u_set(a.u,a.restU,vX);
    a.u.updateWorldMatrix(true,false);
    vX.copy(vH).sub(vE).normalize();u_set(a.l,a.restL,vX,a.u)}
   function u_set(node,rest,dirW,par){const p=par||node.parent;p.getWorldQuaternion(q1).invert();vP.copy(dirW).applyQuaternion(q1);node.quaternion.setFromUnitVectors(rest,vP)}
   function relaxedTarget(a,out){a.u.getWorldPosition(out);out.x+=a.s*.045*k;out.y-=(a.a+a.b)*.95;out.z+=.03*k;return out}
   function canvasToWorld(c,zPlane,out){const m=opts.map;if(!m)return null;const hh=m.w*400/268,nx=((c[0]-m.x0)/m.w)*2-1,ny=-(((c[1]-m.y0)/hh)*2-1);
    vX.set(nx,ny,.5).unproject(camera);vX.sub(camera.position).normalize();const t=(zPlane-camera.position.z)/vX.z;return out.copy(camera.position).addScaledVector(vX,t)}

   /* 매 프레임 */
   const cur={yaw:0,pitch:0,tilt:0,ex:{}},bl={t:-1,next:1.5+Math.random()*4,v:0},vp=new T.Vector3();let last=performance.now(),ph0=Math.random()*10;
   const mgr=vrm.expressionManager,has={};if(mgr)RIG3D_NAMES.forEach(n=>{has[n]=!!(mgr.getExpression&&mgr.getExpression(n))});
   const place=(el,node,dx,dy,fallback)=>{if(node)node.getWorldPosition(vp);else vp.copy(hp).add(fallback);vp.x+=dx*k;vp.y+=dy*k;vp.project(camera);el.style.left=((vp.x*.5+.5)*100).toFixed(2)+'%';el.style.top=((-vp.y*.5+.5)*100).toFixed(2)+'%'};
   const eL=bone('leftEye'),eR=bone('rightEye');
   V.tick=function(now){
    const dt=Math.min(.05,(now-last)/1000);last=now;const t=now/1000+ph0,sm=1-Math.exp(-dt*9);
    /* 고개/몸: 얼굴은 최대 약 24° (몸은 10% 만) */
    const ty=Math.max(-24,Math.min(24,V.yaw*.55))*Math.PI/180;cur.yaw+=(ty-cur.yaw)*sm;cur.pitch+=((V.pitch*.8)*Math.PI/180-cur.pitch)*sm;cur.tilt+=((V.tilt)*Math.PI/180-cur.tilt)*sm;
    const br=Math.sin(t*1.5)*.5+.5;
    if(spine)spine.rotation.set(0,cur.yaw*.18,0);if(chest&&chest!==spine)chest.rotation.set(Math.sin(t*1.5)*.012,cur.yaw*.12,0);
    if(neck)neck.rotation.set(cur.pitch*.4,cur.yaw*.4,-cur.tilt*.4);
    head.rotation.set(cur.pitch*.6+Math.sin(t*.9)*.012+(V.talk?Math.sin(t*14)*.012:0),cur.yaw*.6,-cur.tilt*.6+Math.sin(t*.7)*.01);
    if(hips)hips.position.y=(hips.userData.y0==null?(hips.userData.y0=hips.position.y):hips.userData.y0)+br*.004*k;
    vrm.scene.updateMatrixWorld(true);
    /* 팔: 대기/로비 장면은 손 목표(캔버스 좌표)를 따라가고, 아니면 편하게 내려놓음 */
    arms.forEach(a=>{let tw=null;if(V.hands&&opts.map){const c=(a.s>0)?V.hands.R:V.hands.L;a.u.getWorldPosition(vT);tw=canvasToWorld(c,vT.z+.1*k,new T.Vector3())}
     if(!tw)tw=relaxedTarget(a,new T.Vector3());try{aim(a,tw)}catch(e){}});
    /* 시선 */
    lookT.position.set(V.gx*.06*k,hp.y-V.gy*.05*k,1.6);
    /* 표정: 목표값으로 부드럽게 + 깜빡임 + 말하는 입 */
    bl.next-=dt;if(bl.t<0&&bl.next<=0){bl.t=0}
    if(bl.t>=0){bl.t+=dt;const p=bl.t/.2;bl.v=p<.5?p*2:Math.max(0,2-p*2);if(bl.t>.2){bl.t=-1;bl.v=0;bl.next=(C.motion&&C.motion.blink_s||4.6)*(.6+Math.random()*.9)}}
    const want={};for(const n in V.ex)want[n]=V.ex[n];
    const mo=RIG3D_MOUTH[V.mouthName||'']||{};for(const n in mo)want[n]=Math.max(want[n]||0,mo[n]);
    if(V.talk)want.aa=Math.max(want.aa||0,.25+.4*(Math.sin(t*17)*.5+.5));
    want.blink=Math.max(want.blink||0,bl.v,V.lid||0,(C.rig.sleepy||0)*.9);
    if(mgr)RIG3D_NAMES.forEach(n=>{if(!has[n])return;const w=want[n]||0,c=cur.ex[n]||0,nv=c+(w-c)*(n==='blink'?.6:sm);cur.ex[n]=nv;mgr.setValue(n,nv)});
    vrm.update(dt);renderer.render(scene,camera);
    /* 눈물·홍조 */
    const fx=V.fx,tear=fx.indexOf('tears')>=0||fx.indexOf('welling')>=0,blush=fx.indexOf('blush')>=0;
    place(tearL,eL,0,-.028,new T.Vector3(.032*k,.02*k,.08*k));place(tearR,eR,0,-.028,new T.Vector3(-.032*k,.02*k,.08*k));
    place(blL,eL,.012,-.06,new T.Vector3(.04*k,-.02*k,.08*k));place(blR,eR,-.012,-.06,new T.Vector3(-.04*k,-.02*k,.08*k));
    [tearL,tearR].forEach(e=>e.classList.toggle('on',fx.indexOf('tears')>=0));[blL,blR].forEach(e=>e.classList.toggle('on',blush||tear));
   };
   V.tick(performance.now());
   RIG3D_LIST.push(V);
   if(!RIG3D_LOOP){RIG3D_LOOP=1;const loop=now=>{if(!document.hidden)for(const v of RIG3D_LIST){try{v.tick(now)}catch(e){if(!v.err){v.err=1;console.warn('[rig3d] 렌더 오류',e)}}}requestAnimationFrame(loop)};requestAnimationFrame(loop)}
   /* 성공: 벡터 캐릭터는 숨기고 3D 를 보여 준다 */
   wrap.style.display='block';if(F.rigEl)F.rigEl.style.visibility='hidden';V.on=true;F.vrmOn=true;
   LOG(tag+'✅ 3D 표시 시작 (벡터 캐릭터 숨김)')
  }catch(e){V.error=String(e&&e.message||e);(window.rig3dLog||console.warn)('['+C.key+'] ❌ 3D 실패 → 벡터로 대체: '+V.error+(e&&e.stack?'\n'+String(e.stack).split('\n').slice(0,3).join('\n'):''),true);wrap.style.display='none'}
 });
 return V}
"""
