import os
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QGraphicsBlurEffect, QLineEdit, QScrollArea, QSpacerItem,
    QSizePolicy, QApplication, QMessageBox, QInputDialog, QComboBox, QGridLayout, QAbstractButton,
    QGroupBox, QTextEdit
)
from PySide6.QtGui import QFont, QMouseEvent, QPixmap, QPainter, QColor, QIcon, QIntValidator, QFontMetrics
from PySide6.QtCore import Qt, QPoint, Signal, QSize
import uuid

# Asumiendo que los estilos y dependencias están accesibles
from gui.common.styles import FONTS, COLORS
from features.reservation_service import ReservationService
from features.utils import format_price_with_thousands_separator

class ToggleSwitch(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(False)
        self.setFixedSize(44, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        padding = 2
        handle_radius = (self.height() / 2) - padding
        
        if self.isEnabled():
            bg_color = QColor("#4A90E2") if self.isChecked() else QColor("#BDBDBD")
        else:
            bg_color = QColor("#E0E0E0")
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg_color)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), self.height() / 2, self.height() / 2)

        handle_color = QColor("#FFFFFF") if self.isEnabled() else QColor("#BDBDBD")
        painter.setBrush(handle_color)
        
        handle_x = self.width() - (handle_radius * 2) - padding if self.isChecked() else padding
            
        painter.drawEllipse(handle_x, padding, handle_radius * 2, handle_radius * 2)

class ElidedLabel(QLabel):
    def paintEvent(self, event):
        painter = QPainter(self)
        metrics = QFontMetrics(self.font())
        elided_text = metrics.elidedText(self.text(), Qt.TextElideMode.ElideRight, self.width())
        painter.drawText(self.rect(), int(self.alignment()), elided_text)

