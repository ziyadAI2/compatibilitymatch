"""Idempotently import verified FY2025 financial figures from primary sources.

All stored monetary amounts are normalized to whole Saudi riyals (SAR).
Fields absent from the cited source are deliberately left NULL.
"""

from app import create_app
from app.models import (
    Company,
    CompanyFinancial,
    CompanyFinancialFieldNote,
    CompanySource,
    db,
)
from sqlalchemy import text


# Numbers are in SAR after normalizing each source's stated units.
# Mobily's annual report summary reports balance sheet figures in SAR millions,
# rounded to the nearest million. Its published annual announcement reports
# revenue and attributable net profit in SAR millions.
OFFICIAL_FY2025 = [
    {
        "symbol": "2010",
        "revenue": 116_525_214_000,
        "net_income": -25_779_231_000,
        "total_assets": 244_292_189_000,
        "total_liabilities": 89_472_648_000,
        "current_assets": None,
        "current_liabilities": None,
        "url": "https://www.saudiexchange.sa/wps/portal/saudiexchange/hidden/company-profile-main/%21ut/p/z1/vVTbcqJAEP0afIvTQkCSKiuFFzDRxLhoVF6sESdAFhgyM4ju128TX8Jukt2HraWKYrr79O10DyQgaxLk9JBEVCU8pynKm8Damo4F-tiGmefqI5i7V_35cOR1YHJJVk0A-I8mAh7vjSl8Aw8sEvyNP3zyOPBn_6AJsYfDAUIm9vgOZjpY3d8A954F8wdnPtO7JoCv_wr4oIc3wFdFflmm1yV3JIhSvjsz6uQ7w45IINgzE0y0S4HqWKlCXmugQVVV7YjzKGXtkGcaoPnmtde0S1ruE3YMY5pHDCXUFlKDggtFUw0aZg14KTIqvjOFkIwm-cVZuqioCuNa9WYrMzyctI7hpjykKcPTkIqWpL1lS74mPb11YPueTuPlZFQl-Q82KBLlPTjH9XpykMOx7195Q3v-0u9bfSdKR86mVcqo58wOT7Qy6J1puO7OeFr4R3BX41k0zeRHbMRcKrJukvARTjIqwriggtZx_hc9N2duelTUNdVZ35IquqdViaFJgOUWND_5p2zHca660YHPoOdYZI3BFrhB3Xc7-DS4BAtml9791O54pllvUGNJ50sbV8x3-6YNuj3oNnLUHCS77Lw_xyzN6-YF32uwp4qqU4FdhzxXLFcaCCaRgZBdhDxNWVjffIltxFSoraIy2YalEIjcSjRy7HuxMGFw-68TviNjgz-FL8lYHRJWkWXOcXAp8ev7l-IsyQadfXyLbLmG5PbFTA9TtrKVuTM9_NjV4jn6Ceq3yfQ%21%21/dz/d5/L0lHSklKSUtVS1VKQ2dwUkNTQ2lDbEVLSUtVU0ovWUJZRUFBSU1FQUFBRUVNQ01LR0lNQU9FT0JFQkVKRk5GTkpGRERMRExISU1FRFBQQXZBblBDS0EvNEpDaWpLMWJHTGppRUVwTWhTVFVVMXUybHNacVdhM2JTMjFWRktxaXBBISEvWjdfNUE2MDJIODBPMFZDNDA2ME80R01MODFHNTUvWjZfNUE2MDJIODBPR0YyRTBRRjlCUURFRzEwSzQvdmlldy9ub3JtYWwvbGFuZy9lbi9odHRwOiUwJTB0YWRhd3VsJTAvY29tcGFueVN5bWJvbC8yMDEw/?locale=en",
        "title": "Saudi Exchange profile — SABIC FY2025 financial statements",
        "notes": "Official Saudi Exchange financial profile. Revenue, net loss attributable to shareholders, assets and liabilities are shown in SAR thousands; normalized to SAR. Current balances left NULL because not captured from the source table.",
    },
    {
        "symbol": "2310",
        "revenue": 6_809_700_000,
        "net_income": -860_500_000,
        "total_assets": 20_316_378_000,
        "total_liabilities": None,
        "current_assets": None,
        "current_liabilities": None,
        "url": "https://www.saudiexchange.sa/wps/portal/saudiexchange/newsandreports/issuer-news/issuer-announcements/issuer-announcements-details/?anCat=1&anId=93745&cs=2310&locale=en",
        "title": "Sipchem Annual Financial Results for FY2025",
        "notes": "Official Saudi Exchange annual announcement: revenue and net loss attributable to shareholders are SAR millions; normalized to SAR. Total assets from the Saudi Exchange issuer financial profile, SAR thousands; normalized to SAR.",
        "extra_source": {
            "url": "https://www.saudiexchange.sa/wps/portal/saudiexchange/hidden/company-profile-main/%21ut/p/z1/dY2xDoIwGISfhpX_BCHg1hjFEFHQQexiwEAhYEugyutLogOD3vZdvssRp5S4zF61yHStZNZOfOXuzWEurJ2HY7AOl0gOLIK_8S1gQRfixOcKzrGDZBtH9h4nBHC_Av6EgULiolX5547J3PYE8b4oi77ozWc_1ZXW3bAyYGAcRzOvpTDv6mHg16BSg6Z07lHXNGWknesbfa4YZA%21%21/dz/d5/L0lDU0NRa2dwUXBRb2dwUklrQSEhL29Pb1FBQUlRUmhCS1FRQmtHY2h3UXBDa3FDRUN3UUEhLzRKQ2lqSzFiR0xqaUVFMXUwbHNwcWFWVkV5QSEvWjdfNUE2MDJIODBPMFZDNDA2ME80R01MODFHNTUvWjZfNUE2MDJIODBPR0YyRTBRRjlCUURFRzEwSzQvdmlldy9ub3JtYWwvaHR0cDolMCUwdGFkYXd1bCUwL2NvbXBhbnlTeW1ib2wvMjMxMC9lbi%21%21/",
            "title": "Saudi Exchange profile — Sipchem FY2025 total assets",
            "notes": "Official Saudi Exchange profile; FY2025 total assets shown in SAR thousands.",
        },
    },
    {
        "symbol": "2350",
        "revenue": 8_458_846_000,
        "net_income": -2_293_883_000,
        "total_assets": 22_724_825_000,
        "total_liabilities": 13_544_977_000,
        "current_assets": None,
        "current_liabilities": None,
        "url": "https://www.saudiexchange.sa/wps/portal/saudiexchange/hidden/company-profile-main/%21ut/p/z1/jVLbctowEP2WPvBYazH40r4ZSJ2LHQMuEPuFEWILGuRLbYGHfH3X-CXJQFKNZqTVnt09R7ssZS8szflJ7riWRc4V2Ulqry3PBvPehcidTMYw-_Xk3j9CZILtsNV7AMRTiwDTcBDAHHywWfo_8XBjefBV_JKlLK311TwejObmaADgu12eW-4lUHz6oVTo2zB79maR6VgAsfkRcEXqlSLvtXzKIjK_AJCKhGQ6bzgsx0OwIRr6YeD2fctiq5PEhi3yosqofXGbUfF8xxJesd-U_dPgR5buVLHp-r7XuvzZgx5ovuXNUfWIvyiykufn-JxtCgKZ4A5vQVUhuEL2QnU70jdUeYHZ0eSinTmWNGVtlEWlFeraUDI_XDTQyctSbllCHAy5yYymNPg2k7mxR0XXsjQaVOREQ2jBYswvM-GsH6b-sP_gmk--F4_Bjm1nPvrhAdBvriqsi2MlkM13qEMu8-ciO4qQVwfUE9RcqprNBBd7DPCEasp32JGVdcO12Aey1jEqFBqJ2XN0GUayimrKK56hxlY9Pa5Z0neGTlv1sto3zTcKl9SuN9h-66jw7xFrHXQ_mJCSMlss8vP3w_zuT3g3sPyVq10YZGtMxptXpJ143_4BGrhKvA%21%21/dz/d5/L0lHSklKSUtVS1VKQ2dwUkNpQ2xFS0lLVVNKQSEvWUtZRUFBSU1FQUFBRUVNQ0tJTUFHRUdPRU9FQkpGSkZCSk5ORE5ETElNRU5ISFBIUE5IQ0FvTUtBQSEhLzRKQ2lqSzJNWEhFSUpTWkNrbW9wcmR0TFl6VXMxdTJsdHFxS1ZWRlMvWjdfNUE2MDJIODBPMFZDNDA2ME80R01MODFHNTUvWjZfNUE2MDJIODBPR0YyRTBRRjlCUURFRzEwSzQvdmlldy9ub3JtYWwvbGFuZy9lbi9nbG9iYWwvaHR0cDolMCUwdGFkYXd1bCUwL2NvbXBhbnlTeW1ib2wvMjM1MC8%21/",
        "title": "Saudi Exchange profile — Saudi Kayan FY2025 financial statements",
        "notes": "Official Saudi Exchange profile. Revenue, attributable net loss, assets and liabilities shown in SAR thousands; normalized to SAR.",
    },
    {
        "symbol": "2290",
        "revenue": 5_601_200_000,
        "net_income": 79_000_000,
        "total_assets": None,
        "total_liabilities": None,
        "current_assets": None,
        "current_liabilities": None,
        "url": "https://www.saudiexchange.sa/wps/portal/saudiexchange/newsandreports/issuer-news/issuer-announcements/issuer-announcements-details/?anCat=17&anId=93023&cs=2290&locale=en",
        "title": "YANSAB Annual Financial Results for FY2025",
        "notes": "Official Saudi Exchange annual announcement. Revenue and net profit attributable to issuer shareholders are SAR millions; normalized to SAR. Balance sheet values are left NULL pending a verified source row.",
    },
    {
        "symbol": "2380",
        "revenue": 35_008_000_000,
        "net_income": -3_899_000_000,
        "total_assets": 58_550_035_000,
        "total_liabilities": None,
        "current_assets": None,
        "current_liabilities": None,
        "url": "https://www.saudiexchange.sa/wps/portal/saudiexchange/newsandreports/issuer-news/issuer-announcements/issuer-announcements-details/?anCat=17&anId=93546&cs=2380&locale=en",
        "title": "Petro Rabigh Annual Financial Results for FY2025",
        "notes": "Official Saudi Exchange annual announcement gives revenue and attributable net loss in SAR millions; normalized to SAR. Total assets from Saudi Exchange FY2025 profile in SAR thousands; normalized to SAR. Other balance-sheet values remain NULL.",
    },
    {
        "symbol": "5110",
        "revenue": 102_217_782_000,
        "net_income": 12_974_811_000,
        "total_assets": 635_823_214_000,
        "total_liabilities": 378_139_654_000,
        "current_assets": 41_917_683_000,
        "current_liabilities": 99_967_741_000,
        "url": "https://www.se.com.sa/-/media/sec/Investors/Earning-Reports/Earnings-Release-FY-2025.ashx",
        "title": "Saudi Energy FY2025 Earnings Release",
        "notes": "Official issuer earnings release and FY2025 balance-sheet data. Source unit: SAR thousands; normalized to SAR.",
        "extra_source": {
            "url": "https://www.se.com.sa/-/media/sec/Investors/Earning-Reports/Earnings-Release-FY-2025.ashx",
            "title": "Saudi Energy FY2025 financial statements and balance sheet",
            "notes": "Official Saudi Energy earnings release, including consolidated income statement and balance sheet in SAR thousands.",
        },
    },
    {
        "symbol": "2020",
        "revenue": 13_077_000_000,
        "net_income": 4_322_000_000,
        "total_assets": 27_003_192_000,
        "total_liabilities": None,
        "current_assets": None,
        "current_liabilities": None,
        "url": "https://www.sabic-agrinutrients.com/en/news/49410-20260301-31-12-2025-twelve-months",
        "title": "SABIC Agri-Nutrients FY2025 Consolidated Financial Results",
        "notes": "Official issuer annual results. Revenue and net profit are rounded SAR millions. Total assets from the Saudi Exchange issuer profile, SAR thousands; normalized to SAR. Unverified balance-sheet fields remain NULL.",
        "extra_source": {
            "url": "https://www.saudiexchange.sa/wps/portal/saudiexchange/hidden/company-profile-main/%21ut/p/z1/lZBbb4JAEIV_kdkRZNVHq6liQW6iwkuz4gQ3csuyJaG_viA2xtradrMPO2e_yZk5JCQ7Emas4jGTPM9Y0tRBSF-1CQVlMQJrtFgMwXl-0Ue6uwSwVbL9AphzCs5q4ljKUIP5Bkj4r37wbK0BbFM1wIU50L_1ww9n8qt_0PQPr4BlOlOgMHB9upn1YakSj4Qk3Ndene7zhAQDVem3SsrECeW6LnB6xOhEArMZJXzoZtA74D6tW-CbOM7Ag309Js6hPFxqK7DM30SExI1RznjFD5gdyhlKxpOSOBGLjmhghYnNYuwyaAASKOMe0J4CinYbS1uVGMlcXN5nPRdRnhYsqzuxy6w0eCn1Q5tYoxUoeN4UU99bW-aVunyXkgnZ2WqtLZAi9f3d-xr3Y53blfm00qrPG38AnhOWyg%21%21/dz/d5/L0lHSklKSUtVS1VKSUtJS1VRb2dwUklrIS9ZQVlFQUFJTUVBQUFFRU1DS0lNQUdFR09FT01CQkpKRkpGQkpOTkROREJOQ0xJTU1BQSEhLzRKQ2lqSzJNWEhFSUp6S0pOYnNwYmFhaG10MlV0dFZTeXFvdVFBISEvWjdfNUE2MDJIODBPMFZDNDA2ME80R01MODFHNTUvWjZfNUE2MDJIODBPR0YyRTBRRjlCUURFRzEwSzQvdmlldy9ub3JtYWwvZ2xvYmFsL2h0dHA6JTAlMHRhZGF3dWwlMC9jb21wYW55U3ltYm9sLzIwMjAvZW4%21/",
            "title": "Saudi Exchange profile — SABIC Agri-Nutrients 2025 total assets",
            "notes": "Official Saudi Exchange company profile; total assets for 2025 shown in SAR thousands.",
        },
    },
    {
        "symbol": "7010",
        "revenue": 77_818_675_000,
        "net_income": 14_828_030_000,  # attributable to stc shareholders
        "total_assets": 157_476_669_000,
        "total_liabilities": 71_090_329_000,
        "current_assets": 58_015_755_000,
        "current_liabilities": 40_172_575_000,
        "url": "https://www.stc.com/content/dam/stc/stc-annual-report-2025/financial-performance/",
        "title": "stc Annual Report 2025 — Financial performance",
        "notes": "Official stc FY2025 consolidated figures. Source unit: SAR thousands; normalized to SAR. Net income is attributable to stc shareholders.",
    },
    {
        "symbol": "7020",
        "revenue": 19_642_000_000,
        "net_income": 3_466_000_000,  # attributable to issuer shareholders
        "total_assets": 42_455_000_000,
        "total_liabilities": 22_128_000_000,
        "current_assets": 10_428_000_000,
        "current_liabilities": 11_239_000_000,
        "url": "https://www.saudiexchange.sa/Resources/fsPdf/481_0_2026-03-31_15-21-04_En.pdf",
        "title": "Mobily Annual Report 2025",
        "notes": "Official Saudi Exchange annual report. Balance sheet summary rounded to nearest SAR million; revenue and attributable net profit from FY2025 announcement in SAR millions. Normalized to SAR.",
    },
    {
        "symbol": "2082",
        "revenue": 7_413_501_000,
        "net_income": 1_852_225_000,  # attributable to issuer shareholders
        "total_assets": 70_058_226_000,
        "total_liabilities": 38_406_944_000,
        "current_assets": None,
        "current_liabilities": None,
        "url": "https://iar2025.acwapower.com/en/board-report/further-disclosures",
        "title": "ACWA POWER 2025 Integrated Annual Report — Further disclosures",
        "notes": "Official ACWA 2025 Integrated Annual Report. Values are SAR thousands, normalized to SAR. Net income is attributable to equity holders of the parent; current assets/liabilities are not included because not provided in this cited summary.",
    },
    {
        "symbol": "2222",
        "revenue": 1_671_204_000_000,
        "net_income": 350_210_000_000,
        "total_assets": 2_551_964_000_000,
        "total_liabilities": None,
        "current_assets": None,
        "current_liabilities": None,
        "url": "https://www.aramco.com/-/media/publications/corporate-reports/reports-and-presentations/2025/fy/saudi-aramco-fy-2025-full-financials-english.pdf",
        "title": "Saudi Aramco Annual Report 2025 — Consolidated financial statements",
        "notes": "Official Saudi Aramco consolidated FY2025 figures. Source income statement amounts are SAR millions; total assets is SAR millions from annual report summary; normalized to SAR. Net income is the consolidated net income line. Other balance sheet details were not added because not verified from the cited summary.",
    },
]

