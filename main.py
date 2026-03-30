import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

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
    /* 전체 앱 배경 */
    .stApp { background-color: #1b2838; color: #c7d5e0; }

    /* 사이드바 */
    [data-testid="stSidebar"] { background-color: #171a21 !important; }
    [data-testid="stSidebar"] * { color: #c7d5e0 !important; }

    /* 제목 */
    h1, h2, h3, h4 { color: #66c0f4 !important; }

    /* 일반 텍스트 */
    p, label, div, span, .stMarkdown { color: #c7d5e0 !important; }

    /* 메트릭 카드 */
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

    /* selectbox / multiselect */
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        background-color: #2a475e !important;
        color: #c7d5e0 !important;
        border-color: #4a90a4 !important;
    }

    /* 슬라이더 */
    .stSlider > div { color: #c7d5e0 !important; }
    .stSlider [data-baseweb="slider"] div[role="slider"] {
        background-color: #66c0f4 !important;
    }

    /* 파일 업로더 */
    [data-testid="stFileUploader"] {
        background-color: #2a475e;
        border: 1px dashed #4a90a4;
        border-radius: 8px;
        padding: 8px;
    }

    /* 구분선 */
    hr { border-color: #4a90a4 !important; }

    /* 경고/에러 박스 */
    .stAlert { background-color: #2a475e !important; }

    /* 푸터 */
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 색상 & 테마 상수
# ══════════════════════════════════════════════════════════════════════════════
PLOT_BG      = "#1b2838"   # 차트 외부 배경
CHART_BG     = "#2a475e"   # 차트 내부 배경
FONT_COLOR   = "#c7d5e0"   # 기본 텍스트
GRID_COLOR   = "#3d6680"   # 그리드선
ACCENT_LIGHT = "#66c0f4"   # 스팀 밝은 파랑
ACCENT_DARK  = "#2a6496"   # 스팀 어두운 파랑


# ══════════════════════════════════════════════════════════════════════════════
# 헬퍼 함수
# ══════════════════════════════════════════════════════════════════════════════

def parse_owners(owners_str: str) -> int:
    """
    '1,000,000 - 2,000,000' 형태의 owners 문자열을 평균값 정수로 변환.
    파싱 실패 시 0 반환.
    """
    try:
        cleaned = str(owners_str).replace(",", "").replace(".", "")
        parts   = cleaned.split("-")
        nums    = [int(p.strip()) for p in parts if p.strip().isdigit()]
        return int(np.mean(nums)) if nums else 0
    except Exception:
        return 0


def load_and_preprocess(uploaded_file=None) -> pd.DataFrame | None:
    """
    CSV 로드 및 전처리.
    - uploaded_file 이 있으면 그걸 사용, 없으면 steam_games.csv 시도.
    - 전처리: 타입 변환, owners 평균화, 리뷰 비율 계산, 장르 리스트화.
    """
    try:
        df = pd.read_csv(uploaded_file) if uploaded_file else pd.read_csv("steam_games.csv")
    except FileNotFoundError:
        return None

    # 필수 컬럼 검증
    required = {"name", "price", "genres", "positive", "negative", "owners"}
    missing  = required - set(df.columns)
    if missing:
        st.error(f"⚠️ 필수 컬럼 누락: {missing}")
        return None

    # 기본 정제
    df = df.dropna(subset=["name", "genres"]).copy()
    df["price"]    = pd.to_numeric(df["price"],    errors="coerce").fillna(0)
    df["positive"] = pd.to_numeric(df["positive"], errors="coerce").fillna(0).astype(int)
    df["negative"] = pd.to_numeric(df["negative"], errors="coerce").fillna(0).astype(int)

    # owners → 평균 정수
    df["owners_num"] = df["owners"].apply(parse_owners)

    # 리뷰 관련 파생 컬럼
    df["total_reviews"]  = df["positive"] + df["negative"]
    df["positive_ratio"] = np.where(
        df["total_reviews"] > 0,
        (df["positive"] / df["total_reviews"] * 100).round(1),
        0.0,
    )

    # 장르 문자열 → 리스트 (';' 또는 ',' 구분 모두 처리)
    df["genres_list"] = df["genres"].str.split(r"[;,]").apply(
        lambda x: [g.strip() for g in x if g.strip()] if isinstance(x, list) else []
    )

    return df


def get_all_genres(df: pd.DataFrame) -> list[str]:
    """데이터프레임 내 전체 장르 목록(중복 제거, 정렬) 반환."""
    genres: set[str] = set()
    for gl in df["genres_list"]:
        genres.update(gl)
    return sorted(genres - {""})


def base_layout() -> dict:
    """모든 Plotly 차트에 공통 적용할 layout 딕셔너리."""
    return dict(
        paper_bgcolor=PLOT_BG,
        plot_bgcolor=CHART_BG,
        font=dict(color=FONT_COLOR, family="Segoe UI, sans-serif"),
        margin=dict(l=10, r=10, t=30, b=20),
    )


# ══════════════════════════════════════════════════════════════════════════════
# 사이드바
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🎮 Steam Dashboard")
    st.caption("Steam 게임 데이터 인터랙티브 분석")
    st.markdown("---")

    # CSV가 없을 경우를 대비한 업로더
    uploaded = st.file_uploader("📂 CSV 업로드 (파일 없을 때)", type="csv")
    st.markdown("---")

    # 데이터 로드
    df_raw = load_and_preprocess(uploaded)

    if df_raw is None:
        st.error(
            "❌ `steam_games.csv` 파일을 찾을 수 없습니다.\n\n"
            "위 업로더로 CSV를 직접 올려주세요."
        )
        st.stop()

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
    # 게임 선택은 필터링 후 옵션이 확정되므로, placeholder 먼저 표시


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
    # 긍정 리뷰 수 기준 TOP 10
    top10 = (
        df.nlargest(10, "positive")[["name", "positive", "positive_ratio", "price"]]
        .copy()
    )
    top10["label"] = top10["name"].str[:35]  # 긴 이름 truncate

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
    # 가격 히스토그램 ($0.01 ~ $60 구간만)
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
    )
    st.plotly_chart(fig_hist, use_container_width=True)

st.markdown("---")


# ── 섹션 3: 가격 vs 긍정 리뷰 Scatter Plot ────────────────────────────────────
st.markdown("### 📈 가격 vs 긍정 리뷰 수")
st.caption("버블 크기 = 긍정 비율 | 색상 = 긍정 비율 (높을수록 밝음)")

scatter_df = df[(df["price"] > 0) & (df["price"] < 80)].copy()
# 버블 크기: 긍정 비율 기반, 최소·최대 clamp
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
        title="긍정 비율(%)",
        tickfont=dict(color=FONT_COLOR),
        titlefont=dict(color=FONT_COLOR),
    ),
    height=470,
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
        annotation_font=dict(color=ACCENT_LIGHT, size=12),
        annotation_position="top right",
    )
    fig_ratio.update_layout(
        **base_layout(),
        xaxis=dict(gridcolor=GRID_COLOR, title="긍정 비율 (%)"),
        yaxis=dict(gridcolor=GRID_COLOR, title="게임 수"),
        height=360,
        bargap=0.04,
        showlegend=False,
    )
    st.plotly_chart(fig_ratio, use_container_width=True)

with col4:
    st.markdown("#### 장르별 평균 긍정 비율 TOP 10")

    # 장르 단위로 행 펼치기
    genre_rows = [
        {"genre": g, "positive_ratio": row["positive_ratio"]}
        for _, row in df.iterrows()
        for g in row["genres_list"]
        if g
    ]
    genre_df  = pd.DataFrame(genre_rows)
    genre_agg = (
        genre_df.groupby("genre")["positive_ratio"]
        .agg(mean="mean", count="count")
        .reset_index()
    )
    genre_top = genre_agg[genre_agg["count"] >= 5].nlargest(10, "mean")

    fig_genre = go.Figure(
        go.Bar(
            x=genre_top["mean"],
            y=genre_top["genre"],
            orientation="h",
            marker=dict(
                color=genre_top["mean"],
                colorscale=[[0, ACCENT_DARK], [1, ACCENT_LIGHT]],
                showscale=False,
            ),
            text=genre_top["mean"].apply(lambda v: f"{v:.1f}%"),
            textposition="outside",
            textfont=dict(color=FONT_COLOR, size=11),
        )
    )
    fig_genre.update_layout(
        **base_layout(),
        xaxis=dict(gridcolor=GRID_COLOR, title="평균 긍정 비율 (%)", range=[0, 108]),
        yaxis=dict(gridcolor=GRID_COLOR, autorange="reversed"),
        height=360,
        margin=dict(l=10, r=70, t=30, b=20),
    )
    st.plotly_chart(fig_genre, use_container_width=True)

st.markdown("---")


# ── 섹션 5: 선택한 게임 상세 정보 ────────────────────────────────────────────
st.markdown(f"### 🕹️ 게임 상세 정보")
st.markdown(f"**{selected_game}**")

game = df[df["name"] == selected_game].iloc[0]

# 4개 메트릭
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

# 게이지 + 텍스트 정보
g1, g2 = st.columns([1, 2], gap="large")

with g1:
    # 긍정 비율 게이지
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
