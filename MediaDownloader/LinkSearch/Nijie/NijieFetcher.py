# coding: utf-8
import re
import urllib.parse
from dataclasses import dataclass
from logging import INFO, getLogger
from pathlib import Path

import requests
import requests.cookies

from MediaDownloader.LinkSearch.FetcherBase import FetcherBase
from MediaDownloader.LinkSearch.Nijie.NijieCookie import NijieCookie
from MediaDownloader.LinkSearch.Nijie.NijieDownloader import NijieDownloader
from MediaDownloader.LinkSearch.Nijie.NijieURL import NijieURL
from MediaDownloader.LinkSearch.Password import Password
from MediaDownloader.LinkSearch.URL import URL
from MediaDownloader.LinkSearch.Username import Username

logger = getLogger(__name__)
logger.setLevel(INFO)


@dataclass(frozen=True)
class NijieFetcher(FetcherBase):
    """nijie作品を取得するクラス
    """
    cookies: NijieCookie  # nijieで使用するクッキー
    base_path: Path       # 保存ディレクトリベースパス

    # 接続時に使用するヘッダー
    HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36"}
    # ログイン情報を保持するクッキーファイル置き場
    NIJIE_COOKIE_PATH = "./config/nijie_cookie.ini"

    def __init__(self, username: Username, password: Password, base_path: Path):
        """初期化処理

        バリデーションとクッキー取得

        Args:
            username (Username): nijieログイン用ユーザーID
            password (Password):  nijieログイン用パスワード
            base_path (Path): 保存ディレクトリベースパス
        """
        super().__init__()

        if not isinstance(username, Username):
            raise TypeError("username is not Username.")
        if not isinstance(password, Password):
            raise TypeError("password is not Password.")
        if not isinstance(base_path, Path):
            raise TypeError("base_path is not Path.")

        object.__setattr__(self, "cookies", self.login(username, password))
        object.__setattr__(self, "base_path", base_path)

    def login(self, username: Username, password: Password) -> NijieCookie:
        """nijieページにログインし、ログイン情報を保持したクッキーを返す

        Args:
            username (Username): nijieユーザーID(登録したemailアドレス)
            password (Password): nijieユーザーIDのパスワード

        Returns:
            cookies (NijieCookie): ログイン情報を保持したクッキー
        """
        ncp = Path(self.NIJIE_COOKIE_PATH)

        res = None
        cookies = requests.cookies.RequestsCookieJar()
        if ncp.is_file():
            # クッキーが既に存在している場合
            # クッキーを読み込む
            with ncp.open(mode="r") as fin:
                for line in fin:
                    if line == "":
                        break

                    nc = {}
                    elements = re.split("[,\n]", line)
                    for element in elements:
                        element = element.strip().replace('"', "")  # 左右の空白とダブルクォートを除去
                        if element == "":
                            break

                        key, val = element.split("=")  # =で分割
                        nc[key] = val

                    cookies.set(nc["name"], nc["value"], expires=nc["expires"], path=nc["path"], domain=nc["domain"])

            # クッキーが有効かチェック
            try:
                res = NijieCookie(cookies, self.HEADERS)
                return res
            except Exception:
                pass

        # クッキーが存在していない場合、または有効なクッキーではなかった場合
        # 年齢確認で「はい」を選択したあとのURLにアクセス
        response = requests.get("https://nijie.info/age_jump.php?url=", headers=self.HEADERS)
        response.raise_for_status()

        # 認証用URLクエリを取得する
        qs = urllib.parse.urlparse(response.url).query
        qd = urllib.parse.parse_qs(qs)
        url = qd["url"][0]

        # ログイン時に必要な情報
        payload = {
            "email": username.name,
            "password": password.password,
            "save": "on",
            "ticket": "",
            "url": url
        }

        # ログインする
        login_url = "https://nijie.info/login_int.php"
        response = requests.post(login_url, data=payload)
        response.raise_for_status()

        # 以降はクッキーに認証情報が含まれているため、これを用いて各ページをGETする
        cookies = response.cookies

        # クッキーが有効かチェック
        res = NijieCookie(cookies, self.HEADERS)

        # クッキー解析用
        def CookieToString(c):
            return f'name="{c.name}", value="{c.value}", expires={c.expires}, path="{c.path}", domain="{c.domain}"'

        # クッキー情報をファイルに保存する
        with ncp.open(mode="w") as fout:
            for c in cookies:
                fout.write(CookieToString(c) + "\n")

        return res

    def is_target_url(self, url: URL) -> bool:
        """担当URLかどうか判定する

        FetcherBaseオーバーライド

        Args:
            url (URL): 処理対象url

        Returns:
            bool: 担当urlだった場合True, そうでない場合False
        """
        return NijieURL.is_valid(url.original_url)

    def fetch(self, url: URL) -> None:
        """担当処理：nijie作品を取得する

        FetcherBaseオーバーライド

        Args:
            url (URL): 処理対象url
        """
        novel_url = NijieURL.create(url)
        NijieDownloader(novel_url, self.base_path, self.cookies).download()


if __name__ == "__main__":
    import configparser
    import logging.config
    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    CONFIG_FILE_NAME = "./config/config.ini"
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE_NAME, encoding="utf8")

    base_path = Path("./MediaDownloader/LinkSearch/")
    if config["nijie"].getboolean("is_nijie_trace"):
        fetcher = NijieFetcher(Username(config["nijie"]["email"]), Password(config["nijie"]["password"]), base_path)

        illust_id = 251267  # 一枚絵
        # illust_id = 251197  # 漫画
        # illust_id = 414793  # うごイラ一枚
        # illust_id = 409587  # うごイラ複数

        illust_url = f"https://nijie.info/view_popup.php?id={illust_id}"
        fetcher.fetch(illust_url)
