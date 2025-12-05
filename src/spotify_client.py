import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth


class SpotifyClient:
    """Spotify API操作を担当するクラス"""

    def __init__(self, auth_config: dict):
        self.sp = self._create_spotify_client(auth_config)

    def _create_spotify_client(self, config: dict) -> spotipy.Spotify:
        """Spotify クライアントを初期化する"""
        return spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=config["client_id"],
                client_secret=config["client_secret"],
                redirect_uri=config["redirect_uri"],
                scope="playlist-modify-private playlist-modify-public playlist-read-private",
            )
        )

    def get_artist_name(self, artist_id: str) -> str:
        """アーティスト名を取得"""
        try:
            artist = self.sp.artist(artist_id)
            return artist["name"]
        except spotipy.SpotifyException as e:
            print(f"アーティスト情報の取得中にエラーが発生しました: {e}")
            return "不明なアーティスト"

    def get_playlist_name(self, playlist_id: str) -> str:
        """プレイリスト名を取得"""
        try:
            playlist = self.sp.playlist(playlist_id, fields="name")
            return playlist["name"]
        except spotipy.SpotifyException as e:
            print(f"プレイリスト情報の取得中にエラーが発生しました: {e}")
            return "不明なプレイリスト"

    def get_all_playlist_tracks(self, playlist_id: str) -> set[str]:
        """プレイリスト内のすべてのトラックIDを取得する"""
        tracks = set()
        offset = 0
        retrieved_items = 0

        while True:
            try:
                response = self.sp.playlist_items(
                    playlist_id, offset=offset, limit=100, fields="items.track.id,total"
                )
                items = response.get("items", [])
                new_tracks = {item["track"]["id"] for item in items if item["track"]}
                tracks.update(new_tracks)
                retrieved_items += len(items)

                total_tracks = response.get("total")
                # すべてのプレイリスト項目を処理したか、または項目が返らなくなったら終了
                if not items:
                    break
                if total_tracks is not None and retrieved_items >= total_tracks:
                    break

                offset += len(items)
            except spotipy.SpotifyException as e:
                print(f"プレイリストトラックの取得中にエラーが発生しました: {e}")
                time.sleep(5)

        return tracks

    def get_all_artist_albums(
        self,
        artist_id: str,
        per_type_limit: int = 20,
        known_album_ids: set[str] | None = None,
    ) -> list[dict]:
        """アルバム種別ごとに新しい順で取得し、既知のアルバムのみになったら停止"""
        all_albums = []
        seen_album_ids: set[str] = set()
        known_album_ids = known_album_ids or set()
        album_types = ["album", "single", "compilation"]

        for album_type in album_types:
            album_offset = 0

            while True:
                response = self.sp.artist_albums(
                    artist_id,
                    album_type=album_type,
                    limit=per_type_limit,
                    offset=album_offset,
                )
                albums = response["items"]
                if not albums:
                    break

                new_albums_in_batch = 0
                for album in albums:
                    album_id = album.get("id")
                    if not album_id or album_id in seen_album_ids:
                        continue

                    seen_album_ids.add(album_id)

                    if album_id in known_album_ids:
                        continue

                    all_albums.append(album)
                    new_albums_in_batch += 1

                if (
                    (known_album_ids and new_albums_in_batch == 0)
                    or len(albums) < per_type_limit
                ):
                    break

                album_offset += len(albums)

        return all_albums

    def get_album_tracks(self, album_id: str) -> list[dict]:
        """アルバムの全トラック情報を取得"""
        all_tracks = []
        track_offset = 0

        while True:
            tracks = self.sp.album_tracks(album_id, limit=50, offset=track_offset)
            track_items = tracks["items"]

            if not track_items:
                break

            all_tracks.extend(track_items)

            if len(track_items) < 50:
                break

            track_offset += len(track_items)
            if track_offset > 0:
                time.sleep(0.1)  # API呼び出し制限を避ける

        return all_tracks

    def add_tracks_to_playlist(self, playlist_id: str, track_ids: list[str]) -> None:
        """プレイリストに曲を追加する（100曲ずつバッチ処理）"""
        for i in range(0, len(track_ids), 100):
            batch = track_ids[i : i + 100]
            try:
                self.sp.playlist_add_items(playlist_id, batch)
            except spotipy.SpotifyException as e:
                print(f"プレイリストへの曲の追加中にエラーが発生しました: {e}")
                time.sleep(5)
