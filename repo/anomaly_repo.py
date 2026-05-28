"""AI 이상 점수 레포지토리"""

from datetime import date
from typing import Dict, List, Tuple

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.model.models import AnomalyScore


class AnomalyScoreRepository:
    """anomaly_score 테이블 WRITE / READ 전담"""

    async def bulk_insert(self, session: AsyncSession, scores: List[dict]) -> int:
        """이상 점수 일괄 저장"""
        if not scores:
            return 0

        rows = [AnomalyScore(**score) for score in scores]
        session.add_all(rows)

        return len(rows)

    async def find_latest(self, session: AsyncSession) -> List[dict]:
        """가장 최근에 저장된 이상 점수 조회

        기준:
            inserted가 가장 최근인 묶음을 조회한다.
        """
        latest_inserted_result = await session.execute(
            select(func.max(AnomalyScore.inserted))
        )
        latest_inserted = latest_inserted_result.scalar_one_or_none()

        if latest_inserted is None:
            return []

        result = await session.execute(
            select(AnomalyScore)
            .where(AnomalyScore.inserted == latest_inserted)
            .order_by(AnomalyScore.rack_idx)
        )

        rows = result.scalars().all()

        return [self._to_dict(row) for row in rows]

    async def find_by_date(self, session: AsyncSession, target_date: date) -> List[dict]:
        """특정 날짜의 이상 점수 조회

        기준:
            anomaly_score.date = target_date

        주의:
            같은 날짜에 여러 번 AI 파이프라인을 실행하면
            해당 날짜의 결과가 여러 묶음 저장될 수 있다.

            현재는 해당 날짜 전체 결과를 inserted 최신순, rack_idx 순으로 반환한다.
            나중에 pipeline_run_id를 anomaly_score에 추가하면 실행 단위로 더 정확하게 묶을 수 있다.
        """
        result = await session.execute(
            select(AnomalyScore)
            .where(AnomalyScore.date == target_date)
            .order_by(desc(AnomalyScore.inserted), AnomalyScore.rack_idx)
        )

        rows = result.scalars().all()

        return [self._to_dict(row) for row in rows]

    async def find_latest_by_date(self, session: AsyncSession, target_date: date) -> List[dict]:
        """특정 날짜의 가장 최근 실행 결과만 조회

        기준:
            1. target_date에 해당하는 anomaly_score 중
            2. inserted가 가장 최근인 묶음만 조회한다.

        관제시스템에서는 보통 이 함수가 더 적합하다.
        같은 날짜를 여러 번 재실행해도 가장 최근 결과만 내려주기 때문이다.
        """
        latest_inserted_result = await session.execute(
            select(func.max(AnomalyScore.inserted))
            .where(AnomalyScore.date == target_date)
        )
        latest_inserted = latest_inserted_result.scalar_one_or_none()

        if latest_inserted is None:
            return []

        result = await session.execute(
            select(AnomalyScore)
            .where(AnomalyScore.date == target_date)
            .where(AnomalyScore.inserted == latest_inserted)
            .order_by(AnomalyScore.rack_idx)
        )

        rows = result.scalars().all()

        return [self._to_dict(row) for row in rows]

    def _to_dict(self, row: AnomalyScore) -> Dict:
        """ORM 객체를 API 응답용 dict로 변환"""
        cell_scores = {
            f"c{i}": round(getattr(row, f"sc_c{i}") * 100, 2)
            for i in range(1, 21)
        }

        score_values = list(cell_scores.values())
        score_max = round(max(score_values), 2)
        score_avg = round(sum(score_values) / len(score_values), 2)

        max_cell = max(cell_scores, key=cell_scores.get)

        risk_level, risk_label = self._get_risk_level(score_max)

        return {
            "id": row.id,
            "rack_idx": row.rack_idx,
            "date": row.date.isoformat() if row.date else None,
            "inserted": row.inserted.isoformat() if row.inserted else None,
            "updated": row.updated.isoformat() if row.updated else None,
            "score_max": score_max,
            "score_avg": score_avg,
            "max_cell": max_cell,
            "risk_level": risk_level,
            "risk_label": risk_label,
            "cell_scores": cell_scores,
        }

    def _get_risk_level(self, score: float) -> Tuple[str, str]:
        """점수 기준 위험 등급 계산"""
        if score < 30:
            return "normal", "정상"

        if score < 60:
            return "caution", "주의"

        if score < 80:
            return "warning", "경고"

        return "danger", "위험"