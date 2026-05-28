"""AI 파이프라인 실행/이력 조회 API"""

from fastapi import APIRouter, Query

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
2. pipeline_run_log 테이블에 running 상태 기록
3. 원본 데이터를 raw Parquet 파일로 저장
4. 전처리 데이터를 preprocessed Parquet 파일로 저장
5. AI 이상 점수 계산
6. AI 결과를 result Parquet 파일로 저장
7. anomaly_score 테이블에 결과 저장
8. 오래된 preprocessed 데이터 자동 삭제
9. pipeline_run_log 테이블을 success 또는 error 상태로 업데이트

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


@router.get(
    "/runs/latest",
    summary="Get Latest Pipeline Run",
    description="""
가장 최근에 실행된 AI 파이프라인 이력 1건을 조회한다.

이 API는 운영자 또는 개발자가 아래 내용을 확인할 때 사용한다.

- 마지막 AI 파이프라인이 언제 실행됐는지
- 성공했는지 실패했는지
- 어떤 ESS와 날짜 데이터를 처리했는지
- 몇 건의 배터리 데이터를 수집했는지
- 몇 건의 AI 결과를 저장했는지
- Parquet 파일이 어디에 저장됐는지
- 실패했다면 에러 메시지가 무엇인지
""",
)
async def get_latest_pipeline_run():
    """최신 파이프라인 실행 이력 조회"""
    db_local_service = container.db_local_service()
    run = await db_local_service.find_latest_pipeline_run()

    if run is None:
        return {
            "status": "empty",
            "message": "No pipeline run history found.",
            "result": None,
        }

    return {
        "status": "success",
        "message": "Latest pipeline run retrieved successfully.",
        "result": run,
    }


@router.get(
    "/runs",
    summary="Get Recent Pipeline Runs",
    description="""
최근 AI 파이프라인 실행 이력 목록을 조회한다.

기본적으로 최근 20건을 조회한다.
limit 값을 조정하여 조회 개수를 변경할 수 있다.

예:
- GET /api/v1/pipeline/runs
- GET /api/v1/pipeline/runs?limit=10
- GET /api/v1/pipeline/runs?limit=50
""",
)
async def get_recent_pipeline_runs(
        limit: int = Query(
            default=20,
            ge=1,
            le=100,
            description="조회할 최근 실행 이력 개수. 최소 1, 최대 100",
        )
):
    """최근 파이프라인 실행 이력 목록 조회"""
    db_local_service = container.db_local_service()
    runs = await db_local_service.find_recent_pipeline_runs(limit=limit)

    return {
        "status": "success",
        "count": len(runs),
        "message": "Recent pipeline runs retrieved successfully.",
        "results": runs,
    }