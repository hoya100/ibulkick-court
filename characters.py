"""characters.py — 오리지널 캐릭터 3인방의 '단일 데이터 원본' + 말투/사실 엄수 규칙 + LLM 프롬프트.

  서판결(판사)   만사가 귀찮고 퇴근하고 싶은 나른한 판사          ← 참고 이미지 3 (헝클어진 흑발, 졸린 눈의 남성)
  차냉정(검사)   겉은 얼음, 진실 앞에선 불꽃인 열정의 검사        ← 참고 이미지 2 (흑발 미디엄 레이어드 컷)
  한유리(변호사) 능글맞고 여유로운, 어떤 변명도 포장하는 변호사    ← 참고 이미지 1 (연갈색 장발, 부드러운 미소)

■ 구조
  CHARACTERS[키]  이름·성격·말투·외모·의상·프롬프트 조각·도트 스프라이트 데이터(팔레트/렌더 설정/모션)·일러스트 경로
  SPEAKERS / NAME_OF / ALIAS / SHOUT_MAP / CAST   ← 위 데이터에서 자동으로 만들어지는 기존 호환 상수
  phase1_prompt / phase2_prompt / verdict_system_prompt   ← LLM 시스템 프롬프트
  get_character / sprite_palette / css_vars / css_style / integer_scale / illustration_path   ← 조회·표시용 도우미

■ 연결 상태 (중요)
  · 대사 톤(성격·말투)은 프롬프트로 바로 게임에 적용됩니다.
  · 외모(머리·눈·표정·의상·색)는 templates.py 의 스프라이트 코드가 이 파일의 palette/style/render 를 읽어서 그립니다.
    render.mode = "pixel_hd" : 픽셀 단위로 직접 칠하는 고해상도 도트 엔진 (머리 가닥의 결, 눈동자 그라데이션·하이라이트, 4단계 명암, 색 있는 외곽선). 세 캐릭터 모두 기본값.
    render.mode = "svg"      : 예전의 도형 도트(각진 도트). 문제가 생기면 이 값으로 되돌릴 수 있습니다.
    pixel_hd 에서 쓸 수 있는 스타일은 HD_SUPPORTED 에 적혀 있습니다. 새 스타일을 추가하면 templates.py 의 HD 엔진에도 그리기 코드를 추가하세요.
  · 참고 이미지 파일 자체는 게임에 넣지 않았습니다. 직접 만든(또는 사용 권한이 있는) 이미지를 쓰려면 illustration 항목에 경로를 적고
    use_illustration 을 True 로 바꾸세요.

대사 톤이나 금지 표현을 바꾸고 싶을 때는 여기를 수정하세요.
"""

import os

# 스프라이트 데이터 형식의 버전. templates.py 의 SPRITE_ENGINE_VERSION 과 같아야 합니다 (스타일 이름·팔레트·render.mode 등을 바꿔 형식이 달라지면 둘을 같이 올리세요).
SPRITE_DATA_VERSION = 7

# 3D 모델(.vrm) 파일이 올라가 있는 인터넷 주소(폴더). 비워 두면 지금의 벡터 캐릭터를 씁니다. 설정 방법은 rig3d.py 맨 위 설명을 보세요.
# 예) "https://cdn.jsdelivr.net/gh/내아이디/ibulkick-court@main/assets/models"
MODEL_BASE_URL = ""
# 캐릭터별 모델 파일 이름과 구도 보정(zoom: 클수록 가까이, fy: 위(+)/아래(-)로 이동)
MODEL_FILES = {"JUDGE": {"file": "judge.vrm", "zoom": 1.0, "fy": 0.0}, "PROSECUTOR": {"file": "prosecutor.vrm", "zoom": 1.0, "fy": 0.0}, "LAWYER": {"file": "lawyer.vrm", "zoom": 1.0, "fy": 0.0}}

# =================================================================
# 1. 캐릭터 데이터 (오리지널 캐릭터 3인방)
# =================================================================

# 도트 렌더링 공통 기본값 (캐릭터별로 sprite["render"] 에서 덮어쓸 수 있음)
RENDER_DEFAULT = {
    "viewbox": (200, 160),                 # 반신(바스트) 스프라이트 좌표계 (가로, 세로)
    "mode": "svg",                         # "svg" = 도형으로 그린 도트 / "pixel_hd" = 픽셀 단위로 칠한 고해상도 도트(머리결·눈 그라데이션·명암)
    "shape_rendering": "crispEdges",       # (svg 모드) 도트/픽셀 스타일. 부드러운 곡선으로 보고 싶으면 "geometricPrecision"
    "image_rendering": "pixelated",        # 이미지 확대 시 도트 유지
    "integer_scale": True,                 # 확대 배율은 정수배만 사용 → 계단 현상/흐림 방지
    "preferred_scales": (3, 4, 5, 6),
    "outline_px": 2,                       # 외곽선 두께(도트 단위)
    "shading": "3-tone",                   # 기본색 / 밝은 면 / 어두운 면
    "light_dir": "top-left",
    "rim_light": True,                     # 머리카락·어깨 가장자리 보조광
    "eye_highlight_px": 2,                 # 눈 하이라이트(도트 수)
    "layers": ("back_hair", "torso", "neck", "head", "face", "front_hair", "arms", "props"),
}

