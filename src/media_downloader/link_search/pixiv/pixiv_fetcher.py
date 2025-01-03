import logging
from dataclasses import dataclass
from logging import INFO, getLogger
from pathlib import Path

from pixivpy3 import AppPixivAPI

from media_downloader.link_search.fetcher_base import FetcherBase
from media_downloader.link_search.password import Password
from media_downloader.link_search.pixiv.pixiv_save_directory_path import PixivSaveDirectoryPath
from media_downloader.link_search.pixiv.pixiv_source_list import PixivSourceList
from media_downloader.link_search.pixiv.pixiv_work_downloader import PixivWorkDownloader
from media_downloader.link_search.pixiv.pixiv_work_url import PixivWorkURL
from media_downloader.link_search.url import URL
from media_downloader.link_search.username import Username
from media_downloader.util import CustomLogger

logging.setLoggerClass(CustomLogger)
logger = getLogger(__name__)
logger.setLevel(INFO)


@dataclass(frozen=True)
class PixivFetcher(FetcherBase):
    """pixiv作品を取得するクラス"""

    aapi: AppPixivAPI  # 非公式pixivAPI操作インスタンス
    base_path: Path  # 保存ディレクトリベースパス

    # refresh_tokenファイルパス
    REFRESH_TOKEN_PATH = "./config/refresh_token.ini"

    def __init__(self, username: Username, password: Password, base_path: Path) -> None:
        """初期化処理

        バリデーションと非公式pixivAPIインスタンス取得

        Args:
            username (Username): pixivログイン用ユーザーID
            password (Password):  pixivログイン用パスワード
            base_path (Path): 保存ディレクトリベースパス
        """
        super().__init__()

        if not isinstance(username, Username):
            raise TypeError("username is not Username.")
        if not isinstance(password, Password):
            raise TypeError("password is not Password.")
        if not isinstance(base_path, Path):
            raise TypeError("base_path is not Path.")

        object.__setattr__(self, "aapi", self.login(username, password))
        object.__setattr__(self, "base_path", base_path)

    def login(self, username: Username, password: Password) -> AppPixivAPI:
        """pixivログインして非公式pixivAPIインスタンスを取得する

        Args:
            username (Username): pixivログイン用ユーザーID
            password (Password):  pixivログイン用パスワード

        Returns:
            aapi: AppPixivAPI非公式pixivAPI操作インスタンス
        """
        aapi = AppPixivAPI()

        # 前回ログインからのrefresh_tokenが残っているか調べる
        rt_path = Path(self.REFRESH_TOKEN_PATH)
        if rt_path.is_file():
            refresh_token = ""
            with rt_path.open(mode="r") as fin:
                refresh_token = str(fin.read())
            try:
                # 非公式pixivAPI認証
                aapi.auth(refresh_token=refresh_token)
                if aapi.access_token is not None:
                    return aapi
            except Exception:
                pass

        # refresh_tokenが存在していない場合、または有効なトークンではなかった場合
        # api.login(username, password)
        # aapi.login(username, password)
        # auth_success = (api.access_token is not None) and (aapi.access_token is not None)
        # 2021/05/20 現在PixivPyで新規ログインができない
        # https://gist.github.com/ZipFile/c9ebedb224406f4f11845ab700124362
        # https://gist.github.com/upbit/6edda27cb1644e94183291109b8a5fde
        logger.info(f"not found {self.REFRESH_TOKEN_PATH}")
        logger.info("please access to make refresh_token.ini for below way:")
        logger.info("https://gist.github.com/ZipFile/c9ebedb224406f4f11845ab700124362")
        logger.info(" or ")
        logger.info("https://gist.github.com/upbit/6edda27cb1644e94183291109b8a5fde")
        logger.info("process abort")
        raise ValueError("pixiv auth failed.")

    def is_target_url(self, url: URL) -> bool:
        """担当URLかどうか判定する

        FetcherBaseオーバーライド

        Args:
            url (URL): 処理対象url

        Returns:
            bool: 担当urlだった場合True, そうでない場合False
        """
        return PixivWorkURL.is_valid(url.non_query_url)

    def fetch(self, url: URL) -> None:
        """担当処理：pixiv作品を取得する

        FetcherBaseオーバーライド

        Args:
            url (URL): 処理対象url
        """
        pixiv_url = PixivWorkURL.create(url)
        source_list = PixivSourceList.create(self.aapi, pixiv_url)
        save_directory_path = PixivSaveDirectoryPath.create(self.aapi, pixiv_url, self.base_path)
        PixivWorkDownloader(self.aapi, source_list, save_directory_path).download()


if __name__ == "__main__":
    import configparser
    import logging.config

    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    CONFIG_FILE_NAME = "./config/config.ini"
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE_NAME, encoding="utf8")

    base_path = Path("./MediaDownloader/LinkSearch/")
    if config["pixiv"].getboolean("is_pixiv_trace"):
        pa_cont = PixivFetcher(Username(config["pixiv"]["username"]), Password(config["pixiv"]["password"]), base_path)
        work_url = "https://www.pixiv.net/artworks/86704541"
        work_url = "https://www.pixiv.net/artworks/113310737"
        pa_cont.fetch(work_url)
