from os.path import join
from platform import system
from pyautogui import Size

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QEvent
from PyQt5.QtGui import QDragEnterEvent
from PyQt5.QtGui import QDropEvent
from PyQt5.QtGui import QMovie
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtGui import QEnterEvent
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QSizePolicy

from utils import get_screen_size
from utils import Platforms
from utils import STATUS_CODES

from toggle import AnimatedToggle


class GifPlayer(QtCore.QObject):
    def __init__(self, widget) -> None:
        super().__init__()
        self.central_widget = widget
        self.banner = QLabel(self.central_widget)
        self.banner.setGeometry(
            0, 26, self.central_widget.width(), self.central_widget.height()
        )
        self.banner.setStyleSheet('background-color: rgba(195, 195, 195, 100);')
        self.movie_screen = QLabel(self.central_widget)
        self.movie_screen.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.movie_screen.setAlignment(Qt.AlignCenter)
        self.movie_screen.setScaledContents(True)
        self.movie_screen.setGeometry(
            QtCore.QRect(
                int(self.central_widget.width() // 2 - 62),
                int(self.central_widget.height() // 2 - 62),
                124,
                124,
            )
        )
        self.movie = QMovie(join('images', 'preloader.gif'))
        self.movie.setCacheMode(QMovie.CacheAll)
        self.movie_screen.setMovie(self.movie)
        self.movie_screen.hide()
        self.banner.hide()

    def start_animation(self) -> None:
        self.movie.start()
        self.banner.show()
        self.movie_screen.show()

    def stop_animation(self) -> None:
        self.movie.stop()
        self.banner.hide()
        self.movie_screen.hide()


class Thread(QtCore.QThread):
    callback = QtCore.pyqtSignal(int)

    def __init__(self, function, **kwargs) -> None:
        super().__init__()
        self.is_running = True
        self.function = function
        self.kwargs = kwargs

    def run(self) -> None:
        self.callback.emit(self.function(**self.kwargs))


class DraggableLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasFormat('text/plain'):
            event.accept()

        elif event.mimeData().hasFormat('text/uri-list'):
            event.accept()

        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        self.setText(event.mimeData().text().replace('file:///', ''))


class ClickedQLabel(QLabel):
    clicked = QtCore.pyqtSignal()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.clicked.emit()
        super().mouseReleaseEvent(event)


class BaseMoveEvents(QWidget):
    def _get_window(self) -> QWidget:
        return self._parent.window()

    def _get_window_width(self) -> int:
        return self._parent.window().geometry().width()

    def _get_window_height(self) -> int:
        return self._parent.window().geometry().height()

    def _get_screen_size(self) -> Size:
        return get_screen_size()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
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

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
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
                    'lastPoint': event.pos(),
                    'b_move': True,
                    'x_korr': x_korr,
                    'y_korr': y_korr,
                }
            )
        else:
            self.__dict__.update({'b_move': False})

        self.setCursor(Qt.SizeAllCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)


class Panel(QLabel, BaseMoveEvents):
    def __init__(self, parent: QWidget, width: int, height: int) -> None:
        super(QLabel, self).__init__(parent)
        self._parent = parent
        self._width = width
        self._height = height
        self.setGeometry(QtCore.QRect(0, 0, self._width, self._height))
        self._pixmap = QtGui.QPixmap(join('images', 'header.png'))
        self.setScaledContents(True)
        self.setPixmap(self._pixmap)
        self.setObjectName('header')


class Title(QLabel, BaseMoveEvents):
    def __init__(self, parent: QWidget, width: int, height: int) -> None:
        super(QLabel, self).__init__(parent)
        self._parent = parent
        self._width = width
        self._height = height
        self.font = QtGui.QFont()
        self.font.setFamily('Segoe UI Semibold')
        self.font.setPointSize(8)
        self.font.setWeight(75)
        self.font.setBold(True)
        self.setStyleSheet('color: rgb(255,255,255);')
        self.setFont(self.font)
        self.setGeometry(QtCore.QRect(10, 0, self._width, self._height))
        self.setText('Заголовок')
        self.setObjectName('titleLabel')

    def set_title(self, title: str) -> None:
        self.setText(title)

    def get_title(self) -> str:
        return self.text()


class BaseButtonEvents(QWidget):
    def enterEvent(self, event: QEnterEvent) -> None:
        self.setPixmap(self.pixmap_enter)
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self.setPixmap(self.pixmap_leave)
        super().leaveEvent(event)


class HideButton(ClickedQLabel, BaseButtonEvents):
    def __init__(self, parent: QWidget, x: int, y: int, size: int = 26) -> None:
        super(QLabel, self).__init__(parent)
        self.pixmap = QtGui.QPixmap(join('images', 'hide.png'))
        self.pixmap_leave = self.pixmap.copy(0, 0, size, size)
        self.pixmap_enter = self.pixmap.copy(size, 0, size * 2, size)

        self.setGeometry(QtCore.QRect(x, y, size, size))
        self.setPixmap(self.pixmap_leave)
        self.setObjectName('minimize_button')
        self.setToolTip('Hide')


