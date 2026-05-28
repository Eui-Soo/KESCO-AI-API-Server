"""배터리 데이터 Parquet 저장 서비스"""

import logging
from datetime import date
from pathlib import Path
from typing import List, cast

import pandas as pd

from core.setting import Settings


logger = logging.getLogger('app')

_VOLT_COLS = [f'cv_{i}' for i in range(1, 21)]


class FileService:
    """배터리 데이터를 날짜/index/Rack별 Parquet 파일로 저장하는 서비스 (싱글톤)

    저장 구조:
        files/
          YYYY-MM-DD/
            01/
              Rack_01.parquet
            02/
              Rack_02.parquet
            ...
    """

    def __init__(self, settings: Settings):
        self._files_dir = Path(settings.FILES_DIR)
        logger.info(f'✅ FileService 초기화 완료 (저장 경로: {self._files_dir})')

    def save(self, data: List[dict], target_date: date) -> Path:
        """Rack별 Parquet 파일 생성 후 날짜 폴더 경로 반환"""
        date_dir = self._files_dir / str(target_date)

        if not data:
            logger.warning(f'⚠️  저장할 데이터 없음 ({target_date})')
            return date_dir

        df = pd.DataFrame(data)

        for rack_idx, group in df.groupby('index'):
            idx = cast(int, rack_idx)  # groupby 키는 Hashable로 추론 - pandas 스텁 한계
            rack_dir = date_dir / f'{idx:02d}'
            rack_dir.mkdir(parents=True, exist_ok=True)
            file_path = rack_dir / f'Rack_{idx:02d}.parquet'
            self._save_rack(file_path, group)

        rack_count = df['index'].nunique()
        logger.info(f'💾 Parquet 생성 완료: Rack {rack_count}개 → {date_dir}')
        return date_dir

    def _save_rack(self, file_path: Path, df: pd.DataFrame) -> None:
        cols = ['id', 'total_racks', 'index'] + _VOLT_COLS + ['date']
        out = df[cols].copy()
        out['date'] = pd.to_datetime(out['date'])
        out.to_parquet(file_path, engine='pyarrow', compression='snappy', index=False)
        logger.debug(f'  └─ {file_path.name} 저장 완료 ({len(df)}행)')
