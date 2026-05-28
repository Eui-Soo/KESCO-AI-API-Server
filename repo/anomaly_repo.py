"""이상 점수 레포지토리"""

from typing import List, Tuple

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.model.models import AnomalyScore


class AnomalyScoreRepository:
    """로컬 DB anomaly_score 테이블 WRITE / READ 전담"""

    async def bulk_insert(self, session: AsyncSession, scores: List[dict]) -> int:
        """
        AI 이상 점수를 anomaly_score 테이블에 일괄 저장한다.

        주의:
        - commit은 여기서 하지 않는다.
        - commit은 DBLocalService에서 처리한다.
        """
        records = [AnomalyScore(**score) for score in scores]
        session.add_all(records)
        return len(records)

    async def find_latest(self, session: AsyncSession) -> List[dict]:
        """
        anomaly_score 테이블에서 가장 최근에 저장된 AI 결과를 조회한다.

        현재 DB에는 sc_c1 ~ sc_c20 값이 0.0 ~ 1.0 형태로 저장되어 있다.
        관제시스템에서는 0~100점 형태가 보기 편하므로,
        API 응답을 만들 때 0~100점으로 변환한다.

        추가로 아래 값을 계산해서 응답에 포함한다.

        - score_max: Rack 안에서 가장 높은 셀 점수
        - score_avg: Rack 안의 평균 셀 점수
        - max_cell: 가장 점수가 높은 셀 번호
        - risk_level: 영어 위험 등급
        - risk_label: 한글 위험 등급
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

        latest_scores = []

        for row in rows:
            cell_scores = {}

            for i in range(1, 21):
                raw_score = getattr(row, f"sc_c{i}")

                # DB 저장값: 0.0 ~ 1.0
                # API 응답값: 0 ~ 100점
                display_score = round(raw_score * 100, 2)

                cell_scores[f"c{i}"] = display_score

            score_values = list(cell_scores.values())

            score_max = round(max(score_values), 2)
            score_avg = round(sum(score_values) / len(score_values), 2)
            max_cell = max(cell_scores, key=cell_scores.get)

            risk_level, risk_label = self._get_risk_level(score_max)

            latest_scores.append(
                {
                    "id": row.id,
                    "rack_idx": row.rack_idx,
                    "date": row.date.isoformat(),
                    "inserted": row.inserted.isoformat(),
                    "updated": row.updated.isoformat(),
                    "score_max": score_max,
                    "score_avg": score_avg,
                    "max_cell": max_cell,
                    "risk_level": risk_level,
                    "risk_label": risk_label,
                    "cell_scores": cell_scores,
                }
            )

        return latest_scores

    def _get_risk_level(self, score: float) -> Tuple[str, str]:
        """
        0~100점 기준으로 위험 등급을 계산한다.

        기준:
        - 0 이상 30 미만: 정상
        - 30 이상 60 미만: 주의
        - 60 이상 80 미만: 경고
        - 80 이상 100 이하: 위험
        """
        if score < 30:
            return "normal", "정상"

        if score < 60:
            return "caution", "주의"

        if score < 80:
            return "warning", "경고"

        return "danger", "위험"