CHARACTERS = {
    # ------------------------------------------------------------------ 판사
    "JUDGE": {
        "key": "JUDGE", "name": "서판결", "title": "판사", "display": "서판결 판사",
        "emoji": "🏛️", "ui_color": "#fbbf24", "tagline": "만사가 귀찮은 나른한 판사",
        "aliases": ["서판결", "판사"],
        "shout": {"tag": "ORDER", "code": "O", "text": "…정숙해 주세요. 빨리 끝냅시다."},
        "persona": {
            "summary": "만사가 귀찮고 늘 피곤하다. 속으로는 계속 퇴근 시간을 세고 있지만, 사건의 핵심만큼은 놓치지 않는다.",
            "traits": ["나른함", "만성 피로", "퇴근 갈망", "무심한 듯 정확함"],
            "speech_tone": "느릿하고 단정한 존댓말. 한숨과 짧은 말로 귀찮음을 은근히 드러낸다.",
            "speech_rules": [
                "귀찮음은 한숨('하…'), 짧은 말, 퇴근 시간 언급 정도로 '은근히' 표현한다.",
                "(하품을 삼키며), (시계를 힐끗 보며) 같은 짧은 지문을 가끔 쓴다.",
                "피고인을 비하·조롱하지 않는다. 귀찮아하지만 판결 내용은 사건에 맞게 정확하다.",
                "반말, 욕설, 뜬금없는 질문(식사 여부 등), 억지 유행어, 사자성어, 고서 인용, 고어체('~하오/~로다') 금지.",
            ],
            "catchphrases": ["하… 퇴근 시간이 얼마 안 남았는데.", "요점만 짧게 갑시다.", "서류는 다 읽었습니다. 안 읽고 싶었지만요."],
            "sample_lines": [
                "하… 이런 사건이 오늘 몇 번째인지 모르겠군요. 그래도 읽긴 읽었습니다.",
                "(시계를 힐끗 보며) 퇴근까지 얼마 안 남았으니, 변명은 짧게 부탁드립니다.",
                "아… 형량이요. 정해야 하죠. 이 정도면 되겠네요.",
            ],
            "ambient_lines": ["하… 아직도 이만큼이나 남았나.", "퇴근 시간이 왜 이렇게 안 오지.", "(하품을 삼키며) 보리차나 마셔야겠군요."],
            # AI 응답을 기다리는 동안 보이는 '서류 살피는 판사' 장면의 혼잣말(말풍선). templates.py 가 이 값을 읽는다.
            "wait_lines": {
                "read": ["…", "하… 길다.", "(사락…)"], "flip": ["(서류를 넘긴다)", "(하품을 삼키며)"],
                "compare": ["앞뒤가 맞나… 맞겠죠.", "이쪽이랑 이쪽이라…"], "magnify": ["세부 사항이라… 귀찮지만 봅시다."],
                "rub": ["(눈을 비빈다)", "잠깐만요… 눈이 따가워서."], "yawn": ["(하아암…)", "퇴근 시간까지 얼마나 남았더라."],
                "write": ["메모… 해야 하나.", "(사각사각)"],
                "ponder": {
                    "p1": ["소장 내용은 확인했습니다. 귀찮지만요.", "흠… 이 사건은…"],
                    "p2": ["변명이라… 앞뒤는 따져 봐야겠죠.", "하, 그렇게 나오시는군요."],
                    "verdict": ["이제 판결을 내려야 하는군요… 빨리 끝냅시다.", "형량… 형량이라… 귀찮네요."],
                },
            },
        },
        # LLM 시스템 프롬프트 조각 (CAST 에 그대로 들어갑니다)
        "prompt": """- JUDGE [서판결]: 만사가 귀찮고 피곤한 나른한 판사. 속으로는 퇴근 시간만 세고 있지만, 사건의 핵심은 정확히 짚는다.
  · 귀찮음은 한숨("하…"), 짧은 말, 퇴근 시간 언급 정도로 '은근히' 드러낸다. 예: "하… 퇴근 시간이 얼마 안 남았는데.", "요점만 짧게 갑시다.", "서류는 다 읽었습니다. 안 읽고 싶었지만요."
  · 대사 중간에 (하품을 삼키며), (시계를 힐끗 보며) 같은 짧은 지문을 넣어도 된다. 피고인을 비하하거나 조롱하지 않으며, 판결과 진행은 사건 내용에 맞게 정확하다.
  · 반말, 욕설, 뜬금없는 질문(예: 식사 여부를 묻는 말), 억지 유행어, 사자성어, 고서 인용, 고어체('~하오/~로다') 전부 금지. 느릿하고 단정한 존댓말('~입니다', '~합시다', '~하셨습니까')을 쓰고, 어려운 말 대신 쉬운 말을 쓴다.""",
        "look": {
            "impression": "날카로운 인상인데 눈빛은 졸린 듯 나른한, 무심하고 시크한 청년 판사",
            "hair": "헝클어진 흑발 숏컷. 앞머리가 눈 위로 흘러내려 시선을 반쯤 가린다.",
            "eyes": "날카롭지만 반쯤 감긴 나른한 눈매, 옅은 다크서클",
            "expression": "무심한 무표정, 입꼬리가 살짝 내려감",
            "skin": "창백한 톤",
            "outfit": {
                "name": "묵직한 클래식 법복",
                "pieces": ["무거운 검은 법복(넓은 라펠, 늘어진 어깨선)", "흰 셔츠", "검은 넥타이(살짝 풀어짐)", "검은 정장 바지"],
                "accessory": "라펠의 작은 토끼 핀 (피곤한 분위기와 대비되는 귀여운 포인트)",
            },
            "idle_pose": "턱을 괴고 서류를 넘기며 하품을 참는 자세",
        },
        "sprite": {
            "palette": {
                "outline": "#08080c", "skin": "#f1d7c6", "skin_shadow": "#d9b8a6", "blush": "#e7b3ab",
                "hair": "#14141a", "hair_light": "#34343f", "hair_shadow": "#08080c", "brow": "#0e0e14",
                "eye": "#1a1a22", "iris_light": "#3a3a4a", "pupil": "#05050a", "eye_light": "#ffffff", "eye_bag": "#b99aa3",
                "mouth": "#6a3a40", "tongue": "#c97b84",
                "robe": "#17171d", "robe_light": "#2c2c36", "robe_inner": "#0b0b10",
                "shirt": "#f1f2f7", "shirt_shadow": "#cfd2de", "tie": "#0e0e12", "pin": "#b9bcc9", "accent": "#8a8fa6",
            },
            # 어떤 모양으로 그릴지(머리·눈·눈썹·입·의상). 값은 STYLE_CATALOG 에 있는 이름만 쓸 수 있고, templates.py 의 스프라이트 그리기 코드가 이 이름을 읽는다.
            "style": {"face": "jaw_tidy", "hair": "messy_short", "eyes": "sleepy_half", "brows": "low_tired", "mouth": "weary", "outfit": "judge_robe",
                      "eye_h": 9, "eye_top": 50, "lid_min": 3.8,   # 눈 높이 / 눈 세로 위치 / 평소 눈꺼풀 내려온 정도(졸림)
                      "shoulder_dx": 44, "shoulder_y": 106, "sleeve_w": 17},
            "rig": {"body": "broad", "hair": "messy", "jaw": "tidy", "outfit": "judge_robe", "iris": "#3b3b5c", "iris2": "#8a8ab4", "lash": "#08080c",
                    "tilt": 3, "eyeW": 1.0, "eyeH": 0.92, "mouth": "weary", "sleepy": 0.42, "blushA": 0.35, "pin": "bunny", "rim": "#9fb4e8"},
            "render": {"mode": "layered25d", "rim_light": True, "eye_highlight_px": 2},
            "motion": {"blink_s": 5.2, "idle": ["yawn", "check_watch", "rub_eyes", "slump"], "breath_amp": 0.5},
        },
        "illustration": {"portrait": "assets/characters/judge_portrait.png", "bust": "assets/characters/judge_bust.png", "use_illustration": False},
    },
    # ------------------------------------------------------------------ 검사
    "PROSECUTOR": {
        "key": "PROSECUTOR", "name": "차냉정", "title": "검사", "display": "차냉정 검사",
        "emoji": "⚖️", "ui_color": "#ff5555", "tagline": "겉은 얼음, 속은 불꽃인 열정 검사",
        "aliases": ["차냉정", "검사"],
        "shout": {"tag": "FACT", "code": "F", "text": "잠깐만요! 팩트 체크 들어갑니다!"},
        "persona": {
            "summary": "겉보기엔 차갑고 냉정하지만, 법정과 진실 앞에서는 누구보다 뜨겁게 유죄를 파고든다.",
            "traits": ["냉정한 겉모습", "숨겨진 열정", "예리함", "원칙주의"],
            "speech_tone": "차분하게 시작해 근거가 쌓일수록 열기가 오르는 격식 있는 존댓말. 마지막 한 문장에 열정이 터진다.",
            "speech_rules": [
                "호흡이 긴 문장으로 논리를 쌓는다(시간 순서 정리 → 심리 해부 → 결론 한 방).",
                "감정을 누르려다 새어 나오는 열기가 매력 포인트. 결론 문장은 단호하고 뜨겁게.",
                "지문은 (서류를 탁 덮으며) 같은 짧은 것만 가끔 허용한다.",
            ],
            "catchphrases": ["기록은 거짓말을 하지 않습니다.", "…이건 그냥 넘어갈 수 없습니다!"],
            "sample_lines": [
                "감정은 접어 두겠습니다. 시간순으로 보면 앞뒤가 분명하니까요. …하지만 이 부분만큼은 끝까지 파고들겠습니다!",
                "(서류를 탁 덮으며) 변명은 들었습니다. 이제 기록이 말할 차례입니다.",
            ],
            "ambient_lines": ["유죄의 냄새가… 나는군요.", "기록은 거짓말을 하지 않습니다."],
        },
        "prompt": """- PROSECUTOR [차냉정]: 겉보기엔 얼음처럼 차갑고 냉정하지만, 법정과 진실 앞에서는 누구보다 뜨겁게 유죄를 파고드는 열정적인 검사.
  · 말은 차분하게 시작해서 근거가 쌓일수록 점점 열기가 오르고, 마지막 한 문장에 열정이 터진다(예: "…이건 그냥 넘어갈 수 없는 일입니다!"). 감정을 누르려다 새어 나오는 열기가 포인트.
  · 예리하고 정확하게 후벼파되, 호흡이 긴 문장으로 논리를 쌓는다(시간 순서 정리 → 심리 해부 → 결론 한 방). 격식 있는 존댓말. 지문은 (서류를 탁 덮으며) 같은 짧은 것만 가끔 허용.""",
        "look": {
            "impression": "빈틈없이 단정한, 차갑고 지적인 인상. 무표정 속에 눈빛만 단단하다.",
            "hair": "윤기 나는 흑발 미디엄 레이어드 컷(턱~어깨 길이, 끝이 바깥으로 살짝 뻗음). 가운데 가르마, 눈 옆으로 떨어지는 잔머리.",
            "eyes": "차분한 짙은 흑안, 눈꺼풀이 살짝 내려온 서늘한 눈매",
            "expression": "표정 변화가 거의 없는 단정한 무표정",
            "skin": "창백하고 투명한 톤",
            "outfit": {
                "name": "차콜 그레이 정장 수트 (재킷 + 슬랙스)",
                "pieces": ["차콜 그레이 재킷(각진 어깨, 단정한 라펠)", "흰 셔츠(깃을 빳빳하게)", "짙은 회색 넥타이", "차콜 슬랙스(칼주름)"],
                "accessory": "소매 단추를 끝까지 채운 단정함(빈틈없는 인상)",
            },
            "idle_pose": "서류를 반듯하게 쥐고 가만히 상대를 응시하는 자세",
        },
        "sprite": {
            "palette": {
                "outline": "#14141c", "skin": "#f6e5e3", "skin_shadow": "#e4cdcb", "blush": "#ecc9c6",
                "hair": "#1a1a22", "hair_light": "#3b3d4d", "hair_shadow": "#0c0c12", "brow": "#1a1a22",
                "eye": "#17171f", "iris_light": "#3b3d52", "pupil": "#050508", "eye_light": "#ffffff",
                "mouth": "#8a4a52", "tongue": "#d98a92",
                "suit": "#3f424c", "suit_light": "#5f6370", "shirt": "#eef0f6", "shirt_shadow": "#cdd2e0",
                "tie": "#2c2e36", "accent": "#9aa0b4",
            },
            "style": {"face": "jaw_tidy", "hair": "layered_medium", "eyes": "cool_half", "brows": "straight_sharp", "mouth": "thin_cool", "outfit": "charcoal_suit",
                      "eye_h": 8, "eye_top": 55, "lid_min": 2,
                      "shoulder_dx": 38, "shoulder_y": 106, "sleeve_w": 14},
            "rig": {"body": "slim", "hair": "medium", "jaw": "sharp", "outfit": "charcoal_suit", "iris": "#26263e", "iris2": "#6f82c4", "lash": "#0a0a12",
                    "tilt": 5, "eyeW": 1.0, "eyeH": 0.98, "mouth": "flat", "sleepy": 0.10, "blushA": 0.25, "pin": None, "rim": "#a8c4ff"},
            "render": {"mode": "layered25d", "rim_light": True, "eye_highlight_px": 2},
            "motion": {"blink_s": 4.6, "idle": ["straighten_papers", "adjust_cuff", "slam_desk", "stare"], "breath_amp": 0.35},
        },
        "illustration": {"portrait": "assets/characters/prosecutor_portrait.png", "bust": "assets/characters/prosecutor_bust.png", "use_illustration": False},
    },
    # ------------------------------------------------------------------ 변호사
    "LAWYER": {
        "key": "LAWYER", "name": "한유리", "title": "변호사", "display": "한유리 변호사",
        "emoji": "🛡️", "ui_color": "#66fcf1", "tagline": "능글맞고 여유로운 포장의 달인",
        "aliases": ["한유리", "변호사"],
        "shout": {"tag": "SHIELD", "code": "S", "text": "이의 있습니다! 억지 쉴드 발동!"},
        "persona": {
            "summary": "살짝 능글맞고 늘 여유롭다. 피고인의 터무니없는 변명도 재치 있게 그럴듯하게 포장해 준다.",
            "traits": ["능청스러움", "여유", "친근함", "임기응변"],
            "speech_tone": "능청스럽고 친근한 부드러운 존댓말. 농담과 비유를 섞어 억지 논리를 그럴듯하게 만든다.",
            "speech_rules": [
                "당황하지 않고 웃는 낯으로 받아친다. 과장된 눈물·절규 연기는 하지 않는다.",
                "(씩 웃으며), (어깨를 으쓱하며) 같은 짧은 지문을 가끔 쓴다.",
                "피고인 편에 서서 변명을 재치 있게 포장하되, 사실(원문)을 벗어나 지어내지 않는다.",
            ],
            "catchphrases": ["에이, 그건 너무 박하시죠~", "걱정 마세요, 제가 잘 포장해 드릴게요."],
            "sample_lines": [
                "에이, 그건 너무 박하시죠~ 그건 실수가 아니라 감수성이 풍부했던 거랍니다.",
                "(씩 웃으며) 걱정 마세요, 이 변명, 제가 아주 잘 포장해 드릴게요.",
            ],
            "ambient_lines": ["어서 오세요~ 오늘은 어떤 변명을 포장해 드릴까요?", "소장 접수는 아래 버튼이에요. 제가 잘 부탁드릴게요~", "(윙크) 무죄 각, 보이죠?"],
            # 로비에서 한유리가 일하고·커피 마시고·기지개 켜는 동안 뜨는 말풍선. templates.py 가 이 값을 읽는다.
            "lobby_lines": {
                "wave": ["어서 오세요~ 오늘은 어떤 변명을 포장해 드릴까요?", "👋 어머, 오늘도 오셨네요?"],
                "work": ["📝 변론서 작성 중… 여유롭게요~", "타닥타닥… 이 정도 포장은 식은 죽 먹기죠.", "이 사건, 무죄 각이 보이는데요?"],
                "coffee": ["☕ 커피 타임~", "후루룩… 크으, 이 맛이죠~"],
                "think": ["흠… 이건 어떻게 포장해야 예쁠까요?", "🤔 능청스럽게 가 볼까요?"],
                "stretch": ["으으~ 어깨가 뻐근하네요.", "🙆 잠깐 스트레칭~"],
                "idle": ["소장 접수는 아래 큰 버튼이에요~", "저는 언제든 준비돼 있답니다."],
                "poke": ["어머, 간지러워요~", "소장 접수는 아래 버튼! 제가 잘 부탁드릴게요~", "(윙크) 제 변론, 믿어 보세요.", "커피 마시는 중인데요~?"],
            },
        },
        "prompt": """- LAWYER [한유리]: 살짝 능글맞고 여유로운 변호사. 피고인의 터무니없는 변명도 재치 있게 그럴듯하게 포장해 준다. 어떤 상황에도 당황하지 않고 웃는 낯으로 받아친다.
  · 능청스럽고 친근한 말투(예: "에이, 그건 너무 박하시죠~", "걱정 마세요, 제가 잘 포장해 드릴게요."). 존댓말은 유지하되 부드럽게 풀어서 말한다.
  · 농담과 비유를 곁들여 억지 논리를 그럴듯하게 만든다. 대사 중간에 (씩 웃으며), (어깨를 으쓱하며) 같은 짧은 지문을 넣어도 된다. 과장된 눈물·절규 연기는 하지 않는다.""",
        "look": {
            "impression": "부드럽고 매력적인 인상. 여유 있는 미소로 사람을 안심시키는 능청스러운 변호사",
            "hair": "연한 갈색의 긴 웨이브 장발(허리선 근처). 가르마 앞머리가 얼굴선을 따라 흘러내림. 대체 헤어: 낮은 포니테일.",
            "eyes": "갈색의 처진 반달 눈매. 웃을 때 눈꼬리가 접힌다.",
            "expression": "여유로운 미소, 고개를 한쪽으로 살짝 기울이는 버릇",
            "skin": "밝고 혈색 있는 톤, 볼에 은은한 홍조",
            "outfit": {
                "name": "블랙 슬림핏 비즈니스 수트",
                "pieces": ["검은 슬림핏 재킷", "흰 셔츠(옷깃을 단정히)", "검은 넥타이(단정한 매듭)", "검은 슬랙스"],
                "accessory": "라펠의 작은 저울 핀 (금속 광택)",
            },
            "idle_pose": "의자에 몸을 살짝 기울이고 턱을 괸 채 웃는 자세",
        },
        "sprite": {
            "palette": {
                "outline": "#1a1218", "skin": "#f9d9c4", "skin_shadow": "#efbfa6", "blush": "#f5a3a0",
                "hair": "#a9795a", "hair_light": "#cf9f7c", "hair_shadow": "#7a523a", "brow": "#7a523a",
                "eye": "#6b4430", "iris_light": "#a8714c", "pupil": "#2a1810", "eye_light": "#ffffff",
                "mouth": "#8a3b3b", "tongue": "#e58a8a",
                "suit": "#23252e", "suit_light": "#3a3d4a", "shirt": "#f4f6fb", "shirt_shadow": "#d5dae8",
                "tie": "#15161c", "pin": "#c9b26b", "accent": "#c9b26b",
            },
            "style": {"face": "jaw_tidy", "hair": "long_wavy", "eyes": "crescent_smile", "brows": "arched_raised", "mouth": "smirk", "outfit": "slim_suit",
                      "eye_h": 10, "eye_top": 53, "lid_min": 2,
                      "shoulder_dx": 34, "shoulder_y": 106, "sleeve_w": 12},
            "rig": {"body": "curvy", "hair": "long_wavy", "jaw": "soft", "outfit": "slim_suit", "iris": "#7a3f22", "iris2": "#f0b070", "lash": "#2a1410", "star": True,
                    "tilt": 1, "eyeW": 1.07, "eyeH": 1.1, "mouth": "smile", "sleepy": 0.0, "blushA": 0.6, "pin": "scale", "rim": "#ffd9b0"},
            "render": {"mode": "layered25d", "rim_light": True, "eye_highlight_px": 2},
            "motion": {"blink_s": 4.0, "idle": ["head_tilt", "wink", "hair_flip", "lean_on_hand"], "breath_amp": 0.6},
        },
        "illustration": {"portrait": "assets/characters/lawyer_portrait.png", "bust": "assets/characters/lawyer_bust.png", "use_illustration": False},
    },
}

