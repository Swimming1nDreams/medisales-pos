"""
Legacy PySide6 Native QWidget MainWindow (Deprecated).

Notice:
    This native QWidget view has been archived to `src/ui/legacy/`.
    The active commercial production application boots `MainWindowWeb`
    from `src/ui/main_window_web.py`.
"""
import warnings

# Issue a deprecation notice when accessed directly
warnings.warn(
    "src.ui.main_window.MainWindow is deprecated and archived in src.ui.legacy. "
    "The primary desktop UI engine is src.ui.main_window_web.MainWindowWeb.",
    DeprecationWarning,
    stacklevel=2
)

from .legacy.main_window import MainWindow

__all__ = ["MainWindow"]
