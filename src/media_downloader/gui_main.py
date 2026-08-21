import logging
import logging.config
import subprocess
import sys
from logging import INFO, getLogger
from pathlib import Path

import orjson
from PySide6.QtCore import Qt, Slot, qVersion
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QCheckBox, QDialog, QFileDialog, QGridLayout, QGroupBox, QHBoxLayout
from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QTextEdit, QVBoxLayout

from media_downloader.link_search.link_searcher import LinkSearcher
from media_downloader.util import CustomLogger, Result

APP_NAME = "MediaDownloader"
ICON_PATH = "./image/icon.png"

# ログ設定
logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
for name in logging.root.manager.loggerDict:
    # 自分以外のすべてのライブラリのログ出力を抑制
    if "media_downloader" not in name:
        getLogger(name).disabled = True
logging.setLoggerClass(CustomLogger)
logger = getLogger(__name__)
logger.setLevel(INFO)


class GuiMain(QDialog):
    def __init__(self) -> None:
        super().__init__()

        # 対象URL例サンプル
        # target_url_example = {
        #     "pixiv pic/manga": "https://www.pixiv.net/artworks/xxxxxxxx",
        #     "pixiv novel": "https://www.pixiv.net/novel/show.php?id=xxxxxxxx",
        #     "nijie": "http://nijie.info/view_popup.php?id=xxxxxx",
        #     "seiga": "https://seiga.nicovideo.jp/seiga/imxxxxxxx",
        # }

        # configファイルロード
        CONFIG_FILE_NAME = "./config/config.json"
        if not Path(CONFIG_FILE_NAME).exists():
            raise IOError("Config file not found.")
        self.config = orjson.loads(Path(CONFIG_FILE_NAME).read_bytes())
        if not self.config:
            raise IOError("Config file is invalid.")

        # 保存先パス設定
        self.save_base_path = Path(__file__).parent
        try:
            self.save_base_path = Path(self.config["save_base_path"])
        except Exception:
            self.save_base_path = Path(__file__).parent
        self.save_base_path.mkdir(parents=True, exist_ok=True)
        self.config["save_base_path"] = self.save_base_path

        # アイコン設定
        self.setWindowIcon(QIcon(ICON_PATH))

        # ウィンドウタイトル設定
        qv = qVersion()
        self.setWindowTitle(f"{APP_NAME} by pyside {qv}")

        # レイアウト設定
        self.create_layout()

        logger.info("---ここにログが表示されます---", window=self)
        return

    @Slot()
    def link_search(self) -> Result:
        logger.info("GuiMain link_search -> start")

        # 属性の存在チェック
        required_attribute_exist = [
            hasattr(self, "textbox1"),
            hasattr(self, "textbox3"),
            hasattr(self, "checkbox_list"),
        ]
        if not all(required_attribute_exist):
            # レイアウト作成前に呼び出された場合は何もしない
            logger.info("Layout is not initilized.")
            logger.info("GuiMain link_search -> abort")
            return Result.failed

        # 値チェック
        # この時点ではハッシュ等が末尾についていても許容する
        # 空白かどうかだけ確認する
        work_url = self.textbox1.text()
        if not work_url:
            logger.info("Textbox1 is empty.")
            logger.info("GuiMain link_search -> abort")
            return Result.failed

        # 初期化が必要かどうか調べる
        # すでに一度初期化済、かつ、対象のチェックボックスの状況が変わっていない場合
        # 初期化をスキップする
        need_init = True
        if hasattr(self, "link_searcher"):
            # チェックボックスが変更されているか
            checkbox_match = [
                self.config["pixiv"]["is_enable"] == self.checkbox_list[0].isChecked(),
                self.config["nijie"]["is_enable"] == self.checkbox_list[1].isChecked(),
                self.config["nico_seiga"]["is_enable"] == self.checkbox_list[2].isChecked(),
            ]
            if all(checkbox_match):
                need_init = False

            # 保存先パスが変更されているか
            tp = Path(self.textbox3.text())
            if any([
                self.save_base_path != tp,
                self.config["save_base_path"] != self.save_base_path,
                tp != self.config["save_base_path"],
            ]):
                need_init = True

        # 初期化が必要な場合初期化する
        if need_init:
            logger.info("LinkSearcher init -> start")
            # 保存先パス設定
            tp = Path(self.textbox3.text())
            if any([
                self.save_base_path != tp,
                self.config["save_base_path"] != self.save_base_path,
                tp != self.config["save_base_path"],
            ]):
                # 変更があった場合、テキストボックスに入力されているパスを優先とする
                self.save_base_path = Path(tp)
                self.save_base_path.mkdir(parents=True, exist_ok=True)
                self.config["save_base_path"] = self.save_base_path

            self.config["pixiv"]["is_enable"] = self.checkbox_list[0].isChecked()
            self.config["nijie"]["is_enable"] = self.checkbox_list[1].isChecked()
            self.config["nico_seiga"]["is_enable"] = self.checkbox_list[2].isChecked()
            self.link_searcher = LinkSearcher.create(self.config)
            logger.info("LinkSearcher init -> done")

        # fetch する
        logger.info("LinkSearcher fetch -> start")
        try:
            self.link_searcher.fetch(work_url)
        except Exception as e:
            logger.info(str(e))

        logger.info("LinkSearcher fetch -> done")

        logger.info("GuiMain link_search -> done")
        return Result.success

    @Slot()
    def directory_browse(self):
        logger.info("GuiMain directory_browse -> start")
        if not hasattr(self, "textbox3"):
            # レイアウト作成前に呼び出された場合は何もしない
            logger.info("Textbox3 is not found.")
            logger.info("GuiMain directory_browse -> abort")
            return Result.failed

        # 現状でテキストボックスに入っているパスを初期値とする
        try:
            now_input_path = Path(self.textbox3.text())
            if not now_input_path.exists():
                now_input_path = Path(__file__).parent
        except Exception:
            now_input_path = Path(__file__).parent

        # ディレクトリパスをユーザーに問い合わせる
        dialog = QFileDialog()
        dirname = dialog.getExistingDirectory(dir=str(now_input_path))

        # 問い合わせ結果が空文字なら失敗
        if not dirname:
            logger.info("Directory selection was cancelled.")
            logger.info("GuiMain directory_browse -> abort")
            return Result.failed

        # 問い合わせ結果を確認
        try:
            dirname_path = Path(dirname)
            if not dirname_path.exists():
                logger.info(f"Dirname: '{dirname}' is invalid.")
                logger.info("GuiMain directory_browse -> abort")
                return Result.failed
        except Exception:
            logger.info(f"Dirname: '{dirname}' is invalid.")
            logger.info("GuiMain directory_browse -> abort")
            return Result.failed

        # 新たなディレクトリパスをテキストボックスに設定する
        self.save_base_path = dirname_path
        self.config["save_base_path"] = dirname_path
        self.textbox3.setText(dirname)
        logger.info(f"Set save_base_path: '{str(dirname_path)}'")
        logger.info("GuiMain directory_browse -> done")
        return Result.success

    @Slot()
    def open_explorer(self):
        logger.info("GuiMain open_explorer -> start")
        if not hasattr(self, "textbox3"):
            # レイアウト作成前に呼び出された場合は何もしない
            logger.info("Textbox3 is not found.")
            logger.info("GuiMain open_explorer -> abort")
            return Result.failed

        # 現状でテキストボックスに入っているパスを対象とする
        try:
            target_path = Path(self.textbox3.text())
            if not target_path.exists():
                logger.info(f"Target_path: '{target_path}' is invalid.")
                logger.info("GuiMain directory_browse -> abort")
                return Result.failed
        except Exception:
            logger.info(f"Target_path: '{target_path}' is invalid.")
            logger.info("GuiMain directory_browse -> abort")
            return Result.failed

        # 標準のエクスプローラで開く
        logger.info(f"Open with explorer, path: '{str(target_path)}'")
        subprocess.Popen(["explorer", str(target_path)])
        logger.info("GuiMain open_explorer -> done")
        return Result.success

    def create_layout(self):
        # 1行目
        # ラベル, 作品ページURL, 実行ボタン
        label1 = QLabel("作品ページURL")
        label1.setMinimumWidth(80)
        self.textbox1 = QLineEdit("")
        self.textbox1.setMinimumWidth(500)
        button1 = QPushButton("実行")
        button1.clicked.connect(self.link_search)

        h_layout1 = QHBoxLayout()
        h_layout1.addWidget(label1)
        h_layout1.addWidget(self.textbox1)
        h_layout1.addWidget(button1)
        h_layout1.addStretch(1)

        # 2行目
        # ラベル, 対象指定チェックボックス
        label2 = QLabel("チェック対象")
        label2.setMinimumWidth(80)
        checkbox_label_list = ["pixiv", "nijie", "nico_seiga"]
        self.checkbox_list = [QCheckBox(checkbox_label) for checkbox_label in checkbox_label_list]
        for i, checkbox in enumerate(self.checkbox_list):
            if self.config[checkbox_label_list[i]]["is_enable"]:
                checkbox.setCheckState(Qt.CheckState.Checked)
            else:
                checkbox.setCheckState(Qt.CheckState.Unchecked)

        h_layout2 = QHBoxLayout()
        h_layout2.addWidget(label2)
        for checkbox in self.checkbox_list:
            h_layout2.addWidget(checkbox)
        h_layout2.addStretch(1)

        # 3行目
        # ラベル, 保存先パス, 参照ボタン, 開くボタン
        label3 = QLabel("保存先パス")
        label3.setMinimumWidth(80)
        self.textbox3 = QLineEdit("")
        self.textbox3.setMinimumWidth(500)
        self.textbox3.setText(str(self.save_base_path))
        button31 = QPushButton("参照")
        button31.clicked.connect(self.directory_browse)
        button32 = QPushButton("開く")
        button32.clicked.connect(self.open_explorer)

        h_layout3 = QHBoxLayout()
        h_layout3.addWidget(label3)
        h_layout3.addWidget(self.textbox3)
        h_layout3.addWidget(button31)
        h_layout3.addWidget(button32)
        h_layout3.addStretch(1)

        # グループ化
        groupbox = QGroupBox(APP_NAME)
        group_layout = QVBoxLayout(groupbox)
        group_layout.addLayout(h_layout1)
        group_layout.addLayout(h_layout2)
        group_layout.addLayout(h_layout3)

        # ログ出力用テキストエリア
        self.textarea = QTextEdit()
        self.textarea.setMinimumHeight(300)

        # メインレイアウト設定
        main_layout = QGridLayout(self)
        main_layout.addWidget(groupbox, 0, 0)
        main_layout.addWidget(self.textarea, 1, 0)

        return main_layout


if __name__ == "__main__":
    app = QApplication()
    gui_main = GuiMain()
    gui_main.show()
    gui_main.activateWindow()
    sys.exit(app.exec())
