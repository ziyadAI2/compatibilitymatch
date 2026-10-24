import html
import sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'instance'/'compatibilitymatch.db'
OUT=ROOT/'instance'/'market_context.html'
with sqlite3.connect(DB) as c:
 c.row_factory=sqlite3.Row
 rows=c.execute('SELECT * FROM market_context_indicators ORDER BY metric_code, sector').fetchall()
source=rows[0]['source_url'] if rows else '#'
totals=[r for r in rows if r['sector']=='الاقتصاد السعودي']
shares=[r for r in rows if r['sector']!='الاقتصاد السعودي']
def fmt(v):return f'{v:,.1f}'
summary=''.join(f'<div class="card"><b>{fmt(r["value"])} {html.escape(r["unit"])}</b><span>{html.escape(r["metric_name"])}</span></div>' for r in totals)
body=''.join(f'<tr><td>{html.escape(r["metric_name"])}</td><td>{html.escape(r["sector"])}</td><td>{r["period_year"]}</td><td>{fmt(r["value"])}</td><td>{html.escape(r["unit"])}</td></tr>' for r in shares)
page=f'''<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>بيانات السوق الرسمية</title><style>:root{{--n:#102846;--b:#1976d2;--bg:#f3f6fb;--l:#dbe4ef}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);font:15px/1.7 Segoe UI,Tahoma,Arial;color:#18324f}}header{{background:var(--n);color:white;padding:24px clamp(16px,4vw,48px)}}h1{{margin:0 0 5px;font-size:25px}}main{{padding:22px clamp(12px,3vw,36px)}}.notice{{background:#eaf3ff;border-right:4px solid var(--b);padding:12px 16px;border-radius:8px;margin-bottom:18px}}.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin:14px 0 24px}}.card{{background:white;border:1px solid var(--l);border-radius:12px;padding:14px}}.card b{{display:block;color:var(--b);font-size:21px}}.card span{{font-size:13px}}h2{{margin-top:24px}}.wrap{{overflow:auto;background:white;border:1px solid var(--l);border-radius:10px}}table{{border-collapse:collapse;width:100%;min-width:680px}}th,td{{border-bottom:1px solid var(--l);padding:10px 12px;text-align:right}}th{{background:#e8eff8;color:var(--n)}}a{{color:#075eaa}}footer{{padding:18px;color:#66758a;font-size:13px}}</style><header><h1>بيانات السوق الرسمية حسب النشاط الاقتصادي</h1><div>قاعدة SQLite — مؤشرات مجمعة منشورة من الهيئة العامة للإحصاء</div></header><main><div class="notice">هذه إحصاءات على مستوى الاقتصاد والقطاعات، وليست أرقامًا لشركة محددة ولا تُستخدم بديلًا عن قوائم الشركات. السنة المتاحة في هذا الاستيراد هي 2024، والأرقام مقربة كما وردت في النشرة.</div><h2>الإجماليات الوطنية</h2><div class="cards">{summary}</div><h2>توزيع الإيرادات والمصروفات حسب النشاط</h2><div class="wrap"><table><thead><tr><th>المؤشر</th><th>النشاط</th><th>السنة</th><th>القيمة</th><th>الوحدة</th></tr></thead><tbody>{body}</tbody></table></div><p><a href="{html.escape(source,quote=True)}" target="_blank" rel="noreferrer">فتح نشرة الهيئة العامة للإحصاء الرسمية</a></p></main><footer>عدد السجلات: {len(rows)} — جميعها موسومة غير اصطناعية في قاعدة البيانات.</footer></html>'''
OUT.write_text(page,encoding='utf-8')
print(OUT,'records=',len(rows))
