import json
import streamlit as st
from google import genai

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="이불킥 법정 (Kick-the-Blanket Court)",
    page_icon="🏛️",
    layout="centered",
)

# CSS 스타일링 (역전재판 B급 감성 및 연출 효과)
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0f111a;
        color: #ffffff;
    }
    .court-card {
        background: linear-gradient(135deg, #1f2937, #111827);
        border: 2px solid #ef4444;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
        margin-top: 20px;
    }
    .shake-effect {
        animation: shake 0.5s;
    }
    @keyframes shake {
        0% { transform: translate(1px, 1px) rotate(0deg); }
        20% { transform: translate(-3px, 0px) rotate(-1deg); }
        40% { transform: translate(1px, -1px) rotate(1deg); }
        60% { transform: translate(-3px, 1px) rotate(0deg); }
        80% { transform: translate(1px, -1px) rotate(-1deg); }
        100% { transform: translate(0px, 0px) rotate(0deg); }
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("🏛️ 이불킥 법정 (Kick-the-Blanket Court)")
st.caption(
    "《역전재판》 오마주 기반의 B급 감성 텍스트 법정 시뮬레이터"
)

# 사이드바: API Key 입력 설정
with st.sidebar:
    st.header("⚙️ 시스템 설정")
    api_key = st.text_input(
        "Gemini API Key 입력",
        type="password",
        placeholder="AI 연동 키를 입력하세요",
    )
    st.markdown(
        "[🔑 Google AI Studio 무료 키 발급](https://aistudio.google.com/)"
    )

# 2. 소장 접수 폼 (흑역사 입력)
st.subheader("1단계: 소장 접수")
history_text = st.text_area(
    "심판받고 싶은 흑역사 텍스트를 입력하세요 (1,000자 제한)",
    placeholder="예: 새벽 2시에 감성에 젖어 싸이월드 감성 글을 올렸습니다...",
    max_chars=1000,
)

# 세션 상태 초기화
if "stage" not in st.session_state:
    st.session_state["stage"] = "INPUT"

# [버튼] 재판 개시
if st.button("⚖️ 법정 개정 및 공방 시작"):
    if not api_key:
        st.error("사이드바에 Gemini API Key를 먼저 입력해 주세요!")
    elif not history_text.strip():
        st.warning("심판받을 흑역사 내용을 입력해 주세요!")
    else:
        with st.spinner(
            "AI 판사, 검사, 변호사가 법정에 입장하고 있습니다..."
        ):
            try:
                client = genai.Client(api_key=api_key)

                # Phase 1 시스템 프롬프트 및 스키마 정의 반영
                system_instruction = """
                You are the core AI engine of "Kick-the-Blanket Court" (이불킥 법정), a parody text courtroom simulator.
                Analyze the user's cringe memory and generate a debate in strict JSON format.
                
                Personas:
                - PROSECUTOR (검사 AI - 팩폭러): Ruthless, exposes absolute cringe. Catchphrases: "이의 있소!"
                - LAWYER (변호사 AI - 억지 쉴드): Desperate, absurd excuses. Catchphrases: "재판장님, 당시 피고인은..."
                - JUDGE (판사 AI - 엄근진 꼰대): Solemn boomer dignity.
                
                You must output ONLY a valid JSON object matching this schema:
                {
                  "stage": "STAGE_1_AND_2",
                  "script": [
                    {
                      "speaker": "JUDGE" | "PROSECUTOR" | "LAWYER",
                      "emotion": "STRING",
                      "effect": "SHAKE" | "NONE" | "SWEAT",
                      "dialogue": "STRING"
                    }
                  ],
                  "interrogation": {
                    "question": "STRING",
                    "options": ["STRING", "STRING", "STRING"]
                  }
                }
                """

                prompt = f"[유저의 흑역사]\n{history_text}"

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config={
                        "system_instruction": system_instruction,
                        "response_mime_type": "application/json",
                        "temperature": 0.8,
                    },
                )

                # JSON 파싱 및 세션 저장
                data = json.loads(response.text)
                st.session_state["debate_data"] = data
                st.session_state["history_text"] = history_text
                st.session_state["api_key"] = api_key
                st.session_state["stage"] = "DEBATE"

            except Exception as e:
                st.error(f"AI 연동 및 JSON 파싱 중 오류가 발생했습니다: {e}")

# 3. 중단: 역전재판 스타일 대화창 및 피의자 심문 출력
if st.session_state["stage"] in ["DEBATE", "VERDICT"]:
    data = st.session_state["debate_data"]

    st.markdown("---")
    st.markdown("### 🏛️ 법정 공방 현장")

    # 대화 스크립트 순차 렌더링
    for item in data.get("script", []):
        speaker = item.get("speaker")
        dialogue = item.get("dialogue")
        effect = item.get("effect")

        if speaker == "JUDGE":
            avatar, title = "🏛️", "판사 AI (엄근진 꼰대)"
        elif speaker == "PROSECUTOR":
            avatar, title = "⚖️", "검사 AI (팩폭러)"
        else:
            avatar, title = "🛡️", "변호사 AI (억지 쉴드)"

        # 셰이크 연출 태그 반영
        container_class = (
            "shake-effect" if effect == "SHAKE" else "normal-box"
        )

        with st.chat_message("assistant", avatar=avatar):
            st.markdown(f"**[{title}]**")
            if effect == "SHAKE":
                st.error(f"⚡ [이의 제기/충격 연출] {dialogue}")
            else:
                st.write(dialogue)

    # 4. 인터랙션: ★ [신규] 유저 피의자 심문 이벤트 (Cross-Examination)
    if st.session_state["stage"] == "DEBATE":
        st.markdown("---")
        st.markdown("### 🚨 [긴급] 피의자 심문 이벤트 (Cross-Examination)")
        interrogation = data.get("interrogation", {})
        st.info(f"**판사/검사의 심문:** {interrogation.get('question')}")

        user_choice = st.radio(
            "피고인의 최후 변명 선택지:", interrogation.get("options", [])
        )

        if st.button("변명 제출 및 최종 선고 받기"):
            with st.spinner("판사가 피고인의 태도를 심판하는 중입니다..."):
                try:
                    client = genai.Client(api_key=st.session_state["api_key"])
                    verdict_system_instruction = """
                    You are the Judge AI of "Kick-the-Blanket Court".
                    Based on the user's cringe memory and their interrogation answer, generate the final verdict in strict JSON format.
                    
                    You must output ONLY a valid JSON object matching this schema:
                    {
                      "stage": "STAGE_3_VERDICT",
                      "verdict_title": "STRING",
                      "script": [
                        {
                          "speaker": "JUDGE",
                          "emotion": "STERN",
                          "effect": "GAVEL",
                          "dialogue": "STRING"
                        }
                      ],
                      "summary_card": {
                        "crime_summary": "STRING",
                        "user_excuse": "STRING",
                        "final_sentence": "STRING",
                        "badge": "STRING"
                      }
                    }
                    """

                    verdict_prompt = f"""
                    [유저의 흑역사]: {st.session_state['history_text']}
                    [유저의 피의자 심문 답변]: {user_choice}
                    """

                    v_response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=verdict_prompt,
                        config={
                            "system_instruction": verdict_system_instruction,
                            "response_mime_type": "application/json",
                            "temperature": 0.8,
                        },
                    )

                    v_data = json.loads(v_response.text)
                    st.session_state["verdict_data"] = v_data
                    st.session_state["user_choice"] = user_choice
                    st.session_state["stage"] = "VERDICT"
                    st.rerun()

                except Exception as e:
                    st.error(f"최종 선고 생성 중 오류 발생: {e}")

