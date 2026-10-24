from __future__ import annotations

import json
import hmac
import re
import secrets
import time
from datetime import datetime
import requests

from flask import (
    Blueprint,
    current_app,
    Response,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy.exc import SQLAlchemyError

from app.ai_engine import ai_score_context, analyze_discovery_with_ai, analyze_with_ai, encryption_ready, llm_configured, save_admin_api_key, saved_admin_api_key
from app.auth import roles_required
from app.models import (
    Analysis,
    Company,
    CompatibilityScore,
    MarketContextIndicator,
    Recommendation,
    db,
)
from app.monitoring import dashboard_metrics, gemini_api_metrics, record_event
from app.scoring import SCORING_VERSION, analyze_pair, rank_candidates

bp = Blueprint("main", __name__)

ANALYSIS_LABELS = {
    "partnership": "شراكة استراتيجية",
    "equity_investment": "استثمار قائم",
    "joint_venture": "مشروع مشترك",
}


def _brand_analysis_text(value):
    """Hide the provider name from user-facing analysis text, including old reports."""
    if isinstance(value, str):
        value = value.replace("gemini-ai-v1", "mishrak-ai-v1")
        return re.sub(r"\bgemini\b", "Mishrak AI", value, flags=re.IGNORECASE)
    if isinstance(value, list):
        return [_brand_analysis_text(item) for item in value]
    if isinstance(value, dict):
        return {key: _brand_analysis_text(item) for key, item in value.items()}
    return value

CRITERION_LABELS = {
    "business_complementarity": "تكامل الأنشطة التجارية",
    "product_compatibility": "توافق المنتجات والخدمات",
    "partnership_opportunity": "فرص التعاون",
    "strategic_alignment": "المواءمة الاستراتيجية",
    "financial_capacity": "القدرة المالية",
    "operational_fit": "التوافق التشغيلي",
    "risk_control": "إدارة المخاطر",
    "industry_relationship": "الارتباط بين القطاعات",
    "resource_complementarity": "تكامل الموارد",
    "operational_capability": "القدرات التشغيلية",
    "business_opportunity": "الفرصة التجارية",
    "project_feasibility": "جدوى المشروع",
    "implementation_risk": "مخاطر التنفيذ",
    "mutual_benefit": "المنفعة المتبادلة",
}

DISCOVERY_CRITERION_LABELS = {
    "business_complementarity": "تكامل الأنشطة",
    "opportunity_specificity": "وضوح فرصة التعاون",
    "strategic_alignment": "المواءمة الاستراتيجية",
    "operational_feasibility": "قابلية التنفيذ التشغيلي",
    "evidence_strength": "قوة الأدلة",
    "risk_manageability": "إمكانية إدارة المخاطر",
}

STATUS_LABELS = {
    "draft": "مسودة",
    "approved": "معتمدة",
    "signed": "موقّعة",
    "active": "نشطة",
    "completed": "مكتملة",
    "failed": "تعذّر إكمالها",
    "On Track": "على المسار الصحيح",
    "Needs Attention": "تحتاج إلى متابعة",
    "Off Track": "متأخرة عن الهدف",
    "Insufficient Data": "بيانات غير كافية",
    "pending": "قيد الانتظار",
    "delayed": "متأخرة عن موعدها",
}


def score_class(score):
    if score is None:
        return "score-unavailable"
    if score >= 80:
        return "score-high"
    if score >= 60:
        return "score-mid"
    return "score-low"


def analysis_status_text(analysis):
    if analysis.status == "failed":
        return "تعذّر إكمال التحليل حالياً. تحقق من البيانات وحاول مرة أخرى لاحقاً."
    if analysis.mode == "committee_demo":
        return "سجل عرض توضيحي محسوب بمحرك التقييم من بيانات الشركات الموجودة؛ لا يمثل شراكة أو اتفاقاً فعلياً."
    if analysis.mode == "demo_rules":
        return f"اكتمل التحليل باستخدام قواعد التقييم التجريبية خلال {analysis.latency_ms} ملي ثانية."
    if analysis.mode == "ai_fallback":
        return "اكتملت درجة التوافق بالقواعد الثابتة، لكن تعذّر الاتصال بـMishrak AI؛ الشرح المعروض تجريبي ويحتاج إلى إعادة المحاولة."
    if analysis.mode == "llm":
        return f"حلّل Mishrak AI معايير التوافق والفرص من البيانات المتاحة خلال {analysis.latency_ms} ملي ثانية؛ راجع الأدلة والقيود قبل اتخاذ القرار."
    if analysis.mode == "hybrid":
        return f"اكتمل التحليل بمساعدة الذكاء الاصطناعي خلال {analysis.latency_ms} ملي ثانية."
    return f"اكتمل التحليل خلال {analysis.latency_ms} ملي ثانية."


@bp.app_context_processor
def inject_globals():
    return {
        "llm_mode": "llm" if llm_configured() else "demo",
        "analysis_labels": ANALYSIS_LABELS,
        "criterion_labels": CRITERION_LABELS,
        "status_labels": STATUS_LABELS,
        "score_class": score_class,
        "analysis_status_text": analysis_status_text,
        "scoring_version": SCORING_VERSION,
    }


@bp.route("/")
def home():
    companies = Company.query.order_by(Company.sector, Company.official_name).all()
    metrics = dashboard_metrics() if g.logged_in_user.role == "admin" else None
    recent_analyses = Analysis.query.filter(Analysis.analysis_type.in_(("partnership", "joint_venture"))).order_by(Analysis.created_at.desc()).limit(5).all()
    sector_count = db.session.query(Company.sector).distinct().count()
    return render_template("home.html", companies=companies, metrics=metrics, recent_analyses=recent_analyses, sector_count=sector_count)


@bp.route("/compare", methods=["GET", "POST"])
def compare():
    companies = Company.query.order_by(Company.official_name).all()
    if request.method == "POST":
        a_id = request.form.get("company_a")
        b_id = request.form.get("company_b")
        analysis_type = request.form.get("analysis_type", "partnership")
        simulate = request.form.get("simulate")
        if analysis_type not in ("partnership", "joint_venture"):
            flash("نوع التحليل غير متاح. اختر شراكة استراتيجية أو مشروعاً مشتركاً.", "err")
            return redirect(url_for("main.compare"))
        return _run_comparison(a_id, b_id, analysis_type, simulate)
    return render_template("compare.html", companies=companies)


@bp.route("/analysis/<int:analysis_id>")
def analysis_detail(analysis_id):
    analysis = Analysis.query.get_or_404(analysis_id)
    stored_report = json.loads(analysis.report_json or "{}")
    if stored_report.get("discovery"):
        return redirect(url_for("main.discovery_detail", analysis_id=analysis.id))
    if analysis.analysis_type == "equity_investment":
        abort(404)
    report = _brand_analysis_text(stored_report)
    return render_template("analysis.html", analysis=analysis, report=report)


@bp.route("/discovery/<int:analysis_id>")
def discovery_detail(analysis_id):
    analysis = Analysis.query.get_or_404(analysis_id)
    report = _brand_analysis_text(json.loads(analysis.report_json or "{}"))
    if not report.get("discovery"):
        abort(404)
    by_candidate = {
        item["candidate_id"]: item
        for item in report.get("candidate_results", [])
        if isinstance(item, dict) and isinstance(item.get("candidate_id"), int)
    }
    recommendations = Recommendation.query.filter_by(analysis_id=analysis.id).order_by(Recommendation.rank).all()
    ranked = []
    for rec in recommendations:
        payload = by_candidate.get(rec.candidate_company_id)
        if payload is None:
            payload = {
                "evidence_coverage": None,
                "confidence": rec.confidence,
                "opportunity": rec.why or "لا يوجد تفسير محفوظ لهذا الترشيح المحلي.",
                "evidence_summary": "",
                "risks": [rec.risks] if rec.risks else [],
                "caveats": [],
                "next_step": "تحقق من ملف الشركة ومصادر البيانات قبل التواصل أو اتخاذ قرار.",
                "criteria": [],
            }
        ranked.append((rec, rec.candidate, payload))
    return render_template(
        "discover_results.html",
        company_a=analysis.company_a,
        analysis=analysis,
        ranked=ranked,
        analysis_type=analysis.analysis_type,
        discovery_report=report,
        discovery_criterion_labels=DISCOVERY_CRITERION_LABELS,
    )


@bp.route("/discover", methods=["GET", "POST"])
def discover():
    companies = Company.query.order_by(Company.official_name).all()
    if request.method == "POST":
        a_id = request.form.get("company_a")
        analysis_type = request.form.get("analysis_type", "partnership")
        if analysis_type not in ("partnership", "joint_venture"):
            flash("نوع التحليل غير متاح. اختر شراكة استراتيجية أو مشروعاً مشتركاً.", "err")
            return redirect(url_for("main.discover"))
        return _run_discovery(a_id, analysis_type)
    return render_template("discover.html", companies=companies, ai_enabled=llm_configured())


@bp.route("/investment", methods=["GET", "POST"])
def removed_investment_analysis():
    flash("تحليل الاستثمار غير متاح حالياً. يمكنك مقارنة الشركات أو استكشاف فرص التعاون.", "ok")
    return redirect(url_for("main.compare"))


@bp.route("/system")
@roles_required("admin")
def system_monitor():
    metrics = dashboard_metrics()
    gemini = gemini_api_metrics()
    return render_template("system.html", metrics=metrics, gemini=gemini)


@bp.route("/admin/ai-settings", methods=["GET", "POST"])
@roles_required("admin")
def ai_settings():
    if "ai_settings_csrf" not in session:
        session["ai_settings_csrf"] = secrets.token_urlsafe(32)
    env_key = bool((current_app.config.get("LLM_API_KEY") or "").strip())
    saved_key = saved_admin_api_key()
    encryption_configured = encryption_ready()

    if request.method == "POST":
        supplied_token = request.form.get("csrf_token", "")
        if not hmac.compare_digest(session.get("ai_settings_csrf", ""), supplied_token):
            abort(400)
        if env_key:
            flash("المفتاح مضبوط من إعدادات بيئة الخادم؛ لا يمكن تغييره من هذه الصفحة.", "err")
        elif request.form.get("action") == "remove":
            save_admin_api_key(None)
            flash("تم حذف مفتاح Gemini المحلي. سيعود التطبيق إلى وضع القواعد التجريبية.", "success")
        else:
            value = request.form.get("api_key", "").strip()
            if not encryption_configured:
                flash("يلزم ضبط GEMINI_ENCRYPTION_KEY وتثبيت متطلبات المشروع أولاً. المفتاح لم يُحفظ.", "err")
            elif not value:
                flash("أدخل مفتاح Gemini أولاً.", "err")
            elif len(value) > 2048 or any(ch.isspace() for ch in value):
                flash("صيغة المفتاح غير مقبولة. تحقق من القيمة وأعد إدخالها.", "err")
            else:
                save_admin_api_key(value)
                flash("حُفظ المفتاح محلياً. أجرِ مقارنة لاختبار الاتصال؛ لا يمكن استرجاع قيمته من الصفحة.", "success")
        return redirect(url_for("main.ai_settings"))

    return render_template("ai_settings.html", env_key=env_key, saved_key=saved_key, encryption_configured=encryption_configured, csrf_token=session["ai_settings_csrf"])


@bp.route("/system/simulate", methods=["POST"])
@roles_required("admin")
def simulate():
    kind = request.form.get("kind")
    if kind == "ai_timeout":
        companies = Company.query.limit(2).all()
        _run_comparison(str(companies[0].id), str(companies[1].id), "partnership", "timeout")
        flash("تم محاكاة انتهاء مهلة واجهة الذكاء الاصطناعي.", "ok")
        return redirect(url_for("main.system_monitor"))
    if kind == "missing_company":
        record_event("fault_simulation", False, error_code="simulated_missing_company", details="Missing company simulation; no provider request")
        flash("سُجّل فشل تحقق: شركة ناقصة.", "ok")
        return redirect(url_for("main.system_monitor"))
    if kind == "delayed_analysis":
        t0 = time.time()
        time.sleep(1.2)
        record_event("fault_simulation", True, latency_ms=int((time.time() - t0) * 1000), error_code="simulated_delay", details="Delayed analysis simulation; no provider request")
        flash("سُجّل تحليل متأخر لأغراض المراقبة.", "ok")
        return redirect(url_for("main.system_monitor"))
    return redirect(url_for("main.system_monitor"))


@bp.route("/reports")
def reports():
    analyses = Analysis.query.filter(Analysis.analysis_type.in_(("partnership", "joint_venture"))).order_by(Analysis.created_at.desc()).limit(20).all()
    discovery_ids = set()
    for item in analyses:
        try:
            if json.loads(item.report_json or "{}").get("discovery"):
                discovery_ids.add(item.id)
        except (TypeError, ValueError):
            continue
    return render_template("reports.html", analyses=analyses, discovery_analysis_ids=discovery_ids)


@bp.route("/market-data")
def market_data():
    indicators = MarketContextIndicator.query.order_by(
        MarketContextIndicator.metric_code,
        MarketContextIndicator.sector,
    ).all()
    return render_template("market_data.html", indicators=indicators)


@bp.route("/reports/analysis/<int:analysis_id>.json")
def analysis_json(analysis_id):
    analysis = Analysis.query.get_or_404(analysis_id)
    report = _brand_analysis_text(json.loads(analysis.report_json or "{}"))
    return Response(json.dumps(report, ensure_ascii=False), mimetype="application/json")


def _run_comparison(a_id, b_id, analysis_type, simulate=None):
    t0 = time.time()
    try:
        if not a_id or not b_id or a_id == b_id:
            record_event("validation_failure", False, error_code="invalid_pair", details="same or missing company")
            flash("اختر شركتين مختلفتين.", "err")
            return redirect(url_for("main.compare"))
        company_a = Company.query.get(int(a_id))
        company_b = Company.query.get(int(b_id))
        if not company_a or not company_b:
            record_event("validation_failure", False, error_code="missing_company", details=f"{a_id},{b_id}")
            flash("بيانات الشركة غير موجودة في السجل المحلي.", "err")
            return redirect(url_for("main.compare"))
        score_context = (
            ai_score_context(company_a, company_b, analysis_type)
            if llm_configured()
            else analyze_pair(company_a, company_b, analysis_type)
        )
        ai_scores, narrative, mode, tok_in, tok_out = analyze_with_ai(
            company_a, company_b, analysis_type, score_context, simulate_timeout=(simulate == "timeout")
        )
        score_payload = _brand_analysis_text(ai_scores or score_context)
        narrative = _brand_analysis_text(narrative)
        latency = int((time.time() - t0) * 1000)
        report = {
            "scores": score_payload,
            "narrative": narrative,
            "facts_only_financials": True,
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }
        analysis = Analysis(
            company_a_id=company_a.id,
            company_b_id=company_b.id,
            analysis_type=analysis_type,
            direction="a_to_b",
            status="completed",
            scoring_version="mishrak-ai-v1" if mode == "llm" else SCORING_VERSION,
            mode=mode,
            latency_ms=latency,
            report_json=json.dumps(report, ensure_ascii=False),
        )
        db.session.add(analysis)
        db.session.flush()
        for c in score_payload["criteria"]:
            db.session.add(
                CompatibilityScore(
                    analysis_id=analysis.id,
                    criterion=c["criterion"],
                    score=c["score"],
                    weight=c["weight"],
                    confidence=c["confidence"],
                    explanation=c["explanation"],
                    evidence=c.get("evidence"),
                )
            )
        db.session.commit()
        record_event(
            "ai_analysis",
            True,
            latency_ms=latency,
            details=f"analysis_id={analysis.id};mode={mode}",
        )
        if mode == "demo_rules":
            record_event("ai_demo", True, latency_ms=latency, details="deterministic demo narrative; no Gemini request")
        return redirect(url_for("main.analysis_detail", analysis_id=analysis.id))
    except Exception as exc:
        db.session.rollback()
        latency = int((time.time() - t0) * 1000)
        response_status = getattr(getattr(exc, "response", None), "status_code", None)
        if response_status in (429, 503):
            error_code = f"gemini_{response_status}"
            user_error = "خدمة Gemini مشغولة أو غير متاحة مؤقتاً. انتظر قليلًا ثم أعد التحليل."
        elif response_status in (401, 403):
            error_code = "gemini_auth"
            user_error = "تعذر التحقق من مفتاح Gemini. راجع المفتاح وإعدادات الخدمة."
        elif isinstance(exc, TimeoutError) or "timeout" in str(exc).lower():
            error_code = "timeout"
            user_error = "استغرق الاتصال بخدمة الذكاء الاصطناعي وقتاً طويلاً. أعد المحاولة بعد قليل."
        elif isinstance(exc, requests.ConnectionError):
            error_code = "gemini_connection"
            user_error = "تعذر الوصول إلى خادم Gemini عبر الإنترنت. تحقق من اتصال الخادم بالإنترنت والسماح باتصال HTTPS إلى generativelanguage.googleapis.com:443، ثم أعد التحليل."
        else:
            error_code = "ai_error"
            user_error = "تعذر إكمال التحليل بسبب مشكلة مؤقتة في خدمة الذكاء الاصطناعي. أعد المحاولة بعد قليل."
        failed = Analysis(
            company_a_id=int(a_id) if a_id else 1,
            company_b_id=int(b_id) if b_id else None,
            analysis_type=analysis_type,
            status="failed",
            scoring_version=SCORING_VERSION,
            mode="error",
            latency_ms=latency,
            error_message=user_error,
            report_json="{}",
        )
        try:
            db.session.add(failed)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
        if simulate == "timeout":
            record_event("fault_simulation", False, latency_ms=latency, error_code="simulated_timeout", details="AI timeout simulation; no provider request")
        record_event("ai_analysis", False, latency_ms=latency, error_code=error_code, details="Analysis failed; see Gemini request events for provider diagnostics.")
        flash(user_error, "err")
        return redirect(url_for("main.compare"))


def _run_discovery(a_id, analysis_type):
    t0 = time.time()
    company_a = Company.query.get(int(a_id)) if a_id else None
    if not company_a:
        record_event("validation_failure", False, error_code="missing_company", details="discovery")
        flash("اختر شركة من السجل المحلي.", "err")
        return redirect(url_for("main.discover"))
    candidates = Company.query.filter(Company.id != company_a.id).all()
    ranked = rank_candidates(company_a, candidates, analysis_type)
    ai_result = None
    mode = "deterministic"
    if llm_configured() and ranked:
        screened = [row[2] for row in ranked[:10]]
        try:
            ai_result = _brand_analysis_text(analyze_discovery_with_ai(company_a, screened, analysis_type))
            mode = "llm_discovery"
        except requests.HTTPError as exc:
            db.session.rollback()
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status == 429:
                message, code = "تجاوز Mishrak AI حد الطلبات مؤقتاً. انتظر قليلاً ثم أعد اكتشاف الفرص.", "rate_limit"
            elif status == 503:
                message, code = "Mishrak AI مشغول حالياً. لم نحفظ ترتيباً محلياً على أنه تحليل ذكي؛ أعد المحاولة لاحقاً.", "provider_unavailable"
            elif status in (401, 403):
                message, code = "تعذر التحقق من مفتاح الخدمة. راجع المفتاح في إعدادات المدير.", "authentication"
            else:
                message, code = "تعذر تحليل المرشحين بخدمة Mishrak AI. لم يُحفظ هذا الاكتشاف؛ حاول لاحقاً.", "provider_error"
            record_event("discovery", False, latency_ms=int((time.time() - t0) * 1000), error_code=code, details=f"http_status={status or 'unknown'}")
            flash(message, "err")
            return redirect(url_for("main.discover"))
        except (requests.RequestException, TimeoutError) as exc:
            db.session.rollback()
            code = "timeout" if isinstance(exc, (requests.Timeout, TimeoutError)) else "connection_error"
            message = "انتهت مهلة تحليل المرشحين. أعد المحاولة." if code == "timeout" else "تعذر الاتصال بخدمة Mishrak AI. تحقق من اتصال الخادم ثم أعد المحاولة."
            record_event("discovery", False, latency_ms=int((time.time() - t0) * 1000), error_code=code, details="AI discovery provider request failed")
            flash(message, "err")
            return redirect(url_for("main.discover"))
        except (ValueError, RuntimeError) as exc:
            db.session.rollback()
            record_event("discovery", False, latency_ms=int((time.time() - t0) * 1000), error_code="invalid_ai_response", details=type(exc).__name__)
            flash("وصل رد من Mishrak AI لكنه لم يجتز التحقق المطلوب. لم يُحفظ الاكتشاف؛ أعد المحاولة.", "err")
            return redirect(url_for("main.discover"))

    latency = int((time.time() - t0) * 1000)
    if ai_result:
        result_by_id = {item["candidate_id"]: item for item in ai_result["candidate_results"]}
        ordered = [row[2] for row in ranked[:10] if row[2].id in result_by_id]
        ordered.sort(key=lambda candidate: next(
            index for index, item in enumerate(ai_result["candidate_results"])
            if item["candidate_id"] == candidate.id
        ))
        selected = ordered[:5]
        result_report = {
            "discovery": True,
            "mode": "llm_discovery",
            "provider_label": "Mishrak AI",
            "count_ranked": len(ranked),
            "count_screened": len(ordered),
            "summary": ai_result["summary"],
            "limitations": ai_result["limitations"],
            "candidate_results": ai_result["candidate_results"],
        }
    else:
        selected = [row[2] for row in ranked[:5]]
        result_report = {
            "discovery": True,
            "mode": "deterministic",
            "count_ranked": len(ranked),
            "summary": "هذا ترتيب محلي أولي بالقواعد؛ لم يُقيّم بواسطة Mishrak AI.",
            "limitations": ["الترتيب داخل السجل المحلي فقط، ولا يؤكد وجود اتفاق أو فرصة تجارية."],
        }
    analysis = Analysis(
        company_a_id=company_a.id,
        company_b_id=None,
        analysis_type=analysis_type,
        status="completed",
        scoring_version="mishrak-discovery-v1" if mode == "llm_discovery" else SCORING_VERSION,
        mode=mode,
        latency_ms=latency,
        report_json=json.dumps(result_report, ensure_ascii=False),
    )
    db.session.add(analysis)
    db.session.flush()
    for i, cand in enumerate(selected, start=1):
        if ai_result:
            payload = result_by_id[cand.id]
            score = payload["overall_score"]
            coverage = payload["evidence_coverage"]
            why = "؛ ".join(item for item in (payload["opportunity"], payload["evidence_summary"]) if item)
            risk_items = payload["risks"] + payload["caveats"]
            risks = "؛ ".join(risk_items) or "لم تظهر مخاطر محددة من الأدلة المقدمة؛ يلزم التحقق قبل أي قرار."
            limitations = "؛ ".join(ai_result["limitations"] + payload["caveats"])
            if coverage < 1:
                limitations = (limitations + "؛ " if limitations else "") + "تغطية الأدلة محدودة لبعض المعايير."
        else:
            original = next(row for row in ranked if row[2].id == cand.id)
            score, coverage, _, payload = original
            why = payload["recommendation"] + " " + "؛ ".join(payload.get("strengths") or [])
            risks = "؛ ".join((payload.get("risks") or []) + (payload.get("missing_information") or []))
            limitations = "ترشيح محلي بالقواعد فقط؛ لا يؤكد وجود اتفاق أو فرصة تجارية."
        rec = Recommendation(
            analysis_id=analysis.id,
            candidate_company_id=cand.id,
            rank=i,
            overall_score=score,
            confidence=payload["confidence"] if not ai_result else payload["confidence"],
            why=why,
            risks=risks,
            limitations=limitations,
        )
        db.session.add(rec)
    db.session.commit()
    record_event("discovery", True, latency_ms=latency, details=f"analysis_id={analysis.id};mode={mode}")
    return redirect(url_for("main.discovery_detail", analysis_id=analysis.id))