class BookItemWidget(QFrame):
    """Widget individual para cada libro en la reserva"""
    remove_requested = Signal(object)
    
    def __init__(self, book_data: dict, count: int, parent=None):
        super().__init__(parent)
        self.book_data = book_data
        self.count = count
        self.setup_ui()
    
    def setup_ui(self):
        self.setFixedHeight(45)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 8px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)
        layout.setSpacing(8)
        
        if 'titulo' in self.book_data:
            info = f"{self.book_data['titulo']} (Pos: {self.book_data.get('posicion', 'N/A')})"
        else:
            info = self.book_data.get('descripcion', 'Item')

        count_str = f" (x{self.count})" if self.count > 1 else ""
        book_info_text = f"{info}{count_str} - ${self.book_data.get('precio_venta', 0):,}"

        self.info_label = ElidedLabel(book_info_text)
        self.info_label.setFont(QFont("Arial", 10))
        self.info_label.setStyleSheet("color: #000000; border: none; background: transparent;")
        self.info_label.setWordWrap(False)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        
        self.remove_button = QPushButton()
        self.remove_button.setFixedSize(20, 20)
        
        try:
            icon_path = "gui/dialogs/icono_eliminar.png" 
            icon_pixmap = QPixmap(icon_path)
            if not icon_pixmap.isNull():
                scaled_pixmap = icon_pixmap.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.remove_button.setIcon(QIcon(scaled_pixmap))
            else:
                self.remove_button.setText("×")
        except Exception:
            self.remove_button.setText("×")
            
        self.remove_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4444; color: #000000; border: none;
                border-radius: 10px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #cc3333; }
        """)
        self.remove_button.clicked.connect(lambda: self.remove_requested.emit(self.book_data['id_inventario']))
        
        layout.addWidget(self.info_label, 1)
        layout.addWidget(self.remove_button)

class ReservationDialog(QDialog):
    """
    Diálogo moderno para gestionar la reserva y visualización de libros apartados.
    """
    def __init__(self, reservation_service: ReservationService, parent=None):
        super().__init__(parent)
        self.reservation_service = reservation_service
        self.setWindowTitle("Nueva Reserva o Venta")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setMinimumSize(770, 630)

        self.font_family = FONTS.get("family", "Arial")
        self._drag_pos = QPoint()
        self.top_bar_height = 50
        self.reserved_items = []
        self.current_page = 0
        self.items_per_page = 4 # Ajustado a la nueva altura

        self._blur_effect = None
        if self.parent():
            self._blur_effect = QGraphicsBlurEffect()
            self._blur_effect.setBlurRadius(15)
            self._blur_effect.setEnabled(False)
            target_widget = self.parent().centralWidget() if hasattr(self.parent(), 'centralWidget') else self.parent()
            if target_widget:
                target_widget.setGraphicsEffect(self._blur_effect)

        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(0)
        
        container_frame = QFrame()
        container_frame.setObjectName("containerFrame")
        container_frame.setStyleSheet(f"""
            QFrame#containerFrame {{
                background-color: rgba(255, 255, 255, 0.35);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 16px;
            }}
        """)
        main_layout.addWidget(container_frame)

        container_layout = QVBoxLayout(container_frame)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        container_layout.addSpacing(15) # Espacio añadido ANTES de la barra superior

        # TOP BAR - FIJO
        top_bar = QFrame()
        top_bar.setFixedHeight(self.top_bar_height)
        top_bar.setStyleSheet("background-color: transparent;")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(30, 10, 25, 0) # Margen revertido a un valor seguro
        
        title_label = QLabel("Reserve Books / Disks") #NO MODIFICAR
        title_font = QFont("Montserrat", 22, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #000000; background: transparent; border: none; margin-top: 5px;")
        
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(32, 32)
        self.close_button.setFont(QFont(self.font_family, 16, QFont.Weight.Bold))
        self.close_button.setStyleSheet("""
            QPushButton { background-color: transparent; border: none; border-radius: 16px; color: #000000; }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.2); }
            QPushButton:focus { outline: none; border: none; }
        """)
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button.clicked.connect(self.reject)

        top_bar_layout.addWidget(title_label)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.close_button)
        container_layout.addWidget(top_bar)

        container_layout.addSpacing(15) # Espacio existente debajo de la barra superior

        # --- CONTENIDO PRINCIPAL ---
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 0, 20, 10)
        content_layout.setSpacing(20)

        # --- COLUMNA IZQUIERDA (CLIENTE, PAGO, NOTAS) ---
        left_column = QWidget()
        left_column.setMinimumWidth(280)
        left_column_layout = QVBoxLayout(left_column)
        left_column_layout.setContentsMargins(0, 0, 0, 0)
        left_column_layout.setSpacing(0)

        title_label_style = """
            QLabel {
                font-family: 'Arial';
                font-size: 13px;
                font-weight: bold;
                color: #333;
                background-color: transparent;
                padding-left: 2px;
            }
        """

        content_frame_style = """
            QFrame {
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 8px;
                background-color: rgba(255, 255, 255, 0.2);
            }
        """

        input_style = """
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.55); border: 1px solid rgba(0, 0, 0, 0.15);
                border-radius: 8px; padding: 0 15px; font-size: 14px; color: #000000; margin: 0px;
            }
            QLineEdit:focus {
                border: 1px solid rgba(74, 144, 226, 0.8);
            }
        """

        # 1. Datos del Cliente
        client_title = QLabel("Datos del Cliente")
        client_title.setStyleSheet(title_label_style)

        client_frame = QFrame()
        client_frame.setStyleSheet(content_frame_style)
        client_layout = QVBoxLayout(client_frame)
        client_layout.setSpacing(10)
        client_layout.setContentsMargins(15, 15, 15, 15)

        self.client_name_input = QLineEdit()
        self.client_name_input.setPlaceholderText("Nombre del cliente")
        self.client_name_input.setFixedHeight(36)
        self.client_name_input.setStyleSheet(input_style)
        
        self.client_phone_input = QLineEdit()
        self.client_phone_input.setPlaceholderText("Número de contacto")
        self.client_phone_input.setFixedHeight(36)
        self.client_phone_input.setStyleSheet(input_style)
        
        client_layout.addWidget(self.client_name_input)
        client_layout.addWidget(self.client_phone_input)

        left_column_layout.addWidget(client_title)
        left_column_layout.addSpacing(5)
        left_column_layout.addWidget(client_frame)
        left_column_layout.addSpacing(15)

        # 2. Detalles del Pago
        payment_title = QLabel("Detalles del Pago")
        payment_title.setStyleSheet(title_label_style)
        
        payment_frame = QFrame()
        payment_frame.setStyleSheet(content_frame_style)
        payment_layout = QGridLayout(payment_frame)
        payment_layout.setSpacing(10)
        payment_layout.setContentsMargins(15, 15, 15, 15)

        total_label = QLabel("Total a Pagar:")
        total_label.setFont(QFont(self.font_family, 10))
        total_label.setStyleSheet("color: #000000; background: transparent; border: none;")

        self.total_amount_input = QLineEdit("0")
        self.total_amount_input.setValidator(QIntValidator(0, 9999999))
        self.total_amount_input.setFixedHeight(36)
        self.total_amount_input.setStyleSheet(input_style)
        self.total_amount_input.textChanged.connect(
            lambda text, le=self.total_amount_input: self._handle_price_text_change(le, text)
        )

        paid_label = QLabel("Pago Realizado:")
        paid_label.setFont(QFont(self.font_family, 10))
        paid_label.setStyleSheet("color: #000000; background: transparent; border: none;")

        self.paid_amount_input = QLineEdit("0")
        self.paid_amount_input.setValidator(QIntValidator(0, 9999999))
        self.paid_amount_input.setFixedHeight(36)
        self.paid_amount_input.setStyleSheet(input_style)
        self.paid_amount_input.textChanged.connect(
            lambda text, le=self.paid_amount_input: self._handle_price_text_change(le, text)
        )
        
        due_label = QLabel("Saldo Pendiente:")
        due_label.setFont(QFont(self.font_family, 10))
        due_label.setStyleSheet("color: #000000; background: transparent; border: none;")

        self.due_amount_label = QLineEdit("0")
        self.due_amount_label.setFixedHeight(36)
        self.due_amount_label.setReadOnly(True)
        self.due_amount_label.setStyleSheet("""
            QLineEdit {
                background-color: rgba(220, 220, 220, 0.7); border: 1px solid rgba(0, 0, 0, 0.15);
                border-radius: 8px; padding: 0 15px; font-size: 14px; color: #555555; margin: 0px;
            }
        """)

        payment_layout.addWidget(total_label, 0, 0)
        payment_layout.addWidget(self.total_amount_input, 0, 1)
        payment_layout.addWidget(paid_label, 1, 0)
        payment_layout.addWidget(self.paid_amount_input, 1, 1)
        payment_layout.addWidget(due_label, 2, 0)
        payment_layout.addWidget(self.due_amount_label, 2, 1)

        left_column_layout.addWidget(payment_title)
        left_column_layout.addSpacing(5)
        left_column_layout.addWidget(payment_frame)
        left_column_layout.addSpacing(15)

        # 3. Notas
        notes_title = QLabel("Notas Adicionales")
        notes_title.setStyleSheet(title_label_style)

        notes_frame = QFrame()
        notes_frame.setStyleSheet(content_frame_style)
        notes_layout = QVBoxLayout(notes_frame)
        notes_layout.setContentsMargins(15, 10, 15, 10)
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Añade notas sobre la reserva o venta...")
        self.notes_edit.setMaximumHeight(46)
        self.notes_edit.setStyleSheet("""
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.65);
                border: 1px solid rgba(0, 0, 0, 0.15);
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
                color: #000;
            }
            QTextEdit:focus {
                border: 1px solid rgba(74, 144, 226, 0.8);
            }
        """)
        notes_layout.addWidget(self.notes_edit)

        left_column_layout.addWidget(notes_title)
        left_column_layout.addSpacing(5)
        left_column_layout.addWidget(notes_frame)
        left_column_layout.addStretch()

        # Botón de Confirmar al final de la columna izquierda
        self.confirm_button = QPushButton("Confirm Transaction")
        self.confirm_button.setEnabled(False)
        self.confirm_button.setFixedHeight(50)
        self.confirm_button.setStyleSheet("""
            QPushButton { 
                background-color: #4A90E2; color: #000000; border: none; 
                border-radius: 12px; font-size: 16px; font-weight: bold; 
            }
            QPushButton:hover { background-color: #357ABD; }
            QPushButton:pressed { background-color: #2E6DA4; }
            QPushButton:focus { outline: none; border: none; }
        """)
        self.confirm_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.confirm_button.clicked.connect(self.confirm_reservation)
        left_column_layout.addWidget(self.confirm_button)

        # --- COLUMNA DERECHA (BÚSQUEDA E ITEMS) ---
        right_column = QWidget()
        right_column_layout = QVBoxLayout(right_column)
        right_column_layout.setContentsMargins(0, 0, 0, 0)
        right_column_layout.setSpacing(0)

        # 4. Búsqueda y Adición de Items
        items_title = QLabel("Búsqueda y Items")
        items_title.setStyleSheet(title_label_style)

        items_frame = QFrame()
        items_frame.setStyleSheet(content_frame_style)
        items_layout = QVBoxLayout(items_frame)
        items_layout.setSpacing(10)
        items_layout.setContentsMargins(15, 15, 15, 15)

        # Input ISBN y botones
        isbn_input_layout = QHBoxLayout()
        isbn_input_layout.setSpacing(10)
        
        self.isbn_input = QLineEdit()
        self.isbn_input.setPlaceholderText("Ingresa el ISBN y presiona Enter")
        self.isbn_input.setFixedHeight(36)
        self.isbn_input.setStyleSheet(input_style)
        self.isbn_input.returnPressed.connect(self.add_item_from_input)
        
        icon_button_style = """
            QPushButton { background-color: transparent; border: none; }
            QPushButton:hover { background-color: rgba(0, 0, 0, 0.05); border-radius: 8px; }
        """
        
        self.disc_button = QPushButton()
        self.disc_button.setFixedSize(40, 40)
        self.disc_button.setIcon(QIcon("app/imagenes/dvd.png"))
        self.disc_button.setIconSize(QSize(28, 28))
        self.disc_button.setStyleSheet(icon_button_style)
        self.disc_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.disc_button.clicked.connect(self.add_disc_item)

        self.promo_button = QPushButton()
        self.promo_button.setFixedSize(40, 40)
        self.promo_button.setIcon(QIcon("app/imagenes/descuento.png"))
        self.promo_button.setIconSize(QSize(28, 28))
        self.promo_button.setStyleSheet(icon_button_style)
        self.promo_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.promo_button.clicked.connect(self.add_promo_item)

        isbn_input_layout.addWidget(self.isbn_input)
        isbn_input_layout.addWidget(self.disc_button)
        isbn_input_layout.addWidget(self.promo_button)
        items_layout.addLayout(isbn_input_layout)

        # Frame para mostrar los items
        self.items_display_frame = QFrame()
        self.items_display_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.items_display_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: 8px;
            }
        """)
        self.visible_items_layout = QVBoxLayout(self.items_display_frame)
        self.visible_items_layout.setContentsMargins(8, 8, 8, 8)
        self.visible_items_layout.setSpacing(6)
        
        self.no_items_label = QLabel("Aún no se han añadido items.")
        self.no_items_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_items_label.setStyleSheet("color: rgba(0, 0, 0, 0.7); background: transparent; font-style: italic;")
        self.visible_items_layout.addWidget(self.no_items_label)
        items_layout.addWidget(self.items_display_frame)

        # Navegación de página
        self.page_nav = QFrame()
        self.page_nav.setFixedHeight(40)
        self.page_nav_layout = QHBoxLayout(self.page_nav)
        self.page_nav_layout.setContentsMargins(0, 0, 0, 0)
        self.page_nav_layout.setSpacing(12)
        
        btn_style = """
            QPushButton { 
                background-color: rgba(0, 0, 0, 0.05); 
                border: 1px solid rgba(0, 0, 0, 0.1); 
                border-radius: 8px; color: #000; font-size: 12px; 
                font-weight: 500;
            } 
            QPushButton:hover { background-color: rgba(0, 0, 0, 0.08); } 
            QPushButton:disabled { 
                background-color: rgba(0, 0, 0, 0.02); 
                color: rgba(0, 0, 0, 0.3); 
            }
        """
        
        self.prev_button = QPushButton("◀ Prev")
        self.prev_button.setFixedSize(85, 28)
        self.prev_button.setStyleSheet(btn_style)
        self.prev_button.clicked.connect(self.prev_page)
        
        self.page_info = QLabel("")
        self.page_info.setStyleSheet("color: rgba(0, 0, 0, 0.9); background: transparent; font-size: 12px; font-weight: 500;")
        self.page_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.next_button = QPushButton("Next ▶")
        self.next_button.setFixedSize(85, 28)
        self.next_button.setStyleSheet(btn_style)
        self.next_button.clicked.connect(self.next_page)
        
        self.page_nav_layout.addWidget(self.prev_button)
        self.page_nav_layout.addStretch()
        self.page_nav_layout.addWidget(self.page_info)
        self.page_nav_layout.addStretch()
        self.page_nav_layout.addWidget(self.next_button)
        
        items_layout.addWidget(self.page_nav)
        
        right_column_layout.addWidget(items_title)
        right_column_layout.addSpacing(5)
        right_column_layout.addWidget(items_frame)
        
        content_layout.addWidget(left_column, 1)
        content_layout.addWidget(right_column, 2)

        container_layout.addWidget(content_widget)

    def _handle_price_text_change(self, line_edit: QLineEdit, text: str):
        line_edit.blockSignals(True)
        
        cursor_pos = line_edit.cursorPosition()
        raw_text = text.replace('.', '')
        
        if raw_text.isdigit():
            formatted_text = format_price_with_thousands_separator(raw_text)
            line_edit.setText(formatted_text)
            line_edit.setCursorPosition(cursor_pos + len(formatted_text) - len(text))
        
        line_edit.blockSignals(False)
        self.update_due_amount()

    def add_item_from_input(self):
        isbn = self.isbn_input.text().strip()
        if not isbn:
            return
        self.add_book_by_isbn(isbn)

    def add_book_by_isbn(self, isbn):
        service_result = self.reservation_service.find_book_by_isbn_for_reservation(isbn)
        status = service_result.get("status")

        if status in ("no_encontrado", "no_disponible"):
            QMessageBox.warning(self, "No Disponible", f"No hay copias disponibles en el inventario para el ISBN '{isbn}'.")
            self.isbn_input.clear()
            return

        # Si hay múltiples fuentes de inventario (raro, pero posible), usamos la primera.
        source_item = service_result.get("item") or (service_result.get("items")[0] if service_result.get("items") else None)
        
        if not source_item:
            QMessageBox.critical(self, "Error", "No se pudo obtener la información del item.")
            self.isbn_input.clear()
            return

        source_id = source_item['id_inventario']
        available_quantity = source_item.get('cantidad', 0)

        # Contar cuántas copias de este item de inventario ya están en la reserva
        reserved_count = sum(1 for item in self.reserved_items if item.get('id_inventario') == source_id)

        if reserved_count < available_quantity:
            self.add_book_item(source_item.copy()) # Añadir una copia del diccionario
        else:
            QMessageBox.information(self, "No más copias", "Todas las copias disponibles de este libro ya han sido añadidas a la reserva.")
        
        self.isbn_input.clear()

    def add_promo_item(self):
        promo_data = {
            'id_inventario': f"promo_{uuid.uuid4()}",
            'tipo_item': 'promocion',
            'descripcion': 'Promoción',
            'precio_venta': 10000
        }
        self.add_book_item(promo_data)

    def add_disc_item(self):
        price, ok = QInputDialog.getInt(self, "Precio del Disco", "Ingrese el precio del disco:", 10000, 0, 1000000, 100)
        if ok:
            disc_data = {
                'id_inventario': f"disc_{uuid.uuid4()}",
                'tipo_item': 'disco',
                'descripcion': 'Disco',
                'precio_venta': price
            }
            self.add_book_item(disc_data)

    def get_total_amount(self):
        return sum(item.get('precio_venta', 0) for item in self.reserved_items)

    def update_due_amount(self):
        try:
            total_amount = int(self.total_amount_input.text().replace('.', ''))
        except (ValueError, TypeError):
            total_amount = 0
        
        try:
            paid_amount = int(self.paid_amount_input.text().replace('.', ''))
        except (ValueError, TypeError):
            paid_amount = 0
        
        due_amount = total_amount - paid_amount
        self.due_amount_label.setText(format_price_with_thousands_separator(due_amount))

    def on_full_payment_toggled(self, checked):
        self.paid_amount_input.setEnabled(not checked)
        if checked:
            total_amount = self.get_total_amount()
            self.paid_amount_input.setText(format_price_with_thousands_separator(total_amount))
        else:
            self.paid_amount_input.setText("0")

    def add_book_item(self, book_data):
        # Validación de precio
        if not book_data.get('precio_venta') or book_data.get('precio_venta') <= 0:
            QMessageBox.warning(self, "Precio Inválido", 
                                f"El libro '{book_data.get('titulo', 'N/A')}' no puede ser añadido porque su precio es cero o no es válido.")
            return

        self.reserved_items.append(book_data)
        
        total_pages = (len(self.reserved_items) - 1) // self.items_per_page
        self.current_page = total_pages
        
        self.update_items_display()

    def remove_book_widget(self, inventory_id_to_remove):
        # Encuentra y elimina el libro de la lista de datos
        self.reserved_items = [book for book in self.reserved_items if book['id_inventario'] != inventory_id_to_remove]
        
        if self.reserved_items:
            total_pages = (len(self.reserved_items) - 1) // self.items_per_page
            if self.current_page > total_pages:
                self.current_page = max(0, total_pages)
        else:
            self.current_page = 0
        
        self.update_items_display()

    def update_items_display(self):
        # Limpiar el layout actual
        while self.visible_items_layout.count():
            child = self.visible_items_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not self.reserved_items:
            no_items_label = QLabel("Aún no se han añadido items.")
            no_items_label.setStyleSheet("color: rgba(0, 0, 0, 0.7); background: transparent; font-style: italic;")
            no_items_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.visible_items_layout.addWidget(no_items_label)
        else:
            # Agrupar items para mostrarlos apilados
            grouped_items = {}
            for item in self.reserved_items:
                # La clave para agrupar es el ISBN para libros, o el tipo para otros items
                key = item.get('libro_isbn') if 'libro_isbn' in item else item.get('tipo_item')
                if key not in grouped_items:
                    grouped_items[key] = {'data': item, 'count': 0, 'ids': []}
                grouped_items[key]['count'] += 1
                grouped_items[key]['ids'].append(item['id_inventario'])

            # Mostrar libros de la página actual
            start_idx = self.current_page * self.items_per_page
            # Esto necesita ser ajustado para paginación de grupos, no de items individuales
            # Por ahora, mostraremos todos los grupos
            
            for group in grouped_items.values():
                book_widget = BookItemWidget(group['data'], group['count'])
                # Conectamos la señal para que emita el ID del *primer* item del grupo
                book_widget.remove_requested.connect(
                    lambda item_id=group['ids'][0]: self.remove_book_widget(item_id)
                )
                self.visible_items_layout.addWidget(book_widget)
            
            # Agregar espaciador para mantener la distribución
            self.visible_items_layout.addStretch()

        total_amount = self.get_total_amount()
        # Bloquear señales para evitar bucles de actualización no deseados
        self.total_amount_input.blockSignals(True)
        self.total_amount_input.setText(format_price_with_thousands_separator(total_amount))
        self.total_amount_input.blockSignals(False)
        
        self.update_due_amount()

        self.confirm_button.setEnabled(len(self.reserved_items) > 0)
        self.update_navigation()

    def update_navigation(self):
        # Mostrar navegación siempre
        self.page_nav.setVisible(True) # Asegura que la barra de navegación siempre sea visible
        
        if not self.reserved_items:
            self.page_info.setText("Página 0 de 0")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            return

        total_pages = (len(self.reserved_items) - 1) // self.items_per_page + 1
        self.page_info.setText(f"Página {self.current_page + 1} de {total_pages}")
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < total_pages - 1)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_items_display()

    def next_page(self):
        total_pages = (len(self.reserved_items) - 1) // self.items_per_page
        if self.current_page < total_pages:
            self.current_page += 1
            self.update_items_display()

    def confirm_reservation(self):
        client_name = self.client_name_input.text().strip()
        client_phone = self.client_phone_input.text().strip()
        
        if not client_name or not client_phone:
            QMessageBox.warning(self, "Datos Incompletos", "Por favor, ingrese el nombre y el teléfono del cliente.")
            return

        if not self.reserved_items:
            QMessageBox.warning(self, "Sin Items", "No hay items en la lista.")
            return

        notes = self.notes_edit.toPlainText().strip()
        
        try:
            total_amount = float(self.total_amount_input.text().replace('.', ''))
            paid_amount = float(self.paid_amount_input.text().replace('.', ''))
            due_amount = total_amount - paid_amount
        except ValueError:
            QMessageBox.warning(self, "Monto Inválido", "El monto pagado y el total deben ser números válidos.")
            return

        if due_amount < 0:
            QMessageBox.warning(self, "Saldo Inválido", "¡El saldo no puede ser negativo, confirma los datos en Detalles de pago!")
            return

        # Validaciones de pago simplificadas
        if total_amount <= 0 and len(self.reserved_items) > 0:
             QMessageBox.warning(self, "Monto Inválido", "El monto total debe ser mayor a cero.")
             return
        
        if paid_amount < 0:
            QMessageBox.warning(self, "Pago Inválido", "El monto pagado no puede ser negativo.")
            return

        is_sale = paid_amount >= total_amount

        client_id = self.reservation_service.find_or_create_client(client_name, client_phone)
        if not client_id:
            QMessageBox.critical(self, "Error de Cliente", "No se pudo encontrar o crear el cliente.")
            return

        # Para el servicio, solo enviamos los items que son libros reales del inventario
        items_for_service = [
            item for item in self.reserved_items if 'libro_isbn' in item
        ]

        if is_sale:
            # Lógica para Venta Directa
            success, message = self.reservation_service.create_direct_sale(
                client_id=client_id,
                book_items=[
                    {
                        'id_inventario': item['id_inventario'], 
                        'precio_venta': item.get('precio_venta', 0),
                        'libro_isbn': item.get('libro_isbn')
                    } 
                    for item in items_for_service
                ],
                total_amount=total_amount,
                notes=notes
            )
        else:
            # Lógica para Reserva
            success, message = self.reservation_service.create_reservation(
                client_id=client_id,
                book_items=[
                    {
                        'id_inventario': item['id_inventario'], 
                        'precio_venta': item.get('precio_venta', 0),
                        'libro_isbn': item.get('libro_isbn')
                    } 
                    for item in items_for_service
                ],
                total_amount=total_amount,
                paid_amount=paid_amount,
                notes=notes
            )

        if success:
            QMessageBox.information(self, "Transacción Exitosa", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Error en la Transacción", message)

    def _enable_blur(self, enable: bool):
        if self._blur_effect:
            self._blur_effect.setEnabled(enable)

    def exec(self):
        self._enable_blur(True)
        result = super().exec()
        self._enable_blur(False)
        return result

    def reject(self):
        self._enable_blur(False)
        super().reject()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and event.pos().y() < self.top_bar_height:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def wheelEvent(self, event):
        if self.page_nav.isVisible():
            if event.angleDelta().y() > 0:
                self.prev_page()
            else:
                self.next_page()
            event.accept()
        else:
            super().wheelEvent(event)

    def keyPressEvent(self, event):
        if self.page_nav.isVisible():
            if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Up):
                self.prev_page()
                event.accept()
            elif event.key() in (Qt.Key.Key_Right, Qt.Key.Key_Down):
                self.next_page()
                event.accept()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = QPoint()