CHARACTER_ORDER = ("JUDGE", "PROSECUTOR", "LAWYER")

# 스프라이트 스타일 카탈로그: '스타일 이름 → 그 스타일을 그리는 데 꼭 필요한 팔레트 색 이름'.
# CHARACTERS[...]["sprite"]["style"] 에는 여기 있는 이름만 쓸 수 있고, templates.py 의 그리기 코드가 같은 이름의 그리기 함수를 가지고 있다.
STYLE_CATALOG = {
    "face": {
        "jaw_slim": [],    # 각진 도트 얼굴 + 턱 끝만 살짝 샤프하게 (변호사)
        "jaw_clean": [],   # 깔끔하게 모이는 V 턱 (검사)
        "jaw_tidy": [],    # 턱선만 살짝 정리한 얼굴 (판사)
    },
    "hair": {
        "long_wavy": ["hair", "hair_light", "hair_shadow"],        # 허리 근처까지 내려오는 웨이브 장발 + 가르마 앞머리
        "layered_medium": ["hair", "hair_light", "hair_shadow"],   # 턱~어깨 길이, 끝이 바깥으로 뻗는 레이어드 단발
        "messy_short": ["hair", "hair_light", "hair_shadow"],      # 헝클어진 숏컷, 앞머리가 눈을 반쯤 가림
    },
    "eyes": {
        "crescent_smile": ["eye", "iris_light", "pupil", "eye_light"],            # 웃을 때 반달로 접히는 눈
        "cool_half": ["eye", "iris_light", "pupil", "eye_light"],                 # 서늘하고 차분한 눈
        "sleepy_half": ["eye", "iris_light", "pupil", "eye_light", "eye_bag"],    # 졸린 듯 반쯤 감긴 눈 + 다크서클
    },
    "brows": {"arched_raised": ["brow"], "straight_sharp": ["brow"], "low_tired": ["brow"]},
    "mouth": {"smirk": ["mouth", "tongue"], "thin_cool": ["mouth", "tongue"], "weary": ["mouth", "tongue"]},
    "outfit": {
        "slim_suit": ["suit", "suit_light", "shirt", "shirt_shadow", "tie", "pin"],
        "charcoal_suit": ["suit", "suit_light", "shirt", "shirt_shadow", "tie"],   # 일반 정장(재킷+슬랙스)
        "judge_robe": ["robe", "robe_light", "robe_inner", "shirt", "shirt_shadow", "tie", "pin"],
    },
}
COMMON_PALETTE_KEYS = ["outline", "skin", "skin_shadow", "blush"]
# render.mode == "pixel_hd" 로 그릴 수 있는 스타일 (templates.py 의 HD 엔진에 구현된 것만). 새 스타일을 추가하면 HD 엔진에도 그리기 코드를 추가하고 여기에 이름을 적으세요.
HD_SUPPORTED = {
    "hair": ["long_wavy", "layered_medium", "messy_short"],
    "eyes": ["crescent_smile", "cool_half", "sleepy_half"],
    "brows": ["arched_raised", "straight_sharp", "low_tired"],
    "mouth": ["smirk", "thin_cool", "weary"],
    "outfit": ["slim_suit", "charcoal_suit", "judge_robe"],
}



