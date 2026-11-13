"""templates.py — 화면에 그려지는 HTML/JS 템플릿 모음.

재판 연출(VN_TEMPLATE), 스토리 연출(STORY_TEMPLATE), 판결 결과 패널, 로딩 오버레이, 타이틀 화면.
연출·사운드·픽셀 디자인을 손볼 때는 여기를 수정하세요.
"""

import html
import json

import streamlit.components.v1 as components

from config import LOAD_HEAD, LOAD_STEP

# =================================================================
# HTML 조각
# =================================================================

def overlay_html(msg, kind, el, tip):
    icon, head = LOAD_HEAD[kind]
    return (
        '<style>html,body,.stApp{overflow:hidden !important}</style><div class="lf"><div class="lf-in">'
        f'<div class="lf-icon">{icon}</div><div class="lf-head">{html.escape(head)}</div>'
        f'<div class="lf-step">{html.escape(LOAD_STEP[kind])}</div>'
        f'<div class="lf-msg">{html.escape(msg)}{"." * (el % 3 + 1)}</div><div class="lf-bar"><i></i></div>'
        f'<div class="lf-meta">경과 {el}초</div><div class="lf-tip">💡 {html.escape(tip)}</div></div></div>'
    )

def result_panel_html(res):
    up = res["delta"] >= 0
    if res["dir"] > 0:
        rank_line = f'{res["rank_before"]} → {res["rank_after"]} ⬆️ 랭크 상승!'
    elif res["dir"] < 0:
        rank_line = f'{res["rank_before"]} → {res["rank_after"]} ⬇️ 랭크 하락…'
    else:
        rank_line = f'{res["rank_after"]} 유지'
    streak = f' · 🔥 {res["streak"]}연속 무죄!' if res.get("streak", 0) >= 2 else ""
    return (
        f'<div class="result-big {"up" if up else "down"}"><div class="rb-title">📊 재판 결과 · {html.escape(res["ruling"])}</div>'
        f'<div class="rb-delta">평판 {res["delta"]:+d}</div>'
        f'<div class="rb-rep">{res["rep_before"]} → {res["rep_after"]}점</div>'
        f'<div class="rb-rank">{html.escape(rank_line)}</div>'
        f'<div class="rb-meta">변명 점수 {res["score"]}점{streak}</div></div>'
    )

TITLE_HTML = (
    '<div class="ts"><div class="ts-wall"></div><div class="ts-pil l"></div><div class="ts-pil r"></div>'
    '<div class="ts-seal">法</div><div class="ts-bench"></div><div class="ts-floor"></div>'
    '<div class="ts-logo"><small>― 오리지널 B급 법정 아케이드 ―</small><h1>이불킥<br>법정</h1>'
    '<em>KICK-THE-BLANKET COURT</em></div><div class="ts-crt"></div>'
    '<div class="ts-copy">모든 캐릭터·세계관·그래픽은 이 게임을 위해 새로 창작한 오리지널입니다</div></div>'
)

# =================================================================
# 재판 연출 엔진 (iframe: 카메라 무빙 / 타이핑 / 효과음 / 망치 / 판결문 팝업)
# =================================================================

