"""AI 파이프라인 수동 실행 API"""

from fastapi import APIRouter

from core.container import container


router = APIRouter(
    prefix="/api/v1/pipeline",
    tags=["Pipeline"],
)


@router.post("/run")
async def run_pipeline_once():
    """
    AI 파이프라인을 수동으로 1회 실행한다.

    실행 순서:
    1. battery 테이블에서 오늘 날짜 데이터 조회
    2. Rack별 Parquet 파일 저장
    3. AI 이상 점수 계산
    4. anomaly_score 테이블에 결과 저장
    """
    scheduler_service = container.scheduler_service()
    result = await scheduler_service.run_once()

    return result