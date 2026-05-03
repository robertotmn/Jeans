"""Entry point. Run with `python -m jeans_app.main` or via the `jeans-app` console script."""
import sys

from PySide6 import QtWidgets

from .main_window import MainWindow


def main() -> int:
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
