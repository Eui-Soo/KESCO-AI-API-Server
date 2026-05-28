# KESCO AI API Server

ESS 관제시스템과 AI 모델을 연결하기 위한 **백엔드 AI API 서버**입니다.

이 서버의 목적은 단순합니다.

1. 매일 정해진 시간에 관제시스템 DB에서 하루치 배터리 데이터를 읽어온다.
2. 읽어온 데이터를 전처리하고 AI 모델로 이상 점수를 계산한다.
3. 계산 결과를 우리 AI 결과 DB에 저장한다.
4. 관제시스템이 API로 요청하면 저장된 최신 AI 결과를 JSON으로 반환한다.

현재 저장소는 위 흐름을 개발하기 위한 기본 골격입니다. 아직 실제 AI 모델은 연결 전이며, `ai/ai_process.py`에서는 테스트용 임시 점수를 생성합니다.

---

## 1. 전체 구조

운영 환경에서의 전체 구조는 아래와 같습니다.

```text
┌──────────────────────────────┐
│ 관제시스템 서버               │
│  - 관제 화면                  │
│  - 원본 배터리 데이터 DB       │
│  - 현장 데이터 수집            │
└──────────────┬───────────────┘
               │
               │ ① AI 서버가 하루 1회 원본 데이터 조회
               ▼
┌──────────────────────────────┐
│ KESCO AI API Server           │
│  - 데이터 수집 모듈            │
│  - 전처리 / AI 추론 모듈       │
│  - AI 결과 DB                 │
│  - 결과 조회 API              │
└──────────────┬───────────────┘
               ▲
               │ ② 관제시스템이 결과 요청
               │    GET /api/v1/anomaly-scores/latest
               │
┌──────────────┴───────────────┐
│ 관제시스템 화면               │
│  - Rack별 위험도 표시         │
│  - 정상/주의/경고/위험 표시   │
└──────────────────────────────┘
```

중요한 점은 **관제시스템이 매번 AI 모델을 직접 실행하는 구조가 아니라는 것**입니다.

AI 서버가 매일 자동으로 모델을 실행하여 결과를 미리 저장해두고, 관제시스템은 필요한 시점에 저장된 결과만 조회합니다.

---

## 2. 현재 개발 상태

현재까지 구현된 기능은 아래와 같습니다.

| 구분            |     상태 | 설명                                    |
| ------------- | -----: | ------------------------------------- |
| FastAPI 서버 실행 |     완료 | `python main.py`로 서버 실행               |
| Swagger 문서    |     완료 | `http://localhost:8000/docs`          |
| PostgreSQL 연결 |     완료 | SQLAlchemy + asyncpg 사용               |
| 환경변수 관리       |     완료 | `.env`, `.env.dev`, `.env.example` 구조 |
| 스케줄러          |     완료 | APScheduler 기반 매일 1회 자동 실행            |
| Health API    |     완료 | 서버 상태 확인                              |
| 최신 결과 조회 API  |     완료 | 관제시스템이 최신 AI 결과 조회                    |
| 수동 실행 API     | 개발용 완료 | Swagger에서 테스트 실행 가능                   |
| 실제 AI 모델 연결   |    미완료 | 현재는 random 임시 점수                      |
| 실제 관제 DB 연동   |    미완료 | 현재는 테스트용 battery 테이블 기준               |

---

## 3. 서버가 하는 일

### 3.1 매일 자동 실행되는 작업

스케줄러는 `.env`에 설정된 시간에 하루 한 번 실행됩니다.

```text
관제시스템 DB 접속
    ↓
하루치 배터리 데이터 조회
    ↓
Parquet 파일 저장
    ↓
AI 처리 실행
    ↓
anomaly_score 테이블에 결과 저장
```

현재 스케줄 시간은 `.env`에서 설정합니다.

```env
SCHEDULE_HOUR=0
SCHEDULE_MINUTE=0
SCHEDULE_SECOND=30
```

위 설정은 매일 `00:00:30`에 실행한다는 뜻입니다.

### 3.2 관제시스템이 호출하는 작업

관제시스템은 AI 모델을 직접 실행하지 않고, 최신 결과 조회 API만 호출하면 됩니다.

```text
GET /api/v1/anomaly-scores/latest
```

