"""로컬 DB 서비스"""

import logging
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)
from sqlalchemy.orm import DeclarativeBase

from core.setting import Settings


logger = logging.getLogger('app')


class Base(DeclarativeBase):
    pass


class DBLocalService:
    """우리 AI 결과 DB 서비스

    담당:
        - 로컬 DB 테이블 생성
        - anomaly_score 저장/조회
        - pipeline_run_log 저장/조회
    """

    def __init__(self, settings: Settings):
        self._engine: AsyncEngine = create_async_engine(
            settings.async_db_url,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_pre_ping=True,
            echo=settings.DB_ECHO,
            future=True,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        logger.info('✅ DBLocalService 초기화 완료')

    async def init_db(self) -> None:
        """DB 테이블 생성"""
        async with self._engine.connect() as conn:
            async with conn.begin():
                await conn.run_sync(Base.metadata.create_all)

        logger.info(f'✅ DB 테이블 생성 완료: {list(Base.metadata.tables.keys())}')

    async def save_anomaly_scores(self, scores: List[dict]) -> int:
        """이상 점수 일괄 등록"""
        if not scores:
            logger.warning('⚠️ 등록할 이상 점수 없음')
            return 0

        async with self._session_factory() as session:
            async with session.begin():
                from repo.anomaly_repo import AnomalyScoreRepository

                repo = AnomalyScoreRepository()
                count = await repo.bulk_insert(session, scores)

        logger.info(f'✅ AnomalyScore 등록 완료: {count}건')
        return count

    async def find_latest_anomaly_scores(self) -> List[dict]:
        """가장 최근에 저장된 이상 점수 조회"""
        async with self._session_factory() as session:
            from repo.anomaly_repo import AnomalyScoreRepository

            repo = AnomalyScoreRepository()
            scores = await repo.find_latest(session)

        logger.info(f'✅ 최신 AnomalyScore 조회 완료: {len(scores)}건')
        return scores

    async def create_pipeline_run(
            self,
            ess_id: str,
            target_date,
            message: Optional[str] = None,
    ) -> int:
        """파이프라인 실행 시작 로그 생성

        Returns:
            생성된 pipeline_run_log.id
        """
        async with self._session_factory() as session:
            async with session.begin():
                from repo.pipeline_run_repo import PipelineRunRepository

                repo = PipelineRunRepository()
                log = await repo.create_running(
                    session=session,
                    ess_id=ess_id,
                    target_date=target_date,
                    message=message,
                )
                run_id = log.id

        logger.info(f'✅ PipelineRunLog 시작 기록 완료: run_id={run_id}')
        return run_id

    async def mark_pipeline_success(
            self,
            run_id: int,
            battery_count: int,
            saved_score_count: int,
            deleted_preprocessed_count: int,
            raw_file_path: Optional[str],
            preprocessed_file_path: Optional[str],
            result_file_path: Optional[str],
            message: Optional[str] = None,
    ) -> None:
        """파이프라인 성공 처리"""
        async with self._session_factory() as session:
            async with session.begin():
                from repo.pipeline_run_repo import PipelineRunRepository

                repo = PipelineRunRepository()
                await repo.mark_success(
                    session=session,
                    run_id=run_id,
                    battery_count=battery_count,
                    saved_score_count=saved_score_count,
                    deleted_preprocessed_count=deleted_preprocessed_count,
                    raw_file_path=raw_file_path,
                    preprocessed_file_path=preprocessed_file_path,
                    result_file_path=result_file_path,
                    message=message,
                )

        logger.info(f'✅ PipelineRunLog 성공 처리 완료: run_id={run_id}')

    async def mark_pipeline_error(
            self,
            run_id: int,
            error_message: str,
            battery_count: int = 0,
            saved_score_count: int = 0,
            deleted_preprocessed_count: int = 0,
            raw_file_path: Optional[str] = None,
            preprocessed_file_path: Optional[str] = None,
            result_file_path: Optional[str] = None,
    ) -> None:
        """파이프라인 실패 처리"""
        async with self._session_factory() as session:
            async with session.begin():
                from repo.pipeline_run_repo import PipelineRunRepository

                repo = PipelineRunRepository()
                await repo.mark_error(
                    session=session,
                    run_id=run_id,
                    error_message=error_message,
                    battery_count=battery_count,
                    saved_score_count=saved_score_count,
                    deleted_preprocessed_count=deleted_preprocessed_count,
                    raw_file_path=raw_file_path,
                    preprocessed_file_path=preprocessed_file_path,
                    result_file_path=result_file_path,
                )

        logger.info(f'✅ PipelineRunLog 실패 처리 완료: run_id={run_id}')

    async def find_latest_pipeline_run(self) -> Optional[Dict]:
        """가장 최근 파이프라인 실행 이력 조회"""
        async with self._session_factory() as session:
            from repo.pipeline_run_repo import PipelineRunRepository

            repo = PipelineRunRepository()
            run = await repo.find_latest(session)

        logger.info('✅ 최신 PipelineRunLog 조회 완료')
        return run

    async def find_recent_pipeline_runs(self, limit: int = 20) -> List[Dict]:
        """최근 파이프라인 실행 이력 목록 조회"""
        async with self._session_factory() as session:
            from repo.pipeline_run_repo import PipelineRunRepository

            repo = PipelineRunRepository()
            runs = await repo.find_recent(session, limit=limit)

        logger.info(f'✅ 최근 PipelineRunLog 조회 완료: {len(runs)}건')
        return runs

    async def close(self) -> None:
        """DB 연결 종료"""
        await self._engine.dispose()
        logger.info('✅ DBLocalService 종료 완료')