"""AI 이상치 탐지 서비스"""

import asyncio
import logging
from typing import List

from ai.ai_process import ai_process

logger = logging.getLogger('app')


class AIProcessingService:
    """배터리 데이터의 anomaly_score를 계산하는 서비스 (싱글톤)"""

    async def process(self, data: List[dict]) -> List[dict]:
        """AI 함수를 호출하여 anomaly_score 계산

        ai_process()는 동기 CPU 작업이므로 ThreadPoolExecutor에서 실행하여
        이벤트 루프(FastAPI 요청 처리)가 블로킹되지 않도록 한다.
        """
        if not data:
            logger.warning('⚠️  처리할 데이터 없음')
            return data

        loop = asyncio.get_running_loop()
        scores = await loop.run_in_executor(None, ai_process, data)

        logger.info(f'🤖 AI 처리 완료: {len(scores)}개 데이터 anomaly_score 계산')
        return scores
