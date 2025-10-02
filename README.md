# Morn Steam アップロードヘルパー
<img width="1210" height="1010" alt="image" src="https://github.com/user-attachments/assets/0bda36c0-98d0-4c89-8f0d-e42b30d102b8" />

Steamへのゲームアップロードを簡単にするGUIツールです。複雑なSteamCMDコマンドを覚える必要なく、直感的な操作でゲームをSteamにアップロードできます。

![License](https://img.shields.io/badge/license-Unlicense-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey.svg)

## 🎮 主な機能

- **日本語対応GUI**: 完全日本語化された使いやすいインターフェース
- **設定の保存**: 複数のアップロード設定を保存・管理
- **自動VDF生成**: VDFファイルを自動で作成
- **自動コマンド送信**: Windows/macOSでSteamCMDへ自動でコマンドを送信
- **ダウンロード機能**: ManifestGID指定による特定バージョンのダウンロードに対応
- **マルチプラットフォーム対応**: Windows、macOSで動作

## 📋 必要なもの

- Python 3.7以上
- Steamworks SDK
- Steamworksパートナーアカウント

## 🚀 インストール方法

1. このツールをダウンロード:

   **Gitを使う場合:**
   ```bash
   git clone https://github.com/yourusername/MornSteamUploadHelper.git
   cd MornSteamUploadHelper
   ```

   **ZIPでダウンロードする場合:**
   - GitHubの「Code」ボタンから「Download ZIP」を選択
   - ダウンロードしたZIPファイルを解凍

2. 必要なライブラリをインストール:
   ```bash
   pip install -r requirements.txt
   ```

3. Steam ContentBuilder SDKをダウンロード:
   - [Steamworks ダウンロードページ](https://partner.steamgames.com/downloads/list)にアクセス
   - 「Steamworks SDK」をダウンロード
   - 任意のフォルダに解凍（解凍後、中に「ContentBuilder」フォルダがあります）

## 🎯 使い方

### 🪟 Windows
1. `MornSteamUploadHelper.bat`をダブルクリック

### 🍎 macOS
1. **初回のみ**: 権限の設定が必要な場合があります
   - ターミナルを開く
   - 以下のコマンドを実行:
     ```bash
     chmod +x MornSteamUploadHelper.command
     ```

2. `MornSteamUploadHelper.command`をダブルクリック
   
### ⚙️ 使用手順

1. **ContentBuilderの設定**（初回のみ）:
   - 「基本設定」をクリック
   - 「ContentBuilderフォルダを選択」で、解凍したSDKの中にある「ContentBuilder」フォルダを選択

2. **Steamログイン**:
   - Steamのユーザー名とパスワードを入力
   - Steam Guardを設定している場合は認証コードも入力
   - 「ログイン」をクリック

3. **アップロード設定**:
   - **App ID**: あなたのゲームのApp ID
   - **Depot ID**: あなたのゲームのDepot ID
   - **コンテンツフォルダ**: アップロードするゲームファイルのフォルダ
   - **ブランチ**: アップロード先のブランチ（beta、publicなど）
   - **説明**: ビルドの説明（任意）

4. **アップロード実行**:
   - 設定に名前を付けて保存
   - 「アップロード」ボタンをクリックして実行

### 📥 ダウンロード機能

SteamCMDの`download_depot`コマンドを使用して、特定のビルドをダウンロードできます。

1. **ダウンロード設定**:
   - **App ID**: ダウンロードするゲームのApp ID
   - **Depot ID**: ダウンロードするDepot ID
   - **Manifest GID**: ダウンロードする特定のビルドのManifest GID
   
2. **Manifest GIDの確認方法**:
   - 「ビルドページを開く」ボタンをクリック（App ID入力後）
   - 「ビルドID」を選択する
   - "**マニフェストGID**" を確認できます

3. **注意事項**:
   - アクティブなブランチの最新ビルドのみダウンロード可能
   - 非アクティブブランチや過去のビルドはダウンロード不可
   - ゲームの所有権が必要（開発者アカウントでログイン必須）

## ⚠️ 注意事項

### アップロード中の操作について
- **Windows/macOS**: アップロードコマンドは自動でSteamCMDコンソールに送信されます
- **重要**: コマンド送信時にコンソールウィンドウにフォーカスを移動するため、**アップロード開始後は他の操作をしないことを推奨します**
- アップロードの進行状況はSteamCMDコンソールで確認できます

# ライセンス
The Unlicense（パブリックドメイン）

# 開発
この拡張機能は[Claude Code](https://claude.ai/code)を使用して作成されました。

# 貢献
Issue報告やPull Requestは大歓迎です！
