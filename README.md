VPS環境（Ubuntu）での動作・GitHubクローン・環境構成が前提の構成になっています。

📚 詳細な解説はこちら<br><br>
本プロジェクトの詳しい背景や仕組み、導入手順については、以下のブログ記事で解説しています。<br>
👉 面影AI｜いつか消える面影を、繋ぐ未来をAIに託す挑戦<br>
詳しい説明は<a href="https://www.pmi-sfbac.org/category/product/ai-omokage-system/" target="_blank">こちらのブログ記事 (Beエンジニア)</a>をご覧ください。

---
## 💻 面影AIの動作画面

以下は、実際に面影AIを実行したときの画面例です。<br>
- 面影AIでは、ユーザーが特定の人物をターゲットとして記憶データを蓄積していきます。<br>
- 今回のサンプルでは、「母」を対象とした設定で動作させています。

<div align="center">
  <img src="https://github.com/bepro-engineer/ai-omokage/raw/main/images/omokage_screen.png" width="300">
</div>

```plaintext
# 面影AI（Omokage AI）

「かつての自分から、いまの自分へ答えが届く。」

## 📌 プロジェクト概要

面影AIは、ChatGPTを利用して「過去の自分」の発言や記録をもとに、現在の自分へ応答する自己対話AIです。Phase構成を用いて、記憶の蓄積・再生を段階的に実装しています。

## 🧩 構成ファイル
```
ai_omokage/
  - app.py：エントリーポイント
  - config.py：設定ファイル
  - .env：環境変数
  - requirements.txt：ライブラリ一覧
  - logic/
    - __init__.py
    - chatgpt_logic.py：ChatGPT処理
    - db_utils.py：DB処理
```

## 🚀 セットアップ手順（Ubuntu）
1. GitHubからクローン  
   ※PAT（Personal Access Token）を使用してクローンする必要があります。
   ```bash
   cd ~/projects/ai_omokage
   git clone https://github.com/bepro-engineer/ai-omokage.git
````

2. 仮想環境の作成と起動
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. 依存ライブラリのインストール
   ```bash
   pip install -r requirements.txt
   ```

4. `.env`ファイルの作成
   `.env` に以下を記載（OpenAI APIキーは自身で取得）
   ```
   OPENAI_API_KEY=sk-xxxxxxx
   ```

5. データベース初期化（必要に応じて）
   ```bash
   python logic/db_utils.py
   ```

## 🧪 テスト起動
```bash
python app.py
```

## 💬 モード構成
* `/learn`: 自己記録（記憶）を蓄積
* `/reply`: 記憶から過去の自分が応答

## 🛡️ 注意事項
* 本プロジェクトは**研究・学習用途**です。商用利用はライセンスを確認の上、自己責任で行ってください。
* OpenAIのAPIコストが発生します。使用量には十分注意してください。

## 📝 ライセンス
```plaintext
MIT License
```
