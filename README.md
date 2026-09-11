# CSV教材対応 学習支援アプリ

CSVで教材を登録し、複数分野の学習に利用できるWebアプリケーションです。

用語学習、フラッシュカード学習、問題演習、学習履歴、統計情報などの機能を利用できます。

## 教材CSV

ログイン後の「教材データ」画面から、用語CSVと問題CSVを登録できます。

用語CSVの必須列は次の4列です。`ID`はファイル内で重複しない値にしてください。

初回のおすすめには、IDの小さいデータから優先して使用します。

```csv
ID,カテゴリ,用語,意味
1,基礎,hello,こんにちは
2,基礎,goodbye,さようなら
```

問題CSVの必須列は次のとおりです。

```csv
ID,カテゴリ,問題,正答,誤答1,誤答2,誤答3,解説
1,基礎,helloの意味は？,こんにちは,こんばんは,さようなら,ありがとう,基本的な挨拶です。
```

## フォルダ構成

```text
project_g/
├── src/learning_app/    # アプリケーション本体
│   ├── app.py          # Flaskエントリーポイント
│   ├── config.py       # アプリケーション設定
│   ├── models.py       # データベース処理
│   ├── templates/      # HTMLテンプレート
│   └── static/         # CSS・JavaScript
├── data/               # 問題・用語のCSVデータ
├── tests/              # テストコード
├── scripts/            # 補助スクリプト
├── instance/           # ローカルDB（Git管理外）
├── pyproject.toml      # Pythonプロジェクト設定
├── setup.bat           # Windows初期セットアップ
└── start.bat           # Windows起動スクリプト
```

## 起動方法

### バッチファイルを使用する場合（推奨）

#### 初回起動

初めて使用する場合は、`setup.bat` をダブルクリックしてください。

セットアップが完了したら、`start.bat` をダブルクリックするとアプリが起動します。

#### 2回目以降

セットアップ済みの場合は、`start.bat` をダブルクリックしてください。

---

### WSL / Linuxでバッチファイルを使用しない場合

#### 初回起動

ターミナルでプロジェクトフォルダを開きます。

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
python -m flask --app learning_app.app run
```

#### 2回目以降

```bash
source venv/bin/activate
python -m flask --app learning_app.app run
```

### Windowsでバッチファイルを使用しない場合

#### 初回起動

コマンドプロンプトで次のコマンドを実行します。

```bat
python -m venv venv
venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m pip install -e .
python -m flask --app learning_app.app run
```

#### 2回目以降の起動

```bat
venv\Scripts\activate.bat
python -m flask --app learning_app.app run
```

## アクセス方法

起動後、ブラウザで次のURLにアクセスしてください。

<http://127.0.0.1:5000>

## 終了方法

アプリを終了する場合は、起動しているターミナルまたはコマンドプロンプトで `Ctrl+C` を押してください。

### 注意点

本システムでは、ユーザー情報や学習履歴などのデータを、システムを実行しているPC内のデータベースに保存します。

そのため、以下の点にご注意ください。

- PCごとにユーザー情報・学習データは独立しています。
- 別のPCで本システムを利用する場合、以前のPCで作成したアカウントではログインできません。
- 別のPCでは、新しくアカウントを作成してください
- 学習履歴、理解度、メモなどのデータもPC間では引き継がれません。
