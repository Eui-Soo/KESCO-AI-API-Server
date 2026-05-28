"""APScheduler 서비스 - 일일 ESS AI 처리 파이프라인"""

import logging
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core.db import DBLocalService, DBRemoteService
from core.setting import Settings
from service.file_service import FileService
from service.ai_service import AIProcessingService


logger = logging.getLogger('app')


class SchedulerService:
    """일일 AI 처리 파이프라인 스케줄러

    운영 구조:
        1. 서버가 켜지면 스케줄러만 등록한다.
        2. 서버 시작 즉시 AI를 실행하지 않는다.
        3. 매일 .env에 설정된 시간에 자동 실행된다.
        4. 관제시스템 DB에서 하루치 배터리 데이터를 가져온다.
        5. AI 모델을 실행한다.
        6. 결과를 우리 AI 결과 DB의 anomaly_score 테이블에 저장한다.
    """

    def __init__(
            self,
            remote_db: DBRemoteService,
            local_db: DBLocalService,
            file_service: FileService,
            ai_service: AIProcessingService,
            settings: Settings,
    ):
        self._remote_db = remote_db
        self._local_db = local_db
        self._report = file_service
        self._ai_service = ai_service
        self._settings = settings
        self._is_running = False

        self._scheduler = AsyncIOScheduler()

        # 운영용 스케줄러
        # 실행 시간은 .env의 SCHEDULE_HOUR / SCHEDULE_MINUTE / SCHEDULE_SECOND 값으로 결정된다.
        self._scheduler.add_job(
            self._process,
            trigger='cron',
            hour=self._settings.SCHEDULE_HOUR,
            minute=self._settings.SCHEDULE_MINUTE,
            second=self._settings.SCHEDULE_SECOND,
            max_instances=1,
            misfire_grace_time=3600,
            id='daily_pipeline',
            name='일일 ESS AI 처리 파이프라인',
        )

        logger.info(
            f'✅ SchedulerService 초기화 완료 - 매일 '
            f'{self._settings.SCHEDULE_HOUR:02d}:'
            f'{self._settings.SCHEDULE_MINUTE:02d}:'
            f'{self._settings.SCHEDULE_SECOND:02d} 자동 실행'
        )

    async def _process(self) -> None:
        """스케줄러가 매일 자동으로 실행하는 AI 처리 파이프라인"""
        if self._is_running:
            logger.warning('⏭️ 이전 작업 진행 중 - 이번 실행 생략')
            return

        self._is_running = True
        target_date = date.today()

        logger.info(f'🚀 일일 AI 파이프라인 시작 [{target_date}]')

        try:
            logger.info('📥 [1/3] 관제시스템 DB에서 배터리 데이터 수집')
            data = await self._remote_db.find_battery_by_date(target_date)

            logger.info(f'📊 수집 데이터 수: {len(data)}건')

            logger.info('💾 [2/3] 원본 데이터 Parquet 파일 저장')
            self._report.save(data, target_date)

            logger.info('🤖 [3/3] AI 처리 및 anomaly_score 계산')
            scores = await self._ai_service.process(data)
            saved_count = await self._local_db.save_anomaly_scores(scores)

            logger.info(
                f'✅ 일일 AI 파이프라인 완료 '
                f'[date={target_date}, battery_count={len(data)}, saved_score_count={saved_count}]'
            )

        except Exception as e:
            logger.exception(f'❌ 일일 AI 파이프라인 실행 오류: {e}')

        finally:
            self._is_running = False

    async def run_once(self) -> dict:
        """개발/테스트용 수동 실행 함수

        운영에서는 관제시스템이 이 함수를 직접 호출하지 않는다.
        개발자가 Swagger에서 테스트할 때만 사용한다.

        현재는 오늘 날짜 데이터를 기준으로 실행한다.
        """
        if self._is_running:
            return {
                'status': 'skipped',
                'message': '이미 AI 파이프라인이 실행 중입니다.',
            }

        self._is_running = True
        target_date = date.today()

        logger.info(f'🚀 수동 AI 파이프라인 시작 [{target_date}]')

        try:
            logger.info('📥 [1/3] 관제시스템 DB에서 배터리 데이터 수집')
            data = await self._remote_db.find_battery_by_date(target_date)

            logger.info(f'📊 수집 데이터 수: {len(data)}건')

            logger.info('💾 [2/3] 원본 데이터 Parquet 파일 저장')
            self._report.save(data, target_date)

            logger.info('🤖 [3/3] AI 처리 및 anomaly_score 계산')
            scores = await self._ai_service.process(data)
            saved_count = await self._local_db.save_anomaly_scores(scores)

            logger.info(
                f'✅ 수동 AI 파이프라인 완료 '
                f'[date={target_date}, battery_count={len(data)}, saved_score_count={saved_count}]'
            )

            return {
                'status': 'success',
                'target_date': target_date.isoformat(),
                'battery_count': len(data),
                'saved_score_count': saved_count,
                'message': 'AI pipeline completed successfully.',
            }

        except Exception as e:
            logger.exception(f'❌ 수동 AI 파이프라인 실행 오류: {e}')

            return {
                'status': 'error',
                'target_date': target_date.isoformat(),
                'message': str(e),
            }

        finally:
            self._is_running = False

    def start(self) -> None:
        """스케줄러 시작"""
        self._scheduler.start()
        logger.info(
            f'⏰ 스케줄러 시작 - 매일 '
            f'{self._settings.SCHEDULE_HOUR:02d}:'
            f'{self._settings.SCHEDULE_MINUTE:02d}:'
            f'{self._settings.SCHEDULE_SECOND:02d} 자동 실행'
        )

    def stop(self) -> None:
        """스케줄러 종료"""
        self._scheduler.shutdown(wait=False)
        logger.info('⏰ 스케줄러 종료')