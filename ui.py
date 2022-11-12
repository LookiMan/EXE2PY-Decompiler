# -*- coding: UTF-8 -*-
from PyQt5.QtWidgets import QWidget, QFileDialog
from PyQt5.QtWidgets import QMessageBox, QLabel, QLineEdit, QSizePolicy
from PyQt5 import QtCore, QtGui

import utils
import toggleButton


def show_info(title: str, message_text: str):
    QMessageBox.information(None, title, message_text, QMessageBox.Ok)


def show_warning(title: str, message_text: str):
    QMessageBox.warning(None, title, message_text, QMessageBox.Ok)


def show_error(title: str, message_text: str):
    QMessageBox.critical(None, title, message_text, QMessageBox.Ok)


def file_dialog():
    dlg = QFileDialog()
    dlg.setFileMode(QFileDialog.AnyFile)

    if dlg.exec_():
        return dlg.selectedFiles()


class GifPlayer(QtCore.QObject):
    def __init__(self, widget):
        super().__init__()
        self.central_widget = widget
        self.banner = QLabel(self.central_widget)
        self.banner.setGeometry(
            0, 26, self.central_widget.width(), self.central_widget.height()
        )
        self.banner.setStyleSheet("background-color: rgba(195, 195, 195, 100);")
        self.movie_screen = QLabel(self.central_widget)
        self.movie_screen.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.movie_screen.setAlignment(QtCore.Qt.AlignCenter)
        self.movie_screen.setScaledContents(True)
        self.movie_screen.setGeometry(
            QtCore.QRect(
                int(self.central_widget.width() // 2 - 62),
                int(self.central_widget.height() // 2 - 62),
                124,
                124,
            )
        )
        self.movie = QtGui.QMovie("images\\preloader.gif")
        self.movie.setCacheMode(QtGui.QMovie.CacheAll)
        self.movie_screen.setMovie(self.movie)
        self.movie_screen.hide()
        self.banner.hide()

    def start_animation(self):
        self.movie.start()
        self.banner.show()
        self.movie_screen.show()

    def stop_animation(self):
        self.movie.stop()
        self.banner.hide()
        self.movie_screen.hide()


class Thread(QtCore.QThread):
    callback = QtCore.pyqtSignal(int)

    def __init__(self, function, *args):
        super().__init__()
        self.is_running = True
        self.function = function
        self.args = args

    def run(self):
        self.callback.emit(self.function(*self.args))


class DraggableLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setAcceptDrops(True)

    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat("text/plain"):
            e.accept()

        elif e.mimeData().hasFormat("text/uri-list"):
            e.accept()

        else:
            e.ignore()

    def dropEvent(self, e):
        path = e.mimeData().text()

        if path.startswith("file:///"):
            path = path[8:]

        self.setText(path)


class ClickedQLabel(QLabel):
    """Класс добавляющий событие клика базовому классу QLabel"""

    clicked = QtCore.pyqtSignal()

    def mouseReleaseEvent(self, event):
        self.clicked.emit()
        super().mouseReleaseEvent(event)


class BaseMoveEvents(QWidget):
    """Реализация базовых методов для шапки приложения"""

    def _get_window(self):
        return self._parent.window()

    def _get_window_width(self):
        return self._parent.window().geometry().width()

    def _get_window_height(self):
        return self._parent.window().geometry().height()

    def _get_screen_size(self):
        return (utils.get_screen_width(), utils.get_screen_height())

    def mouseMoveEvent(self, event):
        win = self._get_window()
        screensize = self._get_screen_size()

        if self.b_move:
            x = event.globalX() + self.x_korr - self.lastPoint.x()
            y = event.globalY() + self.y_korr - self.lastPoint.y()
            if x >= screensize[0] - self._get_window_width():
                x = screensize[0] - self._get_window_width()
            if x <= 0:
                x = 0
            if y >= screensize[1] - self._get_window_height():
                y = screensize[1] - self._get_window_height()
            if y <= 0:
                y = 0
            win.move(x, y)

        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            win = self._get_window()
            x_korr = win.frameGeometry().x() - win.geometry().x()
            y_korr = win.frameGeometry().y() - win.geometry().y()
            parent = self
            while not parent == win:
                x_korr -= parent.x()
                y_korr -= parent.y()
                parent = parent.parent()

            self.__dict__.update(
                {
                    "lastPoint": event.pos(),
                    "b_move": True,
                    "x_korr": x_korr,
                    "y_korr": y_korr,
                }
            )
        else:
            self.__dict__.update({"b_move": False})

        self.setCursor(QtCore.Qt.SizeAllCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if hasattr(self, "x_korr") and hasattr(self, "y_korr"):
            self.__dict__.update({"b_move": False})
            x = event.globalX() + self.x_korr - self.lastPoint.x()
            y = event.globalY() + self.y_korr - self.lastPoint.y()

        self.setCursor(QtCore.Qt.ArrowCursor)
        super().mouseReleaseEvent(event)


class Panel(QLabel, BaseMoveEvents):
    """Панель заголовка окна приложения"""

    def __init__(self, parent, width: int, height: int):
        super(QLabel, self).__init__(parent)
        self._parent = parent
        self._width = width
        self._height = height
        self.setGeometry(QtCore.QRect(0, 0, self._width, self._height))
        self._pixmap = QtGui.QPixmap("images\\header.png")
        self.setScaledContents(True)
        self.setPixmap(self._pixmap)
        self.setObjectName("header")


class Title(QLabel, BaseMoveEvents):
    """Заголовок окна приложения"""

    def __init__(self, parent, width: int, height: int):
        super(QLabel, self).__init__(parent)
        self._parent = parent
        self._width = width
        self._height = height
        self.font = QtGui.QFont()
        self.font.setFamily("Segoe UI Semibold")
        self.font.setPointSize(8)
        self.font.setWeight(75)
        self.font.setBold(True)
        self.setStyleSheet("color: rgb(255,255,255);")
        self.setFont(self.font)
        self.setGeometry(QtCore.QRect(10, 0, self._width, self._height))
        self.setText("Заголовок")
        self.setObjectName("titleLabel")

    def set_title(self, title):
        self.setText(title)

    def get_title(self):
        return self.text()


class BaseButtonEvents(QWidget):
    """Общие методы для реализации ховер еффекта"""

    def enterEvent(self, event):
        self.setPixmap(self.pixmap_enter)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setPixmap(self.pixmap_leave)
        super().leaveEvent(event)


class HideButton(ClickedQLabel, BaseButtonEvents):
    """Кнопка сворачивания приложения"""

    def __init__(self, parent, x, y, size=26):
        super(QLabel, self).__init__(parent)
        self.pixmap = QtGui.QPixmap("images/hide.png")
        self.pixmap_leave = self.pixmap.copy(0, 0, size, size)
        self.pixmap_enter = self.pixmap.copy(size, 0, size * 2, size)

        self.setGeometry(QtCore.QRect(x, y, size, size))
        self.setPixmap(self.pixmap_leave)
        self.setObjectName("minimize_button")
        self.setToolTip("Свернуть")


class CloseButton(ClickedQLabel, BaseButtonEvents):
    """Кнопка закрытия приложения"""

    def __init__(self, parent, x, y, size=26):
        super(QLabel, self).__init__(parent)
        self.pixmap = QtGui.QPixmap("images/close.png")
        self.pixmap_leave = self.pixmap.copy(0, 0, size, size)
        self.pixmap_enter = self.pixmap.copy(size, 0, size * 2, size)

        self.setGeometry(QtCore.QRect(x, y, size, size))
        self.setPixmap(self.pixmap_leave)
        self.setObjectName("close_button")
        self.setToolTip("Закрыть")


class Header(object):
    """Шапка приложения с заголовком и кнопками закрытия и сворачивания"""

    def __init__(self, parent):
        self._height = 26
        self.panel = Panel(parent, parent.width(), self._height)
        self.title = Title(parent, parent.width() * 0.8, self._height)
        self.hide_button = HideButton(
            parent, parent.width() - self._height * 2, 0, self._height
        )
        self.close_button = CloseButton(
            parent, parent.width() - self._height, 0, self._height
        )

    def width(self):
        return self._width

    def height(self):
        return self._height


class BaseForm(QtCore.QObject):
    closeHandler = QtCore.pyqtSignal(dict)
    """ Вынесены общие методы для всех форм """

    def _customize_window(self):
        """Создание кастомного окна"""

        # Убираем стандартную рамку
        self.form.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        # Установка иконки
        icon = QtGui.QIcon()
        icon.addPixmap(
            QtGui.QPixmap("images/icon.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off
        )
        self.form.setWindowIcon(icon)

        self.header = Header(self.form)
        self.header.hide_button.clicked.connect(self.minimize)
        self.header.close_button.clicked.connect(self.closeEvent)

    def closeEvent(self):
        """
        Базовый метод, вызывающийся при закрытии по нажатию на кастомный крестик.
        """
        self.close()

    def show(self):
        """Отображение формы"""
        self.form.show()

    def hide(self):
        """Скрытие формы"""
        self.form.hide()

    def minimize(self):
        """Сворачивает окно"""
        self.form.showMinimized()

    def close(self):
        """Закрытие формы"""

        # Если есть дочернее окно, закроет его
        if hasattr(self, "child_form"):
            self.child_form.close()

        self.form.close()

    def set_title(self, title):
        """Метод для установки заголовка окна"""
        self.header.title.set_title(title)

    def get_title(self):
        """Метод для получения заголовка окна"""
        return self.header.title.get_title()

    def set_background_image(self, path):
        """Установка изображения на задний фон"""
        self.background.set_image(path)


class MainWindow(BaseForm):
    def __init__(self):
        super().__init__()
        self.form = QWidget()
        self.form.setObjectName("MainWindow")
        self.form.setFixedSize(644, 175)
        self.form.setStyleSheet(
            "#MainWindow{background-color: #F2F2F2; border: 1 solid #000;}"
        )

        self._customize_window()

        self.header.title.set_title("Decompiller 3.0")

        self.font = QtGui.QFont()
        self.font.setPointSize(10)

        self.label = QLabel(self.form)
        self.label.setObjectName("label")
        self.label.setGeometry(QtCore.QRect(12, 36, 601, 16))
        self.label.setText("Введите путь к декомпилируемой программе или скрипту")
        self.label.setFont(self.font)

        self.lineEdit = DraggableLineEdit(self.form)
        self.lineEdit.setObjectName("lineEdit")
        self.lineEdit.setGeometry(QtCore.QRect(10, 66, 560, 30))
        self.lineEdit.setStyleSheet(
            "#lineEdit{"
            "border: 1px solid #DDDDDD;"
            "padding-left: 5px;"
            "border-radius: 4px;"
            "border-top-right-radius: 0px;"
            "border-bottom-right-radius: 0px;"
            "background-color: #fff;"
            "}"
        )

        self.file_search_button = ClickedQLabel(self.form)
        self.file_search_button.setObjectName("file_search_button")
        self.file_search_button.setGeometry(QtCore.QRect(570, 66, 60, 30))
        self.file_search_button.setFont(self.font)
        self.file_search_button.setText("●●●")
        self.file_search_button.clicked.connect(self.select_file)
        self.file_search_button.setStyleSheet(
            "#file_search_button{"
            "border-bottom: 3px solid #080386;"
            "border-radius: 4px;"
            "border-top-left-radius: 0px;"
            "border-bottom-left-radius: 0px;"
            "qproperty-alignment: AlignCenter;"
            "background-color: #240DC4;"
            "color: #ffffff;"
            "}\n"
            "#file_search_button:hover{"
            "background-color: #080386;"
            "}"
        )

        self.label_2 = QLabel(self.form)
        self.label_2.setObjectName("label_2")
        self.label_2.setGeometry(QtCore.QRect(14, 106, 320, 24))
        self.label_2.setText("Декомпилировать все дополнительные библиотеки")
        self.label_2.setFont(self.font)

        self.checkbox = toggleButton.AnimatedToggle(self.form)
        self.checkbox.move(340, 98)
        self.checkbox.setFixedSize(self.checkbox.sizeHint())
        self.checkbox.show()

        self.label_3 = QLabel(self.form)
        self.label_3.setObjectName("label_2")
        self.label_3.setGeometry(QtCore.QRect(14, 140, 320, 24))
        self.label_3.setText("Автоматически открыть финальные папки")
        self.label_3.setFont(self.font)

        self.checkbox_2 = toggleButton.AnimatedToggle(self.form)
        self.checkbox_2.move(340, 132)
        self.checkbox_2.setChecked(True)

        self.player = GifPlayer(self.form)

        self.start_button = ClickedQLabel(self.form)
        self.start_button.setObjectName("start_button")
        self.start_button.setGeometry(QtCore.QRect(490, 136, 140, 30))
        self.start_button.setFont(self.font)
        self.start_button.setText("Декомпилировать")
        self.start_button.clicked.connect(self.start_processing)
        self.start_button.setStyleSheet(
            "#start_button{"
            "border-bottom: 3px solid #080386;"
            "border-radius: 4px;"
            "qproperty-alignment: AlignCenter;"
            "background-color: #240DC4;"
            "color: #ffffff;"
            "}\n"
            "#start_button:hover{"
            "background-color: #080386;"
            "}"
        )

        self.stop_button = ClickedQLabel(self.form)
        self.stop_button.setObjectName("stop_button")
        self.stop_button.setGeometry(QtCore.QRect(490, 136, 140, 30))
        self.stop_button.setFont(self.font)
        self.stop_button.setText("Остановить")
        self.stop_button.clicked.connect(lambda: self.stop_processing(401))
        self.stop_button.setStyleSheet(
            "#stop_button{"
            "border-bottom: 3px solid #9D0909;"
            "border-radius: 4px;"
            "qproperty-alignment: AlignCenter;"
            "background-color: #ED0D0D;"
            "color: #ffffff;"
            "}\n"
            "#stop_button:hover{"
            "background-color: #9D0909;"
            "}"
        )
        self.stop_button.hide()

        self.form.show()

        QtCore.QMetaObject.connectSlotsByName(self.form)

    def start_processing(self):
        self.player.start_animation()

        self.start_button.hide()
        self.stop_button.show()

        self.thread = Thread(
            self.worker,
            self.lineEdit.text().strip(),
            self.checkbox.isChecked(),
            self.checkbox_2.isChecked(),
        )

        self.thread.callback.connect(self.stop_processing)
        self.thread.start()

    def stop_processing(self, status_code):
        self.stop_button.hide()
        self.player.stop_animation()
        self.start_button.show()

        if status_code in range(200, 300):
            message = utils.STATUS_CODES[status_code]
            show_info("Успех", message)

        elif status_code in range(400, 500):
            message = utils.STATUS_CODES[status_code]
            show_warning("Внимание", message)

        elif status_code in range(500, 600):
            message = utils.STATUS_CODES[status_code]
            show_error("Критическая ошибка", message)

        else:
            show_error(
                "Критическая ошибка", "Непредвиденный статус код: %s" % str(status_code)
            )

    def select_file(self):
        filename = file_dialog()

        if filename is not None:
            filename = filename[0].replace("/", "\\")

        self.lineEdit.setText(filename)
