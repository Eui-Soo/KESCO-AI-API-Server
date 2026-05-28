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