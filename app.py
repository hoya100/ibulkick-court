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

■ 파일 구성 (모듈 분리) ───────────────────────────────────────────
   app.py          화면 라우팅과 UI (이 파일)           ← streamlit run app.py
   config.py       전역 CSS, LLM 설정, 선임비/평판/랭크 정책, 화면 문구
   characters.py   캐릭터(서판결·차냉정·한유리) 설정·외모 데이터, 말투 규칙, 프롬프트
   utils.py        평판·랭크 계산, 선임비 충전, 기록 저장 등 게임 로직
   templates.py    재판/스토리 연출 HTML·JS 템플릿 (카메라 무빙, 사운드, 픽셀 디자인)
   llm_handler.py  OpenRouter 통신, 모델 폴백·재시도, JSON 파싱, 응답 검증
   * 위 6개 파일은 반드시 같은 폴더에 두세요.
───────────────────────────────────────────────────────────────────
"""

import html
import ast
import os
import random
import sys

import streamlit as st

# ── 배포 자가 점검 ──────────────────────────────────────────────────
# 필수 파일/패키지가 빠져 있으면 'ModuleNotFoundError' 대신, 무엇이 없는지 알려 주는 안내 화면을 보여줍니다.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)  # app.py 와 같은 폴더의 모듈을 항상 찾을 수 있게 함
_REQUIRED_FILES = ["config.py", "characters.py", "utils.py", "templates.py", "llm_handler.py", "stage.py", "court_bg.py"]
_present = os.listdir(_HERE)
_missing = []
for _f in _REQUIRED_FILES:
    if _f not in _present:
        _alt = [n for n in _present if n.lower() == _f.lower() or n.lower().startswith(_f.lower() + ".")]
        _missing.append(_f + (f"  (비슷한 이름이 있어요: {', '.join(_alt)} → 이름을 정확히 '{_f}'로 바꿔 주세요)" if _alt else ""))
try:
    import openai  # noqa: F401
except ModuleNotFoundError:
    _missing.append("openai 패키지  (requirements.txt 에 openai 를 추가하세요)")
if _missing:
    st.set_page_config(page_title="이불킥 법정", page_icon="🏛️")
    st.error("🧩 배포 폴더에 필요한 파일/패키지가 빠져 있어요.")
    st.markdown("**없는 것**\n\n" + "\n".join(f"- `{m}`" for m in _missing))
    st.markdown(
        "**해결 방법**\n\n"
        "1. `app.py`, `config.py`, `characters.py`, `utils.py`, `templates.py`, `llm_handler.py` 6개를 **같은 폴더**(GitHub 저장소 최상위)에 올립니다.\n"
        "2. 파일 이름은 소문자 그대로여야 합니다. (리눅스 서버는 대소문자를 구분해요)\n"
        "3. `.gitignore` 에 `config.py` 등이 들어 있지 않은지 확인하고, 커밋/푸시한 뒤 앱을 **Reboot** 하세요."
    )
    with st.expander("서버에 실제로 올라간 파일 목록"):
        st.code("\n".join(sorted(_present)))
    st.stop()

# 파일은 다 있는데 '버전이 서로 안 맞는' 경우(예: app.py 만 최신이고 characters.py 는 옛 버전)도
# ImportError 대신, 어느 파일에 무엇이 없는지 알려 주는 안내 화면을 보여줍니다. (코드를 실행하지 않고 소스만 읽어서 검사)
def _defined_names(path):
    names = set()
    for node in ast.parse(open(path, encoding="utf-8").read()).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            names.update((a.asname or a.name).split(".")[0] for a in node.names)
    return names


_stale = []
for _fname in ["app.py"] + _REQUIRED_FILES:
    try:
        _tree = ast.parse(open(os.path.join(_HERE, _fname), encoding="utf-8").read())
    except (OSError, SyntaxError, UnicodeDecodeError) as _e:
        _stale.append(f"`{_fname}` 을(를) 읽을 수 없습니다 ({type(_e).__name__})")
        continue
    for _node in _tree.body:
        if isinstance(_node, ast.ImportFrom) and _node.level == 0 and _node.module and _node.module + ".py" in _REQUIRED_FILES:
            _have = _defined_names(os.path.join(_HERE, _node.module + ".py"))
            _stale += [
                f"`{_fname}` 이(가) `{_node.module}.py` 의 `{a.name}` 을(를) 쓰려는데, 서버의 `{_node.module}.py` 에는 없습니다"
                for a in _node.names if a.name not in _have
            ]
# 이름은 같아도 '인자(파라미터)'가 옛 버전이면 TypeError 가 나므로, render_vn 의 인자까지 소스로 확인합니다.
try:
    for _n in ast.parse(open(os.path.join(_HERE, "templates.py"), encoding="utf-8").read()).body:
        if isinstance(_n, ast.FunctionDef) and _n.name == "render_vn":
            _args = {a.arg for a in _n.args.args + _n.args.kwonlyargs}
            for _need in ("intro", "opening", "push"):
                if _need not in _args:
                    _stale.append(f"`templates.py` 의 `render_vn` 에 `{_need}` 인자가 없습니다 (서버의 templates.py 가 예전 버전)")
except (OSError, SyntaxError, UnicodeDecodeError):
    pass
if _stale:
    st.set_page_config(page_title="이불킥 법정", page_icon="🏛️")
    st.error("🧩 서버에 올라간 파일들의 버전이 서로 맞지 않아요. (일부 파일이 예전 버전입니다)")
    st.markdown("**맞지 않는 부분**\n\n" + "\n".join(f"- {m}" for m in _stale))
    st.markdown(
        "**해결 방법**\n\n"
        "1. 같은 시점에 받은 8개 파일(`app.py`, `config.py`, `characters.py`, `utils.py`, `templates.py`, `llm_handler.py`, `stage.py`, `court_bg.py`)을 **전부** 최신 버전으로 다시 올립니다. 특히 위에 나온 파일을 확인하세요.\n"
        "2. 커밋/푸시한 뒤 앱을 **Reboot** 하세요."
    )
    with st.expander("서버에 올라간 파일 크기(줄 수)"):
        _info = []
        for _f in ["app.py"] + _REQUIRED_FILES:
            try:
                _info.append(f"{_f}: {len(open(os.path.join(_HERE, _f), encoding='utf-8').read().splitlines())}줄")
            except OSError:
                _info.append(f"{_f}: 읽을 수 없음")
        st.code("\n".join(_info))
    st.stop()

from openai import (
    AuthenticationError,
)

from characters import SPRITE_DATA_VERSION, display_name
from config import (
    APP_CSS,
    FEE_MAX,
    LOBBY_H,
    LOBBY_TIPS,
    RANKS,
    MODEL_CANDIDATES,
    PAGE_ICON,
    PAGE_LAYOUT,
    PAGE_TITLE,
    RULING_LABEL,
    SPEED_MS,
    VN_H,
)
from templates import (
    SPRITE_ENGINE_VERSION,
    TITLE_HTML,
    court_panel_html,
    render_lobby,
    render_story,
    render_vn,
    result_panel_html,
)
from llm_handler import (
    call_llm_json,
    key_format_ok,
    make_client,
)
from utils import (
    add_fee,
    apply_result,
    build_call,
    fee_eta,
    go,
    init_session,
    load_record,
    new_profile,
    rank_info,
    regen_fee,
    reset_run,
    ss,
    start_job,
    vn_opts,
    watch_ad,
)

import inspect as _inspect

# 2막 첫 장면: 판사가 외치며 카메라가 줌아웃 + '제 2 막' 타이틀 (화면 전환/암전 없이 이어짐)
ACT2_OPEN = [{"s": "JUDGE", "t": "2막을 시작합니다!", "k": "act2", "cam": "WIDE"}]

_VN_PARAMS = set(_inspect.signature(render_vn).parameters)


def _render_vn(*args, **kwargs):
    """render_vn 이 모르는 인자(예: 옛 버전에 없는 intro)는 조용히 빼고 호출 — TypeError 방지."""
    return render_vn(*args, **{k: v for k, v in kwargs.items() if k in _VN_PARAMS})


# characters.py(그림 데이터)와 templates.py(그리는 코드)가 서로 짝이 맞는 버전인지 확인
if SPRITE_ENGINE_VERSION != SPRITE_DATA_VERSION:
    st.set_page_config(page_title="이불킥 법정", page_icon="🏛️")
    st.error("🧩 characters.py 와 templates.py 의 버전이 서로 달라요. (한쪽만 최신 버전입니다)")
    st.markdown(
        f"- `templates.py` 의 그림 엔진 버전: **{SPRITE_ENGINE_VERSION}**\n- `characters.py` 의 그림 데이터 버전: **{SPRITE_DATA_VERSION}**\n\n"
        "두 파일을 같은 시점에 받은 최신 버전으로 **함께** 다시 올린 뒤, 커밋/푸시하고 앱을 **Reboot** 하세요."
    )
    st.stop()


# =================================================================
# 페이지 설정 / 전역 CSS  (st.set_page_config 는 반드시 첫 번째 Streamlit 명령이어야 합니다)
# =================================================================
st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout=PAGE_LAYOUT)
st.markdown("<style>" + APP_CSS + "</style>", unsafe_allow_html=True)

init_session()  # 접속(세션)마다 기본값 채우기

# =================================================================
# 공통 UI: 에러 / API 키 안내 / 모달(프로필·설정·상점) / HUD
# =================================================================
def show_error():
    if ss["error"]:
        st.error("😴 AI 법정이 응답하지 못했습니다. (선임비는 차감되지 않았습니다) 다시 시도해 주세요.")
        with st.expander("상세 에러 보기"):
            st.code(ss["error"])

def excuse_gate():
    """변명 입력칸(chat_input)은 평소에 숨기고, 재판 연출에서 '변명 차례'(마지막 심문이 끝난 순간)가 되면 아래에서 올라오게 한다.
    연출(iframe)이 이 표식 컨테이너에 상태를 적으면 config.py의 CSS가 입력창을 보여 준다."""
    with st.container(key="excuse_gate"):
        st.empty()
    if ss.get("error"):  # 에러로 되돌아온 경우엔 연출을 다시 보지 않아도 바로 입력할 수 있게 연다
        st.markdown(
            '<style>.stApp:has(.st-key-excuse_gate) [data-testid="stBottom"]'
            "{transform:none !important;opacity:1 !important;pointer-events:auto !important;animation:none !important}</style>",
            unsafe_allow_html=True,
        )


def key_guard():
    """API 키가 없을 때 보여줄 깔끔한 안내. (키 값은 절대 화면/로그에 노출하지 않는다)"""
    if key_format_ok():
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

# ---------------- 모달(프로필 / 설정 / 상점) ----------------
@st.dialog("👤 내 프로필", width="large")
def profile_dialog():
    p = ss["profile"]
    idx, icon, rname, cur, nxt = rank_info(p["rep"])
    # '오늘의 법정' 상태 패널: 로비에는 항상 띄우지 않고, 프로필을 열었을 때만 이 모달 안에 보여준다
    st.markdown(
        court_panel_html(
            rep=p["rep"], icon=icon, rank=rname,
            pct=100 if nxt is None else int(min((p["rep"] - cur) / (nxt - cur), 1) * 100),
            next_name=None if nxt is None else f"{RANKS[idx + 1][1]} {RANKS[idx + 1][2]}",
            need=0 if nxt is None else nxt - p["rep"],
            streak=p.get("streak", 0), wins=p["wins"], trials=p["trials"],
            fee=ss["fee"], fee_max=FEE_MAX, badges=len(p["badges"]),
        ),
        unsafe_allow_html=True,
    )
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
        if not key_format_ok():
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
        st.info(f"선임비가 가득 찼습니다. {display_name('LAWYER')}가 여유 만렙입니다!")
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

# =================================================================
# 화면 라우팅  TITLE →(STORY_ASK→STORY)→ LOBBY → INPUT →(LOADING)→ DEBATE1 →(LOADING)→ DEBATE2 →(LOADING)→ VERDICT
# =================================================================
stage = ss["stage"]
if ss.get("toast"):
    st.toast(ss.pop("toast"))
# 판결 연출이 끝나기 전에는 HUD를 숨겨서 결과(평판/랭크)가 미리 보이지 않게 한다
hud_hidden = stage in ("TITLE", "STORY_ASK", "STORY", "LOADING", "QUIT") or (stage == "VERDICT" and not ss.get("show_result"))
if not hud_hidden:
    render_hud()

# ---------------- TITLE ----------------
if stage == "TITLE":
    st.markdown(TITLE_HTML, unsafe_allow_html=True)
    with st.container(key="menu"):
        if st.button("▶ 시  작", use_container_width=True, key="b_start"):
            reset_run()
            go("LOBBY" if ss["story_asked"] else "STORY_ASK")  # 최초 1회만 스토리 시청 여부를 묻고, 이후엔 곧장 로비로
        if st.button("📖 스토리 보기" + ("" if ss["story_seen"] else " ✨"), use_container_width=True, key="b_story"):
            go("STORY")
        if st.button("종  료", use_container_width=True, key="b_quit"):
            go("QUIT")

# ---------------- STORY_ASK (이번 접속 최초 1회만 표시) ----------------
elif stage == "STORY_ASK":
    st.markdown(
        '<div class="ask"><div class="ask-icon">📖</div><h2>스토리를 보시겠습니까?</h2>'
        '<p>이번 접속에서는 이 질문이 딱 한 번만 나와요.<br>처음이라면 스토리를 추천해요!</p></div>',
        unsafe_allow_html=True,
    )
    with st.container(key="ask2"):
        if st.button("📖 스토리 보고 시작하기", use_container_width=True, key="ask_yes"):
            ss["story_asked"] = True
            go("STORY")
        if st.button("⚡ 바로 재판장으로 가기", use_container_width=True, key="ask_no"):
            ss["story_asked"] = True
            go("LOBBY")

# ---------------- STORY (1인칭 법원 계단 스토리) ----------------
elif stage == "STORY":
    ss["story_asked"] = True  # 스토리를 한 번이라도 열었다면 이후 [시작]에서 다시 묻지 않는다
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
    # 서브컬처풍 로비: 가운데 캐릭터 장면(iframe) 위에 버튼을 겹쳐 배치한다.
    #   왼쪽 위 = 작은 메뉴 / 오른쪽 아래 = 타이틀로 / 아래 가운데 = 큼직한 [소장 접수]
    with st.container(key="lobby_stage"):
        render_lobby({}, height=LOBBY_H)  # 상태 패널은 숨김 → 장면에 넘길 값이 없다
        with st.container(key="lobby_ui"):
            with st.container(key="lb_side"):
                if st.button("⚙️ 설정", use_container_width=True, key="nav_set"):
                    settings_dialog()
                if st.button("👤 프로필", use_container_width=True, key="nav_prof"):
                    profile_dialog()
                if st.button("🛒 상점", use_container_width=True, key="nav_shop"):
                    shop_dialog()
                if st.button("📖 스토리", use_container_width=True, key="nav_story"):
                    go("STORY")
            with st.container(key="lobby_main"):
                if st.button("⚖️ 소장 접수 (재판 시작)", use_container_width=True, key="b_court", disabled=ss["fee"] <= 0 or not key_format_ok()):
                    reset_run()
                    go("INPUT")
            with st.container(key="lb_corner"):
                if st.button("◀ 타이틀", use_container_width=True, key="b_to_title"):
                    go("TITLE")
    key_guard()
    if ss["fee"] <= 0:
        eta = fee_eta() or 0
        st.markdown(
            '<div class="loading" style="color:#ff9b9b">💸 변호사 선임비가 바닥났습니다!'
            f'<small>{display_name("LAWYER")}가 "선임비 없으면 변론도 없어요~"라며 손을 흔들었습니다 · '
            f'자동 충전까지 {eta // 60}:{eta % 60:02d} · 🛒 상점에서 충전할 수 있어요</small></div>',
            unsafe_allow_html=True,
        )
    st.markdown(f'<div class="tip">💡 {random.choice(LOBBY_TIPS)} · 재판 1회에 선임비 1 소모</div>', unsafe_allow_html=True)

# ---------------- INPUT ----------------
elif stage == "INPUT":
    st.markdown('<div class="doc-head">소 장 접 수<small>― 흑역사를 고발하라 ―</small></div>', unsafe_allow_html=True)
    ready = key_guard()
    with st.container(key="paper"):
        paper_left, paper_right = st.columns([1, 1.7], gap="large")  # 가로 화면: 왼쪽 정보·버튼 / 오른쪽 넓은 입력칸
        with paper_left:
            name = st.text_input("피고인 성명 (닉네임)", value=ss["user_name"], max_chars=12)
        with paper_right:
            history = st.text_area(
                "흑역사 내용 (1,000자 제한)", value=ss.get("history_text", ""), max_chars=1000, height=250,
                placeholder="예: 새벽 2시에 감성에 젖어 싸이월드 감성 글을 올렸습니다...",
            )
        with paper_left:
            st.caption("※ 입력한 내용만 사실로 취급됩니다. 상황이 구체적일수록 공방이 더 정확해집니다. · 재판 1회에 변호사 선임비 1이 듭니다.")
            start = st.button("⚖️ 재판 개시", use_container_width=True, disabled=ss["fee"] <= 0 or not ready)
            back = st.button("◀ 로비", use_container_width=True)
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

# ---------------- LOADING → '대기 연출' (로딩 화면 없이, 판사가 서류를 살피며 고민하는 풀스크린 장면) ----------------
elif stage == "LOADING":
    job = ss.get("job")
    if not job:
        go("LOBBY")
    kind, back = job["kind"], job["back"]
    args, kwargs = build_call(kind)
    # 장면(iframe)을 먼저 화면에 띄운 뒤, 그 장면이 계속 연기하는 동안 AI 응답을 기다린다.
    with st.container(key="wait_stage"):
        _render_vn("wait", [], phase=kind, height=VN_H, **vn_opts())
    try:
        raw = call_llm_json(*args, **kwargs)
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
    _render_vn(
        "debate", ss["p1"]["steps"], height=VN_H, title="제1막 · 개정 & 1차 심문",
        phase="제1막 ▸ 1차 심문", hint="🚨 1차 심문! 아래 입력창에 변명을 적어 제출하세요 ▼", intro=True, push=True, **vn_opts(),
    )
    st.caption("▶ 화면을 클릭(터치)하거나 Space/Enter로 대사를 넘기세요. 천천히 읽고, 심문이 끝나면 변명 입력창이 아래에서 올라옵니다.")
    if st.button("🏳️ 재판 포기 (로비로)", key="giveup1"):
        go("LOBBY")
    show_error()
    excuse_gate()
    ex1 = st.chat_input("1차 변명을 입력하세요 (최대 200자)", key="chat_ex1")
    if ex1 and ex1.strip():
        ss["ex1"] = ex1.strip()[:200]
        start_job("p2", "DEBATE1")

# ---------------- DEBATE2 ----------------
elif stage == "DEBATE2":
    _render_vn(
        "debate", ACT2_OPEN + ss["p2"]["steps"], height=VN_H, title="제2막 · 변명 공방 & 최후 심문",
        phase="제2막 ▸ 최후 심문", hint="🔥 최후 심문! 아래 입력창에 최후 변명을 제출하세요 ▼", opening="act2", push=True, **vn_opts(),
    )
    st.caption("▶ 1차 변명을 두고 벌어지는 공방입니다. 마지막 질문이 끝나면 변명 입력창이 올라옵니다. 사실에 맞고 진심이 담길수록 무죄에 가까워요!")
    if st.button("🏳️ 재판 포기 (로비로)", key="giveup2"):
        go("LOBBY")
    show_error()
    excuse_gate()
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
    _render_vn("verdict", v["steps"], card=card, height=VN_H + 10, title="최종 선고", phase="최종 선고", opening="verdict", **vn_opts())
    if res and not ss.get("show_result"):
        st.caption("🎬 판결 연출을 다 보셨다면, 아래 버튼으로 평판·랭크 변화를 확인하세요!")
        _, show_col, _ = st.columns([1, 2, 1])
        with show_col:
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
    _, c, _ = st.columns([1, 2, 1])
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
