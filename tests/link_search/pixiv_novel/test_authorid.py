"""Authorid のテスト

作者IDを表すクラスをテストする
"""

import sys
import unittest

from media_downloader.link_search.pixiv_novel.authorid import Authorid


class TestAuthorid(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_Authorid(self):
        # 正常系
        id_num = 12345678
        authorid = Authorid(id_num)

        # 異常系
        # 0は不正なIDとする
        with self.assertRaises(ValueError):
            authorid = Authorid(0)

        # マイナスのID
        with self.assertRaises(ValueError):
            authorid = Authorid(-1)

        # 数値でない
        with self.assertRaises(TypeError):
            authorid = Authorid("invalid id")

        # 数値でない
        with self.assertRaises(TypeError):
            authorid = Authorid("")

    def test_id(self):
        id_num = 12345678
        authorid = Authorid(id_num)
        self.assertEqual(id_num, authorid.id)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
