# FULL REVISED CODE WITH RUNNING / PAUSED INDICATOR

import sys
import time
import pandas as pd
import os

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout,
    QMessageBox, QTableWidget, QTableWidgetItem,
    QFrame, QHeaderView, QProgressBar, QPushButton, QFileDialog, QHBoxLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException

LOGIN_URL = "https://services.gst.gov.in/services/login"
LOGOUT_URL = "https://services.gst.gov.in/services/logout"


# ================= WORKER THREAD =================
class GSTWorker(QThread):
    progress_update = pyqtSignal(int, str)
    status_update = pyqtSignal(int, str)
    chrome_closed = pyqtSignal()
    finished_all = pyqtSignal()

    def __init__(self, df, start_index=0):
        super().__init__()
        self.df = df
        self.start_index = start_index
        self.is_paused = False
        self.is_running = True
        self.driver = None

    def run(self):
        try:
            self.start_driver()
            total = len(self.df)

            for i in range(self.start_index, total):

                while self.is_paused:
                    time.sleep(1)

                if not self.is_running:
                    return

                user = str(self.df.iloc[i]["portalUserName"])
                pwd = str(self.df.iloc[i]["portalPassword"])

                self.progress_update.emit(i, f"{i+1}/{total} → Checking {user}")
                status = self.check_login(i, user, pwd)
                self.status_update.emit(i, status)

            self.finished_all.emit()

        except Exception:
            self.chrome_closed.emit()

    def start_driver(self):
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()

    def safe_restart_driver(self):
        try:
            self.driver.quit()
        except:
            pass
        self.start_driver()

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def stop(self):
        self.is_running = False
        try:
            self.driver.quit()
        except:
            pass

    def check_login(self, row_index, user, pwd):
        while True:
            try:
                self.driver.get(LOGIN_URL)
                time.sleep(3)
                self.fill_credentials(user, pwd)

                while True:

                    if self.is_paused:
                        time.sleep(1)
                        continue

                    current_url = self.driver.current_url.lower()
                    page_source = self.driver.page_source.lower()

                    if "changepassword" in current_url:
                        return "Password expired"

                    if "fowelcome" in current_url:
                        self.driver.get(LOGOUT_URL)
                        time.sleep(3)
                        return "Password is working"

                    if "invalid username or password" in page_source:
                        return "WRONG password"

                    if "login" in current_url:
                        try:
                            uname = self.driver.find_element(By.ID, "username").get_attribute("value")
                            if uname == "":
                                self.fill_credentials(user, pwd)
                        except:
                            pass

                    time.sleep(1)

            except WebDriverException:
                self.safe_restart_driver()
                continue

    def fill_credentials(self, user, pwd):
        try:
            self.driver.find_element(By.ID, "username").clear()
            self.driver.find_element(By.ID, "username").send_keys(user)

            pwd_box = self.driver.find_element(By.ID, "user_pass")
            pwd_box.clear()
            pwd_box.send_keys(pwd)
            pwd_box.send_keys(Keys.TAB)

        except WebDriverException:
            self.safe_restart_driver()


# ================= DROP ZONE =================
class DropLabel(QFrame):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)

        title = QLabel("Drop CSV/Excel File Here\n(or click to browse)")
        title.setFont(QFont("Segoe UI", 13))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #64748b;")

        layout.addStretch()
        layout.addWidget(title)
        layout.addStretch()

        self.setStyleSheet("""
            DropLabel {
                background: #ffffff;
                border: 2px dashed #cbd5e1;
                border-radius: 12px;
            }
            DropLabel:hover {
                border: 2px dashed #3b82f6;
                background: #f8fafc;
            }
        """)
        self.setCursor(Qt.PointingHandCursor)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()

    def dropEvent(self, event):
        file_path = event.mimeData().urls()[0].toLocalFile()
        self.parent.process_file(file_path)

    def mousePressEvent(self, event):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV or Excel File",
            os.path.expanduser("~"),
            "CSV Files (*.csv);;Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.parent.process_file(file_path)


