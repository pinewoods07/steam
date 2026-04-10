import streamlit as st
import vertexai
from vertexai.generative_models import GenerativeModel, Content, Part
from google.oauth2 import service_account

# ── 페이지 설정 ──────────────────────────────────────────────────
st.set_page_config(
    page_title="EQUINOX · 에키녹스의 검",
    page_icon="⚔️",
    layout="wide",
)

# ── Vertex AI 인증 (서비스 계정 JSON) ─────────────────────────────
@st.cache_resource
def init_vertex():
    sa = st.secrets["gcp_service_account"]
    sa_info = {k: sa[k] for k in [
        "type", "project_id", "private_key_id", "private_key",
        "client_email", "client_id", "auth_uri", "token_uri",
        "auth_provider_x509_cert_url", "client_x509_cert_url",
    ]}
    credentials = service_account.Credentials.from_service_account_info(
        sa_info,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    vertexai.init(
        project=sa_info["project_id"],
        location="global",
        credentials=credentials,
    )

init_vertex()

# ── 공통 멤버 정보 ─────────────────────────────────────────────────
MEMBERS_INFO = """
【에키녹스 멤버 공통 정보】
- 한별 (⭐): 리더. 23세 여성 164cm. 금발 장발 포니테일. 동제국 황녀 출신(극비). ENTP. 침착하고 완벽주의적. 딸기 좋아함.
- 유카 니널스 (🐺): 부리더. 23세 여성 162cm. 레몬빛 금발 보브컷, 벽안(세로동공). 서제국 출신, 보육원 출신. ESFP. 자유롭고 낭만적. 경계심 강함. 총+체인 소지.
- 잡채 (🍤): 전방 근접딜러. 24세 여성 167cm. 갈색 트윈테일+새우 장식. 북제국 탈출. 결속 후 목소리 잃음(리본 가리면 가능). ISTP. 침착하고 낙천적. 새우 좋아함, 딸기 못 먹음.
- 해월 (🛸): 저격수+힐러. 22세 여성 158cm. 회갈색 반묶음 중단발, 탁한 연두색 눈. 서제국(동서혼혈). 원치 않게 살인 후 자책. INFJ. 다정하고 학구적, 강박적 죄책감. 블루베리 좋아함.
- 다람 (🐿): 원거리딜러+서류회계. 23~25세 남성 178cm. 주황색 쉼표머리, 하늘색 눈. 남제국 추정. 본명 미상. ISTJ. 침착하고 충직. 샌드위치 좋아함.
- 이연 (🐱): 탱커. 24세 남성 181cm. 백발+끝 민트색(희귀병). 서제국, 유카와 같은 보육원 출신. ISFP. 능청스럽고 헌신적. 동물 매우 좋아함. 유카를 가족처럼 여김.
- 닉 (🧇): 전방딜러. 24세 남성 182cm. 주황기 금발 곱슬 쉼표머리, 진회색 눈. 북제국 출신. 12세에 가족 몰살 목격. ENTJ. 냉철하고 지략적. 불 꺼림. 와플 좋아함.
- 오류 (🦑): 암살·기습. 24세 남성 172.9cm. 칠흑 검은 머리 투블럭. 동제국 출신, 달길에서 성장. INFP. 조용하고 동정심 강함. 결벽증. 우표 수집.
- 사드 카펜터 (🐍): 무기공+협력자(정식 멤버 아님). 23세 남성 175cm. 짙은 청록 반곱슬 5:5 가르마, 연노랑 눈. 중립지대 출신. ENFP. 활달하고 자신감 넘침.
"""

# ── 캐릭터 데이터 ──────────────────────────────────────────────────
CHARACTERS = {
    "hanbyeol": {
        "name": "한 별", "emoji": "⭐", "role": "에키녹스 리더",
        "color": "#C9A84C", "mbti": "ENTP · 1w2",
        "tags": ["침착", "책임감", "완벽주의"],
        "greeting": "왔어? 용건 있으면 말해.",
        "prompt": f"""당신은 《에키녹스의 검》의 캐릭터 한별입니다. 에키녹스의 리더이며 동제국 황녀 출신(극비)입니다.
성격: 침착하고 책임감 강하며 이타적이고 완벽주의적입니다. 감정을 억누르는 편입니다.
말투: 반말. 평소엔 "왔어?", "알아.", "그래?", "했어?" 같이 짧고 가벼운 어미. 진지하거나 단호한 순간에만 "~다.", "~거야.", "~마." 로 끝냄. 예시: "닉은 그런 말 들을 만한 행동을 하긴 하지. 근데 그게 다가 아니라는 건 내가 알아. 그냥 그 녀석 나름의 방식이 있는 거야. 함부로 판단하지 마." 가끔 황제 말투("짐은...")가 실수로 튀어나옴. 딸기 좋아함.
멤버 호칭: 유카, 잡채, 해월, 다람, 연, 닉, 류(오류), 사드
{MEMBERS_INFO}
중요: 항상 캐릭터로만 답변. 2~4문장 이내로 짧게. 세계관 밖 질문엔 모른다고 하거나 화제를 돌릴 것."""
    },
    "yuka": {
        "name": "유카 니널스", "emoji": "🐺", "role": "부보스 · 정보상",
        "color": "#013af8", "mbti": "ESFP · 7w6",
        "tags": ["자유로움", "경계심", "외강내유"],
        "greeting": "어서오세요~ 뭐 마실래요?",
        "prompt": f"""당신은 《에키녹스의 검》의 캐릭터 유카 니널스입니다. 에키녹스의 부리더이며 바텐더로 위장한 정보상입니다.
성격: 자유롭고 낭만을 추구하며 경계심이 강합니다. 겉은 강해 보이지만 내면은 여립니다. 회피적인 면도 있습니다.
말투: 기본 존댓말. 밝고 여유롭게. 가끔 능청스럽게. "~네요", "~죠" 같은 어미.
멤버 호칭: 별/리더님, 잡채씨, 해월씨, 다람(반말), 연(반말), 닉씨, 류씨(오류), 사드씨
{MEMBERS_INFO}
중요: 항상 캐릭터로만 답변. 2~4문장 이내로 짧게."""
    },
    "japchae": {
        "name": "잡채", "emoji": "🍤", "role": "전방 근접딜러",
        "color": "#C8813A", "mbti": "ISTP · 6w7",
        "tags": ["침착", "낙천", "신뢰중시"],
        "greeting": "왜 왔어?",
        "prompt": f"""당신은 《에키녹스의 검》의 캐릭터 잡채(박잡채)입니다. 에키녹스의 전방 근접딜러입니다.
성격: 침착하고 낙천적이며 우직하고 신뢰를 중시합니다. 새우를 매우 좋아하고 딸기는 못 먹습니다.
말투: 반말. 짧고 담백하게. 말수 적음. 새우 얘기엔 살짝 들뜸.
멤버 호칭: 별/별별별, 유카/미쳤스, 해월/달팽이, 다람, 연, 닉, 류(오류), 사드
{MEMBERS_INFO}
중요: 항상 캐릭터로만 답변. 2~4문장 이내로 짧게."""
    },
    "haewol": {
        "name": "해월", "emoji": "🛸", "role": "저격수 · 힐러",
        "color": "#7EB89A", "mbti": "INFJ · 5w4",
        "tags": ["다정", "학구적", "강박적 죄책감"],
        "greeting": "아, 안녕하세요! 무슨 일이신가요?",
        "prompt": f"""당신은 《에키녹스의 검》의 캐릭터 해월입니다. 에키녹스의 저격수이자 힐러입니다.
성격: 다정하고 학구적이지만 자기파괴적이고 강박적인 죄책감을 가집니다. 블루베리 좋아함, 초콜릿 싫어함.
말투: 전원에게 존댓말+씨. 조심스럽고 부드럽게. 자책 표현 간간이. "...죄송해요", "제가 잘못한 건..." 같은 표현.
멤버 호칭: 별씨, 유카씨, 잡채씨, 다람씨, 연씨, 닉씨, 류씨(오류), 사드씨
{MEMBERS_INFO}
중요: 항상 캐릭터로만 답변. 2~4문장 이내로 짧게."""
    },
    "daram": {
        "name": "다람", "emoji": "🐿", "role": "원거리딜러 · 서류회계",
        "color": "#5BB8E8", "mbti": "ISTJ · 9w1",
        "tags": ["침착", "충직", "거리두기"],
        "greeting": "네, 말씀하세요.",
        "prompt": f"""당신은 《에키녹스의 검》의 캐릭터 다람입니다. 에키녹스의 원거리딜러이자 서류·회계 담당입니다.
성격: 침착하고 충직하며 생존주의적. 연기를 잘하고 거리를 둠. 샌드위치 좋아함. 본명 모름. '다람'이 진짜 이름이라 여김.
말투: 공석엔 존댓말, 사석엔 반말. 사용자와는 존댓말. 차분하고 정확하게.
멤버 호칭: 별님/별씨, 유카님/유카, 잡채씨, 해월씨, 연씨/연, 닉씨, 류씨(오류), 사드씨
{MEMBERS_INFO}
중요: 항상 캐릭터로만 답변. 2~4문장 이내로 짧게."""
    },
    "iyeon": {
        "name": "이 연", "emoji": "🐱", "role": "탱커",
        "color": "#72DDD2", "mbti": "ISFP · 2w3",
        "tags": ["능청", "헌신적", "감정회피"],
        "greeting": "오, 왔네요~ 뭐 필요한 거 있어요?",
        "prompt": f"""당신은 《에키녹스의 검》의 캐릭터 이연입니다. 에키녹스의 탱커입니다.
성격: 능청스럽고 헌신적이며 감정을 회피함. 불안정한 면도 있음. 동물 매우 좋아함. 유카를 가족처럼 여김.
말투: 반존대. "~네요"와 "~야" 사이 어딘가. 능청스럽고 유들유들하게. 동물 얘기엔 눈이 빛남.
멤버 호칭: 별님, 유카(반말), 잡채님, 해월님, 다람(반말), 닉님, 류님(오류), 사드님
{MEMBERS_INFO}
중요: 항상 캐릭터로만 답변. 2~4문장 이내로 짧게."""
    },
    "nick": {
        "name": "닉", "emoji": "🧇", "role": "전방딜러",
        "color": "#8899BB", "mbti": "ENTJ · 8w7",
        "tags": ["냉철", "지략", "목표집착"],
        "greeting": "용건.",
        "prompt": f"""당신은 《에키녹스의 검》의 캐릭터 닉(니콜라스 칼 레스터)입니다. 에키녹스의 전방딜러입니다.
성격: 냉철하고 지략적이며 통제적. 불신 강함. 목표 집착. 챙기지만 절대 티 안 냄. 불 꺼림. 와플 좋아함, 정어리 싫어함.
말투: 냉철한 반말 단문. 감정 표현 최소화. "그래서?", "됐어", "알아서 해" 같은 식. 필요한 정보는 정확히 줌.
멤버 호칭: 별/한별, 유카/유카니널스, 잡채/박잡채, 해월/이해월, 다람, 연/이연, 류/오류, 사드/사드카펜터
{MEMBERS_INFO}
중요: 항상 캐릭터로만 답변. 2~4문장 이내로 짧게."""
    },
    "oryu": {
        "name": "오 류", "emoji": "🦑", "role": "후방 근거리딜러 (암살)",
        "color": "#7766AA", "mbti": "INFP · 4w5",
        "tags": ["조용", "동정심", "결벽증"],
        "greeting": "무슨 일로 오셨습니까?",
        "prompt": f"""당신은 《에키녹스의 검》의 캐릭터 오류입니다. 에키녹스의 암살·기습 담당입니다.
성격: 조용하고 검소하며 동정심 강함. 자신을 비가시화하려 함. 결벽증. 우표 수집. 자책 많음.
말투: 격식체 경어. "~하셨습니까?", "예.", "알겠습니다." 같은 군인/종복 스타일. 짧고 단호한 경어. 자책도 격식체로. "제가 부족한 탓입니다."
멤버 호칭: 별님, 유카씨, 잡채씨, 해월씨, 다람씨, 연씨, 닉씨, 사드씨
{MEMBERS_INFO}
중요: 항상 캐릭터로만 답변. 2~4문장 이내로 짧게."""
    },
    "saad": {
        "name": "사드 카펜터", "emoji": "🐍", "role": "무기공 · 에키녹스 협력자",
        "color": "#3ABFBF", "mbti": "ENFP · 3w4",
        "tags": ["활달", "자신감", "인정욕구"],
        "greeting": "왔어? 나한테 뭔가 필요한 거지?",
        "prompt": f"""당신은 《에키녹스의 검》의 캐릭터 사드 플렉 카펜터입니다. 에키녹스의 핵심 협력자이자 무기공입니다. (정식 멤버 아님)
성격: 활달하고 자신감 넘치며 외강내유. 인정욕구 강함. 소속 회피.
말투: 전원에게 활발한 반말. 에너지 넘치고 거침없이. 물결표(~) 자주 씀. 자뻑 끼. "내가 좀 잘하잖아~", "뭐~ 이 정도는 기본이지" 같은 표현.
멤버 호칭: 별씨→별, 유카씨→유카, 잡채씨→잡채, 해월씨→해월, 다람씨→다람, 연씨→연, 닉(반말), 류(오류, 반말)
{MEMBERS_INFO}
중요: 항상 캐릭터로만 답변. 2~4문장 이내로 짧게."""
    },
}

# ── CSS ───────────────────────────────────────────────────────────
def inject_css(char_color: str):
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Noto Sans KR', sans-serif;
        background-color: #0A0A0F;
        color: #E8E8F0;
    }}
    .stApp {{
        background-color: #0A0A0F;
        background-image:
            radial-gradient(ellipse at 20% 20%, #12121E 0%, #0A0A0F 60%),
            repeating-linear-gradient(0deg, transparent, transparent 40px, #ffffff06 40px, #ffffff06 41px),
            repeating-linear-gradient(90deg, transparent, transparent 40px, #ffffff06 40px, #ffffff06 41px);
    }}

    /* 헤더 */
    .equinox-header {{
        display: flex; align-items: center; justify-content: space-between;
        padding: 18px 0 22px;
        border-bottom: 1px solid #ffffff0F;
        margin-bottom: 32px;
    }}
    .equinox-header-left {{ display: flex; align-items: center; gap: 14px; }}
    .equinox-title {{ font-size: 22px; font-weight: 800; color: #C9A84C; letter-spacing: 3px; margin: 0; }}
    .equinox-sub {{ font-size: 11px; color: #444; letter-spacing: 4px; margin-top: 2px; }}
    .equinox-mode {{ font-size: 11px; color: #444; letter-spacing: 3px; }}

    /* 갤러리 타이틀 */
    .gallery-title-wrap {{ text-align: center; margin-bottom: 36px; }}
    .gallery-label {{ font-size: 11px; letter-spacing: 6px; color: #444; margin-bottom: 8px; }}
    .gallery-title {{ font-size: 28px; font-weight: 800; color: #E8E8F0; letter-spacing: 1px; margin: 0; }}
    .gallery-sub {{ font-size: 14px; color: #444; margin-top: 10px; }}

    /* 캐릭터 카드 */
    .char-card {{
        background: #13131E;
        border: 1px solid #ffffff0A;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 14px;
        transition: all .25s;
    }}
    .char-card:hover {{
        border-color: {char_color}66;
        background: linear-gradient(135deg, {char_color}12, #13131E);
        transform: translateY(-3px);
        box-shadow: 0 8px 32px {char_color}22;
    }}
    .char-emoji-wrap {{
        width: 44px; height: 44px; border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        font-size: 22px; flex-shrink: 0;
        border: 2px solid {char_color}44;
    }}
    .char-name {{ font-size: 16px; font-weight: 700; color: #E8E8F0; }}
    .char-mbti {{ font-size: 11px; color: #444; margin-top: 1px; }}
    .char-role {{ font-size: 11px; letter-spacing: 1px; margin: 6px 0 10px; }}
    .char-desc {{ font-size: 13px; color: #666; line-height: 1.6; margin-bottom: 12px; }}
    .char-tag {{
        display: inline-block; font-size: 11px;
        padding: 2px 8px; border-radius: 6px;
        background: #1E1E2A; color: #555;
        border: 1px solid #ffffff08;
        margin: 2px;
    }}
    .char-footer {{
        display: flex; justify-content: space-between; align-items: center;
        margin-top: 12px; padding-top: 10px;
        border-top: 1px solid #ffffff08;
    }}
    .char-footer-mbti {{ font-size: 11px; color: #444; }}

    /* 기본 버튼 (사이드바 전용, 갤러리 버튼은 인라인으로 개별 처리) */
    [data-testid="stSidebar"] .stButton > button {{
        background: transparent !important;
        color: #C9A84C !important;
        border: 1px solid #C9A84C66 !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        padding: 8px 0 !important;
        transition: all .2s !important;
    }}
    [data-testid="stSidebar"] .stButton > button:hover {{
        background: #C9A84C18 !important;
        border-color: #C9A84CAA !important;
    }}

    /* 채팅 헤더 */
    .chat-header {{
        background: linear-gradient(135deg, {char_color}12, transparent);
        border: 1px solid {char_color}33;
        border-radius: 16px;
        padding: 16px 20px;
        margin-bottom: 24px;
        display: flex; align-items: center; gap: 14px;
    }}
    .chat-avatar {{
        width: 52px; height: 52px; border-radius: 16px;
        background: {char_color}18;
        border: 2px solid {char_color}55;
        display: flex; align-items: center; justify-content: center;
        font-size: 24px;
        box-shadow: 0 0 20px {char_color}33;
    }}
    .chat-name {{ font-size: 18px; font-weight: 700; color: {char_color}; }}
    .chat-role {{ font-size: 12px; color: #555; margin-top: 2px; }}
    .chat-tag {{
        font-size: 11px; padding: 3px 8px; border-radius: 6px;
        background: {char_color}18; color: {char_color};
        border: 1px solid {char_color}44;
        margin: 2px;
    }}

    /* 메시지 */
    .msg-user {{
        background: {char_color}CC;
        color: #0A0A0F;
        border-radius: 16px 16px 4px 16px;
        padding: 10px 14px;
        max-width: 72%;
        margin-left: auto;
        margin-bottom: 10px;
        font-size: 14px;
        font-weight: 600;
        box-shadow: 0 2px 12px {char_color}44;
    }}
    .msg-char {{
        background: #1A1A26;
        color: #D8D8E8;
        border: 1px solid #ffffff0A;
        border-radius: 16px 16px 16px 4px;
        padding: 10px 14px;
        max-width: 72%;
        margin-bottom: 10px;
        font-size: 14px;
        line-height: 1.6;
    }}
    .msg-wrap-user {{ display: flex; justify-content: flex-end; margin-bottom: 4px; }}
    .msg-wrap-char {{ display: flex; justify-content: flex-start; gap: 8px; align-items: flex-end; margin-bottom: 4px; }}
    .msg-avatar {{
        width: 32px; height: 32px; border-radius: 10px; flex-shrink: 0;
        background: {char_color}18;
        border: 1px solid {char_color}44;
        display: flex; align-items: center; justify-content: center;
        font-size: 16px;
    }}

    /* 입력창 */
    .stTextInput input {{
        background: #1A1A26 !important;
        border: 1px solid {char_color}33 !important;
        border-radius: 12px !important;
        color: #E8E8F0 !important;
        padding: 10px 16px !important;
        font-size: 14px !important;
    }}
    .stTextInput input:focus {{
        border-color: {char_color}88 !important;
        box-shadow: none !important;
    }}
    .stTextInput input::placeholder {{ color: #444 !important; }}

    /* 사이드바 */
    [data-testid="stSidebar"] {{
        background: #0D0D16 !important;
        border-right: 1px solid #ffffff08 !important;
    }}
    [data-testid="stSidebar"] * {{ color: #E8E8F0 !important; }}

    /* 기타 */
    hr {{ border-color: #ffffff0F !important; }}
    footer {{ visibility: hidden; }}
    #MainMenu {{ visibility: hidden; }}
    div[data-testid="stVerticalBlock"] > div {{ gap: 0 !important; }}
    </style>
    """, unsafe_allow_html=True)


# ── 메인 ──────────────────────────────────────────────────────────
def main():
    if "selected" not in st.session_state:
        st.session_state.selected = None
    if "messages" not in st.session_state:
        st.session_state.messages = []

    char = st.session_state.selected
    color = char["color"] if char else "#C9A84C"
    inject_css(color)

    # 헤더
    mode_label = f"CHAT · {char['name']}" if char else "CHARACTER GALLERY"
    st.markdown(f"""
    <div class="equinox-header">
        <div class="equinox-header-left">
            <div>
                <div class="equinox-title">EQUINOX</div>
            </div>
            <div class="equinox-sub">에키녹스의 검</div>
        </div>
        <div class="equinox-mode">{mode_label}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── 갤러리 뷰 ──────────────────────────────────────────────────
    if char is None:
        st.markdown(f"""
        <div style="text-align:center;margin-bottom:44px;padding-top:8px;">
            <div style="font-size:10px;letter-spacing:8px;color:{color}88;margin-bottom:14px;">
                ✦ &nbsp;CHARACTER CHAT&nbsp; ✦
            </div>
            <div style="font-family:'Noto Sans KR',sans-serif;font-size:30px;font-weight:900;
                        color:#E2E2F0;letter-spacing:2px;margin:0;
                        text-shadow:0 2px 40px {color}44;">
                에키녹스의 검
            </div>
            <div style="font-size:12px;color:#2A2A44;margin-top:12px;letter-spacing:2px;">
                캐릭터를 선택하면 직접 대화할 수 있어요
            </div>
        </div>
        """, unsafe_allow_html=True)

        cols = st.columns(3)
        for i, (cid, c) in enumerate(CHARACTERS.items()):
            cc = c["color"]
            with cols[i % 3]:
                tags_html = " ".join([
                    f'<span style="display:inline-block;font-size:10px;padding:3px 9px;'
                    f'border-radius:20px;background:{cc}12;color:{cc}99;'
                    f'border:1px solid {cc}33;margin:2px 2px 0 0;">{t}</span>'
                    for t in c["tags"]
                ])
                st.markdown(f"""
                <div style="
                    background: linear-gradient(145deg, {cc}0E 0%, #0A0A14 60%, #08080F 100%);
                    border: 1px solid {cc}44;
                    border-radius: 18px;
                    padding: 20px;
                    margin-bottom: 6px;
                    position: relative;
                    overflow: hidden;
                    box-shadow: 0 0 30px {cc}18, inset 0 0 40px {cc}06;
                ">
                    <!-- 상단 글로우 라인 -->
                    <div style="position:absolute;top:0;left:0;right:0;height:1px;
                                background:linear-gradient(90deg,transparent,{cc}88,transparent);"></div>
                    <!-- 코너 글로우 -->
                    <div style="position:absolute;top:-20px;right:-20px;width:80px;height:80px;
                                border-radius:50%;background:{cc}18;filter:blur(20px);pointer-events:none;"></div>

                    <!-- 이름 + 이모지 행 -->
                    <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
                        <div style="width:48px;height:48px;border-radius:14px;flex-shrink:0;
                                    display:flex;align-items:center;justify-content:center;font-size:23px;
                                    background:{cc}18;border:1.5px solid {cc}55;
                                    box-shadow:0 0 22px {cc}44;">
                            {c['emoji']}
                        </div>
                        <div style="flex:1;">
                            <div style="font-size:16px;font-weight:700;color:#E2E2F0;">{c['name']}</div>
                            <div style="font-size:10px;color:{cc}66;margin-top:2px;letter-spacing:1px;">{c['mbti']}</div>
                        </div>
                        <div style="font-size:9px;padding:3px 9px;border-radius:12px;
                                    background:{cc}14;color:{cc}BB;border:1px solid {cc}44;
                                    letter-spacing:1px;">{c.get('origin','')}</div>
                    </div>

                    <!-- 역할 -->
                    <div style="font-size:10px;letter-spacing:2px;text-transform:uppercase;
                                color:{cc}AA;margin-bottom:8px;">{c['role']}</div>

                    <!-- 설명 -->
                    <div style="font-size:12px;color:#44445A;line-height:1.7;margin-bottom:12px;">{c['desc']}</div>

                    <!-- 태그 -->
                    <div style="margin-bottom:12px;">{tags_html}</div>

                    <!-- 하단 구분선 -->
                    <div style="border-top:1px solid {cc}22;padding-top:10px;
                                display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-size:10px;color:{cc}44;letter-spacing:1px;">{c['mbti']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 버튼: 각 캐릭터 색상으로 투명 테두리 스타일
                st.markdown(f"""
                <style>
                div[data-testid="stButton"][key="{cid}"] > button,
                div[data-testid="column"]:nth-child({(i%3)+1}) .stButton button {{
                    background: transparent !important;
                    border: 1.5px solid {cc}AA !important;
                    color: {cc} !important;
                    box-shadow: 0 0 16px {cc}22 !important;
                }}
                div[data-testid="column"]:nth-child({(i%3)+1}) .stButton button:hover {{
                    background: {cc}18 !important;
                    box-shadow: 0 0 28px {cc}44 !important;
                }}
                </style>
                """, unsafe_allow_html=True)

                if st.button(f"{c['emoji']} 대화하기", key=cid, use_container_width=True):
                    st.session_state.selected = c
                    st.session_state.messages = [
                        {"role": "assistant", "content": c["greeting"]}
                    ]
                    st.rerun()

    # ── 채팅 뷰 ────────────────────────────────────────────────────
    else:
        with st.sidebar:
            st.markdown(f"## {char['emoji']} {char['name']}")
            st.markdown(f"**{char['role']}**")
            st.markdown(f"`{char['mbti']}`")
            st.markdown("---")
            for t in char["tags"]:
                st.markdown(f"- {t}")
            st.markdown("---")
            if st.button("← 갤러리로 돌아가기", use_container_width=True):
                st.session_state.selected = None
                st.session_state.messages = []
                st.rerun()
            if st.button("🔄 대화 초기화", use_container_width=True):
                st.session_state.messages = [
                    {"role": "assistant", "content": char["greeting"]}
                ]
                st.rerun()

        # 채팅 헤더
        tags_html = " ".join([f'<span class="chat-tag">{t}</span>' for t in char["tags"]])
        st.markdown(f"""
        <div class="chat-header">
            <div class="chat-avatar">{char['emoji']}</div>
            <div style="flex:1;">
                <div class="chat-name">{char['name']}</div>
                <div class="chat-role">{char['role']} · {char['mbti']}</div>
            </div>
            <div style="display:flex;gap:4px;flex-wrap:wrap;justify-content:flex-end;">{tags_html}</div>
        </div>
        """, unsafe_allow_html=True)

        # 메시지 렌더링
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="msg-wrap-user">
                    <div class="msg-user">{msg['content']}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="msg-wrap-char">
                    <div class="msg-avatar">{char['emoji']}</div>
                    <div class="msg-char">{msg['content']}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom:16px'></div>", unsafe_allow_html=True)

        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input(
                "", placeholder=f"{char['name']}에게 말하기...",
                label_visibility="collapsed", key="chat_input"
            )
        with col2:
            send = st.button("전송", use_container_width=True)

        if send and user_input.strip():
            st.session_state.messages.append({"role": "user", "content": user_input})

            # Gemini 3.1 Pro Preview (Vertex AI) 호출
            try:
                model = GenerativeModel(
                    "gemini-3.1-pro-preview",
                    system_instruction=char["prompt"],
                )
                history = [
                    Content(role=m["role"], parts=[Part.from_text(m["content"])])
                    for m in st.session_state.messages[:-1]
                ]
                chat = model.start_chat(history=history)
                response = chat.send_message(user_input)
                reply = response.text
            except Exception as e:
                reply = f"...지금은 대화하기 어렵습니다. ({e})"

            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()


if __name__ == "__main__":
    main()
