"""LinkSearcher のテスト

外部リンク探索クラスをテストする
"""

import configparser
import sys
import unittest
from contextlib import ExitStack
from logging import WARNING, getLogger

from mock import MagicMock, patch

from media_downloader.link_search.link_searcher import LinkSearcher

logger = getLogger("media_downloader.link_search.link_searcher")
logger.setLevel(WARNING)


class TestLinkSearcher(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_LinkSearcher(self):
        lsc = LinkSearcher()
        self.assertEqual([], lsc.fetcher_list)

    def test_register(self):
        lsc = LinkSearcher()

        # 正常系
        fake_fetcher = MagicMock()
        fake_fetcher.is_target_url = MagicMock()
        fake_fetcher.fetch = MagicMock()
        lsc.register(fake_fetcher)
        self.assertEqual(1, len(lsc.fetcher_list))
        self.assertEqual(fake_fetcher, lsc.fetcher_list[0])

        # 異常系
        fake_fetcher = MagicMock()
        del fake_fetcher.is_target_url
        del fake_fetcher.fetch
        with self.assertRaises(TypeError):
            lsc.register(fake_fetcher)

    def test_fetch(self):
        with ExitStack() as stack:
            mock_logger = stack.enter_context(patch.object(logger, "info"))
            lsc = LinkSearcher()

            # 正常系
            url_str = "https://www.pixiv.net/artworks/86704541"
            fake_fetcher = MagicMock()
            fake_fetcher.is_target_url = lambda url: url.non_query_url == url_str
            fake_fetcher.fetch = MagicMock()
            lsc.register(fake_fetcher)

            actual = lsc.fetch(url_str)
            self.assertEqual(None, actual)
            fake_fetcher.fetch.assert_called_once_with(url_str)
            fake_fetcher.fetch.reset_mock()

            # 異常系
            with self.assertRaises(ValueError):
                invalid_url_str = "https://invalid/artworks/86704541"
                actual = lsc.fetch(invalid_url_str)

    def test_can_fetch(self):
        lsc = LinkSearcher()

        # 正常系
        url_str = "https://www.pixiv.net/artworks/86704541"
        fake_fetcher = MagicMock()
        fake_fetcher.is_target_url = lambda url: url.non_query_url == url_str
        fake_fetcher.fetch = MagicMock()
        lsc.register(fake_fetcher)

        actual = lsc.can_fetch(url_str)
        self.assertEqual(True, actual)

        # 異常系
        invalid_url_str = "https://invalid/artworks/86704541"
        actual = lsc.can_fetch(invalid_url_str)
        self.assertEqual(False, actual)

    def test_create(self):
        with ExitStack() as stack:
            mock_notification = stack.enter_context(patch("media_downloader.link_search.link_searcher.notification"))
            mock_pixiv_fetcher = stack.enter_context(patch("media_downloader.link_search.link_searcher.PixivFetcher"))
            mock_pixiv_novel_fetcher = stack.enter_context(
                patch("media_downloader.link_search.link_searcher.PixivNovelFetcher")
            )
            mock_nijie_fetcher = stack.enter_context(patch("media_downloader.link_search.link_searcher.NijieFetcher"))
            mock_nico_seiga_fetcher = stack.enter_context(
                patch("media_downloader.link_search.link_searcher.NicoSeigaFetcher")
            )
            # mock_skeb_fetcher = stack.enter_context(patch("media_downloader.link_search.link_searcher.SkebFetcher"))

            # 正常系
            CONFIG_FILE_NAME = "./config/config.ini"
            config = configparser.ConfigParser()
            if not config.read(CONFIG_FILE_NAME, encoding="utf8"):
                raise IOError

            lsc = LinkSearcher.create(config)

            REGISTER_NUM = 4
            self.assertEqual(REGISTER_NUM, len(lsc.fetcher_list))


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
