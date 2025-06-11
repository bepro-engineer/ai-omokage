---

# 🧠 面影AI – 過去の会話が導く“関係性の記憶”

<div align="center">
<img src="https://raw.githubusercontent.com/bepro-engineer/ai-omokage/main/images/omokage_screen_top.png" width="700">
</div>

## 🧠 面影AI（おもかげ）– 過去の会話で、人を模倣するAI

「“あの人らしい返し”をしてくれるのは、AIじゃなくて、会話の記憶だ。」

---

## ✨ 面影AIとは？

「その口調、まるであの人みたいだね」
これは、面影AIから届く“関係性の記憶”による応答です。

面影AIは、**過去の会話履歴を蓄積・分析し、対象の人物を模倣するAI**です。
ChatGPTとLINEを連携させて構築する “会話模倣AI” で、あなたと他者の会話ログをもとに、
“その人らしい応答”をAIが再現します。

---

## 🚀 なぜ面影AIは特別なのか？

| 通常のAIチャット    | 面影AI              |
| ------------ | ----------------- |
| 一般知識ベースで応答   | **個別の会話履歴ベースで応答** |
| 会話ごとにリセットされる | **会話の流れと関係性を記憶**  |
| 無機質な口調で返す    | **“あの人らしい”口調で返す** |
| 誰にでも同じ応答     | **相手との関係性に応じて変化** |

---

## 💡 こんな人におすすめ

* **あの人との会話をもう一度味わいたい人**
* 自分の過去のやり取りを活かしたい人
* “らしさ”を大事にした対話AIを作りたい人
* 追悼・記録・思い出の継承をAIで行いたい人

---

## 🔁 面影AIが動く2つのモード

| モード        | 内容                                       |
| ---------- | ---------------------------------------- |
| Phase1（記録） | LINEでのやり取りをもとに、会話ログを記録・分類。会話ペアと人格を蓄積します。 |
| Phase2（応答） | 過去のログをもとに、ChatGPTが“その人らしい返答”を生成します。      |

---

## 📚 ブログ解説（導入背景・技術・実装構造）

このプロジェクトの詳しい背景・構造・設計思想については、以下の記事で解説しています。

👉 [面影AIの作り方｜会話の記憶で人を模倣するAIを構築する手順](https://www.pmi-sfbac.org/category/product/ai-omokage-system/)

---

## 💻 面影AIの動作画面

以下は、実際に面影AIをLINE上で動作させた画面イメージです：

* 左：Phase1（記録モード）
* 右：Phase2（応答モード）

<div align="center">
<img src="https://raw.githubusercontent.com/bepro-engineer/ai-omokage/main/images/omokage_screen.png" width="600">
</div>

✍️ 面影AIは「対話の記憶で“関係性”を模倣するAI」です。
Phase1で記録した会話ログが、そのままPhase2での応答の“口調”や“関係性”として反映されます。
つまり、面影AIは「その人らしさ」を言葉で再現するAIなのです。

---

## 📌 プロジェクト構成

```plaintext
ai_omokage/
├── app.py                 # Flaskアプリ本体（LINE受信・処理ルーティング）
├── .env                   # APIキーなどの環境変数
├── requirements.txt       # 必要ライブラリ
├── logic/
│   ├── chatgpt_logic.py   # ChatGPT呼び出し・プロンプト生成・記憶抽出
│   ├── db_utils.py        # SQLite操作（会話ログ保存・検索）
│   └── __init__.py
└── images/
    └── omokage_screen.png # 動作イメージ
```

---

## 🛠️ セットアップ手順（Ubuntu）

```bash
# 1. GitHubからクローン
git clone https://github.com/bepro-engineer/ai-omokage.git
cd ai_omokage

# 2. 仮想環境の構築と起動
python3 -m venv .venv
source .venv/bin/activate

# 3. ライブラリのインストール
pip install -r requirements.txt

# 4. .envファイルの作成
# 以下の内容を.envファイルに記載（各種キーは自分で取得）
OPENAI_API_KEY=sk-xxxxxxx
LINE_CHANNEL_SECRET=xxxxxxxxxx
LINE_CHANNEL_ACCESS_TOKEN=xxxxxxxxxx

# 5. データベース初期化（必要な場合）
python logic/db_utils.py

# 6. テスト起動
python app.py
```

---

## 💬 利用モードについて

```env
PHASE_MODE=learn  → Phase1（記録モード）
PHASE_MODE=reply  → Phase2（応答モード）
```

`.env` ファイル内で `PHASE_MODE` を切り替えて使用してください。

---

## 🛡️ 注意事項

本プロジェクトは自己実験・学習目的で設計されています。
OpenAI APIの利用には料金が発生します。月額上限に注意してください。
記録される会話にはプライバシー上の配慮が必要です。商用利用時は適切な管理が求められます。

---

## 📜 ライセンス

MIT License

---

