"""의존성 주입 컨테이너"""

from dependency_injector import containers, providers

from core.db import DBLocalService, DBRemoteService
from core.log import setup_logging
from core.setting import Settings
from service.file_service import FileService
from service.ai_service import AIProcessingService
from service.schedule_service import SchedulerService


class Container(containers.DeclarativeContainer):
    """싱글톤 의존성 관리

    이 프로젝트는 여러 서비스가 서로 연결되어 있다.

    예:
    - DBLocalService는 우리 AI 결과 DB에 연결한다.
    - DBRemoteService는 관제시스템 원본 DB에 연결한다.
    - FileService는 원본 데이터를 Parquet 파일로 저장한다.
    - AIProcessingService는 AI 모델 처리를 담당한다.
    - SchedulerService는 매일 정해진 시간에 전체 파이프라인을 실행한다.

    Container는 이런 객체들을 한 번만 만들고 재사용하게 해준다.
    """

    # 설정 및 로그
    settings = providers.Singleton(Settings)
    logger = providers.Singleton(setup_logging, settings=settings)

    # DB 서비스
    db_local_service = providers.Singleton(
        DBLocalService,
        settings=settings,
    )

    remote_db_service = providers.Singleton(
        DBRemoteService,
        settings=settings,
    )

    # 애플리케이션 서비스
    file_service = providers.Singleton(
        FileService,
        settings=settings,
    )

    ai_service = providers.Singleton(
        AIProcessingService,
    )

    scheduler_service = providers.Singleton(
        SchedulerService,
        remote_db=remote_db_service,
        local_db=db_local_service,
        file_service=file_service,
        ai_service=ai_service,
        settings=settings,
    )


container = Container()


