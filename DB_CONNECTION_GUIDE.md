# 🗄️ Hull 대시보드 - 실제 DB 연결 가이드

> 현재 CSV 더미데이터 기반 대시보드를 **실제 회사 DB와 연결**하기 위한 준비 문서

---

## 📋 사전 확인 사항

### 필수 정보 수집
회사 DB 담당자로부터 다음 정보를 먼저 확보해야 합니다:

```
[ ] 1. DB 유형 (SQL Server / Oracle / MySQL / PostgreSQL)
[ ] 2. 서버 주소 (hostname 또는 IP)
[ ] 3. 포트 번호 (기본값: SQL Server 1433, Oracle 1521, MySQL 3306)
[ ] 4. 데이터베이스 이름
[ ] 5. 계정 정보 (username / password)
[ ] 6. 테이블 이름 & 스키마
     - Hull_erec_baseMH
     - Hull_info
     - R99_rate
[ ] 7. 행 수 규모 (현재 더미: ~4400행)
[ ] 8. 접근 권한 (읽기만 가능 vs 읽기+쓰기)
[ ] 9. VPN/방화벽 요구사항
```

### 네트워크 연결 테스트
```bash
# SQL Server 연결 테스트 (telnet 또는 Test-Connection)
telnet {서버주소} {포트}

# 또는 PowerShell
Test-NetConnection -ComputerName {서버주소} -Port {포트}
```

---

## 🔧 단계별 구현

### Phase 1: 로컬 개발 환경 설정

#### 1.1 필수 패키지 설치
```bash
# SQL Server 기본
pip install pyodbc sqlalchemy pandas

# Oracle (별도)
pip install oracledb sqlalchemy

# MySQL (별도)
pip install mysql-connector-python sqlalchemy

# PostgreSQL (별도)
pip install psycopg2 sqlalchemy
```

#### 1.2 드라이버 설치 (Windows)
```bash
# SQL Server ODBC 드라이버
# 1. 공식 다운로드: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
# 2. 또는 choco install odbc-driver-17-for-sql-server (관리자 권한)
```

---

### Phase 2: 연결 코드 작성

#### 2.1 SQL Server 예제
```python
import sqlalchemy as sa
from sqlalchemy import create_engine, text
import streamlit as st
import pandas as pd

@st.cache_resource
def get_db_engine():
    """
    SQL Server 연결 객체 생성 (캐시됨)
    - @st.cache_resource: 애플리케이션 수명동안 유지
    - DB 연결은 생성 비용이 높으므로 1회만 생성
    """
    server = "your_server_address"      # 예: "192.168.1.100"
    port = 1433
    database = "hull_db"
    username = "sa"
    password = "your_password"
    
    # ODBC 드라이버를 사용한 연결 문자열
    connection_string = (
        f"mssql+pyodbc://{username}:{password}@{server}:{port}/{database}?"
        f"driver=ODBC+Driver+17+for+SQL+Server"
    )
    
    try:
        engine = create_engine(connection_string)
        # 연결 테스트
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        st.success("✅ DB 연결 성공")
        return engine
    except Exception as e:
        st.error(f"❌ DB 연결 실패: {e}")
        return None

@st.cache_data(ttl=3600)  # 1시간마다 자동 새로고침
def load_data_from_db():
    """
    DB에서 3개 테이블 로드 (캐시됨)
    - ttl=3600: 3600초(1시간) 후 자동 무효화
    """
    engine = get_db_engine()
    if engine is None:
        return None, None, None
    
    try:
        erec_df = pd.read_sql(
            "SELECT * FROM dbo.Hull_erec_baseMH",
            engine
        )
        info_df = pd.read_sql(
            "SELECT * FROM dbo.Hull_info",
            engine
        )
        r99_df = pd.read_sql(
            "SELECT * FROM dbo.R99_rate",
            engine
        )
        
        st.info(f"✅ 로드 완료: {len(erec_df)} 행")
        return erec_df, info_df, r99_df
    
    except Exception as e:
        st.error(f"❌ 데이터 로드 실패: {e}")
        return None, None, None
```

**key 포인트:**
- `@st.cache_resource`: DB 연결은 **resource** 캐시 (수명주기 길음)
- `@st.cache_data`: 쿼리 결과는 **data** 캐시 (ttl 설정으로 주기적 갱신)
- 예외 처리: 연결 실패 시 사용자에게 알림

#### 2.2 Oracle 예제
```python
@st.cache_resource
def get_oracle_engine():
    """Oracle 데이터베이스 연결"""
    oracle_dsn = (
        f"oracle+oracledb://username:password"
        f"@server_address:1521/database_name"
    )
    engine = create_engine(oracle_dsn)
    return engine

@st.cache_data(ttl=1800)  # 30분
def load_oracle_data():
    engine = get_oracle_engine()
    
    # Oracle 테이블명은 대문자 (스키마명 포함 권장)
    erec_df = pd.read_sql(
        "SELECT * FROM SCHEMA_NAME.HULL_EREC_BASEMH",
        engine
    )
    return erec_df
```

