"""
조선 Hull 실적 대시보드
- 프로젝트/선종/stage별 계량, 기준, 실행공수 시각화
- 세 테이블(Hull_erec_baseMH, Hull_info, R99_rate) 조인 기반
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

# ============================================================================
# 1. 페이지 설정
# ============================================================================
st.set_page_config(
    page_title="Hull 실적 대시보드",
    page_icon="⛵",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("⛵ Hull 실적 대시보드")
st.markdown("프로젝트 선종 STAGE 단위 공수 분석")

# ============================================================================
# 2. 데이터 로드 (캐시)
# ============================================================================
@st.cache_data
def load_data():
    """세 테이블 로드 및 초기 조인"""
    # 파일 경로 설정 (Streamlit 실행 위치에 따라 조정)
    base_path = Path(__file__).parent
    
    try:
        # 업로드된 CSV 파일 경로
        erec_path = base_path / "Hull_erec_baseMH.csv"
        info_path = base_path / "Hull_info.csv"
        r99_path = base_path / "R99_rate.csv"
        
        # 파일이 없으면 /mnt/user-data/uploads/ 에서 찾기
        if not erec_path.exists():
            erec_path = Path("/mnt/user-data/uploads/Hull_erec_baseMH.csv")
            info_path = Path("/mnt/user-data/uploads/Hull_info.csv")
            r99_path = Path("/mnt/user-data/uploads/R99_rate.csv")
        
        erec_df = pd.read_csv(erec_path, encoding='utf-8-sig')
        info_df = pd.read_csv(info_path, encoding='utf-8-sig')
        r99_df = pd.read_csv(r99_path, encoding='utf-8-sig')
        
        return erec_df, info_df, r99_df
    
    except FileNotFoundError as e:
        st.error(f"파일을 찾을 수 없습니다: {e}")
        return None, None, None

# ============================================================================
# 3. 데이터 전처리 및 조인
# ============================================================================
@st.cache_data
def prepare_dashboard_data(erec_df, info_df, r99_df):
    """
    세 테이블을 조인하고 실행공수 계산
    
    실행공수 = 기준공수 × (1 + R99율)
    """
    # erec_df와 info_df 조인 (프로젝트 → 선종 매핑)
    merged = erec_df.merge(
        info_df[['프로젝트', '선종']],
        on='프로젝트',
        how='left'
    )
    
    # R99_rate와 조인 (선종, stage → R99율)
    merged = merged.merge(
        r99_df[['선종', 'stage', 'R99율']],
        on=['선종', 'stage'],
        how='left'
    )
    
    # R99율이 없는 경우 0으로 채우기
    merged['R99율'].fillna(0.0, inplace=True)
    
    # 실행공수 계산: 기준공수 × (1 + R99율)
    merged['심출_실행'] = (merged['심출_기준'] * (1 + merged['R99율'])).round(2)
    merged['취부_실행'] = (merged['취부_기준'] * (1 + merged['R99율'])).round(2)
    merged['용접_실행'] = (merged['용접_기준'] * (1 + merged['R99율'])).round(2)
    merged['사상_실행'] = (merged['사상_기준'] * (1 + merged['R99율'])).round(2)
    merged['기타_실행'] = (merged['기타_기준'] * (1 + merged['R99율'])).round(2)
    merged['total_실행'] = (merged['total_기준'] * (1 + merged['R99율'])).round(2)
    
    return merged

# 데이터 로드
erec_df, info_df, r99_df = load_data()

if erec_df is None:
    st.error("데이터를 불러올 수 없습니다.")
    st.stop()

# 대시보드용 통합 데이터
df = prepare_dashboard_data(erec_df, info_df, r99_df)

# ============================================================================
# 4. 사이드바 필터 (새로운 레이아웃)
# ============================================================================

# 사이드바 글꼴 크기 및 줄간격, 색상 조정 (CSS)
st.markdown("""
<style>
    /* 기본 사이드바 스타일 */
    [data-testid="stSidebar"] {
        font-size: 9pt !important;
    }

    [data-testid="stSidebar"] * {
        font-size: 9pt !important;
        line-height: 1.2 !important;
    }

    [data-testid="stSidebar"] h3 {
        margin-top: 3px !important;
        margin-bottom: 2px !important;
        font-size: 9pt !important;
    }

    .project-info {
        font-size: 9pt !important;
        color: #808080 !important;
        line-height: 1.1 !important;
        margin: 1px 0px !important;
    }

    /* multiselect 입력 필드 배경색 (파스텔 하늘색) */
    [data-testid="stSidebar"] input[type="text"] {
        background-color: #E0F4FF !important;
        font-size: 9pt !important;
    }

    /* multiselect 컨테이너 */
    [data-testid="stSidebar"] .stMultiSelect {
        font-size: 9pt !important;
    }

    /* multiselect 태그 (선택된 항목) - 빨간색 제거 */
    [data-testid="stSidebar"] .stMultiSelect div span {
        color: #333333 !important;
        background-color: #E0F4FF !important;
        border: 1px solid #B0E0FF !important;
    }

    /* 드롭다운 옵션 글꼴 */
    [data-testid="stSidebar"] div[role="option"] {
        font-size: 9pt !important;
    }

    /* 라벨 */
    [data-testid="stSidebar"] label {
        font-size: 9pt !important;
    }

    /* 대시보드 메인 영역 글자 크기 축소 (2pt 축소: 9pt -> 7pt) */
    [data-testid="stMetric"] {
        font-size: 7pt !important;
    }

    [data-testid="stMetric"] label {
        font-size: 7pt !important;
    }

    /* 메인 콘텐츠 영역 글자 크기 */
    [data-testid="stMainBlockContainer"] h2 {
        font-size: 16pt !important;
    }

    [data-testid="stMainBlockContainer"] h3 {
        font-size: 14pt !important;
    }

    [data-testid="stMainBlockContainer"] {
        font-size: 7pt !important;
    }

    /* 테이블 글자 크기 */
    [data-testid="stDataFrame"] {
        font-size: 7pt !important;
    }

    /* 차트 글자 크기 */
    .plotly {
        font-size: 7pt !important;
    }

    /* 라디오 버튼 및 탭 글자 크기 */
    [data-testid="stRadio"] label {
        font-size: 7pt !important;
    }

    [role="tab"] {
        font-size: 7pt !important;
    }

    /* Multiselect 드롭다운 높이 제한 (4개 항목 정도만 보이도록) */
    [data-testid="stSidebar"] [role="listbox"] {
        max-height: 120px !important;
        overflow-y: auto !important;
    }

    /* Multiselect 옵션 높이 */
    [data-testid="stSidebar"] [role="option"] {
        padding: 2px 8px !important;
        min-height: 20px !important;
    }
