from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QFrame, QHBoxLayout, 
                             QSpacerItem, QSizePolicy, QPushButton, QLineEdit, QScrollArea, QWidget, QMessageBox)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon, QPainter
import uuid
from features.book_service import BookService
from features.sell_service import SellService
from gui.dialogs.price_input_dialog import PriceInputDialog
from gui.common.styles import FONTS, COLORS, STYLES
from gui.common.utils import get_icon_path, format_price

class ElidedLabel(QLabel):
    """Un QLabel que trunca el texto con '...' si no cabe."""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumWidth(1)

    def paintEvent(self, event):
        painter = QPainter(self)
        metrics = self.fontMetrics()
        elided_text = metrics.elidedText(self.text(), Qt.ElideRight, self.width())
        painter.drawText(self.rect(), self.alignment() | Qt.AlignVCenter, elided_text)

class SaleItemWidget(QFrame):
    """Widget para mostrar un artículo en la lista de venta."""
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self._init_ui()

    def _init_ui(self):
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.setStyleSheet("""
            SaleItemWidget {
                background-color: rgba(255, 255, 255, 0.7);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 10px;
                padding: 12px;
            }
        """)
        
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(0,0,0,0)
        
        # --- Icono a la izquierda ---
        icon_label = QLabel(self)
        item_id = self.item_data.get('id', '')
        if item_id.startswith('promo_'):
            icon_name = "descuento.png"
        elif item_id.startswith('disc_'):
            icon_name = "dvd.png"
        else:
            icon_name = "libro.png"

        pixmap = QIcon(get_icon_path(icon_name)).pixmap(QSize(32, 32))
        icon_label.setPixmap(pixmap)
        icon_label.setFixedSize(42, 42)
        icon_label.setStyleSheet("background-color: #EAEAEA; border-radius: 21px; border: none;")
        icon_label.setAlignment(Qt.AlignCenter)
        
        # --- Bloque de texto a la derecha ---
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setContentsMargins(0,0,0,0)

        title = self.item_data.get('titulo', 'Artículo desconocido')
        title_label = ElidedLabel(title)
        title_label.setFont(QFont("Montserrat", 10, QFont.Weight.DemiBold))
        title_label.setStyleSheet("color: #1A202C; background: transparent; border: none;")

        quantity = self.item_data.get('cantidad', 1)
        price = self.item_data.get('precio', 0)
        details_text = f"Cantidad: {quantity}  |  Precio Unit.: ${format_price(price)}"
        details_label = QLabel(details_text)
        details_label.setFont(QFont("Montserrat", 9))
        details_label.setStyleSheet("color: #4A5568; background: transparent; border: none;")

        text_layout.addWidget(title_label)
        text_layout.addWidget(details_label)
        text_layout.addStretch() # Empuja los textos hacia arriba dentro de su bloque

        main_layout.addWidget(icon_label)
        main_layout.addLayout(text_layout, 1)