#### 2.3 환경변수를 통한 보안 (권장)
```python
# .streamlit/secrets.toml 파일에 저장
# (git에 커밋하지 않을 것!)
[database]
server = "192.168.1.100"
port = 1433
database = "hull_db"
username = "hull_user"
password = "secure_password_here"

# Python 코드에서 접근
import streamlit as st

db_config = st.secrets["database"]
connection_string = (
    f"mssql+pyodbc://{db_config['username']}:{db_config['password']}"
    f"@{db_config['server']}:{db_config['port']}/{db_config['database']}?"
    f"driver=ODBC+Driver+17+for+SQL+Server"
)
```

---

### Phase 3: 쿼리 최적화

#### 3.1 필터 조건을 DB에서 처리
```python
# ❌ 비효율적: 전체 데이터를 메모리에 로드 후 필터링
@st.cache_data
def load_all_data():
    df = pd.read_sql("SELECT * FROM Hull_erec_baseMH", engine)
    return df

df = load_all_data()
filtered = df[df['선종'] == 'LNG']  # 메모리에서 필터링

# ✅ 효율적: DB에서 필터링 후 필터된 데이터만 로드
@st.cache_data
def load_filtered_data(shiptype='LNG', stage=None):
    query = f"SELECT * FROM Hull_erec_baseMH WHERE 선종 = '{shiptype}'"
    if stage:
        query += f" AND stage = {stage}"
    df = pd.read_sql(query, engine)
    return df

filtered = load_filtered_data('LNG')
```

**성능 차이:**
```
전체 로드: 4402행 × 28열 → ~10MB 메모리
필터 로드: 400행 × 28열 → ~1MB 메모리
→ 10배 메모리 절감, 네트워크 대역폭 절감
```

#### 3.2 인덱스 활용
```sql
-- DB 담당자에게 요청할 사항
-- Hull_erec_baseMH에 다음 인덱스 생성
CREATE INDEX idx_project ON Hull_erec_baseMH(프로젝트);
CREATE INDEX idx_shiptype ON Hull_erec_baseMH(선종);
CREATE INDEX idx_stage ON Hull_erec_baseMH(stage);
CREATE CLUSTERED INDEX idx_combo ON Hull_erec_baseMH(프로젝트, 선종, stage);
```

#### 3.3 집계 쿼리 활용
```python
# ❌ 메모리에서 집계
df_all = pd.read_sql("SELECT * FROM Hull_erec_baseMH", engine)
project_summary = df_all.groupby('프로젝트')['total_실행'].sum()

# ✅ DB에서 직접 집계 (더 빠름)
project_summary = pd.read_sql("""
    SELECT 프로젝트, SUM(total_기준) as total_기준, SUM(total_실행) as total_실행
    FROM Hull_erec_baseMH
    GROUP BY 프로젝트
    ORDER BY total_실행 DESC
""", engine)
```

---

### Phase 4: 실제 DB 기반 대시보드 수정

#### 4.1 load_data() 함수 교체
```python
# 현재 코드 (CSV 기반)
@st.cache_data
def load_data():
    erec_df = pd.read_csv("Hull_erec_baseMH.csv", encoding='utf-8-sig')
    info_df = pd.read_csv("Hull_info.csv", encoding='utf-8-sig')
    r99_df = pd.read_csv("R99_rate.csv", encoding='utf-8-sig')
    return erec_df, info_df, r99_df

# 수정 후 (DB 기반)
@st.cache_data(ttl=3600)
def load_data():
    engine = get_db_engine()
    if engine is None:
        st.error("DB 연결 실패")
        return None, None, None
    
    erec_df = pd.read_sql("SELECT * FROM Hull_erec_baseMH", engine)
    info_df = pd.read_sql("SELECT * FROM Hull_info", engine)
    r99_df = pd.read_sql("SELECT * FROM R99_rate", engine)
    
    return erec_df, info_df, r99_df
```

#### 4.2 데이터 타입 확인 & 변환
```python
# DB에서 로드한 후 데이터 타입 확인
def validate_data(erec_df, info_df, r99_df):
    """DB 데이터의 타입/값 범위 검증"""
    
    # stage는 숫자여야 함
    if not pd.api.types.is_numeric_dtype(erec_df['stage']):
        erec_df['stage'] = erec_df['stage'].astype(int)
    
    # 기준공수는 음수가 아니어야 함
    assert (erec_df['total_기준'] >= 0).all(), "음수 기준공수 발견"
    
    # R99율은 -1 ~ 1 범위
    assert (r99_df['R99율'].between(-1, 1)).all(), "범위 밖 R99율 발견"
    
    st.success("✅ 데이터 검증 통과")
    return erec_df, info_df, r99_df

# 사용
erec_df, info_df, r99_df = load_data()
if erec_df is not None:
    erec_df, info_df, r99_df = validate_data(erec_df, info_df, r99_df)
```

