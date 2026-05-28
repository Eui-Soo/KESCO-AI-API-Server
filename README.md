# KERI Digital Twin

**전기안전연구원(KERI)** × **로보볼트(Robovolt)** 공동 개발

ESS(배터리 에너지 저장 시스템)의 배터리 데이터를 매일 자동 수집하고, AI로 이상치를 탐지하여 로컬 DB에 저장하는 백엔드 서버입니다.

---

## 목차

1. [시스템 개요](#1-시스템-개요)
2. [사전 준비](#2-사전-준비)
3. [설치](#3-설치)
4. [데이터베이스 설정](#4-데이터베이스-설정)
5. [환경 설정](#5-환경-설정)
6. [실행](#6-실행)
7. [프로젝트 구조](#7-프로젝트-구조)
8. [동작 방식](#8-동작-방식)
9. [주요 파일 설명](#9-주요-파일-설명)
10. [로그 확인](#10-로그-확인)
11. [프로덕션 전환](#11-프로덕션-전환)
12. [트러블슈팅](#12-트러블슈팅)

---

## 1. 시스템 개요

### 무슨 일을 하는가?

매일 자정 자동으로 아래 3단계 파이프라인이 실행됩니다.

```
[1단계] 원격 DB에서 당일 배터리 데이터 수집
    ↓
[2단계] Parquet 파일로 저장 (files/YYYY-MM-DD/NN/Rack_NN.parquet)
    ↓
[3단계] AI 이상치 점수(anomaly_score) 계산 → 로컬 DB에 저장
```

### 기술 스택

| 분류 | 기술 |
|------|------|
| 웹 프레임워크 | FastAPI + Uvicorn |
| 데이터베이스 | PostgreSQL (SQLAlchemy 2.0, asyncpg) |
| 스케줄러 | APScheduler |
| 데이터 저장 | pandas + pyarrow (Parquet) |
| 설정 관리 | Pydantic V2 (BaseSettings) |
| 의존성 주입 | dependency-injector |

---

## 2. 사전 준비

아래가 설치되어 있어야 합니다.

- **Python 3.8+**
- **PostgreSQL 13+** (로컬 및 원격 DB 모두 필요)
- **Conda** (권장) 또는 pip

---

## 3. 설치

### Conda 사용 (권장)

```bash
# 환경 생성
conda env create -f environment.yml

# 환경 활성화
conda activate KERI-DigitalTwin
```

### pip 사용

```bash
pip install -r requirements.txt
```

또는 항목별로 직접 설치:

```bash
# AI (Python 3.8 + CUDA 환경 필수)
pip install tensorflow-gpu==2.5.0
pip install keras==2.6.0
pip install numpy==1.19.5
pip install pandas==1.3.5
pip install pyarrow==6.0.1
pip install scipy==1.10.1
pip install scikit-learn==1.0.2
pip install matplotlib==3.5.3
pip install Pillow==9.5.0
pip install tensorflow-addons==0.13.0
pip install typeguard==2.13.3

# 웹 프레임워크
pip install fastapi[standard]==0.115.5
pip install uvicorn[standard]==0.32.0

# 데이터베이스 & ORM
pip install sqlalchemy==2.0.34
pip install asyncpg==0.29.0
# pip install psycopg2-binary  # 동기 드라이버가 필요한 경우

# 유틸리티
pip install dependency-injector
pip install apscheduler
pip install typing-extensions==4.11.0
```

> **주의**: `tensorflow-gpu==2.5.0`은 **Python 3.8** + **CUDA 11.2** + **cuDNN 8.1** 조합에서만 정상 동작합니다.

---

## 4. 데이터베이스 설정

### 로컬 DB 초기화

PostgreSQL에 접속하여 아래 SQL을 실행합니다.

```sql
-- 사용자 및 데이터베이스 생성
CREATE USER keri WITH PASSWORD 'keri';
CREATE DATABASE keri_digitaltwin OWNER keri;
GRANT ALL PRIVILEGES ON DATABASE keri_digitaltwin TO keri;
```

> 파일 위치: `sql/db.sql`

테이블(`anomaly_score`)은 **서버 최초 실행 시 자동 생성**됩니다. 별도 마이그레이션 불필요합니다.

### 원격 DB 설정

원격 DB는 **배터리 데이터(`battery` 테이블)가 이미 있는 DB**입니다.
서버가 읽기 전용으로 접근하므로, 연결 정보만 `.env`에 입력하면 됩니다.

개발·테스트 시 원격 DB가 없다면 로컬 DB 동일 서버를 사용하고 `sql/db.sql`의 `INSERT` 쿼리로 샘플 데이터를 삽입할 수 있습니다.

```sql
-- sql/db.sql 내 샘플 데이터 삽입 쿼리 (오늘 날짜 기준 Rack 4개, 1시간 간격 96건)
-- battery 테이블에 테스트 데이터가 필요할 때 실행
```

### DB 구조 요약

**로컬 DB** (`keri_digitaltwin`)

| 테이블 | 설명 |
|--------|------|
| `anomaly_score` | AI가 계산한 Rack별 이상치 점수 (sc_c1~sc_c20) |

**원격 DB** (읽기 전용)

| 테이블 | 설명 |
|--------|------|
| `battery` | 현장에서 수집된 배터리 셀 전압 데이터 (cv_1~cv_20) |

---

## 5. 환경 설정

### 파일 설명

| 파일 | 용도 |
|------|------|
| `.env.dev` | 개발 환경 설정 (로컬 테스트용) |
| `.env` | 프로덕션 설정 (이 파일이 `.env.dev`보다 우선 적용) |

### 개발 환경 시작

```bash
# .env.dev를 복사하여 .env로 사용
cp .env.dev .env

# 필요하면 .env의 DB 접속 정보를 실제 환경에 맞게 수정
```

### 환경변수 전체 목록

```bash
# ─── 앱 기본 ─────────────────────────────────────────────────
APP_NAME=KERI-DigitalTwin
APP_VERSION=1.0.0
APP_HOST=0.0.0.0        # 서버 바인딩 주소 (0.0.0.0 = 모든 IP 허용)
APP_PORT=8000

# ─── 디버그 / 로그 ────────────────────────────────────────────
DEBUG=false             # true: 콘솔 로그 출력 + SQL 쿼리 출력
LOG_DIR=log             # 로그 디렉토리 (자동 생성)
LOG_BACKUP_DAYS=60      # 로그 보관 일수 (이후 자동 삭제)

# ─── 파일 저장 ────────────────────────────────────────────────
FILES_DIR=files         # Parquet 저장 디렉토리 (자동 생성)

# ─── 로컬 DB ─────────────────────────────────────────────────
DB_HOST=localhost
DB_PORT=5432
DB_NAME=keri_digitaltwin
DB_USER=keri
DB_PASSWORD=keri
DB_POOL_SIZE=5          # 연결 풀 크기
DB_MAX_OVERFLOW=10      # 풀 초과 허용 연결 수
DB_POOL_TIMEOUT=30      # 연결 대기 시간(초)
DB_POOL_RECYCLE=1800    # 연결 재활용 주기(초, 기본 30분)
DB_ECHO=false           # true: SQL 쿼리 로그 출력

# ─── 원격 DB ─────────────────────────────────────────────────
# 매 조회마다 연결/종료(NullPool) - 원격 서버 부하 최소화
DB_REMOTE_HOST=원격서버주소
DB_REMOTE_PORT=5432
DB_REMOTE_NAME=배터리DB이름
DB_REMOTE_USER=사용자명
DB_REMOTE_PASSWORD=비밀번호
```

---

## 6. 실행

```bash
# 실행
python main.py
```

정상 실행 시 로그에 아래와 같이 출력됩니다.

```
[2026-02-27 00:00:00] [INFO] ▶ KERI-DigitalTwin 시작 (v1.0.0)
[2026-02-27 00:00:00] [INFO] ✅ SchedulerService 초기화 완료
[2026-02-27 00:00:00] [INFO] ⏰ 스케줄러 시작 (매일 자정 실행)
[2026-02-27 00:00:00] [INFO] 🚀 일일 파이프라인 시작 [2026-02-27]
[2026-02-27 00:00:00] [INFO] 📥 [1/3] 배터리 데이터 수집
[2026-02-27 00:00:00] [INFO] 💾 [2/3] Parquet 파일 저장
[2026-02-27 00:00:00] [INFO] 🤖 [3/3] AI 처리 (anomaly_score 계산)
[2026-02-27 00:00:00] [INFO] ✅ 일일 파이프라인 완료 [2026-02-27]
```

### API 문서 확인

서버 실행 후 브라우저에서 접속합니다.

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 7. 프로젝트 구조

```
KERI-DigitalTwin/
│
├── main.py                        # FastAPI 앱 진입점 (startup/shutdown)
├── .env                           # 프로덕션 환경 설정 (git 제외)
├── .env.dev                       # 개발 환경 설정
├── environment.yml                # Conda 환경 정의
├── requirements.txt               # pip 패키지 목록
│
├── core/                          # 핵심 인프라
│   ├── container/
│   │   └── container.py           # 의존성 주입(DI) 컨테이너 - 싱글톤 관리
│   ├── db/
│   │   ├── db_service.py          # 로컬 DB (테이블 생성, anomaly_score 저장)
│   │   └── db_remote_service.py   # 원격 DB (배터리 데이터 조회)
│   ├── log/
│   │   └── config.py              # 로깅 설정 (파일 로테이션)
│   ├── model/
│   │   └── models.py              # SQLAlchemy ORM 모델 (AnomalyScore, BAT)
│   └── setting/
│       └── settings.py            # 환경변수 → Pydantic 설정 (타입 검증)
│
├── service/                       # 비즈니스 로직
│   ├── schedule_service.py        # 일일 파이프라인 스케줄러 (핵심)
│   ├── file_service.py            # Parquet 파일 저장
│   └── ai_service.py              # AI 이상치 계산 서비스 (래퍼)
│
├── ai/
│   └── ai_process.py              # 실제 이상치 알고리즘 ← 여기를 구현해야 함
│
├── repo/                          # DB 접근 계층
│   ├── anomaly_repo.py            # anomaly_score 테이블 bulk insert
│   └── battery_repo.py            # battery 테이블 조회
│
├── sql/
│   └── db.sql                     # DB 초기화 SQL + 샘플 데이터
│
├── log/                           # 로그 파일 (자동 생성)
│   └── app.log
│
└── files/                         # Parquet 저장 위치 (자동 생성)
    └── YYYY-MM-DD/
        └── NN/
            └── Rack_NN.parquet
```

---

## 8. 동작 방식

### 일일 파이프라인

서버가 시작되면 스케줄러가 등록되고, 매일 자정 00:00:30에 아래 3단계가 순서대로 실행됩니다.

```
[1/3] 원격 DB 조회
      └─ battery 테이블에서 당일 데이터 수집
      └─ 반환: List[dict] (cv_1~cv_20, index, date)
         ↓
[2/3] Parquet 파일 저장
      └─ files/YYYY-MM-DD/NN/Rack_NN.parquet 형태로 저장
         ↓
[3/3] AI 이상치 계산 → 로컬 DB 저장
      └─ ai/ai_process.py 함수 호출
      └─ Rack별 sc_c1~sc_c20 점수 계산
      └─ anomaly_score 테이블에 저장
```

이전 파이프라인이 아직 실행 중이면 새 실행은 자동으로 건너뜁니다.

### DB 연결 전략

| DB | 방식 | 이유 |
|----|------|------|
| 로컬 DB | 연결 풀 (pool_size=5) | 빠른 쓰기, 지속적 연결 유지 |
| 원격 DB | NullPool (매 호출마다 연결/종료) | 원격 서버 부하 최소화 |

---

## 9. 주요 파일 설명

### `ai/ai_process.py` — AI 알고리즘 구현 위치

> **현재 상태**: 랜덤값으로 임시 동작 중 (TODO)

실제 이상치 알고리즘을 여기에 구현해야 합니다.

```python
def ai_process(data: List[dict]) -> List[dict]:
    """
    입력: data = [{'index': 1, 'cv_1': 3.7, ..., 'date': date(2026,2,27)}, ...]
    출력: [{'rack_idx': 1, 'sc_c1': 0.12, ..., 'sc_c20': 0.34, 'date': date(...)}, ...]
    """
    # TODO: 평균 cv 기반 실제 anomaly score 알고리즘으로 교체 필요
```

- 입력: 하루치 전체 배터리 데이터 (여러 Rack, 시간별)
- 출력: **Rack당 1개**의 점수 딕셔너리 (sc_c1~sc_c20, 0.0~1.0 권장)
- 함수는 **동기 함수**로 작성하면 됩니다 (비동기 처리는 `ai_service.py`가 담당)

> **주의 — 동기 AI 함수와 비동기 프레임워크 공존**
>
> FastAPI는 비동기(async) 기반으로 동작합니다. `ai_process()`처럼 CPU 연산이 긴 **동기 함수**를
> `await`로 직접 호출하면 이벤트 루프가 블로킹되어 그동안 FastAPI가 **다른 API 요청을 처리하지
> 못하게** 됩니다.
>
> 이를 방지하기 위해 `service/ai_service.py`에서 `run_in_executor`로 별도 스레드에서 실행합니다.
>
> ```python
> # service/ai_service.py - 현재 구현
> loop = asyncio.get_running_loop()
> scores = await loop.run_in_executor(None, ai_process, data)
> #                                   ^^^^  ←────────────────
> #                                   None = 기본 ThreadPoolExecutor 사용
> ```
>
> `run_in_executor`는 동기 함수를 별도 스레드에서 실행하고, 완료될 때까지 이벤트 루프는
> 다른 요청을 계속 처리합니다. 덕분에 AI 연산 시간이 길어도 API 응답성에 영향을 주지 않습니다.
>
> **따라서 `ai_process()` 함수를 구현할 때 `async def`로 바꾸지 말고 일반 `def`를 유지해야 합니다.**

### `service/schedule_service.py` — 스케줄러

파이프라인 실행 순서와 에러 처리를 담당합니다. 비즈니스 로직 변경 시 주로 이 파일을 수정합니다.

### `core/container/container.py` — 의존성 주입

모든 서비스는 여기서 싱글톤으로 관리됩니다. 새 서비스를 추가할 때 여기에 등록합니다.

```python
# 새 서비스 추가 예시
my_service = providers.Singleton(MyService, settings=settings)
```

---

## 10. 로그 확인

로그 파일은 `log/app.log`에 기록되며, 매일 자정 자동으로 `app.log.YYYY-MM-DD` 형태로 백업됩니다.

```bash
# 실시간 로그 확인
tail -f log/app.log

# 오류 로그만 확인
grep "ERROR\|❌" log/app.log

# 파이프라인 실행 기록만 확인
grep "파이프라인" log/app.log
```

---

## 11. 프로덕션 전환

### 스케줄러 설정 변경

현재 개발 편의를 위해 **서버 시작 시 즉시 1회 실행**으로 설정되어 있습니다.
프로덕션 배포 시 `service/schedule_service.py`를 수정해야 합니다.

```python
# ── 현재 (즉시 1회 실행, 개발용) ─────────────────────────────
self._scheduler.add_job(
    self._process,
    trigger='date',         # ← 이 블록을 제거
    id='immediate_pipeline',
    name='즉시 1회 ESS 처리 파이프라인',
)

# ── 프로덕션 (매일 자정 실행) ─────────────────────────────────
# 아래 주석 블록을 활성화 (""" 제거)
self._scheduler.add_job(
    self._process,
    trigger='cron',
    hour=0,
    minute=0,
    second=30,
    max_instances=1,
    misfire_grace_time=3600,
    id='daily_pipeline',
    name='일일 ESS 처리 파이프라인',
)
```

### 환경 변수 체크리스트

프로덕션 `.env` 파일에서 반드시 확인합니다.

- [ ] `APP_HOST=0.0.0.0`
- [ ] `DEBUG=false`
- [ ] `DB_ECHO=false`
- [ ] 로컬 DB 접속 정보 (실제 서버)
- [ ] 원격 DB 접속 정보 (실제 현장 DB)

---

## 12. 트러블슈팅

### 서버 시작 시 테이블이 생성되지 않음

`main.py` 최상단에 아래 import가 반드시 있어야 합니다.

```python
import core.model  # noqa: F401
```

이 줄이 없으면 `AnomalyScore` 모델이 SQLAlchemy에 등록되지 않아 `CREATE TABLE`이 실행되지 않습니다.

### `InvalidRequestError: Autobegin is disabled` 오류

`async_sessionmaker` 생성 시 `autobegin=False` 옵션을 제거합니다.
(기본값 `autobegin=True`를 사용해야 합니다)

```python
# 잘못된 설정
async_sessionmaker(bind=engine, autobegin=False, ...)  # ← autobegin=False 제거

# 올바른 설정
async_sessionmaker(bind=engine, ...)
```

### 원격 DB 연결 실패

원격 DB는 NullPool을 사용하므로 매 실행마다 새로 연결합니다.
`.env`의 `DB_REMOTE_*` 설정과 실제 서버의 방화벽/접근 권한을 확인합니다.

### 로그에 파이프라인 오류 표시

```
[ERROR] ❌ 파이프라인 실행 오류: ...
```

`log/app.log`에서 전체 스택 트레이스를 확인합니다.
대부분 DB 접속 실패 또는 데이터 형식 불일치가 원인입니다.

---

## 문서

| 문서 | 설명 |
|------|------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 상세 아키텍처 및 설계 결정 기록 |
| [CLAUDE.md](CLAUDE.md) | AI 코드 어시스턴트용 개발 가이드 |

---

## 저작권

Copyright (c) 2026 **전기안전연구원(KERI)** × **로보볼트(Robovolt)**

이 프로젝트는 KERI와 Robovolt의 공동 개발 프로젝트입니다.
무단 복제, 배포, 수정을 금지합니다.
