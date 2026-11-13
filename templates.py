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

from characters import sprite_payload


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
#jchara{display:block}
#w-bubble{position:absolute;left:58%;bottom:100%;margin-bottom:14px;background:#fff;color:#0d0f26;font-size:clamp(13px,2.4vh,17px);font-weight:700;padding:8px 14px;opacity:0;transform:translateY(6px);transition:opacity .4s,transform .4s;white-space:nowrap;box-shadow:0 -3px 0 #0d0f26,0 3px 0 #0d0f26,-3px 0 0 #0d0f26,3px 0 0 #0d0f26,4px 8px 0 0 #0006}
#w-bubble.on{opacity:1;transform:none}
#w-bubble:after{content:"";position:absolute;left:16px;bottom:-12px;border:6px solid transparent;border-top:8px solid #0d0f26}
#w-bench{position:absolute;left:0;right:0;bottom:0;background:#5a3a22;border-top:6px solid #8a5a34;box-shadow:inset 0 6px 0 #d9b85a55}
#w-vig{position:absolute;inset:0;pointer-events:none;background:repeating-linear-gradient(#0000 0 2px,#0001 2px 3px);box-shadow:inset 0 0 120px #000a}
</style></head><body>
<div id="wait"><div class="w-wall"></div><div class="w-wain"></div><div class="w-shelf l"></div><div class="w-shelf r"></div><div class="w-seal">法</div><div class="w-lamp"></div><div id="w-dust"></div>
 <div id="w-cw"><svg id="jchara" viewBox="0 0 200 160" shape-rendering="crispEdges"></svg><div id="w-bubble"></div></div>
 <div id="w-bench"></div><div id="w-vig"></div></div>
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
 /* 의자 등받이 */
 const gChair=E('g');R(gChair,-52,10,104,8,GOLD,OUT);R(gChair,-50,16,100,130,'#5a3a22',OUT);R(gChair,-42,24,84,114,'#6b4528');
 for(let r=0;r<4;r++)for(let c=0;c<5;c++)R(gChair,-32+c*16,34+r*26,4,4,GOLD);
 /* 판사 서판결: 머리·표정·법복은 characters.py 데이터(palette/style)대로 그린다 */
 const F=buildFigure(svg,'JUDGE'),pal=F.pal,SLV=F.sleeve,st=F.style;
 const gArmL=E('g'),gArmR=E('g'),gPL=E('g'),gPR=E('g'),gDesk=E('g'),gTool=E('g');
 /* 팔: 어깨→팔꿈치→손 (역기구학으로 각도 계산). 소매 색·폭은 의상 데이터를 따른다 */
 const SL=[CX-st.shoulder_dx,st.shoulder_y],SR=[CX+st.shoulder_dx,st.shoulder_y],L1=26,L2=27.5;
 function arm(gr,S){const w=SLV.w,w2=w-2;const up=E('g',{},gr);A(up,S[0]-w/2,104,w,28,SLV.color,OUT);A(up,S[0]-w/2,104,w,5,pal.robe_light||pal.suit_light||SLV.color);const fo=E('g',{},up);A(fo,S[0]-w2/2,130,w2,26,SLV.color,OUT);A(fo,S[0]-w2/2-1,150,w2+2,4,SLV.cuff,OUT);A(fo,S[0]-5,154,10,11,pal.skin,OUT);return {up:up,fo:fo}}
 const armL=arm(gArmL,SL),armR=arm(gArmR,SR);
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
  let t1=rotOf(c.a),t2=rotOf(fa)-t1;while(t2>180)t2-=360;while(t2<-180)t2+=360;return {t1:t1,t2:t2,hx:hx,hy:hy}}
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
  armL.up.setAttribute('transform','rotate('+a.t1.toFixed(2)+' '+SL[0]+' 106)');armL.fo.setAttribute('transform','rotate('+a.t2.toFixed(2)+' '+SL[0]+' 132)');
  armR.up.setAttribute('transform','rotate('+b.t1.toFixed(2)+' '+SR[0]+' 106)');armR.fo.setAttribute('transform','rotate('+b.t2.toFixed(2)+' '+SR[0]+' 132)');
  const bob=Math.sin(t*1.6)*0.6;
  F.head.setAttribute('transform','translate(0 '+(bob+cur.lean).toFixed(2)+') rotate('+(cur.tilt+tiltAdd).toFixed(2)+' '+CX+' 88)');
  F.torso.setAttribute('transform','translate(0 '+(Math.sin(t*1.6)*0.5).toFixed(2)+')');
  F.setBrow(cur.brow);F.setGaze(cur.gx,cur.gy);F.setLid(Math.max(cur.lid,((t%3.9)<0.12)?1:0));F.showMouth(p.mouth);
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
 function say(s,ms){const b=g('w-bubble');if(!s){b.className='';return}b.textContent=s;b.className='on';bubbleOff=t+(ms||2600)/1000}
 function nextStep(){if(prev==='flip')newPage();const e=PLAN[kind][idx%PLAN[kind].length];idx++;step=e[0];prev=e[0];tgt=P[e[0]];stepEnd=t+e[1]/1000;
  const lines=(e[0]==='ponder')?(W.ponder&&W.ponder[kind]):W[e[0]];if(lines&&lines.length&&Math.random()<0.8)say(rnd(lines),Math.min(e[1]-300,3200))}
 function tick(dtMs){const dt=Math.min(dtMs,64)/1000;t+=dt;if(!step||t>=stepEnd)nextStep();if(bubbleOff&&t>bubbleOff){say(null);bubbleOff=0}render(dt)}
 /* 크기 맞춤 + 먼지 입자 */
 function fit(){const de=document.documentElement,Wd=de.clientWidth||800,H=de.clientHeight||600;let h=H*0.82,w=h*1.25;if(w>Wd*1.05){w=Wd*1.05;h=w/1.25}
  svg.style.width=w+'px';svg.style.height=h+'px';g('w-bench').style.height=(h*26/160)+'px'}
 window.addEventListener('resize',fit);fit();
 (function(){const d=g('w-dust');for(let i=0;i<18;i++){const e=document.createElement('div');e.className='dust';e.style.left=(Math.random()*96)+'%';e.style.top=(30+Math.random()*60)+'%';e.style.setProperty('--d',(9+Math.random()*8)+'s');e.style.setProperty('--l',(-Math.random()*12)+'s');d.appendChild(e)}})();
 window.__wait={tick:tick,pose:function(n){tgt=P[n];step=n;stepEnd=1e9;idx=0},poses:Object.keys(P),fig:F};
 let last=0;function loop(ts){if(last)tick(ts-last);last=ts;requestAnimationFrame(loop)}requestAnimationFrame(loop);
})();}
</script>
<script>
const $=id=>document.getElementById(id);
const scene=$('scene');
const NAMES={J:D.cast.JUDGE.display,P:D.cast.PROSECUTOR.display,L:D.cast.LAWYER.display};
const CAM={JUDGE:'J',PROSECUTOR:'P',LAWYER:'L'};
const TX={J:'-33.3334%',P:'0%',L:'-66.6667%'};
buildBust($('svgJ'),'JUDGE');
buildBust($('svgP'),'PROSECUTOR');
buildBust($('svgL'),'LAWYER');

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
 if(i===last()&&!ended){if(D.mode==='verdict'){ended=true;setTimeout(gavel,900)}else{$('hint').textContent=D.hint||'';$('hint').style.display='block';exOpen()}}}
