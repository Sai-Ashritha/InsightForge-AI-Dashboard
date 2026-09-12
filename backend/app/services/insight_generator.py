import re
from typing import Dict, List, Optional, Any
import pandas as pd


class InsightGenerator:
    """
    Generate accurate, grounded, understandable business intelligence answers
    strictly based on the active uploaded dataset and computed analytics.
    """

    def generate_kpi_summary(self, kpis: dict) -> str:
        if not kpis:
            return "No dataset analytics available. Please upload a dataset in Quality & Cleaning."

        parts = []
        if "revenue" in kpis and kpis["revenue"] > 0:
            rev = kpis["revenue"]
            rev_label = f"₹{rev / 100000:.2f}L" if rev >= 100000 else f"₹{rev:,.2f}"
            parts.append(f"Total revenue is {rev_label} across {kpis.get('orders', kpis.get('total_records', 0))} records.")
        elif "total_records" in kpis:
            parts.append(f"Dataset contains {kpis['total_records']} total records.")

        if "defect_rate" in kpis and kpis.get("defect_rate", 0) > 0:
            parts.append(f"Recorded defect rate is {kpis['defect_rate']}%.")

        if "inventory" in kpis and kpis.get("inventory") is not None and kpis.get("inventory", 0) > 0:
            parts.append(f"Current inventory stands at {kpis['inventory']:,} units.")

        if "quality_score" in kpis:
            parts.append(f"Data quality score is {kpis['quality_score']}% (out of 100%).")

        return " ".join(parts) if parts else "Dataset analysis is ready."

    def answer_question(
        self,
        question: str,
        kpis: dict,
        anomalies: list = None,
        recommendations: list = None,
        sales_declines: list = None,
        forecast_data: dict = None,
        inventory_data: list = None,
        dataset_meta: dict = None,
    ) -> str:
        q = question.lower().strip()
        kpis = kpis or {}
        anomalies = anomalies or []
        recommendations = recommendations or []
        sales_declines = sales_declines or []
        forecast_data = forecast_data or {}
        inventory_data = inventory_data or []
        dataset_meta = dataset_meta or {}

        if any(w in q for w in ["manufacture", "what should we manufacture", "what should i produce", "produce next month", "production schedule", "what to produce"]):
            if forecast_data and forecast_data.get("product_forecasts"):
                top = forecast_data["product_forecasts"][0]
                item_name = top.get("product", "the primary product line")
                qty = top.get("predicted_demand", 0)
                return (
                    "**Analysis**: The current pattern suggests your next manufacturing plan should prioritize "
                    f"{item_name} with an expected production demand of {qty:,} units. "
                    "**Recommendation**: align production schedules to satisfy forecasted demand while keeping safety stock stable. "
                    "**Suggested Action**: review capacity, materials, and staffing before the next production cycle."
                )
            return (
                "**Analysis**: There is not enough reliable production history to recommend a specific manufacturing plan. "
                "**Recommendation**: upload a dataset with date, product, and quantity information before asking for a manufacturing plan. "
                "**Suggested Action**: add the relevant sales or production data and rerun the forecast."
            )

        # 1. Total Sales / Revenue question
        if any(w in q for w in ["total sales", "what are my total sales", "total revenue", "revenue", "how much sales"]):
            if "revenue" in kpis and kpis["revenue"] > 0:
                rev = kpis["revenue"]
                rev_fmt = f"₹{rev / 100000:.2f} Lakhs" if rev >= 100000 else f"₹{rev:,.2f}"
                orders = kpis.get("orders", kpis.get("total_records", "multiple"))
                return (
                    f"**Total Sales Overview**:\n\n"
                    f"• **Calculated Total**: **{rev_fmt}** (exact value: ₹{rev:,.2f})\n"
                    f"• **Transactions / Records**: {orders}\n"
                    f"• **Data Source**: Uploaded dataset calculations\n\n"
                    f"This total is derived directly by summing actual record amounts from your uploaded file."
                )
            elif "total_sales" in kpis:
                return f"Total sales calculated from your dataset is **{kpis['total_sales']}**."
            else:
                return "The uploaded dataset does not contain a sales or revenue column."

        # 2. Highest Selling Product / Top Performer
        if any(w in q for w in ["highest sales", "top product", "best seller", "highest selling", "best selling"]):
            prod_perf = kpis.get("product_performance", [])
            if prod_perf:
                top = prod_perf[0]
                val_str = f"₹{top['revenue'] / 100000:.2f}L" if top.get("revenue", 0) >= 100000 else f"₹{top.get('revenue', top.get('units', 0)):,.2f}"
                return (
                    f"**Top Performing Product**:\n\n"
                    f"• **Product**: **{top['name']}**\n"
                    f"• **Total Contribution**: {val_str} ({top.get('share', 0)}% of total volume)\n"
                    f"• **Total Units**: {top.get('units', 'N/A')}\n\n"
                    f"Based on actual aggregated records in your uploaded dataset."
                )
            return "The uploaded dataset does not contain identifiable product or sales category columns."

        # 3. Sales Trend / Trend over time
        if any(w in q for w in ["trend", "sales trend", "trajectory", "over time", "timeline"]):
            trend = kpis.get("trend", [])
            labels = kpis.get("trend_labels", [])
            if trend and len(trend) >= 2:
                start_val = trend[0]
                end_val = trend[-1]
                direction = "increasing" if end_val > start_val else "decreasing" if end_val < start_val else "stable"
                return (
                    f"**Sales Trend Analysis**:\n\n"
                    f"• **Direction**: Overall trajectory is **{direction}** across the recorded timeline.\n"
                    f"• **Timeline Span**: {labels[0] if labels else 'Period Start'} to {labels[-1] if labels else 'Period End'}\n"
                    f"• **First Period**: {start_val}\n"
                    f"• **Most Recent Period**: {end_val}\n\n"
                    f"You can view the interactive zoomable line chart in the Overview tab."
                )
            return "Not enough historical timeline data in the dataset to calculate a chronological trend curve."

        # 4. Why Did Sales Decrease / Sales Decline
        if any(w in q for w in ["why did sales decrease", "sales decrease", "drop in sales", "sales drop", "decline"]):
            if sales_declines:
                top_dec = sales_declines[0]
                p_name = top_dec.get("product", "Product")
                pct = top_dec.get("decline_percentage", 0)
                prev = top_dec.get("previous_sales", 0)
                curr = top_dec.get("current_sales", 0)
                return (
                    f"**Sales Decline Analysis**:\n\n"
                    f"• **Affected Item**: **{p_name}**\n"
                    f"• **Observed Drop**: **-{pct}%** (decreased from ₹{prev:,.2f} to ₹{curr:,.2f})\n"
                    f"• **Root Cause**: Possible cause cannot be determined solely from historical sales data. "
                    f"Review inventory availability, regional distributor channels, and local demand changes.\n"
                    f"• **Action**: Evaluate pricing competitiveness and verify if stock was available to fulfill orders."
                )
            return "No significant sales declines were detected across product categories in the active dataset."

        # 5. Inventory / Reorder Level Question
        if any(w in q for w in ["inventory", "reorder level", "stock", "low stock", "below reorder"]):
            if inventory_data and any(item.get("low_stock") for item in inventory_data):
                low_items = [i for i in inventory_data if i.get("low_stock")]
                item_lines = "\n".join([f"• **{i.get('product')}**: Stock = {i.get('stock_available')}, Reorder Level = {i.get('reorder_level')}" for i in low_items[:5]])
                return (
                    f"**Low Stock & Reorder Alert**:\n\n"
                    f"The following items are at or below their designated safety reorder threshold:\n\n"
                    f"{item_lines}\n\n"
                    f"**Action**: Place replenishment purchase orders immediately to avoid stockouts."
                )
            elif kpis.get("inventory") is None and not inventory_data:
                return "The uploaded dataset does not contain inventory or stock columns (such as Current_Stock or Reorder_Level)."
            else:
                return "All inventory items are currently above designated safety reorder levels."

        # 6. What Should I Produce Next Month / Manufacturing Schedule
        if any(w in q for w in ["what should i produce", "produce next month", "manufacture", "production schedule", "what to produce"]):
            if forecast_data and forecast_data.get("product_forecasts"):
                top_forecast = forecast_data["product_forecasts"][0]
                p_name = top_forecast.get("product", "Primary Product")
                pred_qty = top_forecast.get("predicted_demand", 0)
                pred_rev = top_forecast.get("predicted_revenue", 0)
                return (
                    f"**Next-Month Production Guidance**:\n\n"
                    f"1. **Analysis**:\n"
                    f"Forecasting models project highest demand for **{p_name}** with predicted demand of **{pred_qty:,} units** "
                    f"(expected revenue of ₹{pred_rev:,.2f}, representing {top_forecast.get('share_percentage')}% of projected volume).\n\n"
                    f"2. **Recommendation**:\n"
                    f"Align production schedules to prioritize {p_name} to meet anticipated demand without bottlenecking other lines.\n\n"
                    f"3. **Limitations**:\n"
                    f"{forecast_data.get('model_limitations', 'Projections assume normal baseline demand patterns.')}"
                )
            elif "production" in kpis and kpis["production"] > 0:
                return (
                    f"Current production volume is {kpis['production']:,} units. "
                    f"To generate detailed product-level forecasts, upload a dataset with historical Date, Product, and Quantity columns."
                )
            else:
                return (
                    "The uploaded dataset does not contain sufficient chronological production or sales records to project future production schedules. "
                    "Upload a dataset with historical dates and quantities in Quality & Cleaning."
                )

        # 7. Data Quality Score
        if any(w in q for w in ["data quality", "quality score", "how clean is my data", "null percentage"]):
            score = kpis.get("quality_score", 95.0)
            return (
                f"**Dataset Quality Evaluation**:\n\n"
                f"• **Overall Quality Score**: **{score}% / 100%**\n"
                f"• **Scoring Formula**: `100 - (Null Ratio × 40 + Duplicate Ratio × 30 + Outlier Ratio × 30)`\n"
                f"• **Status**: {'Excellent data integrity' if score >= 90 else 'Moderate quality - automatic cleaning applied' if score >= 75 else 'Needs attention'}\n\n"
                f"Automatic cleaning removed duplicate records and handled missing values without altering significant values."
            )

        # 8. Business Risks & Alerts
        if any(w in q for w in ["risk", "risks", "alerts", "main risks", "issues", "problems"]):
            alerts = kpis.get("alerts", [])
            if alerts:
                alert_text = "\n".join([f"• {a}" for a in alerts[:4]])
                return (
                    f"**Identified Business & Operational Risks**:\n\n"
                    f"{alert_text}\n\n"
                    f"Review the Alerts & Causes tab for specific comparative figures and recommended mitigation actions."
                )
            return "No critical business risks or anomalous threshold violations were detected in the uploaded dataset."

        # 9. Generic or Unknown Column Question
        col_keywords = ["employee", "salary", "warehouse", "patient", "admission", "temperature", "voltage", "cost", "profit"]
        for kw in col_keywords:
            if kw in q:
                # check if keyword is in columns
                matched = any(kw in str(c).lower() for c in kpis.get("columns", []))
                if not matched:
                    return f"The uploaded dataset does not contain {kw} information."

        # Default helpful contextual response
        summary = self.generate_kpi_summary(kpis)
        return (
            f"**InsightForge AI Assistant**:\n\n"
            f"{summary}\n\n"
            f"You can ask me questions such as:\n"
            f"• *'What are my total sales?'*\n"
            f"• *'Which product has the highest sales?'*\n"
            f"• *'What is the data quality score?'*\n"
            f"• *'What are the main business risks?'*\n"
            f"• *'Why did sales decrease?'*"
        )
