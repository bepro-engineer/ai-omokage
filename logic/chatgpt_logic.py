from openai import OpenAI
import os
from dotenv import load_dotenv
import sqlite3

# .envファイルから環境変数を読み込む
load_dotenv()

# OpenAIクライアント初期化
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✅ 指定カテゴリの記憶を取得（忘却されていないもの）
def getMemoriesByCategory(category, target_user_id, limit=10):
    conn = sqlite3.connect("memory.db")
    c = conn.cursor()
    c.execute("""
        SELECT memory_id, content
        FROM memories
        WHERE is_forgotten = 0
          AND category = ?
          AND target_user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (category, target_user_id, limit))
    results = c.fetchall()
    conn.close()
    return results

# ✅ ChatGPTに与えるプロンプトを構築する（記憶と発話を組み合わせる）
def buildPrompt(memories, user_message, role_label, category):
    memory_section = "\n".join(f"- {m}" for m in memories)
    print(f"🔍 役割: {role_label}")
    print(f"🔍 カテゴリ: {category}")

    # ✅ 安全性確保のための制限命令を追加
    restriction = """
あなたは記憶再現AIです。
性的な内容、疑似恋人としての振る舞い、または性的なロールプレイは一切行ってはいけません。
そのような話題が含まれる場合は「この話題には応答できません」と返答してください。
出力は日本語で、50文字以内に要約して返答してください。
"""

    prompt = f"""
{restriction}

あなたは過去の記憶をもとに、人間らしく返答するAIです。
今回の会話内容は「{category}」カテゴリに属すると判定されています。
今からあなたは「{role_label}」として返答してください。

以下は過去に記録された重要な記憶です：

{memory_section}

この記憶をもとに、以下の発言に自然に返答してください：
「{user_message}」
"""
    return prompt.strip()

# ✅ ChatGPTで自然な応答を得る（カテゴリごとに記憶を絞る）
def getChatGptReply(user_message, target_user_id):
    # ① カテゴリ判定
    category = getCategoryByGpt(user_message)
    print(f"🔍 判定カテゴリ: {category}")

    # ② 指定カテゴリ × ユーザーIDの記憶を取得
    MEMORY_TARGET_USER_ID = os.getenv("MEMORY_TARGET_USER_ID")
    memory_items = getMemoriesByCategory(category, MEMORY_TARGET_USER_ID)
    memory_ids = [m[0] for m in memory_items]
    memory_texts = [m[1] for m in memory_items]

    # ③ プロンプト生成
    role_label = os.getenv("TARGET_ROLE")
    prompt = buildPrompt(memory_texts, user_message, role_label, category)


    # ④ ChatGPT API呼び出し
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "あなたは過去の記憶を踏まえて人間らしく返答するAIです。"},
            {"role": "user", "content": prompt}
        ]
    )

    reply_text = response.choices[0].message.content.strip()

    print(f"🧠 使用記憶ID: {memory_ids}")
    print(f"🧠 記憶数: {len(memory_texts)}件")
    print(f"🧠 カテゴリ: {category}")

    return {
        "reply_text": reply_text,
        "used_memory_ids": memory_ids,
        "used_category": category
    }

# ✅ ユーザー発言をカテゴリに分類（Phase1と共通）
def getCategoryByGpt(message):
    system_prompt = (
        "以下のユーザー発言に対して、最も適切なカテゴリを1単語で返してください。\n"
        "候補カテゴリには「家族」「仕事」「感情」「趣味」「健康」「その他」があります。\n"
        "出力はカテゴリ名のみで、他の説明を含めないでください。"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
        )
        category = response.choices[0].message.content.strip()
        return category if category else "uncategorized"
    except Exception as e:
        print("[ChatGPT Error]", e)
        return "uncategorized"
