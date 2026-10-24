"""Import official Saudi structural-business indicators for market context.

These are national/sector aggregates, not company financial statements and must
not be used as company-level values in compatibility scoring.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app
from app.models import MarketContextIndicator, db

SOURCE_TITLE = "الهيئة العامة للإحصاء — إحصاءات الأعمال الهيكلية 2024"
SOURCE_URL = "https://www.stats.gov.sa/documents/20117/2435267/Structural%2BBusiness%2BStatistics%2B2024%2BEN.pdf/3cb467dd-e8b0-881c-b81a-4195c6564d41?t=1761717962636"
NOTE = "بيانات رسمية مجمعة على مستوى النشاط الاقتصادي، وليست قيمة خاصة بشركة؛ النسب مقربة كما وردت في النشرة."

ROWS = [
    ("operating_revenue_total", "إجمالي الإيرادات التشغيلية", "الاقتصاد السعودي", 5500.0, "مليار ريال"),
    ("operating_expenditure_total", "إجمالي المصروفات التشغيلية", "الاقتصاد السعودي", 2367.0, "مليار ريال"),
    ("employee_compensation_total", "تعويضات العاملين", "الاقتصاد السعودي", 588.8, "مليار ريال"),
    ("gross_fixed_capital_formation", "تكوين رأس المال الثابت الإجمالي", "الاقتصاد السعودي", 988.0, "مليار ريال"),
    ("operating_revenue_share", "حصة النشاط من الإيرادات التشغيلية", "الصناعات التحويلية", 31.0, "%"),
    ("operating_revenue_share", "حصة النشاط من الإيرادات التشغيلية", "التعدين واستغلال المحاجر", 19.2, "%"),
    ("operating_revenue_share", "حصة النشاط من الإيرادات التشغيلية", "تجارة الجملة والتجزئة وإصلاح المركبات", 16.7, "%"),
    ("operating_revenue_share", "حصة النشاط من الإيرادات التشغيلية", "التشييد", 8.6, "%"),
    ("operating_revenue_share", "حصة النشاط من الإيرادات التشغيلية", "الأنشطة المالية والتأمين", 4.6, "%"),
    ("operating_revenue_share", "حصة النشاط من الإيرادات التشغيلية", "المعلومات والاتصالات", 4.4, "%"),
    ("operating_revenue_share", "حصة النشاط من الإيرادات التشغيلية", "النقل والتخزين", 3.2, "%"),
    ("operating_revenue_share", "حصة النشاط من الإيرادات التشغيلية", "أنشطة اقتصادية أخرى", 12.4, "%"),
    ("operating_expenditure_share", "حصة النشاط من المصروفات التشغيلية", "الصناعات التحويلية", 41.6, "%"),
    ("operating_expenditure_share", "حصة النشاط من المصروفات التشغيلية", "تجارة الجملة والتجزئة وإصلاح المركبات", 22.1, "%"),
    ("operating_expenditure_share", "حصة النشاط من المصروفات التشغيلية", "التشييد", 7.7, "%"),
    ("operating_expenditure_share", "حصة النشاط من المصروفات التشغيلية", "التعدين واستغلال المحاجر", 5.3, "%"),
    ("operating_expenditure_share", "حصة النشاط من المصروفات التشغيلية", "المعلومات والاتصالات", 4.9, "%"),
    ("operating_expenditure_share", "حصة النشاط من المصروفات التشغيلية", "الأنشطة المالية والتأمين", 3.3, "%"),
    ("operating_expenditure_share", "حصة النشاط من المصروفات التشغيلية", "النقل والتخزين", 3.2, "%"),
    ("operating_expenditure_share", "حصة النشاط من المصروفات التشغيلية", "أنشطة اقتصادية أخرى", 11.9, "%"),
]


def import_rows():
    app = create_app()
    with app.app_context():
        for code, name, sector, value, unit in ROWS:
            item = MarketContextIndicator.query.filter_by(
                metric_code=code, sector=sector, period_year=2024
            ).first()
            if item is None:
                item = MarketContextIndicator(metric_code=code, sector=sector, period_year=2024)
            item.metric_name = name
            item.value = value
            item.unit = unit
            item.source_title = SOURCE_TITLE
            item.source_url = SOURCE_URL
            item.notes = NOTE
            item.is_synthetic = False
            db.session.add(item)
        db.session.commit()
        return MarketContextIndicator.query.filter_by(period_year=2024).count()


if __name__ == "__main__":
    print(f"Official market-context rows imported/updated: {import_rows()}")
