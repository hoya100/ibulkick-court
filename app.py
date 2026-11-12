"""
이불킥 법정 (Kick-the-Blanket Court) — 오리지널 B급 법정 아케이드 (Streamlit)

■ 실행/배포 전 체크리스트 ─────────────────────────────────────────
1) 설치      pip install "streamlit>=1.40" openai
2) 실행      streamlit run app.py

3) API 키는 절대 코드에 적지 마세요. 아래 두 가지 중 하나로만 설정합니다.
   (a) 로컬:  프로젝트 폴더에 .streamlit/secrets.toml 파일을 만들고
              OPENROUTER_API_KEY = "여기에_발급받은_키"
   (b) 배포:  Streamlit Community Cloud → 앱 Settings → Secrets 에 같은 한 줄을 붙여넣기
   * 코드는 st.secrets["OPENROUTER_API_KEY"] 를 읽고, 없으면 환경변수 OPENROUTER_API_KEY 를 읽습니다.
   * 키가 없으면 앱이 죽지 않고 '관리자용 설정 방법' 안내만 표시합니다.

4) .gitignore 에 반드시 추가 (키가 GitHub에 올라가는 사고 방지)
       .streamlit/
       secrets.toml
       __pycache__/
       .env
   이미 키를 커밋했다면: 해당 키를 즉시 폐기(재발급)하세요. 삭제 커밋만으로는 기록이 남습니다.

5) requirements.txt (배포용)
       streamlit>=1.40
       openai>=1.30
───────────────────────────────────────────────────────────────────
"""
import concurrent.futures as cf
import html
import json
import os
import random
import re
import time

import streamlit as st
import streamlit.components.v1 as components
from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    OpenAI,
    PermissionDeniedError,
    RateLimitError,
)

# 필요 패키지: pip install "streamlit>=1.40" openai
st.set_page_config(page_title="이불킥 법정", page_icon="🏛️", layout="centered")

APP_CSS = r"""
@import url('https://fonts.googleapis.com/css2?family=Jua&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
@import url('https://cdn.jsdelivr.net/npm/galmuri@latest/dist/galmuri.css');
.stApp, .stApp p, .stApp label, .stApp button, .stApp textarea, .stApp input, .stApp h1, .stApp h2, .stApp h3, .stApp small, .stApp span.st-emotion-cache-0
{ font-family:'Galmuri11','Jua','Apple SD Gothic Neo','Malgun Gothic',sans-serif; }
.stApp{ background:#05070f; color:#eef2ff; }
header[data-testid="stHeader"], footer{ display:none; }
.block-container, [data-testid="stMainBlockContainer"]{ max-width:480px !important; margin:0 auto; padding:1rem .8rem 7rem !important; background:#0a0d18; box-shadow:0 0 0 3px #1b2350, 0 0 60px #000; min-height:100vh; }
html, body{ overflow-x:hidden; }
[data-testid="stBottom"] > div, [data-testid="stBottomBlockContainer"]{ max-width:480px !important; margin:0 auto; }
div[role="dialog"]{ max-width:440px !important; }
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
.ts{ position:relative; height:580px; overflow:hidden; }
.ts-wall{ position:absolute; inset:0; background:linear-gradient(#f1e5b7,#d9c78d); }
.ts-pil{ position:absolute; top:0; bottom:30%; width:11%; border-left:3px solid #8f7a46; border-right:3px solid #8f7a46;
  background:linear-gradient(90deg,#c9b27a,#f3e7bd 45%,#b59c61); }
.ts-pil.l{ left:5%; } .ts-pil.r{ right:5%; }
.ts-seal{ position:absolute; left:50%; top:5%; transform:translateX(-50%); width:78px; height:78px; border-radius:50%;
  background:radial-gradient(#fff,#cfd6e6); border:5px solid #c9a24d; box-shadow:0 0 0 4px #7a5a1e;
  display:flex; align-items:center; justify-content:center; font-size:38px; }
.ts-bench{ position:absolute; left:22%; right:22%; bottom:24%; height:26%; border:5px solid #4f2a12;
  background:linear-gradient(#b06a33 0 14%,#7d4521 14%); }
.ts-floor{ position:absolute; left:0; right:0; bottom:0; height:30%; border-top:5px solid #6b4423;
  background:repeating-conic-gradient(#d7e9de 0 25%,#aecbbb 0 50%) 0 0/54px 54px; }
.ts-logo{ position:absolute; left:0; right:0; top:13%; text-align:center; }
.ts-logo small{ display:inline-block; background:#1a1f4a; color:#9fe8ff; padding:3px 12px; letter-spacing:3px; border:2px solid #9fe8ff; }
.ts-logo h1{ font-size:clamp(44px,12vw,76px); line-height:1.05; color:#fff; margin:8px 0 4px; letter-spacing:4px; padding:0;
  -webkit-text-stroke:3px #1a1f4a; text-shadow:5px 5px 0 #c1121f,8px 8px 0 #000; }
.ts-logo em{ font-style:normal; color:#3a2a0e; font-size:12px; letter-spacing:3px; font-weight:700; }
.ts-crt{ position:absolute; inset:0; pointer-events:none; background:repeating-linear-gradient(#0000 0 2px,#0002 2px 3px); box-shadow:inset 0 0 110px #000b; }
.ts-copy{ position:absolute; left:0; right:0; bottom:6px; text-align:center; font-size:11px; color:#e8f3ee; text-shadow:1px 1px 0 #000; }
.st-key-menu{ position:relative; z-index:5; width:250px; max-width:84%; margin:-282px auto 0; }

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
.lobby-hero{ position:relative; height:250px; overflow:hidden; text-align:center; border:4px solid #2a2f57; box-shadow:6px 6px 0 #000;
  background:linear-gradient(#10163f,#2a2f77 62%,#d9c78d 62%); }
.lobby-hero .stars{ position:absolute; inset:0; opacity:.55; background-image:radial-gradient(#fff 1px,transparent 1.6px); background-size:46px 38px; }
.lobby-hero .bldg{ position:relative; font-size:96px; margin-top:22px; filter:drop-shadow(0 6px 0 #000); }
.lobby-hero .lh-t{ position:absolute; left:0; right:0; bottom:12px; color:#fff; font-weight:700; font-size:17px; text-shadow:2px 2px 0 #000; }
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
.lf-in{ position:relative; z-index:1; width:min(92vw,420px); text-align:center; padding:26px 18px; border:4px double #c9b26b; background:#10162ee6; box-shadow:6px 6px 0 #000; }
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
.st-key-hud, .st-key-paper, .loading, .lf-in, .tip, .result-big, .keybox, .ts, .lobby-hero{ border:0 !important; border-radius:0 !important;
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
.result-big{ margin:18px 5px; padding:20px 12px; text-align:center; background:#161c4d; color:#fff; }
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
.st-key-nav3 [data-testid="stHorizontalBlock"], .st-key-paper [data-testid="stHorizontalBlock"]{ flex-wrap:nowrap !important; gap:8px !important; }
.st-key-ask2 [data-testid="stColumn"], .st-key-story_nav [data-testid="stColumn"], .st-key-nav3 [data-testid="stColumn"],
.st-key-paper [data-testid="stColumn"], .st-key-ask2 [data-testid="column"], .st-key-story_nav [data-testid="column"],
.st-key-nav3 [data-testid="column"], .st-key-paper [data-testid="column"]{ min-width:0 !important; }

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
.ask{ padding:36px 20px; text-align:center; margin:40px 0 18px; background:linear-gradient(#27327f,#151b4a); border:4px solid #ffe3a3; box-shadow:0 12px 28px #000a; }
.ask-icon{ font-size:72px; }
.ask h2{ font-size:25px; line-height:1.4; color:#fff; margin:8px 0; padding:0; }
.ask p{ color:#b8c4e8; margin:0; }
.lf-head{ font-size:32px; color:#fff; margin-top:6px; text-shadow:3px 3px 0 #000; }
.lf-bar, .lf-bar i{ border-radius:0; }
"""
st.markdown("<style>" + APP_CSS + "</style>", unsafe_allow_html=True)

# 🔐 API 키는 코드에 쓰지 않습니다. st.secrets(권장) 또는 환경변수에서만 읽습니다. (아래 get_api_key 참고)

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


def get_api_key():
    """Streamlit Secrets → 환경변수 순서로 키를 읽는다. 키 값은 화면/로그에 절대 출력하지 않는다."""
    key = ""
    try:
        key = st.secrets["OPENROUTER_API_KEY"]
    except Exception:  # secrets.toml이 없거나 키가 없는 경우
        key = ""
    key = key or os.environ.get("OPENROUTER_API_KEY", "")
    return str(key).strip().strip("\"'").strip()  # 공백/따옴표 실수 방지


API_KEY = get_api_key()
KEY_FORMAT_OK = API_KEY.startswith("sk-or-") and len(API_KEY) > 20


def make_client():
    return OpenAI(
        base_url=BASE_URL,
        api_key=API_KEY,
        timeout=REQUEST_TIMEOUT,
        max_retries=0,  # 재시도는 아래 로직에서 직접 제어
        default_headers={"HTTP-Referer": "http://localhost:8501", "X-Title": "Kick-the-Blanket Court"},
    )

SPEAKERS = {
    "JUDGE": ("🏛️", "판사 AI (엄근진 꼰대)", "#fbbf24"),
    "PROSECUTOR": ("⚖️", "검사 AI (팩폭러)", "#ff5555"),
    "LAWYER": ("🛡️", "변호사 AI (억지 쉴드)", "#66fcf1"),
}


