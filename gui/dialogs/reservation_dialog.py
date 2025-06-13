import os
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QGraphicsBlurEffect, QLineEdit, QScrollArea, QSpacerItem,
    QSizePolicy, QApplication, QMessageBox, QInputDialog, QComboBox, QGridLayout, QAbstractButton,
    QGroupBox, QTextEdit
)
from PySide6.QtGui import QFont, QMouseEvent, QPixmap, QPainter, QColor, QIcon, QIntValidator, QFontMetrics
from PySide6.QtCore import Qt, QPoint, Signal, QSize, QTimer
import uuid
from typing import List

from .price_input_dialog import PriceInputDialog

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
    remove_requested = Signal(str)
    
    def __init__(self, book_data: dict, count: int, parent=None):
        super().__init__(parent)
        self.book_data = book_data
        self.count = count
        # La clave para identificar el grupo es el ISBN, o el ID único para items genéricos.
        self.group_id = self.book_data.get('libro_isbn') or self.book_data.get('id')
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
        
        # --- Lógica de texto REFACTORIZADA ---
        price = self.book_data.get('precio_venta', 0)
        price_str = format_price_with_thousands_separator(price)

        if 'titulo' in self.book_data:
            # Es un libro
            info = f"{self.book_data['titulo']} (Pos: {self.book_data.get('posicion', 'N/A')})"
            full_text = f"{info} - {price_str}"
        else:
            # Es un item genérico (la descripción NO contiene el precio)
            base_description = self.book_data.get('descripcion', 'Item Desconocido')
            full_text = f"{base_description} - {price_str}"

        # El contador solo se aplica a libros (items que se agrupan)
        count_str = f" (x{self.count})" if self.count > 1 and 'titulo' in self.book_data else ""
        final_text = f"{full_text}{count_str}"
        
        self.info_label = ElidedLabel(final_text)
        self.info_label.setFont(QFont("Arial", 10))
        self.info_label.setStyleSheet("color: #000000; border: none; background: transparent;")
        self.info_label.setWordWrap(False)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        
        self.remove_button = QPushButton("×")
        self.remove_button.setAutoDefault(False)
        self.remove_button.setFixedSize(20, 20)
        self.remove_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4444; color: white; border: none;
                border-radius: 10px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background-color: #cc3333; }
        """)
        # Emitimos el ID del GRUPO para su eliminación
        self.remove_button.clicked.connect(lambda: self.remove_requested.emit(self.group_id))
        
        layout.addWidget(self.info_label, 1)
        layout.addWidget(self.remove_button)

class ReservationDialog(QDialog):
    """
    Diálogo moderno para gestionar la reserva y visualización de libros apartados.
    """
    def __init__(self, reservation_service: ReservationService, parent=None, blur_effect=None):
        super().__init__(parent)
        self.reservation_service = reservation_service
        self.setWindowTitle("Nueva Reserva o Venta")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setMinimumSize(770, 630)

        self.font_family = FONTS.get("family", "Arial")
        self._drag_pos = QPoint()
        self.top_bar_height = 50
        
        # --- Lógica de Estado de Precios REESTRUCTURADA ---
        self.reserved_items = []    # Lista maestra con precios ORIGINALES.
        self.displayed_items = []   # Lista con precios ajustados para la UI.
        self.manual_total = None    # Si es un float, un descuento manual está activo.

        self.current_page = 0
        self.items_per_page = 6

        self._blur_effect = blur_effect
        if self._blur_effect:
            self._blur_effect.setEnabled(False)

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
        self.close_button.setAutoDefault(False)
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
                border-radius: 8px; padding: 6px 12px; font-size: 14px; color: #000000; margin: 0px;
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
        self.client_phone_input.textChanged.connect(self._validate_phone_input)
        
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
        payment_layout.setColumnStretch(1, 1)
        
        # Total a pagar (Editable)
        total_label = QLabel("Total a Pagar:")
        total_label.setStyleSheet("color: #333; border: none; background-color: transparent;")
        self.total_amount_input = QLineEdit()
        self.total_amount_input.setPlaceholderText("$0")
        self.total_amount_input.setFont(QFont(self.font_family, 14, QFont.Weight.Bold))
        self.total_amount_input.setStyleSheet(f"""
            {input_style}
            QLineEdit {{ 
                font-size: 15px;
                color: #2E86C1;
            }}
        """)
        self.total_amount_input.textChanged.connect(self._format_total_amount_input)
        self.total_amount_input.editingFinished.connect(self.finalize_total_edit)

        # Abono
        paid_label = QLabel("Abono:")
        paid_label.setStyleSheet("color: #333; border: none; background-color: transparent;")
        self.paid_amount_input = QLineEdit()
        self.paid_amount_input.setPlaceholderText("$0")
        self.paid_amount_input.setStyleSheet(input_style)
        self.paid_amount_input.textChanged.connect(self._format_paid_amount_input)

        # Saldo Pendiente
        due_label = QLabel("Saldo Pendiente:")
        due_label.setStyleSheet("color: #333; border: none; background-color: transparent;")
        self.due_amount_label = QLabel(" $0")
        self.due_amount_label.setFont(QFont(self.font_family, 12, QFont.Weight.Bold))
        self.due_amount_label.setStyleSheet("color: #D32F2F; border: none; background-color: transparent; padding-left: 2px;")

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
        self.confirm_button.setAutoDefault(False)
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
        self.disc_button.setAutoDefault(False)
        self.disc_button.setFixedSize(40, 40)
        self.disc_button.setIcon(QIcon("app/imagenes/dvd.png"))
        self.disc_button.setIconSize(QSize(28, 28))
        self.disc_button.setStyleSheet(icon_button_style)
        self.disc_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.disc_button.clicked.connect(self.add_disc_item)

        self.promo_button = QPushButton()
        self.promo_button.setAutoDefault(False)
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
        self.items_container_layout = QVBoxLayout(self.items_display_frame)
        self.items_container_layout.setContentsMargins(8, 8, 8, 8)
        self.items_container_layout.setSpacing(6)
        
        self.no_items_label = QLabel("Aún no se han añadido items.")
        self.no_items_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_items_label.setStyleSheet("color: rgba(0, 0, 0, 0.7); background: transparent; font-style: italic;")
        self.items_container_layout.addWidget(self.no_items_label)
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
        self.prev_button.setAutoDefault(False)
        self.prev_button.setFixedSize(85, 28)
        self.prev_button.setStyleSheet(btn_style)
        self.prev_button.clicked.connect(self.prev_page)
        
        self.page_info = QLabel("")
        self.page_info.setStyleSheet("color: rgba(0, 0, 0, 0.9); background: transparent; font-size: 12px; font-weight: 500;")
        self.page_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.next_button = QPushButton("Next ▶")
        self.next_button.setAutoDefault(False)
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

    def _format_total_amount_input(self):
        """Filtra y formatea el input de total en tiempo real, manteniendo la posición del cursor."""
        line_edit = self.total_amount_input
        line_edit.blockSignals(True)

        text = line_edit.text()
        cursor_pos = line_edit.cursorPosition()
        
        clean_text = "".join(filter(str.isdigit, text))
        
        if clean_text:
            number = int(clean_text)
            formatted_text = f"{number:,}".replace(",", ".")
        else:
            formatted_text = ""
            
        line_edit.setText(formatted_text)
        
        # Recalcular la posición del cursor
        length_diff = len(formatted_text) - len(text)
        new_cursor_pos = cursor_pos + length_diff
        line_edit.setCursorPosition(max(0, new_cursor_pos))
        
        line_edit.blockSignals(False)
        self.update_due_amount()

    def finalize_total_edit(self):
        """Se llama cuando el usuario termina de editar el campo del total."""
        raw_text = ''.join(filter(str.isdigit, self.total_amount_input.text()))
        new_total = float(raw_text) if raw_text else 0.0
        
        base_total = self.get_base_total()

        # Si el usuario establece el total de vuelta al original, cancelamos el descuento.
        if abs(new_total - base_total) < 0.01:
            self.manual_total = None
        else:
            # Si no, guardamos el nuevo total manual.
            self.manual_total = new_total
        
        self.update_all_views()

    def _format_paid_amount_input(self):
        """Filtra y formatea el input de abono en tiempo real, manteniendo la posición del cursor."""
        line_edit = self.paid_amount_input
        line_edit.blockSignals(True)

        text = line_edit.text()
        cursor_pos = line_edit.cursorPosition()
        
        clean_text = "".join(filter(str.isdigit, text))
        
        if clean_text:
            number = int(clean_text)
            formatted_text = f"{number:,}".replace(",", ".")
        else:
            formatted_text = ""
            
        line_edit.setText(formatted_text)
        
        # Recalcular la posición del cursor
        length_diff = len(formatted_text) - len(text)
        new_cursor_pos = cursor_pos + length_diff
        line_edit.setCursorPosition(max(0, new_cursor_pos))
        
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
            'id': f"promo_{uuid.uuid4()}",
            'descripcion': 'Promoción',
            'precio_venta': 10000
        }
        self.add_book_item(promo_data)

    def add_disc_item(self):
        dialog = PriceInputDialog(self, title="Precio del Disco")
        if dialog.exec() == QDialog.DialogCode.Accepted:
            price = dialog.get_price()
            if price > 0:
                disc_data = {
                    'id': f"disc_{uuid.uuid4()}",
                    'descripcion': 'Disco',
                    'precio_venta': price
                }
                self.add_book_item(disc_data)

    def get_base_total(self):
        """Calcula el total a partir de los precios originales en la lista maestra."""
        return sum(item.get('precio_venta', 0) for item in self.reserved_items)

    def update_due_amount(self):
        try:
            raw_total = "".join(filter(str.isdigit, self.total_amount_input.text()))
            total = float(raw_total) if raw_total else 0
            
            raw_paid = "".join(filter(str.isdigit, self.paid_amount_input.text()))
            paid = float(raw_paid) if raw_paid else 0
            
            due = total - paid
            self.due_amount_label.setText(f"{format_price_with_thousands_separator(due)}")
        except (ValueError, TypeError):
            self.due_amount_label.setText("$ Error")

    def on_full_payment_toggled(self, checked):
        self.paid_amount_input.setDisabled(checked)
        self.update_due_amount()

    def add_book_item(self, book_data):
        # Al añadir un nuevo libro, cualquier descuento manual se resetea.
        self.manual_total = None
        self.reserved_items.append(book_data)

        # Mover a la página donde está el nuevo item
        # Como no hay descuento, reserved_items y displayed_items son equivalentes
        new_item_group_key = book_data.get('libro_isbn') or book_data.get('id')
        
        # Agrupamos la lista de reserva para encontrar el índice del grupo del nuevo item.
        grouped_items = self._group_items(self.reserved_items)
        group_keys = list(grouped_items.keys())
        
        try:
            # Encontrar el índice del grupo al que pertenece el nuevo item
            item_index_in_groups = group_keys.index(new_item_group_key)
            # Calcular a qué página corresponde ese índice
            target_page = item_index_in_groups // self.items_per_page
            self.current_page = target_page
        except ValueError:
            # Como fallback, si algo sale mal, simplemente vamos a la última página.
            total_groups = len(grouped_items)
            self.current_page = (total_groups - 1) // self.items_per_page if total_groups > 0 else 0

        self.update_all_views()

    def remove_book_group(self, group_id_to_remove: str):
        """Elimina un grupo de items y re-calcula el descuento si está activo."""
        base_total_before = self.get_base_total()
        
        discount_ratio = None
        if self.manual_total is not None and base_total_before > 0:
            discount_ratio = self.manual_total / base_total_before

        initial_count = len(self.reserved_items)
        # La clave de eliminación coincide con la de agrupación
        def get_item_id(item): return item.get('libro_isbn') or item.get('id')
        self.reserved_items = [item for item in self.reserved_items if get_item_id(item) != group_id_to_remove]
        
        if len(self.reserved_items) < initial_count:
            if discount_ratio is not None:
                new_base_total = self.get_base_total()
                self.manual_total = new_base_total * discount_ratio
            
            self.update_all_views()

    def update_all_views(self):
        """
        Función central que recalcula los precios de visualización y actualiza toda la UI.
        """
        base_total = self.get_base_total()
        display_total = base_total

        if self.manual_total is not None:
            display_total = self.manual_total
            try:
                # Obtenemos la lista de items con precios ajustados
                self.displayed_items = self._get_adjusted_items(self.reserved_items, display_total)
            except ValueError as e:
                QMessageBox.critical(self, "Error de Descuento", str(e))
                # Si hay un error (ej. precio negativo), revertimos el descuento.
                self.manual_total = None
                display_total = base_total
                self.displayed_items = [item.copy() for item in self.reserved_items]
        else:
            # Sin descuento, la lista de visualización es una copia de la lista maestra.
            self.displayed_items = [item.copy() for item in self.reserved_items]

        # Actualizamos la UI con los datos correctos
        self.update_items_display() # Usa self.displayed_items
        self.update_total_amount_display(display_total) # Muestra el total correcto
        self.update_due_amount() # Actualiza el saldo

    def update_total_amount_display(self, display_total: float):
        """Actualiza el QLineEdit del total."""
        self.total_amount_input.blockSignals(True)
        self.total_amount_input.setText(format_price_with_thousands_separator(display_total))
        self.total_amount_input.blockSignals(False)
        self.confirm_button.setEnabled(len(self.reserved_items) > 0)

    def _get_adjusted_items(self, base_items: list, target_total: float) -> list:
        """
        Toma una lista de items con precios base y devuelve una nueva lista
        con precios ajustados para que sumen el target_total.
        """
        adjusted = [item.copy() for item in base_items]
        base_total = sum(item.get('precio_venta', 0) for item in adjusted)

        if base_total == 0:
            if target_total != 0 and adjusted:
                # Si partimos de 0, distribuimos el nuevo total equitativamente
                avg_price = target_total / len(adjusted)
                for item in adjusted: item['precio_venta'] = avg_price
            # y corregimos redondeo...
        else:
            scale_factor = target_total / base_total
            running_total = 0
            for item in adjusted[:-1]:
                new_price = round(item['precio_venta'] * scale_factor)
                if new_price < 0: raise ValueError(f"El ajuste crea un precio negativo para '{item.get('titulo', 'N/A')}'.")
                item['precio_venta'] = new_price
                running_total += new_price
            
            if adjusted:
                last_item = adjusted[-1]
                last_price = target_total - running_total
                if last_price < 0: raise ValueError("El ajuste crea un precio negativo para el último item.")
                last_item['precio_venta'] = last_price

        # Verificación final de redondeo
        final_sum = sum(item.get('precio_venta', 0) for item in adjusted)
        if adjusted and abs(final_sum - target_total) > 0.01:
            adjusted[-1]['precio_venta'] += target_total - final_sum
            
        return adjusted

    def update_items_display(self):
        """
        Reconstruye la lista de widgets de items, manejando el layout correctamente
        para evitar crashes y problemas de posicionamiento.
        """
        # Limpiar el layout de todos los widgets y espaciadores, EXCEPTO de self.no_items_label
        for i in reversed(range(self.items_container_layout.count())):
            layout_item = self.items_container_layout.itemAt(i)
            widget = layout_item.widget()

            # Si es la etiqueta "no items", la saltamos y la dejamos intacta en el layout.
            if widget and widget == self.no_items_label:
                continue

            # Si es cualquier otra cosa (un libro o un espaciador), lo quitamos del layout.
            taken_item = self.items_container_layout.takeAt(i)
            
            # Y si era un widget, lo marcamos para ser eliminado de la memoria.
            if taken_item and taken_item.widget():
                taken_item.widget().deleteLater()
            # Los espaciadores simplemente se descartan al ser quitados del layout.

        grouped_items = self._group_items(self.displayed_items)
        
        # Ahora que el layout está limpio (o solo contiene a no_items_label),
        # podemos gestionar la visibilidad y añadir los nuevos items.
        self.no_items_label.setVisible(not bool(grouped_items))

        if grouped_items:
            # Paginación
            start_index = self.current_page * self.items_per_page
            end_index = start_index + self.items_per_page
            
            page_item_groups = list(grouped_items.values())[start_index:end_index]

            for group in page_item_groups:
                first_item = group['data']
                count = group['count']
                
                item_widget = BookItemWidget(first_item, count)
                item_widget.remove_requested.connect(self.remove_book_group)
                self.items_container_layout.addWidget(item_widget)

        # Añadir un espaciador al final para empujar todos los items hacia arriba.
        self.items_container_layout.addStretch(1)

        self.update_navigation()

    def update_navigation(self):
        grouped_items = self._group_items(self.displayed_items)
        total_groups = len(grouped_items)

        if total_groups == 0:
            self.page_nav.setVisible(False)
            return

        self.page_nav.setVisible(True)
        total_pages = (total_groups - 1) // self.items_per_page + 1
        
        self.page_info.setText(f"Página {self.current_page + 1} de {total_pages}")
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < total_pages - 1)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_items_display()

    def next_page(self):
        total_groups = len(self._group_items(self.displayed_items))
        total_pages = (total_groups - 1) // self.items_per_page + 1
        if self.current_page < total_pages -1:
            self.current_page += 1
            self.update_items_display()

    def confirm_reservation(self):
        client_name = self.client_name_input.text().strip()
        client_phone = self.client_phone_input.text().strip()

        if any(char.isdigit() for char in client_name):
            QMessageBox.warning(self, "Nombre Inválido", "El nombre del cliente no puede contener números.")
            return
        
        if not client_name or not client_phone:
            QMessageBox.warning(self, "Datos Incompletos", "El nombre y el teléfono del cliente son obligatorios.")
            return

        if not self.displayed_items:
            QMessageBox.warning(self, "Sin Artículos", "Agregue al menos un artículo a la reserva.")
            return

        final_items = self.displayed_items
        
        raw_total_str = "".join(filter(str.isdigit, self.total_amount_input.text()))
        final_total = float(raw_total_str) if raw_total_str else 0.0

        raw_paid_str = "".join(filter(str.isdigit, self.paid_amount_input.text()))
        paid_amount = float(raw_paid_str) if raw_paid_str else 0.0
        
        notes = self.notes_edit.toPlainText().strip()
        
        if paid_amount <= 0:
            QMessageBox.warning(self, "Abono Requerido", "No es posible crear una reserva sin un abono inicial.")
            return

        client_lookup = self.reservation_service.get_or_create_client(client_name, client_phone)
        status = client_lookup.get("status")
        client_id = client_lookup.get("client_id")

        if status == 'error':
            QMessageBox.critical(self, "Error de Cliente", client_lookup.get("message", "Ocurrió un error desconocido."))
            return
        
        if status == 'conflict':
            existing_name = client_lookup.get('existing_name', 'N/A')
            reply = QMessageBox.question(self, "Conflicto de Cliente",
                                         f"El teléfono <b>{client_phone}</b> ya está registrado a nombre de <b>{existing_name}</b>.<br><br>"
                                         "¿Desea crear la reserva para el cliente existente? "
                                         "Si elige 'No', por favor corrija el nombre o el teléfono.",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.No:
                self.client_name_input.setFocus()
                return

        if client_id is None:
            QMessageBox.critical(self, "Error de Cliente", "No se pudo obtener un ID de cliente válido.")
            return

        if paid_amount > final_total:
             QMessageBox.warning(self, "Monto Inválido", "El abono no puede ser mayor que el total a pagar.")
             return

        success, message = self.reservation_service.create_reservation(
            client_id=client_id, 
            book_items=final_items, 
            total_amount=final_total, 
            paid_amount=paid_amount,
            notes=notes
        )

        if success:
            QMessageBox.information(self, "Éxito", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"No se pudo completar la operación:\n{message}")

    def _group_items(self, items_list: list) -> dict:
        """Agrupa los items por ISBN (para libros) o por su ID único (para otros)."""
        grouped = {}
        for item in items_list:
            # La clave de agrupación es el ISBN o el ID
            key = item.get('libro_isbn') or item.get('id')
            if key not in grouped:
                grouped[key] = {'data': item, 'count': 0}
            grouped[key]['count'] += 1
        return grouped

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
        if event.button() == Qt.MouseButton.LeftButton and event.pos().y() <= self.top_bar_height:
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

    def _validate_phone_input(self, text: str):
        """Filtra el texto del QLineEdit para permitir solo dígitos."""
        clean_text = ''.join(filter(str.isdigit, text))
        if text != clean_text:
            self.client_phone_input.blockSignals(True)
            # Mover el cursor al final después de cambiar el texto
            cursor_pos = len(clean_text)
            self.client_phone_input.setText(clean_text)
            self.client_phone_input.setCursorPosition(cursor_pos)
            self.client_phone_input.blockSignals(False)