# ================= MAIN APP =================
class GSTLoginHelper(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GST Login Verifier")
        self.resize(1050, 680)

        self.setStyleSheet("QWidget { background:#f8fafc; }")

        self.worker = None
        self.df = None

        main_layout = QVBoxLayout(self)

        header = QLabel("GST Portal Password Verification")
        header.setFont(QFont("Segoe UI", 18, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
        color:white;
        padding:22px;
        border-radius:12px;
        background:qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #0ea5e9, stop:0.5 #0284c7, stop:1 #0369a1);
        """)
        main_layout.addWidget(header)

        self.drop_label = DropLabel(self)
        self.drop_label.setFixedHeight(100)
        main_layout.addWidget(self.drop_label)

        self.progress_label = QLabel("Waiting for file...")
        main_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        # 🔥 NEW STATUS LABEL
        self.state_label = QLabel("IDLE")
        self.state_label.setAlignment(Qt.AlignCenter)
        self.state_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.state_label.setStyleSheet("color:#2563eb; padding:8px;")
        main_layout.addWidget(self.state_label)

        self.table = QTableWidget()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        main_layout.addWidget(self.table)

        # ===== BUTTON BAR CONTAINER (STATIC GREY BACKGROUND) =====
        btn_container = QFrame()
        btn_container.setStyleSheet("""
        QFrame {
            background-color: #e2e8f0;
            border-radius: 14px;
            padding: 12px;
        }
        """)

        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setSpacing(15)

        self.pause_btn = QPushButton("⏸ Pause")
        self.resume_btn = QPushButton("▶ Resume")
        self.export_btn = QPushButton("📤 Export Checked")

        self.pause_btn.clicked.connect(self.pause)
        self.resume_btn.clicked.connect(self.resume)
        self.export_btn.clicked.connect(self.export_checked)

        button_style = """
        QPushButton {
            border-radius: 12px;
            padding: 10px 20px;
            font-size: 12pt;
            font-weight: 600;
            color: white;
            border: none;
        }

        QPushButton:disabled {
            background-color: #cbd5e1;
            color: #475569;
            border: none;
        }
        """

        grey_button_style = """
        QPushButton {
            background-color: #94a3b8;
            color: #1f2933;
            border-radius: 12px;
            padding: 10px 20px;
            font-size: 12pt;
            font-weight: 600;
            border: none;
        }

        QPushButton:hover {
            background-color: #9aa6b2;
        }

        QPushButton:pressed {
            background-color: #7c8a99;
        }

        QPushButton:disabled {
            background-color: #cbd5e1;
            color: #6b7280;
        }
        """

        self.pause_btn.setStyleSheet(grey_button_style)
        self.resume_btn.setStyleSheet(grey_button_style)
        self.export_btn.setStyleSheet(grey_button_style)


        btn_layout.addWidget(self.pause_btn)
        btn_layout.addWidget(self.resume_btn)
        btn_layout.addWidget(self.export_btn)

        main_layout.addWidget(btn_container)


    def export_checked(self):
        if self.df is None:
            QMessageBox.warning(self, "No Data", "Load a file first.")
            return

        checked_df = self.df[self.df["Status"].str.strip() != ""]

        if len(checked_df) == 0:
            QMessageBox.information(self, "Nothing to export", "No GSTs checked yet.")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Checked Results",
            "checked_results.xlsx",
            "Excel Files (*.xlsx)"
        )

        if save_path:
            checked_df.to_excel(save_path, index=False)
            QMessageBox.information(self, "Exported", f"Saved:\n{save_path}")

    def load_table(self):
        self.table.setRowCount(len(self.df))
        self.table.setColumnCount(len(self.df.columns))
        self.table.setHorizontalHeaderLabels(self.df.columns)

        for i in range(len(self.df)):
            for j in range(len(self.df.columns)):
                self.table.setItem(i, j, QTableWidgetItem(str(self.df.iloc[i, j])))

    def update_status(self, row, status):
        self.df.at[row, "Status"] = status
        col = self.df.columns.get_loc("Status")
        self.table.setItem(row, col, QTableWidgetItem(status))

    def update_progress(self, row, text):
        self.progress_label.setText(text)
        self.progress_bar.setValue(int(((row+1)/len(self.df))*100))

    def process_file(self, file_path):
        if file_path.endswith('.csv'):
            self.df = pd.read_csv(file_path)
        else:
            self.df = pd.read_excel(file_path)

        self.df = self.df[["gstin", "name", "portalUserName", "portalPassword"]]
        self.df["Status"] = ""

        self.load_table()

        self.pause_btn.setEnabled(True)
        self.resume_btn.setEnabled(False)
        self.export_btn.setEnabled(True)

        # 🔥 SET RUNNING STATE
        self.state_label.setText("🟢 RUNNING")
        self.state_label.setStyleSheet("color:#16a34a; font-size:18px; font-weight:700;")

        self.worker = GSTWorker(self.df)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.status_update.connect(self.update_status)
        self.worker.finished_all.connect(self.finish)
        self.worker.start()

    def pause(self):
        if self.worker:
            self.worker.pause()
            self.pause_btn.setEnabled(False)
            self.resume_btn.setEnabled(True)

            # 🔥 STATE CHANGE
            self.state_label.setText("🟡 PAUSED")
            self.state_label.setStyleSheet("color:#ca8a04; font-size:18px; font-weight:700;")

    def resume(self):
        if self.worker:
            self.worker.resume()
            self.pause_btn.setEnabled(True)
            self.resume_btn.setEnabled(False)

            # 🔥 STATE CHANGE
            self.state_label.setText("🟢 RUNNING")
            self.state_label.setStyleSheet("color:#16a34a; font-size:18px; font-weight:700;")

    def finish(self):
        self.pause_btn.setEnabled(False)
        self.resume_btn.setEnabled(False)
        self.export_btn.setEnabled(True)

        # 🔥 COMPLETED STATE
        self.state_label.setText("🔵 COMPLETED")
        self.state_label.setStyleSheet("color:#2563eb; font-size:18px; font-weight:700;")

        QMessageBox.information(self, "Done", "Verification completed!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GSTLoginHelper()
    window.show()
    sys.exit(app.exec_())
