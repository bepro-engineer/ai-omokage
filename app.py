# 必要なライブラリのインポート
from flask import Flask, request, abort
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging.models import ReplyMessageRequest, PushMessageRequest, TextMessage
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
# memory_target_user_id = os.getenv("MEMORY_TARGET_USER_ID")
phase_mode = os.getenv("PHASE_MODE")  # "learn" または "reply" を指定
self_user_id    = os.getenv("LINE_USER_ID_SELF") 
target_user_id = os.getenv("LINE_USER_ID_TARGET") 

# 設定ミスがある場合は即時停止
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
        user_id  = event.source.user_id          # 発言者の LINE userId
        message  = event.message.text            # 発言テキスト

        # ─────────────────────────────
        # 0. 禁止ワードチェック（NGワードが含まれていたら即遮断）
        # ─────────────────────────────
        NG_WORDS = ["セフレ", "エロ", "性欲", "キスして", "付き合って", "いやらしい"]
        if any(ng in message.lower() for ng in NG_WORDS):
            ban_reply = "この話題には応答できません。"
            messaging_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=ban_reply)]
                )
            )
            return

        print(f"🌐 DEBUG: phase_mode is {phase_mode}")
        # =====================================================
        # Phase-1 : 学習モード（Bepro ↔ Geeksのやりとりを記録）
        # =====================================================
        if phase_mode.strip() == "learn":
            print("🔁 Phase1 入った")
            # カテゴリ分類のみ（AIはここでのみ使う）
            category = getCategoryByGpt(message)

            # ① input（親）を保存：発言者＝記憶対象
            parent_id = registerMemoryAndDialogue(
                user_id         = user_id,
                message         = message,
                content         = message,              # 応答ではなく、発言内容そのまま
                category        = category,
                sender_user_id  = user_id,
                message_type    = "input"
            )

            # ② 表示処理（Phase1：AIは一切返答せず、人間の発言のみ転送）
            if user_id == self_user_id:
                # Beproの発話をGeeksへ転送（自分にもecho）
                messaging_api.push_message(
                    PushMessageRequest(
                        to=target_user_id,
                        messages=[TextMessage(text=message)]
                    )
                )

            elif user_id == target_user_id:
                # Geeksの発話をBeproへ転送
                messaging_api.push_message(
                    PushMessageRequest(
                        to=self_user_id,
                        messages=[TextMessage(text=message)]
                    )
                )

            else:
                # 想定外ユーザーは無視
                print("Ignored: unknown user in Phase1.")
                return
            print("✅ Phase1 完了：return直前")
            return  # Phase1終了

        # =====================================================
        # Phase-2 : 過去母発言を模倣した応答（未使用）
        # =====================================================
        elif phase_mode.strip() == "reply":
            print("🔁 Phase2 入った")
            category = getCategoryByGpt(message)

            # ① input（親）を保存
            parent_id = registerMemoryAndDialogue(
                user_id         = user_id,
                message         = message,
                content         = message,
                category        = category,
                sender_user_id  = user_id,
                message_type    = "input"
            )

            # ② ChatGPT による応答生成（過去の記憶から返答）
            gpt_result   = getChatGptReply(message, target_user_id, category)
            reply_text   = gpt_result["reply_text"]
            memory_refs  = json.dumps(gpt_result["used_memory_ids"])

            # ③ reply（子）を保存
            reply_sender_id = target_user_id if user_id == self_user_id else self_user_id
            registerMemoryAndDialogue(
                user_id             = target_user_id,
                message             = message,
                content             = reply_text,
                category            = category,
                memory_refs         = memory_refs,
                is_ai_generated     = True,
                sender_user_id      = reply_sender_id,
                message_type        = "reply",
                parent_dialogue_id  = parent_id
            )

            # ④ 相手へPush送信
            to_user_id = reply_sender_id
            messaging_api.push_message(
                PushMessageRequest(
                    to=to_user_id,
                    messages=[TextMessage(text=reply_text)]
                )
            )
            print("💥 getChatGptReply が呼び出された")
            return  # Phase2終了

        # =====================================================
        # モード不一致または対象外ユーザーなど
        # =====================================================
        print("Ignored : not target or phase mismatch.")

    except Exception as e:
        # 例外発生時はログに出力（応答は返さない）
        print(f"[{phase_mode.upper()}] Handler Error: {e}")

# ローカル実行用のエントリーポイント
if __name__ == '__main__':
    print("✅ initDatabase() を実行開始")
    initDatabase()
    print("✅ initDatabase() を完了")
    app.run(debug=False, host='0.0.0.0', port=5001)
