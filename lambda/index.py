import json
import os
import urllib.request
import urllib.error

# 公開APIのエンドポイントを環境変数から取得（デフォルトは ngrok の公開 URL）
EXTERNAL_API_URL = os.environ.get(
    "EXTERNAL_API_URL",
    "https://****.ngrok-free.app"
)

def lambda_handler(event, context):
    """
    Lambda ハンドラ

    リクエストボディ例:
      {
        "prompt": "string",
        "max_new_tokens": 512,
        "do_sample": true,
        "temperature": 0.7,
        "top_p": 0.9
      }

    レスポンス例:
      {
        "generated_text": "string",
        "response_time": 0
      }
    """
    try:
        # リクエストボディのパース
        body = json.loads(event.get("body", "{}"))

        # 必須フィールドチェック
        required = [
            "prompt",
            "max_new_tokens",
            "do_sample",
            "temperature",
            "top_p",
        ]
        missing = [k for k in required if k not in body]
        if missing:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "success": False,
                    "error": f"Missing fields: {missing}"
                })
            }

        # JSON ボディをバイト列に変換
        try:
            payload = json.dumps(body).encode("utf-8")
        except (TypeError, ValueError) as e:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "success": False,
                    "error": f"Invalid JSON body: {e}"
                })
            }

        # urllib.request で外部 API 呼び出し
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        req = urllib.request.Request(
            EXTERNAL_API_URL,
            data=payload,
            headers=headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as res:
                raw = res.read().decode("utf-8")
                data = json.loads(raw)
        except urllib.error.HTTPError as e:
            detail = e.read().decode() if e.fp else e.reason
            return {
                "statusCode": e.code,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"success": False, "error": f"Upstream HTTPError: {detail}"})
            }
        except urllib.error.URLError as e:
            return {
                "statusCode": 502,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"success": False, "error": f"Upstream URLError: {e.reason}"})
            }
        except json.JSONDecodeError:
            return {
                "statusCode": 502,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"success": False, "error": "Upstream did not return valid JSON"})
            }

        # レスポンス検証
        if "generated_text" not in data or "response_time" not in data:
            return {
                "statusCode": 502,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "success": False,
                    "error": "Upstream response missing required fields"
                })
            }

        # 正常レスポンス
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST",
                "Access-Control-Allow-Headers": "Content-Type"
            },
            "body": json.dumps({
                "success": True,
                "generated_text": data["generated_text"],
                "response_time": data["response_time"]
            })
        }

    except Exception as e:
        # 予期しないエラー
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"success": False, "error": str(e)})
        }
