"""AI 이상 점수 조회 API"""

from fastapi import APIRouter

from core.container import container


router = APIRouter(
    prefix="/api/v1/anomaly-scores",
    tags=["Anomaly Scores"],
)


@router.get("/latest")
async def get_latest_anomaly_scores():
    """
    가장 최근에 저장된 AI 이상 점수 결과를 조회한다.

    관제시스템은 이 API를 호출해서 최신 AI 분석 결과를 가져간다.
    """
    db_local_service = container.db_local_service()
    scores = await db_local_service.find_latest_anomaly_scores()

    latest_inserted = None
    latest_date = None

    if scores:
        latest_inserted = scores[0].get("inserted")
        latest_date = scores[0].get("date")

    return {
        "status": "success",
        "count": len(scores),
        "latest_date": latest_date,
        "latest_inserted": latest_inserted,
        "message": "Latest AI anomaly scores retrieved successfully.",
        "results": scores,
    }