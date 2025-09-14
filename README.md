# Spotify Song Extractor

アーティストの楽曲から特定のキーワードを含むものを抽出し、指定したプレイリストに自動追加するツールです！

## Demo

- 条件
  - アーティスト：[電音部](https://open.spotify.com/intl-ja/artist/3wCJxpjgYDXbwLn4vmSBEx)
  - キーワード：Insturumental

![playlist](https://gyazo.com/dbed379ba21fad3e6d87872a4984478d.png)

[この例で作成したプレイリスト](https://open.spotify.com/playlist/5IyIuR8aVu0V2iBr6wO1i2)

## Setup

### 前提条件

- git
- uv

### インストール手順

```bash
# 1. リポジトリをクローン
git clone https://github.com/ittk1229/spotify-song-extractor

# 2. ディレクトリ移動
cd spotify-song-extractor

# 3. 依存関係をインストール
uv sync

# 4. 設定のテンプレートをコピーし、APIキーや抽出条件などを記述
cp config.yaml.example config.yaml

# 5. アプリケーションを実行
uv run src/main.py
```

### 設定内容

#### Spotify の認証情報について

- はじめに [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) でアプリケーションを作成してください
  - こちらの[解説記事](https://note.com/sfp_note/n/n09c8415cbb45)に手順が詳しく説明されています
- アプリケーションの作成後、設定ファイルの`config.yaml`にクライアント ID、クライアントシークレット、リダイレクト URI を記述してください

```yaml:config.yaml
client_id: クライアントID
client_secret: クライアントシークレット
redirect_uri: リダイレクトURI
```

#### 抽出条件について

- 設定ファイルには上記認証情報の他に、楽曲収集対象のアーティスト、楽曲追加先のプレイリスト、抽出条件であるキーワードを指定してください

対象アーティストの ID を取得（下記画像の URL の末尾）

![Image from Gyazo](https://i.gyazo.com/75d6fecdcf513eed332f9b1a18d890c5.png)

楽曲追加先のプレイリストを作成し、その ID を取得（下記画像の URL の末尾）

![Image from Gyazo](https://i.gyazo.com/a63a12221afbae627780a58baee09b1e.png)

```yaml:config.yalm
targets:
  - name: Instrumental Collection  # ツール実行中に表示される名前で、プレイリスト名である必要はありません
    artist_id: アーティストID
    playlist_id: プレイリストID
    keyword: Instrumental
```

#### 設定ファイル

1 つの設定ファイルに認証情報とアプリ設定の両方を記述してください

**複数の処理対象**を指定して一度に実行できます

```yaml
client_id: クライアントID
client_secret: クライアントシークレット
redirect_uri: リダイレクトURI

# 処理対象の設定（複数指定可能）
targets:
  - name: Instrumental Collection
    artist_id: アーティストID1
    playlist_id: プレイリストID1
    keyword: Instrumental
  - name: Remix Collection
    artist_id: アーティストID2
    playlist_id: プレイリストID2
    keyword: Remix
```

## コマンドラインオプション

| オプション      | 短縮形 | 説明                                               |
| --------------- | ------ | -------------------------------------------------- |
| `--config`      | `-c`   | 設定ファイルのパス（デフォルト: config.yaml）      |
| `--dry-run`     | `-d`   | プレビューモード（実際には追加しない）             |
| `--verbose`     | `-v`   | 詳細な出力を有効化                                 |
| `--cache-dir`   |        | キャッシュディレクトリ（デフォルト: .track_cache） |
| `--clear-cache` |        | 実行前にキャッシュをクリア                         |
| `--no-cache`    |        | キャッシュを無効化（常に API から取得）            |
| `--help`        | `-h`   | ヘルプを表示                                       |

## キャッシュ機能

- アーティストの楽曲情報をキャッシュ
- 2 回目以降の実行で API 呼び出しを大幅削減
- 定期実行や dry-run での事前ロード → 本実行に最適

### 使用例

```bash
# 初回実行（キャッシュ作成）
uv run main.py --dry-run
💾 キャッシュから楽曲情報を読み込みました (245 曲)
🔍 [DRY RUN] 合計 5 曲が追加される予定です

# 本実行（キャッシュ使用で高速）
uv run main.py
💾 キャッシュから楽曲情報を読み込みました (245 曲)
🎉 処理完了！合計 5 曲をプレイリストに追加しました

# キャッシュクリアしてから実行
uv run main.py --clear-cache

# キャッシュ無効
uv run main.py --no-cache
```

### キャッシュファイル

- 保存場所: `.track_cache/` ディレクトリ
- ファイル名: `{アーティストID}.json`