def esc(x):
    return html.escape(str(x if x is not None else "")).replace("\n", "<br>")


# =================================================================
# 1. LLM 호출 + 견고한 JSON 파싱
# =================================================================
def extract_json(text):
    """마크다운/설명문이 섞여 있어도 첫 번째 JSON 객체를 최대한 복구."""
    if not text:
        raise ValueError("빈 응답")
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)  # 추론 과정 제거
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("JSON 객체를 찾지 못했습니다")
    body = cleaned[start : end + 1]
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        body = re.sub(r",\s*([}\]])", r"\1", body)  # 꼬리 쉼표 제거
        body = body.replace("\u201c", '"').replace("\u201d", '"')  # 스마트 따옴표
        return json.loads(body, strict=False)  # strict=False: 문자열 내 개행 허용


def read_text(res):
    """응답에서 본문 추출. 비어 있으면 ValueError (→ 재시도/다음 모델)."""
    choices = getattr(res, "choices", None)
    if not choices:
        raise ValueError("API가 빈 응답을 반환했습니다.")
    msg = choices[0].message
    text = (getattr(msg, "content", None) or "").strip()
    if text:
        return text
    # 추론형 모델은 본문을 비우고 reasoning 필드에만 쓰는 경우가 있음 → JSON이 들어 있으면 최후 수단으로 사용
    reasoning = getattr(msg, "reasoning", None) or getattr(msg, "reasoning_content", None) or ""
    if isinstance(reasoning, str) and "{" in reasoning and "}" in reasoning:
        return reasoning
    why = getattr(choices[0], "finish_reason", None)
    raise ValueError("API가 빈 응답을 반환했습니다." + (f" (finish_reason={why})" if why else ""))


def call_llm_json(system_prompt, user_prompt, max_tokens=2500, temperature=0.7, validate=None):
    """OpenRouter 호출 → JSON 파싱.
    - 빈 응답 / JSON 깨짐 / 내용 부족: 같은 모델로 재시도, 그래도 안 되면 다음 모델
    - 429 / 404 / 5xx / 403(모델별 제한): 즉시 다음 모델
    - 401(키 오류): 즉시 중단
    """
    if not API_KEY:
        raise RuntimeError("API 키가 설정되지 않았습니다. Streamlit Secrets에 OPENROUTER_API_KEY를 등록해 주세요.")
    if not KEY_FORMAT_OK:
        raise RuntimeError("API 키 형식이 올바르지 않습니다. 'sk-or-v1-'로 시작하는 키 전체를 넣었는지 확인하세요.")

    client = make_client()
    # 일부 모델은 system 역할을 거부하므로, 하나의 user 메시지로 합쳐서 보냅니다.
    messages = [{"role": "user", "content": f"{system_prompt}\n\n---\n[유저 입력]\n{user_prompt}"}]
    candidates = list(MODEL_CANDIDATES) + ([PAID_FALLBACK] if PAID_FALLBACK else [])

    errors, calls = [], 0
    for model in candidates:
        for attempt in range(1, ATTEMPTS_PER_MODEL + 1):
            if calls >= MAX_TOTAL_CALLS:
                break
            calls += 1
            tag = f"{model} (시도 {attempt}/{ATTEMPTS_PER_MODEL})"
            final = calls > MAX_TOTAL_CALLS - 3  # 막바지에는 검증 기준을 완화
            try:
                res = client.chat.completions.create(
                    model=model, messages=messages, temperature=temperature,
                    max_tokens=max_tokens + REASONING_HEADROOM,
                )
                data = extract_json(read_text(res))
                if validate:
                    validate(data, final)  # 내용 부족/진부함이면 ValueError → 재시도
                return data
            except AuthenticationError as e:
                raise RuntimeError(
                    "🔑 401 인증 실패: OpenRouter 키가 잘못되었거나 삭제되었습니다.\n"
                    "openrouter.ai/keys 에서 키를 확인/재발급한 뒤 Streamlit Secrets의 값을 바꾸고 앱을 다시 실행하세요."
                ) from e
            except ValueError as e:  # 빈 응답, JSON 파싱 실패, 검증 실패 → 같은 모델 재시도
                errors.append(f"{tag}: {e}")
                continue
            except APIConnectionError as e:  # 타임아웃 포함 → 1회 재시도
                errors.append(f"{tag}: 연결 오류/타임아웃 ({type(e).__name__})")
                time.sleep(1)
                continue
            except RateLimitError:
                errors.append(f"{tag}: 429 요청 한도 초과 → 다음 모델")
            except PermissionDeniedError as e:
                errors.append(f"{tag}: 403 이 모델은 직접 호출 불가 → 다음 모델 ({str(e)[:80]})")
            except APIStatusError as e:
                msg = str(e)[:160]
                if e.status_code == 404 and "data policy" in msg.lower():
                    msg += " → openrouter.ai/settings/privacy 에서 무료 모델 데이터 정책을 허용해 주세요."
                errors.append(f"{tag}: HTTP {e.status_code} {msg} → 다음 모델")
            except Exception as e:
                errors.append(f"{tag}: {type(e).__name__}: {str(e)[:120]} → 다음 모델")
            break  # 위에서 continue 되지 않은 오류는 같은 모델을 다시 부르지 않고 다음 모델로
        if calls >= MAX_TOTAL_CALLS:
            break
    raise RuntimeError(
        "모든 모델 호출에 실패했습니다. (무료 모델은 자주 바뀌고 한도가 있습니다. "
        "MODEL_CANDIDATES를 openrouter.ai/collections/free-models 에서 확인한 최신 모델로 바꿔 보세요.)\n"
        + "\n".join(errors)
    )


# =================================================================
# 2. 오리지널 캐릭터 / 프롬프트 / 응답 정규화
# =================================================================
CAST = """등장인물 (모두 이 게임을 위해 새로 만든 오리지널 캐릭터. 다른 작품의 캐릭터·명칭·대사는 절대 사용 금지):
- JUDGE [서판결]: 무게감 있고 차분한 원로 판사. 현실적인 꼰대 잔소리를 하되, 반드시 사건 내용과 직접 연결된 합리적인 훈계만 한다(시간 관리, 체면, 기록이 남는다는 점, 주변에 미치는 영향, 한 번 더 생각하는 습관 등).
  · 반말, 뜬금없는 질문(예: 식사 여부를 묻는 말), 억지 유행어·과장된 개그, 사자성어, 고서 인용, 고어체('~하오/~로다') 전부 금지.
  · 정중하고 단정한 존댓말('~입니다', '~하십시오', '~하셨습니까')을 쓰고, 꼰대 느낌은 "제 경험상", "요즘 세대는" 정도의 평범한 표현으로만 낸다. 어려운 말 대신 쉬운 말을 쓴다.
- PROSECUTOR [차냉정]: 냉정하고 세련된 팩폭러 검사. 감정 없이 정확하게 후벼파며, 숨을 길게 쉬듯 호흡이 긴 문장으로 논리를 쌓는다(시간 순서 정리 → 심리 해부 → 결론 한 방). 격식 있는 존댓말.
- LAWYER [우기기]: 말도 안 되는 흑역사를 어떻게든 감싸려는 눈물겨운 억지 쉴드 변호사. 오글거리는 감성 팔이와 시적인 비유를 총동원하고(예: "그것은 순수한 영혼의 절규였습니다!"), 대사 중간에 (눈물을 훔치며) 같은 짧은 연기 지문을 넣어도 된다. 느낌표가 많고 텐션이 높다."""

FACT_RULES = """[사실 엄수 규칙 — 가장 중요]
- 모든 대사는 오직 유저가 입력한 [흑역사 원문]에 실제로 적힌 사실에만 기반한다.
- 원문에 없는 구체적인 사물, 음식, 인물, 별명, 장소, 숫자, 행동, 설정을 절대 지어내지 말 것.
- 오타처럼 보이는 단어도 임의로 고치거나 다른 말로 해석하지 말고 원문 표현 그대로 인용할 것.
- 원문이 짧아도 새로운 사건을 만들지 말 것. 대신 같은 내용을 다른 각도(그 행동의 의도, 그 순간의 기분, 남이 봤을 때의 인상, 지금 돌아본 시선)로 파고들어 분량을 채울 것.
- 확실하지 않은 부분은 "~라고 적으셨지요", "~했을지도 모릅니다" 같은 인용·추측 표현을 쓰고 사실처럼 단정하지 말 것. "만약 ~였다면" 같은 가정은 가정임을 분명히 밝힐 때만 허용."""

EASY_RULES = """[쉬운 말 규칙]
- 초등학생도 한 번에 이해할 수 있는 쉬운 단어와 짧은 문장을 쓴다. 한 문장은 되도록 40자 안쪽.
- 어려운 한자어, 법률 전문 용어, 영어 약어는 쓰지 않는다. (죄목 이름만 가볍고 웃기게 지어도 된다)
- 한 대사에 한 가지 요점만 담고, 누가 무엇을 했는지 분명하게 말한다."""

