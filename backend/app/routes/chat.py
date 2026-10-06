import json
from typing import Iterator

import pandas as pd
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.auth import get_current_user
from app.database.db import fetch_table
from app.services.anomaly_detector import detect_anomalies
from app.services.alert_engine import detect_real_alerts_and_causes
from app.services.forecasting import train_and_forecast_dynamic
from app.services.local_llm import LocalLLM, build_executive_prompt, deterministic_answer
from app.services.recommendations import generate_recommendations
from app.services.data_quality import assess_data_quality
from app.services.dynamic_engine import compute_dynamic_analytics, get_active_dataset

router = APIRouter(tags=["local-ai"])

class StreamChatMessage(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


def _build_full_context():
    active_df = get_active_dataset()
    if active_df is None or active_df.empty:
        sales_rows = fetch_table("sales")
        active_df = pd.DataFrame(sales_rows) if sales_rows else pd.DataFrame()

    dynamic = compute_dynamic_analytics(active_df)
    quality = assess_data_quality(active_df)
    anomalies_res = detect_anomalies(active_df)
    anomalies = anomalies_res.get("anomalies", [])

    alerts = detect_real_alerts_and_causes(active_df)
    sales_declines = alerts.get("declining_products", [])
    forecast_res = train_and_forecast_dynamic(active_df)
    kpis = {item["key"]: item.get("raw_value") for item in dynamic.get("kpis", []) if item.get("key")}
    kpis.update({
        "total_records": len(active_df),
        "quality_score": quality.get("quality_score", 0),
        "columns": [str(column) for column in active_df.columns],
        "dataset_name": getattr(active_df, "attrs", {}).get("file_name", "Active dataset"),
    })

    recommendations = generate_recommendations(
        data=kpis,
        anomalies=anomalies,
        sales_declines=sales_declines,
        forecast_data=forecast_res,
        inventory_data=[],
    )

    return {
        "kpis": kpis,
        "anomalies": anomalies,
        "sales_declines": sales_declines,
        "forecast_data": forecast_res,
        "inventory_data": [],
        "dataset": {
            "name": kpis["dataset_name"],
            "columns": kpis["columns"],
            "row_count": len(active_df),
            "quality": quality,
            "alerts": alerts.get("alerts", []),
        },
        "recommendations": recommendations,
    }


@router.post("/chat/stream")
def stream_chat(message: StreamChatMessage, current_user=Depends(get_current_user)):
    ctx = _build_full_context()
    prompt = build_executive_prompt(
        question=message.question.strip(),
        kpis=ctx["kpis"],
        anomalies=ctx["anomalies"],
        recommendations=ctx["recommendations"],
        sales_declines=ctx["sales_declines"],
        forecast_data=ctx["forecast_data"],
        inventory_data=ctx["inventory_data"],
    )
    fallback = deterministic_answer(
        question=message.question.strip(),
        kpis=ctx["kpis"],
        anomalies=ctx["anomalies"],
        recommendations=ctx["recommendations"],
        sales_declines=ctx["sales_declines"],
        forecast_data=ctx["forecast_data"],
        inventory_data=ctx["inventory_data"],
    )
    answer, provider = LocalLLM().generate(prompt, fallback)

    def event_stream() -> Iterator[str]:
        yield f"data: {json.dumps({'provider': provider, 'type': 'meta'})}\n\n"
        # Stream by words / chunks
        words = answer.split(" ")
        for index, word in enumerate(words):
            suffix = " " if index < len(words) - 1 else ""
            yield f"data: {json.dumps({'type': 'token', 'content': word + suffix})}\n\n"
        yield "data: {\"type\":\"done\"}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

