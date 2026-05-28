"""AI 이상치 탐지 처리 함수"""

import random
from collections import defaultdict
from datetime import date, datetime
from typing import List


def ai_process(data: List[dict]) -> List[dict]:
    """하루치 배터리 데이터를 Rack별로 집계하여 AnomalyScore 계산

    같은 Rack의 모든 데이터를 모아 Rack당 1개의 score 생성.

    Args:
        data: 배터리 데이터 리스트 (cv_1~20, index, date 포함)

    Returns:
        Rack별 1개씩의 AnomalyScore 스키마 데이터 리스트
    """
    if not data:
        return []

    rack_groups: dict = defaultdict(list)
    rack_date: dict = {}

    for item in data:
        rack_idx = item['index']
        rack_groups[rack_idx].append(item)
        if rack_idx not in rack_date:
            item_date = item['date']
            rack_date[rack_idx] = item_date.date() if isinstance(item_date, datetime) else item_date

    scores = []
    for rack_idx, items in sorted(rack_groups.items()):
        score: dict = {
            'rack_idx': rack_idx,
            'date': rack_date[rack_idx],
        }
        # TODO: 평균 cv 기반 실제 anomaly score 알고리즘으로 교체 필요
        for i in range(1, 21):
            score[f'sc_c{i}'] = round(random.random(), 4)
        scores.append(score)

    return scores