VN_TEMPLATE = r"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
@import url('https://fonts.googleapis.com/css2?family=Jua&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
@import url('https://cdn.jsdelivr.net/npm/galmuri@latest/dist/galmuri.css');
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:#000;overflow:hidden;font-family:'Galmuri11','Jua','Apple SD Gothic Neo','Malgun Gothic',sans-serif;user-select:none;-webkit-tap-highlight-color:transparent}
#scene{position:relative;width:100%;height:100%;overflow:hidden;cursor:pointer}
#world{display:flex;width:300%;height:100%;transform:translateX(-33.3334%);transition:transform .85s cubic-bezier(.65,0,.35,1)}
.panel{position:relative;width:33.3334%;height:100%;overflow:hidden;background:linear-gradient(#f1e5b7,#d6c488)}
.floor{position:absolute;left:0;right:0;bottom:0;height:38%;border-top:5px solid #6b4423;background:repeating-conic-gradient(#d7e9de 0 25%,#aecbbb 0 50%) 0 0/54px 54px}
.wood{position:absolute;top:6%;bottom:36%;left:8%;right:8%;border:5px solid #6b4423;background:repeating-linear-gradient(90deg,#b98450 0 40px,#a3703c 40px 44px)}
.pil{position:absolute;top:0;bottom:36%;width:15%;background:linear-gradient(90deg,#c9b27a,#f3e7bd 45%,#b59c61);border-left:3px solid #8f7a46;border-right:3px solid #8f7a46}
.seal{position:absolute;left:50%;top:7%;transform:translateX(-50%);width:84px;height:84px;border-radius:50%;background:radial-gradient(#fff,#cfd6e6);border:5px solid #c9a24d;box-shadow:0 0 0 4px #7a5a1e;display:flex;align-items:center;justify-content:center;font-size:40px}
.desk{position:absolute;left:-2%;right:-2%;bottom:0;height:27%;z-index:3;border-top:5px solid #e0a866;background:linear-gradient(#c58a4a 0 12%,#8e5a2b 12%)}
.bench{position:absolute;left:12%;right:12%;bottom:0;height:40%;z-index:3;border:5px solid #5e3217;border-bottom:0;background:linear-gradient(#b06a33 0 12%,#8a4b25 12%)}
.char{position:absolute;left:0;right:0;bottom:26%;display:flex;justify-content:center;z-index:2}
.char.j{bottom:36%}
.who{width:clamp(120px,34vw,200px);transform-origin:50% 100%;transition:transform .7s}
.who svg{display:block;width:100%}
#scene[data-cam=J] .char.j .who{transform:scale(1.22)}
.talk svg{animation:bob .3s steps(2) infinite}
.mouth{transform-box:fill-box;transform-origin:center}
.talk .mouth{animation:mouth .22s steps(2) infinite}
@keyframes bob{50%{transform:translateY(-3px)}}
@keyframes mouth{50%{transform:scaleY(2.6)}}
#crt{position:absolute;inset:0;z-index:20;pointer-events:none;background:repeating-linear-gradient(#0000 0 2px,#0002 2px 3px);box-shadow:inset 0 0 90px #000a}
/* 대화창 */
#dlg{position:absolute;left:2.5%;right:2.5%;bottom:3%;height:37%;min-height:150px;z-index:10}
#tag{position:absolute;left:14px;top:-22px;z-index:2;padding:2px;background:#d6eaff;clip-path:polygon(0 0,calc(100% - 14px) 0,100% 50%,calc(100% - 14px) 100%,0 100%)}
#tagin{padding:5px 28px 5px 16px;color:#fff;font-weight:700;font-size:15px;letter-spacing:1px;background:linear-gradient(#3d98da,#1d66a6);clip-path:polygon(0 0,calc(100% - 13px) 0,100% 50%,calc(100% - 13px) 100%,0 100%)}
#box{position:absolute;inset:0;background:linear-gradient(#b4c4e0,#6b80a8);clip-path:polygon(16px 0,calc(100% - 16px) 0,100% 16px,100% calc(100% - 16px),calc(100% - 16px) 100%,16px 100%,0 calc(100% - 16px),0 16px)}
#boxin{position:absolute;inset:3px;overflow:auto;background:linear-gradient(rgba(20,30,62,.9),rgba(10,16,36,.92));clip-path:polygon(14px 0,calc(100% - 14px) 0,100% 14px,100% calc(100% - 14px),calc(100% - 14px) 100%,14px 100%,0 calc(100% - 14px),0 14px)}
#txt{padding:20px 46px 12px 24px;color:#fff;font-size:clamp(14px,3.4vw,19px);line-height:1.65;word-break:keep-all;text-shadow:1px 1px 0 #000}
#arrow{position:absolute;right:20px;bottom:6px;color:#f2c14e;font-size:30px;font-weight:700;animation:blink .8s steps(2) infinite;visibility:hidden}
@keyframes blink{50%{opacity:.15}}
#hint{position:absolute;top:10px;left:50%;transform:translateX(-50%);z-index:12;display:none;white-space:nowrap;background:#b3121c;color:#fff;padding:6px 14px;font-weight:700;font-size:13px;border:2px solid #fff;animation:blink 1s steps(2) infinite}
#mute{position:absolute;top:8px;right:8px;z-index:30;background:#000a;color:#fff;border:2px solid #fff6;padding:3px 8px;font-size:14px;cursor:pointer}
/* 효과 */
#scene.shake{animation:shake .5s}
@keyframes shake{0%,100%{transform:translate(0)}20%{transform:translate(-9px,6px)}40%{transform:translate(8px,-7px)}60%{transform:translate(-7px,-5px)}80%{transform:translate(6px,7px)}}
#flash{position:absolute;inset:0;background:#fff;opacity:0;z-index:25;pointer-events:none}
#flash.on{animation:fl .5s}
@keyframes fl{0%{opacity:.9}100%{opacity:0}}
.hit{position:absolute;z-index:30;font-size:clamp(50px,15vw,110px);font-weight:900;color:#fff;-webkit-text-stroke:3px #b3121c;text-shadow:5px 5px 0 #000;pointer-events:none;animation:pop .8s forwards}
@keyframes pop{0%{transform:scale(.2) rotate(-12deg);opacity:0}25%{transform:scale(1.25) rotate(4deg);opacity:1}70%{opacity:1}100%{transform:scale(1);opacity:0}}
/* 시작 / 판결문 */
#start{position:absolute;inset:0;z-index:50;background:radial-gradient(#1b2350,#05070f);display:flex;flex-direction:column;align-items:center;justify-content:center;color:#fff;text-align:center;cursor:pointer}
#start h2{font-size:clamp(26px,7vw,40px);letter-spacing:6px;color:#f7e9b0;text-shadow:3px 3px 0 #b3121c}
#start p{margin-top:14px;color:#9fe8ff;animation:blink 1s steps(2) infinite}
#cardwrap{position:absolute;inset:0;z-index:40;display:none;align-items:center;justify-content:center;background:rgba(0,0,0,.7);overflow:auto;padding:12px}
@property --a{syntax:'<angle>';inherits:false;initial-value:0deg}
.card{position:relative;margin:auto;width:min(94%,460px);padding:5px;background:conic-gradient(from var(--a),#fff2a8,#d89b1e,#fff2a8,#b8730d,#fff2a8);animation:spin 3s linear infinite,cardin .7s cubic-bezier(.2,1.4,.4,1)}
@keyframes spin{to{--a:360deg}}
@keyframes cardin{0%{transform:scale(.1) rotate(-20deg);opacity:0}100%{transform:scale(1);opacity:1}}
.card-in{position:relative;padding:20px 18px 18px;text-align:center;color:#3a2a0e;background:#fbf3d4;border:2px solid #7a5a1e;outline:2px solid #c9a24d;outline-offset:-8px}
.ctitle{font-size:12px;letter-spacing:4px;color:#7a5a1e}
.card-in h2{font-size:clamp(22px,6vw,30px);letter-spacing:8px;margin:4px 0 2px;color:#7a1f1f}
.csub{font-size:13px;color:#5b4a2a;margin-bottom:8px}
.row{display:flex;gap:10px;text-align:left;margin:7px 0;font-size:14px;line-height:1.5;border-bottom:1px dotted #b9954a;padding-bottom:6px}
.row b{min-width:78px;color:#7a1f1f}
.row.big span{color:#c1121f;font-weight:900;font-size:16px}
.stamp{position:absolute;right:14px;top:46px;width:70px;height:70px;border:4px solid #c1121f;border-radius:50%;color:#c1121f;font-weight:900;font-size:22px;display:flex;align-items:center;justify-content:center;transform:rotate(-14deg);opacity:.88;animation:stampin .5s .7s both}
@keyframes stampin{0%{transform:scale(3) rotate(-14deg);opacity:0}100%{transform:scale(1) rotate(-14deg);opacity:.88}}
.badge{display:inline-block;margin-top:12px;background:#c1121f;color:#fff;padding:8px 20px;font-weight:700;clip-path:polygon(10px 0,calc(100% - 10px) 0,100% 50%,calc(100% - 10px) 100%,10px 100%,0 50%)}
.spark{position:absolute;color:#ffe066;pointer-events:none;animation:tw 1.2s infinite;text-shadow:0 0 6px #fff}
@keyframes tw{0%,100%{opacity:0;transform:scale(.3)}50%{opacity:1;transform:scale(1.2)}}

#hint{top:44px}
#phase{position:absolute;top:12px;left:12px;z-index:23;background:#10162e;color:#ffd23f;border:2px solid #ffd23f;padding:3px 10px;font-size:12px;font-weight:700;letter-spacing:1px}
#frame{position:absolute;inset:0;z-index:22;pointer-events:none;border:7px solid;border-image:repeating-linear-gradient(45deg,#ffd23f 0 12px,#1b1b1b 12px 24px) 7}
.book{position:absolute;left:19%;bottom:40%;z-index:4;padding:3px 10px;font-size:11px;color:#f2d98a;background:#5a2d12;border:2px solid #f2d98a;transform:rotate(-3deg);box-shadow:3px 3px 0 #0006}
#shout{position:absolute;left:-10%;right:-10%;top:28%;z-index:35;display:none;padding:12px 0;text-align:center;font-weight:900;font-size:clamp(17px,5vw,30px);color:#fff;letter-spacing:1px;text-shadow:3px 3px 0 #000;border-top:5px solid #fff;border-bottom:5px solid #fff;pointer-events:none}
#shout.F{background:repeating-linear-gradient(135deg,#0a5fb4 0 18px,#0b3f7a 18px 36px)}
#shout.S{background:repeating-linear-gradient(135deg,#d6336c 0 18px,#a1184b 18px 36px)}
#shout.O{background:repeating-linear-gradient(135deg,#b8860b 0 18px,#7a5a06 18px 36px)}
#shout.on{display:block;animation:slam .95s forwards}
@keyframes slam{0%{transform:skewY(-4deg) translateX(-120%)}15%{transform:skewY(-4deg) translateX(0) scale(1.12)}28%{transform:skewY(-4deg) scale(1)}85%{opacity:1}100%{transform:skewY(-4deg);opacity:0}}

#scene{border-radius:0}
#frame{border-image:none;border:6px solid #0d0f26;border-radius:0;z-index:22;box-shadow:inset 0 0 0 3px #ffd23f}
#crt{border-radius:0}
#dlg{left:3%;right:3%}
#box{clip-path:none;border-radius:0;background:#fff;box-shadow:0 -4px 0 #0d0f26,0 4px 0 #0d0f26,-4px 0 0 #0d0f26,4px 0 0 #0d0f26,0 10px 0 0 #0008}
#boxin{clip-path:none;border-radius:0;inset:4px;background:#1a2358;box-shadow:inset 0 4px 0 #3b4a9a,inset 0 -4px 0 #0e1438}
#tag{clip-path:none;border-radius:0;padding:4px;background:#0d0f26;box-shadow:none}
#tagin{clip-path:none;border-radius:0;padding:4px 16px;color:#2b1a00;background:#ffd23f;box-shadow:inset 0 3px 0 #fff4b8,inset 0 -3px 0 #d98e00}
#phase,#hint,#mute{border-radius:0;border:3px solid #0d0f26;box-shadow:inset 0 -3px 0 #0005}
#shout{left:0;right:0;border-radius:0;border-width:4px;box-shadow:0 6px 0 #0d0f26}
.card{border-radius:0;box-shadow:0 -4px 0 #0d0f26,0 4px 0 #0d0f26,-4px 0 0 #0d0f26,4px 0 0 #0d0f26,0 10px 0 0 #0008}
.card-in{border-radius:0;outline-offset:-10px;padding:24px 20px 22px}
.card-in h2{font-size:clamp(24px,7vw,32px);margin-bottom:6px}
.row{font-size:17px;border-bottom:2px dotted #c9a24d;padding-bottom:9px;margin:11px 0}
.row b{min-width:62px}
.row.big{background:#fff0c9;border-radius:0;border:3px solid #0d0f26;padding:12px;margin-top:14px}
.row.big span{font-size:20px;line-height:1.45}
.badge{clip-path:none;border-radius:0;border:4px solid #0d0f26;font-size:18px;padding:10px 24px;margin-top:16px;box-shadow:inset 0 -5px 0 #8f0b15,0 5px 0 #0d0f26}
.res{margin-top:20px;padding:14px 10px;background:#161c4d;border:4px solid #0d0f26;box-shadow:inset 0 4px 0 #3b4a9a,0 5px 0 #0d0f26;color:#fff;text-align:center}
.res-d{font-size:46px;font-weight:900;line-height:1.1;text-shadow:3px 3px 0 #000}
.res-d.up{color:#59f08a}.res-d.down{color:#ff6b6b}
.res-r{margin-top:8px;font-size:21px;font-weight:700;color:#ffe066;line-height:1.4}
.res-s{margin-top:6px;font-size:14px;color:#9fe8ff}
#start h2{text-shadow:3px 3px 0 #b3121c}

/* ---- 가로 화면: iframe 비율이 가로형(5:4 이상)일 때 적용. 세로 폰에서는 위 기본값을 그대로 사용 ---- */
@media (min-aspect-ratio:5/4){
.who{width:clamp(130px,38vh,260px)}
.char.j{bottom:32%}
#scene[data-cam=J] .char.j .who{transform:scale(1.1)}
.seal{width:96px;height:96px;font-size:46px}
#dlg{left:10%;right:10%;height:36%;min-height:150px}
#txt{font-size:clamp(16px,3.7vh,22px);padding:22px 52px 14px 28px}
#hint{top:12px}
.card{width:min(92%,640px)}
.card-in{padding:20px 30px 18px}
.row{margin:7px 0;padding-bottom:7px}
.row.big{margin-top:10px}
.badge{margin-top:12px}
.res{margin-top:14px;padding:10px}
.res-d{font-size:38px}
}
</style></head><body>
<div id="scene" data-cam="J">
 <div id="world">
  <div class="panel"><div class="wood"></div><div class="pil" style="left:4%"></div><div class="floor"></div>
   <div class="char" data-c="P"><div class="who" id="svgP"></div></div><div class="desk"></div></div>
  <div class="panel"><div class="wood"></div><div class="pil" style="left:6%"></div><div class="pil" style="right:6%"></div><div class="seal">法</div><div class="floor"></div>
   <div class="char j" data-c="J"><div class="who" id="svgJ"></div></div><div class="bench"></div><div class="book">🔍 돋보기 · ☕ 보리차</div></div>
  <div class="panel"><div class="wood"></div><div class="pil" style="right:4%"></div><div class="floor"></div>
   <div class="char" data-c="L"><div class="who" id="svgL"></div></div><div class="desk"></div></div>
 </div>
 <div id="hint"></div><div id="phase"></div><div id="shout"></div><div id="frame"></div>
 <div id="dlg"><div id="tag"><div id="tagin">재판관</div></div><div id="box"></div><div id="boxin"><div id="txt"></div></div><div id="arrow">»</div></div>
 <div id="flash"></div><div id="crt"></div>
 <div id="mute">🔊</div>
 <div id="cardwrap"><div class="card"><div class="card-in"><div class="stamp" id="c_stamp">유죄</div>
  <div class="ctitle">― 이불킥 법정 ―</div><h2>공 식 판 결 문</h2><div class="csub" id="c_title"></div>
  <div class="row"><b>피 고 인</b><span id="c_name"></span></div>
  <div class="row"><b>죄 목</b><span id="c_crime"></span></div>
  
  <div class="row big"><b>선 고</b><span id="c_sentence"></span></div>
  <div class="badge" id="c_badge"></div>
  <div class="res"><div class="res-d" id="r_d"></div><div class="res-r" id="r_r"></div><div class="res-s" id="r_s"></div></div></div></div></div>
 <div id="start"><h2 id="s_t">재판 개시</h2><p>▶ PRESS START (클릭)</p></div>
</div>
<script>
const D=__DATA__;
const $=id=>document.getElementById(id);
const scene=$('scene');
const NAMES={J:'서판결 판사',P:'차냉정 검사',L:'우기기 변호사'};
const CAM={JUDGE:'J',PROSECUTOR:'P',LAWYER:'L'};
const TX={J:'-33.3334%',P:'0%',L:'-66.6667%'};
const EYES='<rect x="37" y="40" width="5" height="5" fill="#222"/><rect x="58" y="40" width="5" height="5" fill="#222"/>';
$('svgJ').innerHTML='<svg viewBox="0 0 100 150" shape-rendering="crispEdges"><polygon points="4,150 14,76 86,76 96,150" fill="#2f5a46"/><polygon points="38,76 50,100 62,76" fill="#f3ead0"/><rect x="46" y="100" width="8" height="50" fill="#d9b85a"/><rect x="29" y="12" width="42" height="44" fill="#f0c9a0"/><rect x="22" y="22" width="9" height="22" fill="#fff"/><rect x="69" y="22" width="9" height="22" fill="#fff"/><rect x="38" y="4" width="24" height="10" fill="#fff"/><rect x="33" y="26" width="14" height="5" fill="#fff"/><rect x="53" y="26" width="14" height="5" fill="#fff"/><rect x="32" y="33" width="16" height="12" fill="none" stroke="#c9a24d" stroke-width="2"/><rect x="52" y="33" width="16" height="12" fill="none" stroke="#c9a24d" stroke-width="2"/><rect x="38" y="37" width="5" height="5" fill="#222"/><rect x="58" y="37" width="5" height="5" fill="#222"/><polygon points="36,52 64,52 62,88 50,100 38,88" fill="#f1f1f6"/><polygon points="34,48 66,48 62,56 50,53 38,56" fill="#fff"/><rect class="mouth" x="43" y="59" width="14" height="4" fill="#7a3b3b"/></svg>';
$('svgP').innerHTML='<svg viewBox="0 0 100 150" shape-rendering="crispEdges"><polygon points="6,150 16,76 84,76 94,150" fill="#1d1f2b"/><polygon points="38,76 50,108 62,76" fill="#e9f3ff"/><polygon points="46,86 54,86 52,130 48,130" fill="#4fc3f7"/><rect x="30" y="20" width="40" height="42" fill="#e8d4c4"/><polygon points="28,34 28,10 40,6 60,6 72,10 72,34 64,24 36,24" fill="#6fa8dc"/><rect x="36" y="39" width="10" height="3" fill="#112"/><rect x="54" y="39" width="10" height="3" fill="#112"/><rect x="33" y="35" width="16" height="10" fill="#bfe9ff" fill-opacity=".35" stroke="#9ad" stroke-width="1.5"/><rect x="51" y="35" width="16" height="10" fill="#bfe9ff" fill-opacity=".35" stroke="#9ad" stroke-width="1.5"/><rect class="mouth" x="45" y="53" width="10" height="2" fill="#6a3b3b"/></svg>';
$('svgL').innerHTML='<svg viewBox="0 0 100 150" shape-rendering="crispEdges"><polygon points="6,150 16,76 84,76 94,150" fill="#e0a82e"/><polygon points="36,76 50,104 64,76" fill="#fff"/><polygon points="45,84 55,84 57,120 50,128 43,120" fill="#7b2cbf"/><rect x="22" y="110" width="6" height="6" fill="#7b2cbf"/><rect x="72" y="124" width="6" height="6" fill="#7b2cbf"/><rect x="30" y="20" width="40" height="42" fill="#f2c79b"/><rect x="18" y="0" width="64" height="26" fill="#f26b1d"/><rect x="12" y="8" width="76" height="20" fill="#f26b1d"/><rect x="22" y="26" width="8" height="14" fill="#f26b1d"/><rect x="70" y="26" width="8" height="14" fill="#f26b1d"/><rect x="34" y="32" width="14" height="14" fill="#fff" stroke="#222" stroke-width="2"/><rect x="52" y="32" width="14" height="14" fill="#fff" stroke="#222" stroke-width="2"/><rect x="39" y="37" width="4" height="4" fill="#222"/><rect x="57" y="37" width="4" height="4" fill="#222"/><rect class="mouth" x="38" y="50" width="24" height="6" fill="#7a1f2b"/><rect x="40" y="50" width="20" height="2" fill="#fff"/></svg>';

if(D.mode==='verdict'){const c=D.card;$('c_title').textContent=c.title;$('c_name').textContent=c.name;$('c_crime').textContent=c.crime;const SC={'무죄':'#1a9b5b','감형':'#d9822b','유죄':'#c1121f'};$('c_stamp').textContent=c.ruling;$('c_stamp').style.color=SC[c.ruling]||'#c1121f';$('c_stamp').style.borderColor=SC[c.ruling]||'#c1121f';$('c_sentence').textContent=c.sentence;$('c_badge').textContent=c.badge;
const R=c.res;if(R){const up=R.delta>=0;$('r_d').textContent='평판 '+(up?'+':'')+R.delta;$('r_d').className='res-d '+(up?'up':'down');
 $('r_r').textContent=R.dir>0?(R.rank_before+' → '+R.rank_after+' ⬆️ 랭크 상승!'):R.dir<0?(R.rank_before+' → '+R.rank_after+' ⬇️ 랭크 하락…'):(R.rank_after+' 유지');
 $('r_s').textContent=R.rep_before+' → '+R.rep_after+'점'+(R.streak>=2?' · 🔥 '+R.streak+'연속 무죄!':'')}else{document.querySelector('.res').style.display='none'}$('s_t').textContent='최종 선고';}

$('s_t').textContent=D.title||'재판 개시';$('phase').textContent=D.phase||'';
/* ---- 사운드 (WebAudio, 파일 없이 합성) ---- */
let AC=null,muted=!!D.mute;
function ac(){if(!AC){try{AC=new(window.AudioContext||window.webkitAudioContext)()}catch(e){}}return AC}
function beep(f,d,v){if(muted)return;const a=ac();if(!a)return;const o=a.createOscillator(),g=a.createGain();o.type='square';o.frequency.value=f;g.gain.value=v||.04;o.connect(g);g.connect(a.destination);o.start();g.gain.exponentialRampToValueAtTime(.0001,a.currentTime+d);o.stop(a.currentTime+d)}
function thud(){if(muted)return;const a=ac();if(!a)return;const n=Math.floor(a.sampleRate*.25),b=a.createBuffer(1,n,a.sampleRate),ch=b.getChannelData(0);for(let i=0;i<n;i++)ch[i]=(Math.random()*2-1)*Math.pow(1-i/n,3);const s=a.createBufferSource();s.buffer=b;const g=a.createGain();g.gain.value=.5;s.connect(g);g.connect(a.destination);s.start();const o=a.createOscillator(),g2=a.createGain();o.frequency.setValueAtTime(170,a.currentTime);o.frequency.exponentialRampToValueAtTime(40,a.currentTime+.2);g2.gain.setValueAtTime(.7,a.currentTime);g2.gain.exponentialRampToValueAtTime(.001,a.currentTime+.25);o.connect(g2);g2.connect(a.destination);o.start();o.stop(a.currentTime+.26)}
$('mute').textContent=muted?'🔇':'🔊';$('mute').onclick=e=>{e.stopPropagation();muted=!muted;$('mute').textContent=muted?'🔇':'🔊'};

/* ---- 진행 엔진 ---- */
let started=false,i=-1,typing=false,timer=null,full='',busy=false,curCam='J',ended=false;
const last=()=>D.steps.length-1;
function setTalk(c){document.querySelectorAll('.char').forEach(e=>e.classList.toggle('talk',e.dataset.c===c))}
function stopType(){clearInterval(timer);typing=false;$('txt').textContent=full;$('arrow').style.visibility='visible';setTalk(null);
 if(i===last()&&!ended){if(D.mode==='verdict'){ended=true;setTimeout(gavel,900)}else{$('hint').textContent=D.hint||'';$('hint').style.display='block'}}}
function type(text){typing=true;full=text;let k=0;$('txt').textContent='';timer=setInterval(()=>{k++;$('txt').textContent=text.slice(0,k);$('boxin').scrollTop=$('boxin').scrollHeight;if(k%2===0)beep(480+Math.random()*140,.04);if(k>=text.length)stopType()},D.speed||32)}
const SHOUT={F:'잠깐만요! 팩트 체크 들어갑니다!',S:'이의 있습니다! 억지 쉴드 발동!',O:'정숙하십시오! 법정에서의 소란은 허용되지 않습니다!'};
function shout(k,cb){const e=$('shout');e.textContent=SHOUT[k];e.className=k+' on';[520,780,1040].forEach((f,j)=>setTimeout(()=>beep(f,.16,.07),j*90));scene.classList.remove('shake');void scene.offsetWidth;scene.classList.add('shake');setTimeout(()=>{e.className='';cb()},950)}
function show(n){const st=D.steps[n],c=CAM[st.s]||'J';busy=true;$('phase').textContent=(D.phase||'')+' · '+(n+1)+'/'+D.steps.length;const changed=c!==curCam;curCam=c;scene.dataset.cam=c;$('world').style.transform='translateX('+TX[c]+')';$('tagin').textContent=NAMES[c];$('txt').textContent='';$('arrow').style.visibility='hidden';
 const speak=()=>{busy=false;setTalk(c);type(st.t)};
 setTimeout(()=>{if(st.c&&SHOUT[st.c])shout(st.c,speak);else speak()},changed?800:150)}
function adv(){if(!started||busy||ended)return;if(typing){stopType();return}if(i<last()){i++;show(i)}}
scene.addEventListener('click',adv);
document.addEventListener('keydown',e=>{if(e.code==='Space'||e.code==='Enter'){e.preventDefault();adv()}});
$('start').addEventListener('click',e=>{e.stopPropagation();started=true;ac();beep(880,.12);$('start').style.display='none';i=0;show(0)});

/* ---- 탕! 탕! 탕! → 판결문 ---- */
function hit(){thud();scene.classList.remove('shake');void scene.offsetWidth;scene.classList.add('shake');const f=$('flash');f.classList.remove('on');void f.offsetWidth;f.classList.add('on');
 const h=document.createElement('div');h.className='hit';h.textContent='탕!';h.style.left=(18+Math.random()*40)+'%';h.style.top=(12+Math.random()*30)+'%';scene.appendChild(h);setTimeout(()=>h.remove(),850)}
function gavel(){[0,750,1500].forEach(d=>setTimeout(hit,d));setTimeout(showCard,2900)}
function showCard(){$('hint').style.display='none';const w=$('cardwrap');w.style.display='flex';[660,880,1320].forEach((f,k)=>setTimeout(()=>beep(f,.25,.06),k*140));
 for(let k=0;k<18;k++){const s=document.createElement('span');s.className='spark';s.textContent='✦';s.style.left=(Math.random()*92)+'%';s.style.top=(Math.random()*92)+'%';s.style.fontSize=(10+Math.random()*18)+'px';s.style.animationDelay=(Math.random()*1.2)+'s';w.appendChild(s)}}
</script></body></html>"""

def render_vn(mode, steps, card=None, height=580, title="", phase="", hint="", mute=False, speed=30):
    payload = json.dumps({"mode": mode, "steps": steps, "card": card or {}, "title": title, "phase": phase, "hint": hint, "mute": mute, "speed": speed}, ensure_ascii=False)
    payload = payload.replace("</", "<\\/")  # </script> 깨짐 방지
    components.html(VN_TEMPLATE.replace("__DATA__", payload), height=height, scrolling=False)

# =================================================================
# 1인칭 법원 스토리 (iframe: 침실 → 명함 → 법원 계단 → 문 열림 → 게임 목적)
# =================================================================

STORY_TEMPLATE = r"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
@import url('https://cdn.jsdelivr.net/npm/galmuri@latest/dist/galmuri.css');
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:#000;overflow:hidden;font-family:'Galmuri11','Jua','Apple SD Gothic Neo','Malgun Gothic',sans-serif;user-select:none;-webkit-tap-highlight-color:transparent}
:root{--k:0;--ink:#0d0f26}
#scene{position:relative;width:100%;height:100%;overflow:hidden;cursor:pointer;background:linear-gradient(#232766 0%,#7a58a8 36%,#ff9f78 62%,#ffd9a0 100%)}
.cloud{position:absolute;height:12px;width:46px;background:#ffffffb0;box-shadow:16px -10px 0 #ffffffb0,32px 0 0 #ffffffb0;animation:drift 34s linear infinite}
@keyframes drift{from{transform:translateX(-90px)}to{transform:translateX(560px)}}
#cam{position:absolute;inset:0}
#cam.bob{animation:bob .38s ease-out}
@keyframes bob{0%{transform:translateY(0)}35%{transform:translateY(9px)}100%{transform:translateY(0)}}
#bldg{position:absolute;left:-28%;width:156%;bottom:30%;transform-origin:50% 100%;transform:translateY(calc(var(--k)*1.5%)) scale(calc(1 + var(--k)*.05));transition:transform .8s cubic-bezier(.4,0,.2,1)}
#bldg svg{display:block;width:100%;height:auto}
#stairs{position:absolute;left:0;right:0;bottom:0;height:35%;transform:translateY(calc(var(--k)*1.1%));transition:transform .6s;background:#5d5a50}
#stairs i{position:absolute;left:0;right:0;display:block;border-top:3px solid #fff8;background:linear-gradient(#e1dac8 0 56%,#a59d88 56%)}
#stairs:after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,#000a,#0000 16%,#0000 84%,#000a)}
#door{position:absolute;inset:0;z-index:15;display:none;overflow:hidden;background:radial-gradient(circle at 50% 45%,#fff8d6,#ffd36e 55%,#c68b2a)}
#sil{position:absolute;left:0;right:0;bottom:34%;text-align:center;font-size:62px;letter-spacing:10px;filter:brightness(0);opacity:.9}
.dl,.dr{position:absolute;top:0;bottom:0;width:50%;z-index:16;transition:transform 1.7s ease-in;background:repeating-linear-gradient(90deg,#5a3418 0 20px,#3f2410 20px 24px)}
.dl{left:0;border-right:5px solid var(--ink)}.dr{right:0;border-left:5px solid var(--ink)}
#door.open .dl{transform:translateX(-102%)}#door.open .dr{transform:translateX(102%)}
#vig{position:absolute;inset:0;z-index:20;pointer-events:none;background:repeating-linear-gradient(#0000 0 2px,#0002 2px 3px);box-shadow:inset 0 0 110px #000b}
#flash{position:absolute;inset:0;background:#fff;opacity:0;z-index:25;pointer-events:none}
#flash.on{animation:fl .6s}
@keyframes fl{0%{opacity:.95}100%{opacity:0}}
#pop{position:absolute;z-index:30;left:50%;top:38%;white-space:nowrap;font-size:clamp(34px,11vw,52px);font-weight:900;color:#fff;pointer-events:none;opacity:0;-webkit-text-stroke:4px var(--ink);paint-order:stroke fill;text-shadow:5px 5px 0 #ff4d4d}
#pop.on{animation:pop .95s forwards}
@keyframes pop{0%{opacity:0;transform:translate(-50%,16px) scale(.5)}20%{opacity:1;transform:translate(-50%,0) scale(1.15)}70%{opacity:1}100%{opacity:0;transform:translate(-50%,-28px) scale(1)}}
.pill{position:absolute;z-index:30;background:#ffd23f;color:#2b1a00;font-size:12px;font-weight:700;padding:5px 10px;cursor:pointer;box-shadow:0 -3px 0 var(--ink),0 3px 0 var(--ink),-3px 0 0 var(--ink),3px 0 0 var(--ink),inset 0 -3px 0 #d98e00}
#stepbar{left:14px;top:14px;cursor:default;display:none;background:#1a2358;color:#fff;box-shadow:0 -3px 0 var(--ink),0 3px 0 var(--ink),-3px 0 0 var(--ink),3px 0 0 var(--ink),inset 0 -3px 0 #0006}
#stepbar b{color:#ffd23f}
#auto{right:14px;top:14px}#mute{right:14px;top:48px}
#end{left:50%;top:84px;transform:translateX(-50%);display:none;white-space:nowrap;background:#ff4d4d;color:#fff;cursor:default;box-shadow:0 -3px 0 var(--ink),0 3px 0 var(--ink),-3px 0 0 var(--ink),3px 0 0 var(--ink),inset 0 -3px 0 #a31515;animation:blink 1s steps(2) infinite}
#replay{left:50%;top:122px;transform:translateX(-50%);display:none}
@keyframes blink{50%{opacity:.35}}
#dlg{position:absolute;left:3%;right:3%;bottom:3%;min-height:28%;z-index:18;background:#fff;box-shadow:0 -4px 0 var(--ink),0 4px 0 var(--ink),-4px 0 0 var(--ink),4px 0 0 var(--ink),0 10px 0 0 #0008}
#dlgin{position:absolute;inset:4px;overflow:auto;background:#1a2358;box-shadow:inset 0 4px 0 #3b4a9a,inset 0 -4px 0 #0e1438}
#tag{position:absolute;left:14px;top:-24px;z-index:2;padding:4px;background:var(--ink)}
#tagin{padding:4px 14px;color:#2b1a00;font-weight:700;font-size:14px;background:#ffd23f;box-shadow:inset 0 3px 0 #fff4b8,inset 0 -3px 0 #d98e00}
#txt{padding:20px 44px 14px 20px;color:#fff;font-size:clamp(15px,3.8vw,19px);line-height:1.7;word-break:keep-all;text-shadow:2px 2px 0 #000}
#arrow{position:absolute;right:16px;bottom:8px;color:#ffd23f;font-size:26px;font-weight:700;animation:blink .8s steps(2) infinite;visibility:hidden}
#start{position:absolute;inset:0;z-index:50;background:radial-gradient(#26307a,#05070f);display:flex;flex-direction:column;align-items:center;justify-content:center;color:#fff;text-align:center;cursor:pointer}
#start h2{font-size:clamp(24px,7vw,34px);color:#ffd23f;-webkit-text-stroke:3px var(--ink);paint-order:stroke fill;text-shadow:4px 4px 0 #ff4d4d;letter-spacing:2px}
#start p{margin-top:16px;color:#9fe8ff;font-family:'Press Start 2P',monospace;font-size:11px;animation:blink 1s steps(2) infinite}
#start small{margin-top:10px;color:#b8c4e8}

/* ---- 장면 전환 레이어 (대사창 z-index 18 아래, 문 오버레이 15 위/아래로 정리) ---- */
.vis{position:absolute;inset:0;z-index:12;opacity:0;pointer-events:none;transition:opacity .7s;overflow:hidden}
.vis.on{opacity:1}
.ov{z-index:16;background:rgba(8,10,30,.82);display:flex;align-items:center;justify-content:center;padding-bottom:30%}
#v_bed{background:linear-gradient(#0a0e2e,#18215c 55%,#26306f)}
#v_bed .stars{position:absolute;inset:0;opacity:.7;background-image:radial-gradient(#fff 1px,transparent 1.6px);background-size:44px 36px}
.win{position:absolute;left:8%;top:7%;width:36%;height:26%;border:6px solid var(--ink);background:linear-gradient(#0f1a70,#2b3fa8);box-shadow:inset 0 0 0 3px #7fa0ff55}
.win:before{content:"";position:absolute;left:50%;top:0;bottom:0;width:5px;background:var(--ink)}
.moon{position:absolute;right:16%;top:18%;width:24px;height:24px;border-radius:50%;background:#fff3b0;box-shadow:inset -7px -2px 0 #2b3fa8}
.clock{position:absolute;right:7%;top:9%;font-family:'Press Start 2P',monospace;font-size:15px;color:#ff4d4d;background:#050510;padding:10px 12px;border:4px solid #3a3f5c;animation:blink 1s steps(2) infinite}
.floorb{position:absolute;left:0;right:0;bottom:0;height:34%;background:repeating-linear-gradient(90deg,#5a3a22 0 40px,#4a2e1a 40px 44px);border-top:5px solid var(--ink)}
.bed{position:absolute;left:5%;right:5%;bottom:30%;height:22%;background:#8a5a34;border:5px solid var(--ink);box-shadow:0 8px 0 #0008}
.pillow{position:absolute;left:3%;top:-30%;width:24%;height:62%;background:#fff;border:4px solid var(--ink);box-shadow:inset 0 -6px 0 #cfd6ee}
.blanket{position:absolute;left:22%;right:-2%;top:-34%;bottom:-6%;border:4px solid var(--ink);background:repeating-linear-gradient(90deg,#4aa8ff 0 22px,#3b8fe6 22px 44px);transform-origin:left bottom}
.blanket.kick{animation:flap .3s infinite}
@keyframes flap{0%,100%{transform:rotate(0)}50%{transform:rotate(-7deg) translateY(-10px)}}
.feet{position:absolute;right:-12px;top:-64%;font-size:46px;transform-origin:left bottom}
.feet.kick{animation:legk .3s infinite}
@keyframes legk{0%,100%{transform:rotate(0)}50%{transform:rotate(-40deg)}}
.think{position:absolute;left:8%;top:40%;max-width:78%;background:#fff;color:var(--ink);border:4px solid var(--ink);padding:8px 12px;font-size:14px;font-weight:700;opacity:0;box-shadow:4px 4px 0 var(--ink)}
.think.on{animation:thinkpop .5s forwards}
@keyframes thinkpop{from{opacity:0;transform:scale(.5)}to{opacity:1;transform:scale(1)}}
.dropcard{position:absolute;left:62%;top:48%;font-size:30px;opacity:0}
.dropcard.on{animation:dropc 1.1s ease-in forwards}
@keyframes dropc{0%{opacity:0;transform:translateY(-30px) rotate(0)}20%{opacity:1}100%{opacity:1;transform:translateY(120px) rotate(300deg)}}
#v_card{background:radial-gradient(circle at 50% 38%,#3a3f8f,#0a0d28 70%)}
.bcard{position:absolute;left:12%;right:12%;top:12%;min-height:200px;overflow:hidden;transform:rotate(-4deg);background:#fff8e0;border:5px solid var(--ink);box-shadow:8px 8px 0 #000;padding:16px;color:var(--ink);text-align:center}
.bcard .back{display:none}.bcard.flip .front{display:none}.bcard.flip .back{display:block}.bcard.flip{animation:flipx .5s}
@keyframes flipx{0%{transform:rotate(-4deg) scaleX(1)}50%{transform:rotate(-4deg) scaleX(.02)}100%{transform:rotate(-4deg) scaleX(1)}}
.bc-logo{font-size:34px}.bc-t{font-size:22px;font-weight:900;margin:6px 0;letter-spacing:2px}.bc-s{font-size:14px;line-height:1.6}
.bc-n{margin-top:10px;display:inline-block;background:var(--ink);color:#ffd23f;padding:3px 10px;font-size:13px}
.bc-hand{font-size:19px;line-height:1.8;color:#3a2a8a;transform:rotate(-2deg);font-weight:700;padding-top:18px}
.shine{position:absolute;top:0;bottom:0;width:30px;background:#ffffff66;transform:skewX(-20deg);animation:shine 2.6s infinite}
@keyframes shine{from{left:-40px}to{left:110%}}
.hallfloor{position:absolute;left:0;right:0;bottom:0;height:30%;background:repeating-conic-gradient(#d7e9de 0 25%,#aecbbb 0 50%) 0 0/48px 48px;border-top:5px solid #6b4423}
.ch{position:absolute;bottom:26%;width:31%;z-index:1;filter:brightness(0);transition:filter .5s}
.ch svg{display:block;width:100%}
.ch.rev{filter:none;animation:hop .45s}
@keyframes hop{0%{transform:translateY(0)}40%{transform:translateY(-16px)}100%{transform:translateY(0)}}
.nm{position:absolute;top:-30px;left:50%;transform:translateX(-50%);white-space:nowrap;background:#ffd23f;color:#2b1a00;font-size:13px;font-weight:700;padding:3px 10px;border:3px solid var(--ink);display:none}
.ch.rev .nm{display:block}
.gbox{width:84%;max-width:360px;text-align:center;background:#161c4d;border:5px solid var(--ink);box-shadow:0 8px 0 #000;padding:16px;color:#fff}
.gt{font-size:18px;font-weight:700;color:#9fe8ff;letter-spacing:2px}
.gbar{height:22px;border:4px solid var(--ink);background:#050510;margin:12px 0 6px;overflow:hidden}
.gbar i{display:block;height:100%;width:62%;background:repeating-linear-gradient(45deg,#ff4d4d 0 10px,#c42f2f 10px 20px)}
.gv{font-family:'Press Start 2P',monospace;font-size:26px;color:#ff6b6b;margin:6px 0}
.ranks{display:flex;justify-content:space-between;font-size:26px;margin-top:8px;padding:0 6px}
.ranks .cur{animation:blink .7s steps(2) infinite}
.gc{margin-top:10px;font-size:15px;color:#ffe066;font-weight:700}
.big{font-size:84px;line-height:1.1}
.stamp2{display:inline-block;margin-top:6px;border:5px solid #1a9b5b;color:#59f08a;font-size:36px;font-weight:900;padding:2px 18px;transform:rotate(-8deg);opacity:0}
.vis.on .stamp2{animation:stampin2 .6s .3s both}
@keyframes stampin2{0%{transform:scale(3) rotate(-8deg);opacity:0}100%{transform:scale(1) rotate(-8deg);opacity:1}}
.gt2{margin-top:10px;font-size:18px;font-weight:700;color:#ffe066}
.streak{display:flex;gap:8px;justify-content:center;margin-top:10px}
.streak b{background:#1a9b5b;color:#fff;border:3px solid var(--ink);padding:4px 10px;font-size:15px;opacity:0}
.vis.on .streak b{animation:fadein .4s forwards}
.vis.on .streak b:nth-child(1){animation-delay:.3s}.vis.on .streak b:nth-child(2){animation-delay:.9s}.vis.on .streak b:nth-child(3){animation-delay:1.5s}
@keyframes fadein{to{opacity:1}}
.crown{display:inline-block;animation:sfloat 1.6s ease-in-out infinite}
@keyframes sfloat{50%{transform:translateY(-10px) scale(1.08)}}

/* ---- 가로 화면: iframe 비율이 가로형(5:4 이상)일 때 적용 ---- */
@media (min-aspect-ratio:5/4){
#bldg{left:0;right:0;margin:0 auto;width:min(156%,112vh)}
#dlg{left:10%;right:10%;min-height:30%}
#txt{font-size:clamp(16px,3.7vh,22px);padding:22px 52px 14px 28px}
.bed{left:0;right:0;margin:0 auto;width:min(90%,760px)}
.win{width:min(36%,300px)}
.bcard{left:0;right:0;margin:0 auto;width:min(76%,400px)}
.ch{width:min(31%,36vh)}
#c_judge{left:calc(50% - min(31%,36vh)/2) !important}
#c_pros{left:calc(50% - min(31%,36vh)*1.5 - 12px) !important}
#c_law{left:calc(50% + min(31%,36vh)*.5 + 12px) !important;right:auto !important}
.gbox{max-width:420px}
}
</style></head><body>
<div id="scene">
 <div class="cloud" style="top:9%;animation-delay:-6s"></div><div class="cloud" style="top:20%;animation-duration:46s;animation-delay:-22s"></div>
 <div id="cam">
  <div id="bldg"><svg viewBox="0 0 160 120" shape-rendering="crispEdges" preserveAspectRatio="xMidYMax meet">
   <rect x="0" y="22" width="52" height="98" fill="#cfc8b6"/><rect x="108" y="22" width="52" height="98" fill="#cfc8b6"/>
   <rect x="0" y="22" width="52" height="4" fill="#efe9d6"/><rect x="108" y="22" width="52" height="4" fill="#efe9d6"/>
   <g fill="#3a3f5c"><rect x="6" y="32" width="6" height="9"/><rect x="18" y="32" width="6" height="9"/><rect x="30" y="32" width="6" height="9"/><rect x="42" y="32" width="6" height="9"/>
   <rect x="6" y="48" width="6" height="9"/><rect x="18" y="48" width="6" height="9"/><rect x="30" y="48" width="6" height="9"/><rect x="42" y="48" width="6" height="9"/>
   <rect x="6" y="64" width="6" height="9"/><rect x="18" y="64" width="6" height="9"/><rect x="30" y="64" width="6" height="9"/><rect x="42" y="64" width="6" height="9"/>
   <rect x="112" y="32" width="6" height="9"/><rect x="124" y="32" width="6" height="9"/><rect x="136" y="32" width="6" height="9"/><rect x="148" y="32" width="6" height="9"/>
   <rect x="112" y="48" width="6" height="9"/><rect x="124" y="48" width="6" height="9"/><rect x="136" y="48" width="6" height="9"/><rect x="148" y="48" width="6" height="9"/>
   <rect x="112" y="64" width="6" height="9"/><rect x="124" y="64" width="6" height="9"/><rect x="136" y="64" width="6" height="9"/><rect x="148" y="64" width="6" height="9"/></g>
   <rect x="40" y="2" width="80" height="118" fill="#d9d2c0"/><rect x="44" y="0" width="72" height="4" fill="#efe9d6"/>
   <rect x="46" y="6" width="68" height="3" fill="#bdb5a0"/><rect x="50" y="9" width="60" height="3" fill="#bdb5a0"/>
   <rect x="46" y="12" width="68" height="60" fill="#c8c0ac"/>
   <rect x="52" y="16" width="56" height="52" fill="#d9d2c0"/>
   <circle cx="80" cy="40" r="20" fill="#1f5ea8" stroke="#e8b84a" stroke-width="3"/><circle cx="80" cy="40" r="13" fill="#2f7cd0"/>
   <rect x="70" y="35" width="20" height="10" fill="#fff"/><text x="80" y="44" font-size="9" font-weight="900" text-anchor="middle" fill="#1f5ea8" font-family="sans-serif">法</text>
   <g fill="#efe9d6"><rect x="42" y="76" width="7" height="44"/><rect x="56" y="76" width="7" height="44"/><rect x="97" y="76" width="7" height="44"/><rect x="111" y="76" width="7" height="44"/></g>
   <rect x="38" y="72" width="84" height="6" fill="#efe9d6"/><rect x="38" y="78" width="84" height="3" fill="#8f8873"/>
   <rect x="64" y="82" width="32" height="38" fill="#1c1e33"/><rect x="66" y="84" width="28" height="3" fill="#3a3f5c"/>
   <rect x="79" y="84" width="2" height="36" fill="#0d0f26"/>
   <rect x="22" y="108" width="18" height="12" fill="#2f7a3d"/><rect x="26" y="104" width="10" height="4" fill="#2f7a3d"/>
   <rect x="120" y="108" width="18" height="12" fill="#2f7a3d"/><rect x="124" y="104" width="10" height="4" fill="#2f7a3d"/>
  </svg></div>
  <div id="stairs"></div>
 </div>
 <div id="v_bed" class="vis on"><div class="stars"></div><div class="win"><div class="moon"></div></div><div class="clock">3:07</div><div class="floorb"></div>
  <div class="bed"><div class="pillow"></div><div class="blanket" id="blanket"></div><div class="feet" id="feet">🦶</div></div>
  <div class="think" id="think">😱 그때 내가 왜 그랬지…!!</div><div class="dropcard" id="dropcard">🪪</div></div>
 <div id="v_card" class="vis"><div class="bcard" id="bcard"><div class="shine"></div>
  <div class="front"><div class="bc-logo">⚖️</div><div class="bc-t">이불킥 법정</div><div class="bc-s">당신의 흑역사,<br>무죄로 만들어 드립니다</div><div class="bc-n">평판 방어 전문 · 변호사 우기기</div></div>
  <div class="back"><div class="bc-hand">“오늘 새벽,<br>법원 정문 계단 위에서<br>기다리겠습니다.”</div></div></div></div>
 <div id="door"><div class="hallfloor"></div>
  <div class="ch" id="c_pros" style="left:2%"><div class="nm">차냉정 검사</div></div>
  <div class="ch" id="c_judge" style="left:34.5%"><div class="nm">서판결 판사</div></div>
  <div class="ch" id="c_law" style="right:2%"><div class="nm">우기기 변호사</div></div>
  <div class="dl"></div><div class="dr"></div></div>
 <div id="v_gauge" class="vis ov"><div class="gbox"><div class="gt">🏆 내 평판</div><div class="gbar"><i id="gfill"></i></div><div class="gv" id="gv">100</div>
  <div class="ranks"><span>👑</span><span>🟢</span><span>🟡</span><span>🟠</span><span class="cur">🔴</span></div><div class="gc">인간 흑역사 박물관 직전…!</div></div></div>
 <div id="v_goal" class="vis ov"><div class="gbox"><div class="big">🎯</div><div class="stamp2">무죄!</div><div class="gt2">평판 ⬆️ · 랭크 방어!</div></div></div>
 <div id="v_crown" class="vis ov"><div class="gbox"><div class="big crown">👑</div><div class="gt2">이불킥 청정수</div>
  <div class="streak"><b>무죄</b><b>무죄</b><b>무죄</b></div><div class="gc">무죄 연승이면 도전할 수 있어요!</div></div></div>
 <div id="stepbar" class="pill">계단 <b id="sn">0</b>/9</div>
 <div id="auto" class="pill">AUTO ▶</div><div id="mute" class="pill">🔊</div>
 <div id="end" class="pill">▼ 아래 [🏛️ 로비로 입장] 버튼을 눌러 주세요</div>
 <div id="replay" class="pill">↻ 다시 보기</div>
 <div id="pop"></div><div id="flash"></div>
 <div id="dlg"><div id="tag"><div id="tagin">나</div></div><div id="dlgin"><div id="txt"></div></div><div id="arrow">»</div></div>
 <div id="vig"></div>
 <div id="start"><h2>이불킥 법정</h2><p>▶ PRESS START</p><small>1인칭 스토리 · 화면을 클릭하세요</small></div>
</div>
<script>
const D=__DATA__;
const $=id=>document.getElementById(id);
const scene=$('scene');
const S=[
 {v:'bed',k:'t',x:'새벽 3시 7분. 나는 이불 속에서 도무지 잠들지 못하고 있었다.'},
 {v:'bed',k:'t',fx:'think',x:'눈을 감으면 자꾸 그날의 일이 떠오른다. 그 글, 그 사진, 그 한마디…'},
 {v:'bed',k:'t',fx:'kick',x:'“으아아악!” 나는 이불을 발로 뻥뻥 걷어찼다. 아무리 차도 흑역사는 사라지지 않았다.'},
 {v:'bed',k:'t',fx:'drop',x:'그때, 발끝에 딱딱한 무언가가 걸렸다. 이불 틈에서 종이 한 장이 툭 떨어졌다.'},
 {v:'card',k:'t',fx:'paper',x:'…명함이었다. 내 것이 아니다. 누가, 언제, 이걸 내 이불 속에…?'},
 {v:'card',k:'t',x:'〈이불킥 법정 — 당신의 흑역사, 무죄로 만들어 드립니다. 평판 방어 전문 · 변호사 우기기〉'},
 {v:'card',k:'t',fx:'flip',x:'뒷면에는 손글씨가 적혀 있었다. “오늘 새벽, 법원 정문 계단 위에서 기다리겠습니다.”'},
 {v:'card',k:'t',x:'수상하다. 하지만 이대로 평생 이불만 걷어차며 살 수는 없다. 나는 외투를 걸치고 집을 나섰다.'},
 {v:'court',k:'t',x:'…와.'},
 {v:'court',k:'t',x:'눈앞에 거대한 법원이 우뚝 서 있다. 고개를 한참 젖혀야 꼭대기가 보인다.'},
 {v:'court',k:'t',x:'명함에 적힌 곳이 틀림없다. 저 둥근 문양 아래에서, 누군가 나를 기다리고 있다.'},
 {v:'court',k:'s',x:'뚜벅… 계단이 생각보다 높다.'},
 {v:'court',k:'s',x:'뚜벅… 이 명함, 장난이 아니길 바랄 뿐이다.'},
 {v:'court',k:'s',x:'뚜벅… 그날 올린 그 글, 그 한마디가 자꾸 떠오른다.'},
 {v:'court',k:'s',x:'뚜벅… 지금도 생각하면 발가락이 오그라든다.'},
 {v:'court',k:'s',x:'뚜벅… 다들 이미 잊었길 바랐는데.'},
 {v:'court',k:'s',x:'뚜벅… 누군가는 분명 캡처해 뒀겠지.'},
 {v:'court',k:'s',x:'뚜벅… 내 평판은 그날 이후로 바닥을 기고 있다.'},
 {v:'court',k:'s',x:'뚜벅… 이제 도망칠 곳도 없다. 한 계단만 더.'},
 {v:'court',k:'s',x:'뚜벅… 드디어, 문 앞이다.'},
 {v:'hall',k:'d',x:'끼이이익—! 무겁고 커다란 문이 천천히 열렸다.'},
 {v:'hall',k:'t',x:'환하게 쏟아지는 빛 속에서, 세 사람의 그림자가 나를 바라보고 있었다.'},
 {v:'judge',k:'t',x:'가운데에는 서판결 판사. 표정은 차분한데, 벌써 잔소리가 시작될 것 같은 눈빛이다.'},
 {v:'pros',k:'t',x:'왼쪽에는 차냉정 검사. 서류를 넘기는 손끝이 얼음처럼 차갑다.'},
 {v:'law',k:'t',x:'오른쪽에는 우기기 변호사. 나를 보더니 눈물을 글썽이며 활짝 웃는다. …왜지?'},
 {v:'law',k:'t',x:'맞다. 그 명함의 주인이 바로 이 사람이었다.'},
 {v:'law',k:'t',w:'우기기 변호사',x:'“기다리고 있었어요! 당신의 흑역사, 제가 어떻게든 무죄로 만들어 드릴게요!”'},
 {v:'gauge',k:'t',x:'나는 안다. 그날의 흑역사 때문에 내 평판과 이불킥 랭크는 이미 바닥을 기고 있다는 것을.'},
 {v:'goal',k:'g',x:'그래서 오늘의 목표는 단 하나! 어떻게든 무죄를 받아내서, 평판과 이불킥 랭크를 지켜내는 것이다!'},
 {v:'crown',k:'g',x:'무죄를 연달아 받아내면… 최고 랭크 👑 [이불킥 청정수]가 될 수도 있다고 한다.'},
 {v:'enter',k:'t',x:'…좋아. 심호흡을 하고 한 발 내디뎠다. 이제, 법정 안으로 들어가 보자.'}
];
const STEPS=S.filter(e=>e.k==='s').length;
$('c_judge').insertAdjacentHTML('afterbegin','<svg viewBox="0 0 100 150" shape-rendering="crispEdges"><polygon points="4,150 14,76 86,76 96,150" fill="#2f5a46"/><polygon points="38,76 50,100 62,76" fill="#f3ead0"/><rect x="46" y="100" width="8" height="50" fill="#d9b85a"/><rect x="29" y="12" width="42" height="44" fill="#f0c9a0"/><rect x="22" y="22" width="9" height="22" fill="#fff"/><rect x="69" y="22" width="9" height="22" fill="#fff"/><rect x="38" y="4" width="24" height="10" fill="#fff"/><rect x="33" y="26" width="14" height="5" fill="#fff"/><rect x="53" y="26" width="14" height="5" fill="#fff"/><rect x="32" y="33" width="16" height="12" fill="none" stroke="#c9a24d" stroke-width="2"/><rect x="52" y="33" width="16" height="12" fill="none" stroke="#c9a24d" stroke-width="2"/><rect x="38" y="37" width="5" height="5" fill="#222"/><rect x="58" y="37" width="5" height="5" fill="#222"/><polygon points="36,52 64,52 62,88 50,100 38,88" fill="#f1f1f6"/><polygon points="34,48 66,48 62,56 50,53 38,56" fill="#fff"/><rect class="mouth" x="43" y="59" width="14" height="4" fill="#7a3b3b"/></svg>');
$('c_pros').insertAdjacentHTML('afterbegin','<svg viewBox="0 0 100 150" shape-rendering="crispEdges"><polygon points="6,150 16,76 84,76 94,150" fill="#1d1f2b"/><polygon points="38,76 50,108 62,76" fill="#e9f3ff"/><polygon points="46,86 54,86 52,130 48,130" fill="#4fc3f7"/><rect x="30" y="20" width="40" height="42" fill="#e8d4c4"/><polygon points="28,34 28,10 40,6 60,6 72,10 72,34 64,24 36,24" fill="#6fa8dc"/><rect x="36" y="39" width="10" height="3" fill="#112"/><rect x="54" y="39" width="10" height="3" fill="#112"/><rect x="33" y="35" width="16" height="10" fill="#bfe9ff" fill-opacity=".35" stroke="#9ad" stroke-width="1.5"/><rect x="51" y="35" width="16" height="10" fill="#bfe9ff" fill-opacity=".35" stroke="#9ad" stroke-width="1.5"/><rect class="mouth" x="45" y="53" width="10" height="2" fill="#6a3b3b"/></svg>');
$('c_law').insertAdjacentHTML('afterbegin','<svg viewBox="0 0 100 150" shape-rendering="crispEdges"><polygon points="6,150 16,76 84,76 94,150" fill="#e0a82e"/><polygon points="36,76 50,104 64,76" fill="#fff"/><polygon points="45,84 55,84 57,120 50,128 43,120" fill="#7b2cbf"/><rect x="22" y="110" width="6" height="6" fill="#7b2cbf"/><rect x="72" y="124" width="6" height="6" fill="#7b2cbf"/><rect x="30" y="20" width="40" height="42" fill="#f2c79b"/><rect x="18" y="0" width="64" height="26" fill="#f26b1d"/><rect x="12" y="8" width="76" height="20" fill="#f26b1d"/><rect x="22" y="26" width="8" height="14" fill="#f26b1d"/><rect x="70" y="26" width="8" height="14" fill="#f26b1d"/><rect x="34" y="32" width="14" height="14" fill="#fff" stroke="#222" stroke-width="2"/><rect x="52" y="32" width="14" height="14" fill="#fff" stroke="#222" stroke-width="2"/><rect x="39" y="37" width="4" height="4" fill="#222"/><rect x="57" y="37" width="4" height="4" fill="#222"/><rect class="mouth" x="38" y="50" width="24" height="6" fill="#7a1f2b"/><rect x="40" y="50" width="20" height="2" fill="#fff"/></svg>');
/* 계단: 아래로 갈수록 두꺼워지는 원근감 */
(function(){const n=9,w=[...Array(n)].map((_,i)=>1+i*.45),sum=w.reduce((a,b)=>a+b,0);let y=0;const box=$('stairs');
 w.forEach(v=>{const h=v/sum*100,e=document.createElement('i');e.style.top=y+'%';e.style.height=h+'%';e.style.left=(8-y*.08)+'%';e.style.right=(8-y*.08)+'%';box.appendChild(e);y+=h})})();
/* 사운드 (WebAudio 합성) */
let AC=null,muted=!!D.mute,auto=true;
function ac(){if(!AC){try{AC=new(window.AudioContext||window.webkitAudioContext)()}catch(e){}}return AC}
function beep(f,d,v,t){if(muted)return;const a=ac();if(!a)return;const o=a.createOscillator(),g=a.createGain();o.type=t||'square';o.frequency.value=f;g.gain.value=v||.04;o.connect(g);g.connect(a.destination);o.start();g.gain.exponentialRampToValueAtTime(.0001,a.currentTime+d);o.stop(a.currentTime+d)}
function footstep(n){if(muted)return;const a=ac();if(!a)return;const len=Math.floor(a.sampleRate*.13),b=a.createBuffer(1,len,a.sampleRate),c=b.getChannelData(0);for(let i=0;i<len;i++)c[i]=(Math.random()*2-1)*Math.pow(1-i/len,2.5);
 const s=a.createBufferSource();s.buffer=b;const f=a.createBiquadFilter();f.type='lowpass';f.frequency.value=n%2?700:520;const g=a.createGain();g.gain.value=.55;s.connect(f);f.connect(g);g.connect(a.destination);s.start();
 const o=a.createOscillator(),g2=a.createGain();o.frequency.setValueAtTime(n%2?120:95,a.currentTime);o.frequency.exponentialRampToValueAtTime(45,a.currentTime+.12);g2.gain.setValueAtTime(.5,a.currentTime);g2.gain.exponentialRampToValueAtTime(.001,a.currentTime+.14);o.connect(g2);g2.connect(a.destination);o.start();o.stop(a.currentTime+.15)}
function creak(){if(muted)return;const a=ac();if(!a)return;const o=a.createOscillator(),g=a.createGain();o.type='sawtooth';o.frequency.setValueAtTime(90,a.currentTime);o.frequency.linearRampToValueAtTime(55,a.currentTime+1.6);g.gain.setValueAtTime(.05,a.currentTime);g.gain.linearRampToValueAtTime(.001,a.currentTime+1.7);o.connect(g);g.connect(a.destination);o.start();o.stop(a.currentTime+1.7)}
$('mute').onclick=e=>{e.stopPropagation();muted=!muted;$('mute').textContent=muted?'🔇':'🔊'};
$('mute').textContent=muted?'🔇':'🔊';
$('auto').onclick=e=>{e.stopPropagation();auto=!auto;$('auto').textContent=auto?'AUTO ▶':'AUTO ■';if(auto)queueAuto()};
/* 진행 엔진 */
let started=false,i=-1,typing=false,tm=null,full='',busy=false,sn=0,at=null,ended=false;
function setTag(e){$('tagin').textContent=e.w||(e.k==='g'?'다짐':'나')}
function stopType(){clearInterval(tm);typing=false;$('txt').textContent=full;$('dlgin').scrollTop=$('dlgin').scrollHeight;$('arrow').style.visibility='visible';
 if(i===S.length-1){ended=true;$('end').style.display='block';$('replay').style.display='block';$('stepbar').style.display='none'}else queueAuto()}
function type(t){typing=true;full=t;let k=0;$('txt').textContent='';$('arrow').style.visibility='hidden';tm=setInterval(()=>{k++;$('txt').textContent=t.slice(0,k);$('dlgin').scrollTop=$('dlgin').scrollHeight;if(k%2===0)beep(420+Math.random()*100,.035);if(k>=t.length)stopType()},D.speed||30)}
function queueAuto(){clearTimeout(at);if(!auto||ended)return;at=setTimeout(()=>{if(!typing&&!busy)adv()},1700)}
function popText(t,alt){const p=$('pop');p.textContent=t;p.style.marginLeft=alt?'-60px':'60px';p.classList.remove('on');void p.offsetWidth;p.classList.add('on')}
function bob(){const c=$('cam');c.classList.remove('bob');void c.offsetWidth;c.classList.add('bob')}
function flash(){const f=$('flash');f.classList.remove('on');void f.offsetWidth;f.classList.add('on')}
let curV='bed';
const OV={bed:'v_bed',card:'v_card',gauge:'v_gauge',goal:'v_goal',crown:'v_crown'};
function rev(ids){['c_pros','c_judge','c_law'].forEach(id=>$(id).classList.toggle('rev',ids.includes(id)))}
function startGauge(){const f=$('gfill');f.style.transition='none';f.style.width='62%';$('gv').textContent='100';void f.offsetWidth;f.style.transition='width 2.4s ease-in';f.style.width='9%';let n=100;const t=setInterval(()=>{n-=4;if(n<=12){n=12;clearInterval(t)}$('gv').textContent=n},100)}
function setScene(v){Object.keys(OV).forEach(k=>$(OV[k]).classList.toggle('on',k===v));
 if(v==='hall')rev([]);else if(v==='judge')rev(['c_judge']);else if(v==='pros')rev(['c_judge','c_pros']);
 else if(['law','gauge','goal','crown','enter'].includes(v))rev(['c_judge','c_pros','c_law']);
 if(v==='gauge')startGauge()}
function paper(){if(muted)return;const a=ac();if(!a)return;const len=Math.floor(a.sampleRate*.12),b=a.createBuffer(1,len,a.sampleRate),c=b.getChannelData(0);for(let i=0;i<len;i++)c[i]=(Math.random()*2-1)*Math.pow(1-i/len,1.5);const s=a.createBufferSource();s.buffer=b;const f=a.createBiquadFilter();f.type='highpass';f.frequency.value=1800;const g=a.createGain();g.gain.value=.35;s.connect(f);f.connect(g);g.connect(a.destination);s.start()}
function doFx(x){
 if(x==='think'){$('think').classList.add('on');beep(520,.1,.05);setTimeout(()=>beep(390,.14,.05),120)}
 else if(x==='kick'){$('blanket').classList.add('kick');$('feet').classList.add('kick');[0,300,600].forEach((d,j)=>setTimeout(()=>{footstep(j);popText('뻥!',j%2)},d))}
 else if(x==='drop'){$('blanket').classList.remove('kick');$('feet').classList.remove('kick');$('dropcard').classList.add('on');paper()}
 else if(x==='paper'){$('bcard').classList.remove('flip');paper()}
 else if(x==='flip'){$('bcard').classList.add('flip');paper()}}
function show(n){const e=S[n];busy=true;clearTimeout(at);setTag(e);$('txt').textContent='';$('arrow').style.visibility='hidden';let wait=250;
 if(e.v&&e.v!==curV){curV=e.v;setScene(e.v);wait=800;if(e.v==='enter'){flash();[660,880,1320].forEach((f,j)=>setTimeout(()=>beep(f,.22,.06),j*140))}}
 if(e.k==='s'){sn++;scene.style.setProperty('--k',sn);$('sn').textContent=sn;$('stepbar').style.display='block';bob();popText(sn%2?'뚜벅…':'뚜벅!',sn%2);footstep(sn);wait=Math.max(wait,700)}
 else if(e.k==='d'){$('stepbar').style.display='none';const d=$('door');d.style.display='block';void d.offsetWidth;d.classList.add('open');creak();wait=1900}
 else if(e.k==='g'){flash();popText(e.v==='goal'?'🎯 목표!':'👑 최고 랭크!',0);[660,880,1320].forEach((f,j)=>setTimeout(()=>beep(f,.22,.06),j*140));wait=Math.max(wait,800)}
 if(e.fx)doFx(e.fx);
 setTimeout(()=>{busy=false;type(e.x)},wait)}
function adv(){if(!started||busy||ended)return;clearTimeout(at);if(typing){stopType();return}if(i<S.length-1){i++;show(i)}}
function reset(){clearTimeout(at);clearInterval(tm);sn=0;ended=false;typing=false;busy=false;curV='bed';scene.style.setProperty('--k',0);
 $('door').style.display='none';$('door').classList.remove('open');setScene('bed');rev([]);
 ['blanket','feet'].forEach(id=>$(id).classList.remove('kick'));$('think').classList.remove('on');$('dropcard').classList.remove('on');$('bcard').classList.remove('flip');
 $('end').style.display='none';$('replay').style.display='none';$('stepbar').style.display='none';$('txt').textContent='';i=0;show(0)}
$('replay').onclick=e=>{e.stopPropagation();reset()};
scene.addEventListener('click',adv);
document.addEventListener('keydown',e=>{if(e.code==='Space'||e.code==='Enter'){e.preventDefault();adv()}});
$('start').addEventListener('click',e=>{e.stopPropagation();started=true;ac();beep(880,.12);$('start').style.display='none';i=0;show(0)});
</script></body></html>"""

def render_story(mute=False, speed=30, height=640):
    payload = json.dumps({"mute": mute, "speed": speed}, ensure_ascii=False).replace("</", "<\\/")
    components.html(STORY_TEMPLATE.replace("__DATA__", payload), height=height, scrolling=False)
