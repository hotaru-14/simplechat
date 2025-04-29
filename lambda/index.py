import json
import os
import re
import urllib.request
import urllib.error

# Lambda コンテキストからリージョンを抽出する関数（未使用可）
def extract_region_from_arn(arn):
    match = re.search(r'arn:aws:lambda:([^:]+):', arn)
    return match.group(1) if match else "us-east-1"

# FastAPI サーバー URL を環境変数から取得
FASTAPI_URL = os.environ.get("FASTAPI_URL")

def lambda_handler(event, context):
    try:
        # リクエストボディの解析
        body = json.loads(event.get('body', '{}'))
        message = body.get('message', '')
        conversation_history = body.get('conversationHistory', [])

        # FastAPI サーバーへのペイロード構築
        payload = {
            "message": message,
            "conversationHistory": conversation_history
        }
        data = json.dumps(payload).encode('utf-8')

        # FastAPI の /generate エンドポイントに POST
        url = FASTAPI_URL.rstrip('/') + "/gererate"
        req = urllib.request.Request(
            url=url,
            data=data,
            headers={
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read().decode('utf-8')
            result = json.loads(resp_body)

        # エラーハンドリング
        if not result.get('success'):
            raise Exception(result.get('error', 'Inference failed'))

        # レスポンスからデータ取得
        assistant_response = result['response']
        updated_history = result.get('conversationHistory', [])

        # 成功レスポンスの返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": updated_history
            })
        }
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode() if hasattr(e, 'read') else str(e)
        print("HTTPError:", error_msg)
        return {
            "statusCode": e.code,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"success": False, "error": error_msg})
        }
    except Exception as error:
        print("Error:", str(error))
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"success": False, "error": str(error)})
        }
