"""AI 파이프라인 실행 API"""

from fastapi import APIRouter

from core.container import container


router = APIRouter(
    prefix="/api/v1/pipeline",
    tags=["Pipeline"],
)


@router.post(
    "/run",
    summary="Run Pipeline Once",
    description="""
AI 파이프라인을 수동으로 1회 실행한다.

이 API는 개발 및 테스트용이다.
운영 환경에서는 스케줄러가 매일 정해진 시간에 자동으로 실행한다.

실행 순서:

1. 관제시스템 DB에서 대상 날짜 배터리 데이터 조회
2. 원본 데이터를 raw Parquet 파일로 저장
3. 전처리 데이터를 preprocessed Parquet 파일로 저장
4. AI 이상 점수 계산
5. AI 결과를 result Parquet 파일로 저장
6. anomaly_score 테이블에 결과 저장
7. 오래된 preprocessed 데이터 자동 삭제

대상 날짜는 .env의 TARGET_DATE_OFFSET_DAYS 설정을 따른다.

예:
- TARGET_DATE_OFFSET_DAYS=0  → 오늘 데이터 처리
- TARGET_DATE_OFFSET_DAYS=-1 → 전날 데이터 처리

파일 저장 경로:

- files/raw/{ess_id}/{YYYY-MM-DD}/battery_raw.parquet
- files/preprocessed/{ess_id}/{YYYY-MM-DD}/battery_preprocessed.parquet
- files/result/{ess_id}/{YYYY-MM-DD}/anomaly_scores.parquet

주의:
- 이 API는 관제시스템이 상시 호출하는 API가 아니다.
- 관제시스템은 일반적으로 GET /api/v1/anomaly-scores/latest API로 최신 결과만 조회한다.
""",
)
async def run_pipeline_once():
    """AI 파이프라인 수동 실행"""
    scheduler_service = container.scheduler_service()
    return await scheduler_service.run_once()