응답 예시는 아래와 같습니다.

```json
{
  "status": "success",
  "count": 2,
  "latest_date": "2026-05-27",
  "latest_inserted": "2026-05-27T17:05:16.023742",
  "message": "Latest AI anomaly scores retrieved successfully.",
  "results": [
    {
      "id": 5,
      "rack_idx": 1,
      "date": "2026-05-27",
      "inserted": "2026-05-27T17:05:16.023742",
      "updated": "2026-05-27T17:05:16.023742",
      "score_max": 94.4,
      "score_avg": 44.87,
      "max_cell": "c10",
      "risk_level": "danger",
      "risk_label": "위험",
      "cell_scores": {
        "c1": 44.05,
        "c2": 84.11,
        "c3": 16.62
      }
    }
  ]
}
```

---

## 4. API 목록

### 4.1 Health Check

```http
GET /api/v1/health
```

서버가 정상 실행 중인지 확인합니다.

응답 예시:

```json
{
  "status": "ok",
  "app_name": "KESCO-DigitalTwin",
  "app_version": "1.0.0",
  "message": "KESCO DigitalTwin AI API server is running."
}
```

### 4.2 최신 AI 결과 조회

```http
GET /api/v1/anomaly-scores/latest
```

관제시스템이 사용할 주요 API입니다. 우리 AI 결과 DB에 저장된 가장 최신 분석 결과를 반환합니다.

결과에는 Rack별 대표 점수와 셀별 점수가 포함됩니다.

| 필드                | 설명                   |
| ----------------- | -------------------- |
| `latest_date`     | 분석 대상 데이터 날짜         |
| `latest_inserted` | AI 결과가 DB에 저장된 시간    |
| `rack_idx`        | Rack 번호              |
| `score_max`       | 해당 Rack에서 가장 높은 셀 점수 |
| `score_avg`       | 해당 Rack의 평균 셀 점수     |
| `max_cell`        | 가장 위험 점수가 높은 셀       |
| `risk_level`      | 영어 위험 등급             |
| `risk_label`      | 한글 위험 등급             |
| `cell_scores`     | 셀별 점수                |

### 4.3 수동 파이프라인 실행

```http
POST /api/v1/pipeline/run
```

개발 및 테스트용 API입니다.

운영에서 관제시스템이 이 API를 호출하는 구조는 권장하지 않습니다. 운영에서는 스케줄러가 자동으로 AI 처리를 실행하고, 관제시스템은 `/latest` API만 호출하는 구조가 기본입니다.

---

## 5. 위험 등급 기준

현재 위험 등급은 `score_max` 기준으로 계산합니다.

|        점수 범위 | risk_level | risk_label |
| -----------: | ---------- | ---------- |
|   0 이상 30 미만 | `normal`   | 정상         |
|  30 이상 60 미만 | `caution`  | 주의         |
|  60 이상 80 미만 | `warning`  | 경고         |
| 80 이상 100 이하 | `danger`   | 위험         |

현재 DB에는 셀별 점수가 `0.0 ~ 1.0` 형태로 저장됩니다. API 응답에서는 관제시스템에서 보기 쉽도록 `0 ~ 100` 점수로 변환해서 반환합니다.

---

## 6. 프로젝트 구조

```text
KESCO-AI-API-Server/
│
├── main.py                         # FastAPI 앱 진입점
├── requirements.txt                # Python 패키지 목록
├── .env.example                    # 환경변수 예시 파일
├── .gitignore                      # Git 제외 파일 설정
│
├── router/                         # API 라우터
│   ├── health_router.py             # /api/v1/health
│   ├── anomaly_router.py            # /api/v1/anomaly-scores/latest
│   └── pipeline_router.py           # /api/v1/pipeline/run
│
├── service/                        # 서비스 계층
│   ├── schedule_service.py          # 매일 자동 실행 스케줄러
│   ├── ai_service.py                # AI 처리 서비스 래퍼
│   └── file_service.py              # Parquet 파일 저장
│
├── repo/                           # DB 접근 계층
│   ├── battery_repo.py              # 관제시스템 DB에서 원본 데이터 조회
│   └── anomaly_repo.py              # AI 결과 저장/조회
│
├── ai/                             # AI 처리 모듈
│   └── ai_process.py                # 현재는 테스트용 임시 점수 생성
│
├── core/                           # 공통 인프라
│   ├── container/                   # 의존성 주입 컨테이너
│   ├── db/                          # DB 연결 서비스
│   ├── model/                       # SQLAlchemy ORM 모델
│   └── setting/                     # 환경설정 로딩
│
└── sql/
    └── db.sql                       # DB 관련 SQL / 샘플 데이터
```