def _validate_characters():
    """필수 항목·스타일 이름·팔레트 색이 빠졌으면 앱이 켜질 때 바로 알려 준다 (데이터를 고치다 실수한 경우 대비)."""
    need = ("key", "name", "title", "display", "emoji", "ui_color", "tagline", "aliases", "shout", "persona", "prompt", "look", "sprite", "illustration")
    for k in CHARACTER_ORDER:
        c = CHARACTERS[k]
        miss = [f for f in need if f not in c]
        if miss:
            raise ValueError(f"CHARACTERS['{k}'] 에 빠진 항목: {miss}")
        if c["key"] != k:
            raise ValueError(f"CHARACTERS['{k}']['key'] 가 키와 다릅니다: {c['key']}")
        if c["name"] not in c["prompt"] or c["name"] not in c["display"]:
            raise ValueError(f"CHARACTERS['{k}'] 의 name('{c['name']}')이 display/prompt 와 일치하지 않습니다 (이름을 바꿨다면 둘 다 고치세요)")
        for alias_must in (c["name"], c["title"]):
            if alias_must not in c["aliases"]:
                raise ValueError(f"CHARACTERS['{k}']['aliases'] 에 '{alias_must}' 가 없습니다")
        for part in ("outfit", "hair", "eyes", "expression"):
            if part not in c["look"]:
                raise ValueError(f"CHARACTERS['{k}']['look'] 에 '{part}' 가 없습니다")
        sp = c["sprite"]
        pal, style = sp.get("palette", {}), sp.get("style")
        if not style:
            raise ValueError(f"CHARACTERS['{k}']['sprite']['style'] 이 없습니다")
        for kind, names in STYLE_CATALOG.items():
            val = style.get(kind)
            if val not in names:
                raise ValueError(f"CHARACTERS['{k}'] 스타일 {kind}='{val}' 은(는) STYLE_CATALOG 에 없습니다. 가능: {list(names)}")
            lacking = [n for n in names[val] if n not in pal]
            if lacking:
                raise ValueError(f"CHARACTERS['{k}'] 팔레트에 '{val}' 스타일이 쓰는 색이 빠졌습니다: {lacking}")
        lacking = [n for n in COMMON_PALETTE_KEYS if n not in pal]
        if lacking:
            raise ValueError(f"CHARACTERS['{k}'] 팔레트에 공통 색이 빠졌습니다: {lacking}")
        if {**RENDER_DEFAULT, **sp.get("render", {})}.get("mode") == "pixel_hd":
            for kind, ok_names in HD_SUPPORTED.items():
                if style.get(kind) not in ok_names:
                    raise ValueError(f"CHARACTERS['{k}'] 은(는) pixel_hd 모드인데 {kind}='{style.get(kind)}' 는 아직 pixel_hd 에서 그릴 수 없어요. 가능: {ok_names} (또는 render.mode 를 'svg' 로)")
        for n in ("shoulder_dx", "shoulder_y", "sleeve_w", "eye_h", "eye_top", "lid_min"):
            if n not in style:
                raise ValueError(f"CHARACTERS['{k}']['sprite']['style'] 에 '{n}' 가 없습니다")


