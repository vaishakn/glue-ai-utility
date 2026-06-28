import json
import traceback
from glue_fetcher import fetch_all_glue_data
from bedrock_caller import call_bedrock

HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
}


def lambda_handler(event, context):
    print("Event received")

    if event.get("httpMethod") == "OPTIONS":
        return {"statusCode": 200, "headers": HEADERS, "body": ""}

    try:
        body = json.loads(event.get("body") or "{}")
        job_name = body.get("job_name", "").strip()
        query = body.get("query", "Analyze this job for cost and performance issues.")

        if not job_name:
            return {
                "statusCode": 400,
                "headers": HEADERS,
                "body": json.dumps({"error": "job_name is required"}),
            }

        print("Processing: " + job_name)
        glue_data = fetch_all_glue_data(job_name)
        print("Glue data fetched")

        ai_response = call_bedrock(glue_data, query)
        print("AI done")

        return {
            "statusCode": 200,
            "headers": HEADERS,
            "body": json.dumps(
                {
                    "job_name": job_name,
                    "job_summary": glue_data["summary"],
                    "ai_analysis": ai_response,
                }
            ),
        }

    except Exception as e:
        print("ERROR: " + traceback.format_exc())
        return {
            "statusCode": 500,
            "headers": HEADERS,
            "body": json.dumps({"error": str(e)}),
        }
