"""Worktitle のテスト

作者名を表すクラスをテストする
"""

import re
import sys
import unittest

import emoji

from media_downloader.link_search.pixiv.worktitle import Worktitle


class TestWorktitle(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def _sanitize(self, _original_title: str) -> str:
        regex = re.compile(r'[\\/:*?"<>|]')
        trimed_title = regex.sub("", _original_title)
        non_emoji_title = emoji.replace_emoji(trimed_title, "")
        return non_emoji_title

    def test_Worktitle(self):
        # 正常系
        # 通常
        title = "タイトル1"
        work_title = Worktitle(title)
        self.assertEqual(title, work_title.title)

        # 記号含み
        title = "タイトル2?****//"
        work_title = Worktitle(title)
        expect = self._sanitize(title)
        self.assertEqual(expect, work_title.title)

        # 絵文字含み
        title = "タイトル3😀"
        work_title = Worktitle(title)
        expect = self._sanitize(title)
        self.assertEqual(expect, work_title.title)

        # 異常系
        # 文字列でない
        with self.assertRaises(TypeError):
            work_title = Worktitle(-1)

        # 空文字列
        with self.assertRaises(ValueError):
            work_title = Worktitle("")

    def test_id(self):
        title = "タイトル1"
        work_title = Worktitle(title)
        self.assertEqual(title, work_title.title)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