class SellBookDialog(QDialog):
    def __init__(self, book_service: BookService, sell_service: SellService, parent=None):
        super().__init__(parent)
        self.book_service = book_service
        self.sell_service = sell_service
        self.raw_sale_items = []
        self.manual_total = None
        self.setWindowTitle("Vender Artículos")

        # Configuración de la ventana
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Contenedor principal
        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("mainFrame")
        self.main_frame.setCursor(Qt.ArrowCursor)
        self.main_frame.setStyleSheet(f"""
            #mainFrame {{
                background-color: {COLORS['background_light']};
                border-radius: 15px;
                border: 1px solid {COLORS['border_light']};
            }}
        """)
        
        # Layout principal que contiene al main_frame
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.main_frame)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Layout del contenido dentro del main_frame
        content_layout = QVBoxLayout(self.main_frame)
        content_layout.setContentsMargins(25, 20, 25, 25)
        content_layout.setSpacing(0) # Reducir espaciado general

        # --- Fila de encabezado: Botón, Título y Espaciador ---
        header_layout = QHBoxLayout()
        
        # 1. Botón de Cerrar (Izquierda)
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f'''
            QPushButton {{
                background: transparent;
                color: {COLORS['text_primary']};
                border: none;
                font-size: 20px;
                font-family: Arial;
            }}
            QPushButton:hover {{
                color: {COLORS['accent_red']};
            }}
        ''')
        close_btn.clicked.connect(self.close)
        
        # 2. Título (Centro)
        title_label = QLabel("Vender Artículos")
        title_font = QFont(FONTS["family_title"], FONTS["size_large_title"], QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {COLORS['text_primary']}; background-color: transparent;")
        title_label.setAlignment(Qt.AlignCenter)
        
        # 3. Espaciador (Derecha) - para balancear el botón de cerrar
        right_spacer = QFrame()
        right_spacer.setFixedSize(30, 30)

        # Añadir los 3 widgets al layout del encabezado
        header_layout.addWidget(close_btn)
        header_layout.addWidget(title_label, 1) # El '1' permite que el título se expanda
        header_layout.addWidget(right_spacer)

        content_layout.addLayout(header_layout)

        # 1. Añadir espacio vertical
        content_layout.addSpacing(20)

        # --- Fila de Búsqueda y Acciones Rápidas (Centrada) ---
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        
        # Espaciador izquierdo para centrar el grupo de widgets
        input_layout.addStretch(1)

        # Campo de entrada para ISBN
        self.isbn_input = QLineEdit()
        self.isbn_input.setPlaceholderText("Ingresar ISBN del libro...")
        # 2. Corregir y aplicar stylesheet para el color
        input_style = f"""
            QLineEdit {{
                color: {COLORS['text_primary']};
                border: 1px solid #bdc3c7;
                border-radius: 5px;
                padding: 5px 10px;
                background-color: #FFFFFF;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS['border_focus']};
            }}
        """
        self.isbn_input.setStyleSheet(input_style)
        self.isbn_input.setFixedWidth(350) # Ancho fijo para evitar que se estire
        self.isbn_input.setFixedHeight(45)
        
        # Botones de acción rápida (Disco y Promoción)
        disc_btn = QPushButton(QIcon(get_icon_path("dvd.png")), "")
        promo_btn = QPushButton(QIcon(get_icon_path("descuento.png")), "")
        
        for btn in [disc_btn, promo_btn]:
            btn.setIconSize(QSize(28, 28))
            btn.setFixedSize(45, 45)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['background_medium']};
                    border: 1px solid {COLORS['border_light']};
                    border-radius: 8px;
                }}
                QPushButton:hover {{
                    border-color: {COLORS['border_focus']};
                }}
            """)

        input_layout.addWidget(self.isbn_input)
        input_layout.addWidget(disc_btn)
        input_layout.addWidget(promo_btn)

        # Espaciador derecho para centrar
        input_layout.addStretch(1)

        content_layout.addLayout(input_layout)

        # Línea de separación con márgenes laterales
        line_layout = QHBoxLayout()
        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet("background-color: #FEEAA5; border: none;")
        
        line_layout.addStretch(1)
        line_layout.addWidget(line, 12) # La línea ocupa 10/12 del espacio
        line_layout.addStretch(1)
        
        # Añadimos un pequeño espacio vertical para la línea
        content_layout.addSpacing(15)
        content_layout.addLayout(line_layout)
        content_layout.addSpacing(10)

        # --- Lista de artículos en venta ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll_area.setMaximumHeight(320) # Limita la altura del área de la lista
        
        items_container = QWidget()
        items_container.setStyleSheet("background: transparent;")
        
        items_columns_layout = QHBoxLayout(items_container)
        items_columns_layout.setSpacing(15)

        self.left_items_layout = QVBoxLayout()
        self.right_items_layout = QVBoxLayout()
        self.left_items_layout.setSpacing(10)
        self.right_items_layout.setSpacing(10)
        self.left_items_layout.setAlignment(Qt.AlignTop)
        self.right_items_layout.setAlignment(Qt.AlignTop)

        items_columns_layout.addLayout(self.left_items_layout)
        items_columns_layout.addLayout(self.right_items_layout)

        scroll_area.setWidget(items_container)
        content_layout.addWidget(scroll_area, 1) # Permitir que la lista se expanda

        # --- Segunda línea de separación ---
        content_layout.addSpacing(15)
        second_line_layout = QHBoxLayout()
        second_line = QFrame()
        second_line.setFixedHeight(2)
        second_line.setStyleSheet("background-color: #FEEAA5; border: none;")
        second_line_layout.addStretch(1)
        second_line_layout.addWidget(second_line, 12)
        second_line_layout.addStretch(1)
        content_layout.addLayout(second_line_layout)
        content_layout.addSpacing(15)

        # --- Sección de Totales y Confirmación ---
        totals_layout = QHBoxLayout()
        totals_layout.setSpacing(15)

        totals_layout.addStretch(1) # Empuja el contenido a la derecha

        subtotal_label = QLabel("SUBTOTAL:")
        subtotal_label.setFont(QFont(FONTS['family_title'], 14, QFont.Weight.Bold))
        subtotal_label.setStyleSheet("color: #333; background: transparent;")

        self.subtotal_input = QLineEdit("$0")
        self.subtotal_input.setFixedWidth(180)
        self.subtotal_input.setFixedHeight(45)
        self.subtotal_input.setAlignment(Qt.AlignRight)
        self.subtotal_input.setFont(QFont(FONTS['family_title'], 18, QFont.Weight.Bold))
        self.subtotal_input.setStyleSheet(f"""
            QLineEdit {{
                color: #005A9C;
                background-color: white;
                border: 1px solid {COLORS['border_medium']};
                border-radius: 8px;
                padding: 5px;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS['border_focus']};
            }}
        """)

        self.confirm_button = QPushButton("Confirmar Venta")
        self.confirm_button.setFixedHeight(45)
        self.confirm_button.setFont(QFont(FONTS['family_title'], 14, QFont.Weight.Bold))
        self.confirm_button.setCursor(Qt.PointingHandCursor)
        self.confirm_button.setStyleSheet(STYLES['button_success_full'])

        totals_layout.addWidget(subtotal_label)
        totals_layout.addWidget(self.subtotal_input)
        totals_layout.addWidget(self.confirm_button)

        content_layout.addLayout(totals_layout)
        
        # Conectar señales
        self.subtotal_input.textChanged.connect(self._format_subtotal_input)
        self.subtotal_input.editingFinished.connect(self._finalize_subtotal_edit)
        
        # Conectar botones de acción rápida
        self.isbn_input.returnPressed.connect(self._add_book_item)
        disc_btn.clicked.connect(self._add_disc_item)
        promo_btn.clicked.connect(self._add_promo_item)
        
        self.confirm_button.clicked.connect(self._confirm_sale)
        
        self.resize(800, 750)
        self._setup_ui()

    def _setup_ui(self):
        self._update_all_views()

    def _add_book_item(self):
        isbn = self.isbn_input.text().strip()
        if not isbn:
            return
        
        book_data = self.book_service.find_book_by_isbn_for_sale(isbn) # Necesitaremos este método
        if book_data:
            self.add_item_to_sale(book_data)
        else:
            QMessageBox.warning(self, "Libro no encontrado", f"No se encontró un libro disponible con el ISBN: {isbn}")
        self.isbn_input.clear()

    def _add_disc_item(self):
        dialog = PriceInputDialog(self, title="Añadir Disco", show_quantity=True)
        if dialog.exec() == QDialog.Accepted:
            price, quantity = dialog.get_values()
            disc_data = {
                'id': f'disc_{price}',
                'titulo': f'Disco Musical (${format_price(price)})',
                'precio': price,
                'cantidad': quantity
            }
            self.add_item_to_sale(disc_data)

    def _add_promo_item(self):
        promo_data = {
            'id': 'promo_10000',
            'titulo': 'Promoción de Libro',
            'precio': 10000,
            'cantidad': 1
        }
        self.add_item_to_sale(promo_data)

    def add_item_to_sale(self, item_data):
        """Añade o actualiza un artículo en la lista de venta."""
        self.manual_total = None # Resetear descuento
        
        # Añadir el item (o items si la cantidad es > 1) a la lista plana
        quantity = item_data.get('cantidad', 1)
        for _ in range(quantity):
            # Creamos una copia para cada unidad
            single_item = item_data.copy()
            single_item['cantidad'] = 1 
            self.raw_sale_items.append(single_item)

        self._update_all_views()

    def _group_items(self, items_list):
        """Agrupa una lista de items por su ID para contarlos."""
        grouped = {}
        for item in items_list:
            group_key = item.get('id')
            if group_key not in grouped:
                first_item = item.copy()
                first_item['cantidad'] = 0
                grouped[group_key] = first_item
            grouped[group_key]['cantidad'] += 1
        return list(grouped.values())

    def _update_all_views(self):
        """Función central para actualizar toda la UI basada en el estado actual."""
        base_total = self._calculate_base_total()
        display_total = self.manual_total if self.manual_total is not None else base_total

        items_to_display = self.raw_sale_items
        if self.manual_total is not None:
            items_to_display = self._get_adjusted_items(self.raw_sale_items, self.manual_total)

        self._update_subtotal_display(display_total)
        self._redraw_sale_list(items_to_display)

    def _calculate_base_total(self):
        """Calcula el total a partir de los precios originales."""
        return sum(item.get('precio', 0) for item in self.raw_sale_items)

    def _update_subtotal_display(self, amount):
        """Actualiza el QLineEdit del subtotal."""
        self.subtotal_input.blockSignals(True)
        self.subtotal_input.setText(f"${format_price(amount)}")
        self.subtotal_input.blockSignals(False)

    def _redraw_sale_list(self, items_to_display):
        """Limpia y redibuja la lista de artículos."""
        for layout in [self.left_items_layout, self.right_items_layout]:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
        
        grouped_items = self._group_items(items_to_display)
        for item_data in grouped_items:
            item_widget = SaleItemWidget(item_data)
            if self.left_items_layout.count() <= self.right_items_layout.count():
                self.left_items_layout.addWidget(item_widget)
            else:
                self.right_items_layout.addWidget(item_widget)

    def _format_subtotal_input(self):
        """Formatea el input de subtotal en tiempo real sin mover el cursor."""
        line_edit = self.subtotal_input
        line_edit.blockSignals(True)
        
        text = line_edit.text()
        cursor_pos = line_edit.cursorPosition()
        
        clean_text = "".join(filter(str.isdigit, text))
        
        if clean_text:
            number = int(clean_text)
            formatted_text = f"${format_price(number)}"
        else:
            formatted_text = "$" # Mantener el símbolo como guía
            
        line_edit.setText(formatted_text)
        
        # Lógica para restaurar la posición del cursor
        length_diff = len(formatted_text) - len(text)
        new_cursor_pos = cursor_pos + length_diff
        line_edit.setCursorPosition(max(1, new_cursor_pos)) # Mínimo 1 para estar después del '$'
        
        line_edit.blockSignals(False)

    def _finalize_subtotal_edit(self):
        """Se activa al terminar de editar el subtotal para aplicar cambios."""
        raw_text = ''.join(filter(str.isdigit, self.subtotal_input.text()))
        new_total = float(raw_text) if raw_text else 0.0
        
        base_total = self._calculate_base_total()

        if abs(new_total - base_total) < 0.01:
            self.manual_total = None
        else:
            self.manual_total = new_total
        
        self._update_all_views()

    def _get_adjusted_items(self, base_items, target_total):
        """Devuelve una nueva lista de items con precios ajustados."""
        adjusted = [item.copy() for item in base_items]
        base_total = sum(item.get('precio', 0) for item in adjusted)

        if base_total == 0:
            if target_total != 0 and adjusted:
                avg_price = target_total / len(adjusted)
                for item in adjusted: item['precio'] = avg_price
            return adjusted
        
        scale_factor = target_total / base_total
        running_total = 0
        for item in adjusted[:-1]:
            new_price = round(item['precio'] * scale_factor)
            item['precio'] = new_price
            running_total += new_price
        
        if adjusted:
            adjusted[-1]['precio'] = target_total - running_total
            
        return adjusted 

    def _confirm_sale(self):
        if not self.raw_sale_items:
            QMessageBox.warning(self, "Venta Vacía", "No hay artículos en la venta para procesar.")
            return

        total_amount = self._calculate_base_total()
        if self.manual_total is not None:
            total_amount = self.manual_total

        final_items = self._group_items(self.raw_sale_items)

        reply = QMessageBox.question(self, "Confirmar Venta",
                                     f"¿Desea finalizar la venta por un total de <b>${format_price(total_amount)}</b>?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            success, message = self.sell_service.process_sale(final_items, total_amount)
            if success:
                QMessageBox.information(self, "Éxito", message)
                self.accept() # Cerrar el diálogo si la venta es exitosa
            else:
                QMessageBox.critical(self, "Error", message) 