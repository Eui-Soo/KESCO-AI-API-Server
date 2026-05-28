"""배터리 데이터 레포지토리"""

from datetime import date, datetime
from typing import List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class BatteryRepository:
    """원격 DB battery 테이블 READ 전담"""

    async def find_by_date(self, session: AsyncSession, target_date: date) -> List[dict]:
        """특정 날짜의 배터리 데이터 조회"""
        result = await session.execute(text('''
            SELECT id,
                total_racks,
                index,
                cv_1, cv_2, cv_3, cv_4, cv_5,
                cv_6, cv_7, cv_8, cv_9, cv_10,
                cv_11, cv_12, cv_13, cv_14, cv_15,
                cv_16, cv_17, cv_18, cv_19, cv_20,
                date
            FROM battery
            WHERE DATE(inserted) = :target_date
            ORDER BY index, inserted
        '''), {'target_date': target_date})

        records = []
        for row in result.mappings():
            record = dict(row)
            if isinstance(record.get('date'), datetime):
                record['date'] = record['date'].date()
            records.append(record)
        return records
