portfolio-automation-tools
Overview
目的：個人の学業・生活・研究を効率化する小規模自動化アプリ群（calendar_sync / nutrition_tracker / contact_manager / exercise_dashboard）。


方針：最小構成で動作させ、共通モジュールに依存しない疎結合（現状 common/ 未使用）。


対象読者：初見の利用者・面接官・将来のコントリビュータ。


Features
Exercise_Management：運動ログ、METs 推計、週次トレンド可視化


Housework&Shopping&Household_Management：家事通知（mod/remainder 方式）、家事繰越管理、買い物リスト表示、支出可視化（ジャンル別・支払い手段別統計、月次推移）


Network_Management：基本属性＋タグ付け、検索、誕生日通知、写真と紐づけ


Nutrition_Management：食事登録、栄養素推計、週次トレンド可視化


Schedule_Management：Outlook同期、予定候補登録、タスク作業時間登録、日ごとのタスク処理推奨時間表示


Task_Management：タスクストック、日ごとのタスク表示
Repository Structure
apps/


Exercise_Management/


Housework&Shopping&Household_Managemen/


Network_Management/


Nutrition_Management/


Schedule_Management/


Task_Management/


docs/


architecture.md


ui_concept.pdf


screenshots/


LICENSE / README.md


Requirements
Python 3.11+


主要ライブラリ：streamlit, pandas, matplotlib 等（各 apps の requirements.txt を参照）


OS：Windows 11


Quick Start
Python: 3.11 推奨（3.10–3.12 可）
リポジトリ取得
 git clone https://github.com/you/portfolio-automation-tools.git
 cd portfolio-automation-tools


仮想環境の作成と有効化
 macOS/Linux:
 python -m venv .venv
 source .venv/bin/activate
 Windows (PowerShell):
 python -m venv .venv
 .venv\Scripts\Activate.ps1


依存関係のインストール（例：栄養管理）
 cd apps/Nutrition_Management
 pip install -r requirements.txt


起動（ポート衝突時は値を変更）
 streamlit run app.py --server.port 8501


補足：環境変数でポートを指定する場合
 macOS/Linux: export STREAMLIT_SERVER_PORT=8501
 Windows (PowerShell): $Env:STREAMLIT_SERVER_PORT=8501


Configuration
本リポジトリの各アプリは既定設定で動作します。環境変数の設定は不要です。


データベースはアプリ内の相対パス（例：tasks.db）で完結します。


機密情報は含まれていません。



License
MIT

