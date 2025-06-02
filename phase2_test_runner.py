# phase2_test_runner.py

from logic.chatgpt_logic import getChatGptReply
from logic.db_utils import registerMemoryAndDialogue
import json
import os

# Phase2テスト用：入力文
test_input = "少し遅れる"
# .envからユーザーIDを取得
memory_target_user_id = os.getenv("MEMORY_TARGET_USER_ID")

# ChatGPTに問い合わせ
result = getChatGptReply(test_input, memory_target_user_id)

# 応答と使用記憶IDを表示
print("=== ChatGPT応答 ===")
print(result["reply_text"])
print("\n=== 使用記憶ID ===")
print(result["used_memory_ids"])

# 対象ユーザー（母）への応答として記録（Phase2用）
registerMemoryAndDialogue(
    user_id=os.getenv("MEMORY_TARGET_USER_ID"),  # 応答対象
    message=test_input,                          # 受け取った発話
    content=result["reply_text"],                # 生成された応答
    category="応答",                             # 応答固定カテゴリ
    memory_refs=json.dumps(result["used_memory_ids"]),
    is_ai_generated=True,
    sender_user_id="test_runner",                # テスト発信者
    message_type="reply"
)

print("\n✅ 登録完了")
