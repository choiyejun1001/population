import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# 페이지 기본 설정 (타이틀 및 레이아웃)
st.set_page_config(
    page_title="동네별 인구 피라미드",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide",
)


# -----------------------------------------------------------------------------
# 1. 데이터 불러오기 및 전처리 (캐싱 적용)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # GitHub 저장소의 raw 파일 다운로드 주소
    url = "https://raw.githubusercontent.com/choiyejun1001/population/main/population_ts_yearly_gender.zip"

    # zip 파일 자동 압축 해제 읽기 (pandas 기본 기능 사용)
    df = pd.read_csv(url, compression="zip")

    # 1. 데이터에 존재하는 연도 중 가장 최신 연도만 추출
    latest_year = df["연도"].max()
    df_latest = df[df["연도"] == latest_year].copy()

    return df_latest, latest_year


# 데이터 로딩 실행
df, latest_year = load_data()


# -----------------------------------------------------------------------------
# 2. 화면 헤더 및 기본 안내 (따뜻한 톤)
# -----------------------------------------------------------------------------
st.title("👨‍👩‍👧‍👦 우리 동네 인구 피라미드 탐색기")
st.write(
    f"안녕하세요! 이 앱은 **{latest_year}년 기준** 전국 읍·면·동의 나이별 인구 구조를 쉽고 한눈에 볼 수 있도록 도움을 드려요."
)
st.caption(
    "💡 시도, 시군구, 읍면동을 선택하시면 오른쪽과 왼쪽에 남녀 인구가 배치된 인구 피라미드 그래프가 짜잔 나타납니다!"
)
st.divider()


# -----------------------------------------------------------------------------
# 3. 사용자 지역 선택 (3단계 연결 드롭다운)
# -----------------------------------------------------------------------------
st.subheader("📍 안내받고 싶은 지역을 선택해 주세요")

col1, col2, col3 = st.columns(3)

with col1:
    # 1단계: 시도 선택 (None/NaN 값 제외 및 정렬)
    sido_list = sorted(df["시도"].dropna().unique())
    selected_sido = st.selectbox("1. 시·도 선택", sido_list)

# 선택한 시도에 해당하는 데이터만 1차 필터링
df_sido = df[df["시도"] == selected_sido]

with col2:
    # 2단계: 시군구 선택
    sigungu_list = sorted(df_sido["시군구"].dropna().unique())
    selected_sigungu = st.selectbox("2. 시·군·구 선택", sigungu_list)

# 선택한 시군구에 해당하는 데이터만 2차 필터링
df_sigungu = df_sido[df_sido["시군구"] == selected_sigungu]

with col3:
    # 3단계: 읍·면·동 선택
    dong_list = sorted(df_sigungu["동"].dropna().unique())
    selected_dong = st.selectbox("3. 읍·면·동 선택", dong_list)

# 최종 선택된 동네의 1개 행 추출
target_row = df_sigungu[df_sigungu["동"] == selected_dong].iloc[0]


# -----------------------------------------------------------------------------
# 4. 나이 및 남여 인구 데이터 정리
# -----------------------------------------------------------------------------
# 나이 라벨 생성 (0세, 1세, ... 99세, 100세 이상)
age_categories = [f"{i}세" for i in range(100)] + ["100세 이상"]

male_pop = []
female_pop = []

# 각 나이별 남/여 인구 열 이름에 맞춰 데이터 수집
for age in age_categories:
    male_col = f"남_{age}"
    female_col = f"여_{age}"

    # 컬럼이 존재할 경우 값 추출 (없으면 0 처리)
    m_val = target_row[male_col] if male_col in target_row else 0
    f_val = target_row[female_col] if female_col in target_row else 0

    male_pop.append(m_val)
    female_pop.append(f_val)


# -----------------------------------------------------------------------------
# 5. Plotly 가로 막대 그래프 (인구 피라미드) 생성
# -----------------------------------------------------------------------------
fig = go.Figure()

# (1) 남성 인구 막대 그래프 (왼쪽으로 뻗어나가도록 음수(-) 값 처리)
fig.add_trace(
    go.Bar(
        y=age_categories,  # Y축: 나이 라벨 (0세 ~ 100세 이상)
        x=[-val for val in male_pop],  # X축: 음수로 변환된 남성 인구수
        name="남성",
        orientation="h",  # 가로 막대 그래프 설정
        hoverinfo="y+text",
        text=[f"{val:,}명" for val in male_pop],  # 툴팁 및 표시용 텍스트 (양수)
        marker=dict(color="#4A90E2"),  # 따뜻한 파란색
    )
)

# (2) 여성 인구 막대 그래프 (오른쪽으로 뻗어나가는 양수(+) 값)
fig.add_trace(
    go.Bar(
        y=age_categories,  # Y축: 나이 라벨 (0세 ~ 100세 이상)
        x=female_pop,  # X축: 여성 인구수
        name="여성",
        orientation="h",
        hoverinfo="y+text",
        text=[f"{val:,}명" for val in female_pop],
        marker=dict(color="#FF6B6B"),  # 따뜻한 분홍색
    )
)


# -----------------------------------------------------------------------------
# 6. 축 세부 설정 및 레이아웃 조정
# -----------------------------------------------------------------------------
# X축 표시 눈금을 위해 최대 인구수 계산 (대칭 축 구성)
max_val = max(max(male_pop), max(female_pop)) if (male_pop and female_pop) else 100
# 여유 공간 확보를 위해 1.1배 조정
max_val = max_val * 1.1 if max_val > 0 else 100

fig.update_layout(
    title=f"<b>[{selected_sido} {selected_sigungu} {selected_dong}] 인구 피라미드</b>",
    title_font_size=20,
    barmode="relative",  # 음수/양수를 반대 방향으로 배치
    bargap=0.1,  # 막대 간격
    xaxis=dict(
        title="인구수 (명)",
        range=[-max_val, max_val],  # 좌우 대칭 축 설정
        # X축 눈금에 표시되는 음수 기호를 제거하고 천 단위 콤마 양수로만 표기
        tickvals=[-max_val / 2, 0, max_val / 2],
        ticktext=[
            f"{int(max_val/2):,}명",
            "0",
            f"{int(max_val/2):,}명",
        ],
    ),
    yaxis=dict(
        title="나이",
        # 나이 라벨의 순서를 원본 배열(0세 -> 100세 이상) 순서 그대로 축에 엄격히 고정
        type="category",
        categoryorder="array",
        categoryarray=age_categories,  # 맨 아래: 0세, 맨 위: 100세 이상
    ),
    height=800,  # 100개 이상의 나이 범주를 시원하게 볼 수 있는 높이
    legend=dict(x=0.85, y=1.05, orientation="h"),  # 범례 상단 배치
    template="plotly_white",
)

# 화면에 그래프 출력
st.plotly_chart(fig, use_container_width=True)

# 하단 안내 메세지
st.info(
    "📊 그래프의 막대에 마우스를 올리시면 해당 나이의 정확한 인구수를 확인하실 수 있습니다."
)
