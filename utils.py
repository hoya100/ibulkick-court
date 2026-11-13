"""utils.py — 게임 로직: 세션 초기화, 평판/랭크 계산, 변호사 선임비(소모·충전·광고), 재판 결과·기록 저장, 재판 단계 호출 준비.
"""

import html
import random
import time

import streamlit as st

from config import (
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

def vn_opts():
    return {"mute": not ss["sound_on"], "speed": SPEED_MS.get(ss["speed_label"], 30)}

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
