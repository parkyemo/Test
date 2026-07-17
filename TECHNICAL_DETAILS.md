# 🔧 Hull 대시보드 - 기술 상세 문서

---

## 📐 코드 구조 분석

### 1. 초기화 블록 (Section 1-3)

#### 페이지 설정
```python
st.set_page_config(
    page_title="Hull 실적 대시보드",
    page_icon="⛵",
    layout="wide",              # 와이드 레이아웃
    initial_sidebar_state="expanded"
)
```
- **wide**: 화면 전체 너비 사용 (기본값: centered)
- **sidebar**: 좌측 필터 패널 기본 열림 상태

#### 데이터 로드 캐싱
```python
@st.cache_data
def load_data():
    # CSV 파일 읽기 (UTF-8-SIG 인코딩)
    erec_df = pd.read_csv(erec_path, encoding='utf-8-sig')
```
- **@st.cache_data**: 함수 반환값을 메모리에 캐싱
  - 첫 실행: 파일 로드
  - 이후 실행: 캐시된 데이터프레임 사용 (즉시 반환)
  - 스크립트 재실행 시 재평가
- **utf-8-sig**: BOM(Byte Order Mark) 처리 (Excel 호환)

---

### 2. 데이터 조인 & 계산 블록 (Section 3)

#### 통합 데이터프레임 생성
```python
# 1단계: Hull_erec_baseMH ← Hull_info (프로젝트→선종 매핑)
merged = erec_df.merge(
    info_df[['프로젝트', '선종']],
    on='프로젝트',
    how='left'
)

# 2단계: merged ← R99_rate (선종+stage→R99율)
merged = merged.merge(
    r99_df[['선종', 'stage', 'R99율']],
    on=['선종', 'stage'],
    how='left'
)
```

**조인 방식 선택 사유:**
- `how='left'`: 실적 데이터(erec_df) 기준 유지
- 선종 또는 R99율이 없는 경우도 행 유지
- 미매칭 시 NaN 값 발생 → 다음 단계에서 처리

#### 실행공수 계산
```python
merged['total_실행'] = (merged['total_기준'] * (1 + merged['R99율'])).round(2)
```

**계산 체계:**
```
실행공수 = 기준공수 × (1 + R99율)

예시 (LNG, stage 40, 기준공수 100):
  → 100 × (1 + 0.221) = 122.1 (실행공수)

R99율의 의미:
  - 0.221 = 22.1% 추가 공수 발생
  - 공정 특성상 계획보다 많은 공수 소요
```

**5개 공정별 실행공수 분해:**
```python
merged['심출_실행'] = (merged['심출_기준'] * (1 + merged['R99율'])).round(2)
merged['취부_실행'] = (merged['취부_기준'] * (1 + merged['R99율'])).round(2)
merged['용접_실행'] = (merged['용접_기준'] * (1 + merged['R99율'])).round(2)
merged['사상_실행'] = (merged['사상_기준'] * (1 + merged['R99율'])).round(2)
merged['기타_실행'] = (merged['기타_기준'] * (1 + merged['R99율'])).round(2)
```

---

### 3. 필터 로직 (Section 4)

#### 다중선택 필터 구현
```python
selected_projects = st.sidebar.multiselect(
    "프로젝트 선택",
    options=all_projects,
    default=all_projects  # 초기값: 전체 선택
)

filtered_df = df[
    (df['프로젝트'].isin(selected_projects)) &  # AND 조건
    (df['선종'].isin(selected_shiptype)) &
    (df['stage'].isin(selected_stages))
]
```

**필터 작동 흐름:**
1. 고유값 추출: `df['프로젝트'].unique()`
2. 사용자 선택받기: `st.sidebar.multiselect()`
3. 부울 마스킹: `df[...].isin(selected_values)`
4. 교집합: `&` 연산자로 3개 조건 동시 만족

**성능 최적화:**
- 부울 인덱싱: O(n) 시간복잡도
- 100만 행 수준에서도 <100ms 응답

---

### 4. KPI 지표 (Section 5)

#### 5단계 메트릭 배치
```python
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("계량 총합", f"{total_qty:,.0f}")
```

