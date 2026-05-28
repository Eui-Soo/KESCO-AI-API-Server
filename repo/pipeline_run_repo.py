"""AI 파이프라인 실행 이력 레포지토리"""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.model.models import PipelineRunLog


class PipelineRunRepository:
    """pipeline_run_log 테이블 WRITE / READ 전담"""

    async def create_running(
            self,
            session: AsyncSession,
            ess_id: str,
            target_date,
            message: Optional[str] = None,
    ) -> PipelineRunLog:
        """파이프라인 실행 시작 로그 생성"""
        log = PipelineRunLog(
            ess_id=ess_id,
            target_date=target_date,
            status="running",
            message=message or "AI pipeline started.",
        )

        session.add(log)
        await session.flush()
        await session.refresh(log)

        return log

    async def mark_success(
            self,
            session: AsyncSession,
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
        log = await session.get(PipelineRunLog, run_id)

        if log is None:
            return

        log.status = "success"
        log.finished_at = datetime.now()
        log.battery_count = battery_count
        log.saved_score_count = saved_score_count
        log.deleted_preprocessed_count = deleted_preprocessed_count
        log.raw_file_path = raw_file_path
        log.preprocessed_file_path = preprocessed_file_path
        log.result_file_path = result_file_path
        log.message = message or "AI pipeline completed successfully."
        log.error_message = None

    async def mark_error(
            self,
            session: AsyncSession,
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
        log = await session.get(PipelineRunLog, run_id)

        if log is None:
            return

        log.status = "error"
        log.finished_at = datetime.now()
        log.battery_count = battery_count
        log.saved_score_count = saved_score_count
        log.deleted_preprocessed_count = deleted_preprocessed_count
        log.raw_file_path = raw_file_path
        log.preprocessed_file_path = preprocessed_file_path
        log.result_file_path = result_file_path
        log.message = "AI pipeline failed."
        log.error_message = error_message

    async def find_latest(self, session: AsyncSession) -> Optional[Dict]:
        """가장 최근 파이프라인 실행 이력 조회"""
        result = await session.execute(
            select(PipelineRunLog)
            .order_by(desc(PipelineRunLog.started_at), desc(PipelineRunLog.id))
            .limit(1)
        )

        row = result.scalar_one_or_none()

        if row is None:
            return None

        return self._to_dict(row)

    async def find_recent(self, session: AsyncSession, limit: int = 20) -> List[Dict]:
        """최근 파이프라인 실행 이력 목록 조회"""
        result = await session.execute(
            select(PipelineRunLog)
            .order_by(desc(PipelineRunLog.started_at), desc(PipelineRunLog.id))
            .limit(limit)
        )

        rows = result.scalars().all()

        return [self._to_dict(row) for row in rows]

    def _to_dict(self, row: PipelineRunLog) -> Dict:
        """ORM 객체를 API 응답용 dict로 변환"""
        return {
            "id": row.id,
            "ess_id": row.ess_id,
            "target_date": row.target_date.isoformat() if row.target_date else None,
            "started_at": row.started_at.isoformat() if row.started_at else None,
            "finished_at": row.finished_at.isoformat() if row.finished_at else None,
            "status": row.status,
            "battery_count": row.battery_count,
            "saved_score_count": row.saved_score_count,
            "deleted_preprocessed_count": row.deleted_preprocessed_count,
            "raw_file_path": row.raw_file_path,
            "preprocessed_file_path": row.preprocessed_file_path,
            "result_file_path": row.result_file_path,
            "message": row.message,
            "error_message": row.error_message,
            "inserted": row.inserted.isoformat() if row.inserted else None,
            "updated": row.updated.isoformat() if row.updated else None,
        }