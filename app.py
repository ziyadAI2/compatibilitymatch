from __future__ import annotations
import json, os, sqlite3, time, urllib.request, urllib.error
from contextlib import contextmanager
from datetime import datetime, date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse, quote

BASE = Path(__file__).parent
DB = Path(os.getenv('CM_DATABASE', BASE / 'compatibilitymatch.db'))

@contextmanager
def connect():
    db=sqlite3.connect(DB); db.row_factory=sqlite3.Row
    try:
        yield db; db.commit()
    except Exception:
        db.rollback(); raise
    finally: db.close()

def init_db():
    with connect() as d:
        d.executescript('''CREATE TABLE IF NOT EXISTS companies(id INTEGER PRIMARY KEY,name TEXT,sector TEXT,description TEXT,products TEXT,revenue REAL,net_income REAL,assets REAL,liabilities REAL,provenance TEXT,source TEXT,ticker TEXT,source_date TEXT);
        CREATE TABLE IF NOT EXISTS analyses(id INTEGER PRIMARY KEY,company_a INTEGER,company_b INTEGER,kind TEXT,score REAL,confidence TEXT,report TEXT,created TEXT);
        CREATE TABLE IF NOT EXISTS relationships(id INTEGER PRIMARY KEY,name TEXT,company_a INTEGER,company_b INTEGER,kind TEXT,start_date TEXT,status TEXT,simulated INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS kpis(id INTEGER PRIMARY KEY,relationship_id INTEGER,name TEXT,target REAL,unit TEXT,direction TEXT,period TEXT,actual REAL,updated TEXT);
        CREATE TABLE IF NOT EXISTS milestones(id INTEGER PRIMARY KEY,relationship_id INTEGER,name TEXT,due TEXT,status TEXT);
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,kind TEXT,status TEXT,latency REAL,detail TEXT,created TEXT);''')
        columns={row['name'] for row in d.execute('PRAGMA table_info(companies)')}
        if 'ticker' not in columns: d.execute('ALTER TABLE companies ADD COLUMN ticker TEXT')
        if 'source_date' not in columns: d.execute('ALTER TABLE companies ADD COLUMN source_date TEXT')
        if d.execute('SELECT count(*) FROM companies').fetchone()[0]==0:
            rows=[('نموذج شركة الطاقة','الطاقة','تطوير حلول الطاقة المتجددة والتخزين للشركات.','ألواح شمسية، تخزين',None,None,None,None,'بيانات توضيحية مولدة',''),('نموذج شركة التقنية','تقنية المعلومات','منصة برمجية لإدارة استهلاك الطاقة وتحليل البيانات.','تحليلات، برمجيات',None,None,None,None,'بيانات توضيحية مولدة',''),('نموذج شركة الخدمات','الخدمات الصناعية','تنفيذ وصيانة المشاريع الصناعية والبنية التحتية.','صيانة، تنفيذ',None,None,None,None,'بيانات توضيحية مولدة',''),('نموذج شركة التمويل','الخدمات المالية','حلول تمويل أعمال للشركات الصغيرة والمتوسطة.','تمويل، استشارات',None,None,None,None,'بيانات توضيحية مولدة','')]
            d.executemany('INSERT INTO companies(name,sector,description,products,revenue,net_income,assets,liabilities,provenance,source) VALUES(?,?,?,?,?,?,?,?,?,?)',rows)
            d.execute("INSERT INTO relationships(name,company_a,company_b,kind,start_date,status,simulated) VALUES('شراكة تجريبية للطاقة الذكية',1,2,'partnership','2026-01-01','Active - simulated',1)")
            rid=d.execute('SELECT last_insert_rowid()').fetchone()[0]
            for period,target,actual in [('2026-01',1000000,800000),('2026-02',1000000,920000),('2026-03',1000000,650000)]:
                d.execute('INSERT INTO kpis(relationship_id,name,target,unit,direction,period,actual,updated) VALUES(?,?,?,?,?,?,?,?)',(rid,'إيرادات من الشراكة',target,'SAR','higher',period,actual,datetime.utcnow().isoformat()))
            d.execute("INSERT INTO milestones(relationship_id,name,due,status) VALUES(?,?,?,?)",(rid,'إطلاق تجربة العميل','2026-11-15','In progress'))
        official=[
            ('أكوا باور (ACWA Power)','الطاقة والمياه','شركة سعودية مدرجة تعمل في تطوير واستثمار وتشغيل مشاريع توليد الطاقة، بما في ذلك الطاقة المتجددة، وتحلية المياه، والهيدروجين الأخضر.','الطاقة المتجددة، تحلية المياه، الهيدروجين الأخضر، توليد الطاقة','شركة مدرجة - مصدر رسمي','https://www.acwapower.com/en/who-we-are/about-us/','2082','صفحة الشركة الرسمية؛ تحقق 2026-10-21'),
            ('الشركة السعودية للاتصالات (stc)','الاتصالات والتقنية','تقدم مجموعة stc خدمات الاتصالات وتقنية المعلومات والإعلام والمدفوعات الرقمية، وتشمل أنشطتها الشبكات الثابتة والمتنقلة والخدمات السحابية وإنترنت الأشياء والأمن السيبراني.','الاتصالات، الشبكات، الخدمات السحابية، إنترنت الأشياء، الأمن السيبراني، تقنية المعلومات','شركة مدرجة - مصدر رسمي','https://www.stc.com.sa/content/dam/stc/stc-annual-report-2024/about-stc.html','7010','التقرير السنوي 2024؛ تحقق 2026-10-21')]
        for row in official:
            if not d.execute('SELECT 1 FROM companies WHERE ticker=? LIMIT 1',(row[6],)).fetchone():
                d.execute('INSERT INTO companies(name,sector,description,products,provenance,source,ticker,source_date) VALUES(?,?,?,?,?,?,?,?)',row)
        # Repair duplicate official rows created by earlier non-idempotent app starts.
        for ticker in ('2082','7010'):
            ids=[r['id'] for r in d.execute('SELECT id FROM companies WHERE ticker=? ORDER BY id',(ticker,))]
            if len(ids)>1:
                keep=ids[0]
                for duplicate in ids[1:]:
                    for table in ('analyses','relationships'):
                        for column in ('company_a','company_b'):
                            d.execute(f'UPDATE {table} SET {column}=? WHERE {column}=?',(keep,duplicate))
                    d.execute('DELETE FROM companies WHERE id=?',(duplicate,))
        d.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_companies_ticker_unique ON companies(ticker) WHERE ticker IS NOT NULL")