NAME_OF = {"JUDGE": "서판결", "PROSECUTOR": "차냉정", "LAWYER": "우기기"}
ALIAS = {"서판결": "JUDGE", "판사": "JUDGE", "차냉정": "PROSECUTOR", "검사": "PROSECUTOR", "우기기": "LAWYER", "변호사": "LAWYER"}
SHOUT_MAP = {"FACT": ("F", "PROSECUTOR"), "SHIELD": ("S", "LAWYER"), "ORDER": ("O", "JUDGE")}
# 형벌의 '형식'만 다양하게 (내용은 반드시 유저의 사실/변명에서 가져오도록 하기 위함)
FORM_HINTS = [
    "숫자가 황당한 반복 횟수형", "공개 낭독형", "금지령형(일정 기간 ~ 금지)", "사회봉사형", "전시·게시형",
    "의무 시청·청취형", "복합형(서로 다른 형벌 2개를 '및'으로 연결)", "자필 반성문형", "기한부 근신형",
]
BANNED = ["이불킥 100회", "기억 소각형", "흑역사 제조기", "감성 과다", "정체불명"]
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


def phase1_prompt(name):
    return f"""당신은 오리지널 B급 법정 아케이드 게임 '이불킥 법정'의 AI 엔진입니다. 피고인 이름: "{name}".
{CAST}
{FACT_RULES}
{EASY_RULES}
[임무] 유저의 [흑역사 원문]을 바탕으로 '제1막: 개정과 1차 심문'을 한국어로 씁니다.
규칙:
1. facts: 먼저 흑역사 원문에서 핵심 사실 2~5개를 '원문에 적힌 표현 그대로' 복사해 적는다. 이후 모든 대사는 이 facts에 기반한다.
2. script는 정확히 7~8줄. 첫 줄은 JUDGE(서판결)의 개정 선언: 원문 내용을 그대로 인용해 사건을 요약하고 무게감 있는 훈계를 한 마디 곁들인다. 이후 PROSECUTOR(차냉정)와 LAWYER(우기기)가 번갈아 공방하며, 중간에 JUDGE가 한 번 끼어들어 사건 내용과 직접 연결된 차분한 훈계를 한다.
3. 템포: 각 dialogue는 반드시 2~3문장, 공백 포함 80~150자의 장문. 한 사람이 자기 논리를 차근차근(주장 → 근거 → 마무리 한 방) 풀어낸다. 짧게 치고 빠지지 말 것. 상대 말을 끊는 느낌은 대사 끝의 '—'로 가끔만 표현.
4. 인물별 말투는 위 등장인물 설정을 엄수한다. 특히 서판결은 반말·뜬금없는 질문·사자성어·고서·고어체 금지.
5. 각 줄의 shout 필드: PROSECUTOR가 상대를 끊고 팩트로 치고 들어갈 때 "FACT", LAWYER가 억지로 반박할 때 "SHIELD", JUDGE가 소란을 정리할 때 "ORDER", 그 외 "NONE". 전체에서 3~4번만 사용.
6. question: 검사 [차냉정]이 피고인에게 던지는 1차 팩폭 질문 (1~2문장, 원문 내용을 구체적으로 짚고, 피고인이 직접 변명을 적어 답할 수 있게).
7. 오직 JSON 객체 하나만 출력. 마크다운, 코드블록, 설명문 금지. 모든 문자열은 큰따옴표.
형식 예시(형식만 참고):
{{"facts":["원문 표현 그대로 1","원문 표현 그대로 2"],"script":[{{"speaker":"JUDGE","dialogue":"...","shout":"NONE"}},{{"speaker":"PROSECUTOR","dialogue":"...","shout":"FACT"}},{{"speaker":"LAWYER","dialogue":"...","shout":"SHIELD"}}],"question":"..."}}"""


def phase2_prompt(name):
    return f"""당신은 오리지널 B급 법정 아케이드 게임 '이불킥 법정'의 AI 엔진입니다. 피고인 이름: "{name}".
{CAST}
{FACT_RULES}
{EASY_RULES}
[임무] 피고인의 1차 변명을 두고 벌어지는 '제2막: 변명 공방과 최후 심문'을 한국어로 씁니다. 입력으로 [흑역사 원문], [확정 사실], 지금까지의 대화, [피고인의 1차 변명]이 주어집니다.
규칙:
1. script는 정확히 6~7줄. LAWYER(우기기)가 피고인의 1차 변명을 눈물겹게 미화·옹호하고, PROSECUTOR(차냉정)가 변명 속 모순과 원문의 사실을 근거로 정밀 타격합니다. 중간에 JUDGE(서판결) 1줄이 사건 내용에 맞는 무게감 있는 훈계로 개입.
2. 피고인의 1차 변명 표현을 대사에서 직접 인용해 반영하고("…라고 변명하셨지요"), 새로운 사건을 지어내지 말 것.
3. 템포: 각 dialogue는 반드시 2~3문장, 공백 포함 80~150자의 장문. 주장 → 근거 → 한 방 순서로 차분히 전개. shout 필드는 1막과 같은 규칙(FACT/SHIELD/ORDER/NONE), 3번 안팎 사용.
4. final_question: 최후 압박 질문. speaker는 "JUDGE" 또는 "PROSECUTOR", text는 1차 변명과 원문을 파고드는 날카로운 1~2문장.
5. 오직 JSON 객체 하나만 출력. 마크다운, 코드블록, 설명문 금지.
형식 예시(형식만 참고):
{{"script":[{{"speaker":"LAWYER","dialogue":"...","shout":"SHIELD"}},{{"speaker":"PROSECUTOR","dialogue":"...","shout":"FACT"}}],"final_question":{{"speaker":"JUDGE","text":"..."}}}}"""


def verdict_system_prompt(name, forms, nonce):
    return f"""당신은 오리지널 B급 법정 아케이드 게임 '이불킥 법정'의 판결 엔진이며, 판사 [서판결]입니다. 피고인 이름: "{name}". 판결 번호: #{nonce}
{CAST}
{FACT_RULES}
{EASY_RULES}
[임무] [흑역사 원문], [확정 사실], 두 번의 공방, 피고인이 직접 적은 1차·최후 변명을 모두 반영해 최종 판결을 내립니다.
[판정 규칙 — 게임의 핵심]
1. defense_score: 0~100 정수. 피고인의 1차·최후 변명이 [확정 사실]과 맞는지, 앞뒤가 일관적인지, 진심이나 재치가 있는지로 채점한다. 점수는 짠 편이다: 대부분 30~70점이고, 80점 이상은 정말 훌륭한 변명에만 준다. 10자 미만의 성의 없는 변명은 40점 이하.
2. ruling: 점수 75 이상이면 "NOT_GUILTY"(무죄), 45~74면 "MITIGATED"(감형), 44 이하면 "GUILTY"(유죄). 점수와 ruling이 반드시 맞아야 한다.
[창작 지시]
3. 죄목·형량·칭호의 '소재'는 반드시 [확정 사실]이나 피고인 변명에 실제로 나온 표현에서만 가져온다. 원문에 없는 물건·인물·장소를 소재로 쓰지 말 것.
4. crime_summary(죄목): 기소된 죄목을 법률 용어를 패러디한 기발한 신조어로 새로 작명(무죄여도 적는다). (예시 '지하철 전동차 내 공개 낭만 유포죄'는 형식만 참고, 그대로 쓰지 말 것)
5. final_sentence(선고): GUILTY면 숫자가 들어간 황당한 형량, MITIGATED면 가볍게 줄어든 황당한 형량, NOT_GUILTY면 반드시 "무죄"로 시작하고 웃긴 훈방 조건을 한 줄 덧붙인다(예: '무죄. 단, 앞으로 ~할 것'). 유죄·감형 문장은 "무죄"로 시작하면 안 된다. 이번 판결의 형식 힌트: [{" / ".join(forms)}]
6. badge(칭호): 맨 앞에 이모지 1개 + 10자 안팎의 칭호. GUILTY는 웃긴 불명예 칭호, MITIGATED는 아슬아슬한 칭호, NOT_GUILTY는 자랑스럽고 웃긴 칭호.
7. 다음 진부한 표현은 금지: {", ".join(BANNED)}
8. script는 JUDGE [서판결]의 선고 대사 3~4줄. 각 줄은 2~3문장, 80~150자. 앞쪽 줄에서 피고인의 변명이 어땠는지 쉬운 말로 평가하고, 마지막 줄에서 판결을 선언한다.
9. verdict_title: 이 판결의 한 줄 제목.
10. 오직 JSON 객체 하나만 출력. 마크다운, 코드블록, 설명문 금지.
형식 예시(형식만 참고):
{{"defense_score":62,"ruling":"MITIGATED","verdict_title":"...","script":[{{"speaker":"JUDGE","dialogue":"..."}}],"summary_card":{{"crime_summary":"...","final_sentence":"...","badge":"🏅 ..."}}}}"""


def to_speaker(raw):
    sp = str(raw or "").upper().strip()
    if sp in SPEAKERS:
        return sp
    for k, v in ALIAS.items():
        if k in str(raw or ""):
            return v
    return "JUDGE"


def parse_script(data):
    steps = []
    items = data.get("script") if isinstance(data, dict) else None
    for it in items or []:
        if not isinstance(it, dict):
            continue
        text = str(it.get("dialogue") or it.get("text") or "").strip()
        if not text:
            continue
        sp = to_speaker(it.get("speaker"))
        k = SHOUT_MAP.get(str(it.get("shout", "")).upper().strip())
        steps.append({"s": sp, "t": text, "c": k[0] if k and k[1] == sp else ""})
    return steps


