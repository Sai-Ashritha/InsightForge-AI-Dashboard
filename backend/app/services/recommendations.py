import numpy as np
import pandas as pd


def generate_recommendations(
    data: dict,
    anomalies: list = None,
    sales_declines: list = None,
    forecast_data: dict = None,
    inventory_data: list = None,
) -> list:
    """
    Generate dynamic, actionable business recommendations based on data patterns,
    anomalies, inventory levels, sales decline, and forecasted demand.
    """
    recommendations = []
    anomalies = anomalies or []
    sales_declines = sales_declines or []
    inventory_data = inventory_data or []

    # 1. Product-specific Production & Demand Recommendations
    if forecast_data and forecast_data.get("product_forecasts"):
        top_prod_forecast = forecast_data["product_forecasts"][0]
        prod_name = top_prod_forecast.get("product", "Top Product")
        pred_demand = top_prod_forecast.get("predicted_demand", 12500)
        recommendations.append({
            "id": "rec_prod_001",
            "priority": "critical" if top_prod_forecast.get("share_percentage", 0) > 30 else "high",
            "category": "Production Scheduling",
            "title": f"Increase Production of {prod_name}",
            "description": f"Increase production of {prod_name} to meet forecasted demand of {pred_demand:,} units next month, capturing expected revenue growth.",
            "impact": "revenue",
            "potential_gain": "15-25%",
            "suggested_action": f"Schedule additional assembly shifts for {prod_name} and secure component supply.",
        })

    # 2. Sales Decline Recommendations
    for decline in sales_declines[:2]:
        p_name = decline.get("product", "Affected Product")
        dec_pct = decline.get("decline_percentage", 15)
        recommendations.append({
            "id": f"rec_decline_{p_name.replace(' ', '_')}",
            "priority": "critical" if dec_pct >= 25 else "high",
            "category": "Sales & Demand",
            "title": f"Investigate Sales Decline in {p_name}",
            "description": f"{p_name} experienced a {dec_pct}% decline compared to the previous period. Evaluate pricing, stock availability, and distributor channels.",
            "impact": "revenue",
            "potential_gain": "10-20%",
            "suggested_action": f"Run regional promotional campaigns and audit channel inventory for {p_name}.",
        })

    # 3. Inventory Reorder & Low Stock Recommendations
    low_stock_items = [item for item in inventory_data if item.get("low_stock") or (item.get("stock_available", 1000) <= item.get("reorder_level", 500))]
    if low_stock_items:
        for item in low_stock_items[:2]:
            p_name = item.get("product", "Critical Item")
            curr_stock = item.get("stock_available", 0)
            reorder_lvl = item.get("reorder_level", 0)
            recommendations.append({
                "id": f"rec_inv_{p_name.replace(' ', '_')}",
                "priority": "critical",
                "category": "Inventory Management",
                "title": f"Reorder Stock for {p_name}",
                "description": f"{p_name} is below the reorder threshold (Current Stock: {curr_stock:,}, Reorder Level: {reorder_lvl:,}). Urgent replenishment is required.",
                "impact": "inventory",
                "potential_gain": "Zero Stockouts",
                "suggested_action": f"Issue purchase orders immediately to avoid production bottlenecks for {p_name}.",
            })
    elif data and data.get("inventory", 0) > 0 and data["inventory"] < 5000:
        recommendations.append({
            "id": "rec_inv_general",
            "priority": "high",
            "category": "Inventory Management",
            "title": "Replenish Factory Floor Inventory",
            "description": f"Total factory inventory stands at {data['inventory']:,} units, which is below safety stock minimums.",
            "impact": "inventory",
            "potential_gain": "15-20%",
            "suggested_action": "Audit warehouse buffers and increase weekly replenishment batches.",
        })

    # 4. Production Efficiency Recommendations
    if data and "efficiency" in data and isinstance(data.get("efficiency"), (int, float)):
        if data["efficiency"] < 85:
            recommendations.append({
                "id": "rec_eff_001",
                "priority": "high",
                "category": "Operational Efficiency",
                "title": "Optimize Machine Uptime & Reduce Downtime",
                "description": f"Current line efficiency is {data['efficiency']}%, below the 90% benchmark. Analyze unplanned machine stoppages.",
                "impact": "efficiency",
                "potential_gain": "8-12%",
                "suggested_action": "Implement preventative maintenance schedules during off-peak hours.",
            })

    # 5. Quality & Defect Rate Recommendations
    if data and "defect_rate" in data and isinstance(data.get("defect_rate"), (int, float)):
        if data["defect_rate"] > 2.5:
            recommendations.append({
                "id": "rec_qual_001",
                "priority": "critical",
                "category": "Quality Assurance",
                "title": "Implement Quality Control Inspection Gates",
                "description": f"Defect rate is at {data['defect_rate']}%, exceeding the 2.0% tolerance limit. Scrap costs are accumulating.",
                "impact": "quality",
                "potential_gain": "25-35%",
                "suggested_action": "Add automated optical inspection (AOI) on the primary fabrication line.",
            })
        else:
            recommendations.append({
                "id": "rec_qual_002",
                "priority": "low",
                "category": "Quality Assurance",
                "title": "Maintain Six Sigma Quality Standards",
                "description": f"Defect rate is maintained at an optimal {data['defect_rate']}%. Standard operating procedures are effective.",
                "impact": "quality",
                "potential_gain": "Stable Quality",
                "suggested_action": "Conduct monthly calibration audits on measuring instrumentation.",
            })

    # 6. Anomalies Resolution
    if anomalies:
        anomaly_count = len(anomalies)
        top_anomaly = anomalies[0]
        anom_title = top_anomaly.get("title", f"{anomaly_count} Anomalies Detected")
        recommendations.append({
            "id": "rec_anom_001",
            "priority": "medium",
            "category": "Anomaly Resolution",
            "title": f"Review {anom_title}",
            "description": f"Found {anomaly_count} anomalous deviations in process metrics. Top issue: {top_anomaly.get('description', '')}",
            "impact": "data_quality",
            "potential_gain": "5-10%",
            "suggested_action": "Inspect sensor logs and verify operator data inputs around deviation timestamps.",
        })

    # Priority sorting
    priority_weights = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    recommendations_sorted = sorted(
        recommendations,
        key=lambda x: priority_weights.get(x.get("priority", "medium"), 4)
    )

    return recommendations_sorted


def prioritize_recommendations(recommendations: list) -> dict:
    """Group and prioritize recommendations by category and impact."""
    prioritized = {
        "critical": [],
        "high": [],
        "medium": [],
        "low": []
    }

    for rec in recommendations:
        priority = rec.get("priority", "low")
        if priority in prioritized:
            prioritized[priority].append(rec)

    return prioritized


def estimate_impact(recommendations: list) -> dict:
    """Estimate combined impact of implementing recommendations."""
    impact_map = {
        "revenue": 0.12,
        "efficiency": 0.08,
        "quality": 0.15,
        "inventory": 0.10,
        "production": 0.10,
        "data_quality": 0.05,
    }

    total_impact = 0.0
    impacts_by_category = {}

    for rec in recommendations:
        category = rec.get("impact")
        if category in impact_map:
            impact_value = impact_map[category]
            total_impact += impact_value
            if category not in impacts_by_category:
                impacts_by_category[category] = 0.0
            impacts_by_category[category] += impact_value

    return {
        "total_potential_improvement": min(85.0, round(total_impact * 100, 1)),
        "improvements_by_category": impacts_by_category,
        "top_priority_count": sum(1 for r in recommendations if r.get("priority") == "critical"),
    }