FINANCIAL_FIELDS = {
    "revenue": "لم تُسجل الإيرادات؛ لا توجد قيمة موثقة مستوردة لهذا الحقل في بيانات FY2025 الحالية.",
    "net_income": "لم يُسجل صافي الربح أو الخسارة؛ لا توجد قيمة موثقة مستوردة لهذا الحقل في بيانات FY2025 الحالية.",
    "total_assets": "لم تُسجل الأصول الإجمالية؛ لا توجد قيمة موثقة مستوردة لهذا الحقل في بيانات FY2025 الحالية.",
    "total_liabilities": "لم تُسجل الالتزامات الإجمالية؛ لم تظهر قيمة موثقة لهذا الحقل في المصدر المسجل.",
    "current_assets": "لم تُسجل الأصول المتداولة؛ لم تظهر قيمة موثقة لهذا الحقل في المصدر المسجل.",
    "current_liabilities": "لم تُسجل الالتزامات المتداولة؛ لم تظهر قيمة موثقة لهذا الحقل في المصدر المسجل.",
    "market_cap": "لم تُسجل القيمة السوقية؛ فهي مقياس سوقي متغير ولم تُحدد له قيمة وتاريخ قياس موثقان.",
}


def create_explained_view():
    """Expose verified numbers and explanatory text in one DBeaver-friendly view."""
    db.session.execute(text("DROP VIEW IF EXISTS company_financials_explained"))
    db.session.execute(text("""
        CREATE VIEW company_financials_explained AS
        SELECT c.symbol AS symbol,
               c.official_name AS company_name,
               COALESCE(f.period_year, 2025) AS period_year,
               COALESCE(CAST(f.revenue AS TEXT), nr.explanation) AS revenue,
               COALESCE(CAST(f.net_income AS TEXT), nn.explanation) AS net_income,
               COALESCE(CAST(f.total_assets AS TEXT), na.explanation) AS total_assets,
               COALESCE(CAST(f.total_liabilities AS TEXT), nl.explanation) AS total_liabilities,
               COALESCE(CAST(f.current_assets AS TEXT), nca.explanation) AS current_assets,
               COALESCE(CAST(f.current_liabilities AS TEXT), ncl.explanation) AS current_liabilities,
               COALESCE(CAST(f.market_cap AS TEXT), nmc.explanation) AS market_cap,
               f.source_url AS financial_source_url,
               CASE WHEN f.id IS NULL THEN 'لا يوجد سجل مالي مستورد' ELSE 'يوجد سجل مالي؛ الخانات غير المتاحة موضحة' END AS record_status
        FROM companies c
        LEFT JOIN company_financials f ON f.company_id = c.id AND f.period_year = 2025
        LEFT JOIN company_financial_field_notes nr ON nr.company_id = c.id AND nr.period_year = 2025 AND nr.field_name = 'revenue'
        LEFT JOIN company_financial_field_notes nn ON nn.company_id = c.id AND nn.period_year = 2025 AND nn.field_name = 'net_income'
        LEFT JOIN company_financial_field_notes na ON na.company_id = c.id AND na.period_year = 2025 AND na.field_name = 'total_assets'
        LEFT JOIN company_financial_field_notes nl ON nl.company_id = c.id AND nl.period_year = 2025 AND nl.field_name = 'total_liabilities'
        LEFT JOIN company_financial_field_notes nca ON nca.company_id = c.id AND nca.period_year = 2025 AND nca.field_name = 'current_assets'
        LEFT JOIN company_financial_field_notes ncl ON ncl.company_id = c.id AND ncl.period_year = 2025 AND ncl.field_name = 'current_liabilities'
        LEFT JOIN company_financial_field_notes nmc ON nmc.company_id = c.id AND nmc.period_year = 2025 AND nmc.field_name = 'market_cap'
        ORDER BY c.symbol
    """))