def score(a,b,kind):
    # Reproducible rubric: text-sector complementarity and available financial evidence only.
    sector= 82 if a['sector']!=b['sector'] else 52
    text= min(90, 45+len(set(a['products'].split(', ')) ^ set(b['products'].split(', ')))*8)
    parts=[('تكامل القطاعات',sector,0.55),('تكامل المنتجات',text,0.45)]
    if kind=='investment':
        parts=[('الملاءمة الاستراتيجية',sector,.4),('توفر البيانات المالية',70 if b['revenue'] is not None else 0,.6)]
    elif kind=='joint_venture': parts=[('تكامل الموارد',sector,.4),('تكامل المنتجات',text,.35),('القدرة المالية المتاحة',70 if a['revenue'] is not None and b['revenue'] is not None else 35,.25)]
    value=round(sum(s*w for _,s,w in parts),1)
    return value,parts

def ai_explain(a,b,kind,parts):
    prompt={'task':'Explain business compatibility. Use only facts in the supplied records. Never invent financial facts, existing contracts, or partnership outcomes. Clearly label interpretations. Return JSON with summary (string), opportunities (array of strings), risks (array of strings), and evidence (array of strings).','kind':kind,'company_a':dict(a),'company_b':dict(b),'score_components':parts}
    gemini_key=os.getenv('GEMINI_API_KEY')
    openai_key=os.getenv('OPENAI_API_KEY')
    if not gemini_key and not openai_key:
        if (a['ticker'],b['ticker']) in [('2082','7010'),('7010','2082')]:
            return {'mode':'Demo Mode','summary':'استنتاج تحليلي أولي: نشاط أكوا باور في أصول الطاقة والمياه قد يتكامل مع خبرات stc في الاتصالات وتقنية المعلومات. يمكن بحث اتصال آمن وإنترنت الأشياء لمراقبة الأصول عن بعد؛ هذا احتمال مقترح وليس شراكة قائمة أو معلومة عن طلب فعلي.','opportunities':['بحث حلول اتصال وإنترنت الأشياء وتحليلات تشغيلية لمرافق الطاقة والمياه، بعد التحقق من الاحتياج والجدوى لدى الطرفين.'],'risks':['لا تتوفر هنا معلومات عن خطة أو عقد قائم بين الشركتين، أو جدوى فنية وتجارية خاصة بالمشروع.','البيانات المالية والتقييم السوقي غير مضمنة في هذه المقارنة.'],'evidence':[a['description'],b['description']]}
        return {'mode':'Demo Mode','summary':f"تفسير توضيحي مبني على بيانات السجل: يوجد اختلاف قطاعي بين {a['name']} و{b['name']}؛ يمكن استكشاف تكامل النشاطين. لا يمثل ذلك تحققاً من فرصة فعلية.",'opportunities':['استكشاف تكامل الحلول والمنتجات المسجلة'],'risks':['البيانات المالية غير متاحة؛ يلزم التحقق من الملاءمة التجارية والتشغيلية'],'evidence':[a['description'],b['description']]}
    schema={'type':'object','properties':{'summary':{'type':'string'},'opportunities':{'type':'array','items':{'type':'string'}},'risks':{'type':'array','items':{'type':'string'}},'evidence':{'type':'array','items':{'type':'string'}}},'required':['summary','opportunities','risks','evidence']}
    try:
        if gemini_key:
            model=os.getenv('GEMINI_MODEL','gemini-3.6-flash')
            url='https://generativelanguage.googleapis.com/v1beta/models/'+quote(model,safe='')+':generateContent'
            body={'contents':[{'role':'user','parts':[{'text':json.dumps(prompt,ensure_ascii=False)}]}], 'generationConfig':{'responseFormat':{'text':{'mimeType':'application/json','schema':schema}}}}
            req=urllib.request.Request(url,data=json.dumps(body,ensure_ascii=False).encode('utf-8'),headers={'x-goog-api-key':gemini_key,'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=20) as resp:
                response=json.loads(resp.read())
            pieces=response['candidates'][0]['content']['parts']
            raw=''.join(part.get('text','') for part in pieces if isinstance(part,dict))
            result=json.loads(raw)
            mode='Gemini API'
        else:
            model=os.getenv('OPENAI_MODEL','gpt-4o-mini')
            body={'model':model,'response_format':{'type':'json_object'},'messages':[{'role':'user','content':json.dumps(prompt,ensure_ascii=False)}]}
            req=urllib.request.Request('https://api.openai.com/v1/chat/completions',data=json.dumps(body,ensure_ascii=False).encode('utf-8'),headers={'Authorization':'Bearer '+openai_key,'Content-Type':'application/json'})
            with urllib.request.urlopen(req,timeout=20) as resp:
                response=json.loads(resp.read())
            result=json.loads(response['choices'][0]['message']['content'])
            mode='OpenAI API'
        if not isinstance(result,dict) or not isinstance(result.get('summary'),str) or not all(isinstance(result.get(key),list) and all(isinstance(item,str) for item in result[key]) for key in ('opportunities','risks','evidence')):
            raise ValueError('AI response did not match the required JSON structure')
        return {'mode':mode,'result':result}
    except Exception as e:
        provider='Gemini' if gemini_key else 'OpenAI'
        raise RuntimeError(provider+' API error: '+str(e))

def record(kind,status,latency,detail):
    with connect() as d: d.execute('INSERT INTO events(kind,status,latency,detail,created) VALUES(?,?,?,?,?)',(kind,status,latency,detail,datetime.utcnow().isoformat()))

def achievement(target,actual,direction):
    if target is None or actual is None or target==0: return None
    if direction=='lower': return round(min(200, target/actual*100) if actual else 200,1)
    return round(actual/target*100,1)

def dashboard():
    with connect() as d:
        companies=[dict(x) for x in d.execute('SELECT * FROM companies')]
        rels=[dict(x) for x in d.execute('SELECT r.*,a.name a_name,b.name b_name FROM relationships r JOIN companies a ON a.id=r.company_a JOIN companies b ON b.id=r.company_b')]
        analyses=[dict(x) for x in d.execute('SELECT * FROM analyses ORDER BY id DESC LIMIT 10')]
        events=[dict(x) for x in d.execute('SELECT * FROM events ORDER BY id DESC LIMIT 30')]
        kpis=[dict(x) for x in d.execute('SELECT k.*,r.name relationship FROM kpis k JOIN relationships r ON r.id=k.relationship_id ORDER BY k.id DESC')]
    return companies,rels,analyses,events,kpis

HTML='''<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>CompatibilityMatch AI</title><link rel="stylesheet" href="/static/style.css"></head><body><header><div class="brand">◈ CompatibilityMatch <span>AI</span><small>ذكاء الشراكات والاستثمار</small></div><nav><a href="/">الرئيسية</a><a href="#compare">مقارنة الشركات</a><a href="#discover">الاكتشاف الذكي</a><a href="#monitor">مراقبة الشراكات</a><a href="#system">مراقبة النظام</a><a href="#reports">التقارير</a></nav></header><main><section class="hero"><div><p class="eyebrow">منصة ذكاء أعمال سعودية · MVP</p><h1>اكتشف التوافق.<br><em>راقب الأثر.</em></h1><p>دعم قرار قائم على بيانات معلومة، مع متابعة أداء العلاقة بعد اعتمادها.</p><a class="button" href="#compare">ابدأ التحليل ←</a></div><div class="hero-card"><span>نموذج التوافق</span><strong>{{ lastscore or '—' }}<small>/100</small></strong><p>درجة استرشادية · منهجية v1</p><div class="bar"><i style="width:{{ lastscore or 0 }}%"></i></div></div></section>
<div class="notice">وضع العرض: الشركات والعلاقة التجريبية بيانات محاكاة وليست شركات أو نتائج حقيقية. لا تمثل التقييمات توصية استثمارية.</div>
<section class="section" id="compare"><div class="section-head"><div><p class="eyebrow">01 / ANALYZE</p><h2>مقارنة الشركات</h2></div><p>قياس قابل للتفسير، مع فصل الحقائق عن التفسيرات.</p></div><form method="post" action="/analyze" class="panel grid"><label>الشركة أ<select name="a">{% for c in companies if c.ticker %}<option value="{{c.id}}" {% if c.ticker=='2082' %}selected{% endif %}>{{c.name }}{% if c.ticker %} ({{c.ticker}}){% endif %}</option>{% endfor %}</select></label><label>الشركة ب<select name="b">{% for c in companies if c.ticker %}<option value="{{c.id}}" {% if c.ticker=='7010' %}selected{% endif %}>{{c.name }}{% if c.ticker %} ({{c.ticker}}){% endif %}</option>{% endfor %}</select></label><label>نوع العلاقة<select name="kind"><option value="partnership">شراكة استراتيجية</option><option value="investment">تحليل استثمار أسهم</option><option value="joint_venture">مشروع مشترك</option></select></label><button class="button">حلّل التوافق</button></form>{% if report %}<div class="panel result"><div class="score">{{report.score}}<small>/100</small></div><div><h3>{{report.a}} × {{report.b}}</h3><p>{{report.kind_label}} · {{report.ai_mode}}</p><p>{{report.confidence}}</p><p>{{report.summary}}</p><div class="tags">{% for k,v in report.parts %}<span>{{k}}: {{v}}</span>{% endfor %}</div><h4>فرص محتملة ومخاطر</h4><p>{{report.opportunities}} | {{report.risks}}</p><p>مصادر: <a href="{{report.source_a}}" target="_blank">{{report.source_title_a}}</a> · <a href="{{report.source_b}}" target="_blank">{{report.source_title_b}}</a></p></div><a class="button secondary" href="#monitor">إنشاء سجل متابعة</a></div>{% endif %}</section>
<section class="section" id="discover"><div class="section-head"><div><p class="eyebrow">02 / DISCOVER</p><h2>الاكتشاف الذكي</h2></div><p>يعرض الشركات ذات السجلات الموثقة فقط، ولا يغطي السوق كاملاً.</p></div><form method="get" action="/discover" class="panel grid"><label>الشركة<select name="company" required><option value="">اختر الشركة لبدء الاكتشاف</option>{% for c in companies if c.ticker %}<option value="{{c.id}}" {% if discovery_id==c.id %}selected{% endif %}>{{c.name}} ({{c.ticker}})</option>{% endfor %}</select></label><label>نوع العلاقة<select name="kind"><option value="partnership">شراكة</option><option value="investment">استثمار</option><option value="joint_venture">مشروع مشترك</option></select></label><button class="button">اعرض المرشحين</button></form>{% if discovery_error %}<p class="panel">{{discovery_error}}</p>{% endif %}{% if candidates is not none %}<div class="panel"><h3>مرشحون محتملون انطلاقًا من {{discovery_company}}</h3><p>ترتيب أولي في مجموعة البيانات المتاحة، وليس توصية أو شراكة قائمة.</p></div><div class="cards">{% for c in candidates %}<article class="panel"><span class="pill">{{c.score}} / 100</span><h3>{{c.name}}</h3><p>{{c.sector}} · {{c.provenance}}</p><p>ترشيح أولي حسب تكامل القطاع والمنتجات المسجلة.</p></article>{% endfor %}</div>{% endif %}</section>
<section class="section" id="monitor"><div class="section-head"><div><p class="eyebrow">03 / BUSINESS MONITORING</p><h2>مراقبة أداء الشراكات</h2></div><p>بيانات العلاقة تأتي من إدخالات المستخدم؛ لا تُستنتج من إفصاحات السوق.</p></div><div class="cards">{% for r in rels %}<article class="panel"><span class="pill">{{r.status}}</span><h3>{{r.name}}</h3><p>{{r.a_name}} × {{r.b_name}} · {{r.kind}}</p>{% for k in kpis if k.relationship_id==r.id %}<div class="kpi"><b>{{k.name}}</b><span>{{k.actual}} / {{k.target}} {{k.unit}}</span><strong>{{k.achievement}}% · {{k.status}}</strong><div class="bar"><i style="width:{{[k.achievement or 0,100]|min}}%"></i></div></div>{% endfor %}</article>{% endfor %}</div><form method="post" action="/relationship" class="panel grid"><h3>تسجيل علاقة معتمدة</h3><label>اسم العلاقة<input name="name" required></label><label>الشركة أ<select name="a">{% for c in companies %}<option value="{{c.id}}">{{c.name}}</option>{% endfor %}</select></label><label>الشركة ب<select name="b">{% for c in companies %}<option value="{{c.id}}">{{c.name}}</option>{% endfor %}</select></label><label>النوع<select name="kind"><option value="partnership">شراكة استراتيجية</option><option value="investment">استثمار</option><option value="joint_venture">مشروع مشترك</option></select></label><label>تاريخ البداية<input name="start" type="date" required></label><label>حالة الاعتماد<select name="status"><option value="Approved">معتمد</option><option value="Signed">موقع</option></select></label><button class="button">إنشاء سجل العلاقة</button></form><form method="post" action="/kpi" class="panel grid"><h3>إضافة نتيجة KPI شهرية</h3><label>العلاقة<select name="relationship">{% for r in rels %}<option value="{{r.id}}">{{r.name}}</option>{% endfor %}</select></label><label>المؤشر<input name="name" value="إيرادات من الشراكة" required></label><label>الهدف<input name="target" type="number" step="any" required></label><label>الفعلي<input name="actual" type="number" step="any" required></label><label>الوحدة<input name="unit" value="SAR"></label><label>الاتجاه<select name="direction"><option value="higher">الأعلى أفضل</option><option value="lower">الأقل أفضل</option></select></label><label>الفترة<input name="period" type="month" required></label><button class="button">حفظ النتيجة</button></form><div class="panel"><h3>اتجاه الإيرادات الفعلي مقابل الهدف</h3><canvas id="chart" height="100"></canvas></div></section>
<section class="section" id="system"><div class="section-head"><div><p class="eyebrow">04 / TECHNICAL HEALTH</p><h2>مراقبة النظام</h2></div><p>الأرقام مستخرجة من أحداث التطبيق المسجلة فعلياً.</p></div><div class="metrics"><div class="panel"><small>الطلبات المكتملة</small><b>{{metrics.completed}}</b></div><div class="panel"><small>الأخطاء</small><b>{{metrics.failed}}</b></div><div class="panel"><small>متوسط زمن الاستجابة</small><b>{{metrics.latency}} ms</b></div><div class="panel"><small>إجمالي الطلبات</small><b>{{metrics.total}}</b></div></div><form method="post" action="/simulate" class="panel grid"><label>اختبار تشخيصي<select name="test"><option value="timeout">محاكاة تعطل مزود الذكاء الاصطناعي</option><option value="missing">بيانات شركة غير موجودة</option><option value="invalid">إدخال KPI غير صالح</option><option value="delay">طلب تحليل بطيء</option></select></label><button class="button secondary">سجل حدث الاختبار</button></form><div class="panel"><h3>الأحداث الأخيرة</h3>{% for e in events %}<p class="event"><b>{{e.kind}}</b> · {{e.status}} · {{e.latency}}ms · {{e.detail}}</p>{% endfor %}</div></section>
<section class="section" id="reports"><div class="section-head"><div><p class="eyebrow">05 / REPORTS</p><h2>التقارير والمنهجية</h2></div></div><div class="panel"><p><b>المعادلة v1:</b> الشراكة = تكامل القطاع 55% + المنتجات 45%. الاستثمار = الملاءمة 40% + توفر البيانات المالية 60%. المشروع المشترك = تكامل الموارد 40% + المنتجات 35% + بيانات القدرة المالية 25%. عدم توفر البيانات المالية يقلل الملاءمة/الثقة ولا يعوض بأرقام مفترضة.</p><p>مؤشر الثقة يشير إلى اكتمال البيانات: محدود عند غياب البيانات المالية. تحليل الاستثمار اتجاهي من أ إلى ب، ولا يقدم توصية شراء.</p><a href="/api/health">API health JSON</a> · <a href="/api/companies.csv">قالب CSV</a></div></section></main><footer>CompatibilityMatch AI · مشروع جامعي · الإصدار 0.1 · جميع بيانات العرض محاكاة</footer><script src="https://cdn.jsdelivr.net/npm/chart.js"></script><script>const rows={{ chartdata|safe }}; if(window.Chart&&rows.length){new Chart(document.getElementById('chart'),{type:'line',data:{labels:rows.map(x=>x.period),datasets:[{label:'الفعلي',data:rows.map(x=>x.actual),borderColor:'#167dff'},{label:'الهدف',data:rows.map(x=>x.target),borderColor:'#9aa9bc',borderDash:[4,4]}]},options:{responsive:true,plugins:{legend:{position:'bottom'}}}})}</script></body></html>'''

class Handler(BaseHTTPRequestHandler):
    def respond(self,code,body,ctype='text/html; charset=utf-8'):
        self.send_response(code); self.send_header('Content-Type',ctype); self.end_headers(); self.wfile.write(body.encode() if isinstance(body,str) else body)
    def do_GET(self):
        path=urlparse(self.path).path
        if path.startswith('/static/'):
            f=BASE/path.lstrip('/'); return self.respond(200,f.read_bytes(),'text/css; charset=utf-8')
        if path=='/api/health': return self.respond(200,json.dumps({'status':'ok','database':str(DB.name)}),'application/json')
        if path=='/api/companies.csv': return self.respond(200,'name,sector,description,products,revenue,net_income,assets,liabilities,provenance,source\n','text/csv')
        companies,rels,analyses,events,kpis=dashboard()
        for k in kpis:
            k['achievement']=achievement(k['target'],k['actual'],k['direction']); k['status']='On Track' if (k['achievement'] or 0)>=80 else 'Needs Attention'
        total=len(events); done=sum(e['status']=='success' for e in events); failed=total-done
        lat=round(sum(e['latency'] for e in events)/total,1) if total else 0
        params=parse_qs(urlparse(self.path).query); candidates=None; discovery_company=None; discovery_id=None; discovery_error=None
        if path=='/discover':
            verified=[c for c in companies if c.get('ticker')]
            if params.get('company',[''])[0]:
                try: cid=int(params['company'][0])
                except (TypeError,ValueError): cid=None
                anchor=next((c for c in verified if c['id']==cid),None)
                if anchor:
                    discovery_id=anchor['id']; discovery_company=anchor['name']; kind=params.get('kind',['partnership'])[0]; candidates=[]
                    for c in verified:
                        if c['id']!=anchor['id']:
                            val,_=score(anchor,c,kind); candidates.append({'name':c['name'],'sector':c['sector'],'provenance':c['provenance'],'score':val})
                    candidates.sort(key=lambda x:x['score'],reverse=True)
                else: discovery_error='لم يتم العثور على شركة موثقة بهذا الاختيار. اختر شركة من القائمة ثم أعد المحاولة.'
            elif path=='/discover' and params: discovery_error='اختر شركة أولاً لعرض المرشحين.'
        report=None
        lastscore=analyses[0]['score'] if analyses else None
        if params.get('analysis'):
            report=json.loads(params['analysis'][0]); lastscore=report['score']
        chart=[{'period':k['period'],'actual':k['actual'],'target':k['target']} for k in kpis if k['name']=='إيرادات من الشراكة']
        from jinja2 import Environment,BaseLoader,select_autoescape
        # Jinja is used if installed; fallback retains a simple local install path.
        try:
            env=Environment(loader=BaseLoader(),autoescape=select_autoescape()); template=env.from_string(HTML)
            out=template.render(companies=companies,rels=rels,analyses=analyses,events=events,kpis=kpis,metrics={'total':total,'completed':done,'failed':failed,'latency':lat},report=report,lastscore=lastscore,candidates=candidates,discovery_company=discovery_company,discovery_id=discovery_id,discovery_error=discovery_error,chartdata=json.dumps(chart,ensure_ascii=False))
        except ImportError: out='<h1>Install requirements: pip install -r requirements.txt</h1>'
        return self.respond(200,out)
    def do_POST(self):
        fields={k:v[0] for k,v in parse_qs(self.rfile.read(int(self.headers.get('Content-Length',0))).decode()).items()}; path=urlparse(self.path).path
        start=time.time()
        try:
            if path=='/analyze':
                with connect() as d: a=d.execute('SELECT * FROM companies WHERE id=?',(fields['a'],)).fetchone(); b=d.execute('SELECT * FROM companies WHERE id=?',(fields['b'],)).fetchone()
                if not a or not b: raise ValueError('company missing')
                val,parts=score(a,b,fields['kind']); ai=ai_explain(a,b,fields['kind'],parts)
                summary=ai.get('summary') or ai.get('result',{}).get('summary','تحليل AI دون ادعاء حقائق خارج السجل.')
                opportunities='؛ '.join(ai.get('opportunities',ai.get('result',{}).get('opportunities',[]))); risks='؛ '.join(ai.get('risks',ai.get('result',{}).get('risks',[])))
                confidence='محدود — البيانات المالية غير متاحة' if a['revenue'] is None or b['revenue'] is None else 'متوسط'
                kind_labels={'partnership':'شراكة استراتيجية','investment':'تحليل استثمار أسهم (اتجاهي من أ إلى ب)','joint_venture':'مشروع مشترك'}
                report={'a':a['name'],'b':b['name'],'kind_label':kind_labels.get(fields['kind'],fields['kind']),'ai_mode':ai.get('mode','Demo Mode'),'score':val,'parts':[(x,v) for x,v,w in parts],'summary':summary,'opportunities':opportunities,'risks':risks,'confidence':confidence,'source_a':a['source'] or '#','source_b':b['source'] or '#','source_title_a':a['source_date'] or a['provenance'],'source_title_b':b['source_date'] or b['provenance']}
                with connect() as d: d.execute('INSERT INTO analyses(company_a,company_b,kind,score,confidence,report,created) VALUES(?,?,?,?,?,?,?)',(a['id'],b['id'],fields['kind'],val,confidence,json.dumps(report,ensure_ascii=False),datetime.utcnow().isoformat()))
                record('analysis','success',(time.time()-start)*1000,'score='+str(val))
                return self.respond(303,'','text/plain') if False else self.redirect('/?analysis='+__import__('urllib.parse').parse.quote(json.dumps(report,ensure_ascii=False)))
            if path=='/relationship':
                if fields['a']==fields['b']: raise ValueError('companies must differ')
                if fields['status'] not in ('Approved','Signed'): raise ValueError('relationship must be approved or signed')
                with connect() as d: d.execute('INSERT INTO relationships(name,company_a,company_b,kind,start_date,status,simulated) VALUES(?,?,?,?,?,?,0)',(fields['name'],fields['a'],fields['b'],fields['kind'],fields['start'],fields['status']))
                record('relationship_create','success',(time.time()-start)*1000,'approved relationship recorded')
            elif path=='/kpi':
                target=float(fields['target']); actual=float(fields['actual'])
                if target<=0 or actual<0: raise ValueError('invalid KPI input')
                with connect() as d: d.execute('INSERT INTO kpis(relationship_id,name,target,unit,direction,period,actual,updated) VALUES(?,?,?,?,?,?,?,?)',(fields['relationship'],fields['name'],target,fields['unit'],fields['direction'],fields['period'],actual,datetime.utcnow().isoformat()))
                record('kpi_update','success',(time.time()-start)*1000,'saved '+fields['period'])
            elif path=='/simulate':
                typ=fields['test']; details={'timeout':'Simulated AI provider timeout','missing':'Company record not found','invalid':'Rejected negative/invalid KPI test input','delay':'Analysis processing delayed 1.2s'}
                if typ=='delay': time.sleep(1.2)
                record(typ,'failure' if typ in ('timeout','missing','invalid') else 'success',(time.time()-start)*1000,details[typ])
            return self.redirect('/#system' if path=='/simulate' else '/#monitor')
        except Exception as e:
            record('analysis' if path=='/analyze' else 'kpi_update','failure',(time.time()-start)*1000,str(e))
            return self.respond(400,'<meta charset="utf-8"><p>تعذر إكمال الطلب: '+str(e)+'</p><a href="/">رجوع</a>')
    def redirect(self,url): self.send_response(303); self.send_header('Location',url); self.end_headers()
    def log_message(self,*args): pass

if __name__=='__main__':
    init_db(); print('CompatibilityMatch server started'); ThreadingHTTPServer(('0.0.0.0',int(os.getenv('PORT','8000'))),Handler).serve_forever()





