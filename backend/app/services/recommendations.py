def generate_recommendations(
    data: dict,
    anomalies: list = None,
    sales_declines: list = None,
    forecast_data: dict = None,
    inventory_data: list = None,
) -> list:
    """Generate evidence-linked follow-up actions without assuming an industry or target gains."""
    recommendations = []
    anomalies = anomalies or []
    sales_declines = sales_declines or []
    inventory_data = inventory_data or []

    if forecast_data and forecast_data.get("has_forecast"):
        target = forecast_data.get("target_metric", "the forecasted measure")
        recommendations.append({
            "id": "rec_forecast_review",
            "priority": "medium",
            "category": "Forecast Review",
            "title": f"Review the {target} forecast",
            "description": f"A forecast is available for {target}. Compare the projected values with current plans before making changes.",
            "impact": "planning",
            "suggested_action": "Validate the source data and consider relevant context not represented in the dataset.",
        })

    for decline in sales_declines[:3]:
        segment = decline.get("product", "segment")
        metric = decline.get("metric", "measured value")
        change = decline.get("decline_percentage", 0)
        recommendations.append({
            "id": f"rec_decline_{str(segment).replace(' ', '_')}",
            "priority": "high" if change >= 25 else "medium",
            "category": "Metric Change",
            "title": f"Review {metric} for {segment}",
            "description": f"The measured value for {segment} decreased by {change}% between the compared periods.",
            "impact": "analysis",
            "suggested_action": "Check the underlying records and compare relevant segments or time periods to identify context.",
        })

    for item in inventory_data:
        if not item.get("low_stock"):
            continue
        label = item.get("product", "Record")
        recommendations.append({
            "id": f"rec_threshold_{str(label).replace(' ', '_')}",
            "priority": "high",
            "category": "Threshold Review",
            "title": f"Review {label} against its supplied threshold",
            "description": f"The observed value ({item.get('stock_available')}) is at or below the supplied threshold ({item.get('reorder_level')}).",
            "impact": "threshold",
            "suggested_action": "Verify the threshold and check the source records before taking operational action.",
        })

    if anomalies:
        anomaly_count = len(anomalies)
        top_anomaly = anomalies[0]
        anom_title = top_anomaly.get("title", f"{anomaly_count} Anomalies Detected")
        recommendations.append({
            "id": "rec_anom_001",
            "priority": "medium",
            "category": "Anomaly Review",
            "title": f"Review {anom_title}",
            "description": f"Detected {anomaly_count} anomalous record(s). {top_anomaly.get('description', '')}",
            "impact": "analysis",
            "suggested_action": "Inspect the flagged records and verify whether the values reflect valid events or data issues.",
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
    impacts_by_category = {}
    for rec in recommendations:
        category = rec.get("impact")
        if category:
            impacts_by_category[category] = impacts_by_category.get(category, 0) + 1

    return {
        "total_potential_improvement": None,
        "improvements_by_category": impacts_by_category,
        "top_priority_count": sum(1 for r in recommendations if r.get("priority") == "critical"),
    }