function type(text){typing=true;full=text;let k=0;$('txt').textContent='';timer=setInterval(()=>{k++;$('txt').textContent=text.slice(0,k);$('boxin').scrollTop=$('boxin').scrollHeight;if(k%2===0)beep(480+Math.random()*140,.04);if(k>=text.length)stopType()},D.speed||32)}
const SHOUT={F:D.cast.PROSECUTOR.shout.text,S:D.cast.LAWYER.shout.text,O:D.cast.JUDGE.shout.text};
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
    payload = json.dumps({"mode": mode, "steps": steps, "card": card or {}, "title": title, "phase": phase, "hint": hint, "mute": mute, "speed": speed, "cast": sprite_payload()}, ensure_ascii=False)
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
#chara{display:block}
#bubble{position:absolute;left:56%;bottom:100%;margin-bottom:12px;max-width:230px;background:#fff;color:var(--ink);font-size:14px;font-weight:700;padding:8px 12px;opacity:0;transition:opacity .3s,transform .3s;transform:translateY(6px);box-shadow:0 -3px 0 var(--ink),0 3px 0 var(--ink),-3px 0 0 var(--ink),3px 0 0 var(--ink),4px 8px 0 0 #0006;white-space:nowrap}
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
 <div id="cw"><svg id="chara" viewBox="0 0 200 160" shape-rendering="crispEdges"></svg><div id="bubble"></div></div>
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
const F=buildFigure($('chara'),'LAWYER'),gHead=F.head,gTorso=F.torso;
const gArmL=E('g'),gArmR=E('g'),gDesk=E('g'),gMugDesk=E('g'),gMugHand=E('g');
// 팔(어깨→팔꿈치→손). 소매 색·폭은 의상 데이터(F.sleeve)를 따른다. 관절 회전은 transform 속성으로 직접 제어
function arm(g,S){const w=F.sleeve.w-1,w2=w-1;const up=E('g',{},g);A(up,S[0]-w/2,100,w,24,F.sleeve.color,OUT);A(up,S[0]-w/2,100,w,5,F.pal.suit_light||F.sleeve.color);
 const fo=E('g',{},up);A(fo,S[0]-w2/2,122,w2,24,F.sleeve.color,OUT);A(fo,S[0]-w2/2,138,w2,3,F.sleeve.cuff);A(fo,S[0]-5,143,10,9,F.pal.skin,OUT);return {up:up,fo:fo}}
