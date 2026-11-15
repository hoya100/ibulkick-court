"""utils.py — 게임 로직: 세션 초기화, 평판/랭크 계산, 변호사 선임비(소모·충전·광고), 재판 결과·기록 저장, 재판 단계 호출 준비.
"""

import html
import random
import time

import streamlit as st

from config import (
    GUILT_START,
    LAST_STAND_AT,
    STANCE_NAME,
    STUTTER,
    TIMER_SEC,
    FEE_MAX,
    RANKS,
    REGEN_SEC,
    REP_START,
    RULING_DELTA,
    RULING_LABEL,
    RUN_KEYS,
    SPEED_MS,
    STREAK_BONUS,
)
from characters import (
    FORM_HINTS,
    NAME_OF,
    facts_block,
    phase1_prompt,
    phase2_prompt,
    transcript,
    verdict_system_prompt,
)
from llm_handler import (
    make_phase1_validator,
    normalize_phase1,
    normalize_phase2,
    normalize_verdict,
    validate_script,
    validate_verdict,
)

# =================================================================
# 세션 / 평판·선임비 / 기록 등 게임 로직
# =================================================================

ss = st.session_state

def init_session():
    """접속(세션)마다 기본값을 채운다. app.py가 매 rerun 시작 시 호출한다.

    모듈은 서버 프로세스 동안 한 번만 import 되므로, 세션 기본값은 import 시점이 아니라
    이 함수에서 채워야 새 접속자에게도 올바르게 적용된다."""
    ss.setdefault("stage", "TITLE")
    ss.setdefault("user_name", "익명의 피고인")
    ss.setdefault("error", "")
    ss.setdefault("fee", FEE_MAX)
    ss.setdefault("fee_ts", None)
    ss.setdefault("daily_claimed", False)
    ss.setdefault("story_seen", False)
    ss.setdefault("story_asked", False)
    ss.setdefault("profile", {"rep": REP_START, "trials": 0, "wins": 0, "streak": 0, "records": [], "badges": []})
    ss.setdefault("sound_on", True)
    ss.setdefault("speed_label", "보통")
    ss.setdefault("profile_tab", "🎖️ 칭호")


def esc(x):
    return html.escape(str(x if x is not None else "")).replace("\n", "<br>")

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

def watch_ad():
    """광고 시청 → 선임비 +1 충전 연출. (실제 광고가 아닌 데모 연출입니다)"""
    bar = st.progress(0, text=f"📺 [광고] {NAME_OF['LAWYER']} 법률사무소 — 변론은 여유롭게~ (연출용 가상 광고)")
    for i in range(1, 41):
        time.sleep(0.1)
        bar.progress(i / 40, text=f"📺 [광고] {NAME_OF['LAWYER']} 법률사무소 — 변론은 여유롭게~ ({4 - i // 10}초)")
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

def vn_opts():
    return {"mute": not ss["sound_on"], "speed": SPEED_MS.get(ss["speed_label"], 30)}

# ---------------- 공방 시스템: 유죄 게이지 / 태도 / 반응 연출 ----------------
def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, int(round(v))))