def auto_shouts(steps):
    """LLM이 외침(shout)을 안 줬을 때, 검사/변호사가 서로 끊고 들어오는 지점에 자동 배정."""
    if any(s["c"] for s in steps):
        return steps
    cnt = {"PROSECUTOR": 0, "LAWYER": 0}
    for k in range(1, len(steps)):
        cur, prev = steps[k], steps[k - 1]
        if cur["s"] in cnt and prev["s"] in cnt and prev["s"] != cur["s"]:
            cnt[cur["s"]] += 1
            if cnt[cur["s"]] % 2 == 1:
                cur["c"] = "F" if cur["s"] == "PROSECUTOR" else "S"
    return steps


def norm_text(t):
    return re.sub(r"\s+", "", str(t or ""))


def validate_script(data, final):
    steps = parse_script(data)
    n = len(steps)
    if n < (3 if final else 5):  # 마지막 시도에서는 완화
        raise ValueError(f"대사가 너무 적습니다({n}줄)")
    avg = sum(len(s["t"]) for s in steps) / n
    if not final and avg < 40:
        raise ValueError(f"대사가 너무 짧습니다(평균 {int(avg)}자, 2~3문장 장문 필요)")


def make_phase1_validator(history):
    src = norm_text(history)

    def v(data, final):
        validate_script(data, final)
        if final:
            return
        facts = [norm_text(f) for f in (data.get("facts") or []) if str(f).strip()]
        if not facts:
            raise ValueError("facts(원문 발췌)가 없습니다")
        if not any(f and f in src for f in facts):
            raise ValueError("facts가 원문과 일치하지 않습니다(내용 왜곡 의심)")

    return v


RULING_LABEL = {"NOT_GUILTY": "무죄", "MITIGATED": "감형", "GUILTY": "유죄"}


def ruling_from_score(score):
    return "NOT_GUILTY" if score >= 75 else ("MITIGATED" if score >= 45 else "GUILTY")


def parse_score(v):
    m = re.search(r"\d+", str(v if v is not None else ""))
    return max(0, min(100, int(m.group()))) if m else None


def to_ruling(raw):
    r = str(raw or "").upper().replace(" ", "").replace("-", "_")
    if "NOT" in r or "무죄" in r:
        return "NOT_GUILTY"
    if "MITIG" in r or "감형" in r:
        return "MITIGATED"
    if "GUILTY" in r or "유죄" in r:
        return "GUILTY"
    return None


def fix_sentence(s, ruling):
    """선고 문구가 판정과 어긋나면 최소한으로 바로잡는다."""
    starts = s.startswith("무죄")
    if ruling == "NOT_GUILTY" and not starts:
        return "무죄. 단, " + s
    if ruling != "NOT_GUILTY" and starts:
        rest = s[2:].lstrip(" .,:·-—")
        return ("감형: " if ruling == "MITIGATED" else "유죄: ") + rest if rest else "유죄. 반성문 제출형"
    return s


def validate_verdict(data, final):
    card = (data.get("summary_card") or {}) if isinstance(data, dict) else {}
    vals = [str(card.get(k) or "").strip() for k in ("crime_summary", "final_sentence", "badge")]
    if not all(vals):
        raise ValueError("판결문 필드가 비어 있습니다")
    if final:
        return
    if any(b in " ".join(vals) for b in BANNED):
        raise ValueError("진부한 표현이 포함되었습니다")
    score = parse_score(data.get("defense_score"))
    if score is None:
        raise ValueError("defense_score가 없습니다")
    ruling = to_ruling(data.get("ruling"))
    if ruling != ruling_from_score(score):
        raise ValueError("판정(ruling)과 점수가 맞지 않습니다")
    if (ruling == "NOT_GUILTY") != vals[1].startswith("무죄"):
        raise ValueError("선고 문구가 판정과 맞지 않습니다")


def normalize_phase1(data, history):
    steps = auto_shouts(parse_script(data))
    if not steps:
        raise ValueError("대사가 비어 있습니다")
    src = norm_text(history)
    facts = [str(f).strip() for f in (data.get("facts") or []) if str(f).strip() and norm_text(f) in src]
    if not facts:  # 검증된 발췌가 없으면 원문 자체를 사실 근거로 사용 (왜곡 방지)
        facts = [history.strip()[:120]]
    q = str(data.get("question") or (data.get("interrogation") or {}).get("question") or "").strip()
    q = q or "피고인! 지금 적으신 그 행동, 당시에 말려 준 사람은 정말 단 한 명도 없었습니까?"
    steps.append({"s": "PROSECUTOR", "t": q, "c": ""})
    return {"steps": steps, "question": q, "facts": facts}


def normalize_phase2(data):
    steps = auto_shouts(parse_script(data))
    if not steps:
        raise ValueError("대사가 비어 있습니다")
    fq = data.get("final_question") or {}
    sp = to_speaker(fq.get("speaker"))
    sp = sp if sp in ("JUDGE", "PROSECUTOR") else "JUDGE"
    text = str(fq.get("text") or "").strip() or "마지막으로 묻겠습니다. 지금 돌아보면 그 선택을 어떻게 평가하십니까?"
    steps.append({"s": sp, "t": text, "c": ""})
    return {"steps": steps, "question": text}


def normalize_verdict(data, ex1="", ex2=""):
    card = data.get("summary_card") or {}
    steps = [
        {"s": "JUDGE", "t": str(i["dialogue"]), "c": ""}
        for i in (data.get("script") or [])
        if isinstance(i, dict) and i.get("dialogue")
    ] or [{"s": "JUDGE", "t": random.choice([
        "이 사건은 기록으로 남았습니다. 다만 피고인이 사실을 숨기지 않고 밝힌 점은 참작하겠습니다.",
        "지나간 일이라도 말과 행동에는 책임이 따르는 법입니다. 이제 판결을 선고하겠습니다.",
    ]), "c": ""}]
    score = parse_score(data.get("defense_score"))
    if score is None:  # 점수가 없으면 ruling으로 추정, 그것도 없으면 무작위
        score = {"NOT_GUILTY": 80, "MITIGATED": 60, "GUILTY": 30}.get(to_ruling(data.get("ruling")), random.randint(30, 70))
    n1, n2 = len(str(ex1).strip()), len(str(ex2).strip())
    if n1 < 10 and n2 < 10:  # 성의 없는 변명은 상한을 둔다
        score = min(score, 40)
    elif n1 < 10 or n2 < 10:
        score = min(score, 70)
    ruling = ruling_from_score(score)
    fallback_sentence = {
        "GUILTY": random.choice([f"자필 반성문 {random.randint(3, 30)}장 공개 낭독형", f"{random.randint(30, 500)}일간 감성 글 작성 금지형"]),
        "MITIGATED": random.choice([f"가벼운 반성문 {random.randint(1, 5)}장 제출형", f"{random.randint(3, 20)}일간 새벽 감성 글 임시저장형"]),
        "NOT_GUILTY": "무죄. 단, 앞으로 새벽에는 감성 글을 임시저장만 할 것",
    }[ruling]
    fallback_badge = {
        "GUILTY": ["🥀 새벽 감성 장인", "🥇 알림음 파괴자", "🎖️ 이불킥 생존자"],
        "MITIGATED": ["🩹 아슬아슬 감형러", "🍀 운 좋은 피고인"],
        "NOT_GUILTY": ["🏅 변명의 달인", "🌟 평판 방어왕"],
    }[ruling]
    sentence = fix_sentence(str(card.get("final_sentence") or "").strip() or fallback_sentence, ruling)
    return {
        "steps": steps,
        "title": data.get("verdict_title") or random.choice(["서판결 법정 판결", "이불킥 사건 판결"]),
        "crime": card.get("crime_summary") or random.choice(["새벽 감성 급발진 및 알림 테러죄", "공개 낭만 과다 분출 방조죄", "과거 자아 과몰입죄"]),
        "sentence": sentence, "badge": card.get("badge") or random.choice(fallback_badge),
        "score": score, "ruling": ruling,
    }


def transcript(steps):
    return "\n".join(f"{NAME_OF.get(s['s'], '?')}: {s['t']}" for s in steps)


def facts_block(facts):
    return "\n".join(f"- {f}" for f in facts)


LOAD_STEP = {"p1": "제1막 준비 중", "p2": "제2막 준비 중", "verdict": "최종 판결문 작성 중"}
LOAD_HEAD = {"p1": ("⚖️", "개정 준비!"), "p2": ("⚡", "이의 있습니다!"), "verdict": ("🔨", "판결 직전!")}
LOAD_MSGS = {"p1": LOADING_P1, "p2": LOADING_P2, "verdict": LOADING_V}
LOAD_TIPS = [
    "구체적으로 적을수록 공방이 정확해집니다.", "입력하신 내용만 사실로 취급됩니다.",
    "변명은 사실에 맞고 진심일수록 무죄에 가까워져요.", "무료 AI라 조금 느릴 수 있어요. 법정이 열리는 중입니다.",
]


def overlay_html(msg, kind, el, tip):
    icon, head = LOAD_HEAD[kind]
    return (
        '<style>html,body,.stApp{overflow:hidden !important}</style><div class="lf"><div class="lf-in">'
        f'<div class="lf-icon">{icon}</div><div class="lf-head">{html.escape(head)}</div>'
        f'<div class="lf-step">{html.escape(LOAD_STEP[kind])}</div>'
        f'<div class="lf-msg">{html.escape(msg)}{"." * (el % 3 + 1)}</div><div class="lf-bar"><i></i></div>'
        f'<div class="lf-meta">경과 {el}초</div><div class="lf-tip">💡 {html.escape(tip)}</div></div></div>'
    )


