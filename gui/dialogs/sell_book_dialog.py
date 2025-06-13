from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QFrame, QHBoxLayout, 
                             QSpacerItem, QSizePolicy, QPushButton, QLineEdit, QScrollArea, QWidget, QMessageBox, QGridLayout)
from PySide6.QtCore import Qt, QSize, QTimer
from PySide6.QtGui import QFont, QIcon, QPainter, QScreen
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

class PlaceholderWidget(QFrame):
    """Widget marcador de posición para un espacio vacío en la rejilla de venta."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.setFixedSize(320, 70)
        self.setStyleSheet("""
            PlaceholderWidget {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
            }
        """)

class SaleItemWidget(QFrame):
    """Widget para mostrar un artículo en la lista de venta, con el nuevo diseño."""
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self._init_ui()

    def _init_ui(self):
        self.setFixedSize(320, 70)
        self.setStyleSheet("""
            SaleItemWidget {
                background-color: #FFFFFF;
                border: 2px solid #6D28D9;
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        # Usar QGridLayout para un control preciso de la alineación
        main_layout = QGridLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(12)
        
        # --- Icono ---
        item_id = self.item_data.get('id', '')
        if item_id.startswith('promo_'):
            icon_name = "descuento.png"
        elif item_id.startswith('disc_'):
            icon_name = "dvd.png"
        else:
            icon_name = "libro.png"

        pixmap = QIcon(get_icon_path(icon_name)).pixmap(QSize(28, 28))
        icon_label = QLabel()
        icon_label.setPixmap(pixmap)
        icon_label.setFixedSize(40, 40)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("background-color: transparent; border: none;")

        # --- Textos (Título y detalles) ---
        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)
        
        title = self.item_data.get('titulo', 'Artículo desconocido')
        quantity = self.item_data.get('cantidad', 1)

        title_label = ElidedLabel(title)
        title_label.setFont(QFont("Montserrat", 10, QFont.Weight.DemiBold))
        title_label.setStyleSheet("color: #1A202C; background: transparent; border: none;")

        details_text = f"Cantidad: {quantity}"
        
        details_label = QLabel(details_text)
        details_label.setFont(QFont("Montserrat", 9))
        details_label.setStyleSheet("color: #718096; background: transparent; border: none;")

        text_layout.addWidget(title_label)
        text_layout.addWidget(details_label)

        # --- Precio ---
        unit_price = self.item_data.get('precio', 0)
        total_price = unit_price * quantity
        price_label = QLabel(f"${format_price(total_price)}")
        price_label.setFont(QFont("Montserrat", 10, QFont.Weight.Normal))
        price_label.setStyleSheet("color: #4A5568; background: transparent; border: none;")

        # --- Ensamblado en la rejilla ---
        main_layout.addWidget(icon_label, 0, 0, Qt.AlignCenter)
        main_layout.addLayout(text_layout, 0, 1)
        main_layout.addWidget(price_label, 0, 2, Qt.AlignCenter)
        
        # Configurar las columnas para que el texto se expanda
        main_layout.setColumnStretch(1, 1)
        main_layout.setColumnMinimumWidth(0, 40)
        main_layout.setColumnMinimumWidth(2, 60)

