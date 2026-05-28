"""이상 점수 모델"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Float, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base


class AnomalyScore(Base):
    """이상 점수 테이블"""
    __tablename__ = 'anomaly_score'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    rack_idx: Mapped[int] = mapped_column(Integer, nullable=False)
    sc_c1: Mapped[float] = mapped_column(Float, nullable=False)
    sc_c2: Mapped[float] = mapped_column(Float, nullable=False)
    sc_c3: Mapped[float] = mapped_column(Float, nullable=False)
    sc_c4: Mapped[float] = mapped_column(Float, nullable=False)
    sc_c5: Mapped[float] = mapped_column(Float, nullable=False)
    sc_c6: Mapped[float] = mapped_column(Float, nullable=False)
    sc_c7: Mapped[float] = mapped_column(Float, nullable=False)
    sc_c8: Mapped[float] = mapped_column(Float, nullable=False)
    sc_c9: Mapped[float] = mapped_column(Float, nullable=False)
    sc_c10: Mapped[float] = mapped_column(Float, nullable=False)
    sc_c11: Mapped[float] = mapped_column(Float, nullable=False)
    sc_c12: Mapped[float] = mapped_column(Float, nullable=False)
    sc_c13: Mapped[float] = mapped_column(Float, nullable=False)
    sc_c14: Mapped[float] = mapped_column(Float, nullable=False)
    sc_c15: Mapped[float] = mapped_column(Float, nullable=False)
    sc_c16: Mapped[float] = mapped_column(Float, nullable=False)
    sc_c17: Mapped[float] = mapped_column(Float, nullable=False)
    sc_c18: Mapped[float] = mapped_column(Float, nullable=False)
    sc_c19: Mapped[float] = mapped_column(Float, nullable=False)
    sc_c20: Mapped[float] = mapped_column(Float, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    inserted: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class BAT(Base):
    """원격 DB 배터리 테이블"""
    __tablename__ = 'battery'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    total_racks: Mapped[int] = mapped_column(Integer, nullable=False)
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    cv_1: Mapped[float] = mapped_column(Float, nullable=False)
    cv_2: Mapped[float] = mapped_column(Float, nullable=False)
    cv_3: Mapped[float] = mapped_column(Float, nullable=False)
    cv_4: Mapped[float] = mapped_column(Float, nullable=False)
    cv_5: Mapped[float] = mapped_column(Float, nullable=False)
    cv_6: Mapped[float] = mapped_column(Float, nullable=False)
    cv_7: Mapped[float] = mapped_column(Float, nullable=False)
    cv_8: Mapped[float] = mapped_column(Float, nullable=False)
    cv_9: Mapped[float] = mapped_column(Float, nullable=False)
    cv_10: Mapped[float] = mapped_column(Float, nullable=False)
    cv_11: Mapped[float] = mapped_column(Float, nullable=False)
    cv_12: Mapped[float] = mapped_column(Float, nullable=False)
    cv_13: Mapped[float] = mapped_column(Float, nullable=False)
    cv_14: Mapped[float] = mapped_column(Float, nullable=False)
    cv_15: Mapped[float] = mapped_column(Float, nullable=False)
    cv_16: Mapped[float] = mapped_column(Float, nullable=False)
    cv_17: Mapped[float] = mapped_column(Float, nullable=False)
    cv_18: Mapped[float] = mapped_column(Float, nullable=False)
    cv_19: Mapped[float] = mapped_column(Float, nullable=False)
    cv_20: Mapped[float] = mapped_column(Float, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    inserted: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
