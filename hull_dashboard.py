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
# 4. 사이드바 필터
# ============================================================================
st.sidebar.header("🔍 필터")

# 모든 필터 옵션 정의
all_projects = sorted(df['프로젝트'].unique())
all_shiptype = sorted(df['선종'].dropna().unique())
all_stages = sorted(df['stage'].unique())

# 필터 초기화 함수
def reset_filters():
    st.session_state.projects_filter = all_projects
    st.session_state.shiptype_filter = all_shiptype
    st.session_state.stages_filter = all_stages

# Session state 초기화
if 'projects_filter' not in st.session_state:
    st.session_state.projects_filter = all_projects
if 'shiptype_filter' not in st.session_state:
    st.session_state.shiptype_filter = all_shiptype
if 'stages_filter' not in st.session_state:
    st.session_state.stages_filter = all_stages

# 프로젝트 필터
selected_projects = st.sidebar.multiselect(
    "프로젝트 선택",
    options=all_projects,
    default=st.session_state.projects_filter,
    key='projects_filter'
)

# 선종 필터
selected_shiptype = st.sidebar.multiselect(
    "선종 선택",
    options=all_shiptype,
    default=st.session_state.shiptype_filter,
    key='shiptype_filter'
)

# Stage 필터
selected_stages = st.sidebar.multiselect(
    "Stage 선택",
    options=all_stages,
    default=st.session_state.stages_filter,
    key='stages_filter'
)

# 필터 초기화 버튼
st.sidebar.markdown("---")
if st.sidebar.button("🔄 필터 초기화", use_container_width=True):
    reset_filters()
    st.rerun()

# 필터 적용
filtered_df = df[
    (df['프로젝트'].isin(selected_projects)) &
    (df['선종'].isin(selected_shiptype)) &
    (df['stage'].isin(selected_stages))
].copy()

# 필터 결과 요약
st.sidebar.markdown("---")
st.sidebar.metric("필터된 행 수", len(filtered_df))
st.sidebar.metric("프로젝트 수", filtered_df['프로젝트'].nunique())
st.sidebar.metric("선종 수", filtered_df['선종'].nunique())

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
tab1, tab2, tab3, tab4 = st.tabs(["📈 프로젝트별", "🚢 선종별", "📍 Stage별", "📋 상세 데이터"])

# ─────────────────────────────────────────────────────────────────────────
# TAB 1: 프로젝트별 분석
# ─────────────────────────────────────────────────────────────────────────
with tab1:
    st.subheader("프로젝트별 공수 비교")
    
    # 프로젝트별 집계
    project_summary = filtered_df.groupby('프로젝트').agg({
        'total_계량': 'sum',
        'total_기준': 'sum',
        'total_실행': 'sum'
    }).reset_index()
    
    project_summary = project_summary.sort_values('total_실행', ascending=False)
    
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
            project_summary.rename(columns={
                'total_계량': '계량',
                'total_기준': '기준',
                'total_실행': '실행공수'
            }),
            use_container_width=True,
            hide_index=True
        )

# ─────────────────────────────────────────────────────────────────────────
# TAB 2: 선종별 분석
# ─────────────────────────────────────────────────────────────────────────
with tab2:
    st.subheader("선종별 공수 비교")
    
    # 선종별 집계
    shiptype_summary = filtered_df.groupby('선종').agg({
        'total_계량': 'sum',
        'total_기준': 'sum',
        'total_실행': 'sum',
        'R99율': 'mean'  # 평균 R99율
    }).reset_index()
    
    shiptype_summary['R99율_%'] = (shiptype_summary['R99율'] * 100).round(1)
    shiptype_summary = shiptype_summary.sort_values('total_실행', ascending=False)
    
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
            shiptype_summary[[
                '선종', 'total_계량', 'total_기준', 'total_실행', 'R99율_%'
            ]].rename(columns={
                'total_계량': '계량',
                'total_기준': '기준',
                'total_실행': '실행공수',
                'R99율_%': 'R99율(%)'
            }),
            use_container_width=True,
            hide_index=True
        )

# ─────────────────────────────────────────────────────────────────────────
# TAB 3: Stage별 분석
# ─────────────────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Stage별 공수 분포 (공정 단계별)")
    
    # Stage별 집계
    stage_summary = filtered_df.groupby('stage').agg({
        'total_계량': 'sum',
        'total_기준': 'sum',
        'total_실행': 'sum'
    }).reset_index()
    
    stage_summary = stage_summary.sort_values('stage')
    
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
        stage_summary.rename(columns={
            'total_계량': '계량',
            'total_기준': '기준',
            'total_실행': '실행공수'
        }),
        use_container_width=True,
        hide_index=True
    )

# ─────────────────────────────────────────────────────────────────────────
# TAB 4: 상세 데이터
# ─────────────────────────────────────────────────────────────────────────
with tab4:
    st.subheader("필터된 상세 데이터")
    
    # 표시할 컬럼 선택
    display_cols = [
        '프로젝트', '모블록번호', '블록번호', 'stage', '선종',
        '모듈',
        'total_계량', 'total_기준', 'total_실행',
        'R99율'
    ]
    
    # 상세 데이터 테이블
    st.dataframe(
        filtered_df[display_cols].rename(columns={
            'total_계량': '계량',
            'total_기준': '기준',
            'total_실행': '실행공수',
            'R99율': 'R99율'
        }),
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

st.markdown("---")
st.markdown("**생성일**: 2024년 | **데이터**: 더미데이터 (seed=42)")
