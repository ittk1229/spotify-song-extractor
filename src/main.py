import click
from typing import List, Tuple

from cache_manager import CacheManager
from config_manager import ConfigManager, TargetConfig
from spotify_client import SpotifyClient
from track_processor import TrackProcessor, TrackEntry


class SpotifyTrackExtractor:
    """Spotifyから楽曲を抽出してプレイリストに追加するオーケストレータークラス"""

    def __init__(self, config_manager: ConfigManager, cache_dir: str = ".track_cache", use_cache: bool = True):
        self.config_manager = config_manager
        auth_config = config_manager.get_auth_config()
        auth_dict = {
            "client_id": auth_config.client_id,
            "client_secret": auth_config.client_secret,
            "redirect_uri": auth_config.redirect_uri,
        }
        self.spotify_client = SpotifyClient(auth_dict)
        self.cache_manager = CacheManager(cache_dir)
        self.track_processor = TrackProcessor(self.spotify_client, self.cache_manager, use_cache)
    
    def get_artist_name(self, artist_id: str) -> str:
        """アーティスト名を取得"""
        return self.spotify_client.get_artist_name(artist_id)
    
    def get_playlist_name(self, playlist_id: str) -> str:
        """プレイリスト名を取得"""
        return self.spotify_client.get_playlist_name(playlist_id)
    
    def get_all_playlist_tracks(self, playlist_id: str) -> set[str]:
        """プレイリスト内のすべてのトラックIDを取得する"""
        return self.spotify_client.get_all_playlist_tracks(playlist_id)
    
    def get_artist_filtered_tracks(self, artist_id: str, keyword: str) -> list[TrackEntry]:
        """アーティストの指定キーワードに一致する曲を取得"""
        all_tracks = self.track_processor.get_all_artist_tracks(artist_id)
        return self.track_processor.filter_tracks_by_keyword(all_tracks, keyword)
    
    def add_tracks_to_playlist(self, playlist_id: str, track_ids: list[str]) -> None:
        """プレイリストに曲を追加する"""
        self.spotify_client.add_tracks_to_playlist(playlist_id, track_ids)
    
    def clear_cache(self):
        """キャッシュをクリア"""
        self.cache_manager.clear_cache()


def initialize_application(config: str, cache_dir: str, clear_cache: bool, no_cache: bool) -> Tuple[ConfigManager, SpotifyTrackExtractor]:
    """アプリケーションを初期化し、設定とExtractorインスタンスを返す"""
    try:
        config_manager = ConfigManager(config)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ 設定エラー: {e}")
        raise
    
    # キャッシュクリア処理
    if clear_cache:
        cache_manager = CacheManager(cache_dir)
        cache_manager.clear_cache()
    
    # キャッシュ無効化の場合は一時的にキャッシュディレクトリを変更
    actual_cache_dir = cache_dir if not no_cache else f"{cache_dir}_disabled"
    extractor = SpotifyTrackExtractor(config_manager, actual_cache_dir, not no_cache)
    
    return config_manager, extractor


def print_startup_info(targets: List[TargetConfig], cache_dir: str, no_cache: bool, dry_run: bool):
    """起動時の情報を表示"""
    cache_status = "無効" if no_cache else f"有効 (ディレクトリ: {cache_dir})"
    print(f"🎵 {len(targets)}個の処理対象を実行します")
    print(f"💾 キャッシュ: {cache_status}")
    if dry_run:
        print("🔍 DRY RUN モード: 実際の追加は行いません")
    print()


def print_target_header(i: int, total: int, target_name: str):
    """ターゲット処理開始時のヘッダーを表示"""
    print(f"{'=' * 60}")
    print(f"📁 処理中 ({i}/{total}): {target_name}")
    print(f"{'=' * 60}")


def print_target_info(artist_name: str, playlist_name: str, keyword: str, verbose: bool):
    """ターゲットの詳細情報を表示"""
    if verbose:
        print(f"🎤 アーティスト: {artist_name}")
        print(f"📋 プレイリスト: {playlist_name}")
        print(f"🔍 キーワード: '{keyword}'")