**Streamlit 레이아웃:**
- `st.columns(5)`: 5개 동일 너비 열 생성
- `with col1:` 내의 위젯은 해당 열에 배치
- 숫자 포매팅: `,` (천 단위 구분), `.0f` (정수)

#### 조건부 계산
```python
if total_std > 0:
    ratio = (total_exec / total_std - 1) * 100  # 백분율
    st.metric("기준 대비 증가율", f"{ratio:.1f}%")
else:
    st.metric("기준 대비 증가율", "N/A")
```

**계산식 의미:**
```
증가율 = (실행공수 / 기준공수 - 1) × 100

예시:
  실행공수 122, 기준공수 100
  → (122/100 - 1) × 100 = 22%
```

---

### 5. 탭 구조 (Section 6)

#### 탭 생성 및 분할
```python
tab1, tab2, tab3, tab4 = st.tabs(["📈 프로젝트별", "🚢 선종별", "📍 Stage별", "📋 상세 데이터"])

with tab1:
    # Tab 1 컨텐츠
```

**특징:**
- 4개 탭: 독립적인 분석 관점
- `with tab1:` 블록 내 모든 위젯이 해당 탭에 렌더링
- 사용자 탭 클릭 시에만 해당 내용 로드

---

### 6. 차트 시각화 (Plotly)

#### 그룹 바 차트 (Tab 1)
```python
fig = go.Figure(data=[
    go.Bar(name='계량', x=project_summary['프로젝트'], y=project_summary['total_계량']),
    go.Bar(name='기준', x=project_summary['프로젝트'], y=project_summary['total_기준']),
    go.Bar(name='실행공수', x=project_summary['프로젝트'], y=project_summary['total_실행'])
])
fig.update_layout(barmode='group', ...)
```

**barmode 옵션:**
- `group`: 나란히 배치 (기본값)
- `stack`: 누적 바
- `relative`: 정규화된 누적 바

#### 도넛 차트 (Tab 2)
```python
fig = go.Figure(data=[go.Pie(
    labels=shiptype_summary['선종'],
    values=shiptype_summary['total_실행'],
    hole=0.3  # 도넛 가운데 구멍 (0.0~1.0)
)])
```

**hole 파라미터:**
- 0.0: 일반 파이 차트
- 0.3: 도넛 차트 (중앙 구멍 30%)

#### 라인 차트 (Tab 3)
```python
fig.add_trace(go.Scatter(
    x=stage_summary['stage'],
    y=stage_summary['total_계량'],
    mode='lines+markers',      # 선 + 포인트
    name='계량',
    line=dict(dash='dash')     # 대시 라인
))
```

**mode 옵션:**
- `lines`: 실선만
- `markers`: 포인트만
- `lines+markers`: 선 + 포인트
- `text`: 텍스트 레이블

**line 옵션:**
- `dash`: 'solid'(기본), 'dash', 'dot', 'dashdot'
- `width`: 선 굵기
- `color`: 선 색상

---

### 7. 데이터 테이블 (Tab 4)

#### Dataframe 렌더링
```python
st.dataframe(
    filtered_df[display_cols],
    use_container_width=True,   # 화면 너비에 맞춤
    hide_index=True,             # 인덱스 숨김
    height=600                   # 스크롤 높이
)
```

#### CSV 다운로드
```python
csv = filtered_df[display_cols].to_csv(index=False, encoding='utf-8-sig')
st.download_button(
    label="💾 필터된 데이터 CSV 다운로드",
    data=csv,
    file_name="hull_dashboard_export.csv",
    mime="text/csv"
)
```

**작동 방식:**
1. `.to_csv()`: 데이터프레임 → 문자열로 변환
2. `st.download_button()`: 다운로드 버튼 렌더링
3. 사용자 클릭 시: 브라우저 기본 다운로드 실행

---

## 🔄 데이터 흐름도

