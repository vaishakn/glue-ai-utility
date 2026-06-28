import json
import urllib.request
import os

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
MODEL_ID = "claude-haiku-4-5-20251001"


def build_prompt(glue_data, user_query):
    config = glue_data["job_config"]
    summary = glue_data["summary"]
    runs = glue_data["run_history"][:5]

    return f"""You are an AWS Glue cost optimization expert.

JOB: {config.get("name")} | Workers: {config.get("num_workers")} x {config.get("worker_type")} | Glue {config.get("glue_version")}
RUNS: {summary.get("total_runs")} total, {summary.get("failed_runs")} failed | Cost: ${summary.get("total_cost_usd")} | Avg duration: {summary.get("avg_duration_min")} min
RECENT RUNS: {json.dumps(runs)}

Question: {user_query}

Respond ONLY with raw JSON. No markdown. No code fences. No backticks. Start your response with {{ and end with }}::
{{"analysis":"2-3 sentence summary","issues_found":["issue 1","issue 2"],"recommendations":[{{"action":"what to do","expected_saving":"$X or X%","priority":"HIGH/MEDIUM/LOW"}}],"estimated_monthly_cost":"$X","optimized_monthly_cost":"$X"}}"""


def call_bedrock(glue_data, user_query):
    print("Calling Anthropic API...")
    prompt = build_prompt(glue_data, user_query)
    payload = json.dumps(
        {
            "model": MODEL_ID,
            "max_tokens": 500,
            "temperature": 0,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read())

    result_text = result["content"][0]["text"]

    try:
        clean = result_text.strip()
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0]
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0]
        return json.loads(clean.strip())
    except json.JSONDecodeError:
        return {"analysis": result_text, "raw": True}
