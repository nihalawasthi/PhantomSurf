import sys
import socket
import ssl
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QTabWidget,
    QLineEdit, QToolBar, QAction, QStatusBar, QPushButton
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt

class URL:
    def __init__(self, url):
        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["http", "https"]
        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
        self.path = "/" + url
        self.port = 80 if self.scheme == "http" else 443
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)

    def request(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)
        request = f"GET {self.path} HTTP/1.0\r\nHost: {self.host}\r\n\r\n"
        s.send(request.encode("utf8"))
        response = s.makefile("r", encoding="utf8", newline="\r\n")
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)
        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n":
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers
        content = response.read()
        s.close()
        return content

class Browser(QMainWindow):
    def __init__(self, url):
        super().__init__()
        self.setWindowTitle("Phantom Surf")
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QTabWidget::pane {
                border: 1px solid #ccc;
                background: #fff;
            }
            QLineEdit {
                border: 1px solid #aaa;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #005bb5;
            }
            QToolBar {
                background: #fff;
                border: 1px solid #ccc;
            }
        """)

        # Main layout
        main_layout = QHBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        sidebar_layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)
        self.tabs.setDocumentMode(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.tabs.currentChanged.connect(self.update_url_bar)

        # New Tab button
        self.new_tab_button = QPushButton("+")
        self.new_tab_button.setFixedSize(25, 25)
        self.new_tab_button.clicked.connect(self.add_new_tab)

        # Sidebar widget
        sidebar_widget = QWidget()
        sidebar_widget_layout = QVBoxLayout()
        sidebar_widget_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_widget_layout.addWidget(self.tabs)
        sidebar_widget_layout.addWidget(self.new_tab_button, alignment=Qt.AlignTop)
        sidebar_widget.setLayout(sidebar_widget_layout)
        sidebar_layout.addWidget(sidebar_widget)

        # Browser area
        self.browser_layout = QVBoxLayout()

        nav_toolbar = QToolBar("Navigation")
        self.addToolBar(nav_toolbar)

        # Back button
        back_btn = QAction("◀", self)
        back_btn.triggered.connect(lambda: self.tabs.currentWidget().back())
        nav_toolbar.addAction(back_btn)

        # Forward button
        forward_btn = QAction("▶", self)
        forward_btn.triggered.connect(lambda: self.tabs.currentWidget().forward())
        nav_toolbar.addAction(forward_btn)

        # Reload button
        reload_btn = QAction("🔄", self)
        reload_btn.triggered.connect(lambda: self.tabs.currentWidget().reload())
        nav_toolbar.addAction(reload_btn)

        # Home button
        home_btn = QAction("🏠", self)
        home_btn.triggered.connect(self.navigate_home)
        nav_toolbar.addAction(home_btn)

        # URL/search bar
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_toolbar.addWidget(self.url_bar)

        # Status bar
        self.setStatusBar(QStatusBar())
        main_layout.addLayout(sidebar_layout)
        browser_widget = QWidget()
        browser_widget.setLayout(self.browser_layout)
        main_layout.addWidget(browser_widget, 1)
        self.add_new_tab(QUrl(f"{url.scheme}://{url.host}{url.path}"), "New Tab")

    def add_new_tab(self, qurl=None, label="New Tab"):
        if not isinstance(qurl, QUrl) or qurl is None:
            qurl = QUrl("https://www.google.com")
        browser = QWebEngineView()
        browser.setUrl(qurl)
        browser.urlChanged.connect(lambda qurl=QUrl(), browser=browser: self.update_url_bar(qurl))
        self.tabs.addTab(browser, label)
        self.tabs.setCurrentWidget(browser)

    def update_url_bar(self, qurl=None):
        if not isinstance(qurl, QUrl):
            qurl = self.tabs.currentWidget().url()
        self.url_bar.setText(qurl.toString())
        self.url_bar.setCursorPosition(0)

    def close_current_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)

    def navigate_home(self):
        home_url = QUrl("https://www.google.com")
        self.tabs.currentWidget().setUrl(home_url)

    def navigate_to_url(self):
        url_text = self.url_bar.text()
        qurl = QUrl(url_text if "://" in url_text else "http://" + url_text)
        self.tabs.currentWidget().setUrl(qurl)

def load(url):
    app = QApplication(sys.argv)
    window = Browser(url)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    load(URL("https://www.example.com"))