---

## ⚠️ 주의사항 및 트러블슈팅

### 1. 연결 타임아웃
```python
# ❌ 기본 타임아웃 (30초) → 느린 네트워크에서 실패
engine = create_engine(connection_string)

# ✅ 연결 타임아웃 연장 (SQL Server)
engine = create_engine(
    connection_string,
    connect_args={'timeout': 120}  # 120초
)

# ✅ 연결 풀 설정
engine = create_engine(
    connection_string,
    pool_size=5,
    max_overflow=10,  # 추가 연결 최대 10개
    pool_recycle=3600  # 1시간마다 연결 재생성
)
```

### 2. 인코딩 문제 (한글)
```python
# ❌ 한글이 깨지는 경우
df = pd.read_sql("SELECT * FROM Hull_info", engine)

# ✅ 해결책 (SQL Server)
# DB 쪽에서 컬럼 인코딩 확인: COLLATE Korean_Wansung_CI_AS 등
# 또는 SQLAlchemy 레벨에서 처리
```

### 3. 권한 부족
```
오류: "Cannot open database ... Login failed"
→ 계정에 해당 데이터베이스 읽기 권한 확인
→ DB 담관자에게 SELECT 권한 요청
```

### 4. 성능 저하
```
증상: 필터 선택이 느림 (5초 이상)
원인: DB 쿼리 느림 또는 네트워크 지연
해결:
  1. 인덱스 추가 (DB 담당자)
  2. 캐싱 TTL 단축 (ttl=600)
  3. 필터 조건을 쿼리에 푸시다운
  4. 데이터 샘플링 (개발용)
```

---

## 🚀 배포 및 보안

### Streamlit Cloud 배포
```bash
# 1. GitHub에 코드 푸시 (secrets.toml 제외!)
git add .
git commit -m "Hull dashboard with DB connection"
git push origin main

# 2. Streamlit Cloud (https://share.streamlit.io/)에서 앱 배포
#    - GitHub 저장소 선택
#    - Secrets 탭에서 환경변수 설정

# 3. .streamlit/secrets.toml 예시
# [database]
# server = "..."
# username = "..."
# password = "..."
```

### Docker 배포 (로컬)
```dockerfile
# Dockerfile
FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "hull_dashboard.py"]
```

```bash
# 빌드 및 실행
docker build -t hull-dashboard .
docker run -p 8501:8501 \
  -e STREAMLIT_SERVER_PORT=8501 \
  -e STREAMLIT_SERVER_HEADLESS=true \
  hull-dashboard
```

### 보안 체크리스트
```
[ ] 데이터베이스 비밀번호를 코드에 하드코딩하지 않음
    → .streamlit/secrets.toml 또는 환경변수 사용
[ ] VPN 연결 필수 (회사 네트워크)
[ ] HTTPS 강제 (Streamlit Cloud 자동 지원)
[ ] 사용자 인증 (SSO/AD 연동 권장)
[ ] 감사 로깅 (누가 언제 어떤 데이터를 봤는지 기록)
[ ] 데이터 마스킹 (민감한 컬럼 제한)
```

---

## 📊 단계별 작업 로드맵

### Week 1: 준비
- [ ] DB 정보 수집 (서버, 포트, 계정, 스키마)
- [ ] 네트워크 연결 테스트
- [ ] 드라이버 설치

### Week 2: 개발
- [ ] 연결 코드 작성 및 테스트
- [ ] 쿼리 최적화
- [ ] 데이터 검증

### Week 3: 통합
- [ ] hull_dashboard.py 수정 (CSV → DB)
- [ ] 전체 기능 테스트
- [ ] 성능 측정

### Week 4: 배포
- [ ] 환경 구성 (secrets.toml, Docker 등)
- [ ] UAT (사용자 승인 테스트)
- [ ] 프로덕션 배포

---

## 📞 문의 및 연락처

**DB 연결 관련 질문:**
1. 기술 상세: TECHNICAL_DETAILS.md 참고
2. SQL 최적화: DBA 팀과 협업
3. Streamlit 사용법: README.md 참고

**예상 완료 기간:** 4주 (병렬 진행 시 2주)

---

**마지막 업데이트**: 2024년  
**상태**: 준비 완료 (DB 연결 대기)
