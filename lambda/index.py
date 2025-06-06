import json
import os
import re
import urllib.request
import urllib.error

# FastAPI サーバーの公開 URL を環境変数から取得
FASTAPI_URL = "https://67c5-34-169-222-242.ngrok-free.app/generate"

def lambda_handler(event, context):
    try:
        # Lambda イベントから body を取得
        body = json.loads(event.get('body', '{}'))
        # ユーザー入力（message フィールド）
        message = body.get('message', '')
        # 会話履歴
        conversation_history = body.get('conversationHistory', [])

        print("body message:", body.get("message"))
        print("conversation history:", conversation_history)

        # FastAPI /generate エンドポイント向けペイロード
        payload = {
            "prompt": message,
            "history": conversation_history,
            "max_new_tokens": 256,
            "do_sample": True,
            "temperature": 0.7,
            "top_p": 0.9
        }
        data = json.dumps(payload).encode('utf-8')

        # エンドポイント URL
        url = FASTAPI_URL
        req = urllib.request.Request(
            url=url,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        # FastAPI サーバーへリクエスト送信
        with urllib.request.urlopen(req) as resp:
            resp_text = resp.read().decode('utf-8')
            result = json.loads(resp_text)

        # レスポンスから generated_text を取り出す
        if 'generated_text' not in result:
            raise Exception('FastAPI response missing "generated_text"')
        generated = result['generated_text']
        # レスポンスタイムを必要に応じて取得
        response_time = result.get('response_time')

        # 会話履歴にアシスタントの応答を追加
        updated_history = conversation_history + [{
            "role": "assistant",
            "content": generated.strip()
        }]

        # Lambda レスポンスを構築
        response_payload = {
            "success": True,
            "response": generated,
            "response_time": response_time
        }

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

    except urllib.error.HTTPError as e:
        # FastAPI からの HTTP エラー
        error_msg = e.read().decode('utf-8') if hasattr(e, 'read') else str(e)
        print("HTTPError:", error_msg)
        return {
            "statusCode": e.code,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"success": False, "error": error_msg})
        }

    except Exception as error:
        # その他の例外
        print("Error:", str(error))
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"success": False, "error": str(error)})
        }
