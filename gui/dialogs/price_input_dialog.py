from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton,
    QFrame, QGraphicsBlurEffect, QLineEdit, QDialogButtonBox
)
from PySide6.QtGui import QFont, QMouseEvent
from PySide6.QtCore import Qt, QPoint

from gui.common.styles import FONTS, STYLES

class PriceInputDialog(QDialog):
    def __init__(self, parent=None, title="Ingresar Valor", show_quantity=False, default_price=0, default_quantity=1):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._price = default_price
        self._quantity = default_quantity
        self._last_price_text = "" # Para arreglar bug del cursor

        self.setModal(True)
        self.setFixedWidth(350)
        self._drag_pos = QPoint()

        self._setup_ui(title, show_quantity, default_price, default_quantity)
        self.price_input.setFocus()
        self._format_price_input() # Formato inicial
        
    def _setup_ui(self, title, show_quantity, default_price, default_quantity):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        container_frame = QFrame()
        container_frame.setObjectName("containerFrame")
        container_frame.setStyleSheet("""
            #containerFrame {
                background-color: #ECEFF1;
                border-radius: 15px;
                border: 1px solid #CFD8DC;
            }
        """)
        
        frame_layout = QVBoxLayout(container_frame)
        frame_layout.setSpacing(15)
        frame_layout.setContentsMargins(20, 15, 20, 20)

        self.title_label = QLabel(title)
        self.title_label.setFont(QFont(FONTS.get("family", "Arial"), 16, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #263238; background: transparent;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        frame_layout.addWidget(self.title_label)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)

        price_label = QLabel("Precio:")
        price_label.setStyleSheet("color: #37474F; font-size: 14px;")
        self.price_input = QLineEdit()
        self.price_input.setStyleSheet("""
            QLineEdit {
                background-color:rgb(255, 255, 255);
                color:rgb(0, 0, 0);
                border: 1px solid rgb(53, 67, 75);
                border-radius: 5px;
                padding: 8px 6px;
                font-size: 14px;
            }
        """)
        self.price_input.textChanged.connect(self._format_price_input)
        self.price_input.setText(str(default_price))
        self.price_input.setFixedWidth(100)

        self.quantity_label = QLabel("Cantidad:")
        self.quantity_label.setStyleSheet("color: #37474F; font-size: 14px;")
        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setButtonSymbols(QSpinBox.NoButtons)
        self.quantity_spinbox.setMinimum(1)
        self.quantity_spinbox.setMaximum(100)
        self.quantity_spinbox.setValue(default_quantity)
        self.quantity_spinbox.setStyleSheet("""
            QSpinBox {
                padding: 8px 4px;
                border: 1px solid #B0BEC5; border-radius: 5px;
                background-color: white; color: black;
                text-align: center;
                font-size: 14px;
            }
        """)
        self.quantity_spinbox.setFixedWidth(40)

        input_layout.addStretch()
        input_layout.addWidget(price_label)
        input_layout.addWidget(self.price_input)
        input_layout.addSpacing(15)
        input_layout.addWidget(self.quantity_label)
        input_layout.addWidget(self.quantity_spinbox)
        input_layout.addStretch()

        self.quantity_label.setVisible(show_quantity)
        self.quantity_spinbox.setVisible(show_quantity)
        
        frame_layout.addLayout(input_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.setStyleSheet(f"QPushButton {{ min-width: 80px; padding: 8px; }}")
        ok_button = button_box.button(QDialogButtonBox.Ok)
        ok_button.setStyleSheet(STYLES['button_success_full'])
        cancel_button = button_box.button(QDialogButtonBox.Cancel)
        cancel_button.setStyleSheet(STYLES['button_danger_full'])

        frame_layout.addWidget(button_box, alignment=Qt.AlignCenter)
        main_layout.addWidget(container_frame)
        self.adjustSize()
    
    def _format_price_input(self):
        line_edit = self.price_input
        text = line_edit.text()
        cursor_pos = line_edit.cursorPosition()

        clean_text = "".join(filter(str.isdigit, text))

        if not clean_text:
            self._price = 0
            formatted_text = ""
        else:
            value = int(clean_text)
            self._price = value
            formatted_text = f"{value:,}".replace(",", ".")

        if text != formatted_text:
            line_edit.blockSignals(True)
            line_edit.setText(formatted_text)
            line_edit.blockSignals(False)

            text_before_cursor = text[:cursor_pos]
            separators_before_cursor_old = text_before_cursor.count('.')
            
            new_text_before_cursor_part = formatted_text[:len(text_before_cursor)]
            separators_before_cursor_new = new_text_before_cursor_part.count('.')

            len_diff = len(formatted_text) - len(text)
            cursor_adjustment = len_diff - (separators_before_cursor_new - separators_before_cursor_old)
            
            new_cursor_pos = cursor_pos + cursor_adjustment
            
            if len(clean_text) > 0 and int(clean_text) == 0 and len(text) > 1 :
                 new_cursor_pos = cursor_pos

            line_edit.setCursorPosition(max(0, new_cursor_pos))

    def accept(self):
        price_text = "".join(filter(str.isdigit, self.price_input.text()))
        self._price = int(price_text) if price_text else 0
        self._quantity = self.quantity_spinbox.value()
        
        if self._price <= 0:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Precio Inválido", "El precio del artículo debe ser mayor que cero.")
            return

        super().accept()

    def get_values(self):
        return self._price, self._quantity

    def exec(self):
        return super().exec()

    def reject(self):
        super().reject()

    def _recenter_dialog(self):
        if self.parentWidget():
            p_geom = self.parentWidget().geometry()
            self.move(p_geom.x() + (p_geom.width() - self.width()) // 2, p_geom.y() + (p_geom.height() - self.height()) // 2)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = QPoint() 