```
┌─────────────────────────────────────────────────┐
│           CSV 파일 (3종)                         │
│  Hull_erec_baseMH(4402행) + Hull_info(10행)    │
│  + R99_rate(28행)                               │
└────────────┬────────────────────────────────────┘
             │ @st.cache_data
             ↓
┌─────────────────────────────────────────────────┐
│       load_data()                                │
│  - 각 CSV를 pandas DataFrame로 읽기             │
│  - 메모리에 캐싱                                 │
└────────────┬────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────┐
│   prepare_dashboard_data()                       │
│  1. erec_df ⇐ info_df (프로젝트→선종)          │
│  2. merged ⇐ r99_df (선종+stage→R99율)         │
│  3. 실행공수 = 기준공수 × (1 + R99율)           │
└────────────┬────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────┐
│    필터 (사이드바)                               │
│  - 프로젝트 multiselect                          │
│  - 선종 multiselect                              │
│  - Stage multiselect                             │
│  → filtered_df 생성                             │
└────────────┬────────────────────────────────────┘
             │
             ↓
┌─────────────────────────────────────────────────┐
│   시각화 & 분석                                  │
│  - KPI 메트릭 (5개)                              │
│  - 탭 1-4 (차트/테이블)                          │
│  - 공정별 분석                                   │
└─────────────────────────────────────────────────┘
```

---

## 🗂️ 테이블 매핑 & 컬럼 활용

### Hull_erec_baseMH
```
┌─────────────────────────────────────────────────────────┐
│ 프로젝트(KEY) │ 모블록번호 │ 블록번호 │ stage │ ...    │
├─────────────────────────────────────────────────────────┤
│ SN1409        │ R87FA     │ R877R   │ 30    │ ...     │
│ SN1409        │ R87FA     │ R877R   │ 30    │ ...     │
│ ...           │ ...       │ ...     │ ...   │ ...     │
└─────────────────────────────────────────────────────────┘

공수 컬럼:
  - total_계량, total_기준 (원본)
  - total_실행 (계산)
  
공정별 분해 (심출, 취부, 용접, 사상, 기타 각 3개):
  - 심출_계량, 심출_기준, 심출_실행
  - 취부_계량, 취부_기준, 취부_실행
  - 용접_계량, 용접_기준, 용접_실행
  - 사상_계량, 사상_기준, 사상_실행
  - 기타_계량, 기타_기준, 기타_실행
```

### Hull_info
```
┌─────────────────────────────┐
│ 프로젝트(KEY) │ 선종(JOIN KEY) │ ...  │
├─────────────────────────────┤
│ SN1409        │ LNG          │ ...  │
│ SN1412        │ CONT         │ ...  │
│ ...           │ ...          │ ...  │
└─────────────────────────────┘

역할: 프로젝트 ↔ 선종 매핑
대시보드에서 사용: 프로젝트 필터 + 선종별 분석
```

### R99_rate
```
┌────────────────────────┐
│ 선종 │ stage │ R99율  │
├────────────────────────┤
│ LNG  │ 40    │ 0.221 │
│ LNG  │ 50    │ 0.312 │
│ ...  │ ...   │ ...   │
└────────────────────────┘

역할: 실행공수 계산용 factor
대시보드에서 사용: 모든 공수 계산에 적용
```

---

## ⚡ 성능 고려사항

### 메모리 사용량 추정
```python
# 대략적인 메모리 사용량 (단위: MB)
erec_df: 4402행 × 28열 ≈ 5-10 MB
info_df: 10행 × 7열 ≈ 0.01 MB
r99_df: 28행 × 3열 ≈ 0.01 MB
merged_df: 4402행 × 32열 ≈ 10-15 MB

총계: ~25 MB (캐시 포함)
→ 대부분 PC/서버에서 무리없음
```

### 쿼리 속도 (필터링)
```python
# 부울 인덱싱 성능
4402행 데이터프레임에서 필터링:
  - 단일 조건: <1ms
  - 3개 AND 조건: <5ms
  - 결과: 체감 지연 없음 (Streamlit 렌더링 시간이 더 김)
```

### 캐싱 효과
```
첫 실행 (캐시 미스):
  load_data() → 100-200ms
  prepare_dashboard_data() → 50-100ms
  렌더링 → 500-1000ms
  총: 1-2초

재실행 (캐시 히트):
  load_data() → 캐시 (0ms)
  prepare_dashboard_data() → 캐시 (0ms)
  필터링 → 5ms
  렌더링 → 500-1000ms
  총: 0.5-1초
```

---

## 🐛 일반적인 버그 & 해결책

