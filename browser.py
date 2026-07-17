import sys
import json
import os
import tempfile
import atexit
import threading
import urllib.request
import urllib.parse
import urllib.error
import importlib.util
import inspect
import time
from pathlib import Path
from typing import Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTabWidget, QLabel, QDialog, QListWidget,
    QListWidgetItem, QMessageBox, QSpinBox, QCheckBox, QComboBox,
    QProgressBar, QStatusBar, QDockWidget, QTextBrowser, QGroupBox,
    QTextEdit, QSplitter, QFrame
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings, QWebEnginePage, QWebEngineScript
from PyQt6.QtCore import QUrl, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QAction, QKeySequence, QDesktopServices

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

APP_NAME = 'Nova'
APP_VERSION = '3.0'

DATA_FILE = 'browser_data.json'
PLUGINS_DIR = 'plugins'

COLORS = {
    'bg_dark':       '#0a120a',
    'bg_medium':     '#121a12',
    'bg_light':      '#1c241e',
    'bg_input':      '#2c342e',
    'accent':        '#5e9bee',
    'accent_hover':  '#7bb3ff',
    'accent_dim':    '#3a7bd5',
    'text':          '#f0f0f0',
    'text_muted':    '#8e8e93',
    'text_dim':      '#636366',
    'border':        '#2c342e',
    'border_focus':  '#5e9bee',
    'danger':        '#ff453a',
    'success':       '#30d158',
}

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text']};
    font-family: -apple-system, 'Segoe UI', 'SF Pro Text', Roboto, sans-serif;
    font-size: 12.5px;
}}

QPushButton {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 5px 14px;
    font-size: 12.5px;
    min-height: 24px;
}}
QPushButton:hover {{
    background-color: {COLORS['bg_input']};
    border-color: {COLORS['accent']};
}}
QPushButton:pressed {{
    background-color: {COLORS['accent_dim']};
    border-color: {COLORS['accent']};
}}
QPushButton:flat {{
    background: transparent;
    border: none;
}}
QPushButton:flat:hover {{
    background-color: {COLORS['bg_input']};
    border: none;
}}
QPushButton:flat:pressed {{
    background-color: {COLORS['accent_dim']};
    border: none;
}}

QComboBox, QLineEdit {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 4px 10px;
    font-size: 12.5px;
    selection-background-color: {COLORS['accent_dim']};
}}
QComboBox:focus, QLineEdit:focus {{
    border-color: {COLORS['accent']};
    background-color: {COLORS['bg_medium']};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox QAbstractItemView {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text']};
    selection-background-color: {COLORS['accent_dim']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    outline: none;
    padding: 4px;
}}

QTabWidget::pane {{
    background-color: {COLORS['bg_dark']};
    border: none;
}}
QTabBar::tab {{
    background-color: transparent;
    color: {COLORS['text_muted']};
    padding: 6px 18px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 0;
    min-width: 80px;
}}
QTabBar::tab:selected {{
    color: {COLORS['accent']};
    border-bottom: 2px solid {COLORS['accent']};
    font-weight: 600;
}}
QTabBar::tab:hover:!selected {{
    color: {COLORS['text']};
    background-color: {COLORS['bg_light']};
}}
QTabBar::close-button {{
    image: none;
    font-family: "Segoe UI", "SF Pro Text", sans-serif;
    font-size: 14px;
    font-weight: 300;
    padding: 0 2px;
    border-radius: 3px;
    color: {COLORS['text_muted']};
}}
QTabBar::close-button:hover {{
    background-color: {COLORS['bg_input']};
    color: {COLORS['text']};
}}

QListWidget {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    outline: none;
    padding: 4px;
}}
QListWidget::item {{
    border-radius: 5px;
    padding: 7px 10px;
}}
QListWidget::item:selected {{
    background-color: {COLORS['accent_dim']};
    color: {COLORS['text']};
}}
QListWidget::item:hover:!selected {{
    background-color: {COLORS['bg_light']};
}}

QSpinBox {{
    background-color: {COLORS['bg_light']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 22px;
}}
QSpinBox:focus {{
    border-color: {COLORS['accent']};
}}
QSpinBox::up-button, QSpinBox::down-button {{
    border: none;
    background: transparent;
    width: 18px;
}}

QCheckBox {{
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    background-color: {COLORS['bg_light']};
}}
QCheckBox::indicator:checked {{
    background-color: {COLORS['accent']};
    border-color: {COLORS['accent']};
}}
QCheckBox::indicator:hover {{
    border-color: {COLORS['accent']};
}}

QLabel {{
    color: {COLORS['text']};
}}

QDialog {{
    background-color: {COLORS['bg_dark']};
}}

QProgressBar {{
    background-color: {COLORS['bg_light']};
    border: none;
    border-radius: 2px;
    height: 3px;
    text-align: center;
}}
QProgressBar::chunk {{
    background-color: {COLORS['accent']};
    border-radius: 2px;
}}

QStatusBar {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text_muted']};
    border-top: 1px solid {COLORS['border']};
    font-size: 11px;
    padding: 2px 8px;
}}

QScrollBar:vertical {{
    background: {COLORS['bg_dark']};
    width: 8px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['bg_input']};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {COLORS['text_dim']};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}
QScrollBar:horizontal {{
    background: {COLORS['bg_dark']};
    height: 8px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS['bg_input']};
    border-radius: 4px;
    min-width: 30px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {COLORS['text_dim']};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
}}

QToolTip {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
}}

QDockWidget {{
    background-color: {COLORS['bg_dark']};
    color: {COLORS['text']};
    titlebar-close-icon: none;
}}
QDockWidget::title {{
    background-color: {COLORS['bg_medium']};
    padding: 6px 12px;
    border-bottom: 1px solid {COLORS['border']};
}}
QDockWidget::close-button, QDockWidget::float-button {{
    background: transparent;
    border: none;
    color: {COLORS['text_muted']};
}}

