```python
# lambda/index.py
import json
import os
import urllib.request
import urllib.error

# Lambda ハンドラ
def lambda_handler(event, context):
    try:
        # ngrok 等で公開した FastAPI サーバーの URL を環境変数から取得
        fastapi_url = os.environ.get("FASTAPI_URL") or https://5a83-34-143-196-229.ngrok-free.app
        if not fastapi_url:
            raise Exception("Environment variable FASTAPI_URL is not set")

        # リクエストボディの解析
        body = json.loads(event.get('body', '{}'))
        message = body.get('message')
        conversation_history = body.get('conversationHistory', [])
        if message is None:
            raise Exception("Missing 'message' in request body")

        # FastAPI サーバー向けペイロード構築
        payload = {
            "message": message,
            "conversationHistory": conversation_history
        }
        data = json.dumps(payload).encode('utf-8')

        # HTTP リクエスト作成
        req = urllib.request.Request(
            url=f"{fastapi_url}/predict",
            data=data,
            headers={
                'Content-Type': 'application/json'
            },
            method='POST'
        )

        # FastAPI 呼び出し
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read().decode('utf-8')
            resp_json = json.loads(resp_body)

        # FastAPI 側のエラーハンドリング
        if not resp_json.get('success'):
            detail = resp_json.get('detail', resp_json)
            raise Exception(f"FastAPI error: {detail}")

        # レスポンスの取得
        assistant_response = resp_json['response']
        updated_history = resp_json.get('conversationHistory', [])

        # 成功レスポンスを返却
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({
                'success': True,
                'response': assistant_response,
                'conversationHistory': updated_history
            })
        }

    except Exception as error:
        # エラー発生時のレスポンス
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({
                'success': False,
                'error': str(error)
            })
        }

"""
**修正ポイント**:
1. **`FASTAPI_URL` 環境変数** に、ngrok などで取得した公開 URL を設定します。
2. **`urllib.request`** で `POST {FASTAPI_URL}/predict` を呼び出し、FastAPI の推論結果を受け取るように変更しました。
3. 元の AWS Bedrock 呼び出しロジックは削除し、外部 API 呼び出しに切り替えています。

このままデプロイして、環境変数 `FASTAPI_URL` を設定すれば、Lambda から ngrok 公開の FastAPI サーバーへ接続して推論が実行できます。
"""