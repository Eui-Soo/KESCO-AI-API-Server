"""로컬 DB 서비스"""

import logging
from typing import List

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine
)
from sqlalchemy.orm import DeclarativeBase

from core.setting import Settings


logger = logging.getLogger('app')


class Base(DeclarativeBase):
    pass


class DBLocalService:
    def __init__(self, settings: Settings):
        self._engine: AsyncEngine = create_async_engine(
            settings.async_db_url,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_pre_ping=True,
            echo=settings.DB_ECHO,
            future=True
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
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
            logger.warning('⚠️  등록할 이상 점수 없음')
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

    async def close(self) -> None:
        """DB 연결 종료"""
        await self._engine.dispose()
        logger.info('✅ DBLocalService 종료 완료')
