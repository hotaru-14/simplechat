import os
import json
import time
import requests

# FastAPI サーバーの公開 URL を環境変数から取得
FASTAPI_URL = os.environ.get("FASTAPI_URL")  # 例: "https://abcd1234.ngrok.io"

# グローバルにセッションを張っておくとコネクション再利用されて高速化
session = requests.Session()

def lambda_handler(event, context):
    try:
        # Cognito で認証されたユーザー情報（任意でログに出す）
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            claims = event['requestContext']['authorizer']['claims']
            user = claims.get('email') or claims.get('cognito:username')
            print(f"Authenticated user: {user}")

        # リクエストボディ解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])

        print("Received message:", message)

        # FastAPI generate エンドポイント用ペイロード
        payload = {
            "prompt": message,
            "conversationHistory": conversation_history,
            # 必要に応じてチューニングパラメータを追加できます
            "max_new_tokens": body.get("max_new_tokens", 512),
            "temperature":      body.get("temperature", 0.7),
            "top_p":            body.get("top_p", 0.9),
            "do_sample":        body.get("do_sample", True)
        }

        # エンドポイント URL を組み立て
        url = FASTAPI_URL.rstrip('/') + "/generate"
        print(f"Calling FastAPI at {url} with payload: {payload}")

        # 呼び出し前にタイムスタンプ
        start_time = time.time()

        resp = session.post(
            url,
            json=payload,
            timeout=10  # 必要に応じてタイムアウトを設定
        )
        resp.raise_for_status()

        # 呼び出し後の経過時間
        total_request_time = time.time() - start_time
        result = resp.json()

        # 必須フィールドのチェック
        if "generated_text" not in result:
            raise ValueError('FastAPI response missing "generated_text"')

        generated = result["generated_text"]
        api_process_time = result.get("response_time")

        # 会話履歴に追加
        updated_history = conversation_history + [{
            "role": "assistant",
            "content": generated.strip()
        }]

        # Lambda 結果ペイロード
        response_payload = {
            "success": True,
            "response": generated,
            "conversationHistory": updated_history,
            "total_request_time": total_request_time
        }
        if api_process_time is not None:
            response_payload["response_time"] = api_process_time

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps(response_payload)
        }

    except requests.exceptions.HTTPError as e:
        # FastAPI からのエラー
        status = e.response.status_code
        text   = e.response.text
        print(f"FastAPI HTTPError {status}: {text}")
        return {
            "statusCode": status,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"success": False, "error": text})
        }

    except Exception as error:
        # その他の例外
        print("Error:", str(error))
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"success": False, "error": str(error)})
        }