# 5. 하단/결과: 최종 선고 및 판결문 짤 카드 표시 영역
if st.session_state["stage"] == "VERDICT":
    v_data = st.session_state["verdict_data"]
    card = v_data.get("summary_card", {})

    st.markdown("---")
    st.markdown("### 🏛️ [최종 판결 선고 결과]")

    for item in v_data.get("script", []):
        with st.chat_message("assistant", avatar="🏛️"):
            st.markdown(f"**[판사 AI 최종 선고]**")
            st.success(item.get("dialogue"))

    # 판결문 짤 카드뉴스 시각화 영역 (Canvas 대체 UI 카드)
    st.markdown(
        f"""
        <div class="court-card">
            <h2 style="text-align: center; color: #f87171;">🏛️ 이불킥 법정 판결문 🏛️</h2>
            <hr style="border-color: #4b5563;">
            <p><b>📌 죄목 요약:</b> {card.get('crime_summary')}</p>
            <p><b>🗣️ 피고인 변명:</b> {st.session_state.get('user_choice')}</p>
            <p><b>⚖️ 최종 판형:</b> <span style="color: #fbbf24; font-size: 1.2em;">{card.get('final_sentence')}</span></p>
            <p style="text-align: center; margin-top: 15px;"><span style="background-color: #dc2626; padding: 6px 14px; border-radius: 20px; font-weight: bold;">{card.get('badge')}</span></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.balloons()
