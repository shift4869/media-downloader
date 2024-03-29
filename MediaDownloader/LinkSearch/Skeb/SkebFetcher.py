# coding: utf-8
from dataclasses import dataclass
from logging import INFO, getLogger
from pathlib import Path

from MediaDownloader.LinkSearch.FetcherBase import FetcherBase
from MediaDownloader.LinkSearch.Password import Password
from MediaDownloader.LinkSearch.Skeb.Converter import Converter
from MediaDownloader.LinkSearch.Skeb.SkebDownloader import SkebDownloader
from MediaDownloader.LinkSearch.Skeb.SkebSaveDirectoryPath import SkebSaveDirectoryPath
from MediaDownloader.LinkSearch.Skeb.SkebSession import SkebSession
from MediaDownloader.LinkSearch.Skeb.SkebSourceList import SkebSourceList
from MediaDownloader.LinkSearch.Skeb.SkebURL import SkebURL
from MediaDownloader.LinkSearch.URL import URL
from MediaDownloader.LinkSearch.Username import Username

logger = getLogger(__name__)
logger.setLevel(INFO)


@dataclass(frozen=True)
class SkebFetcher(FetcherBase):
    """skeb作品を取得するクラス
    """
    session: SkebSession  # skebで使用するセッション
    base_path: Path   # 保存ディレクトリベースパス

    def __init__(self, username: Username, password: Password, base_path: Path) -> None:
        super().__init__()

        if not isinstance(username, Username):
            raise TypeError("username is not Username.")
        if not isinstance(password, Password):
            raise TypeError("password is not Password.")
        if not isinstance(base_path, Path):
            raise TypeError("base_path is not Path.")

        object.__setattr__(self, "session", SkebSession.create(username, password))
        object.__setattr__(self, "base_path", base_path)

    def is_target_url(self, url: URL) -> bool:
        """担当URLかどうか判定する

        FetcherBaseオーバーライド

        Args:
            url (URL): 処理対象url

        Returns:
            bool: 担当urlだった場合True, そうでない場合False
        """
        return SkebURL.is_valid(url.non_query_url)

    def fetch(self, url: URL) -> None:
        """担当処理：skeb作品を取得する

        FetcherBaseオーバーライド

        Args:
            url (URL): 処理対象url
        """
        skeb_url = SkebURL.create(url)
        source_list = SkebSourceList.create(skeb_url, self.session)
        save_directory_path = SkebSaveDirectoryPath.create(skeb_url, self.base_path)
        downloader = SkebDownloader(skeb_url, source_list, save_directory_path, self.session)
        downloader.download()
        dl_file_pathlist = downloader.dl_file_pathlist
        Converter(dl_file_pathlist).convert()


if __name__ == "__main__":
    import configparser
    import logging.config
    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    CONFIG_FILE_NAME = "./config/config.ini"
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE_NAME, encoding="utf8")

    base_path = Path("./MediaDownloader/LinkSearch/")
    username = Username(config["skeb"]["twitter_id"])
    password = Password(config["skeb"]["twitter_password"])
    fetcher = SkebFetcher(username, password, base_path)

    # イラスト（複数）
    work_url = "https://skeb.jp/@matsukitchi12/works/25?query=1"
    # 動画（単体）
    # work_url = "https://skeb.jp/@wata_lemon03/works/7"
    # gif画像（複数）
    # work_url = "https://skeb.jp/@_sa_ya_/works/55"
    work_url = "https://skeb.jp/@gkr16d/works/7"

    fetcher.fetch(work_url)