class SellBookDialog(QDialog):
    NUM_ITEMS_PLACEHOLDERS = 6
    
    def __init__(self, book_service: BookService, sell_service: SellService, parent=None):
        super().__init__(parent)
        self.book_service = book_service
        self.sell_service = sell_service
        self.raw_sale_items = []
        self.manual_total = None
        self.is_content_expanded = False

        self._setup_window()
        self._setup_ui()
        self._connect_signals()
        
        self._update_all_views()
        QTimer.singleShot(0, self._initial_reposition)

    def _setup_window(self):
        self.setWindowTitle("Sell Items")
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.main_frame = QFrame(self)
        self.main_frame.setObjectName("mainFrame")
        self.main_frame.setStyleSheet(f"""
            #mainFrame {{
                background-color: {COLORS['background_light']};
                border-radius: 15px;
                border: 1px solid {COLORS['border_light']};
            }}
        """)
        
        # Layout principal que contiene todo
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.main_frame)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

    def _setup_ui(self):
        content_layout = QVBoxLayout(self.main_frame)
        content_layout.setContentsMargins(25, 20, 25, 25)
        content_layout.setSpacing(20)

        # --- Fila de encabezado ---
        header_layout = self._create_header_layout()
        content_layout.addLayout(header_layout)

        # --- Fila de Búsqueda y Acciones ---
        input_layout = self._create_input_layout()
        content_layout.addLayout(input_layout)

        # --- Contenedor para la lista de artículos (inicialmente oculto) ---
        self.items_container = QWidget()
        self.items_layout = QGridLayout(self.items_container)
        self.items_layout.setSpacing(15)
        self.items_container.setVisible(False)
        content_layout.addWidget(self.items_container)

        # --- Contenedor para el pie de página (inicialmente oculto) ---
        self.footer_container = QWidget()
        footer_layout = self._create_footer_layout()
        self.footer_container.setLayout(footer_layout)
        self.footer_container.setVisible(False)
        content_layout.addWidget(self.footer_container)

    def _create_header_layout(self):
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Vender Artículos")
        title_font = QFont(FONTS["family_title"], FONTS["size_large_title"], QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {COLORS['text_primary']};")

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setAutoDefault(False)
        close_btn.setStyleSheet(f'''
            QPushButton {{ background: transparent; color: {COLORS['text_primary']}; border: none; font-size: 20px; }}
            QPushButton:hover {{ color: {COLORS['accent_red']}; }}
        ''')
        close_btn.clicked.connect(self.reject)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        return header_layout

    def _create_input_layout(self):
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        
        self.isbn_input = QLineEdit()
        self.isbn_input.setPlaceholderText("Ingresar ISBN del libro...")
        self.isbn_input.setStyleSheet(STYLES['line_edit_style'])
        self.isbn_input.setFixedWidth(350)
        self.isbn_input.setFixedHeight(45)

        self.disc_btn = QPushButton(QIcon(get_icon_path("dvd.png")), " CD")
        self.promo_btn = QPushButton(QIcon(get_icon_path("descuento.png")), " Promoción")
        
        for btn in [self.disc_btn, self.promo_btn]:
            btn.setIconSize(QSize(20, 20))
            btn.setFixedHeight(45)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setAutoDefault(False)
            btn.setFont(QFont(FONTS["family"], 10, QFont.Weight.Bold))
            btn.setStyleSheet(STYLES['button_secondary_full'])

        input_layout.addWidget(self.isbn_input)
        input_layout.addWidget(self.disc_btn)
        input_layout.addWidget(self.promo_btn)
        input_layout.addStretch()
        return input_layout

    def _create_footer_layout(self):
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 15, 0, 0)
        
        subtotal_label = QLabel("Subtotal")
        subtotal_label.setFont(QFont(FONTS['family_title'], 14, QFont.Weight.Normal))
        subtotal_label.setStyleSheet(f"color: {COLORS['text_secondary']};")

        self.subtotal_value_label = QLabel("$0")
        self.subtotal_value_label.setFont(QFont(FONTS['family_title'], 18, QFont.Weight.Bold))
        self.subtotal_value_label.setStyleSheet(f"color: {COLORS['text_primary']};")

        self.confirm_button = QPushButton("Confirmar Venta")
        self.confirm_button.setFixedHeight(45)
        self.confirm_button.setFont(QFont(FONTS['family'], 11, QFont.Weight.Bold))
        self.confirm_button.setCursor(Qt.PointingHandCursor)
        self.confirm_button.setAutoDefault(False)
        self.confirm_button.setStyleSheet(STYLES['button_success_full'])
        
        footer_layout.addWidget(subtotal_label)
        footer_layout.addSpacing(10)
        footer_layout.addWidget(self.subtotal_value_label)
        footer_layout.addStretch()
        footer_layout.addWidget(self.confirm_button)
        return footer_layout

    def _connect_signals(self):
        self.isbn_input.returnPressed.connect(self._add_book_item)
        self.disc_btn.clicked.connect(self._add_disc_item)
        self.promo_btn.clicked.connect(self._add_promo_item)
        self.confirm_button.clicked.connect(self._confirm_sale)
    
    def _expand_and_recenter(self):
        """Expande la ventana para mostrar la lista de artículos y la centra."""
        if self.is_content_expanded:
            return

        self.items_container.setVisible(True)
        self.footer_container.setVisible(True)
        
        QTimer.singleShot(0, self._reposition_window)
        self.is_content_expanded = True
    
    def _reposition_window(self):
        # Forzar la reactualización de la geometría ocultando y mostrando la ventana.
        # Es un método más robusto para que el gestor de ventanas (KDE) procese el cambio.
        self.hide()
        self.adjustSize()
        self._center_window()
        self.show()

    def _center_window(self):
        """Centra la ventana respecto al widget padre o la pantalla."""
        if self.parentWidget():
            parent_geometry = self.parentWidget().geometry()
            self.move(
                parent_geometry.x() + (parent_geometry.width() - self.width()) // 2,
                parent_geometry.y() + (parent_geometry.height() - self.height()) // 2
            )
        elif self.screen():
            screen_geometry = self.screen().availableGeometry()
            self.move(
                (screen_geometry.width() - self.width()) // 2,
                (screen_geometry.height() - self.height()) // 2
            )

    def add_item_to_sale(self, item_data):
        self.manual_total = None 
        
        quantity = item_data.get('cantidad', 1)
        for _ in range(quantity):
            single_item = item_data.copy()
            single_item['cantidad'] = 1 
            self.raw_sale_items.append(single_item)

        if not self.is_content_expanded:
            self._expand_and_recenter()

        self._update_all_views()

    def _update_all_views(self):
        base_total = sum(item.get('precio', 0) for item in self.raw_sale_items)
        display_total = self.manual_total if self.manual_total is not None else base_total

        self.subtotal_value_label.setText(f"${format_price(display_total)}")
        self._redraw_sale_list()

    def _redraw_sale_list(self):
        # Limpiar layout existente
        while self.items_layout.count():
            child = self.items_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        grouped_items = self._group_items(self.raw_sale_items)

        # Añadir widgets de artículos
        for i, item_data in enumerate(grouped_items):
            widget = SaleItemWidget(item_data)
            row, col = divmod(i, 2)
            self.items_layout.addWidget(widget, row, col)

        # Rellenar con marcadores de posición
        num_items = len(grouped_items)
        for i in range(num_items, self.NUM_ITEMS_PLACEHOLDERS):
            placeholder = PlaceholderWidget()
            row, col = divmod(i, 2)
            self.items_layout.addWidget(placeholder, row, col)

    def _group_items(self, items_list):
        grouped = {}
        for item in items_list:
            group_key = item.get('id')
            if group_key not in grouped:
                first_item = item.copy()
                first_item['cantidad'] = 0
                grouped[group_key] = first_item
            grouped[group_key]['cantidad'] += 1
        return list(grouped.values())

    # --- Métodos de lógica de negocio (sin cambios importantes) ---

    def _add_book_item(self):
        isbn = self.isbn_input.text().strip()
        if not isbn:
            return

        # Comprobar cuántas unidades de este libro ya están en el carrito
        current_count_in_cart = sum(1 for item in self.raw_sale_items if item.get('id') == isbn)
        
        result = self.sell_service.find_book_by_isbn_for_sale(isbn)
        
        if result:
            book_data = result['book_data']
            stock = result['stock']
            
            if current_count_in_cart < stock:
                self.add_item_to_sale(book_data)
            else:
                QMessageBox.warning(self, "Stock insuficiente", 
                                    f"No hay más unidades disponibles en el inventario para el libro con ISBN: {isbn}. "
                                    f"Ya tiene {current_count_in_cart} en la venta.")
        else:
            QMessageBox.warning(self, "Libro no encontrado", f"No se encontró un libro disponible con el ISBN: {isbn}")
        self.isbn_input.clear()

    def _add_disc_item(self):
        dialog = PriceInputDialog(self, title="Añadir Disco", show_quantity=True, default_price=5000)
        if dialog.exec() == QDialog.Accepted:
            price, quantity = dialog.get_values()
            disc_data = {
                'id': f'disc_{int(price)}',
                'titulo': 'Disco Musical',
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

    def _confirm_sale(self):
        if not self.raw_sale_items:
            QMessageBox.warning(self, "Venta Vacía", "No hay artículos en la venta para procesar.")
            return

        base_total = sum(item.get('precio', 0) for item in self.raw_sale_items)
        total_amount = self.manual_total if self.manual_total is not None else base_total
        final_items = self._group_items(self.raw_sale_items)

        reply = QMessageBox.question(self, "Confirmar Venta",
                                     f"¿Desea finalizar la venta por un total de <b>${format_price(total_amount)}</b>?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            success, message = self.sell_service.process_sale(final_items, total_amount)
            if success:
                QMessageBox.information(self, "Éxito", message)
                self.accept()
            else:
                QMessageBox.critical(self, "Error", message)

    def _initial_reposition(self):
        self.adjustSize()
        self._center_window()