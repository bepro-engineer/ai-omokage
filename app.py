# 必要なライブラリのインポート
from flask import Flask, request, abort
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage

from dotenv import load_dotenv
import os
import json

from logic.db_utils import initDatabase, registerMemoryAndDialogue
from logic.chatgpt_logic import getChatGptReply, getCategoryByGpt
import logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# .envファイルから環境変数を読み込み
load_dotenv()

# 各種設定値を取得（LINE連携やOpenAI、モードなど）
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
openai_api_key = os.getenv("OPENAI_API_KEY")
memory_target_user_id = os.getenv("MEMORY_TARGET_USER_ID")
phase_mode = os.getenv("PHASE_MODE")  # "learn" または "reply" を指定

# 設定ミスがある場合は即時停止
if not memory_target_user_id:
    raise ValueError("MEMORY_TARGET_USER_ID is not set. Startup aborted.")
if phase_mode not in ["learn", "reply"]:
    raise ValueError("PHASE_MODE must be 'learn' or 'reply'. Startup aborted.")

# FlaskアプリとLINE Botの初期化
app = Flask(__name__)
handler = WebhookHandler(channel_secret)
messaging_api = MessagingApi(ApiClient(Configuration(access_token=access_token)))

# SQLite データベースの初期化
initDatabase()

# Webhook エンドポイントの定義（LINEからのPOST受信用）
@app.route("/ai_omokage_webhook", methods=["POST"])
def ai_omokage_webhook():
    signature = request.headers["X-Line-Signature"]
    body_text = request.get_data(as_text=True)
    body_json = request.get_json(force=True)

    events = body_json.get("events", [])
    if not events:
        print("⚠️ Warning: No events in body.")
        return "NO EVENT", 200

    user_id = events[0]["source"]["userId"]
    print("user_id:", user_id)

    try:
        handler.handle(body_text, signature)
    except Exception as e:
        print(f"[{phase_mode.upper()}] Webhook Error: {e}")
        abort(400)

    return "OK"

# メッセージ受信イベントに応答
@handler.add(MessageEvent, message=TextMessageContent)
def handleMessage(event):
    try:
        user_id = event.source.user_id
        message = event.message.text

        # 禁止ワードにヒットした場合は即応答
        NG_WORDS = ["セフレ", "エロ", "性欲", "キスして", "付き合って", "いやらしい"]
        if any(ng in message.lower() for ng in NG_WORDS):
            reply_text = "この話題には応答できません。"
            reply = ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
            messaging_api.reply_message(reply)
            return

        print(f"[{phase_mode.upper()}] Received message from user_id: {user_id}")
        print(f"[{phase_mode.upper()}] MEMORY_TARGET_USER_ID: {memory_target_user_id}")

        # Phaseモードに応じて処理を分岐
        if phase_mode == "learn":
            # 対象ユーザーの発言のみを記録
            if user_id == memory_target_user_id:
                category = getCategoryByGpt(message)
                registerMemoryAndDialogue(
                    user_id=user_id,
                    message=message,
                    content=message,
                    category=category,
                    memory_refs=None,
                    is_ai_generated=False,
                    sender_user_id="self",
                    message_type="input"
                )
                print(f"Memory recorded with category: {category}")
            else:
                print("Ignored: Not memory target (LEARN mode)")

        elif phase_mode == "reply":
            # 対話応答を生成し、記録＋返答
            gpt_result = getChatGptReply(message, memory_target_user_id)
            reply_text = gpt_result["reply_text"]
            memory_refs = json.dumps(gpt_result["used_memory_ids"])
            used_category = gpt_result["used_category"]

            registerMemoryAndDialogue(
                user_id=memory_target_user_id,
                message=message,
                content=reply_text,
                category=used_category,
                memory_refs=memory_refs,
                is_ai_generated=True,
                sender_user_id=user_id,
                message_type="reply"
            )

            reply = ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
            messaging_api.reply_message(reply)
            print(f"Reply sent and recorded (REPLY mode) with category: {used_category}")

    except Exception as e:
        print(f"[{phase_mode.upper()}] Handler Error: {e}")

# ローカル実行用のエントリーポイント
if __name__ == '__main__':
    print("✅ initDatabase() を実行開始")
    initDatabase()
    print("✅ initDatabase() を完了")
    app.run(debug=False, host='0.0.0.0', port=5001)
