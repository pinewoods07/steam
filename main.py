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

st.markdown("""
<style>
    .stApp { background-color: #1b2838; color: #c7d5e0; }
    [data-testid="stSidebar"] { background-color: #171a21 !important; }
    [data-testid="stSidebar"] * { color: #c7d5e0 !important; }
    h1, h2, h3, h4 { color: #66c0f4 !important; }
    p, label, div, span, .stMarkdown { color: #c7d5e0 !important; }
    [data-testid="metric-container"] {
        background-color: #2a475e;
        border: 1px solid #4a90a4;
        border-radius: 8px;
        padding: 16px;
    }
    [data-testid="metric-container"] label { color: #8fb8d1 !important; }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #66c0f4 !important;
        font-size: 1.6rem !important;
    }
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        background-color: #2a475e !important;
        color: #c7d5e0 !important;
        border-color: #4a90a4 !important;
    }
    .stSlider > div { color: #c7d5e0 !important; }
    .stSlider [data-baseweb="slider"] div[role="slider"] {
        background-color: #66c0f4 !important;
    }
    hr { border-color: #4a90a4 !important; }
    .stAlert { background-color: #2a475e !important; }
    footer { visibility: hidden; }

    /* 최소 리뷰 수 원형 프리셋 버튼 */
    div[data-testid="stSidebar"] .dot-btn button {
        border-radius: 50% !important;
        width: 46px !important;
        height: 46px !important;
        min-height: 46px !important;
        padding: 0 !important;
        font-size: 0 !important;
        background: radial-gradient(circle, #1e3a1e 60%, #0d1f0d 100%) !important;
        border: 2px solid #aaff44 !important;
        box-shadow: 0 0 10px #aaff4466, inset 0 0 6px #aaff4422 !important;
        cursor: pointer !important;
        transition: all 0.2s !important;
        display: block !important;
        margin: 0 auto !important;
    }
    div[data-testid="stSidebar"] .dot-btn button:hover,
    div[data-testid="stSidebar"] .dot-btn button:focus {
        background: radial-gradient(circle, #aaff44 30%, #66cc00 100%) !important;
        box-shadow: 0 0 18px #aaff44cc, 0 0 6px #aaff44 !important;
        transform: scale(1.12) !important;
        border-color: #ccff77 !important;
    }
</style>
""", unsafe_allow_html=True)

PLOT_BG      = "#1b2838"
CHART_BG     = "#2a475e"
FONT_COLOR   = "#c7d5e0"
GRID_COLOR   = "#3d6680"
ACCENT_LIGHT = "#66c0f4"
ACCENT_DARK  = "#2a6496"

SAMPLE_CSV = """name,price,genres,positive,negative,owners,average_forever
Counter-Strike 2,0,Action;Free to Play,1250000,320000,50000000 - 100000000,1200
Dota 2,0,Action;Free to Play;Strategy,980000,450000,50000000 - 100000000,3000
PUBG: BATTLEGROUNDS,29.99,Action;Massively Multiplayer,850000,280000,10000000 - 20000000,900
Elden Ring,59.99,Action;RPG,620000,42000,5000000 - 10000000,600
Cyberpunk 2077,59.99,Action;RPG,740000,190000,10000000 - 20000000,480
The Witcher 3: Wild Hunt,39.99,Action;RPG,820000,24000,10000000 - 20000000,720
Grand Theft Auto V,29.99,Action;Adventure,710000,130000,20000000 - 50000000,540
Stardew Valley,14.99,RPG;Simulation;Indie,650000,14000,5000000 - 10000000,360
Terraria,9.99,Action;Adventure;Indie,750000,11000,10000000 - 20000000,480
Portal 2,9.99,Action;Adventure,780000,8500,10000000 - 20000000,300
"""

# ══════════════════════════════════════════════════════════════════════════════
# 모듈 레벨 헬퍼 (load_data / fetch_game_by_appid 모두에서 사용)
# ══════════════════════════════════════════════════════════════════════════════

