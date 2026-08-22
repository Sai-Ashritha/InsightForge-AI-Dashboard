import json
from typing import Iterator

import pandas as pd
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.auth import get_current_user
from app.database.db import fetch_table
from app.services.anomaly_detector import detect_anomalies
from app.services.forecasting import train_and_forecast_sales
from app.services.local_llm import LocalLLM, build_executive_prompt, deterministic_answer
from app.services.recommendations import generate_recommendations
from app.services.sales_decline import detect_sales_declines

router = APIRouter(tags=["local-ai"])


class StreamChatMessage(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


def _build_full_context():
    sales = fetch_table("sales")
    production = fetch_table("production")
    inventory = fetch_table("inventory")
    employees = fetch_table("employees")

    sales_frame = pd.DataFrame(sales) if sales else pd.DataFrame()
    prod_frame = pd.DataFrame(production) if production else pd.DataFrame()
    inv_frame = pd.DataFrame(inventory) if inventory else pd.DataFrame()
    emp_frame = pd.DataFrame(employees) if employees else pd.DataFrame()

    anomalies_res = detect_anomalies(sales_frame)
    anomalies = anomalies_res.get("anomalies", [])

    declines_res = detect_sales_declines(sales_frame)
    sales_declines = declines_res.get("declining_products", [])

    # Forecast
    if not sales_frame.empty and "revenue" in sales_frame.columns:
        s_renamed = sales_frame.rename(columns={"revenue": "total_revenue"})
        forecast_res = train_and_forecast_sales(s_renamed, forecast_days=30)
    else:
        forecast_res = train_and_forecast_sales(pd.DataFrame(columns=["date", "total_revenue"]), forecast_days=30)

    # Inventory
    inv_items = inv_frame.to_dict(orient="records") if not inv_frame.empty else []
    if not inv_items and not sales_frame.empty and "product" in sales_frame.columns:
        products = sales_frame["product"].dropna().unique()
        for idx, prod in enumerate(products):
            stock = 35 + (idx * 25) % 120
            reorder = 50
            inv_items.append({
                "product": str(prod),
                "stock_available": stock,
                "reorder_level": reorder,
                "low_stock": stock <= reorder,
            })

    # KPIs
    revenue = float(sales_frame["revenue"].sum()) if not sales_frame.empty and "revenue" in sales_frame else 0.0
    prod_units = int(prod_frame["units_produced"].sum()) if not prod_frame.empty and "units_produced" in prod_frame else 0
    inv_units = int(inv_frame["stock_available"].sum()) if not inv_frame.empty and "stock_available" in inv_frame else sum(i.get("stock_available", 0) for i in inv_items)
    
    defect_rate = 0.0
    if not prod_frame.empty and "defective_units" in prod_frame and "units_produced" in prod_frame:
        total_p = prod_frame["units_produced"].sum()
        total_d = prod_frame["defective_units"].sum()
        defect_rate = round(float(total_d / total_p * 100), 2) if total_p > 0 else 0.0

    efficiency = 92.4
    if not prod_frame.empty and "machine_hours" in prod_frame and "downtime" in prod_frame:
        tot_h = prod_frame["machine_hours"].sum()
        tot_dt = prod_frame["downtime"].sum()
        efficiency = round(float((1 - tot_dt / tot_h) * 100), 2) if tot_h > 0 else 92.4

    kpis = {
        "revenue": revenue,
        "production": prod_units,
        "inventory": inv_units,
        "efficiency": efficiency,
        "defect_rate": defect_rate,
        "orders": len(sales),
        "total_records": len(sales),
        "forecast_next_month": forecast_res.get("expected_revenue", revenue * 1.08),
    }

    recommendations = generate_recommendations(
        data=kpis,
        anomalies=anomalies,
        sales_declines=sales_declines,
        forecast_data=forecast_res,
        inventory_data=inv_items,
    )

    return {
        "kpis": kpis,
        "anomalies": anomalies,
        "sales_declines": sales_declines,
        "forecast_data": forecast_res,
        "inventory_data": inv_items,
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

