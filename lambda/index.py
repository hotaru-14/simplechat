# lambda/index.py

import json
import os
import re
import urllib.request
import urllib.error

# FastAPI サーバーの公開 URL を環境変数から取得
FASTAPI_URL = os.environ.get("FASTAPI_URL")  # 例: "https://abcd1234.ngrok.io"


def lambda_handler(event, context):
    try:
        # リクエストボディ解析
        body = json.loads(event.get('body', '{}'))
        message = body.get('message', '')
        conversation_history = body.get('conversationHistory', [])

        # FastAPI サーバーへ渡すペイロードを作成
        payload = {
            "message": message,
            "conversationHistory": conversation_history
        }
        data = json.dumps(payload).encode('utf-8')

        # /generate エンドポイントへの完全な URL を組み立て
        url = FASTAPI_URL.rstrip('/') + "/generate"

        # HTTP リクエストを構築
        req = urllib.request.Request(
            url=url,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        # FastAPI サーバーにリクエスト送信＆レスポンス受信
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read().decode('utf-8')
            result = json.loads(resp_body)

        # サーバー側で success=False だった場合は例外に
        if not result.get('success'):
            raise Exception(result.get('error', 'Inference failed'))

        # 推論結果と更新後の会話履歴を取得
        assistant_response = result['response']
        updated_history = result.get('conversationHistory', [])

        # Lambda の成功レスポンス形式で返却
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
        # FastAPI からの HTTP エラーをキャッチ
        error_msg = e.read().decode() if hasattr(e, 'read') else str(e)
        print("HTTPError:", error_msg)
        return {
            "statusCode": e.code,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"success": False, "error": error_msg})
        }

    except Exception as error:
        # その他の例外をキャッチ
        print("Error:", str(error))
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"success": False, "error": str(error)})
        }
