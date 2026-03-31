import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import io
import json

# ══════════════════════════════════════════════════════════════════════════════
# 페이지 기본 설정
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="🎮 Steam Dashboard",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# Steam 스타일 CSS (실제 스팀 색상 팔레트 기반)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    /* ── 전체 배경 & 기본 텍스트 ── */
    .stApp { background-color: #1b2838; color: #e8f0f7; }
    [data-testid="stSidebar"], [data-testid="stSidebar"] * {
        background-color: #171a21 !important;
        color: #e8f0f7 !important;
    }

    /* ── 제목 ── */
    h1, h2, h3, h4, h1 *, h2 *, h3 *, h4 * { color: #66c0f4 !important; }

    /* ── 텍스트 입력 ── */
    input, textarea,
    [data-baseweb="input"] input {
        background-color: #2a475e !important;
        color: #ffffff !important;
        border: 1.5px solid #4a90a4 !important;
        border-radius: 6px !important;
    }

    /* ── 메트릭 카드 ── */
    [data-testid="metric-container"] {
        background-color: #2a475e !important;
        border: 1px solid #4a90a4 !important;
        border-radius: 8px !important;
        padding: 16px !important;
    }
    [data-testid="metric-container"] * { color: #e8f0f7 !important; }
    [data-testid="stMetricValue"] { color: #66c0f4 !important; font-size: 1.6rem !important; }

    /* ── 셀렉트박스 & 멀티셀렉트: 컨테이너 ── */
    [data-baseweb="select"],
    [data-baseweb="select"] > div {
        background-color: #2a475e !important;
        border: 1.5px solid #66c0f4 !important;
        border-radius: 6px !important;
    }
    /* 선택된 값 / 입력 텍스트 */
    [data-baseweb="select"] input,
    [data-baseweb="select"] [data-testid="stMarkdownContainer"] p,
    [data-baseweb="select"] span,
    [data-baseweb="select"] div {
        background-color: #2a475e !important;
        color: #ffffff !important;
    }

    /* ── 드롭다운 팝오버 & 옵션 ── */
    /* 팝오버 최상위 컨테이너부터 전부 어둡게 */
    [data-baseweb="popover"],
    [data-baseweb="popover"] > div,
    [data-baseweb="popover"] > div > div,
    [data-baseweb="popover"] > div > div > div,
    ul[role="listbox"],
    ul[role="listbox"] *,
    [data-baseweb="menu"],
    [data-baseweb="menu"] > div,
    [data-baseweb="menu"] > div > div {
        background-color: #1e3248 !important;
        border-color: #4a90a4 !important;
    }
    li[role="option"] {
        background-color: #1e3248 !important;
        color: #e8f0f7 !important;
        font-size: 0.92rem !important;
        padding: 8px 12px !important;
    }
    li[role="option"] * { 
        background-color: #1e3248 !important;
        color: #e8f0f7 !important; 
    }
    li[role="option"]:hover,
    li[role="option"]:hover * {
        background-color: #2a6496 !important;
        color: #ffffff !important;
    }
    /* "No results" 텍스트 */
    [data-baseweb="menu"] p,
    [data-baseweb="menu"] span {
        background-color: #1e3248 !important;
        color: #a8c8e0 !important;
    }

    /* ── 멀티셀렉트 선택된 태그 ── */
    [data-baseweb="tag"] {
        background-color: #1a5276 !important;
        border: 1px solid #66c0f4 !important;
        border-radius: 4px !important;
    }
    [data-baseweb="tag"] *,
    [data-baseweb="tag"] span { 
        background-color: #1a5276 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* ── 라벨 ── */
    label, .stMultiSelect label, .stSelectbox label {
        color: #66c0f4 !important;
        font-weight: 600 !important;
    }

    /* ── 슬라이더 ── */
    .stSlider * { color: #e8f0f7 !important; }
    .stSlider [data-baseweb="slider"] div[role="slider"] {
        background-color: #66c0f4 !important;
    }

    /* ── caption ── */
    .stCaption *, [data-testid="stCaptionContainer"] * { color: #a8c8e0 !important; }

    /* ── 알림 박스 ── */
    .stAlert { background-color: #2a475e !important; border-color: #4a90a4 !important; }
    .stAlert * { color: #ffffff !important; }

    /* ── 구분선 & 푸터 ── */
    hr { border-color: #4a90a4 !important; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 색상 & 테마 상수
# ══════════════════════════════════════════════════════════════════════════════
PLOT_BG      = "#1b2838"
CHART_BG     = "#2a475e"
FONT_COLOR   = "#c7d5e0"
GRID_COLOR   = "#3d6680"
ACCENT_LIGHT = "#66c0f4"
ACCENT_DARK  = "#2a6496"


# ══════════════════════════════════════════════════════════════════════════════
# 샘플 데이터 (URL 로딩 실패 시 폴백)
# ══════════════════════════════════════════════════════════════════════════════
SAMPLE_CSV = """name,price,genres,positive,negative,owners
Counter-Strike 2,0,Action;Free to Play,1250000,320000,50000000 - 100000000
Dota 2,0,Action;Free to Play;Strategy,980000,450000,50000000 - 100000000
PUBG: BATTLEGROUNDS,29.99,Action;Adventure;Massively Multiplayer,850000,280000,10000000 - 20000000
Elden Ring,59.99,Action;RPG,620000,42000,5000000 - 10000000
Red Dead Redemption 2,59.99,Action;Adventure,530000,28000,5000000 - 10000000
Cyberpunk 2077,59.99,Action;RPG,740000,190000,10000000 - 20000000
The Witcher 3: Wild Hunt,39.99,Action;RPG,820000,24000,10000000 - 20000000
Grand Theft Auto V,29.99,Action;Adventure,710000,130000,20000000 - 50000000
Stardew Valley,14.99,RPG;Simulation;Indie,650000,14000,5000000 - 10000000
Terraria,9.99,Action;Adventure;Indie,750000,11000,10000000 - 20000000
Portal 2,9.99,Action;Adventure,780000,8500,10000000 - 20000000
Half-Life: Alyx,59.99,Action;Adventure,160000,6000,1000000 - 2000000
Hollow Knight,14.99,Action;Indie,420000,7200,5000000 - 10000000
Hades,24.99,Action;Indie;RPG,370000,6800,5000000 - 10000000
Celeste,19.99,Indie;Platformer,280000,4500,2000000 - 5000000
Disco Elysium,39.99,RPG;Adventure;Indie,120000,5500,1000000 - 2000000
Baldur's Gate 3,59.99,RPG;Adventure,620000,18000,5000000 - 10000000
Divinity: Original Sin 2,44.99,RPG;Strategy,290000,9000,2000000 - 5000000
Dark Souls III,59.99,Action;RPG,450000,32000,5000000 - 10000000
Sekiro: Shadows Die Twice,59.99,Action;Adventure,310000,18000,2000000 - 5000000
Death Stranding,39.99,Action;Adventure,180000,24000,2000000 - 5000000
Monster Hunter: World,29.99,Action;RPG,460000,22000,5000000 - 10000000
Destiny 2,0,Action;Free to Play;Massively Multiplayer,380000,210000,5000000 - 10000000
Apex Legends,0,Action;Free to Play;Massively Multiplayer,450000,180000,10000000 - 20000000
Warframe,0,Action;Free to Play;Massively Multiplayer,320000,95000,5000000 - 10000000
Path of Exile,0,Action;Free to Play;RPG,290000,55000,5000000 - 10000000
Team Fortress 2,0,Action;Free to Play,520000,310000,10000000 - 20000000
Among Us,4.99,Casual;Indie;Multiplayer,310000,28000,5000000 - 10000000
Fall Guys,0,Casual;Free to Play;Indie,180000,45000,2000000 - 5000000
Valheim,20.99,Action;Adventure;Indie,480000,14000,5000000 - 10000000
Rust,39.99,Action;Adventure;Massively Multiplayer,560000,210000,5000000 - 10000000
ARK: Survival Evolved,49.99,Action;Adventure;Massively Multiplayer,320000,220000,5000000 - 10000000
Subnautica,29.99,Action;Adventure;Indie,380000,9000,5000000 - 10000000
No Man's Sky,59.99,Action;Adventure;Simulation,240000,40000,2000000 - 5000000
Satisfactory,35.99,Early Access;Indie;Simulation,210000,4200,2000000 - 5000000
Factorio,35.00,Indie;Simulation;Strategy,260000,3800,2000000 - 5000000
RimWorld,39.99,Indie;Simulation;Strategy,290000,11000,2000000 - 5000000
Cities: Skylines,29.99,Simulation;Strategy,380000,14000,5000000 - 10000000
Civilization VI,59.99,Strategy,310000,45000,5000000 - 10000000
Total War: THREE KINGDOMS,59.99,Action;Strategy,130000,18000,1000000 - 2000000
Crusader Kings III,49.99,RPG;Simulation;Strategy,185000,10500,2000000 - 5000000
Hearts of Iron IV,39.99,Simulation;Strategy,290000,28000,2000000 - 5000000
Stellaris,39.99,Simulation;Strategy;Indie,260000,24000,2000000 - 5000000
Football Manager 2024,54.99,Simulation;Sports;Strategy,52000,12000,500000 - 1000000
FIFA 23,59.99,Sports;Simulation,42000,38000,1000000 - 2000000
Rocket League,0,Free to Play;Sports,550000,85000,10000000 - 20000000
NBA 2K24,59.99,Sports;Simulation,14000,28000,500000 - 1000000
Forza Horizon 5,59.99,Racing;Sports,160000,14000,1000000 - 2000000
Need for Speed Heat,49.99,Racing;Sports,28000,9500,500000 - 1000000
Euro Truck Simulator 2,19.99,Simulation;Indie,450000,7500,5000000 - 10000000
Garry's Mod,9.99,Indie;Simulation,680000,14000,20000000 - 50000000
The Sims 4,0,Free to Play;Life Sim;Simulation,120000,65000,5000000 - 10000000
Minecraft Dungeons,19.99,Action;Adventure;RPG,42000,8500,500000 - 1000000
It Takes Two,39.99,Action;Adventure;Co-op,145000,4200,2000000 - 5000000
A Way Out,29.99,Action;Adventure;Co-op,78000,6500,1000000 - 2000000
Phasmophobia,13.99,Early Access;Horror;Indie,320000,18000,2000000 - 5000000
Resident Evil Village,39.99,Action;Adventure;Horror,180000,11000,2000000 - 5000000
Dead by Daylight,19.99,Action;Horror,280000,110000,5000000 - 10000000
Left 4 Dead 2,9.99,Action;Co-op,590000,14000,20000000 - 50000000
Back 4 Blood,39.99,Action;Co-op,75000,28000,1000000 - 2000000
Ori and the Will of the Wisps,29.99,Action;Adventure;Indie,130000,3200,1000000 - 2000000
Cuphead,19.99,Action;Indie,220000,7800,2000000 - 5000000
Shovel Knight: Treasure Trove,24.99,Action;Adventure;Indie,58000,1800,1000000 - 2000000
Undertale,9.99,Indie;RPG,440000,9000,5000000 - 10000000
Deltarune,0,Free to Play;Indie;RPG,82000,2100,1000000 - 2000000
Dave the Diver,19.99,Adventure;Indie;RPG,145000,4500,1000000 - 2000000
Vampire Survivors,4.99,Casual;Indie;RPG,280000,4200,5000000 - 10000000
Slay the Spire,24.99,Indie;RPG;Strategy,350000,7800,5000000 - 10000000
Luck be a Landlord,14.99,Casual;Indie;Strategy,38000,1200,500000 - 1000000
Balatro,17.99,Casual;Indie;Strategy,120000,2100,1000000 - 2000000
"""


# ══════════════════════════════════════════════════════════════════════════════
# 헬퍼 함수
# ══════════════════════════════════════════════════════════════════════════════

def parse_owners(owners_str: str) -> int:
    """
    SteamSpy: '2,000,000 .. 5,000,000'
    구형 CSV: '1,000,000 - 2,000,000'
    두 형식 모두 평균값 정수로 변환. 실패 시 0 반환.
    """
    try:
        cleaned = str(owners_str).replace(",", "").replace("..", "-")
        parts   = cleaned.split("-")
        nums    = [int(p.strip()) for p in parts if p.strip().isdigit()]
        return int(np.mean(nums)) if nums else 0
    except Exception:
        return 0


def tags_to_genres(val) -> str:
    if isinstance(val, str):
        try:
            import json as _json
            val = _json.loads(val)
        except Exception:
            return val
    if not isinstance(val, dict) or not val:
        return ""
    top = sorted(val.items(), key=lambda x: x[1], reverse=True)[:5]
    return ";".join(t[0] for t in top)


@st.cache_data(show_spinner=False, ttl=86400)
def load_data() -> pd.DataFrame:
    """
    SteamSpy API:
      - top100forever / top100in2weeks / top100owned → 태그 포함 풀 데이터 (~300개)
      - all (page 0~4) → 태그 없음, 게임 수 많음 → 이후 병합해 genres 보완
      폴백: 내장 샘플 데이터
    """
    import requests

    BASE = "https://steamspy.com/api.php"

    def fetch(params):
        try:
            r = requests.get(BASE, params=params, timeout=20)
            r.raise_for_status()
            return r.json()
        except Exception:
            return {}

    # top100forever / top100in2weeks / top100owned 엔드포인트
    # → genre 문자열 + tags dict 모두 포함 → 장르 필터 확실히 작동
    rich: dict = {}
    for req in ("top100forever", "top100in2weeks", "top100owned"):
        chunk = fetch({"request": req})
        rich.update(chunk)

    records = list(rich.values())

    if not records:
        return pd.read_csv(io.StringIO(SAMPLE_CSV))

    df = pd.DataFrame(records)

    # price: 센트 → 달러
    if "price" in df.columns:
        df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0) / 100
    else:
        df["price"] = 0.0

    # ── 장르: tags dict 우선(top100은 항상 채워짐), 없으면 genre 문자열 폴백 ──
    genre_from_tags  = df["tags"].apply(tags_to_genres)          if "tags"  in df.columns else pd.Series("", index=df.index)
    genre_from_field = df["genre"].fillna("").astype(str).str.strip() if "genre" in df.columns else pd.Series("", index=df.index)

    # tags 결과 우선 사용, 비어있으면 genre 문자열 사용, 그래도 없으면 빈 값
    df["genres"] = genre_from_tags.where(genre_from_tags.str.strip() != "", genre_from_field)

    return df




@st.cache_data(show_spinner=False, ttl=3600)
def search_steam_games(query: str) -> list[dict]:
    """
    Steam Store Search API로 게임 이름 검색.
    반환: [{"id": appid, "name": "게임명"}, ...]
    """
    import requests
    if not query.strip():
        return []
    try:
        r = requests.get(
            "https://store.steampowered.com/api/storesearch/",
            params={"term": query, "l": "korean", "cc": "KR"},
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("items", [])[:10]
    except Exception:
        return []


@st.cache_data(show_spinner=False, ttl=3600)
def fetch_game_by_appid(appid: int) -> dict | None:
    """
    SteamSpy appdetails 엔드포인트로 특정 게임의 전체 데이터 가져오기.
    tags, genre, owners, reviews 등 풀 데이터 반환.
    """
    import requests
    try:
        r = requests.get(
            "https://steamspy.com/api.php",
            params={"request": "appdetails", "appid": str(appid)},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        # price: 센트 → 달러 변환
        if "price" in data:
            data["price"] = int(data.get("price", 0) or 0) / 100

        # ── 장르 추출: tags dict 우선, 없으면 genre 문자열 사용 ──────────
        genres_from_tags = tags_to_genres(data.get("tags", {}))
        genres_from_field = str(data.get("genre") or data.get("genres") or "").strip()

        if genres_from_tags:
            data["genres"] = genres_from_tags
        elif genres_from_field:
            # "Action, RPG" → "Action;RPG" 으로 통일
            data["genres"] = genres_from_field.replace(", ", ";").replace(",", ";")
        else:
            data["genres"] = ""

        # genre(단수) 컬럼도 genres 와 동일하게 맞춰 preprocess 오작동 방지
        data["genre"] = data["genres"]
        return data
    except Exception:
        return None


def preprocess(df: pd.DataFrame) -> pd.DataFrame | None:
    """전처리: 타입 변환, owners 평균화, 리뷰 비율 계산, 장르 리스트화."""
    df = df.copy()

    # genre(단수) / genres(복수) 통일: genres 없거나 비어있으면 genre로 채움
    if "genre" in df.columns and "genres" not in df.columns:
        df = df.rename(columns={"genre": "genres"})
    elif "genre" in df.columns and "genres" in df.columns:
        # genres 가 비어있는 행은 genre 값으로 채움
        mask_empty = df["genres"].isna() | (df["genres"].astype(str).str.strip() == "")
        df.loc[mask_empty, "genres"] = df.loc[mask_empty, "genre"]

    required = {"name", "price", "genres", "positive", "negative", "owners"}
    missing  = required - set(df.columns)
    if missing:
        st.error(f"⚠️ 필수 컬럼 누락: {missing}")
        return None
    df["genres"] = df["genres"].fillna("")   # SteamSpy: 장르 없는 게임 처리
    df = df.dropna(subset=["name"]).copy()
    df["price"]    = pd.to_numeric(df["price"],    errors="coerce").fillna(0)
    df["positive"] = pd.to_numeric(df["positive"], errors="coerce").fillna(0).astype(int)
    df["negative"] = pd.to_numeric(df["negative"], errors="coerce").fillna(0).astype(int)

    df["owners_num"] = df["owners"].apply(parse_owners)

    df["total_reviews"]  = df["positive"] + df["negative"]
    df["positive_ratio"] = np.where(
        df["total_reviews"] > 0,
        (df["positive"] / df["total_reviews"] * 100).round(1),
        0.0,
    )

    df["genres_list"] = df["genres"].str.split(r"[;,]").apply(
        lambda x: [g.strip() for g in x if g.strip()] if isinstance(x, list) else []
    )

    return df


def get_all_genres(df: pd.DataFrame) -> list[str]:
    genres: set[str] = set()
    for gl in df["genres_list"]:
        genres.update(gl)
    return sorted(genres - {""})


def base_layout() -> dict:
    return dict(
        paper_bgcolor=PLOT_BG,
        plot_bgcolor=CHART_BG,
        font=dict(color=FONT_COLOR, family="Segoe UI, sans-serif"),
    )


# ══════════════════════════════════════════════════════════════════════════════
# 데이터 로딩
# ══════════════════════════════════════════════════════════════════════════════
with st.spinner("🎮 Steam 데이터 불러오는 중..."):
    df_raw_loaded = load_data()

df_raw = preprocess(df_raw_loaded)

if df_raw is None:
    st.error("데이터 전처리에 실패했습니다.")
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
# 사이드바
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🎮 Steam Dashboard")
    st.caption("Steam 게임 데이터 인터랙티브 분석")
    st.markdown("---")

    # 데이터 출처 표시
    total_games = len(df_raw)
    games_with_genre = df_raw["genres_list"].apply(len).gt(0).sum()
    st.success(f"✅ {total_games:,}개 게임 로드 완료")
    st.caption(f"🎯 장르 있는 게임: {games_with_genre:,}개")
    st.markdown("---")

    # ── 장르 필터 ──────────────────────────────────────────────────────────
    all_genres      = get_all_genres(df_raw)
    selected_genres = st.multiselect(
        "🎯 장르 필터",
        options=all_genres,
        default=[],
        placeholder="전체 장르",
    )

    st.markdown("---")

    # ── 최소 리뷰 수 슬라이더 ─────────────────────────────────────────────
    max_slider = int(df_raw["total_reviews"].quantile(0.95))
    min_reviews = st.slider(
        "📝 최소 리뷰 수",
        min_value=0,
        max_value=max(max_slider, 1),
        value=50,
        step=10,
    )

    st.markdown("---")
    st.markdown("### 🔍 게임 상세 정보")
    st.caption("목록에서 선택하거나, 이름으로 직접 검색하세요.")

    # ── 게임 이름 직접 검색 ────────────────────────────────────────────────
    search_query = st.text_input(
        "🔎 게임 이름 검색",
        placeholder="",
        key="game_search_input",
    )

    searched_game_data = None  # 검색 결과 게임 데이터 (전처리 완료)

    if search_query:
        with st.spinner("검색 중..."):
            search_results = search_steam_games(search_query)

        if search_results:
            result_names = [f"{r['name']} (AppID: {r['id']})" for r in search_results]
            chosen_result = st.selectbox(
                "검색 결과",
                options=result_names,
                key="search_result_select",
            )
            chosen_idx  = result_names.index(chosen_result)
            chosen_appid = search_results[chosen_idx]["id"]

            if st.button("📋 이 게임 상세 보기", use_container_width=True):
                st.session_state["detail_appid"] = chosen_appid
                st.session_state["detail_name"]  = search_results[chosen_idx]["name"]
        else:
            st.warning("검색 결과가 없어요 😥")

    # session_state에 저장된 검색 게임이 있으면 불러오기
    if "detail_appid" in st.session_state:
        with st.spinner(f"'{st.session_state['detail_name']}' 정보 불러오는 중..."):
            raw = fetch_game_by_appid(st.session_state["detail_appid"])
        if raw:
            searched_game_data = preprocess(pd.DataFrame([raw]))
            if searched_game_data is not None and not searched_game_data.empty:
                searched_game_data = searched_game_data.iloc[0]
                st.success(f"✅ {st.session_state['detail_name']}")
            else:
                searched_game_data = None
        if st.button("❌ 검색 초기화", use_container_width=True):
            del st.session_state["detail_appid"]
            del st.session_state["detail_name"]
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# 데이터 필터링
# ══════════════════════════════════════════════════════════════════════════════
df = df_raw[df_raw["total_reviews"] >= min_reviews].copy()

if selected_genres:
    mask = df["genres_list"].apply(
        lambda gl: any(g in gl for g in selected_genres)
    )
    df = df[mask]

if df.empty:
    st.warning("⚠️ 조건에 맞는 게임이 없습니다. 필터를 조정해주세요.")
    st.stop()

# 필터링 완료 후 사이드바 게임 드롭다운
with st.sidebar:
    selected_game = st.selectbox(
        "게임 선택",
        options=df["name"].tolist(),
        index=0,
    )


# ══════════════════════════════════════════════════════════════════════════════
# 메인 화면 시작
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("# 🎮 Steam Game Analytics Dashboard")
st.markdown("---")


# ── 섹션 1: 주요 지표 ─────────────────────────────────────────────────────────
st.markdown("### 📊 주요 지표")

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric("🎮 총 게임 수", f"{len(df):,}")

with m2:
    avg_price = df[df["price"] > 0]["price"].mean()
    st.metric("💰 평균 가격", f"${avg_price:.2f}" if not np.isnan(avg_price) else "N/A")

with m3:
    avg_ratio = df["positive_ratio"].mean()
    st.metric("👍 평균 긍정 비율", f"{avg_ratio:.1f}%")

with m4:
    free_pct = (df["price"] == 0).sum() / len(df) * 100
    st.metric("🆓 무료 게임 비율", f"{free_pct:.1f}%")

st.markdown("---")


# ── 섹션 2: TOP 10 & 가격 분포 ───────────────────────────────────────────────
st.markdown("### 🔥 인기 게임 TOP 10 & 💸 가격 분포")
col1, col2 = st.columns([3, 2], gap="large")

with col1:
    top10 = (
        df.nlargest(10, "positive")[["name", "positive", "positive_ratio", "price"]]
        .copy()
    )
    top10["label"] = top10["name"].str[:35]

    fig_top10 = go.Figure(
        go.Bar(
            x=top10["positive"],
            y=top10["label"],
            orientation="h",
            marker=dict(
                color=top10["positive"],
                colorscale=[[0, ACCENT_DARK], [1, ACCENT_LIGHT]],
                showscale=False,
            ),
            text=top10["positive"].apply(lambda v: f"{v:,}"),
            textposition="outside",
            textfont=dict(color=FONT_COLOR, size=11),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "긍정 리뷰: %{x:,}<br>"
                "<extra></extra>"
            ),
        )
    )
    fig_top10.update_layout(
        **base_layout(),
        xaxis=dict(
            gridcolor=GRID_COLOR,
            title="긍정 리뷰 수",
            title_font_color=FONT_COLOR,
        ),
        yaxis=dict(
            gridcolor=GRID_COLOR,
            autorange="reversed",
        ),
        height=420,
        margin=dict(l=10, r=80, t=30, b=20),
    )
    st.plotly_chart(fig_top10, use_container_width=True)

with col2:
    priced = df[(df["price"] > 0) & (df["price"] <= 60)]

    fig_hist = px.histogram(
        priced,
        x="price",
        nbins=25,
        color_discrete_sequence=[ACCENT_LIGHT],
        labels={"price": "가격 ($)", "count": "게임 수"},
    )
    fig_hist.update_layout(
        **base_layout(),
        xaxis=dict(gridcolor=GRID_COLOR, title="가격 ($)"),
        yaxis=dict(gridcolor=GRID_COLOR, title="게임 수"),
        height=420,
        bargap=0.04,
        showlegend=False,
        margin=dict(l=10, r=10, t=30, b=20),
    )
    st.plotly_chart(fig_hist, use_container_width=True)

st.markdown("---")


# ── 섹션 3: 가격 vs 긍정 리뷰 Scatter Plot ────────────────────────────────────
st.markdown("### 📈 가격 vs 긍정 리뷰 수")
st.caption("버블 크기 = 긍정 비율 | 색상 = 긍정 비율 (높을수록 밝음)")

scatter_df = df[(df["price"] > 0) & (df["price"] < 80)].copy()
scatter_df["bubble"] = np.clip(scatter_df["positive_ratio"] / 10, 2, 18)

fig_scatter = px.scatter(
    scatter_df,
    x="price",
    y="positive",
    color="positive_ratio",
    size="bubble",
    hover_name="name",
    color_continuous_scale=[ACCENT_DARK, ACCENT_LIGHT, "#ffffff"],
    labels={
        "price":          "가격 ($)",
        "positive":       "긍정 리뷰 수",
        "positive_ratio": "긍정 비율 (%)",
    },
    hover_data={
        "price":          ":.2f",
        "positive":       ":,",
        "positive_ratio": ":.1f",
        "bubble":         False,
    },
)
fig_scatter.update_traces(
    marker=dict(line=dict(width=0.5, color="#c7d5e0"), opacity=0.85)
)
fig_scatter.update_layout(
    **base_layout(),
    xaxis=dict(gridcolor=GRID_COLOR),
    yaxis=dict(gridcolor=GRID_COLOR),
    coloraxis_colorbar=dict(
        title=dict(text="긍정 비율(%)", font=dict(color=FONT_COLOR)),
        tickfont=dict(color=FONT_COLOR),
    ),
    height=470,
    margin=dict(l=10, r=10, t=30, b=20),
)
st.plotly_chart(fig_scatter, use_container_width=True)
st.markdown("---")


# ── 섹션 4: 긍정 비율 분포 & 장르별 평균 ─────────────────────────────────────
st.markdown("### 👍 긍정 리뷰 비율 분석")
col3, col4 = st.columns(2, gap="large")

with col3:
    st.markdown("#### 비율 분포")
    fig_ratio = px.histogram(
        df,
        x="positive_ratio",
        nbins=20,
        color_discrete_sequence=["#4a90a4"],
        labels={"positive_ratio": "긍정 리뷰 비율 (%)"},
    )
    avg_r = df["positive_ratio"].mean()
    fig_ratio.add_vline(
        x=avg_r,
        line_dash="dash",
        line_color=ACCENT_LIGHT,
        annotation_text=f"평균 {avg_r:.1f}%",
        annotation_font_color=ACCENT_LIGHT,
        annotation_font_size=12,
        annotation_position="top right",
    )
    fig_ratio.update_layout(
        **base_layout(),
        xaxis=dict(gridcolor=GRID_COLOR, title="긍정 비율 (%)"),
        yaxis=dict(gridcolor=GRID_COLOR, title="게임 수"),
        height=360,
        bargap=0.04,
        showlegend=False,
        margin=dict(l=10, r=10, t=30, b=20),
    )
    st.plotly_chart(fig_ratio, use_container_width=True)

with col4:
    st.markdown("#### ⏱️ 평균 플레이타임 TOP 10")

    if "average_forever" in df.columns:
        playtime_df = df[df["average_forever"] > 0].copy()
        playtime_df["playtime_h"] = (playtime_df["average_forever"] / 60).round(1)
        top_play = playtime_df.nlargest(10, "playtime_h")[["name", "playtime_h"]].copy()
        top_play["label"] = top_play["name"].str[:30]

        fig_play = go.Figure(
            go.Bar(
                x=top_play["playtime_h"],
                y=top_play["label"],
                orientation="h",
                marker=dict(
                    color=top_play["playtime_h"],
                    colorscale=[[0, ACCENT_DARK], [1, ACCENT_LIGHT]],
                    showscale=False,
                ),
                text=top_play["playtime_h"].apply(lambda v: f"{v:,.0f}h"),
                textposition="outside",
                textfont=dict(color=FONT_COLOR, size=11),
            )
        )
        fig_play.update_layout(
            **base_layout(),
            xaxis=dict(gridcolor=GRID_COLOR, title="평균 플레이타임 (시간)"),
            yaxis=dict(gridcolor=GRID_COLOR, autorange="reversed"),
            height=360,
            margin=dict(l=10, r=70, t=30, b=20),
        )
        st.plotly_chart(fig_play, use_container_width=True)
    else:
        st.caption("플레이타임 데이터가 없습니다.")

st.markdown("---")


# ── 섹션 5: 선택한 게임 상세 정보 ────────────────────────────────────────────
st.markdown(f"### 🕹️ 게임 상세 정보")

# 검색된 게임이 있으면 우선 표시, 없으면 사이드바 드롭다운 게임 사용
if searched_game_data is not None:
    game        = searched_game_data
    detail_src  = "🔎 검색 결과"
else:
    game        = df[df["name"] == selected_game].iloc[0]
    detail_src  = "📋 목록 선택"

    # 드롭다운 게임 장르 비어있으면 appid로 자동 보완
    if not game["genres_list"] and "appid" in game.index and game["appid"]:
        with st.spinner("장르 정보 불러오는 중..."):
            raw_detail = fetch_game_by_appid(int(game["appid"]))
        if raw_detail:
            detail_df = preprocess(pd.DataFrame([raw_detail]))
            if detail_df is not None and not detail_df.empty:
                detail_row = detail_df.iloc[0]
                if detail_row["genres_list"]:
                    game = game.copy()
                    game["genres_list"] = detail_row["genres_list"]
                    game["genres"]      = detail_row["genres"]

st.markdown(f"**{game['name']}** <span style='color:#4a90a4; font-size:0.8em;'>({detail_src})</span>",
            unsafe_allow_html=True)

d1, d2, d3, d4 = st.columns(4)

with d1:
    price_label = "무료 🆓" if game["price"] == 0 else f"${game['price']:.2f}"
    st.metric("💰 가격", price_label)

with d2:
    st.metric("👍 긍정 리뷰", f"{int(game['positive']):,}")

with d3:
    st.metric("👎 부정 리뷰", f"{int(game['negative']):,}")

with d4:
    st.metric("⭐ 긍정 비율", f"{game['positive_ratio']:.1f}%")

st.markdown(" ")

g1, g2 = st.columns([1, 2], gap="large")

with g1:
    ratio_val = game["positive_ratio"]
    gauge_color = (
        "#c0392b" if ratio_val < 40
        else "#d4a017" if ratio_val < 70
        else ACCENT_LIGHT
    )
    fig_gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=ratio_val,
            number={"suffix": "%", "font": {"color": FONT_COLOR, "size": 28}},
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickcolor": FONT_COLOR,
                    "tickfont": {"color": FONT_COLOR},
                },
                "bar":         {"color": gauge_color},
                "bgcolor":     CHART_BG,
                "bordercolor": GRID_COLOR,
                "steps": [
                    {"range": [0,  40], "color": "#3d1a1a"},
                    {"range": [40, 70], "color": "#3d3010"},
                    {"range": [70, 100], "color": "#1a3040"},
                ],
                "threshold": {
                    "line":      {"color": ACCENT_LIGHT, "width": 3},
                    "thickness": 0.75,
                    "value":     ratio_val,
                },
            },
            title={"text": "긍정 리뷰 비율", "font": {"color": FONT_COLOR, "size": 14}},
        )
    )
    fig_gauge.update_layout(
        paper_bgcolor=PLOT_BG,
        font=dict(color=FONT_COLOR),
        height=280,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

with g2:
    st.markdown(" ")
    info_col1, info_col2 = st.columns(2)

    with info_col1:
        st.markdown("**🎯 장르**")
        genres_str = ", ".join(game["genres_list"]) if game["genres_list"] else "정보 없음"
        st.markdown(genres_str)

        st.markdown(" ")
        st.markdown("**📝 총 리뷰 수**")
        st.markdown(f"{int(game['total_reviews']):,} 개")

    with info_col2:
        st.markdown("**👥 추정 소유자 수**")
        owners_val = int(game["owners_num"])
        st.markdown(f"{owners_val:,} 명" if owners_val > 0 else "정보 없음")

        st.markdown(" ")
        st.markdown("**🏷️ 원본 owners 값**")
        st.markdown(str(game["owners"]))


# ══════════════════════════════════════════════════════════════════════════════
# 푸터
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#4a90a4; font-size:0.8em; padding-bottom:10px;'>"
    "🎮 Steam Game Analytics Dashboard &nbsp;|&nbsp; Powered by Streamlit & Plotly"
    "</div>",
    unsafe_allow_html=True,
)