</style>
""", unsafe_allow_html=True)

st.sidebar.header("🔍 필터")

# 모든 필터 옵션 정의
all_projects = sorted(df['프로젝트'].unique())
all_shiptype = sorted(df['선종'].dropna().unique())
all_stages = sorted(df['stage'].unique())

# Hull_info 로드 (프로젝트 정보 표시)
try:
    base_path = Path(__file__).parent
    info_df_lookup = pd.read_csv(base_path / "Hull_info.csv", encoding='utf-8-sig')
except:
    info_df_lookup = None

# 헬퍼 함수: 프로젝트 정보 표시 (새 형식)
def get_project_info_text(project):
    if info_df_lookup is None:
        return ""
    row = info_df_lookup[info_df_lookup['프로젝트'] == project]
    if not row.empty:
        shiptype = row.iloc[0]['선종'] if pd.notna(row.iloc[0]['선종']) else ''
        shiptype_info = row.iloc[0]['선형'] if pd.notna(row.iloc[0]['선형']) else ''
        shipowner = row.iloc[0]['선주'] if pd.notna(row.iloc[0]['선주']) else ''
        series = row.iloc[0]['시리즈'] if pd.notna(row.iloc[0]['시리즈']) else ''
        info_list = [str(x) for x in [shiptype, shiptype_info, shipowner, series] if x]
        return '[' + '/'.join(info_list) + ']' if info_list else ''
    return ""

# Session state 초기화 (empty로 시작)
if 'projects_filter' not in st.session_state:
    st.session_state.projects_filter = []
if 'shiptype_filter' not in st.session_state:
    st.session_state.shiptype_filter = []
if 'moblock_filter' not in st.session_state:
    st.session_state.moblock_filter = []
if 'block_filter' not in st.session_state:
    st.session_state.block_filter = []
if 'stages_filter' not in st.session_state:
    st.session_state.stages_filter = []

# 필터 초기화 콜백 함수
def reset_filters():
    st.session_state.projects_filter = []
    st.session_state.shiptype_filter = []
    st.session_state.moblock_filter = []
    st.session_state.block_filter = []
    st.session_state.stages_filter = []

# ─ 프로젝트와 선종을 2열로 구성 (양방향 연동)
st.sidebar.markdown("### 📍 프로젝트 / 🚢 선종")

# 시작: 선택 가능한 모든 옵션
current_projects = all_projects
current_shiptypes = all_shiptype

col1, col2 = st.sidebar.columns(2)

with col1:
    # 프로젝트 선택 (선종으로 필터링된 프로젝트만 표시)
    # Session state의 shiptype_filter를 기반으로 필터링
    if st.session_state.shiptype_filter:
        projects_from_shiptype = set(df[df['선종'].isin(st.session_state.shiptype_filter)]['프로젝트'].unique())
    else:
        projects_from_shiptype = set(all_projects)

    # 현재 선택된 프로젝트는 항상 options에 포함
    projects_selected = set(st.session_state.projects_filter) if st.session_state.projects_filter else set()
    current_projects = sorted(projects_from_shiptype | projects_selected)

    selected_projects = st.multiselect(
        "프로젝트",
        options=current_projects,
        key='projects_filter'
    )

with col2:
    # 선종 선택 (프로젝트로 필터링된 선종만 표시)
    # Session state의 projects_filter를 기반으로 필터링
    if st.session_state.projects_filter:
        shiptypes_from_projects = set(df[df['프로젝트'].isin(st.session_state.projects_filter)]['선종'].dropna().unique())
    else:
        shiptypes_from_projects = set(all_shiptype)

    # 현재 선택된 선종은 항상 options에 포함
    shiptypes_selected = set(st.session_state.shiptype_filter) if st.session_state.shiptype_filter else set()
    current_shiptypes = sorted(shiptypes_from_projects | shiptypes_selected)

    selected_shiptype = st.multiselect(
        "선종",
        options=current_shiptypes,
        key='shiptype_filter'
    )

# 프로젝트 정보 표시 (필터 바로 하부)
if selected_projects:
    for proj in selected_projects:
        info_text = get_project_info_text(proj)
        if info_text:
            st.sidebar.markdown(f"<div class='project-info'>{proj} {info_text}</div>", unsafe_allow_html=True)

# ─ 모블록번호 필터 (프로젝트 연동)
st.sidebar.markdown("### 🔲 모블록번호")
available_moblocks = sorted(df[df['프로젝트'].isin(selected_projects)]['모블록번호'].dropna().unique()) if selected_projects else []
selected_moblocks = st.sidebar.multiselect(
    "모블록번호 선택",
    options=available_moblocks,
    key='moblock_filter'
)

# ─ 블록번호 필터 (모블록 연동)
st.sidebar.markdown("### 🔳 블록번호")
filter_condition_block = df['프로젝트'].isin(selected_projects)
if selected_moblocks:
    filter_condition_block = filter_condition_block & df['모블록번호'].isin(selected_moblocks)
available_blocks = sorted(df[filter_condition_block]['블록번호'].dropna().unique())
selected_blocks = st.sidebar.multiselect(
    "블록번호 선택",
    options=available_blocks,
    key='block_filter'
)

# ─ Stage 필터 (블록 연동)
st.sidebar.markdown("### 📊 Stage")
filter_condition_stage = df['프로젝트'].isin(selected_projects)
if selected_blocks:
    filter_condition_stage = filter_condition_stage & df['블록번호'].isin(selected_blocks)
available_stages = sorted(df[filter_condition_stage]['stage'].unique())
selected_stages = st.sidebar.multiselect(
    "Stage 선택",
    options=available_stages,
    key='stages_filter'
)

# 필터 초기화 버튼 (on_click 콜백 사용)
st.sidebar.markdown("---")
st.sidebar.button(
    "🔄 필터 초기화",
    use_container_width=True,
    on_click=reset_filters
)

# 필터 적용 (선택된 필터만 적용, 미선택 필터는 모든 값 허용)
filtered_df = df.copy()

# 프로젝트 필터 (선택된 경우만 적용)
if selected_projects:
    filtered_df = filtered_df[filtered_df['프로젝트'].isin(selected_projects)]

# 선종 필터 (선택된 경우만 적용)
if selected_shiptype:
    filtered_df = filtered_df[filtered_df['선종'].isin(selected_shiptype)]

# Stage 필터 (선택된 경우만 적용)
if selected_stages:
    filtered_df = filtered_df[filtered_df['stage'].isin(selected_stages)]

# 모블록 필터 (선택된 경우만 적용)
if selected_moblocks:
    filtered_df = filtered_df[filtered_df['모블록번호'].isin(selected_moblocks)]

# 블록 필터 (선택된 경우만 적용)
if selected_blocks:
    filtered_df = filtered_df[filtered_df['블록번호'].isin(selected_blocks)]

# 필터 결과 요약
st.sidebar.markdown("---")
st.sidebar.metric("필터된 행 수", len(filtered_df))
st.sidebar.metric("프로젝트 수", filtered_df['프로젝트'].nunique())
st.sidebar.metric("선종 수", filtered_df['선종'].nunique())

# ─ DEBUG: 필터 값 확인 (사이드바 제일 하단)
st.sidebar.markdown("---")
with st.sidebar.expander("🔧 디버그 정보"):
    st.write(f"selected_projects: {selected_projects}")
    st.write(f"selected_shiptype: {selected_shiptype}")
    st.write(f"session projects_filter: {st.session_state.projects_filter}")
    st.write(f"session shiptype_filter: {st.session_state.shiptype_filter}")

# ============================================================================
# 5. 상단 KPI 지표
# ============================================================================
st.markdown("## 📊 주요 지표")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    total_qty = filtered_df['total_계량'].sum()
    st.metric("계량 총합", f"{total_qty:,.0f}")

with col2:
    total_std = filtered_df['total_기준'].sum()
    st.metric("기준 총합", f"{total_std:,.0f}")

with col3:
    total_exec = filtered_df['total_실행'].sum()
    st.metric("실행공수 총합", f"{total_exec:,.0f}")

with col4:
    # 기준 대비 실행공수 비율
    if total_std > 0:
        ratio = (total_exec / total_std - 1) * 100
        st.metric("기준 대비 증가율", f"{ratio:.1f}%")
    else:
        st.metric("기준 대비 증가율", "N/A")

with col5:
    # 평균 R99율
    avg_r99 = filtered_df['R99율'].mean() * 100
    st.metric("평균 R99율", f"{avg_r99:.1f}%")

# ============================================================================
# 6. 탭별 분석
# ============================================================================

# 필터 모드 선택 (기본 vs 비교)
tab_mode = st.radio(
    "분석 모드 선택",
    options=["📊 기본 필터", "🔄 프로젝트 비교"],
    horizontal=True
)

if tab_mode == "📊 기본 필터":
    tab1, tab2, tab3, tab4 = st.tabs(["📈 프로젝트별", "🚢 선종별", "📍 Stage별", "📋 상세 데이터"])
else:
    st.markdown("## 🔄 프로젝트 비교 분석")

# ─────────────────────────────────────────────────────────────────────────
# TAB 1: 프로젝트별 분석
# ─────────────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("프로젝트별 공수 비교")

    # 필터 선택 내용 표시
    filter_info = []
    if selected_projects:
        filter_info.append(f"프로젝트: {', '.join(selected_projects)}")
    if selected_shiptype:
        filter_info.append(f"선종: {', '.join(selected_shiptype)}")
    if selected_stages:
        filter_info.append(f"Stage: {', '.join(map(str, selected_stages))}")
    if selected_moblocks:
        filter_info.append(f"모블록: {', '.join(map(str, selected_moblocks))}")
    if selected_blocks:
        filter_info.append(f"블록: {', '.join(map(str, selected_blocks))}")

    if filter_info:
        st.markdown(f"<div style='font-size:8pt; color:#888;'>필터: {' | '.join(filter_info)}</div>", unsafe_allow_html=True)

    # 프로젝트별 집계
    project_summary = filtered_df.groupby('프로젝트').agg({
        'total_계량': 'sum',
        'total_기준': 'sum',
        'total_실행': 'sum'
    }).reset_index()

    project_summary = project_summary.sort_values('total_실행', ascending=False)

    # 테이블 데이터 포맷팅 (천단위 구분기호 + 정수)
    project_summary_display = project_summary.copy()
    project_summary_display['계량'] = project_summary_display['total_계량'].round(0).astype(int).apply(lambda x: f"{x:,}")
    project_summary_display['기준'] = project_summary_display['total_기준'].round(0).astype(int).apply(lambda x: f"{x:,}")
    project_summary_display['실행공수'] = project_summary_display['total_실행'].round(0).astype(int).apply(lambda x: f"{x:,}")
    project_summary_display = project_summary_display[['프로젝트', '계량', '기준', '실행공수']]

    col1, col2 = st.columns([2, 1])

    with col1:
        # 그룹 바 차트
        fig = go.Figure(data=[
            go.Bar(name='계량', x=project_summary['프로젝트'], y=project_summary['total_계량']),
            go.Bar(name='기준', x=project_summary['프로젝트'], y=project_summary['total_기준']),
            go.Bar(name='실행공수', x=project_summary['프로젝트'], y=project_summary['total_실행'])
        ])
        fig.update_layout(
            barmode='group',
            title="프로젝트별 공수 분포",
            xaxis_title="프로젝트",
            yaxis_title="공수",
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.dataframe(
            project_summary_display,
            use_container_width=True,
            hide_index=True
        )

# ─────────────────────────────────────────────────────────────────────────
# TAB 2: 선종별 분석
# ─────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("선종별 공수 비교")

    # 필터 선택 내용 표시
    filter_info = []
    if selected_projects:
        filter_info.append(f"프로젝트: {', '.join(selected_projects)}")
    if selected_shiptype:
        filter_info.append(f"선종: {', '.join(selected_shiptype)}")
    if selected_stages:
        filter_info.append(f"Stage: {', '.join(map(str, selected_stages))}")
    if selected_moblocks:
        filter_info.append(f"모블록: {', '.join(map(str, selected_moblocks))}")
    if selected_blocks:
        filter_info.append(f"블록: {', '.join(map(str, selected_blocks))}")

    if filter_info:
        st.markdown(f"<div style='font-size:8pt; color:#888;'>필터: {' | '.join(filter_info)}</div>", unsafe_allow_html=True)

    # 선종별 집계
    shiptype_summary = filtered_df.groupby('선종').agg({
        'total_계량': 'sum',
        'total_기준': 'sum',
        'total_실행': 'sum',
        'R99율': 'mean'  # 평균 R99율
    }).reset_index()

    shiptype_summary['R99율_%'] = (shiptype_summary['R99율'] * 100).round(1)
    shiptype_summary = shiptype_summary.sort_values('total_실행', ascending=False)

    # 테이블 데이터 포맷팅 (천단위 구분기호 + 정수)
    shiptype_summary_display = shiptype_summary.copy()
    shiptype_summary_display['계량'] = shiptype_summary_display['total_계량'].round(0).astype(int).apply(lambda x: f"{x:,}")
    shiptype_summary_display['기준'] = shiptype_summary_display['total_기준'].round(0).astype(int).apply(lambda x: f"{x:,}")
    shiptype_summary_display['실행공수'] = shiptype_summary_display['total_실행'].round(0).astype(int).apply(lambda x: f"{x:,}")
    shiptype_summary_display = shiptype_summary_display[['선종', '계량', '기준', '실행공수', 'R99율_%']]
    shiptype_summary_display = shiptype_summary_display.rename(columns={'R99율_%': 'R99율(%)'})

    col1, col2 = st.columns([2, 1])

    with col1:
        # Pie 차트
        fig = go.Figure(data=[go.Pie(
            labels=shiptype_summary['선종'],
            values=shiptype_summary['total_실행'],
            hole=0.3
        )])
        fig.update_layout(
            title="선종별 실행공수 비율",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.dataframe(
            shiptype_summary_display,
            use_container_width=True,
            hide_index=True
        )

# ─────────────────────────────────────────────────────────────────────────
# TAB 3: Stage별 분석
# ─────────────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Stage별 공수 분포 (공정 단계별)")

    # 필터 선택 내용 표시
    filter_info = []
    if selected_projects:
        filter_info.append(f"프로젝트: {', '.join(selected_projects)}")
    if selected_shiptype:
        filter_info.append(f"선종: {', '.join(selected_shiptype)}")
    if selected_stages:
        filter_info.append(f"Stage: {', '.join(map(str, selected_stages))}")
    if selected_moblocks:
        filter_info.append(f"모블록: {', '.join(map(str, selected_moblocks))}")
    if selected_blocks:
        filter_info.append(f"블록: {', '.join(map(str, selected_blocks))}")

    if filter_info:
        st.markdown(f"<div style='font-size:8pt; color:#888;'>필터: {' | '.join(filter_info)}</div>", unsafe_allow_html=True)

    # Stage별 집계
    stage_summary = filtered_df.groupby('stage').agg({
        'total_계량': 'sum',
        'total_기준': 'sum',
        'total_실행': 'sum'
    }).reset_index()

    stage_summary = stage_summary.sort_values('stage')

    # 테이블 데이터 포맷팅 (천단위 구분기호 + 정수)
    stage_summary_display = stage_summary.copy()
    stage_summary_display['계량'] = stage_summary_display['total_계량'].round(0).astype(int).apply(lambda x: f"{x:,}")
    stage_summary_display['기준'] = stage_summary_display['total_기준'].round(0).astype(int).apply(lambda x: f"{x:,}")
    stage_summary_display['실행공수'] = stage_summary_display['total_실행'].round(0).astype(int).apply(lambda x: f"{x:,}")
    stage_summary_display = stage_summary_display[['stage', '계량', '기준', '실행공수']]
    stage_summary_display = stage_summary_display.rename(columns={'stage': 'Stage'})

    # 라인 차트
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=stage_summary['stage'], y=stage_summary['total_계량'],
        mode='lines+markers', name='계량', line=dict(dash='dash')
    ))
    fig.add_trace(go.Scatter(
        x=stage_summary['stage'], y=stage_summary['total_기준'],
        mode='lines+markers', name='기준'
    ))
    fig.add_trace(go.Scatter(
        x=stage_summary['stage'], y=stage_summary['total_실행'],
        mode='lines+markers', name='실행공수', line=dict(width=3)
    ))

    fig.update_layout(
        title="Stage별 공수 추이",
        xaxis_title="Stage",
        yaxis_title="공수",
        height=400,
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        stage_summary_display,
        use_container_width=True,
        hide_index=True
    )

# ─────────────────────────────────────────────────────────────────────────
# TAB 4: 상세 데이터
# ─────────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("필터된 상세 데이터")

    # 필터 선택 내용 표시
    filter_info = []
    if selected_projects:
        filter_info.append(f"프로젝트: {', '.join(selected_projects)}")
    if selected_shiptype:
        filter_info.append(f"선종: {', '.join(selected_shiptype)}")
    if selected_stages:
        filter_info.append(f"Stage: {', '.join(map(str, selected_stages))}")
    if selected_moblocks:
        filter_info.append(f"모블록: {', '.join(map(str, selected_moblocks))}")
    if selected_blocks:
        filter_info.append(f"블록: {', '.join(map(str, selected_blocks))}")

    if filter_info:
        st.markdown(f"<div style='font-size:8pt; color:#888;'>필터: {' | '.join(filter_info)}</div>", unsafe_allow_html=True)

    # 표시할 컬럼 선택
    display_cols = [
        '프로젝트', '모블록번호', '블록번호', 'stage', '선종',
        '모듈',
        'total_계량', 'total_기준', 'total_실행',
        'R99율'
    ]

    # 상세 데이터 포맷팅
    detail_display = filtered_df[display_cols].copy()
    detail_display['계량'] = detail_display['total_계량'].round(0).astype(int).apply(lambda x: f"{x:,}")
    detail_display['기준'] = detail_display['total_기준'].round(0).astype(int).apply(lambda x: f"{x:,}")
    detail_display['실행공수'] = detail_display['total_실행'].round(0).astype(int).apply(lambda x: f"{x:,}")
    detail_display['R99율(%)'] = (detail_display['R99율'] * 100).round(1)
    detail_display = detail_display[['프로젝트', '모블록번호', '블록번호', 'stage', '선종', '모듈', '계량', '기준', '실행공수', 'R99율(%)']]
    detail_display = detail_display.rename(columns={'stage': 'Stage'})

    # 상세 데이터 테이블
    st.dataframe(
        detail_display,
        use_container_width=True,
        hide_index=True,
        height=600
    )

    # 다운로드 버튼
    csv = filtered_df[display_cols].to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="💾 필터된 데이터 CSV 다운로드",
        data=csv,
        file_name="hull_dashboard_export.csv",
        mime="text/csv"
    )

# ============================================================================
# 7. 추가 분석: 공정별 공수 분포
# ============================================================================
st.markdown("---")
st.markdown("## 🔧 공정별 공수 분석")

col1, col2 = st.columns(2)

with col1:
    st.subheader("공정별 계량 분포")
    
    process_qty = pd.DataFrame({
        '심출': [filtered_df['심출_계량'].sum()],
        '취부': [filtered_df['취부_계량'].sum()],
        '용접': [filtered_df['용접_계량'].sum()],
        '사상': [filtered_df['사상_계량'].sum()],
        '기타': [filtered_df['기타_계량'].sum()]
    }).T.rename(columns={0: '계량'})
    
    fig = go.Figure(data=[go.Bar(
        y=process_qty.index,
        x=process_qty['계량'],
        orientation='h',
        marker=dict(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'])
    )])
    fig.update_layout(
        title="공정별 계량 합계",
        xaxis_title="계량",
        height=350,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("공정별 실행공수 분포")
    
    process_exec = pd.DataFrame({
        '심출': [filtered_df['심출_실행'].sum()],
        '취부': [filtered_df['취부_실행'].sum()],
        '용접': [filtered_df['용접_실행'].sum()],
        '사상': [filtered_df['사상_실행'].sum()],
        '기타': [filtered_df['기타_실행'].sum()]
    }).T.rename(columns={0: '실행공수'})
    
    fig = go.Figure(data=[go.Bar(
        y=process_exec.index,
        x=process_exec['실행공수'],
        orientation='h',
        marker=dict(color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'])
    )])
    fig.update_layout(
        title="공정별 실행공수 합계",
        xaxis_title="실행공수",
        height=350,
        showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# 8. 데이터 정보
# ============================================================================
st.markdown("---")
with st.expander("ℹ️ 데이터 정보 및 계산 방식"):
    st.markdown("""
    ### 테이블 구조
    - **Hull_erec_baseMH**: 블록/모듈 단위 작업 실적 (4,402행)
    - **Hull_info**: 호선(프로젝트) 마스터 정보 (10개 프로젝트)
    - **R99_rate**: 선종/stage별 R99율 (실행공수 산출 factor)
    
    ### 계산 방식
    - **기준공수**: 계량공수 × 선종별 factor (LNG 0.8, CONT 0.7, SHTL 0.85, LPG 0.85)
    - **실행공수**: 기준공수 × (1 + R99율)
      - R99율은 선종과 stage 조합별로 지정된 값
      - 예: LNG stage 40 → R99율 0.221 → 기준공수 × 1.221
    
    ### 공정 분류
    - 심출: 11%, 취부: 22%, 용접: 54%, 사상: 10%, 기타: 3%
    
    ### Stage 정의
    - **30, 40**: 자블록(Sub-block) 단계
    - **50, 60, 70**: 모블록(Module Block) 단계
    """)

# ============================================================================
# 8. 프로젝트 비교 섹션 (MODE B)
# ============================================================================
if tab_mode == "🔄 프로젝트 비교":
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 프로젝트 A")
        project_a = st.selectbox(
            "프로젝트 선택",
            options=all_projects,
            key='compare_project_a'
        )
        if project_a:
            info_a = get_project_info_text(project_a)
            st.markdown(f"<div class='project-info'>{project_a} {info_a}</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("### 프로젝트 B")
        project_b = st.selectbox(
            "프로젝트 선택",
            options=all_projects,
            key='compare_project_b'
        )
        if project_b:
            info_b = get_project_info_text(project_b)
            st.markdown(f"<div class='project-info'>{project_b} {info_b}</div>", unsafe_allow_html=True)

    st.markdown("---")

    # 공통 블록/Stage 찾기
    if project_a and project_b and project_a != project_b:
        df_a = df[df['프로젝트'] == project_a]
        df_b = df[df['프로젝트'] == project_b]

        common_blocks = set(df_a['블록번호'].unique()) & set(df_b['블록번호'].unique())
        common_stages = set(df_a['stage'].unique()) & set(df_b['stage'].unique())

        if common_blocks and common_stages:
            st.success(f"✅ 공통 블록: {sorted(common_blocks)}")
            st.success(f"✅ 공통 Stage: {sorted(common_stages)}")

            # 공통 블록과 Stage 모두 가진 데이터만 필터링
            comparison_data = df[
                ((df['프로젝트'] == project_a) | (df['프로젝트'] == project_b)) &
                (df['블록번호'].isin(common_blocks)) &
                (df['stage'].isin(common_stages))
            ].copy()

            # 블록별, Stage별로 비교 데이터 표시
            for block in sorted(common_blocks):
                block_data = comparison_data[comparison_data['블록번호'] == block]
                st.markdown(f"### 📍 블록 {block}")

                for stage in sorted(block_data['stage'].unique()):
                    stage_data = block_data[block_data['stage'] == stage]
                    st.markdown(f"**Stage {stage}**")

                    # 프로젝트별 데이터 비교
                    comparison_table = []
                    for _, row in stage_data.iterrows():
                        comparison_table.append({
                            '프로젝트': row['프로젝트'],
                            '계량': f"{row['total_계량']:,.0f}",
                            '기준': f"{row['total_기준']:,.0f}",
                            '실행공수': f"{row['total_실행']:,.0f}",
                            '심출': f"{row['심출_계량']:.0f}/{row['심출_기준']:.0f}/{row['심출_실행']:.0f}",
                            '취부': f"{row['취부_계량']:.0f}/{row['취부_기준']:.0f}/{row['취부_실행']:.0f}",
                            '용접': f"{row['용접_계량']:.0f}/{row['용접_기준']:.0f}/{row['용접_실행']:.0f}",
                            '사상': f"{row['사상_계량']:.0f}/{row['사상_기준']:.0f}/{row['사상_실행']:.0f}",
                        })

                    if comparison_table:
                        comparison_df = pd.DataFrame(comparison_table)
                        st.dataframe(comparison_df, use_container_width=True, hide_index=True)

                    st.markdown("---")
        else:
            st.warning("⚠️ 공통 블록/Stage가 없습니다.")
    elif project_a == project_b:
        st.warning("⚠️ 다른 프로젝트를 선택해주세요.")
    else:
        st.info("ℹ️ 프로젝트 A, B를 모두 선택해주세요.")

st.markdown("---")
st.markdown("**생성일**: 2024년 | **데이터**: 더미데이터 (seed=42)")
