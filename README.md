# Glue AI Utility

I built this to solve a real problem I kept running into at work — Glue jobs that quietly rack up costs because nobody's watching them closely enough. This tool points an AI at a job's run history and tells you exactly what's wrong and what to fix.

## The problem it solves

AWS Glue jobs are easy to overprovision and hard to debug after the fact. You set 10 workers, the job runs, costs money, fails occasionally — and unless you're digging through CloudWatch manually, you don't know why. This tool automates that investigation.

## How it works

You POST a job name and a question. The Lambda function assumes a read-only IAM role to pull the job config and last 20 run histories, then sends all of that to Claude AI with your question. You get back a structured analysis with specific issues and dollar estimates for each fix.

## Try it yourself

```bash
aws lambda invoke \
  --function-name glue-job-optimizer \
  --payload '{"httpMethod":"POST","body":"{\"job_name\":\"your-job-name\",\"query\":\"Why is this job costing more than expected?\"}"}' \
  --cli-binary-format raw-in-base64-out \
  --cli-read-timeout 60 \
  response.json && python3 -m json.tool response.json
```

## What the output looks like

```json
{
  "job_name": "etl-raw-to-processed",
  "job_summary": {
    "total_runs": 10,
    "failed_runs": 3,
    "total_cost_usd": 3.85,
    "avg_duration_min": 10.5
  },
  "ai_analysis": {
    "analysis": "30% failure rate with failures happening in under 3 minutes — classic sign of a permissions or schema issue at job init, not a processing problem. Successful runs are also showing 40% duration variance which points to data skew.",
    "issues_found": [
      "30% failure rate from missing table metadata and S3 permission errors",
      "High duration variance (11-17 min) suggests uneven data partitioning",
      "10 workers configured but workload likely only needs 6"
    ],
    "recommendations": [
      {
        "action": "Add pre-flight checks for table existence and S3 access before job execution",
        "expected_saving": "$0.78/month",
        "priority": "HIGH"
      },
      {
        "action": "Reduce worker count from 10 to 6 G.1X",
        "expected_saving": "$1.20/month",
        "priority": "MEDIUM"
      }
    ],
    "estimated_monthly_cost": "$11.55",
    "optimized_monthly_cost": "$9.20"
  }
}
```

## Stack

- **Lambda** (Python 3.11) — orchestrates everything
- **API Gateway** — HTTPS endpoint with API key auth
- **IAM** — three roles, two STS assume-role calls per request
- **AWS Glue** — source of truth for job config and run history
- **CloudWatch** — performance metrics
- **Claude AI** — analysis and recommendations