---

## 7. 주요 파일 설명

### `main.py`

FastAPI 서버의 시작점입니다.

서버가 켜질 때 아래 작업을 수행합니다.

1. 서버 정보 출력
2. 로컬 AI 결과 DB 테이블 초기화
3. 스케줄러 시작
4. API 라우터 등록

### `service/schedule_service.py`

매일 정해진 시간에 AI 파이프라인을 실행합니다.

현재 구조는 서버 시작 즉시 AI를 실행하지 않습니다. 서버 시작 시에는 스케줄러만 등록하고, `.env`에 설정된 시간에 자동으로 실행됩니다.

### `repo/battery_repo.py`

관제시스템 DB에서 원본 배터리 데이터를 조회합니다.

현재는 개발용 테스트 테이블 구조를 기준으로 작성되어 있습니다.

```sql
FROM battery
WHERE DATE(inserted) = :target_date
```

운영 전 반드시 실제 관제시스템 DB의 테이블명, 컬럼명, 시간 기준 컬럼에 맞춰 수정해야 합니다.

### `ai/ai_process.py`

AI 처리 함수입니다.

현재는 실제 AI 모델이 아니라 테스트용 random 점수를 생성합니다. 실제 모델 연결 시 이 파일을 중심으로 아래 구조로 확장하는 것을 권장합니다.

```text
ai/
├── ai_process.py
├── model_loader.py
├── preprocess.py
├── inference.py
└── postprocess.py
```

### `repo/anomaly_repo.py`

AI 결과 DB의 `anomaly_score` 테이블을 조회하고, 관제시스템이 보기 좋은 JSON 형태로 변환합니다.

---

## 8. 설치 방법

### 8.1 Python 환경 생성

현재 개발 기준은 Python 3.8입니다.

```bash
conda create -n kesco_api python=3.8 -y
conda activate kesco_api
```

### 8.2 패키지 설치

현재 `requirements.txt`에는 API 서버 패키지와 AI 관련 패키지가 같이 들어 있습니다. 실제 설치 시 AI 패키지에서 문제가 생길 수 있으므로, 개발 초기에는 아래처럼 API 서버에 필요한 패키지부터 설치하는 것을 권장합니다.

```bash
python -m pip install --upgrade pip

pip install "fastapi[standard]==0.115.5" "uvicorn[standard]==0.32.0" sqlalchemy==2.0.34 asyncpg==0.29.0 dependency-injector apscheduler pydantic-settings

pip install pandas==1.3.5 pyarrow==6.0.1 numpy==1.19.5
```

실제 AI 모델 연결 단계에서는 모델 환경에 맞춰 TensorFlow, Keras, scikit-learn 등을 별도로 설치합니다.

---

## 9. PostgreSQL 설정

### 9.1 PostgreSQL 설치 확인

Windows에서 PostgreSQL을 설치한 뒤 아래 명령어로 확인합니다.

```bat
"C:\Program Files\PostgreSQL\16\bin\psql.exe" --version
```

### 9.2 DB 사용자 및 DB 생성

PostgreSQL에 `postgres` 계정으로 접속합니다.

```bat
"C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres
```

아래 SQL을 실행합니다.

```sql
CREATE USER kesco WITH PASSWORD 'kesco';
CREATE DATABASE kesco_digitaltwin OWNER kesco;
GRANT ALL PRIVILEGES ON DATABASE kesco_digitaltwin TO kesco;
```

개발 환경에서는 위처럼 단순한 계정을 써도 되지만, 운영 환경에서는 반드시 강한 비밀번호와 제한된 권한을 사용해야 합니다.

---

## 10. 환경변수 설정

실제 `.env`와 `.env.dev`는 Git에 올리지 않습니다. 대신 `.env.example`을 참고해서 로컬에 직접 만듭니다.

