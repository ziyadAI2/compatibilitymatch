# مِشراك — ذكاء الشراكات

مشروع **Project 1 — AI Product Development and Monitoring**. يساعد فرق الاستراتيجية على مقارنة فرص الشراكات واكتشاف الشركات المناسبة بين شركات مدرجة في السوق الرئيسية السعودية. عند إعداد Gemini، يقيّم النموذج معايير المقارنة ويشرح الفرص والمخاطر؛ أما ترتيب الاكتشاف فيبقى خوارزمية محلية لا تستدعي Gemini.

يحتوي كتالوج النسخة على **27 شركة مدرجة** موزعة على الاتصالات والطاقة والبتروكيماويات والمصارف. مرجع أسماء الشركات ورموزها هو [دليل المُصدرين في تداول السعودية](https://www.saudiexchange.sa/wps/portal/saudiexchange/trading/participants-directory/issuer-directory?locale=en). رموز الإدراج لا تعني توفر بيانات مالية داخل التطبيق. لم تُدرج أرقام مالية غير متحققة؛ استيراد القوائم المالية يحتاج ملفاً موثقاً ورابط مصدر رسمي.

يضم التطبيق مقارنة الشركات والاكتشاف الذكي والتقارير، إضافة إلى لوحة مستقلة لمراقبة أداء النظام تقنياً. لا يقدم المنتج نصيحة استثمارية ولا يتنبأ بعوائد.

## المتطلبات

- Python 3.11+
- اختياري: مفتاح Gemini API لتحليل المقارنات وتوليد التفسيرات. من دون مفتاح يعمل التطبيق بوضع تجريبي بالقواعد ومُعلّم بوضوح.

## تشغيل على Windows PowerShell

```powershell
cd C:\Users\ALOSTATH\Projects\CompatibilityMatch-AI
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

افتح http://127.0.0.1:5000/login . ينشئ التطبيق قاعدة SQLite ويحمّل الشركات عند التشغيل الأول. يمكن للزائر إنشاء حساب مستخدم من صفحة الدخول. حساب المدير يُنشأ مرة واحدة من `ADMIN_USERNAME` و`ADMIN_PASSWORD` في ملف `.env` عند أول تشغيل؛ غيّر كلمة المرور الافتراضية قبل الاستخدام، ولا ترفع `.env` إلى GitHub. المستخدم يصل إلى المقارنة والاكتشاف والتقارير، بينما المدير وحده يصل إلى مراقبة النظام التقنية. عند الترقية من النسخة السابقة، يزيل التطبيق السجلات الخيالية القديمة ويحمّل قائمة الشركات المدرجة الجديدة. لا يحذف السجلات التي لا تحمل رموز DEMO.*.

## متغيرات البيئة

لحفظ مفتاح Gemini من حساب المدير في SQLite، اضبط أولاً `GEMINI_ENCRYPTION_KEY` في البيئة. ولتوليده محلياً بعد تثبيت الاعتماديات، استخدم `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`، ثم خزّن الناتج كقيمة سرية في `.env` أو لوحة أسرار الاستضافة. بعد تشغيل التطبيق، يضيف المدير مفتاح Gemini من صفحة **إعدادات الذكاء الاصطناعي**؛ يُشفّر المفتاح باستخدام Fernet قبل تخزينه في جدول `application_secrets`. لا تحفظ مفتاح التشفير في قاعدة البيانات أو GitHub، واحتفظ بنسخة احتياطية منه منفصلة عن نسخة SQLite؛ فقدانه يمنع فك تشفير المفتاح المخزن. يستخدم التطبيق افتراضياً `gemini-3.5-flash-lite`، ويمكن اختيار نموذج آخر مدعوم بواسطة `LLM_MODEL`. إذا عيّنت `GEMINI_API_KEY` مباشرةً في بيئة الخادم، فسيُستخدم ذلك المفتاح بدلاً من قيمة المدير المشفرة.

### إعداد Gemini بعد النشر على Render

1. انشر آخر نسخة من GitHub على Render وثبّت الاعتماديات من `requirements.txt`.
2. في **Environment** أضف `GEMINI_ENCRYPTION_KEY` كقيمة سرية مولدة بالأمر أعلاه، وأضف `FLASK_SECRET_KEY` قوية، وبيانات مدير آمنة. لا تضع أيّاً منها في GitHub.
3. احتفظ بقاعدة SQLite على قرص دائم، وبنسخة احتياطية من `GEMINI_ENCRYPTION_KEY` في مدير أسرار منفصل. يجب نشر نفس مفتاح التشفير مع التطبيق عند كل تحديث حتى يقرأ المفاتيح القديمة.
4. سجّل الدخول بحساب المدير وافتح **إعدادات الذكاء الاصطناعي** وأدخل مفتاح Gemini؛ يُحفظ مشفراً داخل SQLite. بعد ذلك نفّذ مقارنة وافتح **مراقبة النظام** للتحقق من طلب Gemini الحقيقي.

المراقبة تسجل كل محاولة HTTP حقيقية إلى Gemini على حدة، بما فيها الإعادات، بينما تظل أحداث Demo Mode ومحاكاة الأعطال منفصلة. الرموز والتكلفة لا تُخمن؛ قد لا يتضمن رد المزود بيانات استخدام. التكلفة المعروضة تقدير وفق أسعار الوحدة القياسية المهيأة في التطبيق (قابلة للتغيير وعبر `LLM_INPUT_COST_PER_1M` و`LLM_OUTPUT_COST_PER_1M`) وليست فاتورة، وقد تختلف مع الخطة والأسعار الفعلية.

## خطوات العرض

1. **اكتشاف شريك:** الاكتشاف الذكي ← stc (7010) ← شراكة استراتيجية. جرّب أيضاً مقارنة stc مع موبايلي أو زين، أو أرامكو مع سابك.
2. **تحليل:** افتح المقارنة بعد ضبط مفتاح Gemini. راجع درجات المعايير التي قدّرها النموذج، والدرجة الإجمالية المحسوبة من الأوزان المحددة، والأدلة النصية وحدود المعلومات.
3. **مراقبة النظام:** شغّل تحليلاً، ثم استخدم زر محاكاة timeout لترى الحدث المسجل ومقاييس قاعدة البيانات.

## اختبارات المشروع

```powershell
.\.venv\Scripts\Activate.ps1
pytest -q
```

## استيراد بيانات مالية موثقة

استخدم الأعمدة في `data/companies_demo.csv` كقالب، وأدخل فقط حقائق لها مصادر رسمية. الشركات الموجودة جاهزة في الكتالوج؛ أضف السنة المالية ورابط التقرير الرسمي ثم شغّل `python scripts/import_companies.py path.csv`. يحدّث السكربت البيانات للشركة المعروفة بالرمز ويمنع استيراد بيانات مالية معلّمة كتجريبية.

## ملفات التسليم

- `docs/REPORT.md` التقرير الفني.
- `docs/PITCH.md` نص عرض 3 دقائق.
- `docs/QNA.md` أسئلة نقاش 10 دقائق.
- `docs/DIAGRAMS.md` مخططا التطوير والمراقبة.
- `docs/ARCHITECTURE.md` المعمارية ومصدر البيانات.
- `docs/AI_EVALUATION.md` قالب مراجعة صحة شروحات AI.
- `docs/slides.md` نص الشرائح.

## بنية المشروع

```text
app/       Flask routes, models, scoring, AI, RTL templates
data/      CSV templates
docs/      report, diagrams, pitch, Q&A, evaluation
scripts/   CSV import helper
tests/     pytest suite
run.py     local development server
```
# Official market context data

The app includes a separate `market_context_indicators` table for official
Saudi sector-level context. It is not company financial data and is not fed
into company-level financial scoring. The current import contains 20 records
from GASTAT's 2024 Structural Business Statistics release, with source URL,
period, unit, and a non-synthetic flag on each record.

To re-import/update those records idempotently:

```powershell
.\.venv\Scripts\python.exe .\scripts\import_market_context_2024.py
```

After starting the Flask app, signed-in users can view the records at
`/market-data`. The national open-data page describes the portal and reuse
policy; company-level filings are sourced separately from official issuer and
Saudi Exchange disclosures. Missing company figures remain missing and carry
an explanation. Simulated values must be labeled as simulations and must not
be presented as verified facts.