def fallback_quality(text):
    n = len(str(text).strip())
    return 15 if n < 10 else min(70, 40 + n // 5)

def gauge_delta(q, stance, timeout=False):
    """변명 품질 q(0~100)와 태도에 따라 유죄 게이지 증감(음수 = 감소)을 계산한다.
    - 시간 초과: +18 자폭
    - 뻔뻔하게 우기기: 하이리스크 하이리턴 (성공 -15~-39 / 실패 시 증가폭 2배)
    - 눈물로 호소하기: 안정형 (-14 ~ +8)
    - 논리적 팩트체크: 품질에 비례 (-22 ~ +22)"""
    if timeout:
        return 12
    q = 40 if q is None else q
    if stance == "bold":
        return -round(10 + (q - 60) * 0.4) if q >= 60 else round(1.4 * max(6, (60 - q) * 0.45))
    if stance == "tears":
        return max(-10, min(6, round((50 - q) * 0.22 - 3)))
    if stance == "logic":
        return max(-15, min(15, round((50 - q) * 0.35)))
    return 0


def gauge_walk(steps, start, lo=0, hi=100):
    """각 대사의 증감(g)을 누적해 대사마다 '그 대사 직후의 게이지(gv)'를 기록하고 마지막 값을 돌려준다.
    g 가 없으면 화자로 추정: 검사가 몰아붙이면 +, 변호사가 반론하면 −, 판사는 0."""
    cur = start
    for st in steps:
        g = st.get("g")
        if g is None:
            sp, c = st.get("s"), st.get("c")
            g = (4 + (2 if c == "F" else 0)) if sp == "PROSECUTOR" else (-4 - (2 if c == "S" else 0)) if sp == "LAWYER" else 0
        cur = max(lo, min(hi, cur + int(g)))
        st["gv"] = cur
    return cur

def reaction_steps(stance, q, timeout):
    """변명 직후 캐릭터들이 보이는 반응 대사 + 연기(pose)·표정(e). 태도와 결과에 따라 달라진다."""
    L, P, J = "LAWYER", "PROSECUTOR", "JUDGE"
    def stp(s, t, pose="", e="", c=""):
        d = {"s": s, "t": t, "c": c}
        if pose:
            d["pose"] = pose
        if e:
            d["e"] = e
        return d
    if timeout:
        return [stp(L, "피, 피고인?! 지금 뭐라도 말씀하셔야죠…! 이러면 제가 변호를 못 해요…", "l_panic", "panic"),
                stp(P, "시간 초과입니다. 말을 더듬으셨다는 건, 인정한 것으로 보겠습니다!!", "", "smirk", "F")]
    ok = q >= 60 if stance == "bold" else q >= 45
    if stance == "bold":
        return ([stp(L, "후훗, 이 정도로 당당하면 오히려 설득력이 생기는 법이죠. 검사님, 반박해 보시겠어요?", "l_cross", "smug", "S"),
                 stp(P, "…당당함만으로 넘어갈 사안이 아닙니다만… 크윽…", "p_panic", "panic")] if ok else
                [stp(P, "뻔뻔함도 정도가 있습니다!! 방금 그 주장은 사실과 전혀 맞지 않아요!", "", "angry", "F"),
                 stp(L, "아, 아니 그건… 좀 무리수였네요… 식은땀이 나는데요…", "l_panic", "panic")])
    if stance == "tears":
        return ([stp(L, "…피고인의 눈물에 진심이 느껴지네요. 재판장님도 마음이 흔들리실 거예요.", "l_smug", "aggrieved"),
                 stp(J, "음… 솔직하게 말씀하시니, 조금 마음이 움직이긴 하네요.", "j_main")] if ok else
                [stp(P, "눈물로 사실이 바뀌지는 않습니다. 증거를 보십시오.", "p_main", "angry"),
                 stp(L, "그래도 울면 조금은 봐주는 게 인지상정인데… 아쉽네요.", "l_smug", "aggrieved")])
    return ([stp(P, "으윽… 그, 그건 사실과 맞는 말이군요…", "p_panic", "panic"),
             stp(L, "봤죠? 논리는 배신하지 않아요. 훗.", "l_cross", "smug")] if ok else
            [stp(P, "논리라고 하셨습니까? 앞뒤가 전혀 맞지 않습니다!!", "", "angry", "F"),
             stp(J, "…듣는 제가 다 피곤하군요. 하아.", "j_sigh")])

def case_header():
    return (
        f"[피고인] {ss['case_name']}\n[흑역사 원문]\n\"\"\"\n{ss['history_text']}\n\"\"\"\n"
        f"[확정 사실 — 이것만 사실로 취급]\n{facts_block(ss.get('facts', []))}\n"
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
         f"[변명 성의도 참고] 1차 변명 {len(ss['ex1'].strip())}자, 최후 변명 {len(ss['ex2'].strip())}자 (10자 미만이면 성의 부족)\n"
         f"[유죄 게이지] 1차 변명 후 현재 {ss.get('guilt', GUILT_START)}%\n"
         f"[태도] 1차: {STANCE_NAME.get(ss.get('stance1'), '미선택')} / 최후: {STANCE_NAME.get(ss.get('stance2'), '미선택')}"
         + ("\n[시간 초과] 최후 변명 시간이 초과되어 피고인이 말을 더듬었음" if ss.get("timeout2") else "")
         + ("\n[최후의 변론] 제출됨 — last_stand_score 를 반드시 채점할 것" if ss.get("ls_text") else "")),
        dict(max_tokens=2500, temperature=1.0, validate=validate_verdict),
    )

def apply_result(kind, raw):
    """결과를 세션에 반영하고 다음 화면 이름을 반환"""
    if kind == "p1":
        p1 = normalize_phase1(raw, ss["history_text"])
        ss["facts"], ss["p1"] = p1["facts"], p1
        spend_fee()  # 성공했을 때만 선임비 차감
        end1 = gauge_walk(p1["steps"], GUILT_START, 20, 80)   # 1막은 대사에 따라 20~80 사이에서 출렁인다
        ss["guilt"], ss["g0"], ss["ls_used"] = end1, GUILT_START, False
        ss.pop("cut", None)
        return "DEBATE1"
    if kind == "p2":
        p2 = normalize_phase2(raw)
        timeout = bool(ss.pop("timeout1", False))
        q = p2.get("quality")
        q = fallback_quality(ss.get("ex1", "")) if q is None else q
        if len(str(ss.get("ex1", "")).strip()) < 10 and not timeout:
            q = min(q, 20)
        g0 = ss.get("guilt", GUILT_START)
        delta = gauge_delta(q, ss.get("stance1"), timeout)
        rs = reaction_steps(ss.get("stance1"), q, timeout)
        if rs:  # 태도 결과(상승/하락)를 반응 대사 두 줄에 나눠 싣는다
            half = round(delta / 2)
            rs[0]["g"] = half
            if len(rs) > 1:
                rs[1]["g"] = delta - half
        p2["steps"] = rs + p2["steps"]
        g1 = gauge_walk(p2["steps"], g0, 5, 100)
        hit = [k for k, st in enumerate(p2["steps"]) if st["gv"] >= LAST_STAND_AT]
        p2["ls_idx"] = hit[0] if hit else None            # 게이지가 처음 90을 넘는 대사 → 최후의 변론 이벤트
        p2["ls_g"] = p2["steps"][hit[0]]["gv"] if hit else g1
        p2["gauge"] = (g0, g1)
        ss["g0"], ss["guilt"], ss["p2"] = g0, g1, p2
        return "DEBATE2"
    ctx = {"timeout2": bool(ss.get("timeout2")), "last_stand": bool(ss.get("ls_text")),
           "cut": bool(ss.get("cut")), "guilt": ss.get("guilt", GUILT_START)}
    ss["verdict_data"] = normalize_verdict(raw, ss.get("ex1", ""), ss.get("ex2", ""), ctx)
    ss["verdict_data"]["gauge"] = (ss.get("guilt", GUILT_START), ss["verdict_data"]["final_guilt"])
    finish_trial()
    return "VERDICT"
