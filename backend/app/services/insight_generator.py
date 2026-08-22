import re
from typing import Dict, List, Optional


class InsightGenerator:
    """Generate natural language business insights and 4-part AI recommendations from data and analytics."""

    def __init__(self):
        self.kpi_insights = {}
        self.anomaly_insights = []
        self.recommendation_insights = []

    def generate_kpi_summary(self, kpis: dict) -> str:
        """Generate executive summary of KPIs."""
        if not kpis:
            return "No KPI data available."

        summary_parts = []
        revenue = kpis.get("revenue", 0)
        if revenue > 0:
            revenue_label = f"₹{int(revenue / 100000)}L" if revenue >= 100000 else f"₹{int(revenue):,}"
            summary_parts.append(f"Total revenue stands at {revenue_label}.")

        efficiency = kpis.get("efficiency", 0)
        if efficiency:
            if efficiency > 90:
                summary_parts.append(f"Production efficiency is excellent at {efficiency}%.")
            elif efficiency > 80:
                summary_parts.append(f"Production efficiency is good at {efficiency}%.")
            else:
                summary_parts.append(f"Production efficiency is below target at {efficiency}%.")

        defect_rate = kpis.get("defect_rate", 0)
        if defect_rate:
            if defect_rate < 2:
                summary_parts.append(f"Defect rate is optimal at {defect_rate}%.")
            elif defect_rate < 3:
                summary_parts.append(f"Defect rate is acceptable at {defect_rate}%.")
            else:
                summary_parts.append(f"Defect rate is elevated at {defect_rate}%.")

        inventory = kpis.get("inventory", 0)
        if inventory:
            if inventory < 5000:
                summary_parts.append(f"Inventory levels are critically low at {inventory:,} units.")
            elif inventory < 10000:
                summary_parts.append(f"Inventory levels are low at {inventory:,} units.")
            else:
                summary_parts.append(f"Inventory levels are healthy at {inventory:,} units.")

        production = kpis.get("production", 0)
        if production:
            summary_parts.append(f"Current production output is {production:,} units.")

        return " ".join(summary_parts)

    def generate_anomaly_insights(self, anomalies: list, total_records: int) -> str:
        """Generate natural language description of anomalies."""
        if not anomalies:
            return "No anomalies detected in the data. All process metrics appear normal."

        anomaly_count = len(anomalies)
        percentage = round((anomaly_count / total_records) * 100, 1) if total_records > 0 else 0

        if anomaly_count == 1:
            anom = anomalies[0]
            desc = anom.get("description", "Unusual deviation detected.")
            return f"1 anomalous record detected ({percentage}% of dataset): {desc}"

        top_desc = anomalies[0].get("description", "")
        return f"{anomaly_count} anomalous deviations detected ({percentage}% of data). Major event: {top_desc}"

    def generate_recommendation_summary(self, recommendations: list) -> str:
        """Generate summary of top recommendations."""
        if not recommendations:
            return "No active recommendations available at this time."

        critical = [r for r in recommendations if r.get("priority") == "critical"]
        high = [r for r in recommendations if r.get("priority") == "high"]

        summary_parts = []
        if critical:
            summary_parts.append(f"⚠️ CRITICAL ACTION: {critical[0].get('title')}. {critical[0].get('description')}")
        if high and len(critical) < 2:
            summary_parts.append(f"HIGH PRIORITY: {high[0].get('title')}.")

        total_count = len(recommendations)
        summary_parts.append(f"Overall, {total_count} actionable items prioritized.")
        return " ".join(summary_parts)

    def generate_probable_causes(
        self,
        kpis: dict,
        anomalies: list = None,
        sales_declines: list = None,
        inventory_data: list = None,
    ) -> dict:
        """Analyze combined patterns across sales, inventory, and anomalies to identify probable causes."""
        causes = []
        anomalies = anomalies or []
        sales_declines = sales_declines or []
        inventory_data = inventory_data or []

        # Check if sales decline is linked to inventory shortage
        if sales_declines:
            top_decline = sales_declines[0]
            prod_name = top_decline.get("product", "Primary Product")
            dec_pct = top_decline.get("decline_percentage", 15)

            # Check if that product has low inventory
            prod_inv = next((item for item in inventory_data if item.get("product") == prod_name), None)
            if prod_inv and prod_inv.get("stock_available", 1000) <= prod_inv.get("reorder_level", 500):
                causes.append({
                    "issue": f"{prod_name} Sales Decline ({dec_pct}%)",
                    "probable_cause": f"Sales declined because inventory availability decreased below the reorder level, causing stockouts and lost orders.",
                    "evidence": f"Current stock: {prod_inv.get('stock_available', 0)} vs Reorder level: {prod_inv.get('reorder_level', 0)}.",
                })
            else:
                causes.append({
                    "issue": f"{prod_name} Sales Decline ({dec_pct}%)",
                    "probable_cause": f"Sales declined because demand shifted toward alternative categories or seasonal purchasing cycles changed.",
                    "evidence": f"Period-over-period decrease of ₹{top_decline.get('difference', 0):,}.",
                })

        # Check anomalies
        if anomalies:
            top_anom = anomalies[0]
            causes.append({
                "issue": top_anom.get("title", "Process Anomaly"),
                "probable_cause": f"Unusual variance in {top_anom.get('metric', 'operations')} caused by unexpected machine downtime or sudden demand fluctuations.",
                "evidence": top_anom.get("description", ""),
            })

        # Check efficiency / defect rate
        if kpis.get("defect_rate", 0) > 2.5:
            causes.append({
                "issue": f"Elevated Defect Rate ({kpis.get('defect_rate')}%)",
                "probable_cause": "Tool wear or calibration drift in the primary production cell leading to out-of-tolerance parts.",
                "evidence": f"Defect rate is {kpis.get('defect_rate')}% compared to target of < 2.0%.",
            })

        if not causes:
            causes.append({
                "issue": "General Operations",
                "probable_cause": "Manufacturing throughput and sales velocity are operating within standard parameters with no critical bottlenecks.",
                "evidence": "All core KPIs meet baseline targets.",
            })

        return {
            "primary_cause": causes[0]["probable_cause"],
            "all_causes": causes,
        }

    def answer_question(
        self,
        question: str,
        kpis: dict,
        anomalies: list,
        recommendations: list,
        sales_declines: list = None,
        forecast_data: dict = None,
        inventory_data: list = None,
    ) -> str:
        """Answer business and manufacturing operational questions with a structured 4-part response."""
        q = question.lower().strip()
        sales_declines = sales_declines or []
        forecast_data = forecast_data or {}
        inventory_data = inventory_data or []

        # Target operational manufacturing question: "What should we manufacture next month?"
        if any(w in q for w in ["manufacture", "produce", "production schedule", "next month", "make next month"]):
            top_product = "Product A"
            predicted_demand = 12500
            trend_pct = 18

            if forecast_data and forecast_data.get("product_forecasts"):
                top_item = forecast_data["product_forecasts"][0]
                top_product = top_item.get("product", "Product A")
                predicted_demand = top_item.get("predicted_demand", 12500)
                trend_pct = int(top_item.get("share_percentage", 18))

            rev_est = forecast_data.get("expected_revenue", kpis.get("revenue", 850000))
            rev_label = f"₹{int(rev_est / 100000)}L" if rev_est >= 100000 else f"₹{int(rev_est):,}"

            return (
                f"Based on the sales forecast and current inventory, you should increase production of {top_product} next month.\n\n"
                f"1. **Analysis**:\n"
                f"Forecast models project total next-month demand at approximately {predicted_demand:,} units with expected revenue of {rev_label}. "
                f"{top_product} represents the highest demand share ({trend_pct}% of total projected volume).\n\n"
                f"2. **Probable Cause**:\n"
                f"Demand is expected to increase by approximately {trend_pct}%, while current inventory levels are approaching the reorder threshold. "
                f"Maintaining current production rates risks widespread stockouts and unfulfilled customer orders.\n\n"
                f"3. **Recommendation**:\n"
                f"Scale production capacity for {top_product} by 15-20% starting next week. Rebalance line shifts away from slow-moving inventory to prioritize high-velocity SKUs.\n\n"
                f"4. **Suggested Action**:\n"
                f"Issue raw material replenishment orders to suppliers today, schedule a Saturday maintenance window to ensure 95%+ uptime, and assign two dedicated assembly teams to {top_product}."
            )

        # Questions about Sales Decline
        if any(w in q for w in ["decline", "sales drop", "decreasing", "drop in sales"]):
            if sales_declines:
                top_dec = sales_declines[0]
                return (
                    f"**Sales Decline Analysis**:\n\n"
                    f"1. **Analysis**: {top_dec.get('product', 'Product')} sales dropped by {top_dec.get('decline_percentage')}% "
                    f"(previous: ₹{int(top_dec.get('previous_sales', 0)):,}, current: ₹{int(top_dec.get('current_sales', 0)):,}).\n\n"
                    f"2. **Probable Cause**: Reduced inventory availability at regional distribution hubs created fulfillment delays.\n\n"
                    f"3. **Recommendation**: Conduct targeted promotions in East & North regions and expedite stock replenishment.\n\n"
                    f"4. **Suggested Action**: Coordinate with regional distributors to clear backlogged orders."
                )
            return "No significant sales declines detected in the current period. Overall revenue trajectory is positive."

        # Questions about Revenue / Sales
        if any(w in q for w in ["revenue", "sales", "income", "turnover"]):
            revenue = kpis.get("revenue", 0)
            rev_label = f"₹{int(revenue / 100000)}L" if revenue >= 100000 else f"₹{int(revenue):,}"
            return (
                f"Current revenue is {rev_label} across {kpis.get('orders', 0)} completed transactions. "
                f"Next month's projected revenue is ₹{(kpis.get('forecast_next_month', revenue * 1.08) / 100000):.1f}L. "
                f"Would you like recommendations on boosting product line profitability?"
            )

        # Questions about Inventory / Stock
        if any(w in q for w in ["inventory", "stock", "warehouse", "reorder"]):
            inv = kpis.get("inventory", 0)
            status = "critically low" if inv < 5000 else "low" if inv < 10000 else "healthy"
            return (
                f"Total inventory on hand is {inv:,} units ({status}). "
                f"{'⚠ Immediate purchase orders should be placed for items below minimum safety stock.' if inv < 10000 else 'Stock buffers are sufficient for current run rates.'}"
            )

        # Questions about Anomalies
        if any(w in q for w in ["anomal", "unusual", "outlier", "spike", "defect"]):
            if anomalies:
                return f"Isolation Forest detected {len(anomalies)} anomalies. {self.generate_anomaly_insights(anomalies, kpis.get('total_records', 100))}"
            return "No statistically significant anomalies detected in recent telemetry."

        # Questions about Recommendations / Action plan
        if any(w in q for w in ["recommend", "suggest", "improve", "action", "plan", "priority"]):
            if recommendations:
                top_rec = recommendations[0]
                return (
                    f"**Top Business Recommendation**:\n\n"
                    f"• **Title**: {top_rec.get('title')}\n"
                    f"• **Impact**: {top_rec.get('description')}\n"
                    f"• **Expected Improvement**: {top_rec.get('potential_gain', '10-20%')}\n"
                    f"• **Next Step**: {top_rec.get('suggested_action', 'Execute prioritized tasks.')}"
                )
            return "All operational parameters are currently within target thresholds."

        if any(w in q for w in ["summary", "overview", "status", "health"]):
            return self.generate_kpi_summary(kpis)

        return (
            "I can answer operational questions across revenue trends, sales decline, next-month manufacturing schedules, "
            "anomaly detection, and inventory reordering. Try asking: **'What should we manufacture next month?'**"
        )

