import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# Optional: only used if OPENAI_API_KEY is set
def call_openai_prompt(prompt, max_tokens=250):
    if not OPENAI_API_KEY:
        return None
    try:
        import openai

        openai.api_key = OPENAI_API_KEY
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.6,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI call failed:", e)
        return None


def safe_float_or_pct(value, base):
    """
    Handles numbers or +10%/-5% changes relative to base
    """
    if value is None:
        return base
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if s.endswith("%"):
        try:
            pct = float(s.rstrip("%"))
            return base * (1 + pct / 100.0)
        except:
            return base
    try:
        return float(value)
    except:
        return base


def compute_metrics(item):
    rev, cost, growth = (
        item.get("revenue", 0),
        item.get("cost", 0),
        item.get("growth", 0),
    )
    profit = rev - cost
    margin = (profit / rev) if rev else 0
    next_rev = rev * (1 + growth / 100.0)
    return {**item, "profit": profit, "margin": margin, "revenue_next": next_rev}


def template_narrative(scenario, baseline):
    lines = []
    lines.append(
        f"{scenario['name']}: Revenue ${scenario['revenue']:,.0f}, cost ${scenario['cost']:,.0f}, margin {scenario['margin']*100:.1f}%."
    )
    if scenario["revenue"] > baseline["revenue"]:
        pct = (
            (scenario["revenue"] - baseline["revenue"]) / baseline["revenue"] * 100
            if baseline["revenue"]
            else 0
        )
        lines.append(f"Revenue is {pct:.1f}% higher than baseline.")
    elif scenario["revenue"] < baseline["revenue"]:
        pct = (
            (baseline["revenue"] - scenario["revenue"]) / baseline["revenue"] * 100
            if baseline["revenue"]
            else 0
        )
        lines.append(f"Revenue is {pct:.1f}% lower than baseline.")
    else:
        lines.append("Revenue matches baseline.")
    if scenario["margin"] < 0.05:
        lines.append("Margin is low — consider cost reductions.")
    elif scenario["margin"] > 0.20:
        lines.append("Strong margins — potential for reinvestment.")
    lines.append(f"Next year projected revenue: ${scenario['revenue_next']:,.0f}.")
    return " ".join(lines)


def generate_narrative(scenario_raw, baseline_raw):
    rev = safe_float_or_pct(scenario_raw.get("revenue"), baseline_raw["revenue"])
    cost = safe_float_or_pct(scenario_raw.get("cost"), baseline_raw["cost"])
    growth = safe_float_or_pct(scenario_raw.get("growth"), baseline_raw["growth"])
    scenario = {
        "name": scenario_raw.get("name", "Scenario"),
        "revenue": rev,
        "cost": cost,
        "growth": growth,
    }
    baseline = {
        "revenue": baseline_raw["revenue"],
        "cost": baseline_raw["cost"],
        "growth": baseline_raw["growth"],
    }

    s = compute_metrics(scenario)
    b = compute_metrics(baseline)

    prompt = f"""
You are a financial analyst. Compare the following scenario vs baseline:
Scenario: revenue={s['revenue']}, cost={s['cost']}, margin={s['margin']:.2f}, growth={s['growth']}
Baseline: revenue={b['revenue']}, cost={b['cost']}, margin={b['margin']:.2f}, growth={b['growth']}
Write a 4-6 sentence factual narrative summary with insight.
"""
    ai_text = call_openai_prompt(prompt)
    s["narrative"] = ai_text or template_narrative(s, b)
    return s


def run_scenarios(baseline, scenarios):
    base_metrics = compute_metrics(baseline)
    results = [dict(base_metrics, name="Baseline", narrative="Baseline scenario.")]
    for sc in scenarios:
        results.append(generate_narrative(sc, baseline))
    return results
