"""config.py — 설정값 모음: 전역 CSS, LLM 호출 설정, 선임비/평판/랭크 정책, 화면 문구.

이 파일은 다른 모듈에 의존하지 않습니다. 숫자나 문구만 바꾸고 싶을 때는 여기를 수정하세요.
"""

# =================================================================
# 앱 기본 설정
# =================================================================

PAGE_TITLE = "이불킥 법정"
PAGE_ICON = "🏛️"
PAGE_LAYOUT = "wide"  # 가로 화면: 넓은 레이아웃

# =================================================================
# 전역 CSS (도트/픽셀 아케이드 스타일)
# =================================================================

APP_CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Jua&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
@import url('https://cdn.jsdelivr.net/npm/galmuri@latest/dist/galmuri.css');
.stApp, .stApp p, .stApp label, .stApp button, .stApp textarea, .stApp input, .stApp h1, .stApp h2, .stApp h3, .stApp small, .stApp span.st-emotion-cache-0
{ font-family:'Galmuri11','Jua','Apple SD Gothic Neo','Malgun Gothic',sans-serif; }
.stApp{ background:#05070f; color:#eef2ff; }
header[data-testid="stHeader"], footer{ display:none; }
.block-container, [data-testid="stMainBlockContainer"]{ max-width:1120px !important; margin:0 auto; padding:1rem 1.6rem 6rem !important; background:#0a0d18; box-shadow:0 0 0 3px #1b2350, 0 0 60px #000; min-height:100vh; }
html, body{ overflow-x:hidden; }
[data-testid="stBottom"] > div, [data-testid="stBottomBlockContainer"]{ max-width:1120px !important; margin:0 auto; }
div[role="dialog"]{ max-width:560px !important; }
[data-testid="stToolbar"]{ display:none; }
iframe{ border:4px solid #2a2f57; box-shadow:6px 6px 0 #000; background:#000; }

/* ---------- 버튼 (메뉴 스타일) ---------- */
.stButton>button{ height:48px; background:linear-gradient(#2f4380,#16203f); border:3px solid #c9b26b; border-radius:0;
  letter-spacing:4px; font-weight:700; box-shadow:none;
  clip-path:polygon(10px 0,100% 0,100% calc(100% - 10px),calc(100% - 10px) 100%,0 100%,0 10px); transition:.12s; }
.stButton>button, .stButton>button *{ color:#f7e9b0 !important; }
.stButton>button:hover{ filter:brightness(1.35); border-color:#fff; }
.stButton>button:hover, .stButton>button:hover *{ color:#fff !important; }

/* ---------- 타이틀 ---------- */
.ts{ position:relative; height:520px; overflow:hidden; }
.ts-wall{ position:absolute; inset:0; background:linear-gradient(#f1e5b7,#d9c78d); }
.ts-pil{ position:absolute; top:0; bottom:30%; width:11%; border-left:3px solid #8f7a46; border-right:3px solid #8f7a46;
  background:linear-gradient(90deg,#c9b27a,#f3e7bd 45%,#b59c61); }
.ts-pil.l{ left:5%; } .ts-pil.r{ right:5%; }
.ts-seal{ position:absolute; left:26%; top:5%; transform:translateX(-50%); width:78px; height:78px; border-radius:50%;
  background:radial-gradient(#fff,#cfd6e6); border:5px solid #c9a24d; box-shadow:0 0 0 4px #7a5a1e;
  display:flex; align-items:center; justify-content:center; font-size:38px; }
.ts-bench{ position:absolute; left:22%; right:22%; bottom:24%; height:26%; border:5px solid #4f2a12;
  background:linear-gradient(#b06a33 0 14%,#7d4521 14%); }
.ts-floor{ position:absolute; left:0; right:0; bottom:0; height:30%; border-top:5px solid #6b4423;
  background:repeating-conic-gradient(#d7e9de 0 25%,#aecbbb 0 50%) 0 0/54px 54px; }
.ts-logo{ position:absolute; left:0; right:44%; top:25%; text-align:center; }
.ts-logo small{ display:inline-block; background:#1a1f4a; color:#9fe8ff; padding:3px 12px; letter-spacing:3px; border:2px solid #9fe8ff; }
.ts-logo h1{ font-size:clamp(44px,12vw,76px); line-height:1.05; color:#fff; margin:8px 0 4px; letter-spacing:4px; padding:0;
  -webkit-text-stroke:3px #1a1f4a; text-shadow:5px 5px 0 #c1121f,8px 8px 0 #000; }
.ts-logo em{ font-style:normal; color:#3a2a0e; font-size:12px; letter-spacing:3px; font-weight:700; }
.ts-crt{ position:absolute; inset:0; pointer-events:none; background:repeating-linear-gradient(#0000 0 2px,#0002 2px 3px); box-shadow:inset 0 0 110px #000b; }
.ts-copy{ position:absolute; left:0; right:0; bottom:6px; text-align:center; font-size:11px; color:#e8f3ee; text-shadow:1px 1px 0 #000; }
.st-key-menu{ position:relative; z-index:5; width:330px; max-width:84%; margin:-330px 8% 0 auto; }

/* ---------- 소장 접수 ---------- */
.doc-head{ text-align:center; font-size:30px; font-weight:700; letter-spacing:12px; color:#f7e9b0; text-shadow:3px 3px 0 #000; margin:6px 0 12px; }
.doc-head small{ display:block; font-size:13px; letter-spacing:3px; color:#9fe8ff; }
.st-key-paper{ background:#efe3bf; border:4px double #7a5a2a; padding:18px; box-shadow:6px 6px 0 #000; }
.st-key-paper label, .st-key-paper p, .st-key-paper h3{ color:#2b2111 !important; }
.st-key-paper input, .st-key-paper textarea{ background:#fff8e0 !important; color:#2b2111 !important; }
.st-key-paper [data-baseweb="input"], .st-key-paper [data-baseweb="textarea"], .st-key-paper [data-baseweb="base-input"]{ background:#fff8e0 !important; }

/* ---------- 심문 입력창 ---------- */
[data-testid="stBottom"] > div{ background:#0a0d18; }
[data-testid="stChatInput"]{ background:#10162e; border:3px solid #c9b26b; border-radius:0; }
[data-testid="stChatInput"] textarea{ color:#fff !important; }

/* ---------- HUD (모바일 RPG풍) ---------- */
.st-key-hud{ background:linear-gradient(#1b2350,#10162e); border:3px solid #c9b26b; box-shadow:4px 4px 0 #000; padding:6px 8px; margin-bottom:12px; }
.st-key-hud [data-testid="stHorizontalBlock"]{ flex-wrap:nowrap !important; align-items:center; gap:6px !important; }
.st-key-hud [data-testid="stColumn"], .st-key-hud [data-testid="column"]{ min-width:0 !important; }
.st-key-hud .stButton>button{ height:38px; min-height:38px; padding:0; letter-spacing:0; font-size:18px; clip-path:none; border-width:2px; }
.hud{ display:flex; align-items:center; justify-content:space-between; gap:10px; font-size:12px; line-height:1.35; }
.hud-n{ font-weight:700; color:#fff; max-width:130px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.hud-r{ color:#ffd23f; font-weight:700; white-space:nowrap; }
.hud-fl{ color:#9fe8ff; font-weight:700; white-space:nowrap; }
.pips{ display:flex; gap:4px; margin-top:3px; }
.pip{ width:16px; height:10px; border:2px solid #c9b26b; background:#0a0d18; display:inline-block; }
.pip.on{ background:linear-gradient(#ffe066,#e0a82e); }
.hud-f.low .hud-fl{ color:#ff6b6b; animation:hudblink 1s steps(2) infinite; }
.eta{ display:block; color:#b8c4e8; font-size:11px; }
@keyframes hudblink{ 50%{ opacity:.3; } }

/* ---------- 로딩 연출 ---------- */
.loading{ margin:18px 0; padding:22px 18px; text-align:center; font-size:18px; font-weight:700; color:#f7e9b0;
  background:linear-gradient(#1b2350,#10162e); border:4px double #c9b26b; box-shadow:6px 6px 0 #000; }
.loading small{ display:block; margin-top:10px; font-size:12px; font-weight:400; color:#9fe8ff; }

/* ---------- HUD v2 (닉네임·칭호 / 랭크·선임비) ---------- */
.hud2{ line-height:1.4; font-size:12px; }
.h-l1{ display:flex; align-items:center; gap:6px; white-space:nowrap; overflow:hidden; }
.h-l1 b{ color:#fff; max-width:92px; overflow:hidden; text-overflow:ellipsis; }
.h-title{ color:#9fe8ff; font-size:11px; overflow:hidden; text-overflow:ellipsis; border:1px solid #9fe8ff66; padding:0 5px; }
.h-l2{ display:flex; align-items:center; justify-content:space-between; gap:8px; margin-top:2px; white-space:nowrap; }
.h-rank{ color:#ffd23f; font-weight:700; overflow:hidden; text-overflow:ellipsis; }
.h-fee{ color:#9fe8ff; font-weight:700; display:inline-flex; align-items:center; gap:4px; }
.h-fee.low{ color:#ff6b6b; animation:hudblink 1s steps(2) infinite; }
.h-fee .pips{ display:inline-flex; margin:0; }
.st-key-hud .stButton>button{ padding:0; font-size:17px; }

/* ---------- 로비 ---------- */
.lobby-hero{ position:relative; height:360px; overflow:hidden; text-align:center; border:4px solid #2a2f57; box-shadow:6px 6px 0 #000;
  background:linear-gradient(#10163f,#2a2f77 62%,#d9c78d 62%); }
.lobby-hero .stars{ position:absolute; inset:0; opacity:.55; background-image:radial-gradient(#fff 1px,transparent 1.6px); background-size:46px 38px; }
.lobby-hero .bldg{ position:relative; font-size:128px; margin-top:40px; filter:drop-shadow(0 6px 0 #000); }
.lobby-hero .lh-t{ position:absolute; left:0; right:0; bottom:14px; color:#fff; font-weight:700; font-size:20px; text-shadow:2px 2px 0 #000; }
.lobby-hero .lh-t small{ display:block; font-size:12px; font-weight:400; color:#2a1a00; text-shadow:none; margin-top:2px; }
.st-key-lobby_main{ margin-top:14px; }
.st-key-lobby_main .stButton>button{ height:80px; font-size:21px; letter-spacing:3px; border-color:#ffd23f; background:linear-gradient(#e0a82e,#a8741a); animation:glow 1.6s ease-in-out infinite; }
.st-key-lobby_main .stButton>button, .st-key-lobby_main .stButton>button *{ color:#2a1a00 !important; }
.st-key-lobby_main .stButton>button:disabled{ filter:grayscale(.8); animation:none; }
@keyframes glow{ 50%{ filter:brightness(1.28); } }
.tip{ margin:12px 0; padding:8px 12px; font-size:12px; color:#b8c4e8; border-left:4px solid #c9b26b; background:#10162e; }

/* ---------- 전체 화면 로딩 ---------- */
.lf{ position:fixed; inset:0; z-index:999999; display:flex; align-items:center; justify-content:center;
  background:radial-gradient(#1b2350,#05070f 72%); animation:lfin .35s; }
.lf::after{ content:""; position:absolute; inset:0; pointer-events:none; background:repeating-linear-gradient(#0000 0 2px,#0002 2px 3px); }
.lf-in{ position:relative; z-index:1; width:min(92vw,560px); text-align:center; padding:30px 24px; border:4px double #c9b26b; background:#10162ee6; box-shadow:6px 6px 0 #000; }
.lf-icon{ font-size:64px; animation:lfb 1s steps(2) infinite; }
.lf-step{ margin-top:4px; color:#ffd23f; letter-spacing:3px; font-size:13px; font-weight:700; }
.lf-msg{ margin:14px 0; min-height:60px; font-size:19px; font-weight:700; color:#f7e9b0; line-height:1.5; word-break:keep-all; }
.lf-bar{ height:14px; border:3px solid #c9b26b; background:#0a0d18; overflow:hidden; }
.lf-bar i{ display:block; height:100%; width:40%; background:repeating-linear-gradient(45deg,#ffd23f 0 10px,#e0a82e 10px 20px); animation:lfm 1.4s linear infinite; }
.lf-meta{ margin-top:8px; font-size:12px; color:#9fe8ff; }
.lf-tip{ margin-top:14px; padding-top:10px; border-top:1px dashed #c9b26b66; font-size:12px; color:#b8c4e8; }
@keyframes lfin{ from{ opacity:0; } to{ opacity:1; } }
@keyframes lfb{ 50%{ transform:translateY(-8px) rotate(-6deg); } }
@keyframes lfm{ 0%{ transform:translateX(-100%); } 100%{ transform:translateX(260%); } }
iframe{ animation:pagein .6s; }
@keyframes pagein{ from{ opacity:0; transform:translateY(8px); } to{ opacity:1; transform:none; } }

/* ============ 도트/픽셀 아케이드 오버라이드 ============ */
:root{ --ink:#0d0f26; }
.stApp, .stApp p, .stApp label, .stApp button, .stApp textarea, .stApp input{ font-size:16px; }
/* 픽셀 테두리: 네 방향 그림자로 만든 '모서리가 깎인' 굵은 외곽선 + 단단한 바닥 그림자 */
.stButton{ padding:6px 5px 12px; }
.stButton>button{ height:54px; border:0 !important; border-radius:0 !important; clip-path:none !important; letter-spacing:2px !important; font-weight:700;
  background:#ffd23f !important;
  box-shadow:0 -4px 0 0 var(--ink),0 4px 0 0 var(--ink),-4px 0 0 0 var(--ink),4px 0 0 0 var(--ink),
             inset 0 4px 0 0 #fff4b8,inset 0 -6px 0 0 #d98e00,0 10px 0 0 #0009 !important; transition:transform .06s; }
.stButton>button, .stButton>button *{ color:#2b1a00 !important; text-shadow:0 1px 0 #fff7; }
.stButton>button:hover{ filter:brightness(1.1); transform:translateY(-2px); }
.stButton>button:active{ transform:translateY(5px);
  box-shadow:0 -4px 0 0 var(--ink),0 4px 0 0 var(--ink),-4px 0 0 0 var(--ink),4px 0 0 0 var(--ink),inset 0 4px 0 0 #fff4b8,inset 0 -3px 0 0 #d98e00 !important; }
.stButton>button:disabled{ background:#8a8ea6 !important; opacity:1; transform:none;
  box-shadow:0 -4px 0 0 var(--ink),0 4px 0 0 var(--ink),-4px 0 0 0 var(--ink),4px 0 0 0 var(--ink),inset 0 4px 0 0 #c3c6d8,inset 0 -6px 0 0 #5d6178,0 10px 0 0 #0009 !important; }
.stButton>button:disabled, .stButton>button:disabled *{ color:#3d4056 !important; text-shadow:none; }
/* 보조 버튼(HUD·네비·스토리·소장 접수 하단)은 파란색 */
.st-key-hud .stButton>button, .st-key-nav3 .stButton>button, .st-key-story_nav .stButton>button, .st-key-paper .stButton>button{
  background:#5b8cff !important;
  box-shadow:0 -4px 0 0 var(--ink),0 4px 0 0 var(--ink),-4px 0 0 0 var(--ink),4px 0 0 0 var(--ink),
             inset 0 4px 0 0 #bcd2ff,inset 0 -6px 0 0 #2f4fc4,0 10px 0 0 #0009 !important; }
.st-key-hud .stButton>button, .st-key-hud .stButton>button *, .st-key-nav3 .stButton>button, .st-key-nav3 .stButton>button *,
.st-key-story_nav .stButton>button, .st-key-story_nav .stButton>button *, .st-key-paper .stButton>button, .st-key-paper .stButton>button *{ color:#fff !important; text-shadow:2px 2px 0 #0d0f2699; }
.st-key-hud .stButton{ padding:2px 4px 8px; }
.st-key-hud .stButton>button{ height:40px; font-size:16px; }
/* 메인 [소장 접수] 버튼: 크고 빨갛게 */
.st-key-lobby_main .stButton>button{ height:96px; font-size:22px; background:#ff5b4a !important;
  box-shadow:0 -4px 0 0 var(--ink),0 4px 0 0 var(--ink),-4px 0 0 0 var(--ink),4px 0 0 0 var(--ink),
             inset 0 5px 0 0 #ffb8b0,inset 0 -8px 0 0 #b3261a,0 12px 0 0 #0009 !important; animation:pxpulse 1.1s steps(2) infinite; }
.st-key-lobby_main .stButton>button, .st-key-lobby_main .stButton>button *{ color:#fff !important; text-shadow:3px 3px 0 #7a130a; }
.st-key-lobby_main .stButton>button:disabled{ animation:none; background:#8a8ea6 !important; }
.st-key-lobby_main .stButton>button:disabled, .st-key-lobby_main .stButton>button:disabled *{ color:#3d4056 !important; text-shadow:none; }
@keyframes pxpulse{ 50%{ transform:translateY(-4px); } }
/* 타이틀 메뉴 버튼 */
.st-key-menu .stButton>button{ height:56px; font-size:18px; }
/* 패널류: 픽셀 외곽선 */
.st-key-hud, .st-key-paper, .loading, .lf-in, .tip, .result-big, .keybox, .ts, .lobby-hero, .ask{ border:0 !important; border-radius:0 !important;
  box-shadow:0 -4px 0 0 var(--ink),0 4px 0 0 var(--ink),-4px 0 0 0 var(--ink),4px 0 0 0 var(--ink),inset 0 4px 0 0 #ffffff22,inset 0 -6px 0 0 #00000033,0 10px 0 0 #0009 !important; }
.st-key-hud{ background:linear-gradient(#27327f,#151b4a); padding:8px 8px 4px; margin:4px 5px 14px; }
.st-key-paper{ background:#fff4d6; margin:4px 5px 14px; padding:14px; }
.st-key-paper [data-baseweb="input"], .st-key-paper [data-baseweb="textarea"], .st-key-paper [data-baseweb="base-input"]{
  border-radius:0 !important; border:3px solid var(--ink) !important; background:#fffdf4 !important; }
.ts, .lobby-hero{ margin:4px 5px 14px; }
.tip, .loading, .keybox{ margin:12px 5px; }
.tip{ border-left:0 !important; }
.h-title{ border-radius:0; padding:0 6px; border:2px solid #ffe3a3; background:transparent; color:#ffe3a3; }
.h-fire{ color:#ff9b3d; font-weight:700; }
.pip{ border-radius:0; width:14px; height:12px; }
.keybox{ background:#3a1620; color:#ffd0d0; padding:14px; line-height:1.6; }
.keybox code{ background:#0d0f26; color:#ffe066; padding:1px 6px; }
/* 결과 큼직 패널 */
.result-big{ max-width:760px; margin:18px auto; padding:20px 12px; text-align:center; background:#161c4d; color:#fff; }
.rb-title{ font-size:15px; color:#9fe8ff; letter-spacing:2px; }
.rb-delta{ font-size:56px; font-weight:900; line-height:1.15; margin:6px 0; text-shadow:4px 4px 0 #000; }
.result-big.up .rb-delta{ color:#59f08a; } .result-big.down .rb-delta{ color:#ff6b6b; }
.rb-rep{ font-size:22px; font-weight:700; color:#fff; }
.rb-rank{ font-size:24px; font-weight:900; color:#ffe066; margin-top:10px; text-shadow:3px 3px 0 #000; line-height:1.4; }
.rb-meta{ font-size:14px; color:#b8c4e8; margin-top:10px; }
/* 타이틀 로고: 두꺼운 도트 감성 */
.ts-logo small{ border-radius:0; background:#ffd23f; color:#2b1a00; border:3px solid var(--ink); box-shadow:4px 4px 0 var(--ink); padding:4px 12px; letter-spacing:2px; }
.ts-logo h1{ font-size:clamp(50px,14vw,84px); letter-spacing:2px; -webkit-text-stroke:5px var(--ink); paint-order:stroke fill;
  text-shadow:6px 6px 0 #ff4d4d,11px 11px 0 var(--ink); }
.ts-logo em{ font-family:'Press Start 2P',monospace; font-size:9px; color:#fff; letter-spacing:1px; text-shadow:2px 2px 0 var(--ink); }
.ts-seal{ border-radius:0; box-shadow:0 0 0 4px var(--ink); }
.ts-crt{ border-radius:0; }
.doc-head{ text-shadow:0 4px 0 #000a; }
iframe{ border:0 !important; border-radius:0 !important; margin:4px 5px;
  box-shadow:0 -4px 0 0 var(--ink),0 4px 0 0 var(--ink),-4px 0 0 0 var(--ink),4px 0 0 0 var(--ink),0 10px 0 0 #0009; }
[data-testid="stChatInput"]{ border-radius:0 !important; border:0 !important; background:#10162e;
  box-shadow:0 -4px 0 0 var(--ink),0 4px 0 0 var(--ink),-4px 0 0 0 var(--ink),4px 0 0 0 var(--ink); }
div[role="dialog"]{ border-radius:0 !important; box-shadow:0 -4px 0 0 var(--ink),0 4px 0 0 var(--ink),-4px 0 0 0 var(--ink),4px 0 0 0 var(--ink),0 12px 0 0 #000a; }
/* 좁은 화면에서도 버튼 줄이 세로로 쌓이지 않게 */
.st-key-ask2 [data-testid="stHorizontalBlock"], .st-key-story_nav [data-testid="stHorizontalBlock"],
.st-key-nav3 [data-testid="stHorizontalBlock"]{ flex-wrap:nowrap !important; gap:8px !important; }
.st-key-ask2 [data-testid="stColumn"], .st-key-story_nav [data-testid="stColumn"], .st-key-nav3 [data-testid="stColumn"],
.st-key-ask2 [data-testid="column"], .st-key-story_nav [data-testid="column"], .st-key-nav3 [data-testid="column"]{ min-width:0 !important; }

/* ---------- 스토리 / 스토리 확인 ---------- */
.story{ padding:22px 18px; text-align:center; background:linear-gradient(#1c2557,#0f1538); border:4px solid #ffe3a3;
  box-shadow:0 12px 28px #000a; animation:pagein .5s; min-height:380px; margin-bottom:12px; }
.story-scene{ font-size:78px; margin:10px 0 16px; display:inline-block; }
.story-text{ font-size:18px; line-height:1.85; color:#fff; word-break:keep-all; text-align:left; }
.story-dots{ margin-top:16px; letter-spacing:7px; color:#ffe3a3; font-size:12px; }
.anim-float{ animation:sfloat 2.4s ease-in-out infinite; } @keyframes sfloat{ 50%{ transform:translateY(-12px); } }
.anim-bounce{ animation:sbounce .9s ease-in-out infinite; } @keyframes sbounce{ 50%{ transform:translateY(-14px) rotate(-6deg); } }
.anim-walk{ animation:swalk 2.2s linear infinite; } @keyframes swalk{ 0%{ transform:translateX(-80px); opacity:0; } 30%{ opacity:1; } 100%{ transform:translateX(80px); opacity:0; } }
.anim-zoom{ animation:szoom 2.8s ease-out forwards; } @keyframes szoom{ 0%{ transform:scale(.4); } 100%{ transform:scale(1.5); } }
.anim-pulse{ animation:spulse 1s ease-in-out infinite; } @keyframes spulse{ 50%{ transform:scale(1.25); } }
.ask{ padding:36px 20px; text-align:center; max-width:640px; margin:40px auto 18px; background:linear-gradient(#27327f,#151b4a); border:4px solid #ffe3a3; box-shadow:0 12px 28px #000a; }
.ask-icon{ font-size:72px; }
.ask h2{ font-size:25px; line-height:1.4; color:#fff; margin:8px 0; padding:0; }
.ask p{ color:#b8c4e8; margin:0; }
.lf-head{ font-size:32px; color:#fff; margin-top:6px; text-shadow:3px 3px 0 #000; }
.lf-bar, .lf-bar i{ border-radius:0; }
/* ============ 가로 화면(Landscape) 레이아웃 ============ */
.st-key-ask2, .st-key-story_nav{ max-width:560px; margin-left:auto; margin-right:auto; }
.st-key-lobby_main .stButton>button{ height:104px; font-size:24px; }
.st-key-paper textarea{ font-size:17px; line-height:1.6; }
.tip{ font-size:13px; line-height:1.6; }
.lf-msg{ font-size:22px; }

/* ============ 좁은 화면(세로 모드 폰 등) 대비 ============ */
@media (max-width: 760px){
  .block-container, [data-testid="stMainBlockContainer"]{ max-width:480px !important; padding:1rem .8rem 7rem !important; }
  [data-testid="stBottom"] > div, [data-testid="stBottomBlockContainer"]{ max-width:480px !important; }
  div[role="dialog"]{ max-width:440px !important; }
  .ts{ height:580px; }
  .ts-seal{ left:50%; }
  .ts-logo{ right:0; top:13%; }
  .st-key-menu{ width:250px; margin:-282px auto 0; }
  .lobby-hero{ height:250px; }
  .lobby-hero .bldg{ font-size:96px; margin-top:22px; }
  .lobby-hero .lh-t{ font-size:17px; }
  .lf-in{ width:min(92vw,420px); padding:26px 18px; }
  .lf-msg{ font-size:19px; }
  .st-key-lobby_main .stButton>button{ height:96px; font-size:22px; }
}
/* ============ 서브컬처풍 가로 로비: 장면(iframe) 위에 버튼을 겹쳐 배치 ============ */
.st-key-lobby_stage{ position:relative; margin:4px 5px 14px; }
.st-key-lobby_stage iframe{ margin:0 !important; }
.st-key-lobby_ui{ position:absolute; inset:0; pointer-events:none; z-index:6; }
.st-key-lobby_ui button{ pointer-events:auto; }
.st-key-lb_side{ position:absolute; left:14px; top:14px; width:124px; display:flex; flex-direction:column; gap:2px; }
.st-key-lb_side .stButton>button, .st-key-lb_corner .stButton>button{ height:48px; font-size:14px; letter-spacing:0 !important;
  background:#5b8cff !important;
  box-shadow:0 -4px 0 0 var(--ink),0 4px 0 0 var(--ink),-4px 0 0 0 var(--ink),4px 0 0 0 var(--ink),inset 0 4px 0 0 #bcd2ff,inset 0 -6px 0 0 #2f4fc4,0 10px 0 0 #0009 !important; }
.st-key-lb_side .stButton>button, .st-key-lb_side .stButton>button *, .st-key-lb_corner .stButton>button, .st-key-lb_corner .stButton>button *{
  color:#fff !important; text-shadow:2px 2px 0 #0d0f2699; }
.st-key-lb_corner{ position:absolute; right:14px; bottom:12px; width:124px; }
.st-key-lobby_stage .st-key-lobby_main{ position:absolute; left:50%; bottom:12px; transform:translateX(-50%); width:min(460px,56%); margin:0; }
.st-key-lobby_stage .st-key-lobby_main .stButton{ padding:0 5px 8px; }
.st-key-lobby_stage .st-key-lobby_main .stButton>button{ height:84px; font-size:24px; }
@media (max-width: 760px){
  .st-key-lb_side{ left:8px; top:8px; width:96px; }
  .st-key-lb_side .stButton>button, .st-key-lb_corner .stButton>button{ height:40px; font-size:12px; }
  .st-key-lb_corner{ right:8px; bottom:8px; width:96px; }
  .st-key-lobby_stage .st-key-lobby_main{ width:70%; }
  .st-key-lobby_stage .st-key-lobby_main .stButton>button{ height:72px; font-size:20px; }
}
/* ============ '오늘의 법정' 상태 패널 (프로필 모달 안에서만 표시) ============ */
.court-panel{ background:#10162e; color:#fff; padding:14px 16px; margin:6px 5px 14px;
  box-shadow:0 -4px 0 var(--ink),0 4px 0 var(--ink),-4px 0 0 var(--ink),4px 0 0 var(--ink),inset 0 4px 0 #3b4a9a,0 10px 0 0 #0008; }
.court-panel .cp-t{ font-size:12px; color:#9fe8ff; letter-spacing:2px; }
.court-panel .cp-r{ font-size:24px; font-weight:900; color:#ffe066; margin:4px 0 8px; text-shadow:2px 2px 0 #000; }
.court-panel .cp-row{ display:flex; justify-content:space-between; align-items:center; gap:8px; font-size:14px; margin:6px 0; }
.court-panel .cp-row b{ color:#fff; font-size:16px; }
.court-panel .cp-gauge{ height:14px; border:3px solid var(--ink); background:#050510; margin:6px 0 2px; overflow:hidden; }
.court-panel .cp-gauge i{ display:block; height:100%; background:repeating-linear-gradient(45deg,#59f08a 0 8px,#2fbf63 8px 16px); }
.court-panel .cp-sub{ font-size:12px; color:#b8c4e8; }
.court-panel .cp-pips{ display:inline-flex; gap:4px; align-items:center; }
"""

# =================================================================
# OpenRouter / LLM 호출 설정  (무료 모델 목록은 자주 바뀌니 필요하면 여기만 고치세요)
# =================================================================

BASE_URL = "https://openrouter.ai/api/v1"

# 무료(:free) 모델은 몇 주 단위로 사라지거나 429로 막힙니다. 위에서부터 차례로 시도하며 실패하면 자동으로 다음 모델로 넘어갑니다.
# (2026-11-03 기준 실제 호출 테스트를 통과한 모델 목록. 최신 상태: https://openrouter.ai/collections/free-models)
MODEL_CANDIDATES = [
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nvidia/nemotron-3.5-super-vl:free",
    "nvidia/nemotron-3.5-lightning:free",
    "dots-studio/dots-3-note-preview:free",
    "cohere/north-mini-code:free",
]

# (선택) 무료 모델이 전부 실패할 때 마지막으로 쓸 '유료' 모델. 아주 저렴하지만 크레딧이 필요합니다. 쓰지 않으려면 빈 문자열.
PAID_FALLBACK = ""  # 예: "openai/gpt-oss-120b"

ATTEMPTS_PER_MODEL = 3  # 빈 응답/JSON 깨짐이면 같은 모델에 최대 3회까지 재시도

MAX_TOTAL_CALLS = 9  # 한 번의 요청에서 쓸 최대 호출 수 (무료 한도: 분당 20회, 일 50회 → 낭비 방지)

REASONING_HEADROOM = 2000  # 추론형 모델이 '생각'에 토큰을 쓰고 본문을 비우는 문제 방지용 여유분

REQUEST_TIMEOUT = 90  # 초

# =================================================================
# 게임 정책: 변호사 선임비 / 평판 / 랭크 / 판정
# =================================================================

RULING_LABEL = {"NOT_GUILTY": "무죄", "MITIGATED": "감형", "GUILTY": "유죄"}

FEE_MAX = 3  # 변호사 선임비 (재판 1회당 1 차감)

REGEN_SEC = 600  # 선임비 자동 충전 주기 (10분에 1)

REP_START = 100  # 시작 평판 점수

# 평판 점수가 높을수록 좋은 랭크. 무죄를 '연달아' 받으면 연승 보너스로 👑 최상위 랭크까지 올라갈 수 있다.
RANKS = [
    (0, "🔴", "인간 흑역사 박물관"), (20, "🟠", "이불킥 장인"), (60, "🟡", "새벽 감성러"),
    (120, "🟢", "정상인"), (200, "👑", "이불킥 청정수"),
]

RULING_DELTA = {"NOT_GUILTY": 30, "MITIGATED": 10, "GUILTY": -20}  # 여기에 변명 점수//20 가산

STREAK_BONUS = 10  # 무죄 2연승부터 (연승-1)×10 가산, 최대 +30

SPEED_MS = {"느리게": 45, "보통": 30, "빠르게": 16}

VN_H = 560  # 가로형(16:9에 가까운) 연출 화면 높이
LOBBY_H = 540  # 로비 장면(iframe) 높이

RUN_KEYS = ("p1", "p2", "ex1", "ex2", "facts", "verdict_data", "history_text", "case_name", "result", "show_result", "job")

# =================================================================
# 화면 문구: 로딩 멘트 / 로비 팁
# =================================================================

LOADING_P1 = [
    "⚖️ 검사와 변호사가 치열하게 증거를 조작하는 중", "🏛️ 서판결 판사가 돋보기로 흑역사를 정밀 감식 중",
    "📜 차냉정 검사가 공소장에 빨간 줄을 긋는 중", "🛡️ 우기기 변호사가 눈물겨운 쉴드 대본을 쓰는 중",
    "☕ 서판결 판사가 보리차를 마시며 한숨 쉬는 중", "🔨 법원 직원이 망치를 닦는 중",
]

LOADING_P2 = [
    "🧊 차냉정 검사가 변명의 허점을 얼려서 부수는 중", "🎭 우기기 변호사가 변명을 감동 실화로 각색하는 중",
    "🏛️ 서판결 판사가 훈계 원고를 다듬는 중", "📎 서기관이 변명 속 모순에 형광펜을 긋는 중",
    "💧 우기기 변호사가 손수건을 준비하는 중",
]

LOADING_V = [
    "🖋️ 서판결 판사가 판결문에 만년필을 꾹꾹 눌러쓰는 중", "🎲 형량 룰렛을 돌리는 중", "🏅 뱃지 공방에서 칭호를 각인하는 중",
    "📠 판결문을 인쇄하다 용지가 걸린 중", "🔨 법원 직원이 망치를 다시 닦는 중",
]

LOAD_STEP = {"p1": "제1막 준비 중", "p2": "제2막 준비 중", "verdict": "최종 판결문 작성 중"}

LOAD_HEAD = {"p1": ("⚖️", "개정 준비!"), "p2": ("⚡", "이의 있습니다!"), "verdict": ("🔨", "판결 직전!")}

LOAD_MSGS = {"p1": LOADING_P1, "p2": LOADING_P2, "verdict": LOADING_V}

LOAD_TIPS = [
    "구체적으로 적을수록 공방이 정확해집니다.", "입력하신 내용만 사실로 취급됩니다.",
    "변명은 사실에 맞고 진심일수록 무죄에 가까워져요.", "무료 AI라 조금 느릴 수 있어요. 법정이 열리는 중입니다.",
]

LOBBY_TIPS = [
    "흑역사를 구체적으로 적을수록 공방이 정확해집니다.",
    "입력하신 내용만 사실로 취급됩니다. 없는 얘기는 법정도 지어내지 않아요.",
    "변명은 사실에 맞게, 진심을 담아 쓸수록 무죄에 가까워져요.",
    "무죄를 연달아 받으면 연승 보너스! 3연승이면 👑 이불킥 청정수도 노려볼 수 있어요.",
]
