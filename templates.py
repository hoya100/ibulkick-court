"""templates.py — 화면에 그려지는 HTML/JS 템플릿 모음.

재판 연출(VN_TEMPLATE: 공방·판결 + AI 응답 대기 중 '판사가 서류를 살피는' 연출), 스토리 연출(STORY_TEMPLATE),
로비 연출(LOBBY_TEMPLATE), 판결 결과 패널, 타이틀 화면.

캐릭터의 외모(머리·표정·의상·색)는 이 파일에 적혀 있지 않고, characters.py 의 palette/style 데이터를 읽어서
SPRITES_JS(공용 스프라이트 그리기 코드)가 그립니다. 캐릭터를 바꾸려면 characters.py 를 고치세요.
연출·사운드·픽셀 디자인을 손볼 때는 여기를 수정하세요.
"""

import html
import json

import streamlit.components.v1 as components

from characters import expressions_payload, sprite_payload
from stage import OVERLAYS, SCENE_HTML, STAGE_CSS, STAGE_JS, WAIT_HTML

# 스프라이트 그리기 엔진의 버전. characters.py 의 SPRITE_DATA_VERSION 과 같아야 합니다.
SPRITE_ENGINE_VERSION = 5


# =================================================================
# HTML 조각
# =================================================================

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
.who svg,.who canvas{display:block;width:100%;height:auto}.hdc{image-rendering:pixelated}
.talk svg,.talk canvas{animation:bob .3s steps(2) infinite}
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
#sm{display:none;position:absolute;inset:0;z-index:60;background:#000b;align-items:center;justify-content:center;cursor:default}
#sm.on{display:flex}
#smbox{width:min(300px,84%);background:#151b4a;border:4px solid #ffd23f;box-shadow:6px 6px 0 #000;padding:16px 14px;color:#fff;text-align:center}
#smbox h3{margin:0 0 12px;font-size:18px;color:#ffe066;letter-spacing:2px}
#smbox button{display:block;width:100%;margin:8px 0;padding:11px 6px;font:inherit;font-size:15px;color:#fff;background:#3a4a9a;border:3px solid #0d0f26;box-shadow:3px 3px 0 #000;cursor:pointer}
#smbox button:active{transform:translate(2px,2px);box-shadow:1px 1px 0 #000}
#smbox #sm_go{background:#2f9e57}#smbox #sm_quit{background:#b5382e}#smbox #sm_quit.sure{background:#ff2b1c;animation:smblink .6s infinite alternate}
@keyframes smblink{to{filter:brightness(1.4)}}
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
/* ---- 대기 연출(mode='wait'): 판사가 서류를 살피며 고민하는 몰입형 장면 ---- */
#wait{display:none;position:absolute;inset:0;overflow:hidden;background:#2a1a10}
html.wait #wait{display:block;animation:wfade .9s}
html.wait #scene{display:none}
@keyframes wfade{from{opacity:0}to{opacity:1}}
.w-wall{position:absolute;left:0;right:0;top:0;bottom:16%;background:repeating-linear-gradient(90deg,#8a5a34 0 56px,#7a4c2a 56px 60px)}
.w-wall:after{content:"";position:absolute;inset:0;background:linear-gradient(#0000 30%,#0006)}
.w-wain{position:absolute;left:0;right:0;bottom:16%;height:20%;background:#5a3a22;border-top:6px solid #d9b85a}
.w-shelf{position:absolute;top:10%;bottom:34%;width:17%;border:5px solid #0d0f26;background:repeating-linear-gradient(#0000 0 52px,#2a1a10 52px 60px),repeating-linear-gradient(90deg,#b3261a 0 9px,#2f5a8a 9px 17px,#d9b85a 17px 22px,#2f7a3d 22px 31px,#7b2cbf 31px 38px,#e0a82e 38px 43px)}
.w-shelf.l{left:3%}.w-shelf.r{right:3%}
.w-seal{position:absolute;left:50%;top:4%;transform:translateX(-50%);width:84px;height:84px;border-radius:50%;background:radial-gradient(#fff,#cfd6e6);border:5px solid #c9a24d;box-shadow:0 0 0 4px #7a5a1e;display:flex;align-items:center;justify-content:center;font-size:40px;font-weight:900;color:#1f5ea8}
.w-lamp{position:absolute;left:0;right:0;top:0;height:70%;background:radial-gradient(ellipse at 50% 0%,#ffe9a866,#0000 62%)}
.dust{position:absolute;width:3px;height:3px;background:#ffe9a8;opacity:0;animation:dust var(--d,12s) linear infinite;animation-delay:var(--l,0s)}
@keyframes dust{0%{transform:translate(0,0);opacity:0}15%{opacity:.7}85%{opacity:.6}100%{transform:translate(30px,-130px);opacity:0}}
#w-cw{position:absolute;left:50%;bottom:0;transform:translateX(-50%);transform-origin:50% 100%;animation:wsway 10s ease-in-out infinite}
@keyframes wsway{0%,100%{transform:translateX(-50%) scale(1)}50%{transform:translateX(-50%) scale(1.012)}}
#jchara{display:block;position:relative}#jfig{position:absolute;left:0;top:0;width:100%;height:100%;image-rendering:pixelated}
#w-bubble{position:absolute;left:58%;bottom:100%;margin-bottom:14px;background:#fff;color:#0d0f26;font-size:clamp(13px,2.4vh,17px);font-weight:700;padding:8px 14px;opacity:0;transform:translateY(6px);transition:opacity .4s,transform .4s;width:max-content;max-width:min(340px,72vw);white-space:normal;word-break:keep-all;overflow-wrap:break-word;line-height:1.45;box-shadow:0 -3px 0 #0d0f26,0 3px 0 #0d0f26,-3px 0 0 #0d0f26,3px 0 0 #0d0f26,4px 8px 0 0 #0006}
#w-bubble.on{opacity:1;transform:none}
#w-bubble:after{content:"";position:absolute;left:16px;bottom:-12px;border:6px solid transparent;border-top:8px solid #0d0f26}
#w-bench{position:absolute;left:0;right:0;bottom:0;background:#5a3a22;border-top:6px solid #8a5a34;box-shadow:inset 0 6px 0 #d9b85a55}
#w-vig{position:absolute;inset:0;pointer-events:none;background:repeating-linear-gradient(#0000 0 2px,#0001 2px 3px);box-shadow:inset 0 0 120px #000a}
/*__STAGE_CSS__*/
</style></head><body>
<!--__WAIT__-->
<div id="scene" data-cam="J">
<!--__SCENE__-->
<!--__OVERLAYS__-->
 <div id="hint"></div><div id="phase"></div><div id="shout"></div><div id="frame"></div>
 <div id="dlg"><div id="tag"><div id="tagin">재판관</div></div><div id="box"></div><div id="boxin"><div id="txt"></div></div><div id="arrow">»</div></div>
 <div id="flash"></div><div id="crt"></div>
 <div id="mute">⚙️</div>
 <div id="sm"><div id="smbox"><h3>⚙️ 설 정</h3><button id="sm_snd">🔊 효과음 켜짐</button><button id="sm_go">▶ 계속하기</button><button id="sm_quit">🏳️ 재판 포기 (로비로)</button></div></div>
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
/*__SPRITES__*/
/* ---- 변명 입력칸 제어: 연출(iframe)이 부모 화면의 표식(.st-key-excuse_gate)에 상태를 적어 두면, CSS가 입력창을 숨기거나 올려 준다.
        부모 화면에 접근할 수 없는 환경이면 아무것도 하지 않고(= 입력창은 항상 보임/6초 뒤 자동 표시) 게임은 그대로 진행된다. ---- */
function exSet(attr,after){let n=0;const go=()=>{n++;let m=null;try{m=window.parent.document.querySelector('.st-key-excuse_gate')}catch(e){return true}
 if(m){m.setAttribute(attr,'1');if(after)after();return true}return n>25};if(!go()){const iv=setInterval(()=>{if(go())clearInterval(iv)},200)}}
function exOpen(){if(D.mode!=='debate')return;exSet('data-open',()=>{setTimeout(()=>{try{const ta=window.parent.document.querySelector('[data-testid="stChatInput"] textarea');if(ta)ta.focus({preventScroll:true})}catch(e){}},650)})}
if(D.mode==='debate')exSet('data-gate');
if(D.mode==='wait'){document.documentElement.className='wait';(function(){
 const NS='http://www.w3.org/2000/svg',CX=100,INK='#0d0f26',GOLD='#d9b85a';
 const g=id=>document.getElementById(id),svg=g('jchara');
 const E=(tag,at,p)=>{const e=document.createElementNS(NS,tag);for(const k in at)e.setAttribute(k,at[k]);(p||svg).appendChild(e);return e};
 const A=(p,x,y,w,h,f,o)=>E('rect',Object.assign({x:x,y:y,width:w,height:h,fill:f},o||{}),p);
 const R=(p,dx,y,w,h,f,o)=>A(p,CX+dx,y,w,h,f,o);
 const OUT={stroke:INK,'stroke-width':2},THIN={stroke:INK,'stroke-width':1.2};
 const HDM=(D.cast.JUDGE.render||{}).mode==='pixel_hd';   // pixel_hd: 픽셀 단위 고해상도 도트(캔버스) / svg: 도형 도트
 let F=null,hdF=null,hdCtx=null,chairC=null,pal,SLV,st;
 if(HDM){hdF=hdBuildFigure('JUDGE');pal=hdF.pal;SLV=hdF.sleeve;st=hdF.style;const cv=g('jfig');cv.width=200;cv.height=160;hdCtx=cv.getContext('2d');hdCtx.imageSmoothingEnabled=false}   // 의자는 법정 사진 속 의자를 씀
 else{
  /* 의자 등받이 */
  const gChair=E('g');R(gChair,-52,10,104,8,GOLD,OUT);R(gChair,-50,16,100,130,'#5a3a22',OUT);R(gChair,-42,24,84,114,'#6b4528');
  for(let r=0;r<4;r++)for(let c=0;c<5;c++)R(gChair,-32+c*16,34+r*26,4,4,GOLD);
  /* 판사 서판결: 머리·표정·법복은 characters.py 데이터(palette/style)대로 그린다 */
  F=buildFigure(svg,'JUDGE');pal=F.pal;SLV=F.sleeve;st=F.style;svg.setAttribute('shape-rendering',F.render.shape_rendering||'crispEdges');
 }
 const gArmL=E('g'),gArmR=E('g'),gPL=E('g'),gPR=E('g'),gDesk=E('g'),gTool=E('g');
 /* 팔: 어깨→팔꿈치→손 (역기구학으로 각도 계산). 소매 색·폭은 의상 데이터를 따른다 */
 const SL=[CX-st.shoulder_dx,st.shoulder_y],SR=[CX+st.shoulder_dx,st.shoulder_y],L1=26,L2=27.5;
 function arm(gr,S){const w=SLV.w,w2=w-2;const up=E('g',{},gr);A(up,S[0]-w/2,104,w,28,SLV.color,OUT);A(up,S[0]-w/2,104,w,5,pal.robe_light||pal.suit_light||SLV.color);const fo=E('g',{},up);A(fo,S[0]-w2/2,130,w2,26,SLV.color,OUT);A(fo,S[0]-w2/2-1,150,w2+2,4,SLV.cuff,OUT);A(fo,S[0]-5,154,10,11,pal.skin,OUT);return {up:up,fo:fo}}
 const armL=HDM?null:arm(gArmL,SL),armR=HDM?null:arm(gArmR,SR);
 /* 손에 든 서류 / 돋보기 / 펜 */
 function paper(gr){A(gr,-15,-42,30,42,'#fff',OUT);const ls=[];for(let i=0;i<7;i++)ls.push(A(gr,-11,-37+i*5.4,22,1.8,'#9aa0bb'));E('polygon',{points:'15,-42 15,-34 7,-42',fill:'#dfe3f2'},gr);return ls}
 const linesL=paper(gPL),linesR=paper(gPR);
 function newPage(){[linesL,linesR].forEach(ls=>ls.forEach(l=>l.setAttribute('width',(8+Math.random()*14).toFixed(1))))}newPage();
 const lens=E('g',{},gTool);E('circle',{cx:0,cy:-16,r:11,fill:'#bfe9ff','fill-opacity':.4,stroke:GOLD,'stroke-width':3},lens);A(lens,-2,-5,4,14,GOLD,THIN);A(lens,-6,-22,4,3,'#fff',{opacity:.8});
 const pen=E('g',{},gTool);A(pen,-1.5,-16,3,18,'#222');A(pen,-1.5,-18,3,3,GOLD);E('polygon',{points:'-1.5,2 1.5,2 0,6',fill:'#222'},pen);
 /* 책상: 서류 더미 · 법봉 · 찻잔 · 명패 */
 A(gDesk,0,134,200,26,'#5a3a22');A(gDesk,0,130,200,6,'#8a5a34');A(gDesk,0,134,200,2,GOLD);A(gDesk,0,154,200,6,'#3f2916');
 R(gDesk,-26,143,52,10,GOLD,OUT);E('text',{x:CX,y:151,'font-size':6.2,'text-anchor':'middle',fill:INK,'font-weight':'bold'},gDesk).textContent=D.cast.JUDGE.display;
 R(gDesk,-88,125,36,5,'#fff',OUT);R(gDesk,-86,120,34,5,'#f3f3ff',OUT);R(gDesk,-84,115,32,5,'#fff',OUT);
 R(gDesk,-52,123,18,7,'#c58a4a',OUT);R(gDesk,-60,126,10,3,'#8a5a34',OUT);
 const mugG=E('g',{transform:'translate('+(CX+70)+' 130)'},gDesk);A(mugG,-7,-14,14,14,'#fff',OUT);A(mugG,7,-11,4,8,'#fff',OUT);A(mugG,-5,-12,10,3,'#8a5a2a');
 const steam=[0,1,2].map(i=>A(mugG,-4+i*4,-20,2,4,'#fff',{opacity:.7}));
 /* 역기구학 */
 const rotOf=a=>Math.atan2(-Math.cos(a),Math.sin(a))*180/Math.PI;
 function ik(S,T){let dx=T[0]-S[0],dy=T[1]-S[1],d=Math.hypot(dx,dy);const maxd=L1+L2-0.6,mind=Math.abs(L1-L2)+2,reach=Math.max(mind,Math.min(maxd,d));
  const base=Math.atan2(dy,dx),cb=(L1*L1+reach*reach-L2*L2)/(2*L1*reach),b=Math.acos(Math.max(-1,Math.min(1,cb)));
  const c=[base+b,base-b].map(a=>({a:a,ey:S[1]+L1*Math.sin(a),ex:S[0]+L1*Math.cos(a)})).sort((p,q)=>q.ey-p.ey)[0];
  const hx=S[0]+reach*Math.cos(base),hy=S[1]+reach*Math.sin(base),fa=Math.atan2(hy-c.ey,hx-c.ex);
  let t1=rotOf(c.a),t2=rotOf(fa)-t1;while(t2>180)t2-=360;while(t2<-180)t2+=360;return {t1:t1,t2:t2,hx:hx,hy:hy,ex:c.ex,ey:c.ey}}
 /* 자세: 서류 읽기 · 넘기기 · 두 장 비교 · 돋보기 · 턱 괴고 고민 · 눈 비비기 · 하품 · 메모 */
 const P={
  read:{L:[CX-38,118],R:[CX+24,128],pl:1,pr:0,tilt:-4,gx:0,gy:4,lid:.3,brow:0,mouth:'flat',lean:1,scan:1},
  flip:{L:[CX-38,118],R:[CX+34,126],pl:1,pr:0,tilt:-3,gx:0,gy:4,lid:.3,brow:0,mouth:'flat',lean:1,scan:1,sweep:1},
  compare:{L:[CX-36,120],R:[CX+36,120],pl:1,pr:1,tilt:-5,gx:-3,gy:3,lid:.2,brow:0,mouth:'flat',lean:0,cmp:1},
  magnify:{L:[CX-30,126],R:[CX+4,124],pl:1,pr:0,tilt:2,gx:0,gy:5,lid:.5,brow:1,mouth:'flat',lean:5,tool:'lens',jit:1},
  ponder:{L:[CX-40,126],R:[CX+10,90],pl:0,pr:0,tilt:6,gx:-3,gy:-2,lid:.2,brow:1,mouth:'hmm',lean:0,stroke:1},
  rub:{L:[CX-40,126],R:[CX+8,56],pl:0,pr:0,tilt:-3,gx:0,gy:2,lid:1,brow:2,mouth:'flat',lean:1,rub:1},
  yawn:{L:[CX-40,126],R:[CX+3,77],pl:0,pr:0,tilt:-5,gx:0,gy:0,lid:1,brow:2,mouth:'open',lean:0},
  write:{L:[CX-28,124],R:[CX+10,127],pl:1,pr:0,tilt:-2,gx:2,gy:5,lid:.35,brow:1,mouth:'flat',lean:3,tool:'pen',scribble:1}
 };
 const cur={R:[CX+24,128],L:[CX-38,118],tilt:0,gx:0,gy:0,lid:0,lean:0,brow:0};
 let tgt=P.read,t=0;const ap=(c,v,k,dt)=>c+(v-c)*(1-Math.exp(-k*dt));
 function render(dt){const p=tgt;
  cur.R[0]=ap(cur.R[0],p.R[0],7,dt);cur.R[1]=ap(cur.R[1],p.R[1],7,dt);cur.L[0]=ap(cur.L[0],p.L[0],7,dt);cur.L[1]=ap(cur.L[1],p.L[1],7,dt);
  cur.tilt=ap(cur.tilt,p.tilt,5,dt);cur.lid=ap(cur.lid,p.lid,8,dt);cur.lean=ap(cur.lean,p.lean,5,dt);cur.brow=ap(cur.brow,p.brow,6,dt);
  let gxT=p.gx,gyT=p.gy,tiltAdd=0,rx=cur.R[0],ry=cur.R[1],lx=cur.L[0],ly=cur.L[1];
  if(p.scan){const f=(t*1.3)%1,line=Math.floor(t*1.3)%3;gxT=-3+f*6;gyT=3+line*0.7}
  if(p.cmp){const side=Math.floor(t/1.8)%2;gxT=side?4:-4;tiltAdd=side?10:0}
  if(p.jit)gxT=Math.sin(t*3)*1.4;
  if(p.stroke){ry+=Math.sin(t*5)*1.6;gxT=-3+Math.sin(t*0.7)*3}
  if(p.rub){rx+=Math.sin(t*10)*2.5;ry+=Math.cos(t*8)*1.5}
  if(p.scribble){rx+=Math.sin(t*8)*3;ry+=Math.cos(t*6)*1.5}
  if(p.sweep)rx=CX+34-((t*1.5)%1)*40;
  cur.gx=ap(cur.gx,gxT,10,dt);cur.gy=ap(cur.gy,gyT,10,dt);
  const a=ik(SL,[lx,ly]),b=ik(SR,[rx,ry]);
  const bob=Math.sin(t*1.6)*0.6,lidv=Math.max(cur.lid,((t%3.9)<0.12)?1:0);
  if(HDM){   // 픽셀 도화지에 의자·인물(머리·몸·팔)을 다시 칠한다. 움직임은 1픽셀 단위로 끊어서 도트다운 느낌을 낸다
   hdF.setBrow(cur.brow);hdF.setGaze(cur.gx,cur.gy);hdF.setLid(lidv);hdF.showMouth(p.mouth);hdCtx.clearRect(0,0,200,160);if(chairC)hdCtx.drawImage(chairC,0,0);
   hdF.render(hdCtx,{tilt:cur.tilt+tiltAdd,lean:Math.round(bob+cur.lean),ty:(Math.sin(t*1.6)>0.4?1:0),cw:200,ch:160,arms:{L:{S:SL,E:[a.ex,a.ey],H:[a.hx,a.hy]},R:{S:SR,E:[b.ex,b.ey],H:[b.hx,b.hy]}}});
  }else{
   armL.up.setAttribute('transform','rotate('+a.t1.toFixed(2)+' '+SL[0]+' 106)');armL.fo.setAttribute('transform','rotate('+a.t2.toFixed(2)+' '+SL[0]+' 132)');
   armR.up.setAttribute('transform','rotate('+b.t1.toFixed(2)+' '+SR[0]+' 106)');armR.fo.setAttribute('transform','rotate('+b.t2.toFixed(2)+' '+SR[0]+' 132)');
   F.head.setAttribute('transform','translate(0 '+(bob+cur.lean).toFixed(2)+') rotate('+(cur.tilt+tiltAdd).toFixed(2)+' '+CX+' 88)');
   F.torso.setAttribute('transform','translate(0 '+(Math.sin(t*1.6)*0.5).toFixed(2)+')');
   F.setBrow(cur.brow);F.setGaze(cur.gx,cur.gy);F.setLid(lidv);F.showMouth(p.mouth);
  }
  gPL.setAttribute('display',p.pl?'inline':'none');gPR.setAttribute('display',p.pr?'inline':'none');
  gPL.setAttribute('transform','translate('+a.hx.toFixed(2)+' '+a.hy.toFixed(2)+') rotate(-8)');gPR.setAttribute('transform','translate('+b.hx.toFixed(2)+' '+b.hy.toFixed(2)+') rotate(8)');
  gTool.setAttribute('display',p.tool?'inline':'none');gTool.setAttribute('transform','translate('+b.hx.toFixed(2)+' '+(b.hy+2).toFixed(2)+')');
  lens.setAttribute('display',p.tool==='lens'?'inline':'none');pen.setAttribute('display',p.tool==='pen'?'inline':'none');
  steam.forEach((e,i)=>{const f=((t*0.7+i*0.33)%1);e.setAttribute('y',-20-f*12);e.setAttribute('opacity',(0.7*(1-f)).toFixed(2))})}
 /* 행동 계획: 요청 종류(p1 소장 / p2 변명 / verdict 판결)에 따라 다른 흐름 */
 const PLAN={
  p1:[['read',5000],['flip',900],['read',4500],['magnify',4500],['ponder',4200],['yawn',2400],['read',4500],['flip',900],['compare',5200],['rub',2200]],
  p2:[['compare',5200],['ponder',4400],['read',4200],['flip',900],['write',4600],['yawn',2400],['magnify',4200],['rub',2200]],
  verdict:[['ponder',5200],['compare',4600],['write',4600],['rub',2200],['ponder',5400],['yawn',2400],['read',4200],['flip',900]]
 };
 const W=(D.cast.JUDGE.lines&&D.cast.JUDGE.lines.wait)||{};
 const kind=PLAN[D.phase]?D.phase:'p1',rnd=a=>a[Math.floor(Math.random()*a.length)];
 let idx=0,step=null,stepEnd=0,bubbleOff=0,prev=null;
 function say(s,ms){const b=g('w-bubble');if(!s){b.className='';return}b.textContent=s;b.className='on';spPlaceBubble(b);bubbleOff=t+(ms||2600)/1000}
 function nextStep(){if(prev==='flip')newPage();const e=PLAN[kind][idx%PLAN[kind].length];idx++;step=e[0];prev=e[0];tgt=P[e[0]];stepEnd=t+e[1]/1000;
  const lines=(e[0]==='ponder')?(W.ponder&&W.ponder[kind]):W[e[0]];if(lines&&lines.length&&Math.random()<0.8)say(rnd(lines),Math.min(e[1]-300,3200))}
 function tick(dtMs){const dt=Math.min(dtMs,64)/1000;t+=dt;if(!step||t>=stepEnd)nextStep();if(bubbleOff&&t>bubbleOff){say(null);bubbleOff=0}render(dt)}
 /* 크기 맞춤 + 먼지 입자 */
 function fit(){if(window.Stage)Stage.relayout()}
 window.addEventListener('resize',fit);fit();Stage.wait(kind,D.src);
 (function(){const d=g('w-dust');for(let i=0;i<18;i++){const e=document.createElement('div');e.className='dust';e.style.left=(Math.random()*96)+'%';e.style.top=(30+Math.random()*60)+'%';e.style.setProperty('--d',(9+Math.random()*8)+'s');e.style.setProperty('--l',(-Math.random()*12)+'s');d.appendChild(e)}})();
 window.__wait={tick:tick,pose:function(n){tgt=P[n];step=n;stepEnd=1e9;idx=0},poses:Object.keys(P),fig:F||hdF};
 let last=0;function loop(ts){if(last)tick(ts-last);last=ts;requestAnimationFrame(loop)}requestAnimationFrame(loop);
})();}
</script>
<script>
const $=id=>document.getElementById(id);
const scene=$('scene');
const NAMES={J:D.cast.JUDGE.display,P:D.cast.PROSECUTOR.display,L:D.cast.LAWYER.display};
const CAM={JUDGE:'J',PROSECUTOR:'P',LAWYER:'L'};
const TX={J:'-33.3334%',P:'0%',L:'-66.6667%'};
const BUST={};   // 인물 반신상 (HD 도트는 말하는 동안 입을 직접 여닫는다)
BUST.J=buildBust($('svgJ'),'JUDGE');
BUST.P=buildBust($('svgP'),'PROSECUTOR');
BUST.L=buildBust($('svgL'),'LAWYER');
const EXPR=D.expr||{};
const VCAM=(D.mode!=='wait')?Stage.make({view:$('scene'),pst:$('pst'),wrap:$('camwrap')}):null;   // 사진 법정 + 곡선 카메라 (stage.py)
if(VCAM)VCAM.set(D.opening?Stage.LOOK.JPUSH:Stage.LOOK.WIDE);   // 막 사이 연결 장면은 '판사 줌' 그대로 이어서 시작
/* 표정: 대사에 e 값이 있으면 그 표정, 없으면 외침(c)에 따라 — 검사 팩폭=비웃음 / 변호사 쉴드=억울함 / 판사 정숙=분노 */
function exprFor(st){if(st.e&&EXPR[st.e])return st.e;return {F:'smirk',S:'aggrieved',O:'angry'}[st.c]||'neutral'}
function applyExpr(c,st){for(const k in BUST){const F=BUST[k];if(F&&F.setExpr){F.setExpr(k===c?exprFor(st):'neutral');if(F.redraw)F.redraw()}}}

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
/* ---- ⚙️ 설정창: 열면 재판이 멈추고(대사 넘김 차단) 소리 설정 / 계속하기 / 재판 포기가 뜬다 ---- */
let paused=false;const sm=$('sm'),smq=$('sm_quit');
const smSnd=()=>{$('sm_snd').textContent=muted?'🔇 효과음 꺼짐':'🔊 효과음 켜짐'};
function smOpen(){paused=true;sm.classList.add('on');smq.classList.remove('sure');smq.textContent='🏳️ 재판 포기 (로비로)';smSnd();document.getElementById('scene').classList.add('paused')}
function smClose(){paused=false;sm.classList.remove('on');document.getElementById('scene').classList.remove('paused')}
$('mute').onclick=e=>{e.stopPropagation();smOpen()};
sm.addEventListener('click',e=>e.stopPropagation());
$('sm_go').onclick=e=>{e.stopPropagation();smClose()};
$('sm_snd').onclick=e=>{e.stopPropagation();muted=!muted;smSnd();if(!muted)beep(880,.1)};
if(D.mode!=='debate')smq.style.display='none';
smq.onclick=e=>{e.stopPropagation();if(!smq.classList.contains('sure')){smq.classList.add('sure');smq.textContent='⚠️ 정말 포기? 한 번 더 누르세요';return}
 try{const b=window.parent.document.querySelector('.st-key-giveup_hidden button');if(b){b.click();return}}catch(err){}
 smq.textContent='포기 버튼을 찾지 못했어요 — 새로고침 해주세요'};

/* ---- 진행 엔진 ---- */
let started=false,i=-1,typing=false,timer=null,full='',busy=false,curCam='J',ended=false;
const last=()=>D.steps.length-1;
function setTalk(c){document.querySelectorAll('.char').forEach(e=>e.classList.toggle('talk',e.dataset.c===c));for(const k in BUST)if(BUST[k]&&BUST[k].setTalking)BUST[k].setTalking(k===c)}
function stopType(){clearInterval(timer);typing=false;$('txt').textContent=full;$('arrow').style.visibility='visible';setTalk(null);
 if(i===last()&&!ended){if(D.mode==='verdict'){ended=true;setTimeout(gavel,900)}else{$('hint').textContent=D.hint||'';$('hint').style.display='block';exOpen();if(D.push){const ls=D.steps[last()];Stage.push(VCAM,(ls&&ls.cam)||CAM[ls&&ls.s]||'J')}}}}
function type(text){typing=true;full=text;let k=0;$('txt').textContent='';timer=setInterval(()=>{k++;$('txt').textContent=text.slice(0,k);$('boxin').scrollTop=$('boxin').scrollHeight;if(k%2===0)beep(480+Math.random()*140,.04);if(k>=text.length)stopType()},D.speed||32)}
const SHOUT={F:D.cast.PROSECUTOR.shout.text,S:D.cast.LAWYER.shout.text,O:D.cast.JUDGE.shout.text};
function shout(k,cb){const e=$('shout');e.textContent=SHOUT[k];e.className=k+' on';[520,780,1040].forEach((f,j)=>setTimeout(()=>beep(f,.16,.07),j*90));Stage.impact(k);setTimeout(()=>{e.className='';cb()},950)}
function show(n){const st=D.steps[n],c=CAM[st.s]||'J';busy=true;$('phase').textContent=(D.phase||'')+' · '+(n+1)+'/'+D.steps.length;const changed=c!==curCam;curCam=c;scene.dataset.cam=c;const lk=Stage.look(VCAM,st.cam||c);Stage.face(c);applyExpr(c,st);if(st.k==='act2'){hit();Stage.actTitle('제 2 막','변명 공방 & 최후 심문')}$('tagin').textContent=NAMES[c];$('txt').textContent='';$('arrow').style.visibility='hidden';
 const speak=()=>{busy=false;setTalk(c);Stage.emote(document.querySelector('#pst .char[data-c="'+c+'"]'),(EXPR[exprFor(st)]||{}).icon);type(st.t)};
 setTimeout(()=>{if(st.c&&SHOUT[st.c])shout(st.c,speak);else speak()},changed?Math.round(lk*1000)+140:150)}
function adv(){if(paused||!started||busy||ended)return;if(typing){stopType();return}if(i<last()){i++;show(i)}}
scene.addEventListener('click',adv);
document.addEventListener('keydown',e=>{if(e.code==='Space'||e.code==='Enter'){e.preventDefault();adv()}});
$('start').addEventListener('click',e=>{e.stopPropagation();ac();beep(880,.12);$('start').style.display='none';const go0=()=>{started=true;i=0;show(0)};if(D.intro&&D.mode==='debate')Stage.intro(VCAM,go0);else go0()});
if(D.opening){$('start').style.display='none';started=true;i=0;setTimeout(()=>show(0),450)}   /* 막 사이 연결: 시작 화면 없이 바로 이어짐 */

/* ---- 탕! 탕! 탕! → 판결문 ---- */
function hit(){thud();scene.classList.remove('shake');void scene.offsetWidth;scene.classList.add('shake');const f=$('flash');f.classList.remove('on');void f.offsetWidth;f.classList.add('on');
 const h=document.createElement('div');h.className='hit';h.textContent='탕!';h.style.left=(18+Math.random()*40)+'%';h.style.top=(12+Math.random()*30)+'%';scene.appendChild(h);setTimeout(()=>h.remove(),850)}
function gavel(){[0,750,1500].forEach(d=>setTimeout(hit,d));setTimeout(showCard,2900)}
function showCard(){$('hint').style.display='none';const w=$('cardwrap');w.style.display='flex';[660,880,1320].forEach((f,k)=>setTimeout(()=>beep(f,.25,.06),k*140));
 for(let k=0;k<18;k++){const s=document.createElement('span');s.className='spark';s.textContent='✦';s.style.left=(Math.random()*92)+'%';s.style.top=(Math.random()*92)+'%';s.style.fontSize=(10+Math.random()*18)+'px';s.style.animationDelay=(Math.random()*1.2)+'s';w.appendChild(s)}}
</script></body></html>"""

def render_vn(mode, steps, card=None, height=580, title="", phase="", hint="", mute=False, speed=30, intro=False, opening=None, push=False, src=""):
    payload = json.dumps({"mode": mode, "steps": steps, "card": card or {}, "title": title, "phase": phase, "hint": hint, "mute": mute, "speed": speed, "intro": bool(intro), "opening": opening, "push": bool(push), "src": {"PROSECUTOR": "P", "LAWYER": "L"}.get(src, src if src in ("P", "L", "J") else ""), "cast": sprite_payload(), "expr": expressions_payload()}, ensure_ascii=False)
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
.ch svg,.ch canvas{display:block;width:100%;height:auto}.hdc{image-rendering:pixelated}
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
  <div class="front"><div class="bc-logo">⚖️</div><div class="bc-t">이불킥 법정</div><div class="bc-s">당신의 흑역사,<br>무죄로 만들어 드립니다</div><div class="bc-n" id="bc_n"></div></div>
  <div class="back"><div class="bc-hand">“오늘 새벽,<br>법원 정문 계단 위에서<br>기다리겠습니다.”</div></div></div></div>
 <div id="door"><div class="hallfloor"></div>
  <div class="ch" id="c_pros" style="left:2%"><div class="nm" id="nm_pros"></div></div>
  <div class="ch" id="c_judge" style="left:34.5%"><div class="nm" id="nm_judge"></div></div>
  <div class="ch" id="c_law" style="right:2%"><div class="nm" id="nm_law"></div></div>
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
/*__SPRITES__*/
const $=id=>document.getElementById(id);
const scene=$('scene');
const NJ=D.cast.JUDGE.name,NP=D.cast.PROSECUTOR.name,NL=D.cast.LAWYER.name,DL=D.cast.LAWYER.display;
$('nm_pros').textContent=D.cast.PROSECUTOR.display;$('nm_judge').textContent=D.cast.JUDGE.display;$('nm_law').textContent=DL;$('bc_n').textContent='평판 방어 전문 · 변호사 '+NL;
const S=[
 {v:'bed',k:'t',x:'새벽 3시 7분. 나는 이불 속에서 도무지 잠들지 못하고 있었다.'},
 {v:'bed',k:'t',fx:'think',x:'눈을 감으면 자꾸 그날의 일이 떠오른다. 그 글, 그 사진, 그 한마디…'},
 {v:'bed',k:'t',fx:'kick',x:'“으아아악!” 나는 이불을 발로 뻥뻥 걷어찼다. 아무리 차도 흑역사는 사라지지 않았다.'},
 {v:'bed',k:'t',fx:'drop',x:'그때, 발끝에 딱딱한 무언가가 걸렸다. 이불 틈에서 종이 한 장이 툭 떨어졌다.'},
 {v:'card',k:'t',fx:'paper',x:'…명함이었다. 내 것이 아니다. 누가, 언제, 이걸 내 이불 속에…?'},
 {v:'card',k:'t',x:'〈이불킥 법정 — 당신의 흑역사, 무죄로 만들어 드립니다. 평판 방어 전문 · 변호사 '+NL+'〉'},
 {v:'card',k:'t',fx:'flip',x:'뒷면에는 손글씨가 적혀 있었다. “오늘 새벽, 법원 정문 계단 위에서 기다리겠습니다.”'},
 {v:'card',k:'t',x:'수상하다. 하지만 이대로 평생 이불만 걷어차며 살 수는 없다. 나는 외투를 걸치고 집을 나섰다.'},
 {v:'court',k:'t',x:'…와.'},
 {v:'court',k:'t',x:'눈앞에 거대한 법원이 우뚝 서 있다. 고개를 한참 젖혀야 꼭대기가 보인다.'},
 {v:'court',k:'t',x:'명함에 적힌 곳이 틀림없다. 저 둥근 문양 아래에서, 누군가 나를 기다리고 있다.'},
 {v:'court',k:'s',x:'계단이 생각보다 높다.'},
 {v:'court',k:'s',x:'이 명함, 장난이 아니길 바랄 뿐이다.'},
 {v:'court',k:'s',x:'그날 올린 그 글, 그 한마디가 자꾸 떠오른다.'},
 {v:'court',k:'s',x:'지금도 생각하면 발가락이 오그라든다.'},
 {v:'court',k:'s',x:'다들 이미 잊었길 바랐는데.'},
 {v:'court',k:'s',x:'누군가는 분명 캡처해 뒀겠지.'},
 {v:'court',k:'s',x:'내 평판은 그날 이후로 바닥을 기고 있다.'},
 {v:'court',k:'s',x:'이제 도망칠 곳도 없다. 한 계단만 더.'},
 {v:'court',k:'s',x:'드디어, 문 앞이다.'},
 {v:'hall',k:'d',x:'끼이이익—! 무겁고 커다란 문이 천천히 열렸다.'},
 {v:'hall',k:'t',x:'환하게 쏟아지는 빛 속에서, 세 사람의 그림자가 나를 바라보고 있었다.'},
 {v:'judge',k:'t',x:'가운데에는 '+NJ+' 판사. 졸린 눈으로 나를 보는데, 벌써 퇴근 시간을 세고 있는 눈치다.'},
 {v:'pros',k:'t',x:'왼쪽에는 '+NP+' 검사. 서류를 반듯하게 쥔 채, 얼음 같은 눈으로 나를 훑어본다.'},
 {v:'law',k:'t',x:'오른쪽에는 '+NL+' 변호사. 나를 보더니 느긋하게 웃으며 한쪽 눈을 찡긋한다. …뭐지?'},
 {v:'law',k:'t',x:'맞다. 그 명함의 주인이 바로 이 사람이었다.'},
 {v:'law',k:'t',w:DL,x:'“기다리고 있었어요~ 당신의 흑역사, 제가 그럴듯하게 포장해서 무죄로 만들어 드릴게요.”'},
 {v:'gauge',k:'t',x:'나는 안다. 그날의 흑역사 때문에 내 평판과 이불킥 랭크는 이미 바닥을 기고 있다는 것을.'},
 {v:'goal',k:'g',x:'그래서 오늘의 목표는 단 하나! 어떻게든 무죄를 받아내서, 평판과 이불킥 랭크를 지켜내는 것이다!'},
 {v:'crown',k:'g',x:'무죄를 연달아 받아내면… 최고 랭크 👑 [이불킥 청정수]가 될 수도 있다고 한다.'},
 {v:'enter',k:'t',x:'…좋아. 심호흡을 하고 한 발 내디뎠다. 이제, 법정 안으로 들어가 보자.'}
];
const STEPS=S.filter(e=>e.k==='s').length;
buildBust($('c_judge'),'JUDGE');
buildBust($('c_pros'),'PROSECUTOR');
buildBust($('c_law'),'LAWYER');
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
 setTimeout(()=>{busy=false;type(String(e.x).replace(/^(뚜벅|저벅)[…\.!]*\s*/,''))},wait)}   /* 효과음 글자는 대사에 넣지 않고, 위의 popText 자막으로만 보여 준다 */
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
    payload = json.dumps({"mute": mute, "speed": speed, "cast": sprite_payload()}, ensure_ascii=False).replace("</", "<\\/")
    components.html(STORY_TEMPLATE.replace("__DATA__", payload), height=height, scrolling=False)


# =================================================================
# 서브컬처풍 가로 로비 (iframe: 한유리 변호사가 일하고, 커피 마시고, 기지개 켜는 중앙 연출)
#   * 캐릭터·배경은 모두 이 게임을 위해 직접 그린 오리지널 도트 그래픽입니다.
# =================================================================
LOBBY_TEMPLATE = r"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
@import url('https://cdn.jsdelivr.net/npm/galmuri@latest/dist/galmuri.css');
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:#000;overflow:hidden;font-family:'Galmuri11','Jua','Apple SD Gothic Neo','Malgun Gothic',sans-serif;user-select:none;-webkit-tap-highlight-color:transparent}
:root{--ink:#0d0f26}
#scene{position:relative;width:100%;height:100%;overflow:hidden;background:var(--sky1)}
#scene.day{--sky1:#6ec6ff;--sky2:#d9f1ff;--bld:#8fa7d6;--bld2:#6f88c0;--win:#cfe6ff;--t1:#d9cdb0;--t2:#c4b693;--cl:#ffffffd0;--haze:#ffffff40;--sun:#ffe066}
#scene.dusk{--sky1:#4a3a8c;--sky2:#ffb27a;--bld:#5a4a86;--bld2:#43376d;--win:#ffd98a;--t1:#a99486;--t2:#8f7c71;--cl:#ffd0b0d0;--haze:#ff9a6a30;--sun:#ff9a5a}
#scene.night{--sky1:#0a0e2e;--sky2:#26306f;--bld:#222a5c;--bld2:#181e47;--win:#ffe28a;--t1:#454a6e;--t2:#383d5c;--cl:#5a6aa8a0;--haze:#4a5ad020;--sun:#fff3b0}
#sky{position:absolute;inset:0;background:linear-gradient(var(--sky1),var(--sky2) 68%)}
#stars{position:absolute;inset:0;opacity:0;background-image:radial-gradient(#fff 1px,transparent 1.6px);background-size:46px 38px;transition:opacity 1s}
#scene.night #stars{opacity:.8}
#sun{position:absolute;right:30%;top:9%;width:54px;height:54px;border-radius:50%;background:var(--sun);box-shadow:0 0 40px var(--sun)}
.cloud{position:absolute;height:14px;width:60px;background:var(--cl);box-shadow:20px -10px 0 var(--cl),40px 0 0 var(--cl);animation:drift var(--d,80s) linear infinite}
@keyframes drift{from{transform:translateX(-140px)}to{transform:translateX(1300px)}}
#city{position:absolute;left:0;right:0;bottom:26%;width:100%;height:46%}
#city .b1{fill:var(--bld)}#city .b2{fill:var(--bld2)}#city .w{fill:var(--win)}#city .ink{fill:var(--ink)}
#plaza{position:absolute;left:0;right:0;bottom:0;height:30%;border-top:5px solid var(--ink);background:repeating-conic-gradient(var(--t1) 0 25%,var(--t2) 0 50%) 0 0/60px 60px}
#plaza:after{content:"";position:absolute;inset:0;background:linear-gradient(var(--haze),#0003)}
#papers{position:absolute;inset:0;pointer-events:none;overflow:hidden}
.paper{position:absolute;top:-14px;width:9px;height:12px;background:#fff;border:2px solid var(--ink);opacity:.9;animation:fall var(--fd,14s) linear infinite;animation-delay:var(--fl,0s)}
@keyframes fall{0%{transform:translate(0,0) rotate(0)}50%{transform:translate(40px,300px) rotate(180deg)}100%{transform:translate(-20px,640px) rotate(380deg)}}
#sign{position:absolute;left:50%;top:12px;transform:translateX(-50%);background:var(--ink);color:#ffd23f;font-size:13px;font-weight:700;padding:6px 14px;letter-spacing:1px;box-shadow:0 0 0 3px #ffd23f,0 6px 0 3px #0008;white-space:nowrap}
#sign b{color:#59f08a;animation:blink 1.4s steps(2) infinite}
@keyframes blink{50%{opacity:.35}}
#cw{position:absolute;left:50%;bottom:124px;transform:translateX(-50%);cursor:pointer}
#cfig{position:absolute;left:0;top:0;width:100%;height:100%;image-rendering:pixelated}
#chara{position:relative}
#chara{display:block}
#bubble{position:absolute;left:56%;bottom:100%;margin-bottom:12px;width:max-content;max-width:min(260px,58vw);background:#fff;color:var(--ink);font-size:14px;font-weight:700;padding:9px 14px 10px;opacity:0;transition:opacity .3s,transform .3s;transform:translateY(6px);box-shadow:0 -3px 0 var(--ink),0 3px 0 var(--ink),-3px 0 0 var(--ink),3px 0 0 var(--ink),4px 8px 0 0 #0006;white-space:normal;word-break:keep-all;overflow-wrap:break-word;line-height:1.45;text-align:left}
#bubble.on{opacity:1;transform:none}
#bubble:after{content:"";position:absolute;left:14px;bottom:-12px;border:6px solid transparent;border-top:8px solid var(--ink)}
#bar{position:absolute;left:0;right:0;bottom:0;height:112px;background:linear-gradient(#0d0f2600,#0d0f26d8 26%,#0d0f26f6);border-top:4px solid #ffd23f}
#bar:before{content:"";position:absolute;left:0;right:0;top:-4px;height:4px;background:repeating-linear-gradient(90deg,#ffd23f 0 14px,#0d0f26 14px 20px)}
#vig{position:absolute;inset:0;pointer-events:none;background:repeating-linear-gradient(#0000 0 2px,#0001 2px 3px);box-shadow:inset 0 0 90px #0008}
@media (max-aspect-ratio:5/4){#sign{font-size:11px;padding:5px 10px}#bubble{left:50%;font-size:12px}}
</style></head><body>
<div id="scene" class="day">
 <div id="sky"></div><div id="stars"></div><div id="sun"></div>
 <div class="cloud" style="top:14%;--d:90s;animation-delay:-20s"></div><div class="cloud" style="top:26%;--d:120s;animation-delay:-70s"></div><div class="cloud" style="top:8%;--d:105s;animation-delay:-45s"></div>
 <svg id="city" viewBox="0 0 400 100" preserveAspectRatio="xMidYMax slice" shape-rendering="crispEdges"></svg>
 <div id="plaza"></div><div id="papers"></div>
 <div id="sign"></div>
 <div id="cw"><canvas id="cfig"></canvas><svg id="chara" viewBox="0 0 200 160" shape-rendering="crispEdges"></svg><div id="bubble"></div></div>
  <div id="bar"></div><div id="vig"></div>
</div>
<script>
const D=__DATA__;
/*__SPRITES__*/
const $=id=>document.getElementById(id);
const NS='http://www.w3.org/2000/svg';
const CX=100, INK='#0d0f26';
$('sign').innerHTML='🏛️ '+D.cast.LAWYER.name+' 법률사무소 · <b>영업 중</b>';
const SL=[CX-33,102], SR=[CX+33,102], L1=24, L2=24.5;
function E(tag,attrs,parent){const e=document.createElementNS(NS,tag);for(const k in attrs)e.setAttribute(k,attrs[k]);(parent||$('chara')).appendChild(e);return e}
function A(p,x,y,w,h,f,o){return E('rect',Object.assign({x:x,y:y,width:w,height:h,fill:f},o||{}),p)}
function R(p,dx,y,w,h,f,o){return A(p,CX+dx,y,w,h,f,o)}
const OUT={stroke:INK,'stroke-width':2};

/* ------------------ 도시 배경 (직접 그린 오리지널 도트 스카이라인) ------------------ */
(function(){const c=$('city');
 const blds=[[0,40,34,60],[30,52,26,48],[52,34,30,66],[78,46,28,54],[300,44,30,56],[326,30,28,70],[350,50,26,50],[372,38,28,62]];
 blds.forEach((b,i)=>{E('rect',{class:i%2?'b2':'b1',x:b[0],y:b[1],width:b[2],height:b[3]},c);
  for(let wy=b[1]+6;wy<b[1]+b[3]-6;wy+=10)for(let wx=b[0]+4;wx<b[0]+b[2]-4;wx+=8)if(((wx*7+wy*3+i)%5)!==0)E('rect',{class:'w',x:wx,y:wy,width:4,height:5},c)});
 // 법원 건물(가운데 뒤): 원형 문양 + 기둥 + 돔
 E('rect',{class:'b2',x:140,y:36,width:120,height:64},c);E('rect',{class:'b1',x:150,y:30,width:100,height:70},c);
 E('rect',{class:'b2',x:176,y:14,width:48,height:16},c);E('rect',{class:'b1',x:184,y:6,width:32,height:10},c);E('rect',{class:'ink',x:198,y:0,width:4,height:8},c);
 E('circle',{cx:200,cy:52,r:11,fill:'#1f5ea8',stroke:'#e8b84a','stroke-width':2},c);
 for(let i=0;i<6;i++)E('rect',{class:'b2',x:152+i*18,y:68,width:5,height:32},c);
 E('rect',{class:'ink',x:188,y:78,width:24,height:22},c);
 E('rect',{class:'b2',x:146,y:64,width:108,height:4},c)})();
/* ------------------ 낙하하는 종이 ------------------ */
(function(){const p=$('papers');for(let i=0;i<12;i++){const e=document.createElement('div');e.className='paper';e.style.left=(Math.random()*96)+'%';e.style.setProperty('--fd',(11+Math.random()*9)+'s');e.style.setProperty('--fl',(-Math.random()*16)+'s');p.appendChild(e)}})();

/* ------------------ 캐릭터: 한유리 변호사 — 머리·표정·의상은 characters.py 데이터대로 그린다 ------------------ */
const HDM=(D.cast.LAWYER.render||{}).mode==='pixel_hd';     // pixel_hd: 픽셀 단위 고해상도 도트(캔버스) / svg: 도형 도트
let F=null,gHead=null,gTorso=null,hdF=null,hdCtx=null;
if(HDM){hdF=hdBuildFigure('LAWYER');const cv=$('cfig');cv.width=200;cv.height=160;hdCtx=cv.getContext('2d');hdCtx.imageSmoothingEnabled=false}
else{F=buildFigure($('chara'),'LAWYER');gHead=F.head;gTorso=F.torso;$('chara').setAttribute('shape-rendering',F.render.shape_rendering||'crispEdges')}
const gArmL=E('g'),gArmR=E('g'),gDesk=E('g'),gMugDesk=E('g'),gMugHand=E('g');
// (svg 모드 전용) 팔: 어깨→팔꿈치→손. 소매 색·폭은 의상 데이터(F.sleeve)를 따른다
function arm(g,S){const w=F.sleeve.w-1,w2=w-1;const up=E('g',{},g);A(up,S[0]-w/2,100,w,24,F.sleeve.color,OUT);A(up,S[0]-w/2,100,w,5,F.pal.suit_light||F.sleeve.color);
 const fo=E('g',{},up);A(fo,S[0]-w2/2,122,w2,24,F.sleeve.color,OUT);A(fo,S[0]-w2/2,138,w2,3,F.sleeve.cuff);A(fo,S[0]-5,143,10,9,F.pal.skin,OUT);return {up:up,fo:fo}}
const armL=HDM?null:arm(gArmL,SL),armR=HDM?null:arm(gArmR,SR);
// 책상 + 노트북 + 소품
A(gDesk,0,138,200,22,'#8a5a34');A(gDesk,0,138,200,4,'#b88555');A(gDesk,0,154,200,6,'#6e4526');
R(gDesk,-26,146,52,9,'#ffd23f',OUT);E('text',{x:CX,y:153,'font-size':6,'text-anchor':'middle',fill:INK,'font-weight':'bold'},gDesk).textContent=D.cast.LAWYER.name+' 법률사무소';
R(gDesk,-30,112,60,28,'#cfd3e6',OUT);R(gDesk,-27,115,54,22,'#e6e9f5');R(gDesk,-34,139,68,3,'#9aa0bb');
E('text',{x:CX,y:132,'font-size':15,'text-anchor':'middle'},gDesk).textContent='⚖';
const led=R(gDesk,24,117,3,3,'#59f08a');
R(gDesk,-92,132,28,6,'#fff',OUT);R(gDesk,-90,127,26,6,'#f3f3ff',OUT);R(gDesk,-58,124,9,14,'#4aa8ff',OUT);R(gDesk,-56,118,2,8,'#d2336b');R(gDesk,-53,119,2,7,'#222');
// 머그잔 (책상 위 / 손에 든 것) + 김
function mug(g){A(g,-7,-14,14,14,'#fff',OUT);A(g,7,-11,4,8,'#fff',OUT);A(g,-5,-12,10,3,'#5a2d0c');
 const st=[];for(let i=0;i<3;i++)st.push(A(g,-4+i*4,-20,2,4,'#fff',{opacity:.7}));return st}
gMugDesk.setAttribute('transform','translate('+(CX+62)+' 138)');const steamD=mug(gMugDesk);
const steamH=mug(gMugHand);

/* ------------------ 역기구학(IK): 손 위치 → 어깨·팔꿈치 각도 ------------------ */
function rotOf(a){return Math.atan2(-Math.cos(a),Math.sin(a))*180/Math.PI}
function ik(S,T){let dx=T[0]-S[0],dy=T[1]-S[1],d=Math.hypot(dx,dy);const maxd=L1+L2-0.6,mind=Math.abs(L1-L2)+2;const reach=Math.max(mind,Math.min(maxd,d));
 const base=Math.atan2(dy,dx),cb=(L1*L1+reach*reach-L2*L2)/(2*L1*reach),b=Math.acos(Math.max(-1,Math.min(1,cb)));
 const c=[base+b,base-b].map(a=>({a:a,ey:S[1]+L1*Math.sin(a),ex:S[0]+L1*Math.cos(a)})).sort((p,q)=>q.ey-p.ey)[0];
 const hx=S[0]+reach*Math.cos(base),hy=S[1]+reach*Math.sin(base),fa=Math.atan2(hy-c.ey,hx-c.ex);
 let t1=rotOf(c.a),t2=rotOf(fa)-t1;while(t2>180)t2-=360;while(t2<-180)t2+=360;return {t1:t1,t2:t2,hx:hx,hy:hy,ex:c.ex,ey:c.ey}}

/* ------------------ 자세 정의 ------------------ */
const P={
 work:{R:[CX+12,134],L:[CX-12,134],tilt:3,gx:0,gy:3,lid:.3,mouth:'smile'},
 idle:{R:[CX+42,133],L:[CX-42,133],tilt:0,gx:0,gy:0,lid:0,mouth:'grin'},
 wave:{R:[CX+54,62],L:[CX-42,133],tilt:-4,gx:0,gy:0,lid:0,mouth:'grin',wave:1},
 stretch:{R:[CX+62,36],L:[CX-62,36],tilt:-7,gx:0,gy:-1,lid:1,mouth:'open'},
 think:{R:[CX+9,87],L:[CX-42,133],tilt:5,gx:-3,gy:-2,lid:.15,mouth:'flat'},
 reach:{R:[CX+62,131],L:[CX-42,133],tilt:0,gx:3,gy:2,lid:0,mouth:'grin'},
 lift:{R:[CX+17,88],L:[CX-42,133],tilt:-2,gx:0,gy:0,lid:.4,mouth:'grin',hold:1},
 sip:{R:[CX+12,84],L:[CX-42,133],tilt:-6,gx:0,gy:0,lid:1,mouth:'hidden',hold:1,mugTilt:-24}
};
const cur={R:[CX+42,133],L:[CX-42,133],tilt:0,gx:0,gy:0,lid:0,mugTilt:0,torsoY:0};
let tgt=P.idle,holding=false,t=0;
const ap=(c,g,k,dt)=>c+(g-c)*(1-Math.exp(-k*dt));
function render(dt){
 const p=tgt,k=7;cur.R[0]=ap(cur.R[0],p.R[0],k,dt);cur.R[1]=ap(cur.R[1],p.R[1],k,dt);cur.L[0]=ap(cur.L[0],p.L[0],k,dt);cur.L[1]=ap(cur.L[1],p.L[1],k,dt);
 cur.tilt=ap(cur.tilt,p.tilt||0,6,dt);cur.gx=ap(cur.gx,p.gx||0,8,dt);cur.gy=ap(cur.gy,p.gy||0,8,dt);cur.lid=ap(cur.lid,p.lid||0,10,dt);cur.mugTilt=ap(cur.mugTilt,p.mugTilt||0,7,dt);
 let rx=cur.R[0],ry=cur.R[1],lx=cur.L[0],ly=cur.L[1];
 if(tgt===P.work){const w=t*13;lx+=Math.sin(w)*3;ly+=(Math.sin(w*1.7)>0?1.5:0);rx+=Math.sin(w+1.8)*3;ry+=(Math.sin(w*1.3+1)>0?1.5:0)}
 if(p.wave)rx+=Math.sin(t*9)*7;
 const a=ik(SL,[lx,ly]),b=ik(SR,[rx,ry]);
 const bob=Math.sin(t*2)*0.6+(tgt===P.work?Math.sin(t*9)*0.5:0),blink=((t%4.2)<0.13)?1:0,lid=Math.max(cur.lid,blink);
 if(HDM){   // 픽셀 도화지에 인물(머리·몸·팔)을 다시 칠한다. 움직임은 한 칸(1픽셀) 단위로 끊어서 도트다운 느낌을 낸다
  hdF.setGaze(cur.gx,cur.gy);hdF.setLid(lid);hdF.showMouth(p.mouth);hdCtx.clearRect(0,0,200,160);
  hdF.render(hdCtx,{tilt:cur.tilt,lean:Math.round(bob),ty:(Math.sin(t*1.6)>0.4?1:0),cw:200,ch:160,arms:{L:{S:SL,E:[a.ex,a.ey],H:[a.hx,a.hy]},R:{S:SR,E:[b.ex,b.ey],H:[b.hx,b.hy]}}});
 }else{
  armL.up.setAttribute('transform','rotate('+a.t1.toFixed(2)+' '+SL[0]+' 100)');armL.fo.setAttribute('transform','rotate('+a.t2.toFixed(2)+' '+SL[0]+' 124)');
  armR.up.setAttribute('transform','rotate('+b.t1.toFixed(2)+' '+SR[0]+' 100)');armR.fo.setAttribute('transform','rotate('+b.t2.toFixed(2)+' '+SR[0]+' 124)');
  gHead.setAttribute('transform','translate(0 '+bob.toFixed(2)+') rotate('+cur.tilt.toFixed(2)+' '+CX+' 84)');
  gTorso.setAttribute('transform','translate(0 '+(Math.sin(t*2)*0.5).toFixed(2)+')');
  F.setGaze(cur.gx,cur.gy);F.setLid(lid);F.showMouth(p.mouth);
 }
 // 머그잔: 책상 위 ↔ 손에 쥠
 holding=!!(p.hold||(step&&step.hold));
 gMugDesk.setAttribute('display',holding?'none':'inline');
 gMugHand.setAttribute('display',holding?'inline':'none');
 gMugHand.setAttribute('transform','translate('+b.hx.toFixed(2)+' '+(b.hy+3).toFixed(2)+') rotate('+cur.mugTilt.toFixed(2)+')');
 // 김
 [steamD,steamH].forEach(s=>s.forEach((e,i)=>{const f=((t*0.8+i*0.33)%1);e.setAttribute('y',-20-f*12);e.setAttribute('opacity',(0.75*(1-f)).toFixed(2))}));
 led.setAttribute('fill',(Math.sin(t*5)>0)?'#59f08a':'#2fbf63');
}

/* ------------------ 행동 계획: 일하기 → 커피 → 기지개 → 생각 → 손 흔들기 ... ------------------ */
const LL=(D.cast.LAWYER.lines&&D.cast.LAWYER.lines.lobby)||{};
const SAY={work:LL.work||['…'],think:LL.think||['…'],stretch:LL.stretch||['…'],idle:LL.idle||['…'],wave:LL.wave||['…']};
const rnd=a=>a[Math.floor(Math.random()*a.length)];
function coffee(){return [{p:'reach',d:1000,s:(LL.coffee||['☕ 커피 타임~'])[0]},{p:'lift',d:1000},{p:'sip',d:1900,s:(LL.coffee||['','후루룩… 크으~'])[1]},{p:'lift',d:800},{p:'reach',d:1000,hold:1},{p:'work',d:300}]}
function plan(){return [{p:'work',d:6500,s:rnd(SAY.work)}].concat(coffee(),[{p:'work',d:5500,s:rnd(SAY.work)},{p:'think',d:3200,s:rnd(SAY.think)},{p:'work',d:5000},{p:'stretch',d:3400,s:rnd(SAY.stretch)},{p:'idle',d:3200,s:rnd(SAY.idle)}])}
let queue=[{p:'wave',d:2600,s:rnd(SAY.wave)}].concat(plan()),step=null,stepEnd=0,bubbleOff=0;
function say(s,ms){const b=$('bubble');if(!s){b.classList.remove('on');return}b.textContent=s;b.classList.add('on');spPlaceBubble(b);bubbleOff=t+(ms||2600)/1000}
function nextStep(){if(!queue.length)queue=plan();step=queue.shift();tgt=P[step.p];stepEnd=t+step.d/1000;if(step.s)say(step.s,Math.min(step.d,3400))}
function tick(dtMs){const dt=Math.min(dtMs,64)/1000;t+=dt;if(!step||t>=stepEnd)nextStep();if(bubbleOff&&t>bubbleOff){say(null);bubbleOff=0}render(dt)}
let last=0;function loop(ts){if(last)tick(ts-last);last=ts;requestAnimationFrame(loop)}
$('cw').addEventListener('click',()=>{const lines=LL.poke||['앗!'];queue.unshift({p:'wave',d:1800,s:rnd(lines)});stepEnd=0});
/* ------------------ 화면 구성: 시간대 / 크기 ------------------ */
(function(){const h=new Date().getHours(),s=$('scene');s.className=(h>=6&&h<17)?'day':(h>=17&&h<20)?'dusk':'night';
 if(s.className==='night'){const sun=$('sun');sun.style.boxShadow='inset -14px -4px 0 #26306f,0 0 30px #fff3b0'}})();
const SCALE=0.72; /* 캐릭터·책상·노트북 세트의 크기 비율 (0.70~0.75 권장) */
function fit(){const s=$('scene'),H=s.clientHeight-128,W=s.clientWidth;let w=H*1.25;if(w>W*1.1)w=W*1.1;w*=SCALE;const h=w/1.25;$('chara').style.width=w+'px';$('chara').style.height=h+'px'}
window.addEventListener('resize',fit);fit();
window.__lobby={tick:tick,pose:function(name,dur){tgt=P[name];step={p:name};stepEnd=1e9;queue=[]},state:function(){return {cur:cur,holding:holding}}};
requestAnimationFrame(loop);
</script></body></html>"""


def render_lobby(data, height=540):
    payload = json.dumps(dict(data, cast=sprite_payload()), ensure_ascii=False).replace("</", "<\\/")
    components.html(LOBBY_TEMPLATE.replace("__DATA__", payload), height=height, scrolling=False)


def court_panel_html(rep, icon, rank, pct, next_name, need, streak, wins, trials, fee, fee_max, badges):
    """'오늘의 법정' 상태 패널 (로비에서는 숨겨 두고, 프로필 모달을 열었을 때만 보여준다)"""
    pips = "".join(f'<i class="pip{" on" if k < fee else ""}"></i>' for k in range(fee_max))
    nxt = f"다음 랭크 {html.escape(str(next_name))}까지 {need}점" if next_name else "최고 랭크! 평판을 지켜내세요"
    return (
        '<div class="court-panel"><div class="cp-t">⚖️ 오늘의 법정</div>'
        f'<div class="cp-r">{icon} {html.escape(str(rank))}</div>'
        f'<div class="cp-row"><span>🏆 평판</span><b>{rep}점</b></div>'
        f'<div class="cp-gauge"><i style="width:{pct}%"></i></div><div class="cp-sub">{nxt}</div>'
        f'<div class="cp-row"><span>🔥 연속 무죄</span><b>{streak}연승</b></div>'
        f'<div class="cp-row"><span>✅ 무죄 / 재판</span><b>{wins} / {trials}</b></div>'
        f'<div class="cp-row"><span>🎖️ 칭호</span><b>{badges}개</b></div>'
        f'<div class="cp-row"><span>⚖️ 선임비</span><span class="cp-pips">{pips} {fee}/{fee_max}</span></div></div>'
    )


# =================================================================
# 공용 캐릭터 스프라이트 그리기 코드 (characters.py 의 palette/style 을 읽어서 그린다)
# =================================================================
SPRITES_JS = r"""/* ============ 캐릭터 스프라이트 라이브러리 (도트/픽셀 스타일) ============
   characters.py 의 palette(색)와 style(머리·눈·눈썹·입·의상 이름)을 읽어서 도트 캐릭터를 그린다.
   D.cast[키] = {name, display, palette, style, shout, lines}  ← Python(sprite_payload)에서 넘어온 데이터
   buildFigure(부모, 키) → 머리/몸/표정 조작 함수가 달린 캐릭터 / buildBust(요소, 키) → 재판 화면용 반신상 */
const SPX=100;let SPUID=0;
function spEl(tag,at,p){const e=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const k in at)e.setAttribute(k,at[k]);if(p)p.appendChild(e);return e}
function spR(p,dx,y,w,h,f,o){return spEl('rect',Object.assign({x:SPX+dx,y:y,width:w,height:h,fill:f},o||{}),p)}
function spP(p,pts,f,o){return spEl('polygon',Object.assign({points:pts.map(q=>(SPX+q[0])+','+q[1]).join(' '),fill:f},o||{}),p)}
function spMir(pts){return pts.map(q=>[-q[0],q[1]])}
function spBoth(p,pts,f,o){spP(p,pts,f,o);spP(p,spMir(pts),f,o)}

/* ---------------- 머리카락 ---------------- */
const SP_HAIR={
 long_wavy:{
  back(F,pal){const g=F.back,H=pal.hair,S=pal.hair_shadow,L=pal.hair_light,ST={stroke:S,'stroke-width':1.2};
   spP(g,[[-36,34],[-31,18],[-18,9],[0,7],[18,9],[31,18],[36,34],[38,66],[-38,66]],H,ST);
   spBoth(g,[[-38,50],[-46,84],[-52,124],[-55,162],[-48,174],[-43,162],[-38,174],[-32,160],[-30,120],[-33,84]],H,ST);
   spP(g,[[-38,60],[38,60],[41,112],[38,152],[-38,152],[-41,112]],H,ST);
   spBoth(g,[[-33,84],[-30,120],[-32,160],[-35,152],[-36,110]],S,{opacity:.55});
   spBoth(g,[[-47,76],[-49,110],[-50,142],[-47,112]],L,{opacity:.85})},
  locks(F,pal){const g=F.torso,H=pal.hair,S=pal.hair_shadow,L=pal.hair_light,ST={stroke:S,'stroke-width':1.2};
   spBoth(g,[[-31,58],[-37,86],[-41,120],[-43,152],[-38,160],[-35,142],[-32,114],[-30,84]],H,ST);
   spBoth(g,[[-36,92],[-39,120],[-40,148],[-38,124]],L,{opacity:.8})},
  front(F,pal){const g=F.head,H=pal.hair,S=pal.hair_shadow,L=pal.hair_light,ST={stroke:S,'stroke-width':1.2};
   spP(g,[[-26,32],[26,32],[22,39],[-22,39]],pal.skin_shadow,{opacity:.5});
   spP(g,[[-7,22],[18,21],[30,31],[34,48],[33,66],[29,52],[24,43],[16,37],[6,33],[-7,31]],H,ST);
   spP(g,[[-7,22],[-12,21],[-28,28],[-34,44],[-34,64],[-30,50],[-26,41],[-18,35],[-7,31]],H,ST);
   spP(g,[[-30,27],[-24,13],[0,9],[24,13],[30,27],[0,21]],H,ST);
   spR(g,-13,12,22,3,L,{opacity:.9});spR(g,2,25,16,2,L,{opacity:.8});spR(g,-24,30,10,2,L,{opacity:.8});
   spR(g,10,33,2,10,S,{opacity:.6});spR(g,-18,36,2,9,S,{opacity:.6})}
 },
 layered_medium:{
  back(F,pal){const g=F.back,H=pal.hair,S=pal.hair_shadow,L=pal.hair_light,ST={stroke:S,'stroke-width':1.2};
   spP(g,[[-36,34],[-31,16],[-16,8],[0,6],[16,8],[31,16],[36,34],[40,70],[44,96],[52,108],[42,108],[35,118],[29,104],[22,114],[14,100],[-14,100],[-22,114],[-29,104],[-35,118],[-42,108],[-52,108],[-44,96],[-40,70]],H,ST);
   spP(g,[[-20,70],[20,70],[16,100],[-16,100]],S,{opacity:.7});
   spBoth(g,[[-42,84],[-46,102],[-49,106],[-44,92]],L,{opacity:.7})},
  locks(F,pal){},
  front(F,pal){const g=F.head,H=pal.hair,S=pal.hair_shadow,L=pal.hair_light,ST={stroke:S,'stroke-width':1.2};
   spP(g,[[-26,32],[26,32],[22,39],[-22,39]],pal.skin_shadow,{opacity:.45});
   spBoth(g,[[0,14],[-14,14],[-30,22],[-35,40],[-33,62],[-30,80],[-26,64],[-24,48],[-16,38],[-6,30],[0,27]],H,ST);
   spBoth(g,[[-22,38],[-25,58],[-21,50],[-19,40]],H,{stroke:S,'stroke-width':1});
   spBoth(g,[[-11,32],[-14,48],[-9,40]],H,{stroke:S,'stroke-width':1});
   spBoth(g,[[-27,62],[-29,84],[-25,74]],H,{stroke:S,'stroke-width':1});
   spR(g,-8,13,12,2.5,L,{opacity:.85});spR(g,-26,26,9,2,L,{opacity:.8});spR(g,17,26,9,2,L,{opacity:.8})}
 },
 messy_short:{
  back(F,pal){const g=F.back,H=pal.hair,S=pal.hair_shadow,ST={stroke:S,'stroke-width':1.2};
   spP(g,[[-34,34],[-32,18],[-20,8],[0,6],[20,8],[32,18],[34,34],[30,60],[-30,60]],H,ST);
   spBoth(g,[[-29,56],[-27,76],[-15,70]],H,ST)},
  locks(F,pal){},
  front(F,pal){const g=F.head,H=pal.hair,S=pal.hair_shadow,L=pal.hair_light,ST={stroke:S,'stroke-width':1.2};
   spP(g,[[-26,32],[26,32],[22,39],[-22,39]],pal.skin_shadow,{opacity:.4});
   spP(g,[[-36,38],[-38,22],[-30,12],[-26,20],[-20,6],[-12,16],[-6,3],[2,15],[10,2],[16,15],[24,5],[28,18],[36,11],[38,26],[35,40],[31,30],[23,35],[17,28],[9,37],[1,29],[-7,38],[-16,31],[-24,40],[-30,33]],H,ST);
   spP(g,[[-24,34],[-21,54],[-16,46],[-13,35]],H,ST);spP(g,[[-6,34],[-3,50],[1,37]],H,ST);spP(g,[[11,33],[14,52],[19,40]],H,ST);
   spBoth(g,[[-30,34],[-30,58],[-27,50]],H,ST);
   spR(g,-14,9,8,2,L,{opacity:.8});spR(g,10,8,9,2,L,{opacity:.8});spR(g,-30,17,6,2,L,{opacity:.7});spR(g,24,14,7,2,L,{opacity:.7})}
 }
};
/* ---------------- 눈 / 눈썹 / 입 ---------------- */
/* ---------------- 얼굴형: BEFORE 의 각진 도트 얼굴을 유지하되, 턱 끝만 살짝 좁혀 네모진 느낌을 줄인 3종 ---------------- */
const SP_FACE={
 jaw_slim:{poly:[[-28,30],[28,30],[29,62],[25,73],[19,79],[11,84],[-11,84],[-19,79],[-25,73],[-29,62]],jaw:[[-24,74],[24,74],[19,79],[11,84],[-11,84],[-19,79]]},     // 변호사: 살짝 샤프
 jaw_clean:{poly:[[-28,30],[28,30],[29,62],[25,73],[18,80],[9,85],[-9,85],[-18,80],[-25,73],[-29,62]],jaw:[[-24,74],[24,74],[18,80],[9,85],[-9,85],[-18,80]]},      // 검사: 깔끔한 V 턱
 jaw_tidy:{poly:[[-28,30],[28,30],[29,62],[25,74],[17,80],[10,84],[-10,84],[-17,80],[-25,74],[-29,62]],jaw:[[-24,74],[24,74],[17,80],[10,84],[-10,84],[-17,80]]}      // 판사: 턱선만 정리
};
const SP_EYE={crescent_smile:{H:10,top:49,lidMin:0,cover:1,flick:1,bag:0},cool_half:{H:8,top:51,lidMin:1.6,cover:0,flick:1,bag:0},sleepy_half:{H:9,top:50,lidMin:3.8,cover:0,flick:0,bag:1}};
function spEye(F,pal,side,cfg,hl){const h=F.head,cx=side*14,x0=cx-7,top=cfg.top,H=cfg.H,id='spc'+(++SPUID);
 const cp=spEl('clipPath',{id:id},F.defs);spEl('rect',{x:SPX+x0,y:top,width:14,height:H},cp);
 spR(h,x0,top,14,H,'#fff');
 const pi=spEl('g',{},spEl('g',{'clip-path':'url(#'+id+')'},h));
 spR(pi,cx-4,top-1,8,H+2,pal.eye);spR(pi,cx-3,top+H*0.5,6,H*0.5+1,pal.iris_light,{opacity:.6});spR(pi,cx-2,top,4,H,pal.pupil);
 spR(pi,cx-3.5,top+1,2.5,2.5,pal.eye_light);if(hl>=2)spR(pi,cx+1,top+H-3.5,1.5,1.5,pal.eye_light,{opacity:.85});
 if(cfg.cover)spP(h,[[x0-1,top+H+1],[x0-1,top+H-3.5],[cx-4,top+H-5.5],[cx+4,top+H-5.5],[x0+15,top+H-3.5],[x0+15,top+H+1]],pal.skin);
 if(cfg.bag)spR(h,x0,top+H,14,2,pal.eye_bag,{opacity:.85});
 const lid=spR(h,x0-1,top-1,16,cfg.lidMin,pal.skin),edge=spR(h,x0-1,top-2+cfg.lidMin,16,2,pal.outline);
 spR(h,x0-1.5,top-2.5,17,2.6,pal.outline);if(cfg.flick)spR(h,side>0?x0+14:x0-3.5,top-4.5,3.5,2.4,pal.outline);
 return {g:pi,lid:lid,edge:edge,H:H,top:top,min:cfg.lidMin}}
const SP_BROW={
 arched_raised(g,c){spP(g,[[-22,44],[-17,40.5],[-9,41.5],[-8,43.5],[-16,42.5],[-21,46]],c);spP(g,[[8,42.5],[16,37.5],[23,39.5],[22,41.5],[16,40],[9,44.5]],c)},
 straight_sharp(g,c){spP(g,[[-23,43.5],[-8,46],[-8,48],[-23,45.5]],c);spP(g,[[8,46],[23,43.5],[23,45.5],[8,48]],c)},
 low_tired(g,c){spP(g,[[-22,48],[-8,45],[-8,47.5],[-22,50.5]],c);spP(g,[[8,45],[22,48],[22,50.5],[8,47.5]],c)}};
const SP_MOUTH={
 smirk:{def:'smile',grin:[[-9,69,18,4,'mouth'],[-7,69,14,1.6,'#ffffff'],[9,67.5,2.5,3,'mouth'],[-11,69.5,2,2,'mouth']],smile:[[-6,71,12,2.2,'mouth'],[6,69.5,2.5,2.6,'mouth'],[-7.5,71.2,1.8,1.8,'mouth']],open:[[-6,68,12,9,'mouth'],[-3,73,6,3.5,'tongue']],flat:[[-5,71.5,10,2,'mouth'],[5,70,2.5,2.5,'mouth']],hmm:[[-3,71,6,3.5,'mouth']]},
 thin_cool:{def:'flat',grin:[[-6,71.5,12,1.8,'mouth'],[-7.5,70.2,1.8,1.8,'mouth'],[5.7,70.2,1.8,1.8,'mouth']],smile:[[-5,71.8,10,1.8,'mouth']],open:[[-5,69,10,8,'mouth'],[-3,73,6,3,'tongue']],flat:[[-5,72,10,1.6,'mouth']],hmm:[[-3,71.5,6,3,'mouth']]},
 weary:{def:'flat',grin:[[-5,72,10,1.8,'mouth'],[4,70.8,2.4,1.8,'mouth']],smile:[[-5,72,10,1.8,'mouth'],[-6.6,73.2,1.8,1.6,'mouth'],[4.8,73.2,1.8,1.6,'mouth']],open:[[-6,67,12,13,'mouth'],[-3.5,74,7,4.5,'tongue']],flat:[[-5,72,10,1.8,'mouth'],[-6.6,73.2,1.8,1.6,'mouth'],[4.8,73.2,1.8,1.6,'mouth']],hmm:[[-3,71.5,6,3.5,'mouth']]}};
/* ---------------- 의상 ---------------- */
const SP_OUTFIT={
 slim_suit(F,pal,OL,TH){const g=F.torso;
  spP(g,[[-8,78],[8,78],[9,98],[-9,98]],pal.skin_shadow);
  spP(g,[[-35,96],[35,96],[39,108],[31,152],[34,232],[-34,232],[-31,152],[-39,108]],pal.suit,OL);
  spP(g,[[-35,96],[35,96],[37,103],[-37,103]],pal.suit_light,{opacity:.8});
  spP(g,[[-11,95],[11,95],[0,136]],pal.shirt,TH);
  spBoth(g,[[-12,94],[-27,99],[-23,136],[-8,127]],pal.suit_light,OL);
  spBoth(g,[[-12,93],[-4,99],[-13,106],[-16,98]],pal.shirt,TH);
  spP(g,[[-3,100],[3,100],[4,106],[-4,106]],pal.tie);spP(g,[[-3.5,106],[3.5,106],[5,134],[0,142],[-5,134]],pal.tie);
  spR(g,-24,115,5,1.2,pal.pin);spR(g,-22,113,1.2,5,pal.pin);spR(g,-25,118,7,1.2,pal.pin);   // 라펠의 작은 저울 핀
  F.sleeve={color:pal.suit,cuff:pal.shirt,w:12}},
 charcoal_suit(F,pal,OL,TH){const g=F.torso;
  spP(g,[[-8,78],[8,78],[9,98],[-9,98]],pal.skin_shadow);
  spP(g,[[-33,186],[-1,186],[-1,232],[-30,232]],pal.suit,OL);spP(g,[[33,186],[1,186],[1,232],[30,232]],pal.suit,OL);
  spP(g,[[-39,96],[39,96],[43,110],[40,160],[44,192],[-44,192],[-40,160],[-43,110]],pal.suit,OL);
  spP(g,[[-39,96],[39,96],[41,104],[-41,104]],pal.suit_light,{opacity:.8});
  spP(g,[[-11,95],[11,95],[0,148]],pal.shirt,TH);
  spBoth(g,[[-10,94],[-27,100],[-29,138],[-20,152],[-4,134]],pal.suit_light,OL);
  spBoth(g,[[-11,93],[-3,99],[-12,107],[-15,98]],pal.shirt,TH);
  spP(g,[[-2.5,99],[2.5,99],[3.5,105],[-3.5,105]],pal.tie);spP(g,[[-3,105],[3,105],[4.5,140],[0,148],[-4.5,140]],pal.tie);
  F.sleeve={color:pal.suit,cuff:pal.shirt,w:14}},
 judge_robe(F,pal,OL,TH){const g=F.torso;
  spP(g,[[-9,78],[9,78],[10,98],[-10,98]],pal.skin_shadow);
  spP(g,[[-47,98],[47,98],[54,124],[51,232],[-51,232],[-54,124]],pal.robe,OL);
  spP(g,[[-47,98],[47,98],[51,109],[-51,109]],pal.robe_light,{opacity:.7});
  spP(g,[[-19,97],[19,97],[9,154],[-9,154]],pal.robe_inner);
  spP(g,[[-9,97],[9,97],[0,118]],pal.shirt,TH);
  spBoth(g,[[-19,95],[-38,100],[-35,156],[-8,126]],pal.robe_light,OL);
  spBoth(g,[[-9,95],[-2,100],[-10,107]],pal.shirt,TH);
  spP(g,[[-3,107],[3,107],[4,113],[-4,113]],pal.tie);spP(g,[[-3,113],[4,113],[7,140],[2,152],[-3,140]],pal.tie);
  [-20,-34,20,34].forEach(x=>spR(g,x,150,1.5,80,pal.robe_light,{opacity:.35}));
  const bx=-28,by=132;spR(g,bx-2,by-9,2.4,6,pal.pin);spR(g,bx+1,by-9,2.4,6,pal.pin);spEl('circle',{cx:SPX+bx,cy:by,r:4,fill:pal.pin,stroke:pal.outline,'stroke-width':1},g);   // 라펠의 작은 토끼 핀
  spR(g,bx-2,by-1,1.2,1.2,pal.outline);spR(g,bx+1,by-1,1.2,1.2,pal.outline);
  F.sleeve={color:pal.robe,cuff:pal.shirt,w:17}}
};
/* ---------------- 캐릭터 조립 ---------------- */
function buildFigure(parent,key){
 const C=D.cast[key],pal=C.palette,st=C.style,OL={stroke:pal.outline,'stroke-width':2,'stroke-linejoin':'round'},TH={stroke:pal.outline,'stroke-width':1.2,'stroke-linejoin':'round'};
 const rs=C.render||{},F={key:key,pal:pal,style:st,render:rs,root:spEl('g',{'shape-rendering':rs.shape_rendering||'crispEdges'},parent)};
 F.defs=spEl('defs',{},F.root);F.back=spEl('g',{},F.root);F.torso=spEl('g',{},F.root);F.head=spEl('g',{},F.root);
 const hair=SP_HAIR[st.hair];hair.back(F,pal);SP_OUTFIT[st.outfit](F,pal,OL,TH);hair.locks(F,pal);
 const h=F.head,fc=SP_FACE[st.face];
 spP(h,[[-29,48],[-33,52],[-33,60],[-29,62]],pal.skin,OL);spP(h,[[29,48],[33,52],[33,60],[29,62]],pal.skin,OL);
 spP(h,fc.poly,pal.skin,OL);
 spP(h,fc.jaw,pal.skin_shadow,{opacity:.55});
 spR(h,-24,64,8,4,pal.blush,{opacity:.75});spR(h,16,64,8,4,pal.blush,{opacity:.75});spR(h,-1.5,63,3,3,pal.skin_shadow);
 const cfg=Object.assign({},SP_EYE[st.eyes],{H:st.eye_h,top:st.eye_top,lidMin:st.lid_min}),hl=(C.render&&C.render.eye_highlight_px)||2;
 F.eyes=[spEye(F,pal,-1,cfg,hl),spEye(F,pal,1,cfg,hl)];
 F.brows=spEl('g',{},h);SP_BROW[st.brows](F.brows,pal.brow);
 const md=SP_MOUTH[st.mouth];F.mouths={};['grin','smile','open','flat','hmm'].forEach(n=>{const g=spEl('g',{display:'none'},h);md[n].forEach(r=>spR(g,r[0],r[1],r[2],r[3],pal[r[4]]||r[4]));F.mouths[n]=g});
 F.defaultMouth=md.def;hair.front(F,pal);
 F.showMouth=n=>{for(const k in F.mouths)F.mouths[k].setAttribute('display',k===n?'inline':'none')};
 F.setLid=v=>F.eyes.forEach(e=>{const hgt=e.min+Math.max(0,Math.min(1,v))*(e.H+1-e.min);e.lid.setAttribute('height',hgt.toFixed(2));e.edge.setAttribute('y',(e.top-2+hgt).toFixed(2))});
 F.setGaze=(gx,gy)=>F.eyes.forEach(e=>e.g.setAttribute('transform','translate('+Math.max(-3,Math.min(3,gx*0.55)).toFixed(2)+' '+Math.max(-3,Math.min(3,gy*0.55)).toFixed(2)+')'));
 F.setBrow=dy=>F.brows.setAttribute('transform','translate(0 '+dy.toFixed(2)+')');
 F.showMouth(F.defaultMouth);F.setLid(0);return F}
/* 재판 화면용 반신상 (viewBox 100×150) */
function buildBust(el,key){const rs=D.cast[key].render||{};if(rs.mode==='pixel_hd')return hdBust(el,key);const svg=spEl('svg',{viewBox:'0 0 100 150','shape-rendering':rs.shape_rendering||'crispEdges'});el.appendChild(svg);
 const F=buildFigure(spEl('g',{transform:'translate(-25 -2) scale(.75)'},svg),key);F.mouths[F.defaultMouth].setAttribute('class','mouth');return F}
/* 말풍선이 화면 밖으로 나가지 않도록 가로 위치를 보정 (글이 길면 박스가 커지고, 화면 가장자리에 닿으면 안쪽으로 밀어 준다) */
function spPlaceBubble(b){try{if(!b.getBoundingClientRect)return;b.style.marginLeft='0px';const r=b.getBoundingClientRect(),W=document.documentElement.clientWidth;let dx=0;if(r.right>W-8)dx=W-8-r.right;if(r.left+dx<8)dx=8-r.left;b.style.marginLeft=dx.toFixed(0)+'px'}catch(e){}}
/* ============ HD 도트 엔진 (픽셀 단위로 직접 칠하는 고해상도 도트 페인터) ============
   SVG 도형이 아니라 '픽셀 격자'에 한 칸씩 색을 칠한 뒤 canvas 로 보여 준다.
   · 머리카락: 한 가닥(lock)마다 중심선 + 폭으로 만들고, 결(밝은 줄/어두운 줄)·윤곽 명암·반사광(천사 고리)을 칠한다.
   · 눈: 공막 음영 · 홍채 세로 그라데이션 · 눈동자 · 이중 하이라이트 · 윗속눈썹/눈꼬리 · 눈꺼풀 그림자.
   · 피부/의상: 왼쪽 위에서 빛이 온다고 보고 밝은 면 · 기본 · 그림자 · 깊은 그림자를 단계별로 칠하고, 윤곽선은 이웃 색을 섞어 색 있는 외곽선으로 만든다.
   characters.py 의 palette/style 을 그대로 읽는다. 도화지 크기 200×232 = 인물 좌표계와 같음(1단위 = 1픽셀). */
const HDW=200,HDH=232,HDX=100;
const hdHex=h=>{h=String(h).replace('#','');return [parseInt(h.slice(0,2),16),parseInt(h.slice(2,4),16),parseInt(h.slice(4,6),16)]};
const hdMix=(a,b,t)=>[Math.round(a[0]+(b[0]-a[0])*t),Math.round(a[1]+(b[1]-a[1])*t),Math.round(a[2]+(b[2]-a[2])*t)];
const HD_WHITE=[255,255,255];
function hdRnd(x,y,s){let h=Math.imul(x*7919+(s||0)*104729,374761393)^Math.imul(y*6271+13,668265263);h=Math.imul(h^(h>>>13),1274126177);return ((h^(h>>>16))>>>0)/4294967295}
class HdPx{constructor(w,h){this.w=w;this.h=h;this.d=new Uint8ClampedArray(w*h*4)}
 put(x,y,c){x=Math.round(x);y=Math.round(y);if(x<0||y<0||x>=this.w||y>=this.h)return;const i=(y*this.w+x)*4;this.d[i]=c[0];this.d[i+1]=c[1];this.d[i+2]=c[2];this.d[i+3]=255}
 alpha(x,y){return(x<0||y<0||x>=this.w||y>=this.h)?0:this.d[(y*this.w+x)*4+3]}
 col(x,y){const i=(y*this.w+x)*4;return [this.d[i],this.d[i+1],this.d[i+2]]}
 canvas(){const c=document.createElement('canvas');c.width=this.w;c.height=this.h;c.getContext('2d').putImageData(new ImageData(new Uint8ClampedArray(this.d),this.w,this.h),0,0);return c}}
/* ----- 마스크(칠할 영역) 도구 ----- */
function hdPoly(w,h,pts){const m=new Uint8Array(w*h),n=pts.length;let y0=1e9,y1=-1e9;for(const p of pts){y0=Math.min(y0,p[1]);y1=Math.max(y1,p[1])}
 for(let y=Math.max(0,Math.floor(y0));y<=Math.min(h-1,Math.ceil(y1));y++){const yc=y+0.5,xs=[];for(let i=0;i<n;i++){const a=pts[i],b=pts[(i+1)%n];if((a[1]<=yc&&b[1]>yc)||(b[1]<=yc&&a[1]>yc))xs.push(a[0]+(yc-a[1])/(b[1]-a[1])*(b[0]-a[0]))}
  xs.sort((p,q)=>p-q);for(let k=0;k+1<xs.length;k+=2){const xa=Math.ceil(xs[k]-0.5),xb=Math.ceil(xs[k+1]-0.5)-1;for(let x=Math.max(0,xa);x<=Math.min(w-1,xb);x++)m[y*w+x]=1}}return m}
function hdEll(w,h,cx,cy,rx,ry){const m=new Uint8Array(w*h);for(let y=Math.max(0,Math.floor(cy-ry));y<=Math.min(h-1,Math.ceil(cy+ry));y++)for(let x=Math.max(0,Math.floor(cx-rx));x<=Math.min(w-1,Math.ceil(cx+rx));x++){const a=(x+.5-cx)/rx,b=(y+.5-cy)/ry;if(a*a+b*b<=1)m[y*w+x]=1}return m}
const hdAt=(m,w,h,x,y)=>(x<0||y<0||x>=w||y>=h)?0:m[y*w+x];
function hdEdge(m,w,h,dx,dy){const o=new Uint8Array(w*h);for(let y=0;y<h;y++)for(let x=0;x<w;x++)if(m[y*w+x]&&!hdAt(m,w,h,x+dx,y+dy))o[y*w+x]=1;return o}
const hdAnd=(a,b)=>a.map((v,i)=>v&b[i]),hdOr=(a,b)=>a.map((v,i)=>v|b[i]),hdSub=(a,b)=>a.map((v,i)=>(v&&!b[i])?1:0);
function hdShift(m,w,h,dx,dy){const o=new Uint8Array(w*h);for(let y=0;y<h;y++)for(let x=0;x<w;x++)if(m[y*w+x]){const nx=x+dx,ny=y+dy;if(nx>=0&&ny>=0&&nx<w&&ny<h)o[ny*w+nx]=1}return o}
function hdPaint(px,m,c){for(let i=0;i<m.length;i++)if(m[i])px.put(i%px.w,(i/px.w)|0,c)}
function hdLine(px,x0,y0,x1,y1,c,m){x0=Math.round(x0);y0=Math.round(y0);x1=Math.round(x1);y1=Math.round(y1);const dx=Math.abs(x1-x0),dy=Math.abs(y1-y0),sx=x0<x1?1:-1,sy=y0<y1?1:-1;let e=dx-dy,g=0;
 for(;;){if(!m||hdAt(m,px.w,px.h,x0,y0))px.put(x0,y0,c);if((x0===x1&&y0===y1)||g++>2000)break;const e2=2*e;if(e2>-dy){e-=dy;x0+=sx}if(e2<dx){e+=dx;y0+=sy}}}
function hdPolyline(px,pts,c,m){for(let i=0;i<pts.length-1;i++)hdLine(px,pts[i][0],pts[i][1],pts[i+1][0],pts[i+1][1],c,m)}
/* 색 있는 외곽선: 투명 픽셀 중 불투명 이웃이 있으면, 이웃 색을 윤곽색 쪽으로 섞어 칠한다 */
function hdOutline(px,ol,k){const add=[];for(let y=0;y<px.h;y++)for(let x=0;x<px.w;x++){if(px.alpha(x,y))continue;let nb=null;
 if(px.alpha(x-1,y))nb=px.col(x-1,y);else if(px.alpha(x+1,y))nb=px.col(x+1,y);else if(px.alpha(x,y-1))nb=px.col(x,y-1);else if(px.alpha(x,y+1))nb=px.col(x,y+1);
 if(nb)add.push([x,y,hdMix(nb,ol,k)])}add.forEach(a=>px.put(a[0],a[1],a[2]))}
/* ----- 곡선/머리 가닥 ----- */
function hdCatmull(pts,per,closed){const n=pts.length,out=[],seg=closed?n:n-1;for(let i=0;i<seg;i++){const g=k=>pts[closed?(i+k+n)%n:Math.max(0,Math.min(n-1,i+k))],p0=g(-1),p1=g(0),p2=g(1),p3=g(2);
 for(let s=0;s<per;s++){const t=s/per,t2=t*t,t3=t2*t;out.push([0.5*(2*p1[0]+(-p0[0]+p2[0])*t+(2*p0[0]-5*p1[0]+4*p2[0]-p3[0])*t2+(-p0[0]+3*p1[0]-3*p2[0]+p3[0])*t3),0.5*(2*p1[1]+(-p0[1]+p2[1])*t+(2*p0[1]-5*p1[1]+4*p2[1]-p3[1])*t2+(-p0[1]+3*p1[1]-3*p2[1]+p3[1])*t3)])}}
 if(!closed)out.push(pts[n-1]);return out}
const hdAbs=pts=>pts.map(q=>[HDX+q[0],q[1]]);
function hdLockGeom(ctrl,widths){const per=6,P=hdCatmull(hdAbs(ctrl),per,false),Wd=hdCatmull(widths.map((w,i)=>[i,w]),per,false).map(q=>Math.max(0.5,q[1])),L=[],R=[],N=[];
 for(let i=0;i<P.length;i++){const a=P[Math.max(0,i-1)],b=P[Math.min(P.length-1,i+1)];let dx=b[0]-a[0],dy=b[1]-a[1];const l=Math.hypot(dx,dy)||1,nx=-dy/l,ny=dx/l;N.push([nx,ny]);L.push([P[i][0]+nx*Wd[i]/2,P[i][1]+ny*Wd[i]/2]);R.push([P[i][0]-nx*Wd[i]/2,P[i][1]-ny*Wd[i]/2])}
 return {P:P,Wd:Wd,N:N,poly:L.concat(R.reverse())}}
/* 머리 한 가닥: 기본색 → 결(밝은 줄·어두운 줄) → 위쪽 밝은 가장자리 / 아래쪽 그림자 */
function hdLock(px,lk,C,mirror){const w=px.w,h=px.h,ctrl=mirror?lk.c.map(q=>[-q[0],q[1]]):lk.c,g=hdLockGeom(ctrl,lk.w),m=hdPoly(w,h,g.poly);
 hdPaint(px,m,C.base);
 const n=g.P.length;
 [[-0.34,C.sh,0],[-0.12,C.lt,1],[0.12,C.base,0],[0.3,C.sh,2]].forEach(o=>{const pts=[];for(let i=0;i<n;i++)pts.push([g.P[i][0]+g.N[i][0]*o[0]*g.Wd[i],g.P[i][1]+g.N[i][1]*o[0]*g.Wd[i]]);
  if(o[2]===1){hdPolyline(px,pts.slice(Math.floor(n*0.05),Math.floor(n*0.8)),o[1],m)}else if(o[2]===2){hdPolyline(px,pts.slice(Math.floor(n*0.15),Math.floor(n*0.9)),o[1],m)}else if(o[1]!==C.base){hdPolyline(px,pts.slice(Math.floor(n*0.1),Math.floor(n*0.6)),o[1],m)}});
 const sh=hdEdge(m,w,h,2,2),lt=hdEdge(m,w,h,-1,-1);hdPaint(px,hdSub(sh,lt),C.sh);hdPaint(px,hdSub(lt,sh),C.lt);return m}
/* ----- 색 단계(팔레트 → 밝은 면/기본/그림자/깊은 그림자) ----- */
function hdRamps(pal){const H=hdHex,ol=H(pal.outline);
 const R={ol:ol,skin:{hi:hdMix(H(pal.skin),[255,251,240],.55),base:H(pal.skin),sh:H(pal.skin_shadow),deep:hdMix(H(pal.skin_shadow),[150,66,84],.38),blush:H(pal.blush)},
  hair:{hi:hdMix(H(pal.hair_light),HD_WHITE,.34),lt:H(pal.hair_light),base:H(pal.hair),sh:H(pal.hair_shadow),deep:hdMix(H(pal.hair_shadow),[12,8,20],.5)},
  eye:H(pal.eye),eyeL:H(pal.iris_light),pupil:H(pal.pupil),eyeLight:H(pal.eye_light),mouth:H(pal.mouth),tongue:H(pal.tongue)};
 if(pal.suit){const b=H(pal.suit),l=H(pal.suit_light);R.suit={hi:hdMix(l,HD_WHITE,.2),lt:l,base:b,sh:hdMix(b,[8,8,18],.42),deep:hdMix(b,[4,4,10],.68)}}
 if(pal.shirt){const b=H(pal.shirt),s=H(pal.shirt_shadow);R.shirt={hi:HD_WHITE,base:b,sh:s,deep:hdMix(s,[90,96,130],.4)}}
 if(pal.tie){const b=H(pal.tie);R.tie={hi:hdMix(b,HD_WHITE,.32),base:b,sh:hdMix(b,[0,0,0],.45)}}
 if(pal.pin)R.pin={base:H(pal.pin),hi:hdMix(H(pal.pin),HD_WHITE,.5)};
 if(pal.robe){const b=H(pal.robe),l=H(pal.robe_light);R.robe={hi:hdMix(l,HD_WHITE,.14),lt:l,base:b,sh:hdMix(b,[0,0,8],.5),deep:hdMix(b,[0,0,4],.75)};R.robeIn=H(pal.robe_inner)}
 if(pal.eye_bag)R.eyeBag=H(pal.eye_bag);return R}
/* ----- 얼굴 바탕: 피부 4단계 명암 + 홍조 + 코 + 귀 ----- */
function hdPaintFace(px,R,st,HM){const w=px.w,h=px.h,S=R.skin,poly=hdCatmull(hdAbs(SP_FACE[st.face].poly),3,true),FM=hdPoly(w,h,poly);
 const EL=hdEll(w,h,HDX-29.5,62,3.4,6.2),ER=hdEll(w,h,HDX+29.5,62,3.4,6.2);hdPaint(px,EL,S.base);hdPaint(px,ER,S.base);
 hdPaint(px,hdAnd(EL,hdEll(w,h,HDX-29.5,62.5,1.4,3)),S.sh);hdPaint(px,hdAnd(ER,hdEll(w,h,HDX+29.5,62.5,1.4,3)),S.sh);
 hdPaint(px,FM,S.base);
 const lowFace=hdPoly(w,h,hdAbs([[-40,44],[40,44],[40,100],[-40,100]]));
 hdPaint(px,hdAnd(hdAnd(hdEdge(FM,w,h,4,0),lowFace),FM),S.sh);hdPaint(px,hdAnd(hdAnd(hdEdge(FM,w,h,2,0),lowFace),FM),S.deep);                     // 오른쪽 볼 그림자
 hdPaint(px,hdAnd(hdEdge(FM,w,h,0,4),hdPoly(w,h,hdAbs([[-40,70],[40,70],[40,100],[-40,100]]))),S.sh);hdPaint(px,hdAnd(hdEdge(FM,w,h,0,2),hdPoly(w,h,hdAbs([[-40,72],[40,72],[40,100],[-40,100]]))),S.deep);   // 턱 밑 그림자
 const castD=hdSub(hdAnd(hdShift(HM,w,h,1,2),FM),HM),castS=hdSub(hdSub(hdAnd(hdShift(HM,w,h,1,5),FM),HM),castD);hdPaint(px,castS,S.sh);hdPaint(px,castD,S.deep);       // 앞머리가 이마에 드리우는 그림자
 hdPaint(px,hdAnd(hdEll(w,h,HDX-13,66,5,2.6),FM),S.hi);hdPaint(px,hdAnd(hdEll(w,h,HDX-7,40,9,3),FM),S.hi);                                           // 볼·이마 하이라이트
 [[-1,-1],[1,-1]].forEach(()=>{});
 for(let y=61;y<=65;y++)px.put(HDX-1,y,S.hi);for(let y=62;y<=66;y++)px.put(HDX+1,y,S.sh);px.put(HDX,68,S.deep);px.put(HDX-1,68,S.deep);px.put(HDX+1,68,S.sh);px.put(HDX-2,67,S.sh);   // 코
 [-1,1].forEach(s=>{const bm=hdAnd(hdEll(w,h,HDX+s*17.5,68,5.8,2.8),FM),core=hdAnd(bm,hdEll(w,h,HDX+s*17.5,68,3.6,1.7));hdPaint(px,hdSub(bm,core),S.base);
  for(let i=0;i<bm.length;i++)if(bm[i]&&!core[i]){const x=i%w,y=(i/w)|0;if((x+y)%2===0)px.put(x,y,hdMix(S.base,S.blush,.55))}hdPaint(px,core,hdMix(S.base,S.blush,.8))});               // 볼 홍조(가장자리는 체크무늬로 번지게)
 hdOutline(px,R.ol,0.72);return FM}
/* ----- 눈 (캐릭터 데이터의 크기·위치를 따름) ----- */
const HD_EYE={crescent_smile:{tilt:2,flick:4,smile:1,pink:1,irisRx:3.7,lash:3},cool_half:{tilt:2.8,flick:4,smile:0,pink:0,irisRx:3.6,lash:2},sleepy_half:{tilt:1.8,flick:2,smile:0,pink:0,irisRx:3.6,lash:2,bag:1}};
function hdEyeSprite(R,st,cfg,side,rows,gx,gy,hl){const SW=36,SH=28,s=side,cx=18,top=9,H=st.eye_h,T=cfg.tilt,yc=top+H*0.5,ox=HDX+s*14-cx,oy=st.eye_top-top,px=new HdPx(SW,SH);
 const pts=[[cx-s*7.5,yc+1],[cx-s*4.5,top+1.2],[cx-s*1,top-0.2],[cx+s*3,top+0.2-T*0.3],[cx+s*6,top+1-T*0.8],[cx+s*8,yc-T],[cx+s*7,top+H-0.8-T*0.5],[cx+s*3,top+H+0.2],[cx-s*1,top+H+0.4],[cx-s*5,top+H-0.4]];
 const EM=hdPoly(SW,SH,pts),skin=R.skin;
 const cover=new Uint8Array(SW*SH);for(let y=0;y<SH;y++)for(let x=0;x<SW;x++)if(EM[y*SW+x]&&y<top+rows)cover[y*SW+x]=1;const EV=hdSub(EM,cover);
 const SCL=hdMix([246,247,255],HD_WHITE,0),SCLs=[214,219,236],SCLd=hdMix(SCLs,R.ol,.25);
 hdPaint(px,EV,SCL);hdPaint(px,hdAnd(EV,hdEdge(EM,SW,SH,2,0)),SCLs);hdPaint(px,hdAnd(EV,hdEdge(EM,SW,SH,-2,0)),SCLs);
 const ix=cx+gx,iy=yc+gy*0.6+1.7,rx=cfg.irisRx,ry=H*0.56,IM=hdAnd(EV,hdEll(SW,SH,ix,iy,rx,ry)),ird=hdMix(R.eye,R.ol,.5),mid=hdMix(R.eye,R.eyeL,.55);
 for(let y=0;y<SH;y++)for(let x=0;x<SW;x++)if(IM[y*SW+x]){const t=(y+.5-(iy-ry))/(2*ry);px.put(x,y,t<.2?ird:t<.46?R.eye:t<.74?mid:R.eyeL)}
 hdPaint(px,hdAnd(hdEdge(IM,SW,SH,-1,0),IM),ird);hdPaint(px,hdAnd(hdEdge(IM,SW,SH,1,0),IM),ird);hdPaint(px,hdAnd(hdEdge(IM,SW,SH,0,-1),IM),ird);
 hdPaint(px,hdAnd(hdEll(SW,SH,ix,iy+0.5,1.9,H*0.3),IM),R.pupil);
 const hx=Math.round(ix-2.4),hy=Math.round(iy-ry+1.8);[[0,0],[1,0],[0,1],[1,1]].forEach(d=>{if(hdAt(IM,SW,SH,hx+d[0],hy+d[1]))px.put(hx+d[0],hy+d[1],R.eyeLight)});
 if(hl>=2){const lx=Math.round(ix+2.4),ly=Math.round(iy+ry-3.4);if(hdAt(IM,SW,SH,lx,ly))px.put(lx,ly,hdMix(R.eyeLight,R.eyeL,.35))}
 hdPaint(px,hdAnd(EV,hdSub(hdShift(cover,SW,SH,0,1),cover)),hdMix(R.eye,R.ol,.5));                                                             // 눈꺼풀이 드리우는 그림자
 if(cfg.smile){const sm=hdPoly(SW,SH,[[cx-s*9,top+H+3],[cx-s*9,top+H-0.2],[cx-s*5,top+H-2.2],[cx,top+H-3.2],[cx+s*5,top+H-2.2],[cx+s*9,top+H-0.2-T],[cx+s*9,top+H+3]]);hdPaint(px,sm,skin.base);
  hdPolyline(px,[[cx-s*8,top+H-0.8],[cx-s*5,top+H-2],[cx,top+H-2.6],[cx+s*5,top+H-2],[cx+s*8,top+H-0.6-T]].map(q=>[q[0],q[1]+1.2]),skin.hi)}
 let outerY=top;
 for(let x=0;x<SW;x++){let yt=-1;for(let y=0;y<SH;y++)if(EV[y*SW+x]){yt=y;break}if(yt>=0){px.put(x,yt-1,R.ol);px.put(x,yt-2,R.ol);if(cfg.lash>=3)px.put(x,yt-3,hdMix(R.ol,skin.sh,.25));}}
 if(EV.every(v=>!v)){hdPolyline(px,[[cx-s*7,yc+1.5],[cx-s*3,top+H-0.4],[cx+s*2,top+H+0.4],[cx+s*7.5,yc-T+1]],R.ol);hdPolyline(px,[[cx-s*7,yc+0.5],[cx-s*3,top+H-1.4],[cx+s*2,top+H-0.6],[cx+s*7.5,yc-T]],R.ol)}
 let oxp=cx+s*8,oyp=yc-T-2;hdLine(px,oxp,oyp,oxp+s*cfg.flick,oyp-cfg.flick*0.7,R.ol);hdLine(px,oxp,oyp+1,oxp+s*(cfg.flick-1),oyp-cfg.flick*0.7+1,R.ol);
  if(cfg.pink)for(let k=-5;k<=5;k++){const x=Math.round(cx+s*k);px.put(x,top-4,hdMix(skin.base,skin.blush,.45));px.put(x,top-3,hdMix(skin.base,skin.blush,.6))}
 for(let k=-3;k<=4;k++)px.put(Math.round(cx+s*k),top-5.4+(Math.abs(k)>2?1:0),hdMix(skin.base,skin.sh,.85));
 px.put(Math.round(cx-s*7.5),Math.round(yc+1),[232,150,160]);
 if(cfg.bag&&R.eyeBag){for(let x=0;x<SW;x++){let yb=-1;for(let y=SH-1;y>=0;y--)if(EM[y*SW+x]){yb=y;break}if(yb>=0){px.put(x,yb+1,hdMix(skin.base,R.eyeBag,.9));px.put(x,yb+2,hdMix(skin.base,R.eyeBag,.65));if((x+yb)%2===0)px.put(x,yb+3,hdMix(skin.base,R.eyeBag,.4))}}}   // 다크서클
 return {c:px.canvas(),ox:ox,oy:oy}}
/* ----- 눈썹 / 입 ----- */
const HD_BROW={
 arched_raised:{L:{c:[[-25,3],[-19,-0.5],[-12,-1.2],[-6,0.8]],w:[1.4,2.6,2.4,1.1]},R:{c:[[5,-1.6],[13,-5.6],[20,-5.6],[25,-2.6]],w:[1.2,2.8,2.6,1.2]}},
 low_tired:{L:{c:[[-25,2.8],[-16,0.4],[-6,-1.6]],w:[2.2,2.8,1.9]},R:{c:[[6,-1.6],[16,0.4],[25,2.8]],w:[1.9,2.8,2.2]}},
 straight_sharp:{L:{c:[[-25,1.4],[-17,2.6],[-6,3.8]],w:[1.2,2.1,1.3]},R:{c:[[6,3.8],[17,2.6],[25,1.2]],w:[1.3,2.1,1.2]}}};
function hdPaintBrows(R,st){const px=new HdPx(HDW,70),b=HD_BROW[st.brows],c=hdMix(R.hair.base,R.hair.sh,.3),top=st.eye_top-8-20,fix=o=>({c:o.c.map(q=>[q[0],q[1]+st.eye_top-6-top]),w:o.w});
 [b.L,b.R].forEach(o=>{const g=hdLockGeom(fix(o).c,o.w),m=hdPoly(HDW,70,g.poly);hdPaint(px,m,c);hdPaint(px,hdAnd(m,hdEdge(m,HDW,70,0,-1)),hdMix(c,R.hair.lt,.35))});
 return {c:px.canvas(),ox:0,oy:top}}
const HD_MOUTH={
 smirk:{def:'smile',
  grin:(px,R)=>{const w=px.w,h=px.h,m=hdPoly(w,h,[[HDX-8,74],[HDX,76],[HDX+9,72.5],[HDX+6.5,79.5],[HDX,83],[HDX-6.5,79.5]]);hdPaint(px,m,R.mouth);hdPaint(px,hdPoly(w,h,[[HDX-6.5,75],[HDX,77],[HDX+7.2,74],[HDX+5.5,77.2],[HDX,79],[HDX-5.5,77.2]]),HD_WHITE);hdPaint(px,hdAnd(m,hdEll(w,h,HDX,81.4,3.4,1.8)),R.tongue);hdPolyline(px,[[HDX-8,74],[HDX,76],[HDX+9,72.5]],hdMix(R.mouth,R.ol,.5));px.put(HDX+10,71.5,hdMix(R.skin.sh,R.ol,.3))},
  smile:(px,R)=>{hdPolyline(px,[[HDX-7,75],[HDX-3,77.2],[HDX+3,77.2],[HDX+8,73.6]],R.mouth);hdPolyline(px,[[HDX-5,75.8],[HDX-2,77.8],[HDX+2,77.8],[HDX+6,74.8]],hdMix(R.mouth,R.skin.base,.4));px.put(HDX+9,72.5,hdMix(R.skin.sh,R.ol,.3));px.put(HDX+9,73.4,hdMix(R.skin.sh,R.ol,.2));for(let x=-2;x<=2;x++)px.put(HDX+x,79,R.skin.hi)},
  open:(px,R)=>{const w=px.w,h=px.h,m=hdEll(w,h,HDX,78,4.6,4.8);hdPaint(px,m,R.mouth);hdPaint(px,hdAnd(m,hdEll(w,h,HDX,75.4,3.6,1.1)),HD_WHITE);hdPaint(px,hdAnd(m,hdEll(w,h,HDX,81,2.8,1.6)),R.tongue);hdPaint(px,hdAnd(hdEdge(m,w,h,0,-1),m),hdMix(R.mouth,R.ol,.5))},
  flat:(px,R)=>{hdPolyline(px,[[HDX-5,76.4],[HDX,77.2],[HDX+6,75]],R.mouth);hdPolyline(px,[[HDX-4,77.2],[HDX,78],[HDX+4,76.4]],hdMix(R.mouth,R.skin.base,.5))},
  hmm:(px,R)=>{hdPaint(px,hdEll(px.w,px.h,HDX,77,2.4,2),R.mouth)}},
 weary:{def:'flat',
  grin:(px,R)=>{hdPolyline(px,[[HDX-5,78.4],[HDX+2,78.2],[HDX+6,76.6]],R.mouth);px.put(HDX+7,75.8,hdMix(R.skin.sh,R.ol,.3))},
  smile:(px,R)=>{hdPolyline(px,[[HDX-5,78.8],[HDX,78.2],[HDX+5,78.8]],R.mouth)},
  open:(px,R)=>{const w=px.w,h=px.h,m=hdEll(w,h,HDX,79.5,5.4,7.2);hdPaint(px,m,R.mouth);hdPaint(px,hdAnd(m,hdEll(w,h,HDX,84,3.8,2.6)),R.tongue);hdPaint(px,hdAnd(hdEdge(m,w,h,0,-1),m),hdMix(R.mouth,R.ol,.55))},
  flat:(px,R)=>{hdPolyline(px,[[HDX-5.5,79.6],[HDX-2,77.8],[HDX+2,77.8],[HDX+5.5,79.6]],R.mouth);px.put(HDX-6,80.6,hdMix(R.skin.sh,R.mouth,.5));px.put(HDX+6,80.6,hdMix(R.skin.sh,R.mouth,.5));for(let x=-2;x<=2;x++)px.put(HDX+x,81.2,R.skin.hi)},
  hmm:(px,R)=>{hdPaint(px,hdEll(px.w,px.h,HDX,78.6,2.5,2),R.mouth)}},
 thin_cool:{def:'flat',
  grin:(px,R)=>{hdPolyline(px,[[HDX-6,76],[HDX,77.6],[HDX+6,76]],R.mouth);for(let x=-2;x<=2;x++)px.put(HDX+x,79,R.skin.hi)},
  smile:(px,R)=>{hdPolyline(px,[[HDX-5,76.6],[HDX,77.6],[HDX+5,76.6]],R.mouth)},
  open:(px,R)=>{const w=px.w,h=px.h,m=hdEll(w,h,HDX,78.4,4,4.6);hdPaint(px,m,R.mouth);hdPaint(px,hdAnd(m,hdEll(w,h,HDX,81,2.6,1.5)),R.tongue)},
  flat:(px,R)=>{hdLine(px,HDX-5,77,HDX+5,77,R.mouth);hdLine(px,HDX-3,78,HDX+3,78,hdMix(R.mouth,R.skin.base,.6));px.put(HDX-6,76,hdMix(R.skin.sh,R.mouth,.5));px.put(HDX+6,76,hdMix(R.skin.sh,R.mouth,.5));for(let x=-2;x<=2;x++)px.put(HDX+x,79.5,R.skin.hi)},
  hmm:(px,R)=>{hdPaint(px,hdEll(px.w,px.h,HDX,77.4,2.3,1.9),R.mouth)}}};
/* ----- 머리카락: 뒤쪽 덩어리 + 앞쪽 가닥(lock) 묶음. 가닥마다 결·명암을 칠하고, 정수리에 반사광(천사 고리)을 얹는다 ----- */
function hdStrands(px,M,xs,y0,y1,wave,C,seed){xs.forEach((x0,i)=>{const pts=[];for(let y=y0;y<=y1;y+=3)pts.push([HDX+x0+Math.sin(y*0.09+i*1.7)*wave+(x0/60)*(y-y0)*0.06,y]);
 hdPolyline(px,pts,(i+seed)%3===0?C.lt:(i+seed)%3===1?C.sh:C.base,M)})}
function hdArc(px,cx,cy,rx,ry,a0,a1,c,m){let prev=null;for(let a=a0;a<=a1;a+=2){const p=[HDX+cx+rx*Math.cos(a*Math.PI/180),cy+ry*Math.sin(a*Math.PI/180)];if(prev)hdLine(px,prev[0],prev[1],p[0],p[1],c,m);prev=p}}
function hdFlyaways(px,M,C,seed,ok){const w=px.w,h=px.h,e=hdEdge(M,w,h,0,-1);for(let i=0;i<e.length;i++)if(e[i]){const x=i%w,y=(i/w)|0;if(hdRnd(x,y,seed)<0.1&&ok(x,y)){px.put(x,y-1,C.sh);if(hdRnd(x,y,seed+7)<0.4)px.put(x+(hdRnd(x,y,seed+3)<0.5?-1:1),y-2,C.base)}}}
const HD_HAIR={
 long_wavy:{
  back(px,R){const w=px.w,h=px.h,C=R.hair,M=hdPoly(w,h,hdCatmull(hdAbs([[-29,44],[-31,27],[-19,11],[0,6],[19,11],[31,27],[29,44],[39,70],[43,110],[47,150],[42,176],[34,166],[28,177],[20,164],[-20,164],[-28,177],[-34,166],[-42,176],[-47,150],[-43,110],[-39,70]]),4,true));
   hdPaint(px,M,C.base);hdPaint(px,hdAnd(M,hdPoly(w,h,hdAbs([[-20,90],[20,90],[18,150],[0,160],[-18,150]]))),C.sh);hdPaint(px,hdAnd(M,hdPoly(w,h,hdAbs([[-14,94],[14,94],[10,130],[-10,130]]))),C.deep);
   hdStrands(px,M,[-46,-41,-36,-31,31,36,41,46,-26,26],38,172,1.6,C,0);hdPaint(px,hdSub(hdEdge(M,w,h,3,3),hdEdge(M,w,h,-1,-1)),C.sh);hdPaint(px,hdSub(hdEdge(M,w,h,-1,-1),hdEdge(M,w,h,3,3)),C.lt);return M},
  locks(px,R){const C=R.hair,m1=hdLock(px,{c:[[-29,62],[-34,90],[-38,120],[-39,150],[-36,166]],w:[7,10,10,8,1]},C,false);hdLock(px,{c:[[-29,62],[-34,90],[-38,120],[-39,150],[-36,166]],w:[7,10,10,8,1]},C,true)},
  front(px,R){const w=px.w,h=px.h,C=R.hair,cap=hdPoly(w,h,hdCatmull(hdAbs([[-26,32],[-23,16],[-10,9],[10,9],[23,16],[26,32],[0,24]]),4,true));hdPaint(px,cap,C.base);
   const L=[{c:[[-9,22],[4,22],[16,28],[25,40],[29,56],[29,76]],w:[3,10,12,10,7,1]},{c:[[-9,24],[6,27],[18,36],[24,50],[26,66]],w:[2,7,8,6,1]},{c:[[-9,22],[-18,23],[-26,31],[-30,45],[-30,62],[-28,84]],w:[3,9,11,9,6,1]},{c:[[-9,24],[-17,28],[-24,38],[-27,54]],w:[2,6,7,1]},{c:[[-26,56],[-28,70],[-27,84],[-24,94]],w:[4,5,4,1]},{c:[[26,56],[28,70],[27,84],[24,94]],w:[4,5,4,1]}];
   let U=cap;L.forEach(l=>{U=hdOr(U,hdLock(px,l,C,false))});
   hdArc(px,0,28,23,15,200,340,C.lt,U);hdArc(px,0,27,21,13,215,325,C.hi,U);hdArc(px,-3,28,15,10,235,300,HD_WHITE.map((v,i)=>[255,244,230][i]),U);
   hdFlyaways(px,U,C,3,(x,y)=>y<30||Math.abs(x-HDX)>31);return U}},
 messy_short:{
  back(px,R){const w=px.w,h=px.h,C=R.hair,M=hdPoly(w,h,hdCatmull(hdAbs([[-30,40],[-33,22],[-20,8],[0,5],[20,8],[33,22],[30,40],[29,62],[-29,62]]),3,true));hdPaint(px,M,C.base);
   hdPaint(px,hdAnd(M,hdPoly(w,h,hdAbs([[-22,50],[22,50],[20,64],[-20,64]]))),C.sh);
   [[-31,58],[-26,78],[-13,72]].forEach((_,i)=>{});const nape=hdPoly(w,h,hdAbs([[-27,58],[-26,80],[-12,74],[-12,58]])),nape2=hdPoly(w,h,hdAbs([[27,58],[26,80],[12,74],[12,58]]));hdPaint(px,nape,C.base);hdPaint(px,nape2,C.base);hdPaint(px,hdAnd(nape,hdEdge(nape,w,h,2,2)),C.sh);hdPaint(px,hdAnd(nape2,hdEdge(nape2,w,h,2,2)),C.sh);
   hdPaint(px,hdSub(hdEdge(M,w,h,3,3),hdEdge(M,w,h,-1,-1)),C.sh);hdPaint(px,hdSub(hdEdge(M,w,h,-1,-1),hdEdge(M,w,h,3,3)),C.lt);return M},
  locks(px,R){},
  front(px,R){const w=px.w,h=px.h,C=R.hair,cap=hdPoly(w,h,hdAbs([[-33,42],[-36,24],[-29,12],[-25,20],[-19,6],[-11,16],[-5,3],[3,15],[11,2],[17,15],[25,5],[28,18],[36,11],[37,26],[34,42],[30,31],[22,36],[16,29],[8,40],[0,31],[-7,41],[-15,32],[-23,43],[-29,35]]));
   hdPaint(px,cap,C.base);
   [[-30,40,-36,12],[-22,32,-27,10],[-14,28,-19,6],[-6,28,-5,3],[2,28,10,2],[10,28,17,4],[18,30,25,5],[26,34,36,11],[0,24,0,4],[-10,22,-12,6],[8,22,12,6]].forEach((l,i)=>{hdLine(px,HDX+l[0],l[1],HDX+l[2],l[3],i%2?C.sh:C.lt,cap)});   // 뻗친 머리결(안쪽 → 끝)
   hdPaint(px,hdSub(hdEdge(cap,w,h,2,2),hdEdge(cap,w,h,-1,-1)),C.sh);hdPaint(px,hdSub(hdEdge(cap,w,h,-1,-1),hdEdge(cap,w,h,2,2)),C.lt);
   let U=cap;[{c:[[-22,33],[-21,43],[-19,52]],w:[6,4,1]},{c:[[-6,33],[-5,44],[-3,54]],w:[6,4,1]},{c:[[10,32],[12,43],[15,53]],w:[6,4,1]},{c:[[22,33],[24,43],[24,51]],w:[5,3,1]},{c:[[-29,36],[-30,48],[-28,62]],w:[5,4,1]}].forEach(l=>{U=hdOr(U,hdLock(px,l,C,false))});
   U=hdOr(U,hdLock(px,{c:[[29,36],[30,48],[28,62]],w:[5,4,1]},C,false));
   hdLine(px,HDX-14,9,HDX-8,8,C.hi,U);hdLine(px,HDX+10,8,HDX+18,9,C.hi,U);hdFlyaways(px,U,C,9,(x,y)=>y<20||Math.abs(x-HDX)>33);return U}},
 layered_medium:{
  back(px,R){const w=px.w,h=px.h,C=R.hair,M=hdPoly(w,h,hdAbs([[-30,40],[-34,22],[-20,9],[0,5],[20,9],[34,22],[30,40],[38,70],[42,96],[51,110],[41,108],[35,119],[29,106],[21,115],[13,100],[-13,100],[-21,115],[-29,106],[-35,119],[-41,108],[-51,110],[-42,96],[-38,70]]));
   hdPaint(px,M,C.base);hdPaint(px,hdAnd(M,hdPoly(w,h,hdAbs([[-18,86],[18,86],[14,106],[-14,106]]))),C.sh);hdPaint(px,hdAnd(M,hdPoly(w,h,hdAbs([[-12,90],[12,90],[9,104],[-9,104]]))),C.deep);hdStrands(px,M,[-44,-38,-32,32,38,44,-24,24],36,118,1.2,C,1);
   hdPaint(px,hdSub(hdEdge(M,w,h,3,3),hdEdge(M,w,h,-1,-1)),C.sh);hdPaint(px,hdSub(hdEdge(M,w,h,-1,-1),hdEdge(M,w,h,3,3)),C.lt);return M},
  locks(px,R){},
  front(px,R){const w=px.w,h=px.h,C=R.hair,cap=hdPoly(w,h,hdCatmull(hdAbs([[-28,30],[-22,14],[-8,8],[8,8],[22,14],[28,30],[0,22]]),4,true));hdPaint(px,cap,C.base);
   const half=[{c:[[-1,10],[-12,12],[-23,20],[-29,36],[-31,56],[-30,76],[-27,92]],w:[3,10,12,11,9,6,1]},{c:[[-1,14],[-9,20],[-17,30],[-22,44],[-23,58]],w:[3,7,8,6,1]},{c:[[-3,24],[-8,32],[-12,42],[-13,51]],w:[3,4,3,1]}];
   let U=cap;[false,true].forEach(mir=>half.forEach(l=>{U=hdOr(U,hdLock(px,l,C,mir))}));
   hdArc(px,0,26,23,15,200,340,C.lt,U);hdArc(px,0,25,21,13,215,325,C.hi,U);hdFlyaways(px,U,C,5,(x,y)=>y<30||Math.abs(x-HDX)>30);return U}}};
/* ----- 의상: 왼쪽 위 빛 기준 명암 + 접힌 주름 + 칼라/넥타이/핀 ----- */
function hdRegion(px,pts,C,o){o=o||{};const m=hdPoly(px.w,px.h,hdAbs(pts));hdPaint(px,m,C.base);const sh=hdEdge(m,px.w,px.h,o.sd||2,o.sd||2),lt=hdEdge(m,px.w,px.h,-1,-1);if(!o.noSh)hdPaint(px,hdSub(sh,lt),C.sh);if(!o.noLt)hdPaint(px,hdSub(lt,sh),C.lt||C.hi);return m}
const HD_OUTFIT={
 judge_robe(px,R){const w=px.w,h=px.h,RB=R.robe,SH=R.shirt,T=R.tie;
  const neck=hdRegion(px,[[-9,80],[9,80],[10,100],[-10,100]],{base:R.skin.sh,sh:R.skin.deep,lt:R.skin.sh},{sd:2});hdPaint(px,hdAnd(neck,hdEll(w,h,HDX,87,14,6.5)),R.skin.deep);
  const J=hdRegion(px,[[-47,98],[47,98],[54,124],[51,232],[-51,232],[-54,124]],RB,{sd:3});
  hdPaint(px,hdAnd(J,hdPoly(w,h,hdAbs([[-56,98],[56,98],[56,109],[-56,109]]))),RB.lt);hdPaint(px,hdAnd(J,hdPoly(w,h,hdAbs([[-56,98],[56,98],[56,101],[-56,101]]))),RB.hi);
  [-34,-20,20,34].forEach((x,i)=>{hdPolyline(px,hdAbs([[x,150],[x+(x<0?-1:1),190],[x+(x<0?-2:2),232]]),i%2?RB.sh:RB.lt,J)});hdPolyline(px,hdAbs([[-48,130],[-47,180],[-50,232]]),RB.deep,J);hdPolyline(px,hdAbs([[48,130],[47,180],[50,232]]),RB.deep,J);
  hdPaint(px,hdPoly(w,h,hdAbs([[-19,97],[19,97],[9,154],[-9,154]])),R.robeIn);
  const shirt=hdRegion(px,[[-9,97],[9,97],[0,118]],{base:SH.base,sh:SH.sh,lt:SH.hi},{sd:2});hdPaint(px,hdAnd(shirt,hdPoly(w,h,hdAbs([[1,97],[10,97],[1,118]]))),SH.sh);
  [false,true].forEach(m=>{const f=p=>m?p.map(q=>[-q[0],q[1]]):p;const lap=hdRegion(px,f([[-19,95],[-38,100],[-35,156],[-8,126]]),{base:RB.lt,sh:RB.base,lt:RB.hi},{sd:3});hdPolyline(px,hdAbs(f([[-19,95],[-38,100],[-35,156]])),RB.hi,lap);hdPolyline(px,hdAbs(f([[-35,156],[-8,126]])),RB.deep);hdPolyline(px,hdAbs(f([[-30,108],[-29,140]])),RB.sh,lap);
   hdRegion(px,f([[-9,95],[-2,100],[-10,107]]),{base:SH.base,sh:SH.sh,lt:SH.hi},{sd:1})});
  hdRegion(px,[[-3,107],[3,107],[4,113],[-4,113]],{base:T.base,sh:T.sh,lt:T.hi},{sd:1});const tb=hdRegion(px,[[-3,113],[4,113],[7,140],[2,152],[-3,140]],{base:T.base,sh:T.sh,lt:T.hi},{sd:2});hdPolyline(px,hdAbs([[-1.5,115],[-1.5,138]]),T.hi,tb);
  const P=R.pin,bx=HDX-28,by=132;hdPaint(px,hdEll(w,h,bx,by+1,3.8,3.4),P.base);hdPaint(px,hdEll(w,h,bx-2.2,by-4,1.3,3),P.base);hdPaint(px,hdEll(w,h,bx+2.2,by-4,1.3,3),P.base);   // 라펠의 토끼 핀
  px.put(bx-2,by-4,hdMix(P.base,[230,160,170],.5));px.put(bx+2,by-4,hdMix(P.base,[230,160,170],.5));px.put(bx-1,by,R.ol);px.put(bx+1,by,R.ol);px.put(bx-2,by-1,P.hi);px.put(bx-3,by,P.hi);
  return {base:RB.base,lt:RB.lt,sh:RB.sh,w:17}},
 slim_suit(px,R){const w=px.w,h=px.h,S=R.suit,T=R.tie,SH=R.shirt;
  const neck=hdRegion(px,[[-8,80],[8,80],[9,100],[-9,100]],{base:R.skin.sh,sh:R.skin.deep,lt:R.skin.sh},{sd:2});hdPaint(px,hdAnd(neck,hdEll(w,h,HDX,86,13,6)),R.skin.deep);
  const J=hdRegion(px,[[-35,97],[35,97],[39,108],[32,150],[35,232],[-35,232],[-32,150],[-39,108]],S,{sd:3});
  hdPolyline(px,hdAbs([[-30,112],[-28,132],[-31,150]]),S.sh,J);hdPolyline(px,hdAbs([[30,112],[28,132],[31,150]]),S.deep,J);hdPolyline(px,hdAbs([[-27,114],[-25,134]]),S.lt,J);
  hdPaint(px,hdAnd(J,hdPoly(w,h,hdAbs([[-40,97],[40,97],[40,101],[-40,101]]))),S.lt);
  const shirt=hdRegion(px,[[-11,95],[11,95],[0,134]],{base:SH.base,sh:SH.sh,lt:SH.hi},{sd:2});hdPaint(px,hdAnd(shirt,hdPoly(w,h,hdAbs([[1,95],[12,95],[1,134]]))),SH.sh);
  [false,true].forEach(m=>{const f=p=>m?p.map(q=>[-q[0],q[1]]):p;const lap=hdRegion(px,f([[-12,94],[-27,99],[-23,136],[-8,127]]),{base:S.lt,sh:S.base,lt:S.hi},{sd:2});hdPolyline(px,hdAbs(f([[-12,94],[-27,99],[-23,136]])),S.hi,lap);hdPolyline(px,hdAbs(f([[-8,127],[-23,136]])),S.sh);
   hdRegion(px,f([[-12,93],[-4,99],[-13,106],[-16,98]]),{base:SH.base,sh:SH.sh,lt:SH.hi},{sd:1})});
  hdRegion(px,[[-3,100],[3,100],[4,106],[-4,106]],{base:T.base,sh:T.sh,lt:T.hi},{sd:1});const tb=hdRegion(px,[[-3.5,106],[3.5,106],[5,134],[0,142],[-5,134]],{base:T.base,sh:T.sh,lt:T.hi},{sd:2});hdPolyline(px,hdAbs([[-1.5,108],[-2.5,132]]),T.hi,tb);
  const P=R.pin;[[-22,113],[-24,114],[-23,114],[-22,114],[-21,114],[-20,114],[-24,115],[-20,115],[-25,116],[-24,116],[-23,116],[-21,116],[-20,116],[-19,116]].forEach((q,i)=>px.put(HDX+q[0],q[1],i<1?P.hi:P.base));
  [[-1,150],[-1,151],[0,150],[0,151]].forEach((q,i)=>px.put(HDX+q[0],q[1],i===0?S.lt:S.deep));
  return {base:S.base,lt:S.lt,sh:S.sh,w:12}},
 charcoal_suit(px,R){const w=px.w,h=px.h,S=R.suit,T=R.tie,SH=R.shirt;
  const neck=hdRegion(px,[[-8,80],[8,80],[9,100],[-9,100]],{base:R.skin.sh,sh:R.skin.deep,lt:R.skin.sh},{sd:2});hdPaint(px,hdAnd(neck,hdEll(w,h,HDX,86,13,6)),R.skin.deep);
  const legC={base:hdMix(S.base,[10,10,20],.12),sh:S.sh,lt:S.lt};
  [false,true].forEach(m=>{const f=p=>m?p.map(q=>[-q[0],q[1]]):p;const leg=hdRegion(px,f([[-34,186],[-1,186],[-1,232],[-30,232]]),legC,{sd:3});hdPolyline(px,hdAbs(f([[-16,190],[-15,232]])),S.lt,leg);hdPolyline(px,hdAbs(f([[-2,190],[-2,232]])),S.deep,leg)});
  const J=hdRegion(px,[[-39,97],[39,97],[43,110],[40,160],[44,192],[-44,192],[-40,160],[-43,110]],S,{sd:3});
  hdPaint(px,hdAnd(J,hdPoly(w,h,hdAbs([[-45,97],[45,97],[45,101],[-45,101]]))),S.lt);hdPolyline(px,hdAbs([[-34,114],[-33,140],[-36,170]]),S.sh,J);hdPolyline(px,hdAbs([[34,114],[33,140],[36,170]]),S.deep,J);hdPolyline(px,hdAbs([[-31,116],[-30,140]]),S.lt,J);
  hdPaint(px,hdAnd(J,hdPoly(w,h,hdAbs([[-46,188],[46,188],[46,193],[-46,193]]))),S.sh);hdPolyline(px,hdAbs([[-43,192],[43,192]]),S.deep,J);
  const shirt=hdRegion(px,[[-11,95],[11,95],[0,148]],{base:SH.base,sh:SH.sh,lt:SH.hi},{sd:2});hdPaint(px,hdAnd(shirt,hdPoly(w,h,hdAbs([[1,95],[12,95],[1,148]]))),SH.sh);
  [false,true].forEach(m=>{const f=p=>m?p.map(q=>[-q[0],q[1]]):p;const lap=hdRegion(px,f([[-10,94],[-27,100],[-29,138],[-20,152],[-4,134]]),{base:S.lt,sh:S.base,lt:S.hi},{sd:2});hdPolyline(px,hdAbs(f([[-10,94],[-27,100],[-29,138],[-20,152]])),S.hi,lap);hdPolyline(px,hdAbs(f([[-20,152],[-4,134]])),S.sh);hdPolyline(px,hdAbs(f([[-27,100],[-21,108],[-10,106]])),S.deep);
   hdRegion(px,f([[-11,93],[-3,99],[-12,107],[-15,98]]),{base:SH.base,sh:SH.sh,lt:SH.hi},{sd:1})});
  hdRegion(px,[[-2.5,100],[2.5,100],[3.5,106],[-3.5,106]],{base:T.base,sh:T.sh,lt:T.hi},{sd:1});const tb=hdRegion(px,[[-3,106],[3,106],[4.5,140],[0,148],[-4.5,140]],{base:T.base,sh:T.sh,lt:T.hi},{sd:2});hdPolyline(px,hdAbs([[-1.2,108],[-2,138]]),T.hi,tb);
  hdPolyline(px,hdAbs([[0,152],[0,190]]),S.deep,J);[[-1,160],[0,160],[-1,161],[0,161]].forEach((q,i)=>px.put(HDX+q[0],q[1],i===0?S.hi:S.deep));[[-1,174],[0,174],[-1,175],[0,175]].forEach((q,i)=>px.put(HDX+q[0],q[1],i===0?S.hi:S.deep));
  return {base:S.base,lt:S.lt,sh:S.sh,w:14}}};
/* ----- 팔: 어깨→팔꿈치→손을 픽셀 도화지에 직접 칠한다 (소매 명암 · 셔츠 커프스 · 손) ----- */
function hdSeg(px,a,b,w){const dx=b[0]-a[0],dy=b[1]-a[1],l=Math.hypot(dx,dy)||1,nx=-dy/l*w/2,ny=dx/l*w/2;return hdPoly(px.w,px.h,[[a[0]+nx,a[1]+ny],[b[0]+nx,b[1]+ny],[b[0]-nx,b[1]-ny],[a[0]-nx,a[1]-ny]])}
function hdPaintArm(px,S,E,Hh,sl,R){const w=px.w,h=px.h,wU=sl.w,wF=sl.w-1.5;let m=hdOr(hdSeg(px,S,E,wU),hdEll(w,h,E[0],E[1],wU/2,wU/2));m=hdOr(m,hdSeg(px,E,Hh,wF));hdPaint(px,m,sl.base);
 const sh=hdEdge(m,w,h,2,2),lt=hdEdge(m,w,h,-1,-1);hdPaint(px,hdSub(sh,lt),sl.sh);hdPaint(px,hdSub(lt,sh),sl.lt);
 const c0=[E[0]+(Hh[0]-E[0])*0.72,E[1]+(Hh[1]-E[1])*0.72],c1=[E[0]+(Hh[0]-E[0])*0.9,E[1]+(Hh[1]-E[1])*0.9],cf=hdSeg(px,c0,c1,wF+1);hdPaint(px,cf,R.shirt.base);hdPaint(px,hdAnd(cf,hdEdge(cf,w,h,2,2)),R.shirt.sh);
 const hc=[Hh[0]+(Hh[0]-E[0])*0.06,Hh[1]+(Hh[1]-E[1])*0.06],hm=hdEll(w,h,hc[0],hc[1],4.4,4.8);hdPaint(px,hm,R.skin.base);hdPaint(px,hdSub(hdEdge(hm,w,h,2,2),hdEdge(hm,w,h,-1,-1)),R.skin.sh);hdPaint(px,hdAnd(hm,hdEll(w,h,hc[0]-1.4,hc[1]-1.8,1.5,1.2)),R.skin.hi)}
/* ----- 캐릭터 조립: 레이어(뒤머리·몸·얼굴·앞머리)를 한 번만 칠해 두고, 표정(눈·눈썹·입)만 상태에 따라 바꿔 합성한다 ----- */
/* ----- 표정 효과(볼터치·땀·눈물·분노 마크): 얼굴 위에 한 번 칠해 두고 표정이 바뀔 때만 꺼내 쓴다 ----- */
function hdPaintFx(px,R,st,n){const yt=st.eye_top,yb=yt+st.eye_h,sk=R.skin,WT=[236,246,255],BL=[150,205,250],B2=[104,168,228];
 if(n==='blush')[-1,1].forEach(s=>{const cx=HDX+s*19,cy=yb+5,c=hdMix(sk.base,[244,110,128],.55);for(let k=0;k<3;k++)for(let j=0;j<3;j++)px.put(cx-4+k*3+j,cy+2-j,c)});
 if(n==='tears')[-1,1].forEach(s=>{const x=HDX+s*17;for(let dx=-5;dx<=5;dx++)px.put(HDX+s*14+dx,yb-1,[190,226,255]);for(let y=yb;y<yb+10;y++){px.put(x,y,BL);px.put(x+s,y,y%3===0?WT:[190,226,255])}px.put(x,yb+2,WT);px.put(x-s,yb+10,B2);px.put(x,yb+10,BL);px.put(x,yb+11,B2);px.put(x-s,yb+11,BL)});
 if(n==='sweat'){const x=HDX+28,y=yt-6;px.put(x,y,B2);[[x-1,y+1],[x,y+1],[x+1,y+1],[x-1,y+2],[x,y+2],[x+1,y+2],[x-1,y+3],[x,y+3],[x+1,y+3],[x,y+4]].forEach(q=>px.put(q[0],q[1],BL));px.put(x-1,y+2,WT);px.put(x,y+4,B2)}
 if(n==='vein'){const x=HDX-24,y=yt-13,c=[214,48,60],d=hdMix(c,R.ol,.4);[[0,0],[1,0],[2,0],[0,1],[0,2],[1,1],[3,1],[4,1],[4,2],[3,2],[3,3],[1,3],[2,4],[3,4],[4,4]].forEach(q=>px.put(x+q[0],y+q[1],q[0]+q[1]===2?d:c))}}
function hdBuildFigure(key){const C=D.cast[key],pal=C.palette,st=C.style,R=hdRamps(pal),W=HDW,H=HDH,hair=HD_HAIR[st.hair],suit=HD_OUTFIT[st.outfit];
 const back=new HdPx(W,H),torso=new HdPx(W,H),hairF=new HdPx(W,H),face=new HdPx(W,H);
 hair.back(back,R);hdOutline(back,R.ol,0.7);const sl=suit(torso,R);hair.locks(torso,R);hdOutline(torso,R.ol,0.7);hair.front(hairF,R);hdOutline(hairF,R.ol,0.75);
 const hm=new Uint8Array(W*H);for(let i=0;i<hm.length;i++)hm[i]=hairF.d[i*4+3]?1:0;hdPaintFace(face,R,st,hm);
 const cv={back:back.canvas(),torso:torso.canvas(),face:face.canvas(),hairF:hairF.canvas()},rs=C.render||{},hl=rs.eye_highlight_px||2,cfgEye=HD_EYE[st.eyes],brow=hdPaintBrows(R,st),md=HD_MOUTH[st.mouth],mouths={};
 ['grin','smile','open','flat','hmm'].forEach(n=>{const p=new HdPx(W,H);md[n](p,R);mouths[n]=p.canvas()});
 const eyeCache={},eyeAt=(side,rows,gx,gy)=>{const k=side+'|'+rows+'|'+gx+'|'+gy;return eyeCache[k]||(eyeCache[k]=hdEyeSprite(R,st,cfgEye,side,rows,gx,gy,hl))};
 const headC=document.createElement('canvas');headC.width=W;headC.height=H;const hx=headC.getContext('2d');hx.imageSmoothingEnabled=false;
 const F={key:key,pal:pal,style:st,R:R,sleeve:{base:sl.base,lt:sl.lt,sh:sl.sh,w:sl.w},state:{lid:0,gx:0,gy:0,brow:0,mouth:md.def,baseMouth:md.def,fx:''},defaultMouth:md.def};
 const fxc={},fxCanvas=k=>fxc[k]||(fxc[k]=(()=>{const p=new HdPx(W,H);k.split(',').forEach(n=>n&&hdPaintFx(p,R,st,n));return p.canvas()})());
 F.setLid=v=>{F.state.lid=v};F.setGaze=(a,b)=>{F.state.gx=a;F.state.gy=b};F.setBrow=d=>{F.state.brow=d};F.showMouth=n=>{F.state.mouth=n};
 let headKey='';
 F.composeHead=function(){const s=F.state;
  const rows=Math.max(0,Math.round(st.lid_min+Math.max(0,Math.min(1,s.lid))*(st.eye_h+1-st.lid_min))),gx=Math.max(-2,Math.min(2,Math.round(s.gx*0.5))),gy=Math.max(-1,Math.min(1,Math.round(s.gy*0.4))),key=rows+'|'+gx+'|'+gy+'|'+Math.round(s.brow)+'|'+s.mouth+'|'+s.fx;if(key===headKey)return;headKey=key;hx.clearRect(0,0,W,H);hx.drawImage(cv.face,0,0);
  [-1,1].forEach(side=>{const e=eyeAt(side,rows,gx,gy);hx.drawImage(e.c,e.ox,e.oy)});
  hx.drawImage(brow.c,brow.ox,brow.oy+Math.round(s.brow));if(mouths[s.mouth])hx.drawImage(mouths[s.mouth],0,0);if(s.fx)hx.drawImage(fxCanvas(s.fx),0,0);hx.drawImage(cv.hairF,0,0)};
 /* 표정 적용: characters.py 의 EXPRESSIONS 표(D.expr)에 적힌 값(입·눈썹·눈꺼풀·시선·효과)을 한 번에 바꾼다 */
 F.setExpr=function(name){const E=(D.expr||{})[name]||(D.expr||{}).neutral||{},S=F.state;S.baseMouth=(E.mouth&&mouths[E.mouth])?E.mouth:md.def;S.mouth=S.baseMouth;S.brow=E.brow||0;S.lid=E.lid||0;S.gx=E.gx||0;S.gy=E.gy||0;S.fx=(E.fx||[]).join(',');F.expr=name};
 F.render=function(ctx,o){o=o||{};ctx.imageSmoothingEnabled=false;const cx=o.cx||0,cy=o.cy||0,ty=Math.round(o.ty||0),lean=Math.round(o.lean||0),tilt=o.tilt||0;
  ctx.drawImage(cv.back,-cx,ty-cy);ctx.drawImage(cv.torso,-cx,ty-cy);F.composeHead();
  if(Math.abs(tilt)<0.6)ctx.drawImage(headC,-cx,ty+lean-cy);else{const t=Math.tan(tilt*Math.PI/180);for(let y=0;y<104;y++)ctx.drawImage(headC,0,y,W,1,-cx+Math.round((96-y)*t),ty+lean+y-cy,W,1);ctx.drawImage(headC,0,104,W,H-104,-cx,ty+lean+104-cy,W,H-104)}
  if(o.arms){const cw=o.cw||W,ch=o.ch||H;F._arc=F._arc||{};
   ['L','R'].forEach(k=>{const a=o.arms[k];if(!a)return;const pts=[a.S,a.E,a.H].map(q=>[q[0]-cx,q[1]-cy]),xs=pts.map(q=>q[0]),ys=pts.map(q=>q[1]),
    x0=Math.max(0,Math.floor(Math.min.apply(null,xs))-12),y0=Math.max(0,Math.floor(Math.min.apply(null,ys))-12),x1=Math.min(cw,Math.ceil(Math.max.apply(null,xs))+12),y1=Math.min(ch,Math.ceil(Math.max.apply(null,ys))+12),bw=x1-x0,bh=y1-y0;if(bw<=0||bh<=0)return;
    const px=new HdPx(bw,bh),q=pts.map(p=>[p[0]-x0,p[1]-y0]);hdPaintArm(px,q[0],q[1],q[2],F.sleeve,R);hdOutline(px,R.ol,0.7);
    const c=F._arc[k]||(F._arc[k]=document.createElement('canvas'));if(c.width<bw||c.height<bh){c.width=Math.max(c.width,bw);c.height=Math.max(c.height,bh)}
    const cx2=c.getContext('2d');cx2.clearRect(0,0,c.width,c.height);cx2.putImageData(new ImageData(px.d,bw,bh),0,0);ctx.drawImage(c,0,0,bw,bh,x0,y0,bw,bh)})}};
 return F}
/* 재판/스토리용 반신상: 134×200 픽셀 도화지에 그리고, 말하는 동안 입을 여닫는다 */
/* ----- 2배 해상도 보정(2.5D): 그림을 2배로 키운 뒤 '반 칸 단위'로 입체 음영(디더) · 윤곽 안쪽 림라이트 · 얇은 윤곽선을 더한다 ----- */
const HD_BAYER=[0,8,2,10,12,4,14,6,3,11,1,9,15,7,13,5];
function hdEnhance(src,dst){const w=src.width,h=src.height,sd=src.getContext('2d').getImageData(0,0,w,h).data,W2=w*2,H2=h*2,dx=dst.getContext('2d'),out=dx.createImageData(W2,H2),o=out.data;
 const al=(x,y)=>(x<0||y<0||x>=w||y>=h)?0:sd[(y*w+x)*4+3],px=(x,y,c)=>sd[(y*w+x)*4+c];
 for(let y=0;y<H2;y++){const sy=y>>1;for(let x=0;x<W2;x++){const sx=x>>1,i=(sy*w+sx)*4,a=sd[i+3];if(!a)continue;let r=sd[i],g=sd[i+1],b=sd[i+2];
  const q=(y*W2+x)*4,fx=x&1,fy=y&1,bay=HD_BAYER[(y&3)*4+(x&3)]/16;
  const eL=al(sx-1,sy)===0,eR=al(sx+1,sy)===0,eT=al(sx,sy-1)===0,eB=al(sx,sy+1)===0,edge=eL||eR||eT||eB;
  if(edge&&r+g+b<170){let nx=sx,ny=sy;if(eL&&fx===1)nx=sx+1;else if(eR&&fx===0)nx=sx-1;else if(eT&&fy===1)ny=sy+1;else if(eB&&fy===0)ny=sy-1;
   if((nx!==sx||ny!==sy)&&al(nx,ny)){r=px(nx,ny,0);g=px(nx,ny,1);b=px(nx,ny,2)}}
  else if(!edge){const sh=(x/W2-.46)*.75+(y/H2-.5)*.9;
   if(sh>0){if(sh*1.35>bay){r*=.8;g*=.8;b*=.84}}else if(-sh*1.1>bay){r=Math.min(255,r*1.13+6);g=Math.min(255,g*1.13+6);b=Math.min(255,b*1.09+6)}
   if((al(sx-2,sy)===0||al(sx,sy-2)===0)&&fx+fy===0){r=Math.min(255,r+44);g=Math.min(255,g+40);b=Math.min(255,b+34)}
   else if((al(sx+2,sy)===0||al(sx,sy+2)===0)&&fx+fy===2){r*=.72;g*=.72;b*=.78}}
  o[q]=r;o[q+1]=g;o[q+2]=b;o[q+3]=a}}
 dx.putImageData(out,0,0)}
function hdBust(el,key){const F=hdBuildFigure(key),cvs=document.createElement('canvas');cvs.width=268;cvs.height=400;cvs.className='hdc';el.appendChild(cvs);const ctx=cvs.getContext('2d');
 const tmp=document.createElement('canvas');tmp.width=134;tmp.height=200;const tctx=tmp.getContext('2d',{willReadFrequently:true});
 const draw=()=>{tctx.clearRect(0,0,134,200);F.render(tctx,{cx:33,cy:3});hdEnhance(tmp,cvs)};draw();let tm=null;
 F.setTalking=on=>{if(on&&!tm){let o=false;tm=setInterval(()=>{o=!o;F.state.mouth=o?'open':(F.state.baseMouth||F.defaultMouth);draw()},220)}else if(!on&&tm){clearInterval(tm);tm=null;F.state.mouth=F.state.baseMouth||F.defaultMouth;draw()}};F.redraw=draw;return F}

/* ----- 대기 장면: 판사석 의자 등받이(가죽 + 금 단추 + 접힌 무늬)를 픽셀로 칠한 배경 ----- */
function hdChairLayer(){const px=new HdPx(HDW,160),w=px.w,h=px.h,br=[90,58,34],br2=[112,72,42],gold=[222,188,92],deep=hdMix(br,[10,6,4],.55),gs=hdMix(gold,[70,44,10],.5),gh=hdMix(gold,HD_WHITE,.55);
 hdRegion(px,[[-52,10],[52,10],[52,17],[-52,17]],{base:gold,sh:gs,lt:gh},{sd:1});
 hdRegion(px,[[-50,17],[50,17],[50,146],[-50,146]],{base:br,sh:deep,lt:br2},{sd:3});
 const cu=hdRegion(px,[[-42,24],[42,24],[42,138],[-42,138]],{base:br2,sh:hdMix(br2,[20,10,6],.42),lt:hdMix(br2,HD_WHITE,.14)},{sd:2});
 for(let r=0;r<4;r++)for(let c=0;c<5;c++){const x=-32+c*16,y=34+r*26,dl=hdMix(br2,deep,.4);if(c<4&&r<3){hdLine(px,HDX+x,y,HDX+x+8,y+13,dl,cu);hdLine(px,HDX+x+16,y,HDX+x+8,y+13,dl,cu);hdLine(px,HDX+x+8,y+13,HDX+x,y+26,dl,cu);hdLine(px,HDX+x+8,y+13,HDX+x+16,y+26,dl,cu)}}
 for(let r=0;r<4;r++)for(let c=0;c<5;c++){const x=HDX-32+c*16,y=34+r*26;px.put(x,y,gold);px.put(x+1,y,gold);px.put(x,y+1,gs);px.put(x+1,y+1,gs);px.put(x-1,y-1,gh)}
 hdLine(px,HDX-36,26,HDX-24,60,hdMix(br2,HD_WHITE,.2),cu);hdLine(px,HDX-34,26,HDX-22,60,hdMix(br2,HD_WHITE,.1),cu);
 hdOutline(px,[22,12,6],0.75);return px.canvas()}
"""

# 공용 스프라이트 코드를 각 연출 템플릿의 표시 자리에 끼워 넣는다 (SPRITES_JS 정의 이후에 실행되어야 함)
VN_TEMPLATE = (VN_TEMPLATE.replace("/*__SPRITES__*/", SPRITES_JS + "\n" + STAGE_JS).replace("/*__STAGE_CSS__*/", STAGE_CSS)
               .replace("<!--__WAIT__-->", WAIT_HTML).replace("<!--__SCENE__-->", SCENE_HTML).replace("<!--__OVERLAYS__-->", OVERLAYS))
STORY_TEMPLATE = STORY_TEMPLATE.replace("/*__SPRITES__*/", SPRITES_JS)
LOBBY_TEMPLATE = LOBBY_TEMPLATE.replace("/*__SPRITES__*/", SPRITES_JS)
