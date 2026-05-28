"""AI 이상 점수 조회 API"""

from datetime import date

from fastapi import APIRouter, Query

from core.container import container


router = APIRouter(
    prefix="/api/v1/anomaly-scores",
    tags=["Anomaly Scores"],
)


@router.get(
    "/latest",
    summary="Get Latest Anomaly Scores",
    description="""
가장 최근에 저장된 AI 이상 점수 결과를 조회한다.

관제시스템은 이 API를 호출해서 최신 AI 분석 결과를 가져간다.
""",
)
async def get_latest_anomaly_scores():
    """최신 이상 점수 조회"""
    db_local_service = container.db_local_service()
    scores = await db_local_service.find_latest_anomaly_scores()

    if not scores:
        return {
            "status": "empty",
            "count": 0,
            "latest_date": None,
            "latest_inserted": None,
            "message": "No anomaly scores found.",
            "results": [],
        }

    latest_date = scores[0].get("date")
    latest_inserted = scores[0].get("inserted")

    return {
        "status": "success",
        "count": len(scores),
        "latest_date": latest_date,
        "latest_inserted": latest_inserted,
        "message": "Latest AI anomaly scores retrieved successfully.",
        "results": scores,
    }


@router.get(
    "",
    summary="Get Anomaly Scores By Date",
    description="""
특정 날짜의 AI 이상 점수 결과를 조회한다.

같은 날짜에 AI 파이프라인을 여러 번 실행한 경우,
해당 날짜의 가장 최근 실행 결과만 반환한다.

예:
- GET /api/v1/anomaly-scores?date=2026-05-27
""",
)
async def get_anomaly_scores_by_date(
        target_date: date = Query(
            alias="date",
            description="조회할 분석 대상 날짜. 예: 2026-05-27",
        )
):
    """날짜별 이상 점수 조회"""
    db_local_service = container.db_local_service()
    scores = await db_local_service.find_anomaly_scores_by_date(target_date)

    if not scores:
        return {
            "status": "empty",
            "count": 0,
            "target_date": target_date.isoformat(),
            "latest_inserted": None,
            "message": "No anomaly scores found for requested date.",
            "results": [],
        }

    latest_inserted = scores[0].get("inserted")

    return {
        "status": "success",
        "count": len(scores),
        "target_date": target_date.isoformat(),
        "latest_inserted": latest_inserted,
        "message": "AI anomaly scores by date retrieved successfully.",
        "results": scores,
    }