def print_track_list(tracks: List[TrackEntry], dry_run: bool, playlist_name: str, verbose: bool):
    """見つかったトラックのリストを表示"""
    if dry_run:
        print(f"[DRY RUN] {len(tracks)}曲の新しい曲が「{playlist_name}」に追加される予定です:")
    else:
        print(f"{len(tracks)}曲の新しい曲を 「{playlist_name}」 に追加します...")
    
    for j, track in enumerate(tracks, 1):
        track_name = track[1]
        release_date = track[2]
        if verbose:
            print(f"  {j:02}. {track_name} (リリース日: {release_date})")
        elif j <= 5:
            print(f"  {j:02}. {track_name}")
        elif j == 6:
            print(f"  ... and {len(tracks) - 5} more tracks")


def process_single_target(extractor: SpotifyTrackExtractor, target: TargetConfig, 
                         dry_run: bool, verbose: bool) -> int:
    """単一のターゲットを処理し、追加された曲数を返す"""
    artist_name = extractor.get_artist_name(target.artist_id)
    playlist_name = extractor.get_playlist_name(target.playlist_id)
    
    print_target_info(artist_name, playlist_name, target.keyword, verbose)
    
    # 既存のトラック取得
    print(f"プレイリスト「{playlist_name}」の楽曲情報を取得中...")
    existing_tracks = extractor.get_all_playlist_tracks(target.playlist_id)
    
    # アーティストのトラック取得とフィルタリング
    print(f"アーティスト「{artist_name}」の楽曲情報を取得中...（キーワード: '{target.keyword}'）")
    filtered_tracks = extractor.get_artist_filtered_tracks(target.artist_id, target.keyword)
    
    # 新しいトラックの特定
    new_tracks = [track for track in filtered_tracks if track[0] not in existing_tracks]
    
    if new_tracks:
        print_track_list(new_tracks, dry_run, playlist_name, verbose)
        
        if not dry_run:
            extractor.add_tracks_to_playlist(target.playlist_id, [track[0] for track in new_tracks])
            print("  ✅ プレイリストへの追加が完了しました")
        
        # 詳細モードでは最終トラック数を表示
        if not dry_run and verbose:
            final_track_count = len(extractor.get_all_playlist_tracks(target.playlist_id))
            print(f"  📊 「{playlist_name}」 の最終トラック数: {final_track_count}")
        
        return len(new_tracks)
    else:
        print("  新しく追加する曲はありませんでした")
        return 0


def print_summary(total_added: int, dry_run: bool):
    """処理完了後のサマリーを表示"""
    print(f"{'=' * 60}")
    if dry_run:
        print(f"🔍 [DRY RUN] 合計 {total_added} 曲が追加される予定です")
    else:
        print(f"🎉 処理完了！合計 {total_added} 曲をプレイリストに追加しました")
    print(f"{'=' * 60}")


@click.command()
@click.option(
    "--config",
    "-c",
    default="config.yaml",
    help="Path to the configuration file (includes both app settings and credentials).",
)
@click.option(
    "--dry-run",
    "-d",
    is_flag=True,
    help="Show what would be added without actually adding tracks to the playlist.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output with detailed progress information.",
)
@click.option(
    "--cache-dir",
    default=".track_cache",
    help="Directory to store cache files (default: .track_cache).",
)
@click.option(
    "--clear-cache",
    is_flag=True,
    help="Clear all cache files before running.",
)
@click.option(
    "--no-cache",
    is_flag=True,
    help="Disable cache usage (always fetch from API).",
)
def main(config: str, dry_run: bool, verbose: bool, cache_dir: str, clear_cache: bool, no_cache: bool):
    """Spotify楽曲抽出ツールのメインエントリーポイント"""
    try:
        # アプリケーション初期化
        config_manager, extractor = initialize_application(config, cache_dir, clear_cache, no_cache)
        targets = config_manager.get_targets()
        
        # 起動情報表示
        actual_cache_dir = cache_dir if not no_cache else f"{cache_dir}_disabled"
        print_startup_info(targets, actual_cache_dir, no_cache, dry_run)
        
        # 各ターゲットを処理
        total_added = 0
        for i, target in enumerate(targets, 1):
            print_target_header(i, len(targets), target.name)
            
            added_count = process_single_target(extractor, target, dry_run, verbose)
            total_added += added_count
            
            print()  # ターゲット間の区切り
        
        # サマリー表示
        print_summary(total_added, dry_run)
        
    except (FileNotFoundError, ValueError):
        # 初期化エラーは既にprint済み
        return
    except KeyboardInterrupt:
        print("\n⚠️  処理が中断されました")
        return
    except Exception as e:
        print(f"❌ 予期しないエラーが発生しました: {e}")
        return


if __name__ == "__main__":
    main()
