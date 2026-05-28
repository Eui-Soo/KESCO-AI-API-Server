"""APScheduler 서비스 - 일일 ESS AI 처리 파이프라인"""

import logging
from datetime import date, timedelta
from typing import List
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
        5. 원본 데이터를 raw Parquet 파일로 누적 저장한다.
        6. 전처리 데이터를 preprocessed Parquet 파일로 누적 저장한다.
        7. AI 모델을 실행한다.
        8. AI 결과를 result Parquet 파일과 DB에 저장한다.
        9. 오래된 preprocessed 데이터를 자동 삭제한다.
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
        self._file_service = file_service
        self._ai_service = ai_service
        self._settings = settings
        self._is_running = False

        self._scheduler = AsyncIOScheduler()

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
            f'{self._settings.SCHEDULE_SECOND:02d} 자동 실행, '
            f'처리 날짜 offset={self._settings.TARGET_DATE_OFFSET_DAYS}, '
            f'ESS ID={self._settings.DEFAULT_ESS_ID}, '
            f'preprocessed 보관={self._settings.PREPROCESSED_RETENTION_DAYS}일'
        )

    def _get_target_date(self) -> date:
        """스케줄 실행 시 처리할 대상 날짜 계산

        예:
            TARGET_DATE_OFFSET_DAYS=0
                → 오늘 데이터 처리

            TARGET_DATE_OFFSET_DAYS=-1
                → 전날 데이터 처리
        """
        return date.today() + timedelta(days=self._settings.TARGET_DATE_OFFSET_DAYS)

    def _get_ess_id(self, data: List[dict]) -> str:
        """저장 경로에 사용할 ESS ID를 결정한다.

        우선순위:
            1. 데이터 안에 ess_id가 있으면 그 값을 사용
            2. 데이터 안에 site_id가 있으면 그 값을 사용
            3. 없으면 .env의 DEFAULT_ESS_ID 사용
        """
        if data:
            first = data[0]

            if first.get('ess_id'):
                return str(first['ess_id'])

            if first.get('site_id'):
                return str(first['site_id'])

        return self._settings.DEFAULT_ESS_ID

    async def _process(self) -> None:
        """스케줄러가 매일 자동으로 실행하는 AI 처리 파이프라인"""
        if self._is_running:
            logger.warning('⏭️ 이전 작업 진행 중 - 이번 실행 생략')
            return

        self._is_running = True
        target_date = self._get_target_date()

        logger.info(f'🚀 일일 AI 파이프라인 시작 [target_date={target_date}]')

        try:
            logger.info('📥 [1/6] 관제시스템 DB에서 배터리 데이터 수집')
            data = await self._remote_db.find_battery_by_date(target_date)
            ess_id = self._get_ess_id(data)

            logger.info(f'📊 수집 데이터 수: {len(data)}건, ESS ID={ess_id}')

            logger.info('💾 [2/6] 원본 데이터 raw Parquet 저장')
            raw_file_path = self._file_service.save_raw(
                data=data,
                target_date=target_date,
                ess_id=ess_id,
            )

            logger.info('🧹 [3/6] 전처리 데이터 preprocessed Parquet 저장')
            # 현재는 실제 전처리 로직이 없으므로 raw와 동일한 데이터를 저장한다.
            # 실제 AI 모델 연결 시 preprocessed_data를 전처리 결과로 교체하면 된다.
            preprocessed_data = data
            preprocessed_file_path = self._file_service.save_preprocessed(
                data=preprocessed_data,
                target_date=target_date,
                ess_id=ess_id,
            )

            logger.info('🤖 [4/6] AI 처리 및 anomaly_score 계산')
            scores = await self._ai_service.process(preprocessed_data)

            logger.info('💾 [5/6] AI 결과 result Parquet 저장 및 DB 저장')
            result_file_path = self._file_service.save_result(
                scores=scores,
                target_date=target_date,
                ess_id=ess_id,
            )
            saved_count = await self._local_db.save_anomaly_scores(scores)

            logger.info('🧹 [6/6] 오래된 preprocessed 데이터 자동 삭제')
            deleted_preprocessed_count = self._file_service.cleanup_old_preprocessed()

            logger.info(
                f'✅ 일일 AI 파이프라인 완료 '
                f'[target_date={target_date}, ess_id={ess_id}, '
                f'battery_count={len(data)}, saved_score_count={saved_count}, '
                f'deleted_preprocessed_count={deleted_preprocessed_count}, '
                f'raw_file={raw_file_path}, '
                f'preprocessed_file={preprocessed_file_path}, '
                f'result_file={result_file_path}]'
            )

        except Exception as e:
            logger.exception(f'❌ 일일 AI 파이프라인 실행 오류: {e}')

        finally:
            self._is_running = False

    async def run_once(self) -> dict:
        """개발/테스트용 수동 실행 함수

        운영에서는 관제시스템이 이 함수를 직접 호출하지 않는다.
        개발자가 Swagger에서 테스트할 때만 사용한다.

        TARGET_DATE_OFFSET_DAYS 설정을 반영한 날짜를 기준으로 실행한다.
        """
        if self._is_running:
            return {
                'status': 'skipped',
                'message': '이미 AI 파이프라인이 실행 중입니다.',
            }

        self._is_running = True
        target_date = self._get_target_date()

        logger.info(f'🚀 수동 AI 파이프라인 시작 [target_date={target_date}]')

        try:
            logger.info('📥 [1/6] 관제시스템 DB에서 배터리 데이터 수집')
            data = await self._remote_db.find_battery_by_date(target_date)
            ess_id = self._get_ess_id(data)

            logger.info(f'📊 수집 데이터 수: {len(data)}건, ESS ID={ess_id}')

            logger.info('💾 [2/6] 원본 데이터 raw Parquet 저장')
            raw_file_path = self._file_service.save_raw(
                data=data,
                target_date=target_date,
                ess_id=ess_id,
            )

            logger.info('🧹 [3/6] 전처리 데이터 preprocessed Parquet 저장')
            # 현재는 실제 전처리 로직이 없으므로 raw와 동일한 데이터를 저장한다.
            preprocessed_data = data
            preprocessed_file_path = self._file_service.save_preprocessed(
                data=preprocessed_data,
                target_date=target_date,
                ess_id=ess_id,
            )

            logger.info('🤖 [4/6] AI 처리 및 anomaly_score 계산')
            scores = await self._ai_service.process(preprocessed_data)

            logger.info('💾 [5/6] AI 결과 result Parquet 저장 및 DB 저장')
            result_file_path = self._file_service.save_result(
                scores=scores,
                target_date=target_date,
                ess_id=ess_id,
            )
            saved_count = await self._local_db.save_anomaly_scores(scores)

            logger.info('🧹 [6/6] 오래된 preprocessed 데이터 자동 삭제')
            deleted_preprocessed_count = self._file_service.cleanup_old_preprocessed()

            logger.info(
                f'✅ 수동 AI 파이프라인 완료 '
                f'[target_date={target_date}, ess_id={ess_id}, '
                f'battery_count={len(data)}, saved_score_count={saved_count}, '
                f'deleted_preprocessed_count={deleted_preprocessed_count}, '
                f'raw_file={raw_file_path}, '
                f'preprocessed_file={preprocessed_file_path}, '
                f'result_file={result_file_path}]'
            )

            return {
                'status': 'success',
                'target_date': target_date.isoformat(),
                'target_date_offset_days': self._settings.TARGET_DATE_OFFSET_DAYS,
                'ess_id': ess_id,
                'battery_count': len(data),
                'saved_score_count': saved_count,
                'deleted_preprocessed_count': deleted_preprocessed_count,
                'raw_file_path': raw_file_path,
                'preprocessed_file_path': preprocessed_file_path,
                'result_file_path': result_file_path,
                'message': 'AI pipeline completed successfully.',
            }

        except Exception as e:
            logger.exception(f'❌ 수동 AI 파이프라인 실행 오류: {e}')

            return {
                'status': 'error',
                'target_date': target_date.isoformat(),
                'target_date_offset_days': self._settings.TARGET_DATE_OFFSET_DAYS,
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
            f'{self._settings.SCHEDULE_SECOND:02d} 자동 실행, '
            f'처리 날짜 offset={self._settings.TARGET_DATE_OFFSET_DAYS}, '
            f'ESS ID={self._settings.DEFAULT_ESS_ID}, '
            f'preprocessed 보관={self._settings.PREPROCESSED_RETENTION_DAYS}일'
        )

    def stop(self) -> None:
        """스케줄러 종료"""
        self._scheduler.shutdown(wait=False)
        logger.info('⏰ 스케줄러 종료')