import html
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / 'instance' / 'compatibilitymatch.db'
OUTPUT = ROOT / 'instance' / 'company_financials_explained.html'
METRICS = [
    ('revenue', 'الإيرادات'), ('net_income', 'صافي الربح أو الخسارة'),
    ('total_assets', 'إجمالي الأصول'), ('total_liabilities', 'إجمالي الالتزامات'),
    ('current_assets', 'الأصول المتداولة'), ('current_liabilities', 'الالتزامات المتداولة'),
    ('market_cap', 'القيمة السوقية'),
]

def render_metric(value):
    if value is None:
        return 'لا توجد قيمة أو ملاحظة مسجلة'
    try:
        return f'{float(value):,.0f} ريال'
    except (ValueError, TypeError):
        return str(value)

with sqlite3.connect(DB) as conn:
    conn.row_factory = sqlite3.Row
    rows = conn.execute('SELECT * FROM company_financials_explained ORDER BY symbol').fetchall()

numeric_counts = {}
for key, _ in METRICS:
    numeric_counts[key] = 0
    for row in rows:
        try:
            float(row[key])
            numeric_counts[key] += 1
        except (ValueError, TypeError):
            pass

cards = []
for row in rows:
    metrics = ''.join(
        f'<div class="metric"><span>{html.escape(label)}</span><strong>{html.escape(render_metric(row[key]))}</strong></div>'
        for key, label in METRICS
    )
    source = row['financial_source_url']
    source_html = (
        f'<a href="{html.escape(source, quote=True)}" target="_blank" rel="noreferrer">فتح المصدر الرسمي</a>'
        if source else '<span class="muted">لم يُسجل مصدر رسمي لهذه الشركة بعد</span>'
    )
    searchable = html.escape(f"{row['symbol']} {row['company_name']}", quote=True)
    cards.append(
        f'<article class="company" data-search="{searchable}">'
        f'<div class="company-head"><div><span class="symbol">{html.escape(str(row["symbol"]))}</span>'
        f'<h2>{html.escape(str(row["company_name"]))}</h2></div>'
        f'<span class="year">السنة المالية {html.escape(str(row["period_year"]))}</span></div>'
        f'<div class="metrics">{metrics}</div>'
        f'<div class="status">{html.escape(str(row["record_status"] or "لا توجد حالة مسجلة"))}</div>'
        f'<div class="source">{source_html}</div></article>'
    )

counts = ''.join(
    f'<div class="count"><b>{numeric_counts[key]} / {len(rows)}</b><span>{html.escape(label)} لها أرقام موثقة</span></div>'
    for key, label in METRICS
)
page = f'''<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>كل البيانات المالية المشروحة</title><style>
:root{{--navy:#102846;--blue:#1976d2;--bg:#f3f6fb;--line:#dbe4ef}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);font:15px/1.75 Segoe UI,Tahoma,Arial;color:#18324f}}header{{background:var(--navy);color:#fff;padding:24px clamp(16px,4vw,48px)}}h1{{margin:0 0 5px;font-size:26px}}header p{{margin:0;color:#d9e8fa}}main{{padding:22px clamp(12px,3vw,36px)}}.counts{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin-bottom:16px}}.count,.company{{background:#fff;border:1px solid var(--line);border-radius:12px}}.count{{padding:11px 14px}}.count b{{display:block;color:var(--blue);font-size:19px}}.count span{{font-size:13px}}.notice{{background:#eaf3ff;border-right:4px solid var(--blue);padding:12px 15px;border-radius:8px;margin:14px 0}}input{{width:min(440px,100%);padding:11px 14px;border:1px solid #b8c9dc;border-radius:8px;margin:0 0 14px;font:inherit}}#companies{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,520px),1fr));gap:14px}}.company{{padding:15px;min-width:0}}.company-head{{display:flex;justify-content:space-between;align-items:start;gap:10px;border-bottom:1px solid var(--line);padding-bottom:10px;margin-bottom:11px}}h2{{font-size:18px;margin:1px 0}}.symbol{{font-size:12px;color:#60748d}}.year{{white-space:nowrap;color:#506982;font-size:13px}}.metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:8px}}.metric{{background:#f6f9fd;border-radius:8px;padding:9px 10px;min-height:69px}}.metric span{{display:block;color:#5f7187;font-size:13px}}.metric strong{{display:block;font-size:14px;font-weight:600;overflow-wrap:anywhere}}.status{{margin-top:10px;color:#455d78;font-size:13px}}.source{{margin-top:5px;font-size:13px}}a{{color:#075eaa}}.muted{{color:#7b8795}}footer{{padding:18px 4vw;color:#66758a;font-size:13px}}
</style><header><h1>كل البيانات المالية المشروحة</h1><p>كل المؤشرات السبعة لكل شركة — من قاعدة SQLite، مع تفسير الحقول التي لا تتوفر لها أرقام موثقة.</p></header><main><div class="counts">{counts}</div><div class="notice">الأرقام المتاحة مرتبطة بمصادرها الرسمية. النص في خانة المؤشر يوضح سبب غياب القيمة حين لم تُستورد من مصدر رسمي. ملخص التغطية أعلاه يبيّن عدد الشركات التي لها رقم فعلي لكل مؤشر.</div><input id="q" placeholder="ابحث باسم الشركة أو الرمز" oninput="filterCards()"><section id="companies">{''.join(cards)}</section></main><footer>ملف SQLite: TuwaiqProject/instance/compatibilitymatch.db — الفترة المعروضة FY2025 — العملة: الريال السعودي بحسب مصادر البيانات.</footer><script>function filterCards(){{const q=document.getElementById('q').value.toLowerCase();document.querySelectorAll('.company').forEach(c=>c.hidden=!c.dataset.search.toLowerCase().includes(q))}}</script></html>'''
OUTPUT.write_text(page, encoding='utf-8')
print(f'Created {OUTPUT}; companies={len(rows)}; coverage={numeric_counts}')
