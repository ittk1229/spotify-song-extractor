import time
from datetime import datetime

import spotipy
from tqdm import tqdm

from boolean_parser import is_boolean_expression, parse_boolean_expression
from cache_manager import CacheManager
from spotify_client import SpotifyClient


class TrackProcessor:
    """トラック取得・処理・フィルタリングを担当するクラス"""

    def __init__(
        self,
        spotify_client: SpotifyClient,
        cache_manager: CacheManager,
        use_cache: bool = True,
    ):
        self.spotify_client = spotify_client
        self.cache_manager = cache_manager
        self.use_cache = use_cache

    def get_all_artist_tracks(self, artist_id: str) -> list[tuple[str, str, str]]:
        """アーティストの全楽曲情報を取得（キャッシュ対応）"""
        if not self.use_cache:
            return self._get_all_tracks_from_api(artist_id)

        cache_result = self.cache_manager.load_tracks(artist_id)
        if cache_result is not None:
            cached_tracks, last_updated = cache_result
            print(
                f"💾 キャッシュから楽曲情報を読み込みました ({len(cached_tracks)} 曲)"
            )

            new_tracks = self._get_new_tracks_since(artist_id, last_updated)
            if new_tracks:
                print(f"🆕 新しい楽曲を {len(new_tracks)} 曲発見しました")
                updated_tracks = self._merge_tracks(cached_tracks, new_tracks)
                if updated_tracks != cached_tracks:
                    self.cache_manager.save_tracks(artist_id, updated_tracks)
                    print(
                        f"💾 楽曲情報を更新しました (新規追加: {len(updated_tracks) - len(cached_tracks)} 曲, 合計: {len(updated_tracks)} 曲)"
                    )
                    return updated_tracks
                else:
                    print("🔍 新しいユニークな楽曲はありませんでした")
                    return cached_tracks
            else:
                print("🔍 新しい楽曲はありませんでした")
                return cached_tracks

        print("🌐 Spotify APIから楽曲情報を取得中...")
        all_tracks = self._get_all_tracks_from_api(artist_id)
        self.cache_manager.save_tracks(artist_id, all_tracks)
        print(f"💾 楽曲情報をキャッシュに保存しました ({len(all_tracks)} 曲)")
        return all_tracks

    def _merge_tracks(
        self,
        cached_tracks: list[tuple[str, str, str]],
        new_tracks: list[tuple[str, str, str]],
    ) -> list[tuple[str, str, str]]:
        """キャッシュされたトラックと新しいトラックをマージ（重複削除）"""
        existing_ids = {track[0] for track in cached_tracks}
        unique_new_tracks = [
            track for track in new_tracks if track[0] not in existing_ids
        ]

        if unique_new_tracks:
            all_tracks = cached_tracks + unique_new_tracks
            all_tracks.sort(key=lambda x: x[2], reverse=False)  # リリース日順にソート
            return all_tracks
        return cached_tracks

    def _get_new_tracks_since(
        self, artist_id: str, last_updated: str
    ) -> list[tuple[str, str, str]]:
        """last_updated以降にリリースされた楽曲のみを取得"""
        try:
            last_update_date = datetime.fromisoformat(
                last_updated.replace("Z", "+00:00")
            )
        except:
            return self._get_all_tracks_from_api(artist_id)

        print(
            f"🔄 {last_update_date.strftime('%Y-%m-%d %H:%M')} 以降の新しい楽曲を検索中..."
        )

        all_albums = self.spotify_client.get_all_artist_albums(artist_id)
        relevant_albums = self._filter_albums_by_date(all_albums, last_update_date)

        if not relevant_albums:
            return []

        return self._extract_tracks_from_albums(relevant_albums)

    def _filter_albums_by_date(
        self, albums: list[dict], cutoff_date: datetime
    ) -> list[dict]:
        """指定日以降のアルバムをフィルタリング"""
        relevant_albums = []

        for album in albums:
            try:
                release_date_str = album["release_date"]
                if len(release_date_str) == 10:  # YYYY-MM-DD
                    album_date = datetime.fromisoformat(release_date_str + "T00:00:00")
                else:
                    album_date = datetime.fromisoformat(release_date_str)

                if album_date > cutoff_date:
                    relevant_albums.append(album)
                else:
                    break  # 古いアルバムに到達したら終了
            except:
                continue

        return relevant_albums

    def _get_all_tracks_from_api(self, artist_id: str) -> list[tuple[str, str, str]]:
        """APIからアーティストの全楽曲を取得"""
        all_albums = self.spotify_client.get_all_artist_albums(artist_id)
        print(f"アルバム情報を取得中... ({len(all_albums)}個)")

        return self._extract_tracks_from_albums(all_albums)

    def _extract_tracks_from_albums(
        self, albums: list[dict]
    ) -> list[tuple[str, str, str]]:
        """アルバムリストからトラック情報を抽出"""
        all_tracks = []

        for album in tqdm(albums, desc="アルバム処理中", unit="album"):
            try:
                release_date = album["release_date"]
                album_tracks = self.spotify_client.get_album_tracks(album["id"])

                for track in album_tracks:
                    all_tracks.append((track["id"], track["name"], release_date))

            except spotipy.SpotifyException as e:
                print(
                    f"\nアルバム 「{album['name']}」 のトラック取得中にエラーが発生しました: {e}"
                )
                time.sleep(5)

        all_tracks.sort(key=lambda x: x[2], reverse=False)  # リリース日順にソート
        return all_tracks

    def filter_tracks_by_keyword(
        self, tracks: list[tuple[str, str, str]], keyword: str
    ) -> list[tuple[str, str, str]]:
        """キーワードまたはブール式でトラックをフィルタリング"""
        try:
            if is_boolean_expression(keyword):
                # ブール式として処理
                expression = parse_boolean_expression(keyword)
                filtered_tracks = [
                    track for track in tracks if expression.evaluate(track[1])
                ]
                print(
                    f"🔍 ブール式 '{keyword}' に一致する楽曲を {len(filtered_tracks)} 曲見つけました"
                )
            else:
                # 従来の単純な文字列検索
                filtered_tracks = [
                    track for track in tracks if keyword.lower() in track[1].lower()
                ]
                print(
                    f"🔍 キーワード '{keyword}' に一致する楽曲を {len(filtered_tracks)} 曲見つけました"
                )

            return filtered_tracks

        except ValueError as e:
            print(f"❌ ブール式の解析エラー: {e}")
            print("💡 単純なキーワード検索として処理します")
            # エラーの場合は従来の検索にフォールバック
            filtered_tracks = [
                track for track in tracks if keyword.lower() in track[1].lower()
            ]
            print(
                f"🔍 キーワード '{keyword}' に一致する楽曲を {len(filtered_tracks)} 曲見つけました"
            )
            return filtered_tracks

    def get_new_tracks_for_playlist(
        self, tracks: list[tuple[str, str, str]], existing_track_ids: set[str]
    ) -> list[tuple[str, str, str]]:
        """プレイリストに存在しない新しいトラックを取得"""
        return [track for track in tracks if track[0] not in existing_track_ids]
