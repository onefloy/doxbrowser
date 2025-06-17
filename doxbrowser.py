import os
import sys
from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLineEdit, QVBoxLayout, QWidget,
    QLabel, QMenuBar, QAction, QFileDialog, QHBoxLayout,
    QPushButton, QFrame, QTabWidget
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage, QWebEngineSettings


class BrowserTab(QWidget):
    def __init__(self, profile, on_url_change_callback):
        super().__init__()
        self.profile = profile
        self.on_url_change_callback = on_url_change_callback

        self.layout = QVBoxLayout(self)
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Введите URL и нажмите Enter")
        self.url_bar.setStyleSheet("background-color: #111; color: white; padding: 6px; font-family: Courier;")
        self.url_bar.returnPressed.connect(self.load_url)
        self.layout.addWidget(self.url_bar)

        self.browser = QWebEngineView()
        self.page = QWebEnginePage(profile, self.browser)
        self.browser.setPage(self.page)
        self.browser.urlChanged.connect(self.handle_url_change)
        self.layout.addWidget(self.browser)

    def load_url(self):
        text = self.url_bar.text().strip()
        if text.startswith("http://") or text.startswith("https://"):
            url = text
        elif "." in text and " " not in text:
            url = "http://" + text
        else:
            url = f"https://www.google.com/search?q={text.replace(' ', '+')}"
        self.browser.load(QUrl(url))

    def handle_url_change(self, qurl):
        self.url_bar.setText(qurl.toString())
        if self.on_url_change_callback:
            self.on_url_change_callback(qurl)


class DoxBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DOXBROWSER")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background-color: black; color: white;")
        self.anonymous = True
        self.plugins = []

        self.init_ui()
        self.create_profile()
        self.create_menu()
        self.add_tab()

    def init_ui(self):
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)

        # Заголовок с анимацией
        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Courier", 20, QFont.Bold))
        self.layout.addWidget(self.title_label)

        self.title_text = "DOXBROWSER"
        self.visible = [True] * len(self.title_text)
        self.current_index = 0
        self.start_animation()

        # Панель плагинов
        self.plugin_panel = QFrame()
        self.plugin_panel.setFrameShape(QFrame.StyledPanel)
        self.plugin_layout = QHBoxLayout(self.plugin_panel)
        self.plugin_panel.setVisible(False)
        self.layout.addWidget(self.plugin_panel)

        # Вкладки
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.layout.addWidget(self.tabs)

        self.setCentralWidget(self.container)

    def start_animation(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate_title)
        self.timer.start(150)

    def animate_title(self):
        self.visible[self.current_index] = not self.visible[self.current_index]
        style = "".join(
            f"<span style='color:{'hsl('+str((i*36)%360)+',100%,50%)' if self.visible[i] else 'black'}'>{c}</span>"
            for i, c in enumerate(self.title_text)
        )
        self.title_label.setText(f"<html>{style}</html>")
        self.current_index = (self.current_index + 1) % len(self.title_text)

    def create_profile(self):
        self.profile = QWebEngineProfile(self)
        if self.anonymous:
            self.profile.setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
            self.profile.setCachePath("")
            self.profile.setPersistentStoragePath("")
        self.profile.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)

    def create_menu(self):
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        plugin_menu = menubar.addMenu("🔌 Плагины")
        load_action = QAction("Загрузить плагин", self)
        load_action.triggered.connect(self.load_plugin)
        plugin_menu.addAction(load_action)

        view_plugin_panel = QAction("Панель плагинов", self, checkable=True)
        view_plugin_panel.setChecked(False)
        view_plugin_panel.triggered.connect(lambda ch: self.plugin_panel.setVisible(ch))
        plugin_menu.addAction(view_plugin_panel)

        tools_menu = menubar.addMenu("🛠 Инструменты")

        anon_action = QAction("Анонимность", self, checkable=True)
        anon_action.setChecked(True)
        anon_action.triggered.connect(self.toggle_anonymous_mode)
        tools_menu.addAction(anon_action)

        new_tab_action = QAction("🆕 Новая вкладка", self)
        new_tab_action.triggered.connect(self.add_tab)
        menubar.addAction(new_tab_action)

    def add_tab(self):
        tab = BrowserTab(self.profile, self.update_urlbar_from_tab)
        index = self.tabs.addTab(tab, "Новая вкладка")
        self.tabs.setCurrentIndex(index)
        tab.load_url()

    def close_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)

    def on_tab_changed(self, index):
        tab = self.tabs.widget(index)
        if isinstance(tab, BrowserTab):
            tab.url_bar.setFocus()

    def update_urlbar_from_tab(self, qurl):
        # Можно сделать расширение, если нужно показывать URL в главной строке, но сейчас адресная строка — у вкладки
        pass

    def toggle_anonymous_mode(self, enabled):
        self.anonymous = enabled
        self.create_profile()
        # Обновляем страницу для всех вкладок
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if isinstance(tab, BrowserTab):
                tab.browser.setPage(QWebEnginePage(self.profile, tab.browser))

    def load_plugin(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выбери плагин", "", "Python (*.py)")
        if not path:
            return
        try:
            current_tab = self.tabs.currentWidget()
            gl = {"browser": current_tab.browser, "page": current_tab.page, "url_bar": current_tab.url_bar}
            with open(path, encoding="utf-8") as f:
                code = compile(f.read(), path, 'exec')
                exec(code, gl)
            btn = QPushButton(os.path.basename(path))
            btn.clicked.connect(lambda: gl.get("run_plugin", lambda: None)())
            self.plugin_layout.addWidget(btn)
            self.plugins.append((path, btn))
        except Exception as e:
            print("Ошибка загрузки плагина:", e)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DoxBrowser()
    win.show()
    sys.exit(app.exec_())