def run_with_overlay(kind, fn, *args, **kwargs):
    """LLM 호출을 별도 스레드에서 돌리는 동안, 화면 전체를 덮는 독립 로딩 연출을 보여준다."""
    box = st.empty()
    start = time.time()
    msgs = random.sample(LOAD_MSGS[kind], len(LOAD_MSGS[kind]))
    tip = random.choice(LOAD_TIPS)
    try:
        with cf.ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(fn, *args, **kwargs)
            while not fut.done():
                el = int(time.time() - start)
                box.markdown(overlay_html(msgs[(el // 3) % len(msgs)], kind, el, tip), unsafe_allow_html=True)
                time.sleep(0.5)
            return fut.result()
    finally:
        box.empty()


# =================================================================
# 3. 비주얼 노벨 연출 엔진 (iframe 안에서 동작: 카메라 무빙 / 타이핑 / 망치 / 판결문 팝업)
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
# 3-b. 1인칭 법원 계단 스토리 (iframe 연출: 올려다보기 → 뚜벅뚜벅 계단 → 문 열림 → 게임 목적)
#      * 법원 건물/인물은 모두 CSS·SVG로 직접 그린 오리지널 도트풍 그래픽입니다. (실제 사진·로고 미사용)
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
#dlg{position:absolute;left:3%;right:3%;bottom:3%;min-height:28%;z-index:10;background:#fff;box-shadow:0 -4px 0 var(--ink),0 4px 0 var(--ink),-4px 0 0 var(--ink),4px 0 0 var(--ink),0 10px 0 0 #0008}
#dlgin{position:absolute;inset:4px;overflow:auto;background:#1a2358;box-shadow:inset 0 4px 0 #3b4a9a,inset 0 -4px 0 #0e1438}
#tag{position:absolute;left:14px;top:-24px;z-index:2;padding:4px;background:var(--ink)}
#tagin{padding:4px 14px;color:#2b1a00;font-weight:700;font-size:14px;background:#ffd23f;box-shadow:inset 0 3px 0 #fff4b8,inset 0 -3px 0 #d98e00}
#txt{padding:20px 44px 14px 20px;color:#fff;font-size:clamp(15px,3.8vw,19px);line-height:1.7;word-break:keep-all;text-shadow:2px 2px 0 #000}
#arrow{position:absolute;right:16px;bottom:8px;color:#ffd23f;font-size:26px;font-weight:700;animation:blink .8s steps(2) infinite;visibility:hidden}
#start{position:absolute;inset:0;z-index:50;background:radial-gradient(#26307a,#05070f);display:flex;flex-direction:column;align-items:center;justify-content:center;color:#fff;text-align:center;cursor:pointer}
#start h2{font-size:clamp(24px,7vw,34px);color:#ffd23f;-webkit-text-stroke:3px var(--ink);paint-order:stroke fill;text-shadow:4px 4px 0 #ff4d4d;letter-spacing:2px}
#start p{margin-top:16px;color:#9fe8ff;font-family:'Press Start 2P',monospace;font-size:11px;animation:blink 1s steps(2) infinite}
#start small{margin-top:10px;color:#b8c4e8}
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
 <div id="door"><div id="sil">👴🧊🤪</div><div class="dl"></div><div class="dr"></div></div>
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
 {k:'t',x:'…와.'},
 {k:'t',x:'눈앞에 거대한 법원이 우뚝 서 있다. 고개를 한참 젖혀야 꼭대기가 보인다.'},
 {k:'t',x:'저 둥근 문양 아래가 오늘 내가 서야 할 곳. 손에는 구겨진 소환장 한 장이 들려 있다.'},
 {k:'s',x:'뚜벅… 계단이 생각보다 높다.'},
 {k:'s',x:'뚜벅… 심장이 벌써 쿵쿵 뛴다.'},
 {k:'s',x:'뚜벅… 그날 올린 그 글, 그 한마디가 자꾸 떠오른다.'},
 {k:'s',x:'뚜벅… 지금도 생각하면 발가락이 오그라든다.'},
 {k:'s',x:'뚜벅… 다들 이미 잊었길 바랐는데.'},
 {k:'s',x:'뚜벅… 누군가는 분명 캡처해 뒀겠지.'},
 {k:'s',x:'뚜벅… 내 평판은 그날 이후로 바닥을 기고 있다.'},
 {k:'s',x:'뚜벅… 이제 도망칠 곳도 없다. 한 계단만 더.'},
 {k:'s',x:'뚜벅… 드디어, 문 앞이다.'},
 {k:'d',x:'끼이이익—! 무겁고 커다란 문이 천천히 열렸다.'},
 {k:'t',x:'안에서 세 사람이 나를 바라보고 있었다. 판사 서판결, 검사 차냉정, 변호사 우기기.'},
 {k:'t',x:'나는 안다. 그날의 흑역사 때문에 내 평판과 이불킥 랭크는 이미 바닥을 기고 있다는 것을.'},
 {k:'g',x:'그래서 오늘의 목표는 단 하나! 어떻게든 무죄를 받아내서, 평판과 이불킥 랭크를 지켜내는 것이다!'},
 {k:'g',x:'무죄를 연달아 받아내면… 최고 랭크 👑 [이불킥 청정수]가 될 수도 있다고 한다.'},
 {k:'t',x:'…좋아. 심호흡을 하고 한 발 내디뎠다. 이제, 법정 안으로 들어가 보자.'}
];
const STEPS=S.filter(e=>e.k==='s').length;
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
function setTag(k){$('tagin').textContent=(k==='g')?'다짐':'나'}
function stopType(){clearInterval(tm);typing=false;$('txt').textContent=full;$('dlgin').scrollTop=$('dlgin').scrollHeight;$('arrow').style.visibility='visible';
 if(i===S.length-1){ended=true;$('end').style.display='block';$('replay').style.display='block';$('stepbar').style.display='none'}else queueAuto()}
function type(t){typing=true;full=t;let k=0;$('txt').textContent='';$('arrow').style.visibility='hidden';tm=setInterval(()=>{k++;$('txt').textContent=t.slice(0,k);$('dlgin').scrollTop=$('dlgin').scrollHeight;if(k%2===0)beep(420+Math.random()*100,.035);if(k>=t.length)stopType()},D.speed||30)}
function queueAuto(){clearTimeout(at);if(!auto||ended)return;at=setTimeout(()=>{if(!typing&&!busy)adv()},1700)}
function popText(t,alt){const p=$('pop');p.textContent=t;p.style.marginLeft=alt?'-60px':'60px';p.classList.remove('on');void p.offsetWidth;p.classList.add('on')}
function bob(){const c=$('cam');c.classList.remove('bob');void c.offsetWidth;c.classList.add('bob')}
function flash(){const f=$('flash');f.classList.remove('on');void f.offsetWidth;f.classList.add('on')}
function show(n){const e=S[n];busy=true;clearTimeout(at);setTag(e.k);$('txt').textContent='';$('arrow').style.visibility='hidden';let wait=250;
 if(e.k==='s'){sn++;scene.style.setProperty('--k',sn);$('sn').textContent=sn;$('stepbar').style.display='block';bob();popText(sn%2?'뚜벅…':'뚜벅!',sn%2);footstep(sn);wait=700}
 else if(e.k==='d'){$('stepbar').style.display='none';const d=$('door');d.style.display='block';void d.offsetWidth;d.classList.add('open');creak();wait=1900}
 else if(e.k==='g'){flash();popText('🎯 목표!',0);[660,880,1320].forEach((f,j)=>setTimeout(()=>beep(f,.22,.06),j*140));wait=800}
 setTimeout(()=>{busy=false;type(e.x)},wait)}
function adv(){if(!started||busy||ended)return;clearTimeout(at);if(typing){stopType();return}if(i<S.length-1){i++;show(i)}}
function reset(){clearTimeout(at);clearInterval(tm);i=-1;sn=0;ended=false;typing=false;busy=false;scene.style.setProperty('--k',0);$('door').style.display='none';$('door').classList.remove('open');
 $('end').style.display='none';$('replay').style.display='none';$('stepbar').style.display='none';$('txt').textContent='';i=0;show(0)}
$('replay').onclick=e=>{e.stopPropagation();reset()};
scene.addEventListener('click',adv);
document.addEventListener('keydown',e=>{if(e.code==='Space'||e.code==='Enter'){e.preventDefault();adv()}});
$('start').addEventListener('click',e=>{e.stopPropagation();started=true;ac();beep(880,.12);$('start').style.display='none';i=0;show(0)});
</script></body></html>"""


def render_story(mute=False, speed=30, height=640):
    payload = json.dumps({"mute": mute, "speed": speed}, ensure_ascii=False).replace("</", "<\\/")
    components.html(STORY_TEMPLATE.replace("__DATA__", payload), height=height, scrolling=False)


# =================================================================
# 4. 세션 / 프로필 / HUD / 화면 흐름
#    TITLE →(STORY)→ LOBBY → INPUT →(LOADING)→ DEBATE1 →(LOADING)→ DEBATE2 →(LOADING)→ VERDICT
#    로그인 없음 · 브라우저 세션 단위 '앱 맛보기' (새로고침하면 프로필과 기록이 초기화됩니다)
# =================================================================
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
VN_H = 640  # 세로형 연출 화면 높이

ss = st.session_state
ss.setdefault("stage", "TITLE")
ss.setdefault("user_name", "익명의 피고인")
ss.setdefault("error", "")
ss.setdefault("fee", FEE_MAX)
ss.setdefault("fee_ts", None)
ss.setdefault("daily_claimed", False)
ss.setdefault("story_seen", False)
ss.setdefault("profile", {"rep": REP_START, "trials": 0, "wins": 0, "streak": 0, "records": [], "badges": []})
ss.setdefault("sound_on", True)  # 위젯 key와 분리된 '진짜' 설정값 (위젯 상태가 정리돼도 유지됨)
ss.setdefault("speed_label", "보통")
ss.setdefault("profile_tab", "🎖️ 칭호")
RUN_KEYS = ("p1", "p2", "ex1", "ex2", "facts", "verdict_data", "history_text", "case_name", "result", "show_result", "job")


def new_profile():
    return {"rep": REP_START, "trials": 0, "wins": 0, "streak": 0, "records": [], "badges": []}


def rank_info(rep):
    """(인덱스, 아이콘, 이름, 현재 구간 시작점, 다음 랭크 시작점 or None)"""
    idx = 0
    for i, (th, _, _) in enumerate(RANKS):
        if rep >= th:
            idx = i
    nxt = RANKS[idx + 1][0] if idx + 1 < len(RANKS) else None
    return idx, RANKS[idx][1], RANKS[idx][2], RANKS[idx][0], nxt


def rank_label(rep):
    _, icon, name, _, _ = rank_info(rep)
    return f"{icon} {name}"


def regen_fee():
    if ss["fee"] >= FEE_MAX:
        ss["fee"], ss["fee_ts"] = FEE_MAX, None
        return
    if ss["fee_ts"] is None:
        ss["fee_ts"] = time.time()
        return
    gained = int((time.time() - ss["fee_ts"]) // REGEN_SEC)
    if gained > 0:
        ss["fee"] = min(FEE_MAX, ss["fee"] + gained)
        ss["fee_ts"] = None if ss["fee"] >= FEE_MAX else ss["fee_ts"] + gained * REGEN_SEC


def fee_eta():
    if ss["fee"] >= FEE_MAX or ss["fee_ts"] is None:
        return None
    return max(0, int(REGEN_SEC - (time.time() - ss["fee_ts"])))


def spend_fee():
    ss["fee"] = max(0, ss["fee"] - 1)
    if ss["fee_ts"] is None:
        ss["fee_ts"] = time.time()


def add_fee(n=1):
    ss["fee"] = min(FEE_MAX, ss["fee"] + n)
    if ss["fee"] >= FEE_MAX:
        ss["fee_ts"] = None


def go(stage):
    ss["stage"] = stage
    ss["error"] = ""
    st.rerun()


def reset_run():
    for k in RUN_KEYS:
        ss.pop(k, None)


def show_error():
    if ss["error"]:
        st.error("😴 AI 법정이 응답하지 못했습니다. (선임비는 차감되지 않았습니다) 다시 시도해 주세요.")
        with st.expander("상세 에러 보기"):
            st.code(ss["error"])


def key_guard():
    """API 키가 없을 때 보여줄 깔끔한 안내. (키 값은 절대 화면/로그에 노출하지 않는다)"""
    if KEY_FORMAT_OK:
        return True
    st.markdown(
        '<div class="keybox"><b>🔑 API 키 설정이 필요해요</b><br>'
        '이 게임은 OpenRouter AI를 사용합니다. 관리자가 <code>OPENROUTER_API_KEY</code>를 Streamlit Secrets에 등록해야 재판을 열 수 있어요.</div>',
        unsafe_allow_html=True,
    )
    with st.expander("관리자용 설정 방법"):
        st.markdown(
            "1. **로컬 실행:** 프로젝트 폴더에 `.streamlit/secrets.toml` 파일을 만들고 아래처럼 한 줄을 적습니다.\n"
            "2. **Streamlit Community Cloud 배포:** 앱 설정 → **Secrets** 칸에 같은 한 줄을 붙여넣습니다.\n"
            "3. 저장 후 앱을 다시 실행합니다."
        )
        st.code('OPENROUTER_API_KEY = "여기에_발급받은_키"', language="toml")
        st.caption("⚠️ `.streamlit/` 폴더는 반드시 `.gitignore`에 추가하세요. 키를 코드나 GitHub에 올리지 마세요.")
    return False


def watch_ad():
    """광고 시청 → 선임비 +1 충전 연출. (실제 광고가 아닌 데모 연출입니다)"""
    bar = st.progress(0, text="📺 [광고] 우기기 변호사 사무소 — 억지도 법이다! (연출용 가상 광고)")
    for i in range(1, 41):
        time.sleep(0.1)
        bar.progress(i / 40, text=f"📺 [광고] 우기기 변호사 사무소 — 억지도 법이다! ({4 - i // 10}초)")
    add_fee(1)
    ss["toast"] = "✅ 변호사 선임비가 +1 충전되었습니다!"
    st.rerun()


def finish_trial():
    """판결 확정 → 평판 / 연승 / 랭크 / 칭호 / 기록 반영 (세션 단위)"""
    p = ss["profile"]
    rep_before = p["rep"]
    rb = rank_info(rep_before)[0]
    v = ss["verdict_data"]
    if v["ruling"] == "NOT_GUILTY":
        p["streak"] = p.get("streak", 0) + 1
        p["wins"] += 1
        bonus = min(max(p["streak"] - 1, 0) * STREAK_BONUS, 30)
    else:  # 감형·유죄는 연승이 끊긴다
        p["streak"] = 0
        bonus = 0
    p["rep"] = max(0, rep_before + RULING_DELTA[v["ruling"]] + v["score"] // 20 + bonus)
    p["trials"] += 1
    if v["badge"] not in p["badges"]:
        p["badges"].append(v["badge"])
    ra = rank_info(p["rep"])[0]
    res = {
        "delta": p["rep"] - rep_before, "rep_before": rep_before, "rep_after": p["rep"],
        "rank_before": rank_label(rep_before), "rank_after": rank_label(p["rep"]),
        "dir": (ra > rb) - (ra < rb), "streak": p["streak"], "score": v["score"], "ruling": RULING_LABEL[v["ruling"]],
    }
    p["records"].append({
        "ts": time.strftime("%m/%d %H:%M"), "name": ss["case_name"], "history": ss["history_text"],
        "ex1": ss.get("ex1", ""), "ex2": ss.get("ex2", ""), "verdict": v, "res": res,
    })
    p["records"] = p["records"][-20:]
    ss["result"], ss["show_result"] = res, False


def load_record(rec):
    ss["case_name"] = rec.get("name", ss["user_name"])
    ss["history_text"] = rec.get("history", "")
    ss["ex1"], ss["ex2"] = rec.get("ex1", ""), rec.get("ex2", "")
    ss["verdict_data"] = rec["verdict"]
    ss["result"], ss["show_result"] = rec.get("res"), False
    go("VERDICT")


# ---------------- 모달(프로필 / 설정 / 상점) ----------------
@st.dialog("👤 내 프로필")
def profile_dialog():
    p = ss["profile"]
    _, icon, rname, cur, nxt = rank_info(p["rep"])
    st.markdown(f"### {icon} {rname}")
    st.write(
        f"🏆 평판 **{p['rep']}점** · 🔥 연속 무죄 **{p.get('streak', 0)}회** · ⚖️ 재판 **{p['trials']}회** · "
        f"✅ 무죄 **{p['wins']}회** · 🎖️ 칭호 **{len(p['badges'])}개**"
    )
    if nxt is not None:
        st.progress(min((p["rep"] - cur) / (nxt - cur), 1.0), text=f"다음 랭크까지 평판 {nxt - p['rep']}점")
    else:
        st.caption("👑 최고 랭크 달성! 이 명예로운 평판을 지켜내세요.")
    st.caption("랭크 기준: 👑 이불킥 청정수 200↑ · 🟢 정상인 120↑ · 🟡 새벽 감성러 60↑ · 🟠 이불킥 장인 20↑ · 🔴 인간 흑역사 박물관")
    st.caption("💡 무죄를 연달아 받으면 연승 보너스(+10, +20, +30)가 붙어요!")
    tabs = ["🎖️ 칭호", "📚 흑역사 기록"]
    tab = st.radio("탭", tabs, index=tabs.index(ss["profile_tab"]), horizontal=True, label_visibility="collapsed", key="rad_prof")
    ss["profile_tab"] = tab  # 탭 상태를 세션에 보관
    if tab == tabs[0]:
        if p["badges"]:
            for b in reversed(p["badges"]):
                st.markdown(f"- {b}")
        else:
            st.caption("아직 받은 칭호가 없습니다. 첫 재판을 받아 보세요!")
    else:
        if not p["records"]:
            st.caption("아직 기록이 없습니다.")
        for i, rec in enumerate(reversed(p["records"])):
            v = rec["verdict"]
            with st.expander(f"{rec['ts']} · {RULING_LABEL[v['ruling']]} · {v['badge']}"):
                st.write(f"**죄목** {v['crime']}")
                st.write(f"**선고** {v['sentence']}")
                if rec.get("res"):
                    st.write(f"**평판** {rec['res']['delta']:+d}점 ({rec['res']['rank_after']})")
                st.caption("흑역사: " + (rec["history"][:80] + ("…" if len(rec["history"]) > 80 else "")))
                if st.button("▶ 판결 다시 보기", key=f"rec_{i}"):
                    load_record(rec)
    st.caption("※ 로그인 없는 맛보기 모드라서 새로고침하거나 창을 닫으면 기록이 사라집니다.")


@st.dialog("⚙️ 설정")
def settings_dialog():
    nick = st.text_input("닉네임", value=ss["user_name"], max_chars=12, key="w_nick")
    if st.button("닉네임 저장", key="w_nicksave"):
        ss["user_name"] = nick.strip() or ss["user_name"]
        st.rerun()
    ss["sound_on"] = st.toggle("🔊 효과음", value=ss["sound_on"], key="w_snd")
    ss["speed_label"] = st.select_slider("⌨️ 대사 글자 속도", options=list(SPEED_MS), value=ss["speed_label"], key="w_spd")
    st.caption("효과음·글자 속도는 다음 장면부터 적용됩니다.")
    st.divider()
    if st.button("📖 스토리 다시 보기", key="w_story"):
        go("STORY")
    if st.button("🔌 API 연결 테스트", key="w_api"):
        if not KEY_FORMAT_OK:
            st.error("API 키가 설정되지 않았습니다. (Streamlit Secrets의 OPENROUTER_API_KEY)")
        else:
            try:
                with st.spinner("연결 확인 중..."):
                    r = make_client().chat.completions.create(
                        model=MODEL_CANDIDATES[0], messages=[{"role": "user", "content": "한 단어로 인사해줘."}], max_tokens=200,
                    )
                st.success(f"✅ 연결 성공! 응답 모델: {getattr(r, 'model', '?')}")
            except AuthenticationError:
                st.error("❌ 401: 키가 잘못되었거나 삭제되었습니다.")
            except Exception as e:
                st.error(f"❌ 실패: {type(e).__name__}: {str(e)[:200]}")
    st.divider()
    sure = st.checkbox("내 평판과 기록을 모두 지우는 데 동의합니다", key="w_sure")
    if st.button("🧹 기록 초기화", key="w_reset", disabled=not sure):
        ss["profile"] = new_profile()
        ss["toast"] = "🧹 기록이 초기화되었습니다."
        st.rerun()


@st.dialog("🛒 상점")
def shop_dialog():
    regen_fee()
    full = ss["fee"] >= FEE_MAX
    st.markdown(f"### ⚖️ 변호사 선임비 {ss['fee']}/{FEE_MAX}")
    eta = fee_eta()
    st.caption("⏳ 자동 충전: 10분마다 +1" + (f" (다음 +1까지 {eta // 60}:{eta % 60:02d})" if eta is not None else ""))
    if full:
        st.info("선임비가 가득 찼습니다. 우기기 변호사가 의욕 만렙입니다!")
    st.markdown("**📺 광고 보고 충전 (+1)**")
    st.caption("연출용 가상 광고입니다. 4초 뒤 선임비가 충전됩니다.")
    if st.button("광고 보기", key="shop_ad", disabled=full, use_container_width=True):
        watch_ad()
    st.markdown("**🎁 오늘의 출석 보상 (+1)**")
    if st.button("보상 받기" if not ss["daily_claimed"] else "오늘은 이미 받았습니다", key="shop_daily",
                 disabled=full or ss["daily_claimed"], use_container_width=True):
        ss["daily_claimed"] = True
        add_fee(1)
        ss["toast"] = "🎁 출석 보상! 선임비 +1"
        st.rerun()
    st.markdown("**💳 선임비 3개 팩**")
    st.button("준비 중 (정식 앱에서 제공 예정)", key="shop_pack", disabled=True, use_container_width=True)
    st.caption("이 데모에는 실제 결제가 없습니다.")


def render_hud():
    regen_fee()
    p = ss["profile"]
    _, icon, rname, _, _ = rank_info(p["rep"])
    pips = "".join(f'<i class="pip{" on" if k < ss["fee"] else ""}"></i>' for k in range(FEE_MAX))
    eta = fee_eta()
    eta_html = f' <span class="eta">+1 {eta // 60}:{eta % 60:02d}</span>' if eta is not None else ""
    low = " low" if ss["fee"] <= 0 else ""
    fire = f' <span class="h-fire">🔥{p["streak"]}</span>' if p.get("streak", 0) >= 2 else ""
    with st.container(key="hud"):
        c1, c2, c3, c4 = st.columns([6.4, 1, 1, 1])
        c1.markdown(
            f'<div class="hud2"><div class="h-l1">👤 <b>{html.escape(ss["user_name"])}</b>'
            f'<span class="h-title">🏆 평판 {p["rep"]}</span>{fire}</div>'
            f'<div class="h-l2"><span class="h-rank">{icon} {html.escape(rname)}</span>'
            f'<span class="h-fee{low}">⚖️ <span class="pips">{pips}</span> {ss["fee"]}/{FEE_MAX}{eta_html}</span></div></div>',
            unsafe_allow_html=True,
        )
        if c2.button("⚙️", key="hud_set", help="설정"):
            settings_dialog()
        if c3.button("👤", key="hud_prof", help="프로필"):
            profile_dialog()
        if c4.button("🛒", key="hud_shop", help="상점 (선임비 충전)"):
            shop_dialog()


def vn_opts():
    return {"mute": not ss["sound_on"], "speed": SPEED_MS.get(ss["speed_label"], 30)}


def case_header():
    return (
        f"[피고인] {ss['case_name']}\n[흑역사 원문]\n\"\"\"\n{ss['history_text']}\n\"\"\"\n"
        f"[확정 사실 — 이것만 사실로 취급]\n{facts_block(ss.get('facts', []))}\n"
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


# ---------------- 로딩 단계 (독립 풀스크린 화면) ----------------
def start_job(kind, back):
    ss["job"] = {"kind": kind, "back": back}
    go("LOADING")


def build_call(kind):
    if kind == "p1":
        return (
            (phase1_prompt(ss["case_name"]), f"[피고인] {ss['case_name']}\n[흑역사 원문]\n\"\"\"\n{ss['history_text']}\n\"\"\""),
            dict(max_tokens=3500, temperature=0.8, validate=make_phase1_validator(ss["history_text"])),
        )
    if kind == "p2":
        return (
            (phase2_prompt(ss["case_name"]),
             f"{case_header()}\n[제1막 대화]\n{transcript(ss['p1']['steps'])}\n\n[피고인의 1차 변명]\n{ss['ex1']}"),
            dict(max_tokens=3500, temperature=0.8, validate=validate_script),
        )
    return (
        (verdict_system_prompt(ss["case_name"], random.sample(FORM_HINTS, 2), random.randint(1000, 9999)),
         f"{case_header()}\n[제1막 대화]\n{transcript(ss['p1']['steps'])}\n[피고인의 1차 변명]\n{ss['ex1']}\n\n"
         f"[제2막 대화]\n{transcript(ss['p2']['steps'])}\n[피고인의 최후 변명]\n{ss['ex2']}\n\n"
         f"[변명 성의도 참고] 1차 변명 {len(ss['ex1'].strip())}자, 최후 변명 {len(ss['ex2'].strip())}자 (10자 미만이면 성의 부족)"),
        dict(max_tokens=2500, temperature=1.0, validate=validate_verdict),
    )


def apply_result(kind, raw):
    """결과를 세션에 반영하고 다음 화면 이름을 반환"""
    if kind == "p1":
        p1 = normalize_phase1(raw, ss["history_text"])
        ss["facts"], ss["p1"] = p1["facts"], p1
        spend_fee()  # 성공했을 때만 선임비 차감
        return "DEBATE1"
    if kind == "p2":
        ss["p2"] = normalize_phase2(raw)
        return "DEBATE2"
    ss["verdict_data"] = normalize_verdict(raw, ss.get("ex1", ""), ss.get("ex2", ""))
    finish_trial()
    return "VERDICT"


TITLE_HTML = (
    '<div class="ts"><div class="ts-wall"></div><div class="ts-pil l"></div><div class="ts-pil r"></div>'
    '<div class="ts-seal">法</div><div class="ts-bench"></div><div class="ts-floor"></div>'
    '<div class="ts-logo"><small>― 오리지널 B급 법정 아케이드 ―</small><h1>이불킥<br>법정</h1>'
    '<em>KICK-THE-BLANKET COURT</em></div><div class="ts-crt"></div>'
    '<div class="ts-copy">모든 캐릭터·세계관·그래픽은 이 게임을 위해 새로 창작한 오리지널입니다</div></div>'
)
LOBBY_TIPS = [
    "흑역사를 구체적으로 적을수록 공방이 정확해집니다.",
    "입력하신 내용만 사실로 취급됩니다. 없는 얘기는 법정도 지어내지 않아요.",
    "변명은 사실에 맞게, 진심을 담아 쓸수록 무죄에 가까워져요.",
    "무죄를 연달아 받으면 연승 보너스! 3연승이면 👑 이불킥 청정수도 노려볼 수 있어요.",
]

stage = ss["stage"]
if ss.get("toast"):
    st.toast(ss.pop("toast"))
# 판결 연출이 끝나기 전에는 HUD를 숨겨서 결과(평판/랭크)가 미리 보이지 않게 한다
hud_hidden = stage in ("TITLE", "STORY", "LOADING", "QUIT") or (stage == "VERDICT" and not ss.get("show_result"))
if not hud_hidden:
    render_hud()

# ---------------- TITLE ----------------
if stage == "TITLE":
    st.markdown(TITLE_HTML, unsafe_allow_html=True)
    with st.container(key="menu"):
        if st.button("▶ 시  작", use_container_width=True, key="b_start"):
            reset_run()
            go("LOBBY")
        if st.button("📖 스토리 보기" + ("" if ss["story_seen"] else " ✨"), use_container_width=True, key="b_story"):
            go("STORY")
        if st.button("종  료", use_container_width=True, key="b_quit"):
            go("QUIT")

# ---------------- STORY (1인칭 법원 계단 스토리) ----------------
elif stage == "STORY":
    render_story(height=VN_H, **vn_opts())
    st.caption("▶ 화면을 클릭하면 빨리 넘어가요. 이야기가 끝나면 아래 버튼으로 입장하세요.")
    with st.container(key="story_nav"):
        s1, s2 = st.columns([1, 1.4])
        if s1.button("◀ 타이틀", use_container_width=True, key="st_back"):
            go("TITLE")
        if s2.button("🏛️ 로비로 입장", use_container_width=True, key="st_enter"):
            ss["story_seen"] = True
            go("LOBBY")

# ---------------- LOBBY ----------------
elif stage == "LOBBY":
    st.markdown(
        '<div class="lobby-hero"><div class="stars"></div><div class="bldg">🏛️</div>'
        '<div class="lh-t">오늘의 법정이 열렸습니다<small>무죄를 받아내고 평판을 지켜 보세요!</small></div></div>',
        unsafe_allow_html=True,
    )
    ready = key_guard()
    if ss["fee"] <= 0:
        eta = fee_eta() or 0
        st.markdown(
            '<div class="loading" style="color:#ff9b9b">💸 변호사 선임비가 바닥났습니다!'
            '<small>우기기 변호사가 "선임비 없으면 억지도 없다"며 퇴장했습니다 · '
            f'자동 충전까지 {eta // 60}:{eta % 60:02d} · 🛒 상점에서 충전할 수 있어요</small></div>',
            unsafe_allow_html=True,
        )
    with st.container(key="lobby_main"):
        if st.button("⚖️ 소장 접수 (재판 시작)", use_container_width=True, key="b_court", disabled=ss["fee"] <= 0 or not ready):
            reset_run()
            go("INPUT")
    st.markdown(f'<div class="tip">💡 {random.choice(LOBBY_TIPS)} · 재판 1회에 선임비 1 소모</div>', unsafe_allow_html=True)
    with st.container(key="nav3"):
        n1, n2, n3 = st.columns(3)
        if n1.button("⚙️ 설정", use_container_width=True, key="nav_set"):
            settings_dialog()
        if n2.button("👤 프로필", use_container_width=True, key="nav_prof"):
            profile_dialog()
        if n3.button("🛒 상점", use_container_width=True, key="nav_shop"):
            shop_dialog()
    if st.button("◀ 타이틀로", key="b_to_title"):
        go("TITLE")

# ---------------- INPUT ----------------
elif stage == "INPUT":
    st.markdown('<div class="doc-head">소 장 접 수<small>― 흑역사를 고발하라 ―</small></div>', unsafe_allow_html=True)
    ready = key_guard()
    with st.container(key="paper"):
        name = st.text_input("피고인 성명 (닉네임)", value=ss["user_name"], max_chars=12)
        history = st.text_area(
            "흑역사 내용 (1,000자 제한)", value=ss.get("history_text", ""), max_chars=1000, height=170,
            placeholder="예: 새벽 2시에 감성에 젖어 싸이월드 감성 글을 올렸습니다...",
        )
        st.caption("※ 입력한 내용만 사실로 취급됩니다. 상황이 구체적일수록 공방이 더 정확해집니다. · 재판 1회에 변호사 선임비 1이 듭니다.")
        c1, c2 = st.columns(2)
        back = c1.button("◀ 로비", use_container_width=True)
        start = c2.button("⚖️ 재판 개시", use_container_width=True, disabled=ss["fee"] <= 0 or not ready)
    if back:
        go("LOBBY")
    if start:
        ss["user_name"] = name.strip() or "익명의 피고인"
        ss["case_name"] = ss["user_name"]
        if not history.strip():
            st.warning("심판받을 흑역사 내용을 입력해 주세요!")
        else:
            ss["history_text"] = history.strip()
            start_job("p1", "INPUT")
    show_error()

# ---------------- LOADING (풀스크린 로딩/전환 연출) ----------------
elif stage == "LOADING":
    job = ss.get("job")
    if not job:
        go("LOBBY")
    kind, back = job["kind"], job["back"]
    args, kwargs = build_call(kind)
    try:
        raw = run_with_overlay(kind, call_llm_json, *args, **kwargs)
        nxt = apply_result(kind, raw)
        ss.pop("job", None)
        go(nxt)
    except Exception as e:  # 실패하면 원래 화면으로 돌아가 에러를 보여줌 (선임비 차감 없음)
        ss["error"] = str(e)
        ss.pop("job", None)
        ss["stage"] = back
        st.rerun()

# ---------------- DEBATE1 ----------------
elif stage == "DEBATE1":
    render_vn(
        "debate", ss["p1"]["steps"], height=VN_H, title="제1막 · 개정 & 1차 심문",
        phase="제1막 ▸ 1차 심문", hint="🚨 1차 심문! 아래 입력창에 변명을 적어 제출하세요 ▼", **vn_opts(),
    )
    st.caption("▶ 화면을 클릭(터치)하거나 Space/Enter로 대사를 넘기세요. 천천히 읽고, 심문이 끝나면 아래 입력창에 1차 변명을 제출하세요.")
    if st.button("🏳️ 재판 포기 (로비로)", key="giveup1"):
        go("LOBBY")
    show_error()
    ex1 = st.chat_input("1차 변명을 입력하세요 (최대 200자)", key="chat_ex1")
    if ex1 and ex1.strip():
        ss["ex1"] = ex1.strip()[:200]
        start_job("p2", "DEBATE1")

# ---------------- DEBATE2 ----------------
elif stage == "DEBATE2":
    render_vn(
        "debate", ss["p2"]["steps"], height=VN_H, title="제2막 · 변명 공방 & 최후 심문",
        phase="제2막 ▸ 최후 심문", hint="🔥 최후 심문! 아래 입력창에 최후 변명을 제출하세요 ▼", **vn_opts(),
    )
    st.caption("▶ 1차 변명을 두고 벌어지는 공방입니다. 마지막 질문에 최후 변명을 직접 입력하세요. 사실에 맞고 진심이 담길수록 무죄에 가까워요!")
    if st.button("🏳️ 재판 포기 (로비로)", key="giveup2"):
        go("LOBBY")
    show_error()
    ex2 = st.chat_input("최후 변명을 입력하세요 (최대 200자)", key="chat_ex2")
    if ex2 and ex2.strip():
        ss["ex2"] = ex2.strip()[:200]
        start_job("verdict", "DEBATE2")

# ---------------- VERDICT ----------------
elif stage == "VERDICT":
    v = ss["verdict_data"]
    res = ss.get("result")
    card = {
        "title": v["title"], "name": ss.get("case_name") or ss["user_name"], "crime": v["crime"],
        "sentence": v["sentence"], "badge": v["badge"], "ruling": RULING_LABEL[v["ruling"]],
        "res": {
            "delta": res["delta"], "rep_before": res["rep_before"], "rep_after": res["rep_after"],
            "rank_before": res["rank_before"], "rank_after": res["rank_after"], "dir": res["dir"], "streak": res["streak"],
        } if res else None,
    }
    render_vn("verdict", v["steps"], card=card, height=VN_H + 10, title="최종 선고", phase="최종 선고", **vn_opts())
    if res and not ss.get("show_result"):
        st.caption("🎬 판결 연출을 다 보셨다면, 아래 버튼으로 평판·랭크 변화를 확인하세요!")
        if st.button("📊 평판 · 랭크 결과 확인", use_container_width=True, key="b_show_result"):
            ss["show_result"] = True
            st.rerun()
    elif res:
        st.markdown(result_panel_html(res), unsafe_allow_html=True)
        if res["dir"] > 0 and res["rank_after"].startswith("👑"):
            st.balloons()
            st.success("👑 최고 랭크 달성! 당신은 이제 [이불킥 청정수]입니다!")
        elif res["dir"] > 0:
            st.success(f"🎉 랭크 상승! 이제 {res['rank_after']}입니다!")
        elif res["dir"] < 0:
            st.warning(f"😱 랭크 하락… {res['rank_after']}(으)로 떨어졌어요. 다음 재판에서 무죄로 방어하세요!")
    _, c, _ = st.columns([1, 3, 1])
    with c:
        if st.button("🏠 로비로 돌아가기", use_container_width=True, key="b_lobby_back"):
            reset_run()
            go("LOBBY")

# ---------------- QUIT ----------------
else:
    st.markdown(
        '<div class="ts" style="height:360px"><div class="ts-wall" style="background:#05070f"></div>'
        '<div class="ts-logo" style="top:32%"><h1 style="font-size:54px">폐 정!</h1>'
        '<em style="color:#9fe8ff">오늘의 재판은 이것으로 끝났습니다. 이불은 소중히 다뤄 주세요.</em></div>'
        '<div class="ts-crt"></div></div>',
        unsafe_allow_html=True,
    )
    if st.button("다시 입장하기"):
        go("TITLE")