_validate_characters()

# =================================================================
# 1-B. 표정 표 (EXPRESSIONS) — 표정을 늘리고 싶으면 여기에 한 줄만 추가하세요 (엔진 코드는 건드릴 필요 없음)
# =================================================================
# mouth : 입 모양 (grin/smile/open/flat/hmm 중 하나, None 이면 캐릭터 기본 입)
# brow  : 눈썹 위치 (음수=위로 올림, 양수=내림)     lid : 눈꺼풀 (0=기본, 1=감음)     gx/gy : 시선 (눈동자 좌우/상하)
# fx    : 얼굴 위에 얹는 효과 (blush 볼터치 / sweat 식은땀 / tears 눈물 / vein 분노 마크)
# icon  : 머리 옆에 잠깐 뜨는 감정 아이콘 (anger / exclaim / drop / sparkle, 없으면 None)
# 대사 데이터(step)에 "e": "표정이름" 을 넣으면 그 표정으로, 없으면 외침 종류(F/S/O)에 따라 자동 선택됩니다.
EXPRESSIONS = {
    "neutral":   {"label": "기본",        "mouth": None,    "brow": 0,  "lid": 0,    "gx": 0, "gy": 0, "fx": []},
    # 킹받는 표정: 반쯤 감은 눈 + 한쪽 눈썹만 치켜올림 + 비스듬한 능글 미소 + 고개 살짝 젖힘
    "smirk":     {"label": "킹받는 비웃음", "mouth": "grin", "brow": -1, "bs": 0.6, "lid": 0.32, "gx": 1, "gy": 0, "fx": [], "smug": 1, "tilt": 4, "pitch": -3, "icon": "sparkle"},
    # 억울해서 눈물 그렁그렁: 팔자 눈썹 + 눈가에 물이 찬 눈 + 파르르 떠는 입 + 홍조·식은땀
    "aggrieved": {"label": "억울함",       "mouth": "hmm",   "brow": 0,  "bs": -2.6, "lid": 0.05, "gx": 0, "gy": 2, "fx": ["welling", "blush", "sweat"], "tilt": -3, "pitch": 4, "icon": "drop"},
    "tears":     {"label": "눈물 폭발",     "mouth": "wail",  "brow": 0,  "bs": -3,   "lid": 0.22, "gx": 0, "gy": 2, "fx": ["tears", "welling", "blush"], "tilt": -2, "pitch": 5, "icon": "drop"},
    "shock":     {"label": "충격",         "mouth": "open",  "brow": -3, "bs": -0.5, "lid": 0,    "gx": 0, "gy": 0, "fx": ["sweat"], "pitch": -2, "icon": "exclaim"},
    "angry":     {"label": "분노",         "mouth": "grit",  "brow": 2,  "bs": 3.2,  "lid": 0.22, "gx": 0, "gy": 0, "fx": ["vein"], "pitch": 3, "icon": "anger"},
    "pout":      {"label": "삐짐",         "mouth": "pout",  "brow": 1,  "bs": 1.0,  "lid": 0.12, "gx": 2, "gy": 1, "fx": ["blush"], "tilt": 3},
    "shy":       {"label": "당황·부끄",     "mouth": "hmm",   "brow": -1, "bs": -1.4, "lid": 0.1,  "gx": -2, "gy": 2, "fx": ["blush", "sweat"], "tilt": -4},
}
EXPR_MOUTHS = ("grin", "smile", "open", "flat", "hmm", "smirk", "pout", "wail", "weary", "grit")
EXPR_FX = ("blush", "sweat", "tears", "vein", "welling", "gloom")
EXPR_ICONS = (None, "anger", "exclaim", "drop", "sparkle")


