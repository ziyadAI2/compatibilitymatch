-- استعراض توضيحي شفاف لنتائج محرك التوافق في قاعدة المشروع.
-- كل الاستعلامات للقراءة فقط. لا تمثل النتائج وجود شراكة فعلية.

-- 1) التحليلات المحفوظة، درجة النتيجة، وعدد معاييرها/توصياتها.
SELECT
    a.id AS analysis_id,
    ca.official_name AS company_a,
    cb.official_name AS company_b,
    a.analysis_type,
    a.mode,
    a.scoring_version,
    json_extract(a.report_json, '$.scores.overall_score') AS overall_score,
    json_extract(a.report_json, '$.scores.confidence') AS confidence,
    (SELECT COUNT(*) FROM compatibility_scores s WHERE s.analysis_id = a.id) AS criteria_rows,
    (SELECT COUNT(*) FROM recommendations r WHERE r.analysis_id = a.id) AS recommendation_rows,
    a.created_at
FROM analyses a
JOIN companies ca ON ca.id = a.company_a_id
LEFT JOIN companies cb ON cb.id = a.company_b_id
ORDER BY a.id;

-- 2) تفاصيل معايير المقارنة المحفوظة: الدرجة والوزن والثقة والتفسير والدليل.
SELECT
    s.analysis_id,
    s.criterion,
    s.score,
    s.weight,
    s.confidence,
    s.explanation,
    s.evidence
FROM compatibility_scores s
WHERE s.analysis_id = 1
ORDER BY s.weight DESC;

-- 3) المرشحون الخمسة الأوائل في استكشاف أرامكو (تحليل الاكتشاف رقم 2).
SELECT
    r.analysis_id,
    r.rank,
    c.official_name AS candidate,
    c.symbol,
    r.overall_score,
    r.confidence,
    r.why,
    r.risks,
    r.limitations
FROM recommendations r
JOIN companies c ON c.id = r.candidate_company_id
WHERE r.analysis_id = 2
ORDER BY r.rank;
