from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton,
    QFrame, QGraphicsBlurEffect
)
from PySide6.QtGui import QFont, QMouseEvent
from PySide6.QtCore import Qt, QPoint

from gui.common.styles import FONTS

class PriceInputDialog(QDialog):
    def __init__(self, parent=None, title="Ingresar Precio", value=10000, min_val=0, max_val=1000000, step=100):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._blur_effect = None
        if self.parent():
            self._blur_effect = QGraphicsBlurEffect()
            self._blur_effect.setBlurRadius(15)
            self._blur_effect.setEnabled(False)
            target_widget = self.parent().centralWidget() if hasattr(self.parent(), 'centralWidget') and self.parent().centralWidget() else self.parent()
            if target_widget and hasattr(target_widget, 'setGraphicsEffect'):
                target_widget.setGraphicsEffect(self._blur_effect)

        self.setModal(True)
        self._drag_pos = QPoint()

        self._setup_ui(title, value, min_val, max_val, step)
        self.price_input.setFocus()
        

    def _setup_ui(self, title, value, min_val, max_val, step):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        container_frame = QFrame(self)
        container_frame.setObjectName("containerFrame")
        container_frame.setStyleSheet("""
            QFrame#containerFrame {
                background-color: rgba(255, 255, 255, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 16px;
                padding: 25px;
            }
        """)
        
        frame_layout = QVBoxLayout(container_frame)
        frame_layout.setSpacing(10)

        self.title_label = QLabel(title)
        self.title_label.setFont(QFont(FONTS.get("family", "Arial"), 16, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #000000; background: transparent;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(self.title_label)

        self.price_input = QSpinBox()
        self.price_input.setRange(min_val, max_val)
        self.price_input.setSingleStep(step)
        self.price_input.setValue(value)
        self.price_input.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.price_input.setSuffix("")
        self.price_input.setFixedHeight(38)
        self.price_input.setStyleSheet("""
            QSpinBox {
                background-color: rgba(255, 255, 255, 0.7); 
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 8px; padding: 0px 10px; 
                font-size: 14px; color: #000000;
            }
            QSpinBox:focus {
                border: 1.5px solid rgba(74, 144, 226, 0.9);
            }
        """)
        frame_layout.addWidget(self.price_input)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 10, 0, 0)
        button_layout.setSpacing(10)

        self.ok_button = QPushButton("✓ OK")
        self.ok_button.setAutoDefault(True)
        self.ok_button.clicked.connect(self.accept)
        
        self.cancel_button = QPushButton("⨉ Cancelar")
        self.cancel_button.setAutoDefault(False)
        self.cancel_button.clicked.connect(self.reject)

        button_style = """
            QPushButton { 
                background-color: rgba(0, 0, 0, 0.05); 
                border: 1px solid rgba(0, 0, 0, 0.1); 
                border-radius: 8px; color: #000; font-size: 12px; 
                padding: 8px 12px;
                font-weight: 500;
                min-width: 80px;
            } 
            QPushButton:hover { background-color: rgba(0, 0, 0, 0.1); }
            QPushButton:pressed { background-color: rgba(0, 0, 0, 0.07); }
        """
        ok_button_style = """
            QPushButton { 
                background-color: #4A90E2; 
                color: white;
                border: none;
                border-radius: 8px; font-size: 12px; 
                padding: 8px 12px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover { background-color: #357ABD; }
            QPushButton:pressed { background-color: #2E6DA4; }
        """
        self.ok_button.setStyleSheet(ok_button_style)
        self.cancel_button.setStyleSheet(button_style)
        
        self.ok_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)

        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        frame_layout.addLayout(button_layout)
        main_layout.addWidget(container_frame)
        self.adjustSize()

    def get_price(self):
        return self.price_input.value()

    def _enable_blur(self, enable: bool):
        if not self._blur_effect:
            return
            
        target_widget = self.parent()
        if not target_widget:
            return

        if enable:
            if target_widget.graphicsEffect() != self._blur_effect:
                target_widget.setGraphicsEffect(self._blur_effect)
            self._blur_effect.setEnabled(True)
        else:
            if target_widget.graphicsEffect() == self._blur_effect:
                self._blur_effect.setEnabled(False)
                target_widget.setGraphicsEffect(None)
        
        target_widget.update()

    def exec(self):
        self._recenter_dialog()
        self._enable_blur(True)
        result = super().exec()
        self._enable_blur(False)
        return result

    def reject(self):
        self._enable_blur(False)
        super().reject()

    def _recenter_dialog(self):
        if self.parentWidget():
            p_geom = self.parentWidget().geometry()
            self.move(p_geom.x() + (p_geom.width() - self.width()) // 2, p_geom.y() + (p_geom.height() - self.height()) // 2)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = QPoint() 