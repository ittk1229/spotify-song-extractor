from dataclasses import dataclass
from typing import Any

import yaml


@dataclass
class TargetConfig:
    """処理対象の設定を表すデータクラス"""

    name: str
    artist_id: str
    playlist_id: str
    keyword: str


@dataclass
class AuthConfig:
    """認証設定を表すデータクラス"""

    client_id: str
    client_secret: str
    redirect_uri: str


class ConfigManager:
    """設定ファイルの読み込みと管理を担当するクラス"""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self._config_data = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """設定ファイルを読み込む"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"設定ファイルの形式が正しくありません: {e}")

    def get_auth_config(self) -> AuthConfig:
        """認証設定を取得"""
        try:
            return AuthConfig(
                client_id=self._config_data["client_id"],
                client_secret=self._config_data["client_secret"],
                redirect_uri=self._config_data["redirect_uri"],
            )
        except KeyError as e:
            raise ValueError(f"認証設定が不足しています: {e}")

    def get_targets(self) -> list[TargetConfig]:
        """処理対象のリストを取得"""
        try:
            targets_data = self._config_data["targets"]
            targets = []

            for i, target_data in enumerate(targets_data, 1):
                try:
                    target = TargetConfig(
                        name=target_data.get("name", f"Target {i}"),
                        artist_id=target_data["artist_id"],
                        playlist_id=target_data["playlist_id"],
                        keyword=target_data["keyword"],
                    )
                    targets.append(target)
                except KeyError as e:
                    raise ValueError(f"ターゲット {i} の設定が不足しています: {e}")

            return targets
        except KeyError:
            raise ValueError("targets 設定が見つかりません")

