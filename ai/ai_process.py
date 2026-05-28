"""AI 이상 점수 처리 함수

현재 이 파일은 실제 AI 모델이 연결되기 전까지 사용하는 개발용 임시 처리 모듈이다.

운영 전 반드시 아래 구조로 교체해야 한다.

권장 구조:
    ai/
    ├── model_loader.py   # 서버 시작 시 AI 모델 1회 로딩
    ├── preprocess.py     # DB 원본 데이터를 모델 입력 형태로 변환
    ├── inference.py      # 실제 AI 모델 추론 실행
    ├── postprocess.py    # 모델 출력값을 anomaly_score 저장 형식으로 변환
    └── ai_process.py     # 전체 처리 흐름 연결

중요:
    - 현재 코드는 random 점수를 생성한다.
    - 현재 결과는 실제 배터리 이상 예측 결과가 아니다.
    - API / DB / 스케줄러 연동 흐름을 검증하기 위한 임시 점수다.
"""

import random
from collections import defaultdict
from datetime import datetime
from typing import List


def ai_process(data: List[dict]) -> List[dict]:
    """하루치 배터리 데이터를 Rack별로 묶어 이상 점수를 생성한다.

    현재 동작:
        - 입력 데이터를 Rack 번호 기준으로 그룹화한다.
        - Rack당 anomaly_score 결과 1건을 만든다.
        - sc_c1 ~ sc_c20 값은 random 값으로 생성한다.

    운영 전 교체 필요:
        - random 점수 생성 부분을 실제 AI 모델 추론 결과로 바꿔야 한다.
        - 전처리, 추론, 후처리 로직을 분리하는 것을 권장한다.

    Args:
        data:
            관제시스템 DB에서 조회한 하루치 배터리 데이터 리스트.
            현재 테스트 구조에서는 아래 키를 사용한다.

            - index: Rack 번호
            - date: 데이터 날짜
            - cv_1 ~ cv_20: 셀 전압값

    Returns:
        anomaly_score 테이블에 저장 가능한 dict 리스트.
        Rack별로 1개 결과가 생성된다.
    """
    if not data:
        return []

    rack_groups: dict = defaultdict(list)
    rack_date: dict = {}

    for item in data:
        rack_idx = item["index"]

        rack_groups[rack_idx].append(item)

        if rack_idx not in rack_date:
            item_date = item["date"]
            rack_date[rack_idx] = (
                item_date.date()
                if isinstance(item_date, datetime)
                else item_date
            )

    scores = []

    for rack_idx, items in sorted(rack_groups.items()):
        score: dict = {
            "rack_idx": rack_idx,
            "date": rack_date[rack_idx],
        }

        # TODO:
        #   아래 random 점수 생성 로직은 개발용 임시 코드다.
        #   실제 운영 전에는 아래 흐름으로 교체해야 한다.
        #
        #   1. items 데이터를 모델 입력 형태로 전처리
        #   2. AI 모델 추론 실행
        #   3. 모델 출력값을 sc_c1 ~ sc_c20 형태로 변환
        #   4. anomaly_score 테이블에 저장
        #
        #   현재 값의 범위:
        #   - DB 저장값: 0.0 ~ 1.0
        #   - API 응답값: repo/anomaly_repo.py에서 0 ~ 100점으로 변환
        for i in range(1, 21):
            score[f"sc_c{i}"] = round(random.random(), 4)

        scores.append(score)

    return scores