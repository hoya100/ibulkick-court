"""llm_handler.py — OpenRouter API 통신, LLM 호출(모델 순차 폴백·재시도), JSON 파싱, 응답 검증/정규화.

API 키는 st.secrets["OPENROUTER_API_KEY"] → 환경변수 순서로만 읽습니다. (코드에 키를 적지 않습니다)
"""

import json
import os
import random
import re
import time

import streamlit as st
from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    OpenAI,
    PermissionDeniedError,
    RateLimitError,
)

from config import (
    ATTEMPTS_PER_MODEL,
    BASE_URL,
    MAX_TOTAL_CALLS,
    MODEL_CANDIDATES,
    PAID_FALLBACK,
    REASONING_HEADROOM,
    REQUEST_TIMEOUT,
)
from characters import (
    ALIAS,
    BANNED,
    SHOUT_MAP,
    SPEAKERS,
)

# =================================================================
# API 키 / OpenRouter 클라이언트
# =================================================================

def get_api_key():
    """Streamlit Secrets → 환경변수 순서로 키를 읽는다. 키 값은 화면/로그에 절대 출력하지 않는다."""
    key = ""
    try:
        key = st.secrets["OPENROUTER_API_KEY"]
    except Exception:  # secrets.toml이 없거나 키가 없는 경우
        key = ""
    key = key or os.environ.get("OPENROUTER_API_KEY", "")
    return str(key).strip().strip("\"'").strip()  # 공백/따옴표 실수 방지

def key_format_ok():
    """키가 'sk-or-'로 시작하는 정상 형식인지 확인 (호출 시점마다 현재 Secrets/환경변수를 다시 읽는다)."""
    key = get_api_key()
    return key.startswith("sk-or-") and len(key) > 20


def make_client():
    return OpenAI(
        base_url=BASE_URL,
        api_key=get_api_key(),
        timeout=REQUEST_TIMEOUT,
        max_retries=0,  # 재시도는 아래 로직에서 직접 제어
        default_headers={"HTTP-Referer": "http://localhost:8501", "X-Title": "Kick-the-Blanket Court"},
    )

# =================================================================
# LLM 호출 + 견고한 JSON 파싱 (모델 순차 폴백 / 재시도)
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
    if not get_api_key():
        raise RuntimeError("API 키가 설정되지 않았습니다. Streamlit Secrets에 OPENROUTER_API_KEY를 등록해 주세요.")
    if not key_format_ok():
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
# 응답 검증 / 정규화
# =================================================================

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
