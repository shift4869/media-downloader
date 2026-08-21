"""NicoSeigaFetcher のテスト

ニコニコ静画を取得するクラスをテストする
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from media_downloader.link_search.nico_seiga.nico_seiga_fetcher import NicoSeigaFetcher
from media_downloader.link_search.nico_seiga.nico_seiga_url import NicoSeigaURL
from media_downloader.link_search.url import URL


class TestNicoSeigaFetcher(unittest.TestCase):
    def setUp(self):
        self.base_path = Path("./tests")

        self.config = {
            "nico_seiga": {
                "user_session": "dummy_user_session",
                "is_enable": True,
            }
        }

    def _create_fetcher(self):
        """テスト用の NicoSeigaFetcher を生成する"""
        mock_session = self.enterContext(
            patch("media_downloader.link_search.nico_seiga.nico_seiga_fetcher.NicoSeigaSession")
        )

        fetcher = NicoSeigaFetcher(
            self.config,
            self.base_path,
        )

        return fetcher, mock_session

    def test_NicoSeigaFetcher(self):
        """NicoSeigaFetcher の正常系・異常系を確認する"""
        mock_session = self.enterContext(
            patch("media_downloader.link_search.nico_seiga.nico_seiga_fetcher.NicoSeigaSession")
        )

        actual = NicoSeigaFetcher(
            self.config,
            self.base_path,
        )

        self.assertIsInstance(actual, NicoSeigaFetcher)
        self.assertTrue(hasattr(actual, "session"))
        self.assertTrue(hasattr(actual, "base_path"))

        self.assertEqual(
            self.base_path,
            actual.base_path,
        )

        mock_session.assert_called_once_with(self.config)

        with self.assertRaises(TypeError):
            NicoSeigaFetcher(
                "invalid config",
                self.base_path,
            )

        with self.assertRaises(TypeError):
            NicoSeigaFetcher(
                self.config,
                "invalid base path",
            )

    def test_is_target_url(self):
        """is_target_url の正常系・異常系を確認する"""
        fetcher, _ = self._create_fetcher()

        valid_url = URL("https://seiga.nicovideo.jp/seiga/im11111111?query=1")

        actual = fetcher.is_target_url(valid_url)

        self.assertTrue(actual)

        invalid_url = URL("https://invalid.url/seiga/im11111111?query=1")

        actual = fetcher.is_target_url(invalid_url)

        self.assertFalse(actual)

    def test_fetch(self):
        """fetch の正常系・異常系を確認する"""
        fetcher, _ = self._create_fetcher()

        mock_downloader = self.enterContext(
            patch("media_downloader.link_search.nico_seiga.nico_seiga_fetcher.NicoSeigaDownloader")
        )

        illust_url = "https://seiga.nicovideo.jp/seiga/im11111111?query=1"
        url = URL(illust_url)

        nicoseiga_url = NicoSeigaURL.create(url)

        actual = fetcher.fetch(url)

        self.assertIsNone(actual)

        mock_downloader.assert_called_once_with(
            nicoseiga_url,
            self.base_path,
            fetcher.session,
        )

        mock_downloader.return_value.download.assert_called_once_with()


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]

    unittest.main(warnings="ignore")