def main():
    app = create_app()
    with app.app_context():
        inserted = 0
        updated = 0
        for item in OFFICIAL_FY2025:
            company = Company.query.filter_by(symbol=item["symbol"]).one()
            financial = CompanyFinancial.query.filter_by(
                company_id=company.id, period_year=2025
            ).first()
            if financial is None:
                financial = CompanyFinancial(
                    company_id=company.id, period_year=2025, is_synthetic=False
                )
                db.session.add(financial)
                inserted += 1
            else:
                updated += 1
            for field in (
                "revenue",
                "net_income",
                "total_assets",
                "total_liabilities",
                "current_assets",
                "current_liabilities",
            ):
                setattr(financial, field, item[field])
            financial.market_cap = None
            financial.source_url = item["url"]
            financial.is_synthetic = False

            source = CompanySource.query.filter_by(
                company_id=company.id, url=item["url"]
            ).first()
            if source is None:
                db.session.add(
                    CompanySource(
                        company_id=company.id,
                        title=item["title"],
                        url=item["url"],
                        published_at=None,
                        notes=item["notes"],
                    )
                )
            extra = item.get("extra_source")
            if extra and CompanySource.query.filter_by(
                company_id=company.id, url=extra["url"]
            ).first() is None:
                db.session.add(
                    CompanySource(
                        company_id=company.id,
                        title=extra["title"],
                        url=extra["url"],
                        published_at=None,
                        notes=extra["notes"],
                    )
                )
        # Record explicit reasons for all NULL metrics, including companies for
        # which no FY2025 row has yet been imported. Keep numeric columns NULL.
        financial_rows = {
            row.company_id: row
            for row in CompanyFinancial.query.filter_by(period_year=2025).all()
        }
        for company in Company.query.all():
            financial = financial_rows.get(company.id)
            for field, default_note in FINANCIAL_FIELDS.items():
                value = getattr(financial, field, None) if financial is not None else None
                note = CompanyFinancialFieldNote.query.filter_by(
                    company_id=company.id, period_year=2025, field_name=field
                ).first()
                if value is not None:
                    if note is not None:
                        db.session.delete(note)
                    continue
                explanation = (
                    "لا يوجد سجل مالي للسنة 2025 لهذه الشركة؛ لم تُستورد أرقام مالية من مصدر رسمي بعد. "
                    + default_note
                    if financial is None
                    else default_note
                )
                if note is None:
                    note = CompanyFinancialFieldNote(
                        company_id=company.id,
                        period_year=2025,
                        field_name=field,
                        explanation=explanation,
                    )
                    db.session.add(note)
                else:
                    note.explanation = explanation
        db.session.flush()
        create_explained_view()
        db.session.commit()
        notes_count = CompanyFinancialFieldNote.query.filter_by(period_year=2025).count()
        print(
            f"FY2025 official financial rows inserted={inserted}, updated={updated}; "
            f"explanatory notes={notes_count}; view=company_financials_explained"
        )


if __name__ == "__main__":
    main()
