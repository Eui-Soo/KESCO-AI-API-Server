CREATE USER keri with password 'keri';

CREATE DATABASE keri_digitaltwin owner keri;

grant all privileges on database keri_digitaltwin to keri;

commit;


-- ============================================================
-- battery 테이블 백데이터 삽입
-- 오늘 날짜 기준 1시간 간격 × 4 Rack = 24 × 4 = 96건
-- total_racks: 4  /  index: 1~4  /  cv_1~cv_20: 3.50~3.80V
-- ============================================================
INSERT INTO battery (
    total_racks, index,
    cv_1,  cv_2,  cv_3,  cv_4,  cv_5,
    cv_6,  cv_7,  cv_8,  cv_9,  cv_10,
    cv_11, cv_12, cv_13, cv_14, cv_15,
    cv_16, cv_17, cv_18, cv_19, cv_20,
    date, inserted, updated
)
SELECT
    4                                           AS total_racks,
    rack_idx                                    AS index,
    ROUND((3.50 + random() * 0.30)::NUMERIC, 3) AS cv_1,
    ROUND((3.50 + random() * 0.30)::NUMERIC, 3) AS cv_2,
    ROUND((3.50 + random() * 0.30)::NUMERIC, 3) AS cv_3,
    ROUND((3.50 + random() * 0.30)::NUMERIC, 3) AS cv_4,
    ROUND((3.50 + random() * 0.30)::NUMERIC, 3) AS cv_5,
    ROUND((3.50 + random() * 0.30)::NUMERIC, 3) AS cv_6,
    ROUND((3.50 + random() * 0.30)::NUMERIC, 3) AS cv_7,
    ROUND((3.50 + random() * 0.30)::NUMERIC, 3) AS cv_8,
    ROUND((3.50 + random() * 0.30)::NUMERIC, 3) AS cv_9,
    ROUND((3.50 + random() * 0.30)::NUMERIC, 3) AS cv_10,
    ROUND((3.50 + random() * 0.30)::NUMERIC, 3) AS cv_11,
    ROUND((3.50 + random() * 0.30)::NUMERIC, 3) AS cv_12,
    ROUND((3.50 + random() * 0.30)::NUMERIC, 3) AS cv_13,
    ROUND((3.50 + random() * 0.30)::NUMERIC, 3) AS cv_14,
    ROUND((3.50 + random() * 0.30)::NUMERIC, 3) AS cv_15,
    ROUND((3.50 + random() * 0.30)::NUMERIC, 3) AS cv_16,
    ROUND((3.50 + random() * 0.30)::NUMERIC, 3) AS cv_17,
    ROUND((3.50 + random() * 0.30)::NUMERIC, 3) AS cv_18,
    ROUND((3.50 + random() * 0.30)::NUMERIC, 3) AS cv_19,
    ROUND((3.50 + random() * 0.30)::NUMERIC, 3) AS cv_20,
    t                                           AS date,
    t                                           AS inserted,
    t                                           AS updated
FROM generate_series(
    CURRENT_DATE,
    CURRENT_DATE + INTERVAL '23 hours',
    INTERVAL '1 hour'
) AS t
CROSS JOIN generate_series(1, 4) AS rack_idx
ORDER BY t, rack_idx;


-- ============================================================
-- monitoring_battery_sample 개발용 샘플 데이터
-- 실제 운영에서는 관제시스템 DB 원본 테이블을 조회하므로,
-- 이 테이블은 로컬 개발/테스트 및 컬럼 매핑 기준용으로 사용한다.
-- ============================================================

INSERT INTO monitoring_battery_sample (
    ess_id,
    site_id,
    bank_no,
    rack_no,
    string_no,
    module_no,
    measured_at,
    cv_1, cv_2, cv_3, cv_4, cv_5,
    cv_6, cv_7, cv_8, cv_9, cv_10,
    cv_11, cv_12, cv_13, cv_14, cv_15,
    cv_16, cv_17, cv_18, cv_19, cv_20,
    temperature,
    current_a,
    voltage_v,
    soc
)
VALUES
(
    'KESCO_ESS_001',
    'SITE_001',
    1,
    1,
    1,
    1,
    '2026-05-27 00:00:00',
    3.612, 3.615, 3.611, 3.613, 3.614,
    3.610, 3.616, 3.612, 3.613, 3.615,
    3.614, 3.611, 3.612, 3.613, 3.614,
    3.615, 3.613, 3.612, 3.611, 3.614,
    27.5,
    12.3,
    722.5,
    64.2
),
(
    'KESCO_ESS_001',
    'SITE_001',
    1,
    2,
    1,
    1,
    '2026-05-27 00:00:00',
    3.622, 3.621, 3.620, 3.623, 3.624,
    3.621, 3.625, 3.620, 3.622, 3.623,
    3.624, 3.621, 3.622, 3.623, 3.620,
    3.621, 3.624, 3.622, 3.623, 3.621,
    28.1,
    11.8,
    724.1,
    65.0
),
(
    'KESCO_ESS_001',
    'SITE_001',
    1,
    1,
    1,
    1,
    '2026-05-27 00:01:00',
    3.613, 3.616, 3.612, 3.614, 3.615,
    3.611, 3.617, 3.613, 3.614, 3.616,
    3.615, 3.612, 3.613, 3.614, 3.615,
    3.616, 3.614, 3.613, 3.612, 3.615,
    27.6,
    12.1,
    722.7,
    64.3
),
(
    'KESCO_ESS_001',
    'SITE_001',
    1,
    2,
    1,
    1,
    '2026-05-27 00:01:00',
    3.623, 3.622, 3.621, 3.624, 3.625,
    3.622, 3.626, 3.621, 3.623, 3.624,
    3.625, 3.622, 3.623, 3.624, 3.621,
    3.622, 3.625, 3.623, 3.624, 3.622,
    28.2,
    11.6,
    724.3,
    65.1
);