def _validate_expressions():
    if "neutral" not in EXPRESSIONS:
        raise ValueError("EXPRESSIONS 에 'neutral' 이 있어야 합니다")
    for n, e in EXPRESSIONS.items():
        if e.get("mouth") is not None and e["mouth"] not in EXPR_MOUTHS:
            raise ValueError(f"EXPRESSIONS['{n}'] mouth='{e['mouth']}' 는 없는 입 모양입니다. 가능: {EXPR_MOUTHS}")
        if e.get("icon") not in EXPR_ICONS:
            raise ValueError(f"EXPRESSIONS['{n}'] icon='{e.get('icon')}' 는 없는 아이콘입니다. 가능: {EXPR_ICONS}")
        bad = [f for f in e.get("fx", []) if f not in EXPR_FX]
        if bad:
            raise ValueError(f"EXPRESSIONS['{n}'] fx 에 없는 효과가 있습니다: {bad}. 가능: {EXPR_FX}")


_validate_expressions()


def expressions_payload():
    """화면 연출(templates.py)에 넘기는 표정 표 (JSON 직렬화 가능)"""
    return {n: dict(e) for n, e in EXPRESSIONS.items()}


# =================================================================
# 2. 기존 모듈과 호환되는 파생 상수 (위 데이터에서 자동 생성)
# =================================================================

