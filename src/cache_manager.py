import json
from datetime import datetime
from pathlib import Path


class CacheManager:
    """トラック情報のキャッシュ管理を担当するクラス"""

    def __init__(self, cache_dir: str = ".track_cache"):
        self.cache_dir = Path(cache_dir)
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        """キャッシュディレクトリを作成"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, artist_id: str) -> Path:
        """キャッシュファイルのパスを取得"""
        return self.cache_dir / f"{artist_id}.json"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """キャッシュが有効かチェック"""
        return cache_path.exists()

    def save_tracks(self, artist_id: str, tracks: list[tuple[str, str, str]]):
        """楽曲情報をキャッシュに保存"""
        cache_path = self._get_cache_path(artist_id)

        cache_data = {
            "artist_id": artist_id,
            "last_updated": datetime.now().isoformat(),
            "tracks": tracks,
        }

        cache_path.write_text(
            json.dumps(cache_data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def load_tracks(
        self, artist_id: str
    ) -> tuple[list[tuple[str, str, str]], str] | None:
        """キャッシュから楽曲情報を読み込み、(tracks, last_updated) を返す"""
        cache_path = self._get_cache_path(artist_id)

        if not self._is_cache_valid(cache_path):
            return None

        try:
            cache_data = json.loads(cache_path.read_text(encoding="utf-8"))
            tracks = [tuple(track) for track in cache_data["tracks"]]
            last_updated = cache_data.get("last_updated", "1900-01-01T00:00:00")
            return tracks, last_updated
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            return None

    def clear_cache(self):
        """キャッシュディレクトリを削除"""
        import shutil

        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            print(f"🗑️  キャッシュディレクトリ '{self.cache_dir}' をクリアしました")
