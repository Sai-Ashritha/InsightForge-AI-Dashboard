import json
import os
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.services.insight_generator import InsightGenerator


class LocalLLM:
    def __init__(self):
        self.url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2")

    def generate(self, prompt: str, fallback: str) -> tuple[str, str]:
        payload = json.dumps({"model": self.model, "prompt": prompt, "stream": False}).encode()
        request = Request(self.url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=5) as response:
                body = json.loads(response.read().decode("utf-8"))
            output = body.get("response", "").strip()
            if output:
                return output, "ollama"
        except (OSError, URLError, TimeoutError, ValueError, json.JSONDecodeError):
            pass
        return fallback, "deterministic_fallback"


def build_executive_prompt(
    question: str,
    kpis: dict,
    anomalies: list = None,
    recommendations: list = None,
    sales_declines: list = None,
    forecast_data: dict = None,
    inventory_data: list = None,
) -> str:
    return (
        "You are an expert AI Manufacturing Operations Advisor for InsightForge.\n"
        "Provide a structured, actionable response containing:\n"
        "1. Analysis (current data state, forecast, and KPIs)\n"
        "2. Probable Cause (why issues occurred or why demand changed)\n"
        "3. Recommendation (what to manufacture or adjust)\n"
        "4. Suggested Action (concrete next steps)\n\n"
        f"User Question: {question}\n"
        f"Live KPIs: {json.dumps(kpis or {}, default=str)}\n"
        f"Sales Declines: {json.dumps((sales_declines or [])[:3], default=str)}\n"
        f"Forecast Models: {json.dumps(forecast_data or {}, default=str)}\n"
        f"Inventory Telemetry: {json.dumps((inventory_data or [])[:5], default=str)}\n"
        f"Detected Anomalies: {json.dumps((anomalies or [])[:5], default=str)}\n"
        f"System Recommendations: {json.dumps((recommendations or [])[:3], default=str)}\n"
    )


def deterministic_answer(
    question: str,
    kpis: dict,
    anomalies: list = None,
    recommendations: list = None,
    sales_declines: list = None,
    forecast_data: dict = None,
    inventory_data: list = None,
) -> str:
    return InsightGenerator().answer_question(
        question=question,
        kpis=kpis,
        anomalies=anomalies or [],
        recommendations=recommendations or [],
        sales_declines=sales_declines or [],
        forecast_data=forecast_data or {},
        inventory_data=inventory_data or [],
    )