class CloseButton(ClickedQLabel, BaseButtonEvents):
    def __init__(self, parent: QWidget, x: int, y: int, size: int = 26) -> None:
        super(QLabel, self).__init__(parent)
        self.pixmap = QtGui.QPixmap(join('images', 'close.png'))
        self.pixmap_leave = self.pixmap.copy(0, 0, size, size)
        self.pixmap_enter = self.pixmap.copy(size, 0, size * 2, size)

        self.setGeometry(QtCore.QRect(x, y, size, size))
        self.setPixmap(self.pixmap_leave)
        self.setObjectName('close_button')
        self.setToolTip('Close')


class Header:
    def __init__(self, parent: QWidget) -> None:
        self._height = 26
        self.panel = Panel(parent, parent.width(), self._height)
        self.title = Title(parent, parent.width() * 0.8, self._height)
        self.hide_button = HideButton(
            parent, parent.width() - self._height * 2, 0, self._height
        )
        self.close_button = CloseButton(
            parent, parent.width() - self._height, 0, self._height
        )

    def width(self) -> int:
        return self._width

    def height(self) -> int:
        return self._height


class BaseForm(QtCore.QObject):
    closeHandler = QtCore.pyqtSignal(dict)

    def _customize_window(self) -> None:
        """Creating a custom window"""

        self.form.setWindowFlags(Qt.FramelessWindowHint)
        icon = QtGui.QIcon()
        icon.addPixmap(
            QtGui.QPixmap(join('images', 'icon.ico')), QtGui.QIcon.Normal, QtGui.QIcon.Off
        )
        self.form.setWindowIcon(icon)

        self.header = Header(self.form)
        self.header.hide_button.clicked.connect(self.minimize)
        self.header.close_button.clicked.connect(self.closeEvent)

    def closeEvent(self) -> None:
        self.close()

    def show(self) -> None:
        self.form.show()

    def hide(self) -> None:
        self.form.hide()

    def minimize(self) -> None:
        self.form.showMinimized()

    def close(self) -> None:
        self.form.close()

    def set_title(self, title: str) -> None:
        self.header.title.set_title(title)

    def get_title(self) -> str:
        return self.header.title.get_title()

    def set_background_image(self, path: str) -> None:
        self.background.set_image(path)

    def show_info(self, title: str, message_text: str) -> None:
        QMessageBox.information(self.form, title, message_text, QMessageBox.Ok)

    def show_warning(self, title: str, message_text: str) -> None:
        QMessageBox.warning(self.form, title, message_text, QMessageBox.Ok)

    def show_error(self, title: str, message_text: str) -> None:
        QMessageBox.critical(self.form, title, message_text, QMessageBox.Ok)