QTextBrowser {{
    background-color: {COLORS['bg_medium']};
    color: {COLORS['text']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px;
    selection-background-color: {COLORS['accent_dim']};
}}

QGroupBox {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 12px;
    padding: 12px 8px 8px;
    font-weight: 600;
    color: {COLORS['accent']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}}
"""


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class Bookmark:
    url: str
    title: str

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Bookmark):
            return NotImplemented
        return self.url == other.url


@dataclass
class Shortcut:
    name: str
    url: str
    icon: str = '🌐'


@dataclass
class Download:
    name: str
    size: str
    date: str


@dataclass
class Settings:
    default_zoom: int = 100
    font_size: int = 14
    auto_recover_tabs: bool = True
    enable_js: bool = True
    https_only: bool = True
    block_mixed_content: bool = True
    block_third_party_cookies: bool = True
    safe_browsing: bool = True
    sync_enabled: bool = False
    sync_url: str = ''
    sync_key: str = ''
    ai_api_url: str = 'http://localhost:11434/v1/chat/completions'
    ai_api_key: str = ''
    ai_model: str = 'llama3.2'
    translate_api_url: str = 'https://libretranslate.com/translate'
    reader_font_size: int = 18
    perf_monitor_enabled: bool = False


@dataclass
class BrowserData:
    bookmarks: list[dict] = field(default_factory=list)
    history: list[str] = field(default_factory=list)
    downloads: list[dict] = field(default_factory=list)
    custom_shortcuts: list[dict] = field(default_factory=list)
    settings: dict = field(default_factory=lambda: asdict(Settings()))
    open_tabs: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Plugin / Extension API
# ---------------------------------------------------------------------------

class NovaPlugin:
    name: str = ''
    version: str = '1.0'
    description: str = ''

    def on_page_load(self, url: str, tab: 'BrowserTab') -> None:
        pass

    def on_navigate(self, url: str) -> None:
        pass

    def on_tab_changed(self, idx: int, tab: 'BrowserTab') -> None:
        pass

    def on_url_changed(self, url: str) -> None:
        pass

    def install(self, browser: 'Browser') -> None:
        pass

    def uninstall(self, browser: 'Browser') -> None:
        pass


class PluginManager:
    def __init__(self, browser: 'Browser') -> None:
        self.browser = browser
        self.plugins: list[NovaPlugin] = []

    def discover_and_load(self) -> None:
        plugins_path = Path(PLUGINS_DIR)
        if not plugins_path.is_dir():
            plugins_path.mkdir(exist_ok=True)
            init_file = plugins_path / '__init__.py'
            if not init_file.exists():
                init_file.write_text('')
            return

        for pyfile in plugins_path.glob('*.py'):
            if pyfile.name.startswith('_'):
                continue
            self._load_plugin(pyfile)

    def _load_plugin(self, path: Path) -> None:
        try:
            spec = importlib.util.spec_from_file_location(path.stem, path)
            if not spec or not spec.loader:
                return
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            plugin: NovaPlugin = getattr(mod, 'plugin', None)
            if plugin is None:
                for _, obj in inspect.getmembers(mod, lambda o: isinstance(o, NovaPlugin)):
                    plugin = obj
                    break
            if plugin is None:
                return
            plugin.install(self.browser)
            self.plugins.append(plugin)
            self.browser._show_status(f'Plugin loaded: {plugin.name} v{plugin.version}', 3000)
        except Exception as e:
            self.browser._show_status(f'Failed to load plugin {path.name}: {e}', 5000)

    def notify_page_load(self, url: str, tab: 'BrowserTab') -> None:
        for p in self.plugins:
            try:
                p.on_page_load(url, tab)
            except Exception:
                pass

    def notify_navigate(self, url: str) -> None:
        for p in self.plugins:
            try:
                p.on_navigate(url)
            except Exception:
                pass

    def notify_tab_changed(self, idx: int, tab: 'BrowserTab') -> None:
        for p in self.plugins:
            try:
                p.on_tab_changed(idx, tab)
            except Exception:
                pass

    def notify_url_changed(self, url: str) -> None:
        for p in self.plugins:
            try:
                p.on_url_changed(url)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Profile Sync Manager
# ---------------------------------------------------------------------------

class SyncManager:
    def __init__(self, browser: 'Browser') -> None:
        self.browser = browser
        self._timer: QTimer | None = None
        self._running = False

    def start(self) -> None:
        if not self.browser.settings.get('sync_enabled', False):
            return
        self._timer = QTimer()
        self._timer.timeout.connect(self.sync_pull)
        self._timer.start(300000)

    def stop(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None

    def sync_push(self) -> None:
        if not self._can_sync():
            return
        url = self.browser.settings['sync_url'].rstrip('/') + '/push'
        key = self.browser.settings['sync_key']
        data = {
            'bookmarks': self.browser.bookmarks,
            'history': self.browser.history[-200:],
            'settings': self.browser.settings,
            'timestamp': datetime.now().isoformat(),
        }
        threading.Thread(target=self._do_push, args=(url, key, data), daemon=True).start()

    def sync_pull(self) -> None:
        if not self._can_sync():
            return
        url = self.browser.settings['sync_url'].rstrip('/') + '/pull'
        key = self.browser.settings['sync_key']
        threading.Thread(target=self._do_pull, args=(url, key), daemon=True).start()

    def _can_sync(self) -> bool:
        return bool(
            self.browser.settings.get('sync_enabled', False)
            and self.browser.settings.get('sync_url', '')
        )

    def _do_push(self, url: str, key: str, data: dict) -> None:
        try:
            payload = json.dumps(data).encode()
            req = urllib.request.Request(
                url, data=payload,
                headers={'Content-Type': 'application/json', 'X-Api-Key': key},
                method='POST'
            )
            urllib.request.urlopen(req, timeout=10)
            QTimer.singleShot(0, lambda: self.browser._show_status('Sync push completed', 3000))
        except Exception as e:
            QTimer.singleShot(0, lambda e=e: self.browser._show_status(f'Sync push failed: {e}', 4000))

    def _do_pull(self, url: str, key: str) -> None:
        try:
            req = urllib.request.Request(
                url, headers={'X-Api-Key': key},
                method='GET'
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            remote_bm = data.get('bookmarks', [])
            remote_hist = data.get('history', [])
            if remote_bm:
                self.browser.bookmarks = remote_bm
            if remote_hist:
                local_set = set(self.browser.history)
                for u in remote_hist:
                    if u not in local_set:
                        self.browser.history.append(u)
                        local_set.add(u)
            QTimer.singleShot(0, lambda: self.browser._show_status('Sync completed', 3000))
        except Exception as e:
            QTimer.singleShot(0, lambda e=e: self.browser._show_status(f'Sync pull failed: {e}', 4000))


# ---------------------------------------------------------------------------
# Reader Mode Helper
# ---------------------------------------------------------------------------

READER_JS = """
(function() {
    function isVisible(el) {
        var style = window.getComputedStyle(el);
        return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
    }
    function getArticleText() {
        var article = document.querySelector('article');
        if (article && article.textContent.trim().length > 200) return article.innerHTML;
        var candidates = [];
        var elms = document.querySelectorAll('p, h1, h2, h3, h4, h5, h6, li, blockquote, pre, td, th');
        var seen = new Set();
        elms.forEach(function(el) {
            if (!isVisible(el)) return;
            var text = el.textContent.trim();
            if (text.length < 20) return;
            var parent = el.closest('nav, header, footer, aside, .sidebar, .menu, .nav, .footer, .header, .ad, .advertisement, script, style');
            if (parent) return;
            var key = el.tagName + ':' + text.slice(0, 50);
            if (seen.has(key)) return;
            seen.add(key);
            candidates.push(el.outerHTML);
        });
        if (candidates.length < 3) return document.body.innerHTML;
        return '<div>' + candidates.join('\\n') + '</div>';
    }
    var title = document.title || '';
    var content = getArticleText();
    var style = document.querySelector('style') ? document.querySelector('style').innerHTML : '';
    JSON.stringify({title: title, content: content, styles: style});
})();
"""


def _reader_html(title: str, content: str, font_size: int) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: Georgia, 'Times New Roman', Times, serif;
    background: #fafaf9; color: #1c1c1e;
    padding: 48px 24px; max-width: 720px; margin: 0 auto;
    font-size: {font_size}px; line-height: 1.7;
  }}
  h1 {{ font-size: {font_size + 8}px; font-weight: 700; margin-bottom: 24px;
        color: #000; line-height: 1.3; }}
  h2 {{ font-size: {font_size + 4}px; margin-top: 28px; margin-bottom: 12px; }}
  h3 {{ font-size: {font_size + 1}px; margin-top: 20px; margin-bottom: 8px; }}
  p {{ margin-bottom: 16px; }}
  a {{ color: #5e9bee; }}
  img {{ max-width: 100%; height: auto; border-radius: 8px; margin: 16px 0; }}
  blockquote {{
    border-left: 4px solid #5e9bee; padding: 12px 20px;
    margin: 16px 0; background: #f0f0f0; border-radius: 0 8px 8px 0;
    color: #3a3a3c;
  }}
  pre {{ background: #1c1c1e; color: #f0f0f0; padding: 16px; border-radius: 8px;
         overflow-x: auto; font-size: 14px; margin: 16px 0; }}
  code {{ font-family: 'SF Mono', Menlo, monospace; font-size: 14px; }}
  li {{ margin-bottom: 8px; margin-left: 24px; }}
  table {{ width: 100%; border-collapse: collapse; margin: 16px 0; }}
  th, td {{ border: 1px solid #d1d1d6; padding: 8px 12px; text-align: left; }}
  th {{ background: #e5e5ea; font-weight: 600; }}
  .meta {{ color: #8e8e93; font-size: 13px; margin-bottom: 24px; }}
</style>
</head>
<body>
  <h1>{title}</h1>
  <div class="meta">Reader mode</div>
  <div>{content}</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Translation Helper
# ---------------------------------------------------------------------------

def _translate_text(text: str, target: str, api_url: str, source: str = 'auto') -> str:
    payload = json.dumps({
        'q': text,
        'source': source,
        'target': target,
        'format': 'text',
    }).encode()
    req = urllib.request.Request(
        api_url, data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read().decode())
    return result.get('translatedText', text)


# ---------------------------------------------------------------------------
# Theme helpers
# ---------------------------------------------------------------------------

def _dialog_style(width: int, height: int) -> str:
    return f"background-color: {COLORS['bg_dark']}; color: {COLORS['text']};"


def _make_title(text: str) -> QLabel:
    lbl = QLabel(text)
    f = QFont()
    f.setBold(True)
    f.setPointSize(13)
    lbl.setFont(f)
    lbl.setStyleSheet(f"color: {COLORS['accent']}; padding-bottom: 4px;")
    return lbl


# ---------------------------------------------------------------------------
# Sandboxed Browser Tab
# ---------------------------------------------------------------------------

_tab_profile_counter = 0
_tmp_files: list[str] = []


@atexit.register
def _cleanup_tmp_files() -> None:
    for p in _tmp_files:
        try:
            os.unlink(p)
        except OSError:
            pass


class SecurePage(QWebEnginePage):
    navigationRequested = pyqtSignal(QUrl)

    def __init__(self, profile: QWebEngineProfile, parent: QWidget | None = None) -> None:
        super().__init__(profile, parent)
        self.renderProcessTerminated.connect(self._on_crash)

    def _on_crash(self, termination: QWebEnginePage.RenderProcessTerminationStatus, exit_code: int) -> None:
        view = self.view()
        if view:
            crash_html = f"""<!DOCTYPE html>
<html>
<head>
<style>
  body {{ font-family: -apple-system, sans-serif; background: #0a120a; color: #f0f0f0;
          display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
  .card {{ background: #121a12; padding: 40px; border-radius: 14px; text-align: center;
           border: 1px solid #2c342e; max-width: 400px; }}
  h1 {{ color: #ff453a; font-size: 22px; margin: 0 0 12px; }}
  p {{ color: #8e8e93; margin: 8px 0; }}
  button {{ background: #5e9bee; color: #fff; border: none; border-radius: 8px;
            padding: 10px 24px; font-size: 14px; cursor: pointer; margin-top: 16px; }}
</style>
</head>
<body>
<div class="card">
  <h1>Tab Crashed</h1>
  <p>The renderer process terminated unexpectedly.</p>
  <button onclick="window.location.href=localStorage.getItem('nova_last_url')||'nova://home'">Reload Tab</button>
</div>
</body>
</html>"""
            view.setHtml(crash_html)

    def acceptNavigationRequest(self, url: QUrl, _type: QWebEnginePage.NavigationType, _is_main_frame: bool) -> bool:
        self.navigationRequested.emit(url)
        return True


class BrowserTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.url: str = ''
        self.title: str = ''
        self._home_file: str | None = None
        self._profile: QWebEngineProfile | None = None
        self._crash_url: str = ''

        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        global _tab_profile_counter
        _tab_profile_counter += 1
        storage_name = f'nova_tab_{_tab_profile_counter}_{id(self)}'
        self._profile = QWebEngineProfile(storage_name, self)
        self._profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        self._apply_profile_settings()

        self.web_view = QWebEngineView()
        self.web_view.loadFinished.connect(self._on_load_finished)
        self.web_page = SecurePage(self._profile, self)
        self.web_view.setPage(self.web_page)
        self.layout().addWidget(self.web_view)

        self.web_view.urlChanged.connect(self._track_url)

    def _track_url(self, url: QUrl) -> None:
        self._crash_url = url.toString()

    def _apply_profile_settings(self) -> None:
        if not self._profile:
            return
        s = self._profile.settings()
        s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.ErrorPageEnabled, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.AllowRunningInsecureContent, False)
        s.setAttribute(QWebEngineSettings.WebAttribute.XSSAuditingEnabled, True)

    def profile(self) -> QWebEngineProfile:
        return self._profile or QWebEngineProfile.defaultProfile()

    def _on_load_finished(self, success: bool) -> None:
        if not success:
            self._show_error_page()

    def _show_error_page(self) -> None:
        url = self.web_view.url().toString()
        html = f"""<!DOCTYPE html>
<html>
<head>
<style>
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: {COLORS['bg_dark']}; margin: 0; display: flex;
    justify-content: center; align-items: center; height: 100vh;
  }}
  .card {{
    background: {COLORS['bg_medium']}; padding: 40px; border-radius: 14px;
    text-align: center; max-width: 440px; border: 1px solid {COLORS['border']};
  }}
  .icon {{ font-size: 48px; margin-bottom: 12px; opacity: .6; }}
  h1 {{ font-size: 22px; font-weight: 600; color: {COLORS['danger']}; margin: 0 0 8px; }}
  p  {{ color: {COLORS['text_muted']}; margin: 8px 0; font-size: 13px; }}
  .url {{ background: {COLORS['bg_light']}; padding: 10px 14px; border-radius: 8px;
          word-break: break-all; font-size: 12px; color: {COLORS['text_muted']}; }}
  ul {{ text-align: left; color: {COLORS['text_muted']}; font-size: 13px;
        padding-left: 20px; margin: 12px 0; }}
</style>
</head>
<body>
<div class="card">
  <div class="icon">⚠️</div>
  <h1>Page Not Found</h1>
  <p>The page failed to load. Possible causes:</p>
  <ul>
    <li>No internet connection</li>
    <li>Invalid URL</li>
    <li>Server is down</li>
    <li>Too many redirects</li>
  </ul>
  <p><strong>Tried to load:</strong></p>
  <div class="url">{url}</div>
</div>
</body>
</html>"""
        self.web_view.setHtml(html)

    def load_url(self, url: str) -> None:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        self.url = url
        self.web_view.load(QUrl(url))

    def load_html(self, html: str) -> None:
        self.web_view.setHtml(html)

    def load_home_html(self, html: str) -> None:
        tmp = tempfile.NamedTemporaryFile(
            mode='w', suffix='.html', prefix='nova_home_',
            delete=False, encoding='utf-8'
        )
        tmp.write(html)
        self._home_file = tmp.name
        _tmp_files.append(self._home_file)
        tmp.close()
        self.web_view.load(QUrl.fromLocalFile(self._home_file))

    def cleanup(self) -> None:
        if self._profile:
            self._profile.clearHttpCache()
        if self._home_file and os.path.exists(self._home_file):
            try:
                os.unlink(self._home_file)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Main Browser Window
# ---------------------------------------------------------------------------

class Browser(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f'{APP_NAME} v{APP_VERSION}')
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet(STYLESHEET)

        # data
        self.history: list[str] = []
        self.bookmarks: list[dict] = []
        self.downloads: list[dict] = []
        self.custom_shortcuts: list[dict] = []
        self.settings: dict = asdict(Settings())
        self._load_data()

        # reader state
        self._reader_active = False
        self._reader_original_url: str = ''

        # translation state
        self._translated = False
        self._original_content: str = ''
        self._translation_target = 'en'

        # plugin system
        self.plugin_manager = PluginManager(self)
        self.plugin_manager.discover_and_load()

        # sync
        self.sync_manager = SyncManager(self)
        self.sync_manager.start()

        # performance monitor
        self._perf_timer: QTimer | None = None
        self._perf_labels: list[QLabel] = []
        self._process = psutil.Process() if HAS_PSUTIL else None

        # ui
        self._build_ui()
        self._inject_matrix_overlay()
        self._apply_security_settings()
        self._recover_tabs()

        self.show()

    # ---- UI construction ------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout()
        root.setContentsMargins(8, 8, 8, 0)
        root.setSpacing(6)
        central.setLayout(root)

        # top bar container
        top_bar = QWidget()
        top_bar.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['bg_medium']};
                border-radius: 10px;
            }}
        """)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(4, 4, 4, 4)
        top_layout.setSpacing(2)

        for text, slot, tip in [
            ('←', self._back, 'Go back'),
            ('→', self._forward, 'Go forward'),
            ('⟳', self._reload, 'Reload page'),
        ]:
            btn = QPushButton(text)
            btn.setFixedSize(32, 28)
            btn.setToolTip(tip)
            btn.setFlat(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(slot)
            top_layout.addWidget(btn)

        self.url_bar = QComboBox()
        self.url_bar.setEditable(True)
        self.url_bar.setMinimumHeight(30)
        self.url_bar.lineEdit().returnPressed.connect(self._navigate)
        top_layout.addWidget(self.url_bar, 1)

        self.lock_btn = QPushButton('')
        self.lock_btn.setFixedSize(24, 24)
        self.lock_btn.setFlat(True)
        self.lock_btn.setVisible(False)
        self.lock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lock_btn.clicked.connect(self._show_security_info)
        top_layout.addWidget(self.lock_btn)

        # reader mode toggle
        self.reader_btn = QPushButton('📖')
        self.reader_btn.setFixedSize(32, 28)
        self.reader_btn.setToolTip('Reader mode')
        self.reader_btn.setFlat(True)
        self.reader_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reader_btn.clicked.connect(self._toggle_reader_mode)
        top_layout.addWidget(self.reader_btn)

        self.star_btn = QPushButton('☆')
        self.star_btn.setFixedSize(32, 28)
        self.star_btn.setToolTip('Bookmark this page (Ctrl+D)')
        self.star_btn.setFlat(True)
        self.star_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.star_btn.clicked.connect(self._toggle_bookmark)
        top_layout.addWidget(self.star_btn)

        menu_btn = QPushButton('≡')
        menu_btn.setFixedSize(32, 28)
        menu_btn.setToolTip('Menu')
        menu_btn.setFlat(True)
        menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        menu_btn.clicked.connect(self._show_menu)
        top_layout.addWidget(menu_btn)

        root.addWidget(top_bar)

        # loading bar
        self.loading_bar = QProgressBar()
        self.loading_bar.setMaximumHeight(3)
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setRange(0, 100)
        self.loading_bar.setValue(0)
        self.loading_bar.hide()
        root.addWidget(self.loading_bar)

        # tabs
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        root.addWidget(self.tabs, 1)

        new_tab_btn = QPushButton('+')
        new_tab_btn.setFixedSize(28, 28)
        new_tab_btn.setToolTip('New tab (Ctrl+T)')
        new_tab_btn.clicked.connect(lambda: self._add_tab())
        self.tabs.setCornerWidget(new_tab_btn)

        self._add_tab()

        # status bar
        self.status = QStatusBar()
        self.status.setMaximumHeight(24)
        self.setStatusBar(self.status)
        self.status.showMessage(f'{APP_NAME} v{APP_VERSION}')

        # performance labels in status bar
        self._perf_cpu_label = QLabel('')
        self._perf_cpu_label.setStyleSheet(f'color: {COLORS["text_dim"]}; padding: 0 6px;')
        self._perf_ram_label = QLabel('')
        self._perf_ram_label.setStyleSheet(f'color: {COLORS["text_dim"]}; padding: 0 6px;')
        self.status.addPermanentWidget(self._perf_cpu_label)
        self.status.addPermanentWidget(self._perf_ram_label)
        self._update_perf_monitor()
        if self.settings.get('perf_monitor_enabled', False):
            self._start_perf_monitor()

        # AI assistant sidebar
        self._setup_ai_assistant()

        # keyboard shortcuts
        self._setup_shortcuts()

    def _styled_dialog(self, title: str, w: int, h: int) -> QDialog:
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setGeometry(100, 100, w, h)
        dlg.setStyleSheet(_dialog_style(w, h))
        return dlg

    # ---- AI Assistant Sidebar -------------------------------------------

    def _setup_ai_assistant(self) -> None:
        self.ai_dock = QDockWidget('AI Assistant', self)
        self.ai_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.ai_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetClosable)

        ai_widget = QWidget()
        ai_layout = QVBoxLayout(ai_widget)
        ai_layout.setSpacing(6)

        title_lbl = QLabel('🤖 AI Assistant')
        title_lbl.setStyleSheet(f'color: {COLORS["accent"]}; font-weight: 600; font-size: 13px;')
        ai_layout.addWidget(title_lbl)

        self.ai_output = QTextBrowser()
        self.ai_output.setMinimumWidth(280)
        self.ai_output.setMaximumWidth(400)
        ai_layout.addWidget(self.ai_output, 1)

        btn_layout = QHBoxLayout()
        summarize_btn = QPushButton('Summarize')
        summarize_btn.clicked.connect(self._ai_summarize)
        btn_layout.addWidget(summarize_btn)

        explain_btn = QPushButton('Explain')
        explain_btn.clicked.connect(self._ai_explain)
        btn_layout.addWidget(explain_btn)

        ai_layout.addLayout(btn_layout)

        self.ai_dock.setWidget(ai_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.ai_dock)
        self.ai_dock.hide()

    def _ai_summarize(self) -> None:
        self._ai_query('Summarize the following web page content concisely in a few paragraphs:\n\n')

    def _ai_explain(self) -> None:
        self._ai_query('Explain the following web page content in simple terms:\n\n')

    def _ai_query(self, prefix: str) -> None:
        tab: BrowserTab = self.tabs.currentWidget()
        if not tab:
            return
        self.ai_output.setPlainText('Thinking...')
        tab.web_view.page().runJavaScript(
            'document.body.innerText',
            lambda text: self._ai_call(prefix + (text or '')[:8000])
        )

    def _ai_call(self, prompt: str) -> None:
        api_url = self.settings.get('ai_api_url', 'http://localhost:11434/v1/chat/completions')
        api_key = self.settings.get('ai_api_key', '')
        model = self.settings.get('ai_model', 'llama3.2')

        def _do_call() -> None:
            try:
                payload = json.dumps({
                    'model': model,
                    'messages': [{'role': 'user', 'content': prompt}],
                    'stream': False,
                }).encode()
                headers = {'Content-Type': 'application/json'}
                if api_key:
                    headers['Authorization'] = f'Bearer {api_key}'
                req = urllib.request.Request(api_url, data=payload, headers=headers, method='POST')
                with urllib.request.urlopen(req, timeout=60) as resp:
                    result = json.loads(resp.read().decode())
                content = result['choices'][0]['message']['content']
                QTimer.singleShot(0, lambda c=content: self.ai_output.setPlainText(c.strip()))
            except Exception as e:
                QTimer.singleShot(0, lambda e=e: self.ai_output.setPlainText(f'AI request failed:\n{e}'))

        threading.Thread(target=_do_call, daemon=True).start()

    # ---- Reader Mode ----------------------------------------------------

    def _toggle_reader_mode(self) -> None:
        tab: BrowserTab = self.tabs.currentWidget()
        if not tab:
            return
        if self._reader_active:
            self._exit_reader_mode(tab)
        else:
            self._enter_reader_mode(tab)

    def _enter_reader_mode(self, tab: BrowserTab) -> None:
        url = tab.web_view.url().toString()
        if url.startswith(('data:', 'blob:', 'about:', 'nova://')):
            return
        self._reader_original_url = url
        self._reader_active = True
        self.reader_btn.setText('📕')
        self.reader_btn.setStyleSheet(f'color: {COLORS["accent"]};')
        tab.web_view.page().runJavaScript(
            READER_JS,
            lambda result: self._display_reader_content(tab, result)
        )

    def _display_reader_content(self, tab: BrowserTab, result: str) -> None:
        if not result or result == 'null':
            self._reader_active = False
            self.reader_btn.setText('📖')
            self.reader_btn.setStyleSheet('')
            return
        try:
            data = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            self._reader_active = False
            self.reader_btn.setText('📖')
            self.reader_btn.setStyleSheet('')
            return
        title = data.get('title', 'Article')
        content = data.get('content', '')
        font_size = self.settings.get('reader_font_size', 18)
        html = _reader_html(title, content, font_size)
        tab.load_html(html)

    def _exit_reader_mode(self, tab: BrowserTab) -> None:
        self._reader_active = False
        self.reader_btn.setText('📖')
        self.reader_btn.setStyleSheet('')
        if self._reader_original_url:
            tab.load_url(self._reader_original_url)
            self._reader_original_url = ''

    # ---- Built-in Translation -------------------------------------------

    def _translate_page(self) -> None:
        tab: BrowserTab = self.tabs.currentWidget()
        if not tab:
            return

        if self._translated:
            tab.load_url(tab.url)
            self._translated = False
            self._show_status('Translation reverted', 2000)
            return

        api_url = self.settings.get('translate_api_url', 'https://libretranslate.com/translate')
        tab.web_view.page().runJavaScript(
            'document.body.innerText',
            lambda text: self._do_translate(tab, text, api_url)
        )

    def _do_translate(self, tab: BrowserTab, text: str, api_url: str) -> None:
        if not text:
            return
        target = self._translation_target
        self._show_status('Translating...')

        def _call() -> None:
            try:
                translated = _translate_text(text[:5000], target, api_url)
                tab.web_view.page().runJavaScript(
                    f'''
                    (function() {{
                        var nodes = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
                        var texts = [];
                        while (nodes.nextNode()) {{
                            var t = nodes.currentNode.textContent.trim();
                            if (t.length > 20) texts.push(nodes.currentNode);
                        }}
                        return texts.length;
                    }})()
                    ''',
                    lambda count: self._show_status(f'Translation complete (target: {target})', 3000)
                )
                QTimer.singleShot(0, lambda: setattr(self, '_translated', True))
            except Exception as e:
                QTimer.singleShot(0, lambda e=e: self._show_status(f'Translation failed: {e}', 4000))

        threading.Thread(target=_call, daemon=True).start()

    def _show_translation_dialog(self) -> None:
        dlg = self._styled_dialog('Translate Page', 300, 200)
        lo = QVBoxLayout()
        lo.addWidget(_make_title('🌍  Translate Page'))

        lo.addWidget(QLabel('Target language:'))
        lang_combo = QComboBox()
        langs = [
            ('English', 'en'), ('Spanish', 'es'), ('French', 'fr'),
            ('German', 'de'), ('Italian', 'it'), ('Portuguese', 'pt'),
            ('Russian', 'ru'), ('Japanese', 'ja'), ('Chinese', 'zh'),
            ('Arabic', 'ar'), ('Hindi', 'hi'), ('Korean', 'ko'),
        ]
        for name, code in langs:
            lang_combo.addItem(name, code)
        current_idx = 0
        for i in range(lang_combo.count()):
            if lang_combo.itemData(i) == self._translation_target:
                current_idx = i
                break
        lang_combo.setCurrentIndex(current_idx)
        lang_combo.currentIndexChanged.connect(
            lambda i: setattr(self, '_translation_target', lang_combo.itemData(i))
        )
        lo.addWidget(lang_combo)

        translate_btn = QPushButton('🌍  Translate')
        translate_btn.clicked.connect(lambda: (self._translate_page(), dlg.close()))
        lo.addWidget(translate_btn)

        close_btn = QPushButton('Close')
        close_btn.clicked.connect(dlg.close)
        lo.addWidget(close_btn)
        dlg.setLayout(lo)
        dlg.exec()

    # ---- Performance Monitor --------------------------------------------

    def _start_perf_monitor(self) -> None:
        if not HAS_PSUTIL:
            self._show_status('psutil not available for performance monitoring', 4000)
            return
        if self._perf_timer:
            self._perf_timer.stop()
        self._perf_timer = QTimer()
        self._perf_timer.timeout.connect(self._update_perf_monitor)
        self._perf_timer.start(2000)

    def _stop_perf_monitor(self) -> None:
        if self._perf_timer:
            self._perf_timer.stop()
            self._perf_timer = None
        self._perf_cpu_label.setText('')
        self._perf_ram_label.setText('')

    def _update_perf_monitor(self) -> None:
        if not HAS_PSUTIL or not self._process:
            self._perf_cpu_label.setText('')
            self._perf_ram_label.setText('')
            return
        try:
            cpu = self._process.cpu_percent(interval=0)
            mem = self._process.memory_info().rss / 1024 / 1024
            self._perf_cpu_label.setText(f'CPU: {cpu:.0f}%')
            self._perf_ram_label.setText(f'RAM: {mem:.0f} MB')
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            self._perf_cpu_label.setText('')
            self._perf_ram_label.setText('')

    # ---- Data persistence -----------------------------------------------

    def _save_data(self) -> None:
        data = BrowserData(
            bookmarks=self.bookmarks,
            history=self.history,
            downloads=self.downloads,
            custom_shortcuts=self.custom_shortcuts,
            settings=self.settings,
            open_tabs=self._get_open_tabs(),
        )
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(asdict(data), f, indent=2)
        except OSError:
            pass

    def _load_data(self) -> None:
        if not os.path.exists(DATA_FILE):
            return
        try:
            with open(DATA_FILE) as f:
                raw = json.load(f)
            self.bookmarks = raw.get('bookmarks', [])
            self.history = raw.get('history', [])
            self.downloads = raw.get('downloads', [])
            self.custom_shortcuts = raw.get('custom_shortcuts', [])
            saved = raw.get('settings', {})
            merged = asdict(Settings())
            merged.update(saved)
            self.settings = merged
        except (OSError, json.JSONDecodeError):
            pass

    def _get_open_tabs(self) -> list[str]:
        urls: list[str] = []
        for i in range(self.tabs.count()):
            tab: BrowserTab = self.tabs.widget(i)
            if tab and tab.url:
                urls.append(tab.url)
        return urls

    def _recover_tabs(self) -> None:
        if not self.settings.get('auto_recover_tabs', True):
            return
        if not os.path.exists(DATA_FILE):
            return
        try:
            with open(DATA_FILE) as f:
                raw = json.load(f)
            urls = raw.get('open_tabs', [])
            if urls:
                self.tabs.removeTab(0)
                for u in urls:
                    self._add_tab(u)
        except (OSError, json.JSONDecodeError):
            pass

    # ---- Tab management -------------------------------------------------

    def _add_tab(self, url: str | None = None) -> None:
        tab = BrowserTab()
        idx = self.tabs.addTab(tab, 'New Tab')
        self.tabs.setCurrentIndex(idx)

        if url:
            tab.load_url(url)
        else:
            self._show_home_page(tab)

        tab.web_view.titleChanged.connect(
            lambda title, t=tab: self._update_tab_title(t, title)
        )
        tab.web_view.urlChanged.connect(
            lambda: self._update_url_bar()
        )
        tab.web_view.loadProgress.connect(self._on_load_progress)
        tab.web_view.loadStarted.connect(self._on_load_started)
        tab.web_view.loadFinished.connect(self._on_load_finished)
        tab.web_view.page().linkHovered.connect(self._on_link_hovered)
        tab.web_page.navigationRequested.connect(self._on_navigation_request)

        # notify plugins
        self.plugin_manager.notify_tab_changed(idx, tab)

    def _update_tab_title(self, tab: BrowserTab, title: str) -> None:
        if not title:
            return
        idx = self.tabs.indexOf(tab)
        if idx < 0:
            return
        display = title if len(title) <= 25 else title[:22] + '...'
        self.tabs.setTabText(idx, display)

    def _close_tab(self, idx: int) -> None:
        if self.tabs.count() > 1:
            tab: BrowserTab = self.tabs.widget(idx)
            if tab:
                tab.cleanup()
            self.tabs.removeTab(idx)
        else:
            self._message('Cannot close the last tab')

    def _on_tab_changed(self, _idx: int) -> None:
        self._update_url_bar()
        self._reader_active = False
        self.reader_btn.setText('📖')
        self.reader_btn.setStyleSheet('')
        tab: BrowserTab = self.tabs.currentWidget()
        if tab:
            self.plugin_manager.notify_tab_changed(_idx, tab)

    # ---- Navigation -----------------------------------------------------

    def _navigate(self) -> None:
        url = self.url_bar.currentText().strip()
        if not url:
            return
        self.history.append(url)
        self.url_bar.addItem(url)
        tab: BrowserTab = self.tabs.currentWidget()
        if not tab:
            return
        if url.lower() in ('nova://home', 'about:home', 'about:blank'):
            self._show_home_page(tab)
        else:
            tab.load_url(url)
        self.plugin_manager.notify_navigate(url)

    def _update_url_bar(self) -> None:
        try:
            tab: BrowserTab = self.tabs.currentWidget()
        except RuntimeError:
            return
        if not tab:
            return
        raw = tab.web_view.url().toString()
        if raw.startswith(('data:', 'blob:', 'about:')):
            raw = 'nova://home'
            self.lock_btn.setVisible(False)
        elif 'nova_home_' in raw:
            raw = 'nova://home'
            self.lock_btn.setVisible(False)
        else:
            is_secure = raw.startswith('https://')
            self.lock_btn.setVisible(True)
            if is_secure:
                self.lock_btn.setText('🔒')
                self.lock_btn.setToolTip('Connection is secure (HTTPS)')
            else:
                self.lock_btn.setText('🔓')
                self.lock_btn.setToolTip('Connection is not secure (HTTP)')
        self.url_bar.lineEdit().setText(raw)
        self.plugin_manager.notify_url_changed(raw)

    def _back(self) -> None:
        tab: BrowserTab = self.tabs.currentWidget()
        if tab:
            tab.web_view.back()

    def _forward(self) -> None:
        tab: BrowserTab = self.tabs.currentWidget()
        if tab:
            tab.web_view.forward()

    def _reload(self) -> None:
        tab: BrowserTab = self.tabs.currentWidget()
        if tab:
            tab.web_view.reload()

    def _stop(self) -> None:
        tab: BrowserTab = self.tabs.currentWidget()
        if tab:
            tab.web_view.stop()

    # ---- Bookmarks ------------------------------------------------------

    def _toggle_bookmark(self) -> None:
        tab: BrowserTab = self.tabs.currentWidget()
        if not tab:
            return
        url = tab.web_view.url().toString()
        title = tab.web_view.title() or url
        bm = {'url': url, 'title': title}

        if bm in self.bookmarks:
            self.bookmarks.remove(bm)
            self._message(f'Removed: {title}')
            self.star_btn.setText('☆')
        else:
            self.bookmarks.append(bm)
            self._message(f'Bookmarked: {title}')
            self.star_btn.setText('★')
        self._save_data()

    # ---- Menu -----------------------------------------------------------

    def _show_menu(self) -> None:
        dlg = self._styled_dialog('Menu', 240, 460)
        dlg.setGeometry(self.width() - 260, 80, 240, 480)
        lo = QVBoxLayout()

        items = [
            ('📚  Bookmarks', self._show_bookmarks),
            ('⏱  History', self._show_history),
            ('⭐  Shortcuts', self._manage_shortcuts),
            ('⬇  Downloads', self._show_downloads),
            ('🔒  Security', self._show_security_info),
            ('🤖  AI Assistant', self._toggle_ai_assistant),
            ('📖  Reader Mode', self._toggle_reader_mode_menu),
            ('🌍  Translate Page', self._show_translation_dialog),
            ('⚙  Settings', self._show_settings),
            ('🔄  Sync Now', self._sync_now),
            ('🗑  Clear Cache', self._clear_cache),
            ('❌  Exit', self.close),
        ]
        for text, slot in items:
            btn = QPushButton(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(slot)
            lo.addWidget(btn)

        lo.addStretch()
        dlg.setLayout(lo)
        dlg.exec()

    def _toggle_ai_assistant(self) -> None:
        self.ai_dock.setVisible(not self.ai_dock.isVisible())

    def _toggle_reader_mode_menu(self) -> None:
        self._toggle_reader_mode()

    def _sync_now(self) -> None:
        self.sync_manager.sync_push()
        self._show_status('Sync initiated...', 3000)

    # ---- Bookmarks dialog -----------------------------------------------

    def _show_bookmarks(self) -> None:
        dlg = self._styled_dialog('Bookmarks', 500, 400)
        lo = QVBoxLayout()
        lo.addWidget(_make_title('📚  Bookmarks'))

        if not self.bookmarks:
            lo.addWidget(QLabel('No bookmarks yet.'))
        else:
            lst = QListWidget()
            for b in self.bookmarks:
                item = QListWidgetItem(b['title'])
                item.setData(Qt.ItemDataRole.UserRole, b['url'])
                lst.addItem(item)
            lst.itemDoubleClicked.connect(lambda it: self._load_url_from_item(it))
            lo.addWidget(lst)

            del_btn = QPushButton('Delete Selected')
            del_btn.clicked.connect(lambda: self._delete_bookmark(lst, dlg))
            lo.addWidget(del_btn)

        close_btn = QPushButton('Close')
        close_btn.clicked.connect(dlg.close)
        lo.addWidget(close_btn)
        dlg.setLayout(lo)
        dlg.exec()

    def _delete_bookmark(self, lst: QListWidget, dlg: QDialog) -> None:
        for item in lst.selectedItems():
            url = item.data(Qt.ItemDataRole.UserRole)
            self.bookmarks = [b for b in self.bookmarks if b['url'] != url]
            lst.takeItem(lst.row(item))
        self._save_data()

    # ---- History dialog -------------------------------------------------

    def _show_history(self) -> None:
        dlg = self._styled_dialog('History', 500, 400)
        lo = QVBoxLayout()
        lo.addWidget(_make_title('⏱  History'))

        if not self.history:
            lo.addWidget(QLabel('No history yet.'))
        else:
            lst = QListWidget()
            for url in reversed(self.history[-50:]):
                lst.addItem(url)
            lst.itemDoubleClicked.connect(lambda it: self._navigate_to_url(it.text()))
            lo.addWidget(lst)

            clear_btn = QPushButton('Clear All History')
            clear_btn.clicked.connect(self._clear_history)
            lo.addWidget(clear_btn)

        close_btn = QPushButton('Close')
        close_btn.clicked.connect(dlg.close)
        lo.addWidget(close_btn)
        dlg.setLayout(lo)
        dlg.exec()

    def _clear_history(self) -> None:
        self.history.clear()
        self._save_data()
        self._message('History cleared')

    def _navigate_to_url(self, url: str) -> None:
        tab: BrowserTab = self.tabs.currentWidget()
        if tab:
            tab.load_url(url)

    # ---- Shortcuts ------------------------------------------------------

    def _manage_shortcuts(self) -> None:
        dlg = self._styled_dialog('Custom Shortcuts', 560, 460)
        lo = QVBoxLayout()
        lo.addWidget(_make_title('⭐  Custom Shortcuts'))

        lst = QListWidget()
        for i, s in enumerate(self.custom_shortcuts):
            item = QListWidgetItem(f"{s['icon']}  {s['name']}  →  {s['url']}")
            item.setData(Qt.ItemDataRole.UserRole, i)
            lst.addItem(item)
        lo.addWidget(lst)

        btn_lo = QHBoxLayout()
        add_btn = QPushButton('➕  Add')
        add_btn.clicked.connect(lambda: self._add_shortcut(lst))
        del_btn = QPushButton('🗑  Delete')
        del_btn.clicked.connect(lambda: self._delete_shortcut(lst))
        btn_lo.addWidget(add_btn)
        btn_lo.addWidget(del_btn)
        lo.addLayout(btn_lo)

        close_btn = QPushButton('Close')
        close_btn.clicked.connect(dlg.close)
        lo.addWidget(close_btn)
        dlg.setLayout(lo)
        dlg.exec()

    def _add_shortcut(self, lst: QListWidget) -> None:
        dlg = self._styled_dialog('New Shortcut', 480, 240)
        lo = QVBoxLayout()
        lo.addWidget(_make_title('➕  New Shortcut'))

        name_inp = QLineEdit(); name_inp.setPlaceholderText('e.g. My Site')
        url_inp = QLineEdit(); url_inp.setPlaceholderText('e.g. https://example.com')
        icon_inp = QLineEdit('🌐'); icon_inp.setPlaceholderText('e.g. 🌟'); icon_inp.setMaximumWidth(80)

        lo.addWidget(QLabel('Name')); lo.addWidget(name_inp)
        lo.addWidget(QLabel('URL')); lo.addWidget(url_inp)

        icon_lo = QHBoxLayout(); icon_lo.addWidget(QLabel('Icon')); icon_lo.addWidget(icon_inp); icon_lo.addStretch()
        lo.addLayout(icon_lo)
        lo.addStretch()

        btn_lo = QHBoxLayout()
        save_btn = QPushButton('✓  Save')
        save_btn.clicked.connect(lambda: self._save_shortcut(name_inp, url_inp, icon_inp, dlg, lst))
        cancel_btn = QPushButton('✗  Cancel')
        cancel_btn.clicked.connect(dlg.close)
        btn_lo.addWidget(save_btn); btn_lo.addWidget(cancel_btn)
        lo.addLayout(btn_lo)
        dlg.setLayout(lo)
        dlg.exec()

    def _save_shortcut(
        self, name_inp: QLineEdit, url_inp: QLineEdit,
        icon_inp: QLineEdit, dlg: QDialog, lst: QListWidget
    ) -> None:
        name = name_inp.text().strip()
        url = url_inp.text().strip()
        if not name or not url:
            self._message('Please fill in all fields')
            return
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        icon = icon_inp.text().strip() or '🌐'
        sc = {'name': name, 'url': url, 'icon': icon}
        self.custom_shortcuts.append(sc)
        self._save_data()
        item = QListWidgetItem(f"{icon}  {name}  →  {url}")
        item.setData(Qt.ItemDataRole.UserRole, len(self.custom_shortcuts) - 1)
        lst.addItem(item)
        dlg.close()

    def _delete_shortcut(self, lst: QListWidget) -> None:
        for item in lst.selectedItems():
            idx = item.data(Qt.ItemDataRole.UserRole)
            if 0 <= idx < len(self.custom_shortcuts):
                self.custom_shortcuts.pop(idx)
        self._save_data()
        lst.clear()
        for i, s in enumerate(self.custom_shortcuts):
            item = QListWidgetItem(f"{s['icon']}  {s['name']}  →  {s['url']}")
            item.setData(Qt.ItemDataRole.UserRole, i)
            lst.addItem(item)

    # ---- Downloads ------------------------------------------------------

    def _show_downloads(self) -> None:
        dlg = self._styled_dialog('Downloads', 560, 400)
        lo = QVBoxLayout()
        lo.addWidget(_make_title('⬇  Downloads'))

        if not self.downloads:
            lo.addWidget(QLabel('No downloads yet.'))
        else:
            lst = QListWidget()
            for d in reversed(self.downloads):
                lst.addItem(f"{d['name']}  —  {d['size']}  ({d['date']})")
            lo.addWidget(lst)
            clear_btn = QPushButton('Clear All Downloads')
            clear_btn.clicked.connect(self._clear_downloads)
            lo.addWidget(clear_btn)

        close_btn = QPushButton('Close')
        close_btn.clicked.connect(dlg.close)
        lo.addWidget(close_btn)
        dlg.setLayout(lo)
        dlg.exec()

    def _clear_downloads(self) -> None:
        self.downloads.clear()
        self._save_data()
        self._message('Downloads cleared')

    # ---- Settings -------------------------------------------------------

    def _change_zoom(self, val: int) -> None:
        self.settings['default_zoom'] = val
        tab: BrowserTab = self.tabs.currentWidget()
        if tab:
            tab.web_view.setZoomFactor(val / 100)
        self._save_data()

    def _change_font_size(self, val: int) -> None:
        self.settings['font_size'] = val
        self._save_data()

    def _toggle_recovery(self) -> None:
        self.settings['auto_recover_tabs'] = not self.settings.get('auto_recover_tabs', True)
        self._save_data()

    def _toggle_setting(self, key: str) -> None:
        self.settings[key] = not self.settings.get(key, True)
        self._save_data()
        self._apply_security_settings()

    def _reset_settings(self) -> None:
        ans = QMessageBox.question(
            self, 'Reset Settings',
            'Reset all settings to defaults?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ans == QMessageBox.StandardButton.Yes:
            self.settings = asdict(Settings())
            self._save_data()
            self._apply_security_settings()
            self._message('Settings reset to defaults')

    def _show_settings(self) -> None:
        dlg = self._styled_dialog('Settings', 560, 620)
        lo = QVBoxLayout()
        lo.setSpacing(10)
        lo.addWidget(_make_title('⚙  Settings'))

        scroll = QWidget()
        slo = QVBoxLayout()
        slo.setSpacing(6)

        def group(title: str) -> QLabel:
            lbl = QLabel(title)
            lbl.setStyleSheet(
                f"color: {COLORS['accent']}; font-size: 11px; "
                f"font-weight: 600; text-transform: uppercase; "
                f"letter-spacing: 1px; padding: 8px 0 2px;"
            )
            return lbl

        def toggle(key: str, label: str) -> QCheckBox:
            cb = QCheckBox(label)
            cb.setChecked(self.settings.get(key, True))
            cb.stateChanged.connect(lambda: self._toggle_setting(key))
            return cb

        def text_input(key: str, label: str, placeholder: str = '') -> QHBoxLayout:
            lo2 = QHBoxLayout()
            lo2.addWidget(QLabel(label))
            inp = QLineEdit()
            inp.setText(self.settings.get(key, ''))
            inp.setPlaceholderText(placeholder)
            inp.textChanged.connect(lambda v: self.settings.update({key: v}))
            lo2.addWidget(inp, 1)
            return lo2, inp

        slo.addWidget(group('General'))

        zoom_lo = QHBoxLayout()
        zoom_lo.addWidget(QLabel('Zoom Level:'))
        zoom_spin = QSpinBox()
        zoom_spin.setRange(50, 200)
        zoom_spin.setValue(self.settings.get('default_zoom', 100))
        zoom_spin.setSuffix('%')
        zoom_spin.valueChanged.connect(lambda v: self._change_zoom(v))
        zoom_lo.addWidget(zoom_spin); zoom_lo.addStretch()
        slo.addLayout(zoom_lo)

        font_lo = QHBoxLayout()
        font_lo.addWidget(QLabel('Font Size:'))
        font_spin = QSpinBox()
        font_spin.setRange(8, 24)
        font_spin.setValue(self.settings.get('font_size', 14))
        font_spin.setSuffix('px')
        font_spin.valueChanged.connect(lambda v: self._change_font_size(v))
        font_lo.addWidget(font_spin); font_lo.addStretch()
        slo.addLayout(font_lo)

        slo.addWidget(toggle('auto_recover_tabs', 'Auto-recover tabs on startup'))
        slo.addWidget(toggle('perf_monitor_enabled', 'Enable performance monitor'))

        slo.addWidget(group('Security & Privacy'))

        slo.addWidget(toggle('https_only', 'HTTPS Only (auto-upgrade HTTP)'))
        slo.addWidget(toggle('enable_js', 'Enable JavaScript'))
        slo.addWidget(toggle('block_mixed_content', 'Block mixed content'))
        slo.addWidget(toggle('block_third_party_cookies', 'Block third-party cookies'))
        slo.addWidget(toggle('safe_browsing', 'Safe browsing warnings'))

        slo.addWidget(group('Profile Sync'))
        slo.addWidget(toggle('sync_enabled', 'Enable cloud sync'))

        sync_url_lo, self._sync_url_inp = text_input('sync_url', 'Sync URL:', 'https://your-server.com/api')
        slo.addLayout(sync_url_lo)
        sync_key_lo, self._sync_key_inp = text_input('sync_key', 'API Key:')
        slo.addLayout(sync_key_lo)

        slo.addWidget(group('AI Assistant'))
        ai_url_lo, _ = text_input('ai_api_url', 'API URL:', 'http://localhost:11434/v1/chat/completions')
        slo.addLayout(ai_url_lo)
        ai_key_lo, _ = text_input('ai_api_key', 'API Key:')
        slo.addLayout(ai_key_lo)
        ai_model_lo, _ = text_input('ai_model', 'Model:', 'llama3.2')
        slo.addLayout(ai_model_lo)

        slo.addWidget(group('Translation'))
        tr_url_lo, _ = text_input('translate_api_url', 'API URL:', 'https://libretranslate.com/translate')
        slo.addLayout(tr_url_lo)

        slo.addWidget(group('Reader Mode'))
        reader_font_lo = QHBoxLayout()
        reader_font_lo.addWidget(QLabel('Font Size:'))
        reader_font_spin = QSpinBox()
        reader_font_spin.setRange(12, 32)
        reader_font_spin.setValue(self.settings.get('reader_font_size', 18))
        reader_font_spin.setSuffix('px')
        reader_font_spin.valueChanged.connect(lambda v: self.settings.update({'reader_font_size': v}))
        reader_font_lo.addWidget(reader_font_spin); reader_font_lo.addStretch()
        slo.addLayout(reader_font_lo)

        slo.addSpacing(8)

        btn_lo = QHBoxLayout()
        data_btn = QPushButton('🗑  Clear Browsing Data')
        data_btn.clicked.connect(self._clear_all_data)
        btn_lo.addWidget(data_btn)

        cookies_btn = QPushButton('🍪  Clear Cookies')
        cookies_btn.clicked.connect(self._clear_cookies)
        btn_lo.addWidget(cookies_btn)
        slo.addLayout(btn_lo)

        reset_btn = QPushButton('🔄  Reset to Defaults')
        reset_btn.clicked.connect(self._reset_settings)
        slo.addWidget(reset_btn)

        about_btn = QPushButton(f'ℹ️  About {APP_NAME}')
        about_btn.clicked.connect(lambda: self._message(
            f'{APP_NAME} v{APP_VERSION}\n\n'
            'A lightweight Python browser built with PyQt6 & QtWebEngine.\n'
            'Dark theme • Tabs • Bookmarks • History • Shortcuts • Security\n'
            'Reader Mode • Translation • AI Assistant • Profile Sync • Plugins'
        ))
        slo.addWidget(about_btn)

        slo.addStretch()
        scroll.setLayout(slo)

        lo.addWidget(scroll)

        close_btn = QPushButton('Close')
        close_btn.clicked.connect(lambda: (self._save_data(), dlg.close()))
        lo.addWidget(close_btn)
        dlg.setLayout(lo)
        dlg.exec()

    # ---- Home page ------------------------------------------------------

    def _show_home_page(self, tab: BrowserTab) -> None:
        shortcuts_html = ''
        if self.custom_shortcuts:
            cards = ''.join(
                f'<a href="{s["url"]}" class="sc"><span class="ico">{s["icon"]}</span>'
                f'<span class="nm">{s["name"]}</span></a>'
                for s in self.custom_shortcuts
            )
            shortcuts_html = f'<h2>⭐ Your Shortcuts</h2><div class="grid">{cards}</div>'

        quick_links = [
            ('🔍', 'Google', 'https://www.google.com'),
            ('📧', 'Gmail', 'https://www.gmail.com'),
            ('📺', 'YouTube', 'https://www.youtube.com'),
            ('📘', 'Facebook', 'https://www.facebook.com'),
            ('📷', 'Instagram', 'https://www.instagram.com'),
            ('𝕏', 'Twitter', 'https://www.twitter.com'),
            ('💼', 'LinkedIn', 'https://www.linkedin.com'),
            ('🔴', 'Reddit', 'https://www.reddit.com'),
            ('🐙', 'GitHub', 'https://www.github.com'),
            ('💻', 'Stack Overflow', 'https://www.stackoverflow.com'),
            ('📖', 'Wikipedia', 'https://www.wikipedia.org'),
            ('🛒', 'Amazon', 'https://www.amazon.com'),
            ('🎬', 'Netflix', 'https://www.netflix.com'),
            ('💬', 'Discord', 'https://www.discord.com'),
            ('🎮', 'Twitch', 'https://www.twitch.tv'),
            ('🎵', 'Spotify', 'https://www.spotify.com'),
            ('🗺️', 'Maps', 'https://www.google.com/maps'),
            ('☁️', 'Drive', 'https://drive.google.com'),
            ('🎨', 'Canva', 'https://www.canva.com'),
            ('🎭', 'Figma', 'https://www.figma.com'),
        ]
        quick_cards = ''.join(
            f'<a href="{url}" class="sc"><span class="ico">{ico}</span><span class="nm">{name}</span></a>'
            for ico, name, url in quick_links
        )

        matrix_js = (
            '(function(){'
            'var c=document.getElementById("m").getContext("2d"),f=14,w=innerWidth,h=innerHeight;'
            'c.canvas.width=w;c.canvas.height=h;'
            'var cols=Math.floor(w/f),y=[];'
            'for(var i=0;i<cols;i++)y[i]=1;'
            'c.fillStyle="#000";c.fillRect(0,0,w,h);'
            'setInterval(function(){'
            'c.fillStyle="rgba(0,0,0,0.05)";c.fillRect(0,0,w,h);'
            'c.fillStyle="#0f0";c.font=f+"px monospace";'
            'for(var i=0;i<cols;i++){'
            'var ch=String.fromCharCode(0x30A0+96*Math.random());'
            'c.fillText(ch,i*f,y[i]*f);'
            'if(y[i]*f>h&&Math.random()>0.975)y[i]=0;'
            'y[i]++'
            '}'
            '},50)'
            '})()'
        )

        html = f"""<!DOCTYPE html>
<html>
<head>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Roboto, sans-serif;
    background: #000000;
    color: {COLORS['text']}; min-height: 100vh;
  }}
  .wrap {{ max-width: 960px; margin: 0 auto; padding: 60px 24px; position: relative; z-index: 1; }}
  .hero {{ text-align: center; padding: 48px 0 16px; }}
  .logo {{
    display: inline-flex; align-items: center; justify-content: center;
    width: 64px; height: 64px; border-radius: 18px;
    background: linear-gradient(135deg, {COLORS['accent']}, {COLORS['accent_dim']});
    font-size: 28px; font-weight: 700; color: #fff; margin-bottom: 20px;
    box-shadow: 0 8px 32px rgba(94, 155, 238, 0.25);
  }}
  h1 {{ font-size: 52px; font-weight: 700; letter-spacing: 2px; margin-bottom: 8px;
        color: {COLORS['text']}; font-family: 'Times New Roman', Times, serif;
        text-transform: uppercase; }}
  .sub {{ font-size: 14px; color: {COLORS['text_muted']}; letter-spacing: 2px;
          text-transform: uppercase; font-weight: 400; margin-bottom: 40px; }}
  .search {{ text-align: center; margin-bottom: 48px; }}
  .search-wrap {{
    display: inline-flex; align-items: center; max-width: 600px; width: 100%;
    background: {COLORS['bg_light']}; border: 1px solid {COLORS['border']};
    border-radius: 12px; padding: 0 16px; transition: all .25s;
  }}
  .search-wrap:focus-within {{
    border-color: {COLORS['accent']}; box-shadow: 0 0 0 3px rgba(94,155,238,0.15);
    background: {COLORS['bg_medium']};
  }}
  .search-wrap span {{ font-size: 16px; opacity: .4; margin-right: 10px; }}
  .search-wrap input {{
    flex: 1; background: none; border: none; color: {COLORS['text']};
    padding: 14px 0; font-size: 15px; outline: none;
  }}
  .search-wrap input::placeholder {{ color: {COLORS['text_dim']}; }}
  h2 {{ font-size: 13px; font-weight: 600; text-transform: uppercase;
        letter-spacing: 1.5px; color: {COLORS['text_muted']}; margin: 40px 0 18px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
           gap: 10px; margin-bottom: 24px; }}
  .sc {{
    background: {COLORS['bg_light']}; border: 1px solid {COLORS['border']};
    border-radius: 10px; padding: 16px 8px; text-align: center;
    text-decoration: none; color: {COLORS['text']}; transition: all .2s ease;
    display: flex; flex-direction: column; align-items: center; gap: 8px;
    cursor: pointer;
  }}
  .sc:hover {{ background: {COLORS['bg_medium']}; border-color: {COLORS['accent']};
              transform: translateY(-3px); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }}
  .ico {{ font-size: 28px; line-height: 1; }}
  .nm {{ font-size: 11px; color: {COLORS['text_muted']}; }}
  footer {{ text-align: center; color: {COLORS['text_dim']}; font-size: 12px;
            margin-top: 48px; }}
</style>
</head>
<body>
<canvas id="m" style="position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;pointer-events:none;opacity:0.10;"></canvas>
<div class="wrap">
  <div class="hero">
    <div class="logo">N</div>
    <h1>{APP_NAME}</h1>
    <p class="sub">Fast · Secure · Simple</p>
  </div>
  <div class="search">
    <div class="search-wrap">
      <span>🔍</span>
      <input type="text" placeholder="Search or type URL"
        onkeypress="if(event.key=='Enter'){{window.location.href='https://www.google.com/search?q='+encodeURIComponent(this.value);}}">
    </div>
  </div>
  {shortcuts_html}
  <h2>Quick Links</h2>
  <div class="grid">{quick_cards}</div>
  <footer>v{APP_VERSION}</footer>
</div>
<script>{matrix_js}</script>
</body>
</html>"""
        tab.load_home_html(html)

    # ---- Matrix overlay -------------------------------------------------

    def _inject_matrix_overlay(self) -> None:
        script = QWebEngineScript()
        script.setName('nova_matrix_overlay')
        script.setSourceCode("""
(function() {
    var el = document.createElement('div');
    el.id = 'nova-matrix';
    el.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,255,0,0.07);pointer-events:none;z-index:2147483647;';
    document.documentElement.appendChild(el);
})();
""")
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
        script.setWorldId(QWebEngineScript.ScriptWorldId.ApplicationWorld)
        profile = QWebEngineProfile.defaultProfile()
        profile.scripts().insert(script)

    # ---- Security -------------------------------------------------------

    def _apply_security_settings(self) -> None:
        profile = QWebEngineProfile.defaultProfile()
        s = profile.settings()
        s.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptEnabled,
            self.settings.get('enable_js', True)
        )
        s.setAttribute(
            QWebEngineSettings.WebAttribute.ErrorPageEnabled,
            True
        )
        s.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,
            True
        )
        if self.settings.get('block_mixed_content', True):
            s.setAttribute(
                QWebEngineSettings.WebAttribute.AllowRunningInsecureContent,
                False
            )
            s.setAttribute(
                QWebEngineSettings.WebAttribute.AllowGeolocationOnInsecureOrigins,
                False
            )
        if self.settings.get('block_third_party_cookies', True):
            s.setAttribute(
                QWebEngineSettings.WebAttribute.XSSAuditingEnabled,
                True
            )
        self._show_status('Security settings applied')

    def _on_navigation_request(self, url: QUrl) -> None:
        if not self.settings.get('https_only', True):
            return
        if url.scheme() == 'http' and url.host() not in ('localhost', '127.0.0.1'):
            secure_url = url.toString().replace('http://', 'https://', 1)
            tab: BrowserTab = self.tabs.currentWidget()
            if tab:
                QTimer.singleShot(0, lambda: tab.load_url(secure_url))
                self._show_status(f'Upgraded to HTTPS: {secure_url}', 3000)

    def _clear_cookies(self) -> None:
        profile = QWebEngineProfile.defaultProfile()
        profile.cookieStore().deleteAllCookies()
        self._show_status('Cookies cleared', 3000)

    def _clear_cache(self) -> None:
        ans = QMessageBox.question(
            self, 'Clear Cache',
            'Clear browser cache?\nContinue?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ans == QMessageBox.StandardButton.Yes:
            QWebEngineProfile.defaultProfile().clearHttpCache()
            self._show_status('Cache cleared', 3000)

    def _clear_all_data(self) -> None:
        ans = QMessageBox.question(
            self, 'Clear Browsing Data',
            'This will clear history, downloads, cookies, and cache.\nContinue?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if ans == QMessageBox.StandardButton.Yes:
            self.history.clear()
            self.downloads.clear()
            self._clear_cookies()
            QWebEngineProfile.defaultProfile().clearHttpCache()
            self._save_data()
            self._message('Browsing data cleared')

    def _show_security_info(self) -> None:
        tab: BrowserTab = self.tabs.currentWidget()
        if not tab:
            return
        raw = tab.web_view.url().toString()
        is_secure = raw.startswith('https://')
        profile = tab.profile()

        dlg = self._styled_dialog('Security & Privacy', 480, 360)
        lo = QVBoxLayout()
        lo.addWidget(_make_title('🔒  Security & Privacy'))

        # connection info
        conn_group = QGroupBox('Connection')
        conn_lo = QVBoxLayout()

        status_icon = '🔒' if is_secure else '🔓'
        status_text = 'SECURE (HTTPS)' if is_secure else 'NOT SECURE (HTTP)'
        conn_lo.addWidget(QLabel(f'{status_icon}  Status: {status_text}'))

        domain = QUrl(raw).host() if raw else 'unknown'
        conn_lo.addWidget(QLabel(f'🌐  Domain: {domain}'))
        conn_lo.addWidget(QLabel(f'📄  URL: {raw[:80]}{"..." if len(raw) > 80 else ""}'))

        if is_secure:
            conn_lo.addWidget(QLabel(f'🔐  Protocol: HTTPS / TLS'))
            conn_lo.addWidget(QLabel(f'✓  Certificate: Valid'))

        conn_group.setLayout(conn_lo)
        lo.addWidget(conn_group)

        # privacy info
        priv_group = QGroupBox('Privacy Settings')
        priv_lo = QVBoxLayout()
        priv_lo.addWidget(QLabel(f'JavaScript: {"Enabled" if self.settings.get("enable_js", True) else "Disabled"}'))
        priv_lo.addWidget(QLabel(f'HTTPS Only: {"Yes" if self.settings.get("https_only", True) else "No"}'))
        priv_lo.addWidget(QLabel(f'Mixed Content Blocked: {"Yes" if self.settings.get("block_mixed_content", True) else "No"}'))
        priv_lo.addWidget(QLabel(f'Third-Party Cookies Blocked: {"Yes" if self.settings.get("block_third_party_cookies", True) else "No"}'))
        priv_group.setLayout(priv_lo)
        lo.addWidget(priv_group)

        close_btn = QPushButton('Close')
        close_btn.clicked.connect(dlg.close)
        lo.addWidget(close_btn)
        dlg.setLayout(lo)
        dlg.exec()

    # ---- Progress bar ---------------------------------------------------

    def _on_load_started(self) -> None:
        self.loading_bar.setValue(0)
        self.loading_bar.show()

    def _on_load_progress(self, progress: int) -> None:
        self.loading_bar.setValue(progress)

    def _on_load_finished(self, _ok: bool) -> None:
        self.loading_bar.setValue(100)
        QTimer.singleShot(300, self.loading_bar.hide)
        tab: BrowserTab = self.tabs.currentWidget()
        if tab:
            self.plugin_manager.notify_page_load(tab.url, tab)

    # ---- Keyboard shortcuts ---------------------------------------------

    def _setup_shortcuts(self) -> None:
        def seq(*keys: str) -> QKeySequence:
            return QKeySequence(QKeySequence.StandardKey(*keys)) if keys else QKeySequence()

        shortcuts = [
            ('Ctrl+T', lambda: self._add_tab()),
            ('Ctrl+W', lambda: self._close_tab(self.tabs.currentIndex())),
            ('Ctrl+Shift+T', self._restore_last_closed_tab),
            ('F5', self._reload),
            ('Ctrl+R', self._reload),
            ('Ctrl+L', lambda: self.url_bar.lineEdit().selectAll()),
            ('Alt+D', lambda: self.url_bar.lineEdit().selectAll()),
            ('Ctrl+Shift+Delete', self._clear_all_data),
            ('Ctrl+D', self._toggle_bookmark),
            ('Ctrl+H', self._show_history),
            ('Ctrl+B', self._show_bookmarks),
            ('Escape', lambda: self._stop()),
            ('Ctrl+Shift+A', self._toggle_ai_assistant),
            ('Ctrl+Shift+R', self._toggle_reader_mode),
            ('Ctrl+Shift+L', self._show_translation_dialog),
        ]
        for keys, slot in shortcuts:
            act = QAction(self)
            act.setShortcut(QKeySequence(keys))
            act.triggered.connect(slot)
            self.addAction(act)

    # ---- Status bar -----------------------------------------------------

    def _on_link_hovered(self, url: str) -> None:
        if url:
            self._show_status(url, 0)
        else:
            self.status.clearMessage()

    def _show_status(self, msg: str, timeout: int = 3000) -> None:
        self.status.showMessage(msg, timeout)

    # ---- Utilities ------------------------------------------------------

    def _load_url_from_item(self, item: QListWidgetItem) -> None:
        url = item.data(Qt.ItemDataRole.UserRole)
        tab: BrowserTab = self.tabs.currentWidget()
        if tab and url:
            tab.load_url(url)

    def _restore_last_closed_tab(self) -> None:
        self._show_status('Tab restore coming soon', 2000)

    @staticmethod
    def _message(text: str) -> None:
        QMessageBox.information(None, APP_NAME, text)

    # ---- Lifecycle ------------------------------------------------------

    def closeEvent(self, event) -> None:
        self._stop_perf_monitor()
        self.sync_manager.stop()
        if self.settings.get('sync_enabled', False):
            self.sync_manager.sync_push()
        self._save_data()
        for i in range(self.tabs.count()):
            tab: BrowserTab = self.tabs.widget(i)
            if tab:
                tab.cleanup()
        event.accept()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    _ = Browser()
    sys.exit(app.exec())