SPEAKERS = {k: (CHARACTERS[k]["emoji"], f'{CHARACTERS[k]["title"]} AI ({CHARACTERS[k]["tagline"]})', CHARACTERS[k]["ui_color"]) for k in CHARACTER_ORDER}

NAME_OF = {k: CHARACTERS[k]["name"] for k in CHARACTER_ORDER}

ALIAS = {alias: k for k in CHARACTER_ORDER for alias in CHARACTERS[k]["aliases"]}

SHOUT_MAP = {CHARACTERS[k]["shout"]["tag"]: (CHARACTERS[k]["shout"]["code"], k) for k in CHARACTER_ORDER}

CAST = "등장인물 (모두 이 게임을 위해 새로 만든 오리지널 캐릭터. 다른 작품의 캐릭터·명칭·대사는 절대 사용 금지):\n" + "\n".join(
    CHARACTERS[k]["prompt"] for k in CHARACTER_ORDER
)

# =================================================================
# 3. 조회·표시용 도우미
# =================================================================


def get_character(key):
    """키(JUDGE/PROSECUTOR/LAWYER)로 캐릭터 데이터를 가져온다."""
    return CHARACTERS[key]


def sprite_palette(key):
    """도트 스프라이트용 색상표 (이름 → #hex)."""
    return dict(CHARACTERS[key]["sprite"]["palette"])


def render_settings(key):
    """공통 기본값 + 캐릭터별 덮어쓰기를 합친 렌더 설정."""
    r = dict(RENDER_DEFAULT)
    r.update(CHARACTERS[key]["sprite"].get("render", {}))
    return r


def css_vars(key):
    """팔레트를 CSS 변수 딕셔너리로 변환: {'--c-hair': '#a9795a', ...}"""
    return {"--c-" + name.replace("_", "-"): val for name, val in CHARACTERS[key]["sprite"]["palette"].items()}


def css_style(key):
    """style 속성에 바로 넣을 수 있는 CSS 변수 문자열: '--c-hair:#a9795a;--c-skin:#f9d9c4;...'"""
    return ";".join(f"{k}:{v}" for k, v in css_vars(key).items())


def integer_scale(avail_px, key=None):
    """도트가 번지지 않도록, 주어진 높이(px) 안에 들어가는 '가장 큰 정수 배율'을 고른다. (없으면 1)"""
    r = render_settings(key) if key else RENDER_DEFAULT
    base_h = r["viewbox"][1]
    fits = [s for s in r["preferred_scales"] if base_h * s <= avail_px]
    return max(fits) if fits else 1


def illustration_path(key, kind="portrait"):
    """직접 준비한 일러스트를 쓰도록 설정했고(use_illustration=True) 파일이 실제로 있으면 경로를, 아니면 None(→ 도트 스프라이트 사용)."""
    ill = CHARACTERS[key]["illustration"]
    path = ill.get(kind)
    if ill.get("use_illustration") and path and os.path.exists(path):
        return path
    return None


def display_name(key):
    return CHARACTERS[key]["display"]


def sprite_payload():
    """화면 연출(templates.py)에 넘기는 캐릭터 데이터: 이름·팔레트·스타일·외침 문구·말풍선 대사. JSON 으로 바로 직렬화할 수 있다."""
    out = {}
    for k in CHARACTER_ORDER:
        c = CHARACTERS[k]
        persona = c["persona"]
        out[k] = {
            "key": k, "name": c["name"], "title": c["title"], "display": c["display"],
            "palette": dict(c["sprite"]["palette"]), "style": dict(c["sprite"]["style"]),
            "render": {k2: (list(v) if isinstance(v, tuple) else v) for k2, v in render_settings(k).items()},
            "rig": dict(c["sprite"].get("rig", {}), **({"model": dict(MODEL_FILES[k], url=MODEL_BASE_URL.rstrip("/") + "/" + MODEL_FILES[k]["file"])} if MODEL_BASE_URL.strip() and k in MODEL_FILES else {})),
            "motion": dict(c["sprite"].get("motion", {})),
            "shout": dict(c["shout"]),
            "lines": {"ambient": list(persona.get("ambient_lines", [])), "lobby": persona.get("lobby_lines", {}), "wait": persona.get("wait_lines", {})},
        }
    return out

# =================================================================
# 4. 사실 엄수 · 쉬운 말 규칙 / 형벌 형식 / 금지 표현
# =================================================================

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

# 형벌의 '형식'만 다양하게 (내용은 반드시 유저의 사실/변명에서 가져오도록 하기 위함)
FORM_HINTS = [
    "숫자가 황당한 반복 횟수형", "공개 낭독형", "금지령형(일정 기간 ~ 금지)", "사회봉사형", "전시·게시형",
    "의무 시청·청취형", "복합형(서로 다른 형벌 2개를 '및'으로 연결)", "자필 반성문형", "기한부 근신형",
]