class MainWindow(BaseForm):
    def __init__(self, worker: callable, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.worker = worker
        self.form = QWidget()
        self.form.setObjectName('MainWindow')
        self.form.setFixedSize(644, 175)
        self.form.setStyleSheet(
            '#MainWindow{background-color: #F2F2F2; border: 1 solid #000;}'
        )

        self._customize_window()

        self.header.title.set_title('Decompiller 3.0')

        self.font = QtGui.QFont()
        self.font.setPointSize(10)

        self.label = QLabel(self.form)
        self.label.setObjectName('label')
        self.label.setGeometry(QtCore.QRect(12, 36, 601, 16))
        self.label.setText('Enter the path to the program or script to be decompiled')
        self.label.setFont(self.font)

        self.lineEdit = DraggableLineEdit(self.form)
        self.lineEdit.setObjectName('lineEdit')
        self.lineEdit.setGeometry(QtCore.QRect(10, 66, 560, 30))
        self.lineEdit.setStyleSheet(
            '#lineEdit{'
            'border: 1px solid #DDDDDD;'
            'padding-left: 5px;'
            'border-radius: 4px;'
            'border-top-right-radius: 0px;'
            'border-bottom-right-radius: 0px;'
            'background-color: #fff;'
            '}'
        )

        self.file_search_button = ClickedQLabel(self.form)
        self.file_search_button.setObjectName('file_search_button')
        self.file_search_button.setGeometry(QtCore.QRect(570, 66, 60, 30))
        self.file_search_button.setFont(self.font)
        self.file_search_button.setText('●●●')
        self.file_search_button.clicked.connect(self.select_file)
        self.file_search_button.setStyleSheet(
            '#file_search_button{'
            'border-bottom: 3px solid #080386;'
            'border-radius: 4px;'
            'border-top-left-radius: 0px;'
            'border-bottom-left-radius: 0px;'
            'qproperty-alignment: AlignCenter;'
            'background-color: #240DC4;'
            'color: #ffffff;'
            '}\n'
            '#file_search_button:hover{'
            'background-color: #080386;'
            '}'
        )

        self.is_need_decompile_sub_libraries_label = QLabel(self.form)
        self.is_need_decompile_sub_libraries_label.setObjectName('decompile_sub_libraries_label')
        self.is_need_decompile_sub_libraries_label.setGeometry(QtCore.QRect(14, 106, 190, 24))
        self.is_need_decompile_sub_libraries_label.setText('Decompile all additional libraries')
        self.is_need_decompile_sub_libraries_label.setFont(self.font)

        self.is_need_decompile_sub_libraries_checkbox = AnimatedToggle(self.form)
        self.is_need_decompile_sub_libraries_checkbox.move(210, 98)
        self.is_need_decompile_sub_libraries_checkbox.setFixedSize(
            self.is_need_decompile_sub_libraries_checkbox.sizeHint()
        )
        self.is_need_decompile_sub_libraries_checkbox.show()

        self.is_need_open_output_folder_label = QLabel(self.form)
        self.is_need_open_output_folder_label.setObjectName('open_output_folder_label')
        self.is_need_open_output_folder_label.setGeometry(QtCore.QRect(14, 140, 190, 24))
        self.is_need_open_output_folder_label.setText('Automatically open final folder')
        self.is_need_open_output_folder_label.setFont(self.font)

        self.is_need_open_output_folder_checkbox = AnimatedToggle(self.form)
        self.is_need_open_output_folder_checkbox.move(210, 132)
        self.is_need_open_output_folder_checkbox.setChecked(True)

        self.player = GifPlayer(self.form)

        self.start_button = ClickedQLabel(self.form)
        self.start_button.setObjectName('start_button')
        self.start_button.setGeometry(QtCore.QRect(490, 136, 140, 30))
        self.start_button.setFont(self.font)
        self.start_button.setText('Decompile')
        self.start_button.clicked.connect(self.start_processing)
        self.start_button.setStyleSheet(
            '#start_button{'
            'border-bottom: 3px solid #080386;'
            'border-radius: 4px;'
            'qproperty-alignment: AlignCenter;'
            'background-color: #240DC4;'
            'color: #ffffff;'
            '}\n'
            '#start_button:hover{'
            'background-color: #080386;'
            '}'
        )

        self.stop_button = ClickedQLabel(self.form)
        self.stop_button.setObjectName('stop_button')
        self.stop_button.setGeometry(QtCore.QRect(490, 136, 140, 30))
        self.stop_button.setFont(self.font)
        self.stop_button.setText('Stop')
        self.stop_button.clicked.connect(lambda: self.stop_processing(401))
        self.stop_button.setStyleSheet(
            '#stop_button{'
            'border-bottom: 3px solid #9D0909;'
            'border-radius: 4px;'
            'qproperty-alignment: AlignCenter;'
            'background-color: #ED0D0D;'
            'color: #ffffff;'
            '}\n'
            '#stop_button:hover{'
            'background-color: #9D0909;'
            '}'
        )
        self.stop_button.hide()
        self.form.show()
        QtCore.QMetaObject.connectSlotsByName(self.form)

    def start_processing(self) -> None:
        self.player.start_animation()

        self.start_button.hide()
        self.stop_button.show()

        self.thread = Thread(
            self.worker,
            target=self.lineEdit.text().strip(),
            is_need_decompile_sub_libraries=self.is_need_decompile_sub_libraries_checkbox.isChecked(),
            is_need_open_output_folder=self.is_need_open_output_folder_checkbox.isChecked(),
        )

        self.thread.callback.connect(self.stop_processing)
        self.thread.start()

    def stop_processing(self, status_code) -> None:
        self.stop_button.hide()
        self.player.stop_animation()
        self.start_button.show()

        if not STATUS_CODES.get(status_code):
            self.show_error(
                'Critical', f'Unknown status code: {status_code}'
            )

        elif status_code in range(200, 300):
            message = STATUS_CODES[status_code]
            self.show_info('Success', message)

        elif status_code in range(400, 500):
            message = STATUS_CODES[status_code]
            self.show_warning('Warning', message)

        elif status_code in range(500, 600):
            message = STATUS_CODES[status_code]
            self.show_error('Critical', message)

    def select_file(self) -> None:
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.ExistingFile)

        if not dlg.exec_():
            return

        file = dlg.selectedFiles()

        if not file:
            return

        file = file[0]

        if system() == Platforms.WINDOWS.value:
            file = file.replace('/', '\\')

        self.lineEdit.setText(file)

        state = True if file.endswith('.exe') else False

        self.is_need_decompile_sub_libraries_checkbox.setChecked(state)
        self.is_need_decompile_sub_libraries_checkbox.setDisabled(not state)
