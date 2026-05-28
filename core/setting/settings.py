from functools import cached_property
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 전체 설정

    이 클래스는 .env / .env.dev 파일에 적힌 환경변수를 읽어서
    Python 코드에서 사용할 수 있게 해준다.

    예:
    - APP_PORT=8000
    - DB_HOST=localhost
    - SCHEDULE_HOUR=0
    """

    # Application
    APP_NAME: str = 'KESCO-DigitalTwin'
    APP_VERSION: str = '1.0.0'
    APP_HOST: str = '0.0.0.0'
    APP_PORT: int = 8000
    DEBUG: bool = False

    # Logging
    LOG_BACKUP_DAYS: int = 60
    LOG_DIR: str = 'log'

    # Files
    FILES_DIR: str = 'files'

    # Scheduler
    # 매일 몇 시에 AI 파이프라인을 자동 실행할지 설정한다.
    SCHEDULE_HOUR: int = 0
    SCHEDULE_MINUTE: int = 0
    SCHEDULE_SECOND: int = 30

    # 스케줄 실행 시 처리할 데이터 날짜 기준
    # 0  = 오늘 데이터 처리
    # -1 = 전날 데이터 처리
    TARGET_DATE_OFFSET_DAYS: int = 0

    # Database - 우리 AI 결과 DB
    DB_HOST: str = 'localhost'
    DB_PORT: int = 5432
    DB_NAME: str = 'kesco_digitaltwin'
    DB_USER: str = 'kesco'
    DB_PASSWORD: str = 'kesco'
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_ECHO: bool = False

    # Remote Database - 관제시스템 원본 DB
    # 개발 테스트 중에는 우리 로컬 DB를 임시로 원격 DB처럼 사용한다.
    DB_REMOTE_HOST: str = 'localhost'
    DB_REMOTE_PORT: int = 5432
    DB_REMOTE_NAME: str = 'kesco_digitaltwin'
    DB_REMOTE_USER: str = 'kesco'
    DB_REMOTE_PASSWORD: str = 'kesco'

    model_config = SettingsConfigDict(
        env_file=('.env.dev', '.env'),
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='ignore',
    )

    @cached_property
    def log_file(self) -> Path:
        """현재 로그 파일 경로"""
        return Path(self.LOG_DIR, 'app.log')

    @cached_property
    def log_dir_path(self) -> Path:
        """로그 디렉토리 경로"""
        return Path(self.LOG_DIR)

    @cached_property
    def async_db_url(self) -> str:
        """우리 AI 결과 DB 접속 URL"""
        return (
            f'postgresql+asyncpg://'
            f'{self.DB_USER}:{self.DB_PASSWORD}'
            f'@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'
        )

    @cached_property
    def async_db_remote_url(self) -> str:
        """관제시스템 원본 DB 접속 URL"""
        return (
            f'postgresql+asyncpg://'
            f'{self.DB_REMOTE_USER}:{self.DB_REMOTE_PASSWORD}'
            f'@{self.DB_REMOTE_HOST}:{self.DB_REMOTE_PORT}/{self.DB_REMOTE_NAME}'
        )