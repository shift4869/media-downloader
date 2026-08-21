"""NicoSeigaSession のテスト

NicoSeigaSessionを表すクラスをテストする
"""

import sys
import unittest
from unittest.mock import MagicMock, patch

import httpx

from media_downloader.link_search.nico_seiga.authorid import Authorid
from media_downloader.link_search.nico_seiga.authorname import Authorname
from media_downloader.link_search.nico_seiga.illustid import Illustid
from media_downloader.link_search.nico_seiga.illustname import Illustname
from media_downloader.link_search.nico_seiga.nico_seiga_session import NicoSeigaSession
from media_downloader.link_search.url import URL


class TestNicoSeigaSession(unittest.TestCase):
    def _get_session(self):
        """テスト用の NicoSeigaSession を生成する"""
        config = {
            "nico_seiga": {
                "user_session": "dummy_user_session",
            }
        }

        session = NicoSeigaSession(config)

        mock_get = self.enterContext(
            patch.object(
                session._session,
                "get",
            )
        )

        def return_get_html(url):
            response = MagicMock()

            image_info_endpoint = "http://seiga.nicovideo.jp/api/illust/info?id="
            username_endpoint = "https://seiga.nicovideo.jp/api/user/info?id="
            source_endpoint = "https://seiga.nicovideo.jp/image/source?id="

            if image_info_endpoint in url:
                response.text = "<image><user_id>1234567</user_id><title>title_1</title></image>"
            elif username_endpoint in url:
                response.text = "<user><nickname>author_name_1</nickname></user>"
            elif source_endpoint in url:
                response.text = (
                    '<div id="content"><div class="illust_view_big" data-src="http://source_url"></div></div>'
                )
            else:
                response.content = b"sample image bytes"

            response.raise_for_status.return_value = None
            return response

        mock_get.side_effect = return_get_html

        return session

    def test_NicoSeigaSession(self):
        """NicoSeigaSession の初期化を確認する"""
        session = self._get_session()

        h_mozilla = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        h_webkit = "AppleWebKit/537.36 (KHTML, like Gecko)"
        h_chrome = "Chrome/88.0.4324.190 Safari/537.36"

        expected_headers = {"User-Agent": f"{h_mozilla} {h_webkit} {h_chrome}"}

        expected_image_info_endpoint = "http://seiga.nicovideo.jp/api/illust/info?id="
        expected_username_endpoint = "https://seiga.nicovideo.jp/api/user/info?id="
        expected_source_endpoint = "https://seiga.nicovideo.jp/image/source?id="

        self.assertIsNotNone(session._session)
        self.assertIsInstance(
            session._session,
            httpx.Client,
        )
        self.assertEqual(
            expected_headers,
            session.HEADERS,
        )
        self.assertEqual(
            expected_image_info_endpoint,
            session.IMAGE_INFO_API_ENDPOINT_BASE,
        )
        self.assertEqual(
            expected_username_endpoint,
            session.USERNAME_API_ENDPOINT_BASE,
        )
        self.assertEqual(
            expected_source_endpoint,
            session.IMAGE_SOUECE_API_ENDPOINT_BASE,
        )

    def test_is_valid(self):
        """_is_valid の正常系・異常系を確認する"""
        session = self._get_session()

        valid_session = MagicMock(spec=httpx.Client)

        object.__setattr__(
            session,
            "_session",
            valid_session,
        )

        actual = session._is_valid()

        self.assertTrue(actual)

        object.__setattr__(
            session,
            "_session",
            None,
        )

        with self.assertRaises(TypeError):
            session._is_valid()

    def test_get_author_id(self):
        """get_author_id の正常系を確認する"""
        session = self._get_session()

        illust_id = Illustid(12345678)

        expected = Authorid(1234567)
        actual = session.get_author_id(illust_id)

        self.assertEqual(
            expected,
            actual,
        )

    def test_get_author_name(self):
        """get_author_name の正常系を確認する"""
        session = self._get_session()

        author_id = Authorid(1234567)

        expected = Authorname("author_name_1")
        actual = session.get_author_name(author_id)

        self.assertEqual(
            expected,
            actual,
        )

    def test_get_illust_title(self):
        """get_illust_title の正常系を確認する"""
        session = self._get_session()

        illust_id = Illustid(12345678)

        expected = Illustname("title_1")
        actual = session.get_illust_title(illust_id)

        self.assertEqual(
            expected,
            actual,
        )

    def test_get_source_url(self):
        """get_source_url の正常系を確認する"""
        session = self._get_session()

        illust_id = Illustid(12345678)

        expected = URL("http://source_url")
        actual = session.get_source_url(illust_id)

        self.assertEqual(
            expected,
            actual,
        )

    def test_get_illust_binary(self):
        """get_illust_binary の正常系を確認する"""
        session = self._get_session()

        source_url = URL("http://source_url")

        expected = b"sample image bytes"
        actual = session.get_illust_binary(source_url)

        self.assertEqual(
            expected,
            actual,
        )


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]

    unittest.main(warnings="ignore")