BANNED = ["이불킥 100회", "기억 소각형", "흑역사 제조기", "감성 과다", "정체불명"]

# =================================================================
# 프롬프트 (제1막 / 제2막 / 최종 판결)
# =================================================================

def phase1_prompt(name):
    return f"""당신은 오리지널 B급 법정 아케이드 게임 '이불킥 법정'의 AI 엔진입니다. 피고인 이름: "{name}".
{CAST}
{FACT_RULES}
{EASY_RULES}
[임무] 유저의 [흑역사 원문]을 바탕으로 '제1막: 개정과 1차 심문'을 한국어로 씁니다.
규칙:
1. facts: 먼저 흑역사 원문에서 핵심 사실 2~5개를 '원문에 적힌 표현 그대로' 복사해 적는다. 이후 모든 대사는 이 facts에 기반한다.
2. script는 정확히 7~8줄. 첫 줄은 JUDGE({NAME_OF['JUDGE']})의 개정 선언: 원문 내용을 그대로 인용해 사건을 요약하되, 귀찮고 피곤한 기색(한숨, 퇴근 시간 등)을 은근히 곁들인다. 이후 PROSECUTOR({NAME_OF['PROSECUTOR']})와 LAWYER({NAME_OF['LAWYER']})가 번갈아 공방하며, 중간에 JUDGE가 한 번 끼어들어 귀찮아하면서도 사건의 핵심을 짚는 한마디를 한다.
3. 템포: 각 dialogue는 반드시 2~3문장, 공백 포함 80~150자의 장문. 한 사람이 자기 논리를 차근차근(주장 → 근거 → 마무리 한 방) 풀어낸다. 짧게 치고 빠지지 말 것. 상대 말을 끊는 느낌은 대사 끝의 '—'로 가끔만 표현.
4. 인물별 말투는 위 등장인물 설정을 엄수한다: {NAME_OF['JUDGE']}: 나른하고 귀찮은 존댓말(반말·뜬금없는 질문·사자성어·고서·고어체 금지) / {NAME_OF['PROSECUTOR']}: 차갑게 시작해 갈수록 열정적으로 / {NAME_OF['LAWYER']}: 능청스럽고 친근하게.
5. 각 줄의 shout 필드: PROSECUTOR가 상대를 끊고 팩트로 치고 들어갈 때 "FACT", LAWYER가 능청스럽게 받아치며 억지로 감쌀 때 "SHIELD", JUDGE가 소란을 정리할 때 "ORDER", 그 외 "NONE". 전체에서 3~4번만 사용.
6. question: 검사 [{NAME_OF['PROSECUTOR']}]이 피고인에게 던지는 1차 팩폭 질문 (1~2문장, 원문 내용을 구체적으로 짚고, 피고인이 직접 변명을 적어 답할 수 있게).
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
1. script는 정확히 6~7줄. LAWYER({NAME_OF['LAWYER']})가 피고인의 1차 변명을 재치 있게 그럴듯하게 포장·옹호하고, PROSECUTOR({NAME_OF['PROSECUTOR']})가 변명 속 모순과 원문의 사실을 근거로 열정적으로 파고듭니다. 중간에 JUDGE({NAME_OF['JUDGE']}) 1줄이 귀찮음을 은근히 드러내며 사건 내용에 맞는 한마디로 개입.
2. 피고인의 1차 변명 표현을 대사에서 직접 인용해 반영하고("…라고 변명하셨지요"), 새로운 사건을 지어내지 말 것.
3. 템포: 각 dialogue는 반드시 2~3문장, 공백 포함 80~150자의 장문. 주장 → 근거 → 한 방 순서로 차분히 전개. shout 필드는 1막과 같은 규칙(FACT/SHIELD/ORDER/NONE), 3번 안팎 사용.
4. final_question: 최후 압박 질문. speaker는 "JUDGE" 또는 "PROSECUTOR", text는 1차 변명과 원문을 파고드는 날카로운 1~2문장.
5. 오직 JSON 객체 하나만 출력. 마크다운, 코드블록, 설명문 금지.
형식 예시(형식만 참고):
{{"script":[{{"speaker":"LAWYER","dialogue":"...","shout":"SHIELD"}},{{"speaker":"PROSECUTOR","dialogue":"...","shout":"FACT"}}],"final_question":{{"speaker":"JUDGE","text":"..."}}}}"""

def verdict_system_prompt(name, forms, nonce):
    return f"""당신은 오리지널 B급 법정 아케이드 게임 '이불킥 법정'의 판결 엔진이며, 판사 [{NAME_OF['JUDGE']}]입니다. 피고인 이름: "{name}". 판결 번호: #{nonce}
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
8. script는 JUDGE [{NAME_OF['JUDGE']}]의 선고 대사 3~4줄. 각 줄은 2~3문장, 80~150자. 나른하고 피곤한 말투로 빨리 끝내고 싶은 기색(한숨, 퇴근 시간 등)을 은근히 드러내되, 판결 내용은 사건과 변명에 맞게 정확해야 한다. 앞쪽 줄에서 피고인의 변명이 어땠는지 쉬운 말로 평가하고, 마지막 줄에서 판결을 선언한다.
9. verdict_title: 이 판결의 한 줄 제목.
10. 오직 JSON 객체 하나만 출력. 마크다운, 코드블록, 설명문 금지.
형식 예시(형식만 참고):
{{"defense_score":62,"ruling":"MITIGATED","verdict_title":"...","script":[{{"speaker":"JUDGE","dialogue":"..."}}],"summary_card":{{"crime_summary":"...","final_sentence":"...","badge":"🏅 ..."}}}}"""

def transcript(steps):
    return "\n".join(f"{NAME_OF.get(s['s'], '?')}: {s['t']}" for s in steps)

def facts_block(facts):
    return "\n".join(f"- {f}" for f in facts)
