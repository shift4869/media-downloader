"""URL のテスト

URLを表すクラスをテストする
"""

import sys
import unittest
import urllib.parse

from media_downloader.link_search.url import URL


class TestURL(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_URL(self):
        # 正常系
        # クエリなし
        url_str = "https://www.pixiv.net/artworks/86704541"
        url = URL(url_str)
        self.assertEqual(url_str, url.non_query_url)
        self.assertEqual(url_str, url.original_url)

        # クエリ付き
        url_str = "https://www.pixiv.net/artworks/86704541?some_query=1"
        non_query_url = urllib.parse.urlunparse(urllib.parse.urlparse(str(url_str))._replace(query=None))
        url = URL(url_str)
        self.assertEqual(non_query_url, url.non_query_url)
        self.assertEqual(url_str, url.original_url)

        # URLオブジェクトから再生成
        url_another = URL(url)
        self.assertEqual(url, url_another)

        # 異常系
        # 不正なURLアドレス
        with self.assertRaises(ValueError):
            url_str = "https://不正なURLアドレス/artworks/86704541"
            url = URL(url_str)

    def test_is_valid(self):
        url_str = "https://www.pixiv.net/artworks/86704541"
        self.assertEqual(True, URL.is_valid(url_str))

        url_str = "https://不正なURLアドレス/artworks/86704541"
        self.assertEqual(False, URL.is_valid(url_str))


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
