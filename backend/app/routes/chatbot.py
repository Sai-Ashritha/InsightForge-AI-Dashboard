from fastapi import APIRouter, Depends
from pydantic import BaseModel
import pandas as pd

from app.database.db import fetch_table
from app.auth import get_current_user
from app.services.anomaly_detector import detect_anomalies
from app.services.recommendations import generate_recommendations
from app.services.insight_generator import InsightGenerator
from app.services.kpi_calculator import get_live_kpis

router = APIRouter()


class ChatMessage(BaseModel):
    question: str


@router.post("/chat")
async def chat(message: ChatMessage, current_user=Depends(get_current_user)):
    """Process a user question and generate an AI response."""
    try:
        question = message.question.strip()
        if not question:
            return {
                "status": "error",
                "message": "Please enter a question.",
                "response": ""
            }

        from app.routes.chat import _build_full_context
        from app.services.local_llm import LocalLLM, build_executive_prompt, deterministic_answer

        ctx = _build_full_context()
        prompt = build_executive_prompt(
            question=question,
            kpis=ctx["kpis"],
            anomalies=ctx["anomalies"],
            recommendations=ctx["recommendations"],
            sales_declines=ctx["sales_declines"],
            forecast_data=ctx["forecast_data"],
            inventory_data=ctx["inventory_data"],
        )
        fallback = deterministic_answer(
            question=question,
            kpis=ctx["kpis"],
            anomalies=ctx["anomalies"],
            recommendations=ctx["recommendations"],
            sales_declines=ctx["sales_declines"],
            forecast_data=ctx["forecast_data"],
            inventory_data=ctx["inventory_data"],
        )
        response, provider = LocalLLM().generate(prompt, fallback)

        return {
            "status": "success",
            "question": question,
            "response": response,
            "provider": provider,
            "context": {
                "kpis": ctx["kpis"],
                "anomalies_detected": len(ctx["anomalies"]),
                "recommendations_available": len(ctx["recommendations"]),
                "declining_products": len(ctx["sales_declines"]),
            }
        }

    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "response": "Sorry, I encountered an error processing your question."
        }


@router.get("/insights/executive-summary")
def get_executive_summary():
    """Generate an executive summary of the manufacturing operation."""
    try:
        sales_data = fetch_table("sales")

        kpis = get_live_kpis()

        anomalies = []
        if sales_data:
            df = pd.DataFrame(sales_data)
            anomaly_result = detect_anomalies(df, contamination=0.05)
            anomalies = anomaly_result.get("anomalies", [])

        recommendations = generate_recommendations(kpis, anomalies)

        insight_gen = InsightGenerator()

        summary_text = insight_gen.generate_kpi_summary(kpis)
        anomaly_text = insight_gen.generate_anomaly_insights(anomalies, kpis.get("total_records", 100))
        recommendation_text = insight_gen.generate_recommendation_summary(recommendations)

        return {
            "status": "success",
            "executive_summary": f"{summary_text} {anomaly_text} {recommendation_text}",
            "kpi_summary": summary_text,
            "anomaly_summary": anomaly_text,
            "recommendation_summary": recommendation_text,
            "key_metrics": {
                "revenue": f"₹{int(kpis['revenue'] / 100000)}L",
                "efficiency": f"{kpis['efficiency']}%",
                "defect_rate": f"{kpis['defect_rate']}%",
                "inventory": f"{kpis['inventory']} units",
            }
        }

    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc)
        }


@router.get("/insights/health-check")
def get_health_insight():
    """Get an AI-generated health check of the manufacturing operation."""
    try:
        sales_data = fetch_table("sales")

        kpis = get_live_kpis()

        efficiency = kpis.get("efficiency", 0)
        defect_rate = kpis.get("defect_rate", 0)
        inventory = kpis.get("inventory", 0)

        health_score = 100
        health_issues = []

        if efficiency < 80:
            health_score -= 20
            health_issues.append("Production efficiency is critically low")
        elif efficiency < 85:
            health_score -= 10
            health_issues.append("Production efficiency needs improvement")

        if defect_rate > 3:
            health_score -= 15
            health_issues.append("Defect rate is above acceptable threshold")

        if inventory < 5000:
            health_score -= 20
            health_issues.append("Inventory levels are critically low")
        elif inventory < 10000:
            health_score -= 10
            health_issues.append("Inventory levels are lower than optimal")

        health_status = "Excellent" if health_score >= 85 else "Good" if health_score >= 70 else "Fair" if health_score >= 50 else "Poor"

        summary = f"Manufacturing operation health: {health_status} (Score: {health_score}/100). "
        if health_issues:
            summary += "Issues identified: " + ", ".join(health_issues) + "."
        else:
            summary += "No critical issues detected."

        return {
            "status": "success",
            "health_status": health_status,
            "health_score": health_score,
            "summary": summary,
            "issues": health_issues
        }

    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc)
        }
