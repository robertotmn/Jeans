import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def main_window(qtbot):
    from jeans_app.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    return w


def test_main_window_has_form_and_preview(main_window):
    assert hasattr(main_window, "form")
    assert hasattr(main_window, "preview")


def test_main_window_default_pattern_builds(main_window):
    """The default (size 50) measurements produce all 11 pieces."""
    pat = main_window._build_pattern()
    assert len(list(pat)) == 11


def test_main_window_changing_form_emits_signal(main_window, qtbot):
    with qtbot.waitSignal(main_window.form.measurements_changed, timeout=1000):
        main_window.form.set_value("waistband", 92.0)


def test_main_window_report_label(main_window):
    main_window._refresh_preview()
    text = main_window.info_label.text()
    assert "Agio fianchi" in text
    assert "Cavallo Br: 20.0 cm" in text


def test_main_window_jacket_pattern_builds(main_window):
    """Switching the model to the jacket produces all 17 Design 4041 pieces."""
    from jeans_app.measurement_form import MODEL_JACKET
    main_window.form.set_model(MODEL_JACKET)
    pat = main_window._build_pattern()
    assert len(list(pat)) == 17


def test_main_window_jacket_report_label(main_window):
    from jeans_app.measurement_form import MODEL_JACKET
    main_window.form.set_model(MODEL_JACKET)
    main_window._refresh_preview()
    text = main_window.info_label.text()
    assert "Prof. giro Sd: 25.0 cm" in text
    assert "Lunghezza Lg: 64.0 cm" in text
    assert "Agio petto" in text
    assert "Agio testa" in text
    assert "Cavallo Br" not in text


def test_main_window_export_name_follows_model(main_window):
    from jeans_app.measurement_form import MODEL_JACKET
    assert main_window._export_name("pdf") == "jeans_pattern.pdf"
    main_window.form.set_model(MODEL_JACKET)
    assert main_window._export_name("pdf") == "jacket_pattern.pdf"
    assert main_window._export_name("svg") == "jacket_pattern.svg"