```bash
cp .env.example .env
```

Windows CMD에서는 직접 복사합니다.

```bat
copy .env.example .env
```

주요 환경변수는 아래와 같습니다.

```env
# Application
APP_NAME=KESCO-DigitalTwin
APP_VERSION=1.0.0
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=false

# Scheduler
SCHEDULE_HOUR=0
SCHEDULE_MINUTE=0
SCHEDULE_SECOND=30

# Database - AI result DB
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kesco_digitaltwin
DB_USER=your_db_user
DB_PASSWORD=your_db_password

# Remote Database - monitoring system source DB
DB_REMOTE_HOST=monitoring_db_host
DB_REMOTE_PORT=5432
DB_REMOTE_NAME=monitoring_db_name
DB_REMOTE_USER=readonly_user
DB_REMOTE_PASSWORD=readonly_password
```

### DB 설정 개념

이 프로젝트에서는 DB 접속 정보가 두 묶음입니다.

| 설정            | 의미              |
| ------------- | --------------- |
| `DB_*`        | 우리 AI 결과 DB     |
| `DB_REMOTE_*` | 관제시스템 원본 데이터 DB |

운영 기준으로 우리 쪽에서 관리하는 DB는 **AI 결과 DB 1개**입니다. 다만 원본 데이터를 읽기 위해 관제시스템 DB에도 접속해야 하므로 설정이 두 묶음으로 나뉘어 있습니다.

---

## 11. 서버 실행

```bash
python main.py
```

정상 실행 시 터미널에 아래와 비슷한 출력이 나옵니다.

```text
▶ uvicorn 서버 실행 준비 중...
======================================================================
🚀 KESCO-DigitalTwin 서버 시작
📌 Version : 1.0.0
🌐 Host    : 0.0.0.0
🔌 Port    : 8000
📄 Swagger : http://localhost:8000/docs
======================================================================
🗄️  로컬 DB 테이블 초기화 중...
✅ 로컬 DB 테이블 초기화 완료
⏰ 스케줄러 시작 중...
✅ 스케줄러 시작 완료
✅ 서버 준비 완료. 브라우저에서 Swagger를 열어 확인하세요.
👉 http://localhost:8000/docs
```

서버 실행 후 브라우저에서 접속합니다.

```text
http://localhost:8000/docs
```

---

## 12. 개발 테스트 흐름

처음 개발할 때는 실제 관제시스템 DB가 없을 수 있습니다. 이 경우 로컬 DB의 `battery` 테이블을 임시 원본 DB처럼 사용해서 테스트할 수 있습니다.

테스트 흐름은 아래와 같습니다.

```text
1. PostgreSQL 실행
2. kesco_digitaltwin DB 생성
3. battery 테이블에 샘플 데이터 입력
4. python main.py 실행
5. Swagger 접속
6. POST /api/v1/pipeline/run 실행
7. GET /api/v1/anomaly-scores/latest 확인
```

현재 `POST /api/v1/pipeline/run`은 개발자 테스트용입니다. 운영에서 관제시스템이 이 API를 호출할 필요는 없습니다.

---

## 13. 실제 관제시스템 DB 연동 시 필요한 정보

운영 연동 전 관제시스템 개발팀에게 아래 정보를 받아야 합니다.

1. 원본 배터리 데이터 테이블명
2. 측정 시간 컬럼명
3. DB 저장 시간 컬럼명
4. Rack 번호 컬럼명
5. Cell 전압 컬럼명 목록
6. 하루치 데이터를 조회할 기준 시간
7. 예시 데이터 5~10행
8. DB 접속 주소, 포트, DB명, 읽기 전용 계정

현재 `battery_repo.py`는 테스트용으로 아래 컬럼명을 가정합니다.

```text
battery
- id
- total_racks
- index
- cv_1 ~ cv_20
- date
- inserted
```

실제 관제시스템 DB가 이 구조와 다르면 `repo/battery_repo.py`를 수정해야 합니다.

특히 현재 조회 조건은 `DATE(inserted) = :target_date`입니다. 운영에서는 `inserted`가 아니라 실제 측정 시간 컬럼을 기준으로 조회해야 할 수 있습니다.

---

## 14. 실제 AI 모델 연결 시 수정할 부분

