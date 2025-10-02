# Steam Download Helper - ダウンロード機能について

## download_depot コマンドの制限事項

SteamCMDの`download_depot`コマンドには以下の制限があります：

### 1. 認証要件
- 多くのゲームはanonymousログインではダウンロードできません
- ゲームを所有しているSteamアカウントでログインする必要があります

### 2. 利用可能なデポ
- すべてのデポがダウンロード可能ではありません
- 一部のデポは開発者専用や内部用です

### 3. エラーが発生する場合

以下のエラーが表示される場合：
```
Depot download failed : Invalid default manifest (Missing configuration)
Depot download failed : missing app info (Missing configuration)
```

**考えられる原因：**
- App IDまたはDepot IDが正しくない
- ゲームを所有していない
- anonymousログインでアクセスできないデポ
- そのデポがダウンロード不可能

## ダウンロード可能な例（anonymous）

以下は`login anonymous`でダウンロード可能な例です：

```
# Counter-Strike: Global Offensive - Dedicated Server
download_depot 740 741

# Team Fortress 2 - Dedicated Server  
download_depot 232250 232251

# Left 4 Dead 2 - Dedicated Server
download_depot 222860 222861
```

## 代替ツール

`download_depot`で問題が発生する場合は、以下のツールの使用を検討してください：

- [DepotDownloader](https://github.com/SteamRE/DepotDownloader) - より柔軟なデポダウンロードツール
- Steam公式クライアント - 通常のゲームダウンロード

## トラブルシューティング

1. **正しいIDの確認**
   - [SteamDB](https://steamdb.info/)でApp IDとDepot IDを確認

2. **ログイン状態の確認**
   - 所有ゲームの場合は正しいアカウントでログイン
   - `login username password`を使用

3. **別のデポを試す**
   - 同じゲームの別のデポIDを試してみる

4. **ログを確認**
   - SteamCMDコンソールでエラーの詳細を確認