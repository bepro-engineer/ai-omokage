import sqlite3
import os
import json

# 使用するSQLiteデータベースのファイル名
DB_NAME = "memory.db"

# データベースが存在しない場合、初期化処理を行う
def initDatabase():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # memories テーブルが存在するか確認（テーブルの有無で制御）
    c.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='memories';
    """)
    result = c.fetchone()

    if result is None:
        print("✅ memories テーブルが存在しないので、初期化を開始します。")

        # 記憶本体テーブル（修正後）
        c.execute("""
            CREATE TABLE memories (
                memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                category TEXT,
                target_user_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                current_weight INTEGER DEFAULT 1,
                deleted_flag INTEGER DEFAULT 0,
                is_forgotten INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 発話ログテーブル（Phase2用）
        c.execute("""
            CREATE TABLE dialogues (
                dialogue_id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_user_id TEXT NOT NULL,
                sender_user_id TEXT NOT NULL,
                message_type TEXT NOT NULL,
                is_ai_generated BOOLEAN NOT NULL,
                text TEXT NOT NULL,
                memory_refs TEXT,
                prompt_version TEXT,
                temperature REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 重み履歴テーブル
        c.execute("""
            CREATE TABLE weights (
                weight_id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id INTEGER NOT NULL,
                interact TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (memory_id) REFERENCES memories(memory_id)
            )
        """)

        conn.commit()
        print("✅ 初期化が完了しました。")
    else:
        print("✅ すでに初期化済みです。テーブルは存在しています。")

    conn.close()

# ✅ 記憶と発話ログを1つのトランザクションで同時に保存（カテゴリ＋weight＝1）
def registerMemoryAndDialogue(
    user_id,
    message,
    content,
    category,
    memory_refs=None,
    is_ai_generated=False,
    sender_user_id="self",
    message_type="input"
):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        # ✅ 記憶を保存（初期weight=1）
        c.execute(
            """
            INSERT INTO memories
            (content, category, current_weight, target_user_id, user_id)
            VALUES
            (?, ?, ?, ?, ?)
            """,
            (content, category, 1, user_id, user_id)
        )
        memory_id = c.lastrowid

        # ✅ 発話ログ（dialogues）へ保存
        c.execute(
            """
            INSERT INTO dialogues (
                target_user_id, sender_user_id, message_type,
                is_ai_generated, text, memory_refs,
                prompt_version, temperature
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                sender_user_id,
                message_type,
                is_ai_generated,
                message,
                json.dumps(memory_refs) if memory_refs else None,
                None,
                None
            )
        )

        # ✅ 重み初期ログ
        c.execute(
            "INSERT INTO weights (memory_id, interact) VALUES (?, ?)",
            (memory_id, "初期登録（weight=1）")
        )

        conn.commit()
        print("Memory and dialogue registered.")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# ✅ 全記憶（忘却フラグなし）
def getAllMemories():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT memory_id, content, category, weight FROM memories WHERE is_forgotten = 0")
    results = c.fetchall()
    conn.close()
    return results

# ✅ 重み履歴を追加
def insertWeightLog(memory_id, interact):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO weights (memory_id, interact) VALUES (?, ?)",
            (memory_id, interact)
        )
        conn.commit()
        print(f"Weight log inserted for memory_id={memory_id}")
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# ✅ 特定memory_idに紐づく重み履歴を取得
def getWeightLogsByMemoryId(memory_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "SELECT interact, created_at FROM weights WHERE memory_id = ? ORDER BY created_at DESC",
        (memory_id,)
    )
    logs = c.fetchall()
    conn.close()
    return logs

# ✅ 全weight履歴を取得（管理・表示用）
def getAllWeightLogs():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT weight_id, memory_id, interact, created_at FROM weights ORDER BY created_at DESC")
    logs = c.fetchall()
    conn.close()
    return logs

# ✅ 単体実行でのテスト実行
if __name__ == "__main__":
    initDatabase()
    # 任意テスト用サンプル
    # registerMemoryAndDialogue("U123", "これはテスト発言です", "これは記憶です", "感情")
    # print(getAllMemories())
    # insertWeightLog(1, "再評価：強調対象としてweight変更候補")
    # print(getWeightLogsByMemoryId(1))