const armL=arm(gArmL,SL),armR=arm(gArmR,SR);
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
 let t1=rotOf(c.a),t2=rotOf(fa)-t1;while(t2>180)t2-=360;while(t2<-180)t2+=360;return {t1:t1,t2:t2,hx:hx,hy:hy}}

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
 armL.up.setAttribute('transform','rotate('+a.t1.toFixed(2)+' '+SL[0]+' 100)');armL.fo.setAttribute('transform','rotate('+a.t2.toFixed(2)+' '+SL[0]+' 124)');
 armR.up.setAttribute('transform','rotate('+b.t1.toFixed(2)+' '+SR[0]+' 100)');armR.fo.setAttribute('transform','rotate('+b.t2.toFixed(2)+' '+SR[0]+' 124)');
 // 머리: 호흡 + 타이핑 끄덕임 + 기울기
 const bob=Math.sin(t*2)*0.6+(tgt===P.work?Math.sin(t*9)*0.5:0);
 gHead.setAttribute('transform','translate(0 '+bob.toFixed(2)+') rotate('+cur.tilt.toFixed(2)+' '+CX+' 84)');
 gTorso.setAttribute('transform','translate(0 '+(Math.sin(t*2)*0.5).toFixed(2)+')');
 // 눈: 시선 + 깜빡임
 const blink=((t%4.2)<0.13)?1:0,lid=Math.max(cur.lid,blink);
 F.setGaze(cur.gx,cur.gy);F.setLid(lid);
 // 입
 F.showMouth(p.mouth);
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
function say(s,ms){const b=$('bubble');if(!s){b.classList.remove('on');return}b.textContent=s;b.classList.add('on');bubbleOff=t+(ms||2600)/1000}
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
SPRITES_JS = r"""/* ============ 캐릭터 스프라이트 라이브러리 ============
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
 charcoal_vest(F,pal,OL,TH){const g=F.torso;
  spP(g,[[-8,78],[8,78],[9,98],[-9,98]],pal.skin_shadow);
  spP(g,[[-39,96],[39,96],[43,110],[37,232],[-37,232],[-43,110]],pal.suit,OL);
  spP(g,[[-39,96],[39,96],[41,104],[-41,104]],pal.suit_light,{opacity:.8});
  spP(g,[[-19,95],[19,95],[17,152],[0,164],[-17,152]],pal.vest,TH);
  for(let i=-3;i<=3;i++)spR(g,i*5-0.5,112,1,42,pal.vest_shadow,{opacity:.7});
  spP(g,[[-9,95],[9,95],[0,124]],pal.shirt,TH);
  spBoth(g,[[-19,95],[-31,100],[-27,152],[-17,142]],pal.suit_light,OL);
  spBoth(g,[[-10,93],[-3,98],[-11,106]],pal.shirt,TH);
  spP(g,[[-2.5,99],[2.5,99],[3.5,105],[-3.5,105]],pal.tie);spP(g,[[-3,105],[3,105],[4,138],[0,144],[-4,138]],pal.tie);
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
 const F={key:key,pal:pal,style:st,root:spEl('g',{},parent)};
 F.defs=spEl('defs',{},F.root);F.back=spEl('g',{},F.root);F.torso=spEl('g',{},F.root);F.head=spEl('g',{},F.root);
 const hair=SP_HAIR[st.hair];hair.back(F,pal);SP_OUTFIT[st.outfit](F,pal,OL,TH);hair.locks(F,pal);
 const h=F.head;
 spP(h,[[-29,48],[-33,52],[-33,60],[-29,62]],pal.skin,OL);spP(h,[[29,48],[33,52],[33,60],[29,62]],pal.skin,OL);
 spP(h,[[-28,30],[28,30],[29,62],[24,74],[14,83],[-14,83],[-24,74],[-29,62]],pal.skin,OL);
 spP(h,[[-24,74],[24,74],[14,83],[-14,83]],pal.skin_shadow,{opacity:.55});
 spR(h,-24,64,8,4,pal.blush,{opacity:.75});spR(h,16,64,8,4,pal.blush,{opacity:.75});spR(h,-1.5,63,3,3,pal.skin_shadow);
 const cfg=SP_EYE[st.eyes],hl=(C.render&&C.render.eye_highlight_px)||2;
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
function buildBust(el,key){const svg=spEl('svg',{viewBox:'0 0 100 150','shape-rendering':'crispEdges'});el.appendChild(svg);
 const F=buildFigure(spEl('g',{transform:'translate(-25 -2) scale(.75)'},svg),key);F.mouths[F.defaultMouth].setAttribute('class','mouth');return F}
"""

# 공용 스프라이트 코드를 각 연출 템플릿의 표시 자리에 끼워 넣는다 (SPRITES_JS 정의 이후에 실행되어야 함)
VN_TEMPLATE = VN_TEMPLATE.replace("/*__SPRITES__*/", SPRITES_JS)
STORY_TEMPLATE = STORY_TEMPLATE.replace("/*__SPRITES__*/", SPRITES_JS)
LOBBY_TEMPLATE = LOBBY_TEMPLATE.replace("/*__SPRITES__*/", SPRITES_JS)