### 1. "정렬할 수 없음" 오류
```python
# ❌ 오류 원인
stage_summary = stage_summary.sort_values('stage')  # stage가 문자열(str)

# ✅ 해결책
filtered_df['stage'] = filtered_df['stage'].astype(int)  # 숫자로 변환
stage_summary = stage_summary.sort_values('stage')
```

### 2. NaN 값으로 인한 차트 깨짐
```python
# ❌ 원인
df['R99율'].fillna(0.0)  # 이미 선택한 행에서 NaN 존재
→ 계산 시 NaN이 0이 아님 (NaN * 100 = NaN)

# ✅ 해결책
df['R99율'].fillna(0.0, inplace=True)  # 데이터 로드 직후 처리
df['total_실행'].fillna(0.0, inplace=True)  # 계산 후에도 적용
```

### 3. 필터가 작동하지 않음
```python
# ❌ 원인: 부울 배열 크기 불일치
filtered_df = df[mask1 & mask2 & mask3]  # 인덱스 정렬 안 됨

# ✅ 해결책
filtered_df = df[(mask1) & (mask2) & (mask3)]  # 괄호 명시
# 또는
filtered_df = df.loc[df.index.isin(...) & ...]  # 명시적 인덱싱
```

---

## 🔌 실제 DB 연결 준비

### 현재 (CSV 기반)
```python
@st.cache_data
def load_data():
    erec_df = pd.read_csv('Hull_erec_baseMH.csv')
    info_df = pd.read_csv('Hull_info.csv')
    r99_df = pd.read_csv('R99_rate.csv')
    return erec_df, info_df, r99_df
```

### 향후 (SQL Server 기반, 예시)
```python
import sqlalchemy as sa

@st.cache_resource  # 데이터베이스 연결은 resource 캐시
def get_db_connection():
    engine = sa.create_engine(
        'mssql+pyodbc://user:pass@server/db?driver=ODBC+Driver+17+for+SQL+Server'
    )
    return engine

@st.cache_data(ttl=3600)  # 1시간 캐시
def load_data_from_db():
    engine = get_db_connection()
    erec_df = pd.read_sql('SELECT * FROM Hull_erec_baseMH', engine)
    info_df = pd.read_sql('SELECT * FROM Hull_info', engine)
    r99_df = pd.read_sql('SELECT * FROM R99_rate', engine)
    return erec_df, info_df, r99_df
```

**변경점:**
1. `@st.cache_data` → `@st.cache_resource` (DB 연결용)
2. CSV 파일 읽기 → SQL 쿼리
3. 필요시 `ttl=3600` (1시간마다 자동 새로고침)

---

## 📚 Streamlit 핵심 API 참고

| 함수 | 용도 | 예시 |
|------|------|------|
| `st.sidebar.XXX` | 사이드바 위젯 | `st.sidebar.multiselect()` |
| `st.columns()` | 열 레이아웃 | `col1, col2 = st.columns(2)` |
| `st.tabs()` | 탭 생성 | `tab1, tab2 = st.tabs(['Tab1', 'Tab2'])` |
| `st.metric()` | KPI 표시 | `st.metric("라벨", 123)` |
| `st.dataframe()` | 테이블 렌더링 | `st.dataframe(df)` |
| `st.plotly_chart()` | Plotly 차트 | `st.plotly_chart(fig)` |
| `st.download_button()` | 다운로드 | `st.download_button(..., data=csv)` |
| `@st.cache_data` | 데이터 캐싱 | `@st.cache_data def load(): ...` |

---

## 🎓 학습 경로

**Streamlit 입문 (1-2일)**
1. 공식 튜토리얼: https://docs.streamlit.io/get-started
2. 기본 위젯: `st.text()`, `st.button()`, `st.slider()`

**데이터 시각화 (2-3일)**
1. Plotly 기본: Bar, Line, Pie 차트
2. Streamlit 통합: `st.plotly_chart()`

**대시보드 구축 (3-5일)**
1. 데이터 조인: Pandas `.merge()`
2. 필터 로직: 부울 인덱싱
3. 레이아웃: columns, tabs, expander

**프로덕션 배포 (2-3일)**
1. Streamlit Cloud (클라우드 호스팅)
2. Docker (로컬 호스팅)
3. 비용/보안 고려사항

---

**마지막 업데이트**: 2024년  
**작성자**: 아트박