def tags_to_genres(val) -> str:
    """tags dict(또는 JSON 문자열) → 상위 5개 태그를 세미콜론으로 연결."""
    if isinstance(val, str):
        try:
            val = json.loads(val)
        except Exception:
            return val  # 이미 "Action;RPG" 형태면 그대로 반환
    if not isinstance(val, dict) or not val:
        return ""
    top = sorted(val.items(), key=lambda x: x[1], reverse=True)[:5]
    return ";".join(t[0] for t in top)


def parse_owners(owners_str: str) -> int:
    """'2,000,000 .. 5,000,000' 또는 '1,000,000 - 2,000,000' → 평균 정수."""
    try:
        cleaned = str(owners_str).replace(",", "").replace("..", "-")
        parts   = cleaned.split("-")
        nums    = [int(p.strip()) for p in parts if p.strip().isdigit()]
        return int(np.mean(nums)) if nums else 0
    except Exception:
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# 데이터 로딩
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False, ttl=86400)
def load_data() -> pd.DataFrame:
    """
    SteamSpy API:
      1) top100forever / top100in2weeks / top100owned → tags 포함 풀 데이터
      2) all (page 0~19) → 약 19,000개 게임, tags 없음
      rich 데이터로 bulk 덮어써서 tags 보존.
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

    # ── 1단계: tags 포함 엔드포인트 ───────────────────────────────────────────
    rich: dict = {}
    for req in ("top100forever", "top100in2weeks", "top100owned"):
        rich.update(fetch({"request": req}))

    # ── 2단계: all 엔드포인트 (page 0~19, 최대 ~19,000개) ────────────────────
    bulk: dict = {}
    for page in range(20):
        data = fetch({"request": "all", "page": page})
        if not data:
            break
        bulk.update(data)

    # rich(tags 있는 게임)로 bulk 덮어쓰기
    bulk.update(rich)
    records = list(bulk.values())

    if not records:
        return pd.read_csv(io.StringIO(SAMPLE_CSV))

    df = pd.DataFrame(records)

    # price: 센트 → 달러
    if "price" in df.columns:
        df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0) / 100
    else:
        df["price"] = 0.0

    # genres 합성:
    #   - tags 컬럼(rich 게임): tags_to_genres 변환
    #   - genres 컬럼(all 게임): SteamSpy가 비워서 줌 → 그대로 사용
    #   tags 결과가 있으면 우선, 없으면 기존 genres 값 사용
    genre_from_tags = (
        df["tags"].apply(tags_to_genres)
        if "tags" in df.columns
        else pd.Series("", index=df.index)
    )
    genre_from_bulk = df["genres"].fillna("") if "genres" in df.columns else pd.Series("", index=df.index)
    df["genres"] = genre_from_tags.where(genre_from_tags != "", genre_from_bulk)

    return df


@st.cache_data(show_spinner=False, ttl=3600)
def search_steam_games(query: str) -> list[dict]:
    """Steam Store Search API로 게임 이름 검색."""
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
    """SteamSpy appdetails로 특정 게임 전체 데이터 (tags 포함)."""
    import requests
    try:
        r = requests.get(
            "https://steamspy.com/api.php",
            params={"request": "appdetails", "appid": str(appid)},
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()
        if "price" in data:
            data["price"] = int(data.get("price", 0) or 0) / 100
        # tags → genres (tags_to_genres는 이제 모듈 레벨)
        genre = tags_to_genres(data.get("tags", {}))
        if not genre and data.get("genre"):
            genre = data["genre"]
        data["genres"] = genre
        return data
    except Exception:
        return None


def preprocess(df: pd.DataFrame) -> pd.DataFrame | None:
    """전처리: 타입 변환, owners 평균화, 리뷰 비율 계산, 장르 리스트화."""
    df = df.copy()

    # genres 컬럼 보장
    if "genres" not in df.columns:
        df["genres"] = ""
    df["genres"] = df["genres"].fillna("")

    required = {"name", "price", "genres", "positive", "negative", "owners"}
    missing  = required - set(df.columns)
    if missing:
        st.error(f"⚠️ 필수 컬럼 누락: {missing}")
        return None

    df = df.dropna(subset=["name"]).copy()
    df["price"]    = pd.to_numeric(df["price"],    errors="coerce").fillna(0)
    df["positive"] = pd.to_numeric(df["positive"], errors="coerce").fillna(0).astype(int)
    df["negative"] = pd.to_numeric(df["negative"], errors="coerce").fillna(0).astype(int)
    df["owners_num"]     = df["owners"].apply(parse_owners)
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

    total_games = len(df_raw)
    st.success(f"✅ {total_games:,}개 게임 로드 완료")
    st.markdown("---")



    st.markdown("**📝 최소 리뷰 수**")
    presets = [("전체", 0), ("50", 50), ("500", 500), ("5000", 5000)]
    preset_cols = st.columns(4)
    for i, (label, val) in enumerate(presets):
        with preset_cols[i]:
            # 라벨 (숫자/텍스트) 위에
            st.markdown(
                f"<div style='text-align:center;color:#aaff44;font-size:0.75em;"
                f"font-weight:600;margin-bottom:4px;letter-spacing:0.02em'>{label}</div>",
                unsafe_allow_html=True,
            )
            # 원형 버튼 (점처럼)
            st.markdown('<div class="dot-btn">', unsafe_allow_html=True)
            if st.button("●", key=f"preset_{val}", use_container_width=False):
                st.session_state["min_reviews"] = val
            st.markdown('</div>', unsafe_allow_html=True)

    custom_val = st.number_input(
        "직접 입력",
        min_value=0,
        value=st.session_state.get("min_reviews", 50),
        step=1,
        label_visibility="collapsed",
        placeholder="숫자 직접 입력...",
        key="min_reviews_input",
    )
    # number_input 변경 시 session_state 동기화
    if custom_val != st.session_state.get("min_reviews", 50):
        st.session_state["min_reviews"] = custom_val

    min_reviews = st.session_state.get("min_reviews", 50)
    st.markdown("---")
    st.markdown("### 🔍 게임 상세 정보")
    st.caption("목록에서 선택하거나, 이름으로 직접 검색하세요.")

    search_query = st.text_input(
        "🔎 게임 이름 검색",
        placeholder="두 글자 이상 입력하면 자동으로 검색돼요",
        key="game_search_input",
    )

    searched_game_data = None

    # 2글자 이상이면 자동으로 검색 (버튼 없음)
    if len(search_query) >= 2:
        with st.spinner("검색 중..."):
            search_results = search_steam_games(search_query)

        if search_results:
            result_names = [r["name"] for r in search_results]
            chosen_name  = st.selectbox(
                "검색 결과 (선택하면 바로 적용)",
                options=result_names,
                key="search_result_select",
            )
            chosen_idx   = result_names.index(chosen_name)
            chosen_appid = search_results[chosen_idx]["id"]
            # 선택이 바뀌면 바로 session_state 업데이트
            if (st.session_state.get("detail_appid") != chosen_appid):
                st.session_state["detail_appid"] = chosen_appid
                st.session_state["detail_name"]  = chosen_name
        else:
            st.caption("검색 결과가 없어요 😥")

    elif search_query:
        st.caption("두 글자 이상 입력해주세요")

    # 검색 초기화 버튼 (검색어 있을 때만)
    if "detail_appid" in st.session_state and not search_query:
        if st.button("❌ 검색 초기화", use_container_width=True):
            del st.session_state["detail_appid"]
            del st.session_state["detail_name"]
            st.rerun()

    if "detail_appid" in st.session_state:
        with st.spinner(f"'{st.session_state['detail_name']}' 불러오는 중..."):
            raw = fetch_game_by_appid(st.session_state["detail_appid"])
        if raw:
            searched_game_data = preprocess(pd.DataFrame([raw]))
            if searched_game_data is not None and not searched_game_data.empty:
                searched_game_data = searched_game_data.iloc[0]
            else:
                searched_game_data = None


# ══════════════════════════════════════════════════════════════════════════════
# 데이터 필터링
# ══════════════════════════════════════════════════════════════════════════════
df = df_raw[df_raw["total_reviews"] >= min_reviews].copy()


if df.empty:
    st.warning("⚠️ 조건에 맞는 게임이 없습니다. 필터를 조정해주세요.")
    st.stop()




# ══════════════════════════════════════════════════════════════════════════════
# 메인 화면
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("# 🎮 Steam Game Analytics Dashboard")
st.markdown("---")

# ── 섹션 1: 주요 지표
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

# ── 섹션 2: TOP 10 & 가격 분포
st.markdown("### 🔥 인기 게임 TOP 10 & 💸 가격 분포")
col1, col2 = st.columns([3, 2], gap="large")

with col1:
    top10 = df.nlargest(10, "positive")[["name", "positive", "positive_ratio", "price"]].copy()
    top10["label"] = top10["name"].str[:35]
    fig_top10 = go.Figure(go.Bar(
        x=top10["positive"], y=top10["label"], orientation="h",
        marker=dict(color=top10["positive"], colorscale=[[0, ACCENT_DARK], [1, ACCENT_LIGHT]], showscale=False),
        text=top10["positive"].apply(lambda v: f"{v:,}"),
        textposition="outside", textfont=dict(color=FONT_COLOR, size=11),
        hovertemplate="<b>%{y}</b><br>긍정 리뷰: %{x:,}<extra></extra>",
    ))
    fig_top10.update_layout(
        **base_layout(),
        xaxis=dict(gridcolor=GRID_COLOR, title="긍정 리뷰 수", title_font_color=FONT_COLOR),
        yaxis=dict(gridcolor=GRID_COLOR, autorange="reversed"),
        height=420, margin=dict(l=10, r=80, t=30, b=20),
    )
    st.plotly_chart(fig_top10, use_container_width=True)

with col2:
    priced = df[(df["price"] > 0) & (df["price"] <= 60)]
    fig_hist = px.histogram(priced, x="price", nbins=25,
                            color_discrete_sequence=[ACCENT_LIGHT],
                            labels={"price": "가격 ($)", "count": "게임 수"})
    fig_hist.update_layout(
        **base_layout(),
        xaxis=dict(gridcolor=GRID_COLOR, title="가격 ($)"),
        yaxis=dict(gridcolor=GRID_COLOR, title="게임 수"),
        height=420, bargap=0.04, showlegend=False,
        margin=dict(l=10, r=10, t=30, b=20),
    )
    st.plotly_chart(fig_hist, use_container_width=True)

st.markdown("---")

# ── 섹션 3: Scatter Plot
st.markdown("### 📈 가격 vs 긍정 리뷰 수")
st.caption("버블 크기 = 긍정 비율 | 색상 = 긍정 비율 (높을수록 밝음)")
scatter_df = df[(df["price"] > 0) & (df["price"] < 80)].copy()
scatter_df["bubble"] = np.clip(scatter_df["positive_ratio"] / 10, 2, 18)
fig_scatter = px.scatter(
    scatter_df, x="price", y="positive", color="positive_ratio", size="bubble",
    hover_name="name",
    color_continuous_scale=[ACCENT_DARK, ACCENT_LIGHT, "#ffffff"],
    labels={"price": "가격 ($)", "positive": "긍정 리뷰 수", "positive_ratio": "긍정 비율 (%)"},
    hover_data={"price": ":.2f", "positive": ":,", "positive_ratio": ":.1f", "bubble": False},
)
fig_scatter.update_traces(marker=dict(line=dict(width=0.5, color="#c7d5e0"), opacity=0.85))
fig_scatter.update_layout(
    **base_layout(),
    xaxis=dict(gridcolor=GRID_COLOR),
    yaxis=dict(gridcolor=GRID_COLOR),
    coloraxis_colorbar=dict(
        title=dict(text="긍정 비율(%)", font=dict(color=FONT_COLOR)),
        tickfont=dict(color=FONT_COLOR),
    ),
    height=470, margin=dict(l=10, r=10, t=30, b=20),
)
st.plotly_chart(fig_scatter, use_container_width=True)
st.markdown("---")

# ── 섹션 4: 긍정 비율 분포 & 평균 플레이타임 TOP 10
st.markdown("### 👍 긍정 리뷰 비율 분석")
col3, col4 = st.columns(2, gap="large")

with col3:
    st.markdown("#### 비율 분포")
    fig_ratio = px.histogram(df, x="positive_ratio", nbins=20,
                             color_discrete_sequence=["#4a90a4"],
                             labels={"positive_ratio": "긍정 리뷰 비율 (%)"})
    avg_r = df["positive_ratio"].mean()
    fig_ratio.add_vline(x=avg_r, line_dash="dash", line_color=ACCENT_LIGHT,
                        annotation_text=f"평균 {avg_r:.1f}%",
                        annotation_font_color=ACCENT_LIGHT, annotation_font_size=12,
                        annotation_position="top right")
    fig_ratio.update_layout(
        **base_layout(),
        xaxis=dict(gridcolor=GRID_COLOR, title="긍정 비율 (%)"),
        yaxis=dict(gridcolor=GRID_COLOR, title="게임 수"),
        height=360, bargap=0.04, showlegend=False,
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
        fig_play = go.Figure(go.Bar(
            x=top_play["playtime_h"], y=top_play["label"], orientation="h",
            marker=dict(color=top_play["playtime_h"],
                        colorscale=[[0, ACCENT_DARK], [1, ACCENT_LIGHT]], showscale=False),
            text=top_play["playtime_h"].apply(lambda v: f"{v:,.0f}h"),
            textposition="outside", textfont=dict(color=FONT_COLOR, size=11),
        ))
        fig_play.update_layout(
            **base_layout(),
            xaxis=dict(gridcolor=GRID_COLOR, title="평균 플레이타임 (시간)"),
            yaxis=dict(gridcolor=GRID_COLOR, autorange="reversed"),
            height=360, margin=dict(l=10, r=70, t=30, b=20),
        )
        st.plotly_chart(fig_play, use_container_width=True)
    else:
        st.caption("플레이타임 데이터가 없습니다.")

st.markdown("---")

# ── 섹션 5: 게임 상세 정보
st.markdown("### 🕹️ 게임 상세 정보")

if searched_game_data is None:
    st.info("👈 사이드바에서 게임을 검색해보세요!")
    st.stop()

game = searched_game_data
st.markdown(
    f"**{game['name']}** <span style='color:#4a90a4; font-size:0.8em;'>(🔎 검색 결과)</span>",
    unsafe_allow_html=True,
)

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
    gauge_color = "#c0392b" if ratio_val < 40 else "#d4a017" if ratio_val < 70 else ACCENT_LIGHT
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number", value=ratio_val,
        number={"suffix": "%", "font": {"color": FONT_COLOR, "size": 28}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": FONT_COLOR, "tickfont": {"color": FONT_COLOR}},
            "bar": {"color": gauge_color},
            "bgcolor": CHART_BG, "bordercolor": GRID_COLOR,
            "steps": [
                {"range": [0,  40], "color": "#3d1a1a"},
                {"range": [40, 70], "color": "#3d3010"},
                {"range": [70, 100], "color": "#1a3040"},
            ],
            "threshold": {"line": {"color": ACCENT_LIGHT, "width": 3}, "thickness": 0.75, "value": ratio_val},
        },
        title={"text": "긍정 리뷰 비율", "font": {"color": FONT_COLOR, "size": 14}},
    ))
    fig_gauge.update_layout(
        paper_bgcolor=PLOT_BG, font=dict(color=FONT_COLOR),
        height=280, margin=dict(l=20, r=20, t=60, b=20),
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

with g2:
    st.markdown(" ")
    info_col1, info_col2 = st.columns(2)

    with info_col1:
        st.markdown("**🎯 장르**")
        # genres_list 우선, 없으면 raw genres 문자열, 그것도 없으면 정보 없음
        if game["genres_list"]:
            genres_str = ", ".join(game["genres_list"])
        elif game.get("genres"):
            genres_str = str(game["genres"]).replace(";", ", ")
        else:
            genres_str = "정보 없음"
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

# ── 푸터
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#4a90a4; font-size:0.8em; padding-bottom:10px;'>"
    "🎮 Steam Game Analytics Dashboard &nbsp;|&nbsp; Powered by Streamlit & Plotly"
    "</div>",
    unsafe_allow_html=True,
)
