"""배터리 데이터 레포지토리

이 파일은 관제시스템 원본 DB에서 배터리 데이터를 읽어오는 역할을 한다.

현재 상태:
    - 개발/테스트용 battery 테이블을 조회한다.

나중에 실제 관제시스템 DB 구조를 받으면:
    - SQL의 FROM 테이블명
    - SELECT 컬럼명
    - WHERE 날짜 조건
    - _to_standard_dict() 안의 컬럼 매핑

이 부분만 수정하면 된다.

중요:
    이 레포지토리는 외부 DB 구조를 그대로 반환하지 않고,
    AI 서버 내부에서 쓰기 좋은 표준 dict 형태로 변환해서 반환한다.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class BatteryRepository:
    """관제시스템 원본 배터리 데이터 READ 전담

    현재는 개발용 battery 테이블을 조회한다.

    추후 실제 관제 DB 연동 시 이 클래스만 수정하면
    service / ai / file 저장 구조는 최대한 그대로 유지할 수 있다.
    """

    async def find_by_date(self, session: AsyncSession, target_date: date) -> List[dict]:
        """특정 날짜의 배터리 데이터 조회

        현재 기준:
            - 개발용 battery 테이블 조회
            - inserted 날짜 기준으로 조회

        운영 전 수정 필요:
            실제 관제시스템 DB에서는 inserted가 아니라
            measured_at / collect_dt / clct_dt 같은 실제 측정 시간 컬럼을
            기준으로 조회해야 할 가능성이 높다.
        """

        # ============================================================
        # TODO: 실제 관제시스템 DB 연동 시 이 SQL을 수정한다.
        #
        # 현재 개발용 테이블:
        #   battery
        #
        # 실제 운영 시 예시:
        #   FROM 실제_관제_DB_테이블명
        #   WHERE measured_at >= :start_datetime
        #     AND measured_at < :end_datetime
        #
        # 현재는 기존 테스트 데이터와 호환하기 위해
        # DATE(inserted) = :target_date 조건을 사용한다.
        # ============================================================
        result = await session.execute(
            text(
                """
                SELECT
                    id,
                    total_racks,
                    index,
                    cv_1, cv_2, cv_3, cv_4, cv_5,
                    cv_6, cv_7, cv_8, cv_9, cv_10,
                    cv_11, cv_12, cv_13, cv_14, cv_15,
                    cv_16, cv_17, cv_18, cv_19, cv_20,
                    date,
                    inserted
                FROM battery
                WHERE DATE(inserted) = :target_date
                ORDER BY index, inserted
                """
            ),
            {"target_date": target_date},
        )

        records = []

        for row in result.mappings():
            raw_record = dict(row)
            standard_record = self._to_standard_dict(raw_record, target_date)
            records.append(standard_record)

        return records

    def _to_standard_dict(
            self,
            raw: Dict[str, Any],
            target_date: date,
    ) -> Dict[str, Any]:
        """DB row를 AI 서버 내부 표준 dict로 변환한다.

        내부 표준 형태:
            {
                "ess_id": "KESCO_ESS_001",
                "site_id": "SITE_001",
                "rack_no": 1,
                "index": 1,
                "measured_at": datetime 또는 None,
                "date": date,
                "cv_1": 3.61,
                ...
                "cv_20": 3.62,
                "temperature": None,
                "current_a": None,
                "voltage_v": None,
                "soc": None,
            }

        왜 표준 dict로 변환하나?
            실제 관제시스템 DB 컬럼명이 바뀌어도
            service/file_service/ai_process 쪽 코드는 최대한 안 바꾸기 위해서다.
        """

        # 현재 개발용 battery 테이블에서는 ESS ID가 없다.
        # 그래서 기본값을 넣는다.
        #
        # 실제 관제 DB 연동 시에는 예를 들어:
        #   ess_id = raw.get("ess_id") or raw.get("site_code") or raw.get("eqp_no")
        # 이런 식으로 바꾸면 된다.
        ess_id = self._get_first_value(
            raw,
            ["ess_id", "site_id", "eqp_no"],
            default="KESCO_ESS_001",
        )

        site_id = self._get_first_value(
            raw,
            ["site_id", "eqp_no"],
            default=None,
        )

        # 현재 개발용 battery 테이블에서는 index가 Rack 번호 역할을 한다.
        rack_no = raw.get("rack_no")
        if rack_no is None:
            rack_no = raw.get("index")

        # 기존 ai_process.py 호환을 위해 index도 유지한다.
        # 현재 ai_process.py에서 item["index"]를 Rack 번호로 사용 중이다.
        rack_index = rack_no

        raw_date = raw.get("date")
        normalized_date = self._normalize_date(raw_date, default=target_date)

        # 현재 개발용 battery 테이블에는 measured_at이 없으므로 inserted를 대신 넣는다.
        # 실제 관제 DB에서는 measured_at / collect_dt / clct_dt를 직접 매핑하면 된다.
        measured_at = self._get_first_value(
            raw,
            ["measured_at", "collect_dt", "clct_dt", "inserted"],
            default=None,
        )

        record: Dict[str, Any] = {
            "id": raw.get("id"),
            "ess_id": ess_id,
            "site_id": site_id,
            "total_racks": raw.get("total_racks"),
            "bank_no": raw.get("bank_no"),
            "rack_no": rack_no,
            "index": rack_index,
            "string_no": raw.get("string_no"),
            "module_no": raw.get("module_no"),
            "measured_at": measured_at,
            "date": normalized_date,
            "temperature": raw.get("temperature"),
            "current_a": raw.get("current_a"),
            "voltage_v": raw.get("voltage_v"),
            "soc": raw.get("soc"),
        }

        for i in range(1, 21):
            record[f"cv_{i}"] = raw.get(f"cv_{i}")

        return record

    def _normalize_date(
            self,
            value: Any,
            default: Optional[date] = None,
    ) -> Optional[date]:
        """date/datetime/string 값을 date로 정리한다."""
        if value is None:
            return default

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        if isinstance(value, str):
            # '2026-05-27' 또는 '2026-05-27 00:00:00' 형태 대응
            try:
                return datetime.fromisoformat(value).date()
            except ValueError:
                return default

        return default

    def _get_first_value(
            self,
            raw: Dict[str, Any],
            keys: List[str],
            default: Any = None,
    ) -> Any:
        """여러 후보 컬럼 중 처음으로 값이 있는 것을 반환한다.

        실제 관제 DB는 컬럼명이 달라질 수 있으므로
        alias 후보를 이 함수로 처리한다.

        예:
            ["measured_at", "collect_dt", "clct_dt"]
        """
        for key in keys:
            value = raw.get(key)

            if value is not None:
                return value

        return default