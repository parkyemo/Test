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
from datetime import datetime

# ============================================================================
# 1. 페이지 설정
# ============================================================================
st.set_page_config(
    page_title="조선계량 조회 및 분석",
    page_icon="⛵",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.header("■ 조선계량 조회 및 분석")
st.markdown("<div style='font-size:12pt; color:#666;'>프로젝트/선종/STAGE별 공수, 원단위 정보 조회 및 분석</div>", unsafe_allow_html=True)

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
        margin-top: 0px !important;
        margin-bottom: 0px !important;
        font-size: 9pt !important;
    }

    /* 사이드바 내 블록(제목-위젯 등) 간 세로 간격 최소화 */
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0.15rem !important;
    }

    [data-testid="stSidebar"] .element-container {
        margin-bottom: 0px !important;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
        margin-bottom: 0px !important;
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

    /* ─ 기본 필터 모드 탭(프로젝트별/선종별/STAGE별/상세데이터) 색상 및
       탭 클릭 시 아래 콘텐츠 테두리 색상 연동 (탭 순서와 패널 순서가 1:1로 대응) */
    [data-testid="stTabs"] [data-testid="stTab"]:nth-child(1) {
        background-color: rgb(0, 176, 240) !important;
        color: #ffffff !important;
    }
    [data-testid="stTabs"] [data-testid="stTab"]:nth-child(2) {
        background-color: rgb(146, 208, 80) !important;
        color: #ffffff !important;
    }
    [data-testid="stTabs"] [data-testid="stTab"]:nth-child(3) {
        background-color: rgb(255, 192, 0) !important;
        color: #000000 !important;
    }
    [data-testid="stTabs"] [data-testid="stTab"]:nth-child(4) {
        background-color: rgb(217, 217, 217) !important;
        color: #000000 !important;
    }
    [data-testid="stTabs"] [data-testid="stTab"] p {
        color: inherit !important;
    }
    /* 탭 글자 양옆으로 한글자 정도의 여백 추가 */
    [data-testid="stTabs"] [data-testid="stTab"] {
        padding-left: 1em !important;
        padding-right: 1em !important;
    }

    /* stTabPanel의 형제로 tablist(DIV)가 앞에 있어 nth-of-type 카운트가 1칸 밀림 */
    [data-testid="stTabPanel"]:nth-of-type(2) {
        border: 3px solid rgb(0, 176, 240) !important;
        padding: 12px;
    }
    [data-testid="stTabPanel"]:nth-of-type(3) {
        border: 3px solid rgb(146, 208, 80) !important;
        padding: 12px;
    }
    [data-testid="stTabPanel"]:nth-of-type(4) {
        border: 3px solid rgb(255, 192, 0) !important;
        padding: 12px;
    }
    [data-testid="stTabPanel"]:nth-of-type(5) {
        border: 3px solid rgb(217, 217, 217) !important;
        padding: 12px;
    }
</style>
""", unsafe_allow_html=True)

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

# Widget 캐시 무효화용 카운터
if '_reset_counter' not in st.session_state:
    st.session_state._reset_counter = 0

# 필터 초기화 콜백 함수 (카운터 증가 → 모든 위젯 key가 바뀌며 완전히 새로 렌더링됨)
def reset_filters():
    st.session_state._reset_counter += 1

_rc = st.session_state._reset_counter
KEY_PROJECT = f'projects_select_{_rc}'
KEY_SHIPTYPE = f'shiptype_select_{_rc}'
KEY_MOBLOCK = f'moblock_select_{_rc}'
KEY_BLOCK = f'block_select_{_rc}'
KEY_STAGE = f'stage_select_{_rc}'

# ─ 5개 필터(프로젝트/선종/모블록번호/블록번호/Stage) 완전 상호연동
# Streamlit은 위젯 상호작용 시 session_state[key]를 스크립트 재실행 전에 이미 갱신하므로,
# 아래에서 읽는 값은 "이번 rerun에서 사용자가 방금 변경한 위젯"까지 포함한 최신 상태다.
# → 어떤 필터를 먼저 선택하든 나머지 4개 필터가 그 조건을 즉시 반영한다.
cur_projects = st.session_state.get(KEY_PROJECT, [])
cur_shiptypes = st.session_state.get(KEY_SHIPTYPE, [])
cur_moblocks = st.session_state.get(KEY_MOBLOCK, [])
cur_blocks = st.session_state.get(KEY_BLOCK, [])
cur_stages = st.session_state.get(KEY_STAGE, [])

def _mask_excluding(exclude):
    """exclude로 지정한 필터를 제외한 나머지 필터 조건으로 df를 필터링하는 mask 반환"""
    mask = pd.Series(True, index=df.index)
    if exclude != 'project' and cur_projects:
        mask &= df['프로젝트'].isin(cur_projects)
    if exclude != 'shiptype' and cur_shiptypes:
        mask &= df['선종'].isin(cur_shiptypes)
    if exclude != 'moblock' and cur_moblocks:
        mask &= df['모블록번호'].isin(cur_moblocks)
    if exclude != 'block' and cur_blocks:
        mask &= df['블록번호'].isin(cur_blocks)
    if exclude != 'stage' and cur_stages:
        mask &= df['stage'].isin(cur_stages)
    return mask

# 각 필터의 선택 가능 옵션 = (자신을 제외한 나머지 4개 필터로 걸러진 데이터의 고유값) ∪ (현재 선택값)
available_projects = sorted(set(df[_mask_excluding('project')]['프로젝트'].unique()) | set(cur_projects))
available_shiptypes = sorted(set(df[_mask_excluding('shiptype')]['선종'].dropna().unique()) | set(cur_shiptypes))
available_moblocks = sorted(set(df[_mask_excluding('moblock')]['모블록번호'].dropna().unique()) | set(cur_moblocks))
available_blocks = sorted(set(df[_mask_excluding('block')]['블록번호'].dropna().unique()) | set(cur_blocks))
available_stages = sorted(set(df[_mask_excluding('stage')]['stage'].unique()) | set(cur_stages))

# ─ 프로젝트 / 선종 (2열)
st.sidebar.markdown("### ■ 프로젝트 / 선종")
col_left, col_right = st.sidebar.columns(2)

with col_left:
    selected_projects = st.multiselect(
        "프로젝트",
        options=available_projects,
        default=cur_projects,
        key=KEY_PROJECT
    )

with col_right:
    selected_shiptype = st.multiselect(
        "선종",
        options=available_shiptypes,
        default=cur_shiptypes,
        key=KEY_SHIPTYPE
    )

projects_filter = selected_projects
shiptype_filter = selected_shiptype

# 프로젝트 정보 표시 (필터 바로 하부)
if projects_filter:
    for proj in projects_filter:
        info_text = get_project_info_text(proj)
        if info_text:
            st.sidebar.markdown(f"<div class='project-info'>{proj} {info_text}</div>", unsafe_allow_html=True)

# ─ 모블록번호
st.sidebar.markdown("### ■ 모블록번호")
selected_moblocks = st.sidebar.multiselect(
    "모블록번호 선택",
    options=available_moblocks,
    default=cur_moblocks,
    key=KEY_MOBLOCK
)

# ─ 블록번호
st.sidebar.markdown("### ■ 블록번호")
selected_blocks = st.sidebar.multiselect(
    "블록번호 선택",
    options=available_blocks,
    default=cur_blocks,
    key=KEY_BLOCK
)

# ─ Stage
st.sidebar.markdown("### ■ Stage")
selected_stages = st.sidebar.multiselect(
    "Stage 선택",
    options=available_stages,
    default=cur_stages,
    key=KEY_STAGE
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
if projects_filter:
    filtered_df = filtered_df[filtered_df['프로젝트'].isin(projects_filter)]

# 선종 필터 (선택된 경우만 적용)
if shiptype_filter:
    filtered_df = filtered_df[filtered_df['선종'].isin(shiptype_filter)]

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
st.sidebar.markdown("### ■ 필터된 항목")
summary_rows = [
    ('필터된 행수', len(filtered_df)),
    ('프로젝트수', filtered_df['프로젝트'].nunique()),
    ('블록수', filtered_df['블록번호'].nunique()),
    ('선종수', filtered_df['선종'].nunique()),
]
summary_html = "<table style='width:100%; font-size:9pt; color:#808080; border-collapse:collapse;'>"
for label, value in summary_rows:
    summary_html += f"<tr><td style='padding:1px 0;'>{label}</td><td style='padding:1px 0; text-align:right;'>{value:,}</td></tr>"
summary_html += "</table>"
st.sidebar.markdown(summary_html, unsafe_allow_html=True)

# ─ 배포 정보 (사이드바 제일 하단)
st.sidebar.markdown("---")
st.sidebar.markdown(
    "<div style='font-size:9pt; color:#808080;'>"
    "배포날짜 : 2026-07-19<br>"
    "문의사항 : 기획운영그룹장에게 문의바랍니다."
    "</div>",
    unsafe_allow_html=True
)

# ============================================================================
# 5. 상단 KPI 지표
# ============================================================================
st.markdown("## ■ 주요 지표")

# ─ 원단위 계산 헬퍼 (공수 ÷ 용접장_total)
def calc_wondanwi(numerator_sum, denom_sum):
    """원단위 = 분자합 ÷ 용접장합. 용접장합이 0이면 0으로 처리 (0으로 나눌 수 없음)"""
    if denom_sum == 0:
        return 0.0
    return round(numerator_sum / denom_sum, 4)

total_qty = filtered_df['total_계량'].sum()
total_std = filtered_df['total_기준'].sum()
total_exec = filtered_df['total_실행'].sum()
weld_len_sum = filtered_df['용접장_total'].sum()
qty_wondanwi = calc_wondanwi(total_qty, weld_len_sum)
std_wondanwi = calc_wondanwi(total_std, weld_len_sum)
exec_wondanwi = calc_wondanwi(total_exec, weld_len_sum)

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("계량공수합", f"{total_qty:,.0f}")
with col2:
    st.metric("기준공수합", f"{total_std:,.0f}")
with col3:
    st.metric("실행공수합", f"{total_exec:,.0f}")
with col4:
    st.metric("계량원단위", f"{qty_wondanwi:.4f}")
with col5:
    st.metric("기준원단위", f"{std_wondanwi:.4f}")
with col6:
    st.metric("실행원단위", f"{exec_wondanwi:.4f}")

# ============================================================================
# 6. 탭별 분석 & 프로젝트 비교
# ============================================================================

# 필터 모드 선택 (기본 vs 비교)
tab_mode = st.radio(
    "분석 모드 선택",
    options=["기본 필터", "프로젝트 비교"],
    horizontal=True
)

# ─────────────────────────────────────────────────────────────────────────
# 기본 필터 모드: 4개 탭 분석
# ─────────────────────────────────────────────────────────────────────────
if tab_mode == "기본 필터":
    tab1, tab2, tab3, tab4 = st.tabs(["■ 프로젝트별", "■ 선종별", "■ STAGE별", "■ 상세 데이터"])

    # TAB 1: 프로젝트별 원단위 비교
    with tab1:
        st.subheader("프로젝트별 원단위 비교")

        # 필터 선택 내용 표시
        filter_info = []
        if projects_filter:
            filter_info.append(f"프로젝트: {', '.join(projects_filter)}")
        if shiptype_filter:
            filter_info.append(f"선종: {', '.join(shiptype_filter)}")
        if selected_stages:
            filter_info.append(f"Stage: {', '.join(map(str, selected_stages))}")
        if selected_moblocks:
            filter_info.append(f"모블록: {', '.join(map(str, selected_moblocks))}")
        if selected_blocks:
            filter_info.append(f"블록: {', '.join(map(str, selected_blocks))}")

        if filter_info:
            st.markdown(f"<div style='font-size:8pt; color:#888;'>필터: {' | '.join(filter_info)}</div>", unsafe_allow_html=True)

        # 프로젝트별 집계 (원단위 = 프로젝트별 SUM(값) ÷ SUM(용접장_total))
        project_summary = filtered_df.groupby('프로젝트').agg(
            용접장합=('용접장_total', 'sum'),
            total_계량=('total_계량', 'sum'),
            total_기준=('total_기준', 'sum'),
            total_실행=('total_실행', 'sum'),
        ).reset_index()

        project_summary['계량원단위'] = project_summary.apply(lambda r: calc_wondanwi(r['total_계량'], r['용접장합']), axis=1)
        project_summary['기준원단위'] = project_summary.apply(lambda r: calc_wondanwi(r['total_기준'], r['용접장합']), axis=1)
        project_summary['실행원단위'] = project_summary.apply(lambda r: calc_wondanwi(r['total_실행'], r['용접장합']), axis=1)

        project_summary = project_summary.sort_values('실행원단위', ascending=False)

        # 테이블 데이터 포맷팅: 기준/실행원단위는 계량원단위 대비 비율(%)도 함께 표기
        def _ratio_pct(value, base):
            if base == 0:
                return "N/A"
            return f"{value:.4f} ({value / base * 100:.1f}%)"

        project_summary_display = project_summary.copy()
        project_summary_display['기준원단위(계량비 %)'] = project_summary_display.apply(
            lambda r: _ratio_pct(r['기준원단위'], r['계량원단위']), axis=1
        )
        project_summary_display['실행원단위(계량비 %)'] = project_summary_display.apply(
            lambda r: _ratio_pct(r['실행원단위'], r['계량원단위']), axis=1
        )
        project_summary_display['계량원단위'] = project_summary_display['계량원단위'].apply(lambda x: f"{x:.4f}")
        project_summary_display = project_summary_display[
            ['프로젝트', '계량원단위', '기준원단위(계량비 %)', '실행원단위(계량비 %)']
        ]

        col1, col2 = st.columns([3, 2])

        with col1:
            # 그룹 바 차트
            fig = go.Figure(data=[
                go.Bar(name='계량원단위', x=project_summary['프로젝트'], y=project_summary['계량원단위'],
                       hovertemplate='계량원단위: %{y:.3f}<extra></extra>'),
                go.Bar(name='기준원단위', x=project_summary['프로젝트'], y=project_summary['기준원단위'],
                       hovertemplate='기준원단위: %{y:.3f}<extra></extra>'),
                go.Bar(name='실행원단위', x=project_summary['프로젝트'], y=project_summary['실행원단위'],
                       hovertemplate='실행원단위: %{y:.3f}<extra></extra>')
            ])
            fig.update_layout(
                barmode='group',
                xaxis_title="프로젝트",
                yaxis_title="원단위",
                height=400,
                hovermode='x unified',
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5)
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.dataframe(
                project_summary_display,
                use_container_width=True,
                hide_index=True
            )

    # TAB 2: 선종별 분석 (사이드바 필터 무시, 전체 데이터베이스 기준)
    with tab2:
        st.subheader("선종별 호선 실행공수·원단위 비교")
        st.markdown(
            "<div style='font-size:8pt; color:#888;'>사이드바 필터와 무관하게 전체 데이터 기준으로 표시됩니다.</div>",
            unsafe_allow_html=True
        )

        # 호선(프로젝트)별 실행공수·원단위 집계 (전체 df 기준)
        project_level = df.groupby(['선종', '프로젝트']).agg(
            용접장합=('용접장_total', 'sum'),
            계량합=('total_계량', 'sum'),
            기준합=('total_기준', 'sum'),
            실행합=('total_실행', 'sum'),
        ).reset_index()
        project_level['계량원단위'] = project_level.apply(lambda r: calc_wondanwi(r['계량합'], r['용접장합']), axis=1)
        project_level['기준원단위'] = project_level.apply(lambda r: calc_wondanwi(r['기준합'], r['용접장합']), axis=1)
        project_level['실행원단위'] = project_level.apply(lambda r: calc_wondanwi(r['실행합'], r['용접장합']), axis=1)

        col_left, col_right = st.columns([3, 2])

        # ─ 좌측: 선종별 콤보차트 (호선별 실행공수 막대 + 실행원단위 꺾은선), 세로 순차 배치
        with col_left:
            all_shiptypes_sorted = sorted(project_level['선종'].dropna().unique())
            for stype in all_shiptypes_sorted:
                stype_data = project_level[project_level['선종'] == stype].sort_values('프로젝트')

                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=stype_data['프로젝트'], y=stype_data['실행합'],
                    name='실행공수', yaxis='y1',
                    marker_color='#1f77b4',
                    customdata=[f"{v/1000:.1f}K" for v in stype_data['실행합']],
                    hovertemplate='실행공수: %{customdata}<extra></extra>'
                ))
                fig.add_trace(go.Scatter(
                    x=stype_data['프로젝트'], y=stype_data['실행원단위'],
                    name='실행원단위', yaxis='y2',
                    hovertemplate='실행원단위: %{y:.3f}<extra></extra>',
                    mode='lines+markers', line=dict(color='#d62728', width=3)
                ))
                fig.update_layout(
                    title=f"{stype} 호선별 실행공수·실행원단위",
                    xaxis_title="호선(프로젝트)",
                    yaxis=dict(title="실행공수"),
                    yaxis2=dict(title="실행원단위", overlaying='y', side='right'),
                    height=320,
                    hovermode='x unified',
                    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
                )
                st.plotly_chart(fig, use_container_width=True)

        # ─ 우측: 선종별 호선당 평균 요약 테이블
        with col_right:
            # 공수(계량/기준/실행)는 호선당 평균 = 선종 총합 ÷ 호선수
            shiptype_summary = project_level.groupby('선종').agg(
                호선수=('프로젝트', 'nunique'),
                계량공수평균=('계량합', 'mean'),
                기준공수평균=('기준합', 'mean'),
                실행공수평균=('실행합', 'mean'),
            ).reset_index()

            # 원단위는 개별(프로젝트/블록 등) 원단위를 절대 평균 내지 않고,
            # 선종 전체 데이터의 SUM(값) ÷ SUM(용접장_total)로 한 번에 계산한다.
            # (실행공수는 선종·stage별 R99 factor가 이미 행 단위로 반영되어 있으므로
            #  그대로 합산하면 되고, 비율 자체를 평균내면 안 됨)
            shiptype_raw_agg = project_level.groupby('선종').agg(
                용접장합=('용접장합', 'sum'),
                계량합=('계량합', 'sum'),
                기준합=('기준합', 'sum'),
                실행합=('실행합', 'sum'),
            ).reset_index()
            shiptype_raw_agg['계량원단위평균'] = shiptype_raw_agg.apply(lambda r: calc_wondanwi(r['계량합'], r['용접장합']), axis=1)
            shiptype_raw_agg['기준원단위평균'] = shiptype_raw_agg.apply(lambda r: calc_wondanwi(r['기준합'], r['용접장합']), axis=1)
            shiptype_raw_agg['실행원단위평균'] = shiptype_raw_agg.apply(lambda r: calc_wondanwi(r['실행합'], r['용접장합']), axis=1)

            shiptype_summary = shiptype_summary.merge(
                shiptype_raw_agg[['선종', '계량원단위평균', '기준원단위평균', '실행원단위평균']],
                on='선종'
            )

            display = shiptype_summary.copy()
            display['계량공수평균'] = display['계량공수평균'].round(0).astype(int).apply(lambda x: f"{x:,}")
            display['기준공수평균'] = display['기준공수평균'].round(0).astype(int).apply(lambda x: f"{x:,}")
            display['실행공수평균'] = display['실행공수평균'].round(0).astype(int).apply(lambda x: f"{x:,}")
            display['계량원단위평균'] = display['계량원단위평균'].apply(lambda x: f"{x:.4f}")
            display['기준원단위평균'] = display['기준원단위평균'].apply(lambda x: f"{x:.4f}")
            display['실행원단위평균'] = display['실행원단위평균'].apply(lambda x: f"{x:.4f}")
            # 전치 후 각 열(선종)의 dtype이 일관되도록 호선수도 문자열로 변환
            # (혼합 dtype이면 Arrow 직렬화 시 자동 형변환을 시도하다 실패함)
            display['호선수'] = display['호선수'].astype(str)

            # 선종을 열(가로)로, 지표를 행으로 전치
            display_t = display.set_index('선종').T
            display_t.index.name = '항목'
            display_t = display_t.reset_index()

            st.markdown("<div style='font-size:9pt; color:#666;'>선종별 호선당(프로젝트당) 평균값</div>", unsafe_allow_html=True)
            st.dataframe(display_t, use_container_width=True, hide_index=True)

    # TAB 3: Stage별 분석
    with tab3:
        st.subheader("Stage별 원단위 추이 (공정 단계별)")

        # 필터 선택 내용 표시
        filter_info = []
        if projects_filter:
            filter_info.append(f"프로젝트: {', '.join(projects_filter)}")
        if shiptype_filter:
            filter_info.append(f"선종: {', '.join(shiptype_filter)}")
        if selected_stages:
            filter_info.append(f"Stage: {', '.join(map(str, selected_stages))}")
        if selected_moblocks:
            filter_info.append(f"모블록: {', '.join(map(str, selected_moblocks))}")
        if selected_blocks:
            filter_info.append(f"블록: {', '.join(map(str, selected_blocks))}")

        if filter_info:
            st.markdown(f"<div style='font-size:8pt; color:#888;'>필터: {' | '.join(filter_info)}</div>", unsafe_allow_html=True)

        # Stage별 집계 (원단위 = SUM(값) ÷ SUM(용접장_total))
        stage_summary = filtered_df.groupby('stage').agg(
            용접장합=('용접장_total', 'sum'),
            total_계량=('total_계량', 'sum'),
            total_기준=('total_기준', 'sum'),
            total_실행=('total_실행', 'sum'),
        ).reset_index()
        stage_summary['계량원단위'] = stage_summary.apply(lambda r: calc_wondanwi(r['total_계량'], r['용접장합']), axis=1)
        stage_summary['기준원단위'] = stage_summary.apply(lambda r: calc_wondanwi(r['total_기준'], r['용접장합']), axis=1)
        stage_summary['실행원단위'] = stage_summary.apply(lambda r: calc_wondanwi(r['total_실행'], r['용접장합']), axis=1)

        stage_summary = stage_summary.sort_values('stage')

        # 테이블 데이터 포맷팅: 기준원단위/실행원단위는 계량원단위 대비 비율(%)을 함께 표기
        stage_summary_display = stage_summary.copy()

        def _ratio_pct(value, base):
            if base == 0:
                return "N/A"
            return f"{value:.4f} ({value / base * 100:.1f}%)"

        stage_summary_display['기준원단위(계량비 %)'] = stage_summary_display.apply(
            lambda r: _ratio_pct(r['기준원단위'], r['계량원단위']), axis=1
        )
        stage_summary_display['실행원단위(계량비 %)'] = stage_summary_display.apply(
            lambda r: _ratio_pct(r['실행원단위'], r['계량원단위']), axis=1
        )
        stage_summary_display['계량원단위'] = stage_summary_display['계량원단위'].apply(lambda x: f"{x:.4f}")
        stage_summary_display = stage_summary_display[
            ['stage', '계량원단위', '기준원단위(계량비 %)', '실행원단위(계량비 %)']
        ]
        stage_summary_display = stage_summary_display.rename(columns={'stage': 'Stage'})

        # 라인 차트 (x축은 stage에 실제 존재하는 값만 카테고리로 표시)
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=stage_summary['stage'].astype(str), y=stage_summary['계량원단위'],
            mode='lines+markers', name='계량원단위', line=dict(dash='dash'),
            hovertemplate='계량원단위: %{y:.3f}<extra></extra>'
        ))
        fig.add_trace(go.Scatter(
            x=stage_summary['stage'].astype(str), y=stage_summary['기준원단위'],
            mode='lines+markers', name='기준원단위',
            hovertemplate='기준원단위: %{y:.3f}<extra></extra>'
        ))
        fig.add_trace(go.Scatter(
            x=stage_summary['stage'].astype(str), y=stage_summary['실행원단위'],
            mode='lines+markers', name='실행원단위', line=dict(width=3),
            hovertemplate='실행원단위: %{y:.3f}<extra></extra>'
        ))

        fig.update_layout(
            title="Stage별 원단위 추이",
            xaxis_title="Stage",
            xaxis_type='category',
            yaxis_title="원단위",
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            stage_summary_display,
            use_container_width=True,
            hide_index=True
        )

    # TAB 4: 상세 데이터
    with tab4:
        st.subheader("필터된 상세 데이터")

        # 필터 선택 내용 표시
        filter_info = []
        if projects_filter:
            filter_info.append(f"프로젝트: {', '.join(projects_filter)}")
        if shiptype_filter:
            filter_info.append(f"선종: {', '.join(shiptype_filter)}")
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

    # ════════════════════════════════════════════════════════════════════════
    # 추가 분석: 공정별 공수 비율
    # ════════════════════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("## ■ 공정별 공수 분석")

    process_names = ['심출', '취부', '용접', '사상', '기타']
    process_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

    col1, col2, col3 = st.columns(3)

    process_cols = [
        (col1, '계량', '공정별 계량 비율', '계량공수(JMH)'),
        (col2, '기준', '공정별 기준공수 비율', '기준공수(JMH)'),
        (col3, '실행', '공정별 실행공수 비율', '실행공수(JMH)'),
    ]

    for col, kind, title, center_label in process_cols:
        with col:
            st.subheader(title)
            values = [filtered_df[f'{p}_{kind}'].sum() for p in process_names]
            total_value = sum(values)

            fig = go.Figure(data=[go.Pie(
                labels=process_names,
                values=values,
                hole=0.6,
                marker=dict(colors=process_colors),
                texttemplate='%{percent:.1%}',
                hovertemplate='%{label}: %{value:,.0f}<br>%{percent:.1%}<extra></extra>'
            )])
            fig.update_layout(
                height=380,
                margin=dict(t=20, b=60, l=10, r=10),
                showlegend=True,
                legend=dict(orientation='h', yanchor='top', y=-0.05, xanchor='center', x=0.5),
                annotations=[dict(
                    text=f"<span style='font-size:11px'>{center_label}</span><br><span style='font-size:18px'>{total_value:,.0f}</span>",
                    x=0.5, y=0.5,
                    font=dict(size=18),
                    showarrow=False
                )]
            )
            st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────
# 프로젝트 비교 모드
# ─────────────────────────────────────────────────────────────────────────
else:
    st.markdown("---")

    # ─ 프로젝트 비교 모드에 반응하는 사이드바 필터는 "선종"과 "모블록번호" 두 가지뿐
    _sidebar_selection_parts = []
    if shiptype_filter:
        _sidebar_selection_parts.append(f"[{', '.join(shiptype_filter)}]")
    if selected_moblocks:
        _sidebar_selection_parts.append(f"[{', '.join(selected_moblocks)}]")

    if _sidebar_selection_parts:
        _sidebar_caption = ', '.join(_sidebar_selection_parts) + "를 선택했습니다"
    else:
        _sidebar_caption = "프로젝트 A, B를 선택하세요"
    st.markdown(f"<div style='font-size:9pt; color:#666;'>{_sidebar_caption}</div>", unsafe_allow_html=True)

    # 선종이 선택되어 있으면 프로젝트 A/B 옵션을 해당 선종 소속 프로젝트로 좁힘
    if shiptype_filter:
        compare_project_options = sorted(df[df['선종'].isin(shiptype_filter)]['프로젝트'].unique())
    else:
        compare_project_options = all_projects

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 프로젝트 A")
        project_a = st.selectbox(
            "프로젝트 선택",
            options=compare_project_options,
            key='compare_project_a'
        )
        if project_a:
            info_a = get_project_info_text(project_a)
            st.markdown(f"<div class='project-info'>{project_a} {info_a}</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("### 프로젝트 B")
        project_b = st.selectbox(
            "프로젝트 선택",
            options=compare_project_options,
            key='compare_project_b'
        )
        if project_b:
            info_b = get_project_info_text(project_b)
            st.markdown(f"<div class='project-info'>{project_b} {info_b}</div>", unsafe_allow_html=True)

    st.markdown("---")

    # ─ 블록+Stage 단위 원단위 편차 분석
    # 이 탭에 반응하는 사이드바 필터는 모블록번호뿐 (블록번호/Stage 필터는 미반영)
    def get_project_wondanwi_table(project_name):
        sub = df[df['프로젝트'] == project_name]
        if selected_moblocks:
            sub = sub[sub['모블록번호'].isin(selected_moblocks)]
        if sub.empty:
            return None

        grp = sub.groupby(['블록번호', 'stage']).agg(
            용접장합=('용접장_total', 'sum'),
            계량합=('total_계량', 'sum'),
            기준합=('total_기준', 'sum'),
            실행합=('total_실행', 'sum'),
        ).reset_index()
        grp['계량원단위'] = grp.apply(lambda r: calc_wondanwi(r['계량합'], r['용접장합']), axis=1)
        grp['기준원단위'] = grp.apply(lambda r: calc_wondanwi(r['기준합'], r['용접장합']), axis=1)
        grp['실행원단위'] = grp.apply(lambda r: calc_wondanwi(r['실행합'], r['용접장합']), axis=1)
        return grp.sort_values(['블록번호', 'stage']).reset_index(drop=True)

    def render_project_wondanwi(project_name, label):
        st.markdown(f"#### {label}: {project_name}")
        grp = get_project_wondanwi_table(project_name)

        if grp is None or grp.empty:
            if selected_moblocks:
                st.info(f"해당 모블록번호는 없습니다. ({', '.join(selected_moblocks)})")
            else:
                st.info("선택한 조건에 해당하는 데이터가 없습니다.")
            return None

        # 표시 항목: 블록번호/STAGE/용접장합/기준공수합/기준원단위/실행공수합/실행원단위
        # 공수(용접장합/기준공수합/실행공수합)는 정수+1000단위 구분기호, 원단위는 소수점 3자리
        display_df = grp.copy()
        display_df['용접장합'] = display_df['용접장합'].round(0).astype(int).apply(lambda x: f"{x:,}")
        display_df['기준공수합'] = display_df['기준합'].round(0).astype(int).apply(lambda x: f"{x:,}")
        display_df['실행공수합'] = display_df['실행합'].round(0).astype(int).apply(lambda x: f"{x:,}")
        display_df['기준원단위'] = display_df['기준원단위'].apply(lambda x: f"{x:.3f}")
        display_df['실행원단위'] = display_df['실행원단위'].apply(lambda x: f"{x:.3f}")
        display_df = display_df.rename(columns={'stage': 'STAGE'})
        st.dataframe(
            display_df[['블록번호', 'STAGE', '용접장합', '기준공수합', '기준원단위', '실행공수합', '실행원단위']],
            use_container_width=True, hide_index=True
        )

        # 블록+Stage 조합이 2개 이상일 때만 편차 표시 (1개면 편차 개념이 성립하지 않음)
        if len(grp) > 1:
            dev_lines = []
            for col_name, kr_label in [('기준원단위', '기준'), ('실행원단위', '실행')]:
                max_row = grp.loc[grp[col_name].idxmax()]
                min_row = grp.loc[grp[col_name].idxmin()]
                dev = round(max_row[col_name] - min_row[col_name], 3)
                dev_lines.append(
                    f"{kr_label}원단위 편차(최대-최소): <b>{dev:.3f}</b> "
                    f"(최대 {max_row['블록번호']}-S{max_row['stage']}: {max_row[col_name]:.3f}, "
                    f"최소 {min_row['블록번호']}-S{min_row['stage']}: {min_row[col_name]:.3f})"
                )
            st.markdown(
                "<div style='font-size:9pt; color:#808080; line-height:1.6;'>" +
                "<br>".join(dev_lines) + "</div>",
                unsafe_allow_html=True
            )

        return grp

    if project_a and project_b and project_a != project_b:
        col_a, col_b = st.columns(2)
        with col_a:
            grp_a = render_project_wondanwi(project_a, "프로젝트 A")
        with col_b:
            grp_b = render_project_wondanwi(project_b, "프로젝트 B")

        # ─ 실행원단위 편차 상위 10개 (프로젝트 A+B 데이터 기준)
        combined_parts = []
        if grp_a is not None:
            t = grp_a.copy()
            t['프로젝트'] = project_a
            combined_parts.append(t)
        if grp_b is not None:
            t = grp_b.copy()
            t['프로젝트'] = project_b
            combined_parts.append(t)

        if combined_parts:
            combined = pd.concat(combined_parts, ignore_index=True)
            if len(combined) > 1:
                mean_exec = combined['실행원단위'].mean()
                combined['평균과의차이'] = (combined['실행원단위'] - mean_exec).abs().round(4)
                top10 = combined.sort_values('평균과의차이', ascending=False).head(10)

                st.markdown("---")
                st.markdown("### ■ 실행원단위 편차 상위 10개 (프로젝트 A+B 기준)")
                st.dataframe(
                    top10[['프로젝트', '블록번호', 'stage', '실행원단위', '평균과의차이']].rename(
                        columns={'stage': 'Stage'}
                    ),
                    use_container_width=True, hide_index=True
                )
    elif project_a == project_b:
        st.warning("⚠️ 다른 프로젝트를 선택해주세요.")
    else:
        st.info("ℹ️ 프로젝트 A, B를 모두 선택해주세요.")

# ════════════════════════════════════════════════════════════════════════════
# 푸터
# ════════════════════════════════════════════════════════════════════════════
st.markdown("---")
# 생성일: 데이터베이스 연결 시 조회 시점의 날짜/시간을 표시 (현재는 앱 렌더링 시각)
_generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.markdown(f"**생성일**: {_generated_at} | **데이터**: ")