현재 `ai/ai_process.py`는 테스트용 random 점수를 생성합니다.

실제 AI 모델을 연결할 때는 아래 구조를 권장합니다.

```text
ai/
├── model_loader.py      # 서버 시작 시 모델 1회 로딩
├── preprocess.py        # DB 원본 데이터를 모델 입력 형태로 변환
├── inference.py         # 모델 추론 실행
├── postprocess.py       # 모델 출력값을 anomaly_score 형태로 변환
└── ai_process.py        # 전체 처리 흐름 연결
```

중요한 원칙은 아래와 같습니다.

1. 모델은 요청마다 로딩하지 않는다.
2. 서버 시작 시 1회만 로딩한다.
3. 추론 시에는 이미 로딩된 모델 객체를 재사용한다.
4. 전처리, 추론, 후처리를 분리한다.
5. 모델 버전 정보를 결과에 남길 수 있도록 준비한다.

---

## 15. 운영 전 점검 사항

운영 반영 전 아래 항목을 확인해야 합니다.

| 항목        | 확인 내용                      |
| --------- | -------------------------- |
| 관제 DB 연결  | `DB_REMOTE_*` 설정으로 접속 가능한지 |
| 원본 데이터 조회 | 하루치 데이터가 정확히 조회되는지         |
| 시간 기준     | 오늘 데이터인지 전날 데이터인지 확정       |
| AI 모델     | random 점수가 아닌 실제 모델 추론인지   |
| 결과 DB     | `anomaly_score` 저장이 정상인지   |
| API 응답    | 관제시스템이 JSON을 정상 파싱하는지      |
| 스케줄 시간    | 현장 운영 시간과 맞는지              |
| 보안        | `.env`가 GitHub에 올라가지 않는지   |
| 로그        | 장애 발생 시 원인 추적 가능한지         |

---

## 16. 현재 한계와 다음 개발 과제

현재 저장소는 API 서버와 DB 연동 골격을 검증한 상태입니다. 다음 과제가 남아 있습니다.

### 16.1 requirements 분리

현재 `requirements.txt`에는 API 서버 패키지와 AI 패키지가 섞여 있습니다. 추천 구조는 아래와 같습니다.

```text
requirements-api.txt
requirements-ai.txt
```

### 16.2 실제 관제 DB 구조 반영

`repo/battery_repo.py`를 실제 관제시스템 DB 컬럼명에 맞게 수정해야 합니다.

### 16.3 실제 AI 모델 연결

`ai/ai_process.py`의 random 점수를 실제 AI 모델 추론으로 교체해야 합니다.

### 16.4 실행 이력 관리

현재 최신 결과 조회는 `inserted`의 최대값 기준입니다. 운영 안정성을 높이려면 `pipeline_run_id`를 추가해 실행 단위로 결과를 묶는 구조가 좋습니다.

### 16.5 분석 날짜 정책 확정

매일 00:00:30에 실행한다면 당일 데이터가 아니라 전날 데이터를 처리해야 할 수 있습니다. 운영 전 아래 정책을 확정해야 합니다.

```text
스케줄 실행 시 처리할 날짜 = 오늘? 전날?
```

---

## 17. Git 사용 흐름

코드를 수정한 뒤에는 아래 순서로 GitHub에 반영합니다.

```bash
git status
git add .
git commit -m "작업 내용"
git push
```

`.env`, `.env.dev`는 `.gitignore`에 의해 제외되어야 합니다. 실제 비밀번호가 들어간 파일은 GitHub에 올리지 않습니다.

---

## 18. 요약

이 서버는 ESS 관제시스템에 AI 모델을 붙이기 위한 중간 서버입니다.

핵심 흐름은 아래와 같습니다.

```text
관제시스템 DB 원본 데이터
    ↓
AI 서버가 매일 1회 조회
    ↓
AI 모델 추론
    ↓
우리 AI 결과 DB 저장
    ↓
관제시스템이 최신 결과 API 호출
    ↓
Rack별 위험도 JSON 응답
```

현재는 API 서버 골격, DB 저장, 최신 결과 조회, 스케줄러까지 구현되어 있습니다. 다음 핵심 작업은 실제 관제시스템 DB 구조 반영과 실제 AI 모델 연결입니다.
