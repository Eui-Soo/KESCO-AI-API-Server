"""SQLAlchemy ORM 모델 정의"""

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    func,
)

from core.db.db_service import Base


class Battery(Base):
    """개발/테스트용 배터리 원본 데이터 테이블

    실제 운영 환경에서는 이 테이블을 우리 DB에 둘 필요가 없다.
    운영에서는 관제시스템 DB의 원본 테이블을 읽어온다.

    현재 이 테이블은 로컬 개발 환경에서 관제시스템 DB를 흉내내기 위한
    샘플 테이블 역할을 한다.
    """

    __tablename__ = "battery"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    total_racks = Column(Integer, nullable=False)
    index = Column("index", Integer, nullable=False)

    cv_1 = Column(Float, nullable=False)
    cv_2 = Column(Float, nullable=False)
    cv_3 = Column(Float, nullable=False)
    cv_4 = Column(Float, nullable=False)
    cv_5 = Column(Float, nullable=False)
    cv_6 = Column(Float, nullable=False)
    cv_7 = Column(Float, nullable=False)
    cv_8 = Column(Float, nullable=False)
    cv_9 = Column(Float, nullable=False)
    cv_10 = Column(Float, nullable=False)
    cv_11 = Column(Float, nullable=False)
    cv_12 = Column(Float, nullable=False)
    cv_13 = Column(Float, nullable=False)
    cv_14 = Column(Float, nullable=False)
    cv_15 = Column(Float, nullable=False)
    cv_16 = Column(Float, nullable=False)
    cv_17 = Column(Float, nullable=False)
    cv_18 = Column(Float, nullable=False)
    cv_19 = Column(Float, nullable=False)
    cv_20 = Column(Float, nullable=False)

    date = Column(Date, nullable=False)

    inserted = Column(DateTime, nullable=False, server_default=func.now())
    updated = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

class MonitoringBatterySample(Base):
    """관제시스템 원본 배터리 데이터 예시 테이블

    실제 운영 환경에서 반드시 이 테이블을 사용하는 것은 아니다.

    목적:
        - 관제시스템 DB 구조를 받기 전 개발용 표준 구조로 사용
        - 실제 관제 DB 컬럼을 어떤 내부 필드로 매핑할지 기준 제공
        - 로컬 테스트에서 관제시스템 원본 DB를 흉내내기 위한 샘플 테이블

    실제 관제 DB 연동 시:
        repo/battery_repo.py에서 실제 DB 컬럼명을 이 표준 구조로 변환한다.

    예:
        clct_dt 또는 collect_time  -> measured_at
        site_code 또는 eqp_no      -> ess_id / site_id
        rack_no                    -> rack_no
        cel_volt_01                -> cv_1
    """

    __tablename__ = "monitoring_battery_sample"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # ESS / Site 식별 정보
    ess_id = Column(String(100), nullable=False)
    site_id = Column(String(100), nullable=True)

    # 배터리 계층 구조
    bank_no = Column(Integer, nullable=True)
    rack_no = Column(Integer, nullable=False)
    string_no = Column(Integer, nullable=True)
    module_no = Column(Integer, nullable=True)

    # 실제 센서 측정 시간
    measured_at = Column(DateTime, nullable=False)

    # Cell voltage
    cv_1 = Column(Float, nullable=True)
    cv_2 = Column(Float, nullable=True)
    cv_3 = Column(Float, nullable=True)
    cv_4 = Column(Float, nullable=True)
    cv_5 = Column(Float, nullable=True)
    cv_6 = Column(Float, nullable=True)
    cv_7 = Column(Float, nullable=True)
    cv_8 = Column(Float, nullable=True)
    cv_9 = Column(Float, nullable=True)
    cv_10 = Column(Float, nullable=True)
    cv_11 = Column(Float, nullable=True)
    cv_12 = Column(Float, nullable=True)
    cv_13 = Column(Float, nullable=True)
    cv_14 = Column(Float, nullable=True)
    cv_15 = Column(Float, nullable=True)
    cv_16 = Column(Float, nullable=True)
    cv_17 = Column(Float, nullable=True)
    cv_18 = Column(Float, nullable=True)
    cv_19 = Column(Float, nullable=True)
    cv_20 = Column(Float, nullable=True)

    # 선택 센서 값
    temperature = Column(Float, nullable=True)
    current_a = Column(Float, nullable=True)
    voltage_v = Column(Float, nullable=True)
    soc = Column(Float, nullable=True)

    # DB 저장/수정 시간
    inserted = Column(DateTime, nullable=False, server_default=func.now())
    updated = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class AnomalyScore(Base):
    """AI 이상 점수 결과 테이블

    AI 모델이 계산한 Rack별 Cell 이상 점수를 저장한다.

    현재 구조:
        - Rack 1개당 row 1개
        - sc_c1 ~ sc_c20: Cell별 이상 점수
        - DB 저장값은 0.0 ~ 1.0 범위
        - API 응답 시 0 ~ 100점으로 변환
    """

    __tablename__ = "anomaly_score"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    rack_idx = Column(Integer, nullable=False)

    sc_c1 = Column(Float, nullable=False)
    sc_c2 = Column(Float, nullable=False)
    sc_c3 = Column(Float, nullable=False)
    sc_c4 = Column(Float, nullable=False)
    sc_c5 = Column(Float, nullable=False)
    sc_c6 = Column(Float, nullable=False)
    sc_c7 = Column(Float, nullable=False)
    sc_c8 = Column(Float, nullable=False)
    sc_c9 = Column(Float, nullable=False)
    sc_c10 = Column(Float, nullable=False)
    sc_c11 = Column(Float, nullable=False)
    sc_c12 = Column(Float, nullable=False)
    sc_c13 = Column(Float, nullable=False)
    sc_c14 = Column(Float, nullable=False)
    sc_c15 = Column(Float, nullable=False)
    sc_c16 = Column(Float, nullable=False)
    sc_c17 = Column(Float, nullable=False)
    sc_c18 = Column(Float, nullable=False)
    sc_c19 = Column(Float, nullable=False)
    sc_c20 = Column(Float, nullable=False)

    date = Column(Date, nullable=False)

    inserted = Column(DateTime, nullable=False, server_default=func.now())
    updated = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class PipelineRunLog(Base):
    """AI 파이프라인 실행 이력 테이블

    AI 파이프라인이 실행될 때마다 실행 정보를 기록한다.

    기록 목적:
        - 언제 실행됐는지 확인
        - 어떤 ESS / 날짜 데이터를 처리했는지 확인
        - 몇 건을 수집하고 몇 건을 저장했는지 확인
        - Parquet 파일이 어디에 저장됐는지 추적
        - 실패 시 에러 메시지 확인

    status 값:
        - running: 실행 중
        - success: 성공
        - error: 실패
        - skipped: 이전 작업 실행 중이라 생략
    """

    __tablename__ = "pipeline_run_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    ess_id = Column(String(100), nullable=False)
    target_date = Column(Date, nullable=False)

    started_at = Column(DateTime, nullable=False, server_default=func.now())
    finished_at = Column(DateTime, nullable=True)

    status = Column(String(20), nullable=False)

    battery_count = Column(Integer, nullable=False, default=0)
    saved_score_count = Column(Integer, nullable=False, default=0)
    deleted_preprocessed_count = Column(Integer, nullable=False, default=0)

    raw_file_path = Column(Text, nullable=True)
    preprocessed_file_path = Column(Text, nullable=True)
    result_file_path = Column(Text, nullable=True)

    message = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    inserted = Column(DateTime, nullable=False, server_default=func.now())
    updated = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())