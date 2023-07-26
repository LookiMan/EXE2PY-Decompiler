from PyQt5.QtWidgets import QCheckBox

from PyQt5.QtCore import pyqtProperty
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QEasingCurve
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QPoint
from PyQt5.QtCore import QPointF
from PyQt5.QtCore import QPropertyAnimation
from PyQt5.QtCore import QRectF
from PyQt5.QtCore import QSequentialAnimationGroup

from PyQt5.QtGui import QColor
from PyQt5.QtGui import QBrush
from PyQt5.QtGui import QPainter
from PyQt5.QtGui import QPaintEvent
from PyQt5.QtGui import QPen


class AnimatedToggle(QCheckBox):
    _transparent_pen = QPen(Qt.transparent)
    _light_grey_pen = QPen(Qt.lightGray)

    def __init__(
        self,
        parent=None,
        bar_color=Qt.gray,
        checked_color='#240DC4',
        handle_color=Qt.white,
        pulse_unchecked_color='#D5D5D5',
        pulse_checked_color='#4400B0EE',
    ) -> None:
        super().__init__(parent)

        self._bar_brush = QBrush(bar_color)
        self._bar_checked_brush = QBrush(QColor(checked_color).lighter())
        self._handle_brush = QBrush(handle_color)
        self._handle_checked_brush = QBrush(QColor(checked_color))
        self._pulse_unchecked_animation = QBrush(QColor(pulse_unchecked_color))
        self._pulse_checked_animation = QBrush(QColor(pulse_checked_color))

        self.setContentsMargins(8, 0, 8, 0)
        self._handle_position = 0
        self._pulse_radius = 0

        self.animation = QPropertyAnimation(self, b'handle_position', self)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.animation.setDuration(250)

        self.pulse_anim = QPropertyAnimation(self, b'pulse_radius', self)
        self.pulse_anim.setDuration(250)
        self.pulse_anim.setStartValue(10)
        self.pulse_anim.setEndValue(17)

        self.animations_group = QSequentialAnimationGroup()
        self.animations_group.addAnimation(self.animation)
        self.animations_group.addAnimation(self.pulse_anim)

        self.stateChanged.connect(self.setup_animation)

    def sizeHint(self) -> QSize:
        return QSize(58, 45)

    def hitButton(self, pos: QPoint) -> bool:
        return self.contentsRect().contains(pos)

    @pyqtSlot(int)
    def setup_animation(self, value: int) -> None:
        self.animations_group.stop()
        self.animation.setEndValue(bool(value))
        self.animations_group.start()

    def paintEvent(self, event: QPaintEvent) -> None:
        contRect = self.contentsRect()
        handleRadius = round(0.24 * contRect.height())

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        p.setPen(self._transparent_pen)
        barRect = QRectF(
            0, 0, contRect.width() - handleRadius, 0.40 * contRect.height()
        )
        barRect.moveCenter(contRect.center())
        rounding = barRect.height() / 2
        trailLength = contRect.width() - 2 * handleRadius
        xPos = contRect.x() + handleRadius + trailLength * self._handle_position

        if self.pulse_anim.state() == QPropertyAnimation.Running:
            p.setBrush(
                self._pulse_checked_animation
                if self.isChecked()
                else self._pulse_unchecked_animation
            )
            p.drawEllipse(
                QPointF(xPos, barRect.center().y()),
                self._pulse_radius,
                self._pulse_radius,
            )

        if self.isChecked():
            p.setBrush(self._bar_checked_brush)
            p.drawRoundedRect(barRect, rounding, rounding)
            p.setBrush(self._handle_checked_brush)

        else:
            p.setBrush(self._bar_brush)
            p.drawRoundedRect(barRect, rounding, rounding)
            p.setPen(self._light_grey_pen)
            p.setBrush(self._handle_brush)

        p.drawEllipse(QPointF(xPos, barRect.center().y()), handleRadius, handleRadius)

        p.end()

    @pyqtProperty(float)
    def handle_position(self) -> float:
        return self._handle_position

    @handle_position.setter
    def handle_position(self, pos: float) -> None:
        self._handle_position = pos
        self.update()

    @pyqtProperty(float)
    def pulse_radius(self) -> float:
        return self._pulse_radius

    @pulse_radius.setter
    def pulse_radius(self, pos: float) -> None:
        self._pulse_radius = pos
        self.update()
