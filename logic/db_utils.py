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

        # ✅ 記憶本体テーブル（target_user_id 削除）
        c.execute("""
            CREATE TABLE memories (
                memory_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                content        TEXT    NOT NULL,
                category       TEXT,
                user_id        TEXT    NOT NULL,  -- ← 発言主（記憶所有者）
                current_weight INTEGER DEFAULT 1,
                deleted_flag   INTEGER DEFAULT 0,
                is_forgotten   INTEGER DEFAULT 0,
                created_at     TEXT    DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ✅ 発話ログテーブル（target_user_id は残す）
        c.execute("""
            CREATE TABLE dialogues (
                dialogue_id           INTEGER PRIMARY KEY AUTOINCREMENT,
                target_user_id        TEXT    NOT NULL,      -- ← 返信相手のID
                sender_user_id        TEXT    NOT NULL,      -- ← 発信者のID
                message_type          TEXT    NOT NULL,      -- 'input' / 'reply'
                is_ai_generated       BOOLEAN NOT NULL,      -- 1=AI, 0=human
                text                  TEXT    NOT NULL,
                category              TEXT,
                parent_dialogue_id    INTEGER,
                memory_refs           TEXT,
                prompt_version        TEXT,
                temperature           REAL,
                created_at            TEXT    DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 重み履歴テーブル
        c.execute("""
            CREATE TABLE weights (
                weight_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id   INTEGER NOT NULL,
                interact    TEXT,
                created_at  TEXT    DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (memory_id) REFERENCES memories(memory_id)
            )
        """)

        conn.commit()
        print("✅ 初期化が完了しました。")
    else:
        print("✅ すでに初期化済みです。テーブルは存在しています。")

    conn.close()

# ✅ 記憶と発話ログを 1 トランザクションで保存
def registerMemoryAndDialogue(
    user_id: str,
    message: str,
    content: str,
    category: str,
    memory_refs=None,
    is_ai_generated=False,
    sender_user_id="self",
    message_type="input",
    parent_dialogue_id=None
) -> int:
    """
    ・memories      : user_id 単位で記憶保存
    ・dialogues     : 対話ログに sender/target を記録（役割保持）
    ・weights       : 重みログも記録
    """
    conn = sqlite3.connect(DB_NAME)
    c    = conn.cursor()
    try:
        # ✅ memories へ INSERT（target_user_id は不要）
        c.execute(
            """
            INSERT INTO memories (
                content, category, current_weight, user_id
            ) VALUES (?, ?, 1, ?)
            """,
            (content, category, user_id)
        )
        memory_id = c.lastrowid

        # ✅ dialogues へ INSERT（sender / target を明記）
        c.execute(
            """
            INSERT INTO dialogues (
                target_user_id, sender_user_id, message_type,
                is_ai_generated, text, memory_refs,
                category, parent_dialogue_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                sender_user_id if sender_user_id != user_id else user_id,  # target = 相手側
                sender_user_id,
                message_type,
                int(is_ai_generated),
                message,
                json.dumps(memory_refs) if memory_refs else None,
                category,
                parent_dialogue_id
            )
        )
        dialogue_id = c.lastrowid

        # ✅ weights へ INSERT
        c.execute(
            "INSERT INTO weights (memory_id, interact) VALUES (?, ?)",
            (memory_id, "初期登録（weight=1）")
        )

        conn.commit()
        print("Memory & dialogue registered (dialogue_id = {})".format(dialogue_id))
        return dialogue_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# ✅ 全記憶（忘却フラグなし）
def getAllMemories():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT memory_id, content, category, current_weight FROM memories WHERE is_forgotten = 0")
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
