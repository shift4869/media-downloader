"""NicoSeigaDownloader のテスト

ニコニコ静画作品をDLするクラスをテストする
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from media_downloader.link_search.nico_seiga.authorid import Authorid
from media_downloader.link_search.nico_seiga.authorname import Authorname
from media_downloader.link_search.nico_seiga.illustname import Illustname
from media_downloader.link_search.nico_seiga.nico_seiga_downloader import DownloadResult, NicoSeigaDownloader
from media_downloader.link_search.nico_seiga.nico_seiga_info import NicoSeigaInfo
from media_downloader.link_search.nico_seiga.nico_seiga_save_directory_path import NicoSeigaSaveDirectoryPath
from media_downloader.link_search.nico_seiga.nico_seiga_session import NicoSeigaSession
from media_downloader.link_search.nico_seiga.nico_seiga_url import NicoSeigaURL


class TestNicoSeigaDownloader(unittest.TestCase):
    def setUp(self):
        self.config = {
            "nico_seiga": {
                "user_session": "dummy_user_session",
                "is_enable": True,
            }
        }

    def _create_session(self):
        """テスト用の NicoSeigaSession を生成する"""
        mock_session_class = self.enterContext(
            patch("media_downloader.link_search.nico_seiga.nico_seiga_downloader.NicoSeigaSession")
        )

        session = mock_session_class.return_value

        return session, mock_session_class

    def test_NicoSeigaDownloader(self):
        """NicoSeigaDownloader の正常系・異常系を確認する"""
        nicoseiga_url = NicoSeigaURL.create("https://seiga.nicovideo.jp/seiga/im11111111")
        base_path = Path("./tests")

        session = MagicMock(spec=NicoSeigaSession)

        downloader = NicoSeigaDownloader(
            nicoseiga_url,
            base_path,
            session,
        )

        self.assertEqual(
            nicoseiga_url,
            downloader.nicoseiga_url,
        )
        self.assertEqual(
            base_path,
            downloader.base_path,
        )
        self.assertEqual(
            session,
            downloader.session,
        )

        with self.assertRaises(TypeError):
            NicoSeigaDownloader(
                "invalid args",
                base_path,
                session,
            )

        with self.assertRaises(TypeError):
            NicoSeigaDownloader(
                nicoseiga_url,
                "invalid args",
                session,
            )

        with self.assertRaises(TypeError):
            NicoSeigaDownloader(
                nicoseiga_url,
                base_path,
                "invalid args",
            )

    def test_is_valid(self):
        """_is_valid の正常系・異常系を確認する"""
        nicoseiga_url = NicoSeigaURL.create("https://seiga.nicovideo.jp/seiga/im11111111")
        base_path = Path("./tests")
        session = MagicMock(spec=NicoSeigaSession)

        downloader = NicoSeigaDownloader(
            nicoseiga_url,
            base_path,
            session,
        )

        self.assertTrue(downloader._is_valid())

        object.__setattr__(
            downloader,
            "nicoseiga_url",
            "invalid args",
        )

        with self.assertRaises(TypeError):
            downloader._is_valid()

        object.__setattr__(
            downloader,
            "nicoseiga_url",
            nicoseiga_url,
        )

        object.__setattr__(
            downloader,
            "base_path",
            "invalid args",
        )

        with self.assertRaises(TypeError):
            downloader._is_valid()

        object.__setattr__(
            downloader,
            "base_path",
            base_path,
        )

        object.__setattr__(
            downloader,
            "session",
            "invalid args",
        )

        with self.assertRaises(TypeError):
            downloader._is_valid()

    def test_download(self):
        """download の正常系・スキップ系を確認する"""
        nicoseiga_url = NicoSeigaURL.create("https://seiga.nicovideo.jp/seiga/im11111111")

        author_id = Authorid(12345678)
        illust_id = nicoseiga_url.illust_id
        illust_name = Illustname("作品名1")
        author_name = Authorname("作成者1")

        illust_info = NicoSeigaInfo(
            illust_id,
            illust_name,
            author_id,
            author_name,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)

            save_directory_path = NicoSeigaSaveDirectoryPath.create(
                illust_info,
                base_path,
            )

            session = MagicMock(spec=NicoSeigaSession)

            session.get_author_id.return_value = author_id
            session.get_illust_title.return_value = illust_name
            session.get_author_name.return_value = author_name
            session.get_source_url.return_value = MagicMock()
            session.get_illust_binary.return_value = b"\x89\x50\x4e\x47\x0d\x0a\x1a\x0a"

            logger_info = self.enterContext(
                patch("media_downloader.link_search.nico_seiga.nico_seiga_downloader.logger.info")
            )

            downloader = NicoSeigaDownloader(
                nicoseiga_url,
                base_path,
                session,
            )

            # 初回DL
            actual = downloader.download()

            self.assertEqual(
                DownloadResult.SUCCESS,
                actual,
            )

            session.get_author_id.assert_called_once_with(illust_id)
            session.get_illust_title.assert_called_once_with(illust_id)
            session.get_author_name.assert_called_once_with(author_id)
            session.get_source_url.assert_called_once_with(illust_id)
            session.get_illust_binary.assert_called_once()

            sd_path = save_directory_path.path

            downloaded_files = list(sd_path.parent.glob("*"))

            self.assertEqual(
                1,
                len(downloaded_files),
            )

            self.assertEqual(
                ".png",
                downloaded_files[0].suffix,
            )

            self.assertIn(
                str(illust_id.id),
                downloaded_files[0].name,
            )

            # 2回目DL
            session.reset_mock()

            actual = downloader.download()

            self.assertEqual(
                DownloadResult.PASSED,
                actual,
            )

            # 既存ファイルなので再取得しない
            session.get_author_id.assert_called_once_with(illust_id)
            session.get_illust_title.assert_called_once_with(illust_id)
            session.get_author_name.assert_called_once_with(author_id)

            session.get_source_url.assert_not_called()
            session.get_illust_binary.assert_not_called()

            logger_info.assert_called()

    def test_DownloadResult(self):
        """DownloadResult の値を確認する"""
        expected = [
            "SUCCESS",
            "PASSED",
        ]

        actual = [result.name for result in DownloadResult]

        self.assertEqual(
            expected,
            actual,
        )


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]

    unittest.main(warnings="ignore")
