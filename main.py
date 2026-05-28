"""KERI Digital Twin API"""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

import core.model  # noqa: F401 - Base.metadata 테이블 등록
from core.container import container
from router.health_router import router as health_router
from router.anomaly_router import router as anomaly_router
from router.pipeline_router import router as pipeline_router


settings = container.settings()
logger = container.logger()


@asynccontextmanager
async def lifespan(_: FastAPI):
    print("=" * 70, flush=True)
    print(f"🚀 {settings.APP_NAME} 서버 시작", flush=True)
    print(f"📌 Version : {settings.APP_VERSION}", flush=True)
    print(f"🌐 Host    : {settings.APP_HOST}", flush=True)
    print(f"🔌 Port    : {settings.APP_PORT}", flush=True)
    print(f"📄 Swagger : http://localhost:{settings.APP_PORT}/docs", flush=True)
    print("=" * 70, flush=True)

    logger.info(f'▶ {settings.APP_NAME} 시작 (v{settings.APP_VERSION})')

    db_local_service = container.db_local_service()

    print("🗄️  로컬 DB 테이블 초기화 중...", flush=True)
    await db_local_service.init_db()
    print("✅ 로컬 DB 테이블 초기화 완료", flush=True)

    print("⏰ 스케줄러 시작 중...", flush=True)
    container.scheduler_service().start()
    print("✅ 스케줄러 시작 완료", flush=True)

    print("✅ 서버 준비 완료. 브라우저에서 Swagger를 열어 확인하세요.", flush=True)
    print(f"👉 http://localhost:{settings.APP_PORT}/docs", flush=True)

    yield

    print("🛑 서버 종료 중...", flush=True)

    container.scheduler_service().stop()
    await db_local_service.close()
    await container.remote_db_service().close()

    logger.info('◀ 종료')
    print("✅ 서버 종료 완료", flush=True)


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# API Router 등록
app.include_router(health_router)
app.include_router(anomaly_router)
app.include_router(pipeline_router)


if __name__ == '__main__':
    print("▶ uvicorn 서버 실행 준비 중...", flush=True)

    uvicorn.run(
        app,
        host=settings.APP_HOST,
        port=settings.APP_PORT,
    )