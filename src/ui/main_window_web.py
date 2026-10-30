import os
from PySide6.QtWidgets import QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtCore import QUrl
from src.ui_web.bridge import FrontendBridge

class MainWindowWeb(QMainWindow):
    def __init__(self, services):
        super().__init__()
        self.setWindowTitle("Say Mahar - Pharmacy & Retail Management")
        self.resize(1200, 800)

        # Setup WebEngineView
        self.view = QWebEngineView(self)
        self.setCentralWidget(self.view)

        # Setup Bridge and WebChannel
        self.bridge = FrontendBridge(services, parent=self)
        self.channel = QWebChannel(self.view.page())
        self.channel.registerObject("backend", self.bridge)
        self.view.page().setWebChannel(self.channel)

        # Sync initial window title with saved language preference if available
        try:
            conn = services['db_manager'].get_connection()
            row = conn.execute("SELECT value FROM settings WHERE key = 'language'").fetchone()
            if row and row['value'] == 'my':
                self.update_language_title('my')
        except Exception:
            pass

        # Load local HTML file
        from src.utils.paths import get_web_ui_dir
        html_path = os.path.join(get_web_ui_dir(), "index.html")
        
        # We need a proper file:// URL
        url = QUrl.fromLocalFile(html_path)
        self.view.load(url)

    def update_language_title(self, lang):
        if lang == 'my':
            self.setWindowTitle("ဆေးမဟာ - ဆေးနှင့်ကုန်စုံအရောင်းဆိုင် စီမံခန့်ခွဲမှုစနစ်")
        else:
            self.setWindowTitle("Say Mahar - Pharmacy & Retail Management")
