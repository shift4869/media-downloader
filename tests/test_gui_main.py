import logging
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import orjson
from PySide6.QtWidgets import QApplication, QCheckBox, QLineEdit, QPushButton, QTextEdit

from media_downloader.gui_main import GuiMain
from media_downloader.util import Result

CONFIG_FILE_NAME = "./config/config.json"


class TestGuiMain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Qt アプリケーションを一度だけ生成する"""
        cls.app = QApplication.instance()
        if cls.app is None:
            cls.app = QApplication([])

        # テスト中の GUI ログを抑制する
        cls.logger = logging.getLogger("media_downloader.gui_main")
        cls.original_log_level = cls.logger.level
        cls.logger.setLevel(logging.WARNING)

    @classmethod
    def tearDownClass(cls):
        """ログレベルを元に戻す"""
        cls.logger.setLevel(cls.original_log_level)

    def setUp(self):
        """テスト用設定を読み込む"""
        self.config = orjson.loads(Path(CONFIG_FILE_NAME).read_bytes())

    def _create_window(self):
        """テスト用 GuiMain を生成する"""
        return GuiMain()

    def test_init(self):
        """GuiMain 初期化の正常系・異常系を確認する"""

        # 正常系
        window = self._create_window()

        self.assertIsNotNone(window)
        self.assertIsInstance(window.config, dict)

        self.assertIn("pixiv", window.config)
        self.assertIn("nijie", window.config)
        self.assertIn("nico_seiga", window.config)
        self.assertIn("save_base_path", window.config)

        self.assertIsInstance(window.save_base_path, Path)

        self.assertTrue(hasattr(window, "textbox1"))
        self.assertTrue(hasattr(window, "textbox3"))
        self.assertTrue(hasattr(window, "checkbox_list"))
        self.assertTrue(hasattr(window, "textarea"))

        expected = Path(self.config["save_base_path"])
        self.assertEqual(expected, window.save_base_path)
        self.assertEqual(expected, window.config["save_base_path"])

        # 異常系: 設定ファイルが存在しない
        mock_exists = self.enterContext(
            patch(
                "media_downloader.gui_main.Path.exists",
                return_value=False,
            )
        )

        with self.assertRaises(IOError):
            GuiMain()

        mock_exists.assert_called_once()

        # 異常系: 設定ファイルが空
        mock_exists.return_value = True

        mock_loads = self.enterContext(
            patch(
                "media_downloader.gui_main.orjson.loads",
                return_value={},
            )
        )

        with self.assertRaises(IOError):
            GuiMain()

        mock_loads.assert_called_once()

        # 異常系: save_base_path が不正
        invalid_config = self.config.copy()
        invalid_config["save_base_path"] = None

        mock_loads.reset_mock()
        mock_loads.return_value = invalid_config

        window = GuiMain()

        expected = Path(
            __import__(
                "media_downloader.gui_main",
                fromlist=["__file__"],
            ).__file__
        ).parent

        self.assertEqual(expected, window.save_base_path)
        self.assertEqual(expected, window.config["save_base_path"])

    def test_link_search(self):
        """link_search の正常系・異常系を確認する"""

        mock_create = self.enterContext(patch("media_downloader.gui_main.LinkSearcher.create"))

        # 異常系: レイアウト未初期化
        window = GuiMain.__new__(GuiMain)

        actual = window.link_search()

        self.assertEqual(Result.failed, actual)
        mock_create.assert_not_called()

        # 異常系: URL が空
        window = self._create_window()
        window.textbox1.setText("")

        mock_create.reset_mock()
        mock_create.side_effect = None
        mock_create.return_value = MagicMock()

        actual = window.link_search()

        self.assertEqual(Result.failed, actual)
        mock_create.assert_not_called()

        # 正常系: fetch 成功
        window = self._create_window()
        work_url = "https://www.pixiv.net/artworks/86704541"
        window.textbox1.setText(work_url)

        mock_create.reset_mock()
        mock_create.side_effect = None

        mock_link_searcher = MagicMock()
        mock_create.return_value = mock_link_searcher

        actual = window.link_search()

        self.assertEqual(Result.success, actual)
        mock_create.assert_called_once_with(window.config)
        mock_link_searcher.fetch.assert_called_once_with(work_url)
        self.assertTrue(hasattr(window, "link_searcher"))

        # 異常系: fetch で例外が発生しても success
        window = self._create_window()
        window.textbox1.setText(work_url)

        mock_create.reset_mock()
        mock_create.side_effect = None

        mock_link_searcher = MagicMock()
        mock_link_searcher.fetch.side_effect = ValueError("invalid URL")
        mock_create.return_value = mock_link_searcher

        actual = window.link_search()

        self.assertEqual(Result.success, actual)
        mock_create.assert_called_once_with(window.config)
        mock_link_searcher.fetch.assert_called_once_with(work_url)

        # 正常系: チェック状態が変わらない場合は再利用
        window = self._create_window()
        window.textbox1.setText(work_url)

        mock_create.reset_mock()
        mock_create.side_effect = None

        mock_link_searcher = MagicMock()
        mock_create.return_value = mock_link_searcher

        actual = window.link_search()
        self.assertEqual(Result.success, actual)

        actual = window.link_search()
        self.assertEqual(Result.success, actual)

        self.assertEqual(1, mock_create.call_count)
        self.assertEqual(2, mock_link_searcher.fetch.call_count)

        # 正常系: pixiv のチェック状態が変化した場合は再生成
        window = self._create_window()
        window.textbox1.setText(work_url)

        mock_create.reset_mock()
        mock_create.side_effect = None

        mock_link_searcher1 = MagicMock()
        mock_link_searcher2 = MagicMock()

        mock_create.side_effect = [
            mock_link_searcher1,
            mock_link_searcher2,
        ]

        actual = window.link_search()
        self.assertEqual(Result.success, actual)

        window.checkbox_list[0].setChecked(not window.checkbox_list[0].isChecked())

        actual = window.link_search()
        self.assertEqual(Result.success, actual)

        self.assertEqual(2, mock_create.call_count)

        mock_link_searcher1.fetch.assert_called_once_with(work_url)
        mock_link_searcher2.fetch.assert_called_once_with(work_url)

        # 正常系: LinkSearcher 初期化時に設定を更新
        window = self._create_window()
        window.textbox1.setText(work_url)

        window.checkbox_list[0].setChecked(True)
        window.checkbox_list[1].setChecked(False)
        window.checkbox_list[2].setChecked(True)

        mock_create.reset_mock()
        mock_create.side_effect = None

        mock_link_searcher = MagicMock()
        mock_create.return_value = mock_link_searcher

        actual = window.link_search()

        self.assertEqual(Result.success, actual)

        self.assertTrue(window.config["pixiv"]["is_enable"])
        self.assertFalse(window.config["nijie"]["is_enable"])
        self.assertTrue(window.config["nico_seiga"]["is_enable"])
        self.assertEqual(
            window.save_base_path,
            window.config["save_base_path"],
        )

    def test_directory_browse(self):
        """directory_browse の正常系・異常系を確認する"""

        mock_dialog = self.enterContext(patch("media_downloader.gui_main.QFileDialog"))

        # 異常系: レイアウト未初期化
        window = GuiMain.__new__(GuiMain)

        actual = window.directory_browse()

        self.assertEqual(Result.failed, actual)
        mock_dialog.assert_not_called()

        # 正常系: フォルダ選択成功
        window = self._create_window()

        selected_path = str(Path(window.save_base_path).resolve())

        mock_dialog.return_value.getExistingDirectory.return_value = selected_path

        actual = window.directory_browse()

        self.assertEqual(Result.success, actual)
        self.assertEqual(
            selected_path,
            window.textbox3.text(),
        )
        self.assertEqual(
            Path(selected_path),
            window.save_base_path,
        )
        self.assertEqual(
            Path(selected_path),
            window.config["save_base_path"],
        )

        mock_dialog.return_value.getExistingDirectory.assert_called_once()

        # 異常系: 存在しないディレクトリ
        window = self._create_window()

        invalid_path = Path(window.save_base_path) / "not_exist"

        mock_dialog.reset_mock()
        mock_dialog.return_value.getExistingDirectory.return_value = str(invalid_path)

        actual = window.directory_browse()

        self.assertEqual(Result.failed, actual)
        mock_dialog.return_value.getExistingDirectory.assert_called_once()

        # 異常系: キャンセル
        window = self._create_window()

        original_save_base_path = window.save_base_path
        original_text = window.textbox3.text()

        mock_dialog.reset_mock()
        mock_dialog.return_value.getExistingDirectory.return_value = ""

        actual = window.directory_browse()

        self.assertEqual(Result.failed, actual)
        self.assertEqual(
            original_save_base_path,
            window.save_base_path,
        )
        self.assertEqual(
            original_text,
            window.textbox3.text(),
        )

        mock_dialog.return_value.getExistingDirectory.assert_called_once()

    def test_open_explorer(self):
        """open_explorer の正常系・異常系を確認する"""

        mock_popen = self.enterContext(patch("media_downloader.gui_main.subprocess.Popen"))

        # 異常系: レイアウト未初期化
        window = GuiMain.__new__(GuiMain)

        actual = window.open_explorer()

        self.assertEqual(Result.failed, actual)
        mock_popen.assert_not_called()

        # 正常系
        window = self._create_window()

        target_path = Path(window.textbox3.text())
        self.assertTrue(target_path.exists())

        actual = window.open_explorer()

        self.assertEqual(Result.success, actual)
        mock_popen.assert_called_once_with(["explorer", str(target_path)])

        # 異常系: 存在しないパス
        window = self._create_window()

        invalid_path = Path(window.save_base_path) / "not_exist"
        window.textbox3.setText(str(invalid_path))

        mock_popen.reset_mock()

        actual = window.open_explorer()

        self.assertEqual(Result.failed, actual)
        mock_popen.assert_not_called()

    def test_create_layout(self):
        """create_layout による GUI レイアウト生成を確認する"""

        window = self._create_window()

        # QDialog にレイアウトが設定されている
        self.assertIsNotNone(window.layout())

        # 作品ページ URL
        self.assertIsInstance(
            window.textbox1,
            QLineEdit,
        )

        # 保存先パス
        self.assertIsInstance(
            window.textbox3,
            QLineEdit,
        )
        self.assertEqual(
            str(window.save_base_path),
            window.textbox3.text(),
        )

        # チェックボックス
        self.assertEqual(
            3,
            len(window.checkbox_list),
        )

        for checkbox in window.checkbox_list:
            self.assertIsInstance(
                checkbox,
                QCheckBox,
            )

        self.assertEqual(
            ["pixiv", "nijie", "nico_seiga"],
            [checkbox.text() for checkbox in window.checkbox_list],
        )

        expected_checkbox_state = [
            window.config["pixiv"]["is_enable"],
            window.config["nijie"]["is_enable"],
            window.config["nico_seiga"]["is_enable"],
        ]

        actual_checkbox_state = [checkbox.isChecked() for checkbox in window.checkbox_list]

        self.assertEqual(
            expected_checkbox_state,
            actual_checkbox_state,
        )

        # ログ表示用テキストエリア
        self.assertIsInstance(
            window.textarea,
            QTextEdit,
        )

        # ボタン
        buttons = window.findChildren(QPushButton)

        self.assertEqual(
            3,
            len(buttons),
        )

        button_texts = {button.text() for button in buttons}

        self.assertEqual(
            {"実行", "参照", "開く"},
            button_texts,
        )

        # チェックボックスの状態変更
        checkbox = window.checkbox_list[0]

        original = checkbox.isChecked()
        checkbox.setChecked(not original)

        self.assertNotEqual(
            original,
            checkbox.isChecked(),
        )

        # ウィンドウタイトル
        self.assertIn(
            "MediaDownloader",
            window.windowTitle(),
        )


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]

    unittest.main(warnings="ignore")
