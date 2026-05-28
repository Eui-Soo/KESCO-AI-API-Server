"""원격 DB 서비스 - 매 호출마다 1회 연결/종료"""

import logging
from datetime import date
from typing import List

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from core.setting import Settings
from repo.battery_repo import BatteryRepository


logger = logging.getLogger('app')

class DBRemoteService:
    """원격 DB 서비스

    NullPool 방식:
        - 세션 open  → 물리 연결 생성
        - 세션 close → 물리 연결 즉시 종료 (풀에 반환하지 않음)
        - 연결을 상시 유지하지 않으므로 원격 DB 부하 최소화
    """

    def __init__(self, settings: Settings):
        self._settings = settings

        # NullPool: 풀 없음 - 세션마다 새 연결 생성/종료
        self._engine: AsyncEngine = create_async_engine(
            settings.async_db_remote_url,
            poolclass=NullPool,
            echo=settings.DB_ECHO,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        logger.info('✅ RemoteDBService 초기화 완료 (NullPool - 연결 풀 없음)')

    async def find_battery_by_date(self, target_date: date) -> List[dict]:
        """배터리 데이터 조회: 연결 → SELECT → 연결 종료"""
        logger.info(f'🔗 원격 DB 연결 시작 ({self._settings.DB_REMOTE_HOST}:{self._settings.DB_REMOTE_PORT}/{self._settings.DB_REMOTE_NAME})')
        async with self._session_factory() as session:  # 연결 생성
            repo = BatteryRepository()
            data = await repo.find_by_date(session, target_date)

        logger.info(f'🔌 원격 DB 연결 종료 (수집: {len(data)}건)')
        return data

    async def close(self) -> None:
        """앱 종료 시 엔진 메타데이터 정리"""
        await self._engine.dispose()
        logger.info('✅ RemoteDBService 종료')
