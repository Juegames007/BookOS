from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QFrame, QHBoxLayout, 
                             QSpacerItem, QSizePolicy, QPushButton, QLineEdit, QScrollArea, QWidget, QMessageBox, QGridLayout)
from PySide6.QtCore import Qt, QSize, QTimer, Signal
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
    remove_item = Signal(str)

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
        
        # Configurar las columnas para que el tegxto se expanda
        main_layout.setColumnStretch(1, 1)
        main_layout.setColumnMinimumWidth(0, 40)
        main_layout.setColumnMinimumWidth(2, 60)

        # --- Botón de Eliminar ---
        remove_btn = QPushButton("×", self)
        remove_btn.setFixedSize(22, 22)
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #FEE2E2;
                color: #EF4444;
                border: none;
                border-radius: 11px;
                font-family: "Arial";
                font-size: 16px;
                font-weight: bold;
                padding-bottom: 2px;
            }
            QPushButton:hover { background-color: #FECACA; }
            QPushButton:pressed { background-color: #FCA5A5; }
        """)
        remove_btn.move(self.width() - remove_btn.width() - 5, 5)
        remove_btn.raise_()
        
        item_id_to_remove = self.item_data.get('id')
        remove_btn.clicked.connect(lambda: self.remove_item.emit(item_id_to_remove))

class SellBookDialog(QDialog):
    NUM_ITEMS_PER_PAGE = 6
    
    def __init__(self, book_service: BookService, sell_service: SellService, parent=None):
        super().__init__(parent)
        self.book_service = book_service
        self.sell_service = sell_service
        self.raw_sale_items = []
        self.manual_total = None
        self.is_content_expanded = False
        self.current_page = 0

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

        # --- Fila de Paginación ---
        self.page_nav_container = QWidget()
        nav_layout = self._create_navigation_layout()
        self.page_nav_container.setLayout(nav_layout)
        self.page_nav_container.setVisible(False)
        content_layout.addWidget(self.page_nav_container)

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

    def _create_navigation_layout(self):
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(0, 10, 0, 0)
        
        btn_style = """
            QPushButton { 
                background-color: rgba(0, 0, 0, 0.05); 
                border: 1px solid rgba(0, 0, 0, 0.1); 
                border-radius: 8px; color: #000; font-size: 12px; 
                font-weight: 500; padding: 5px 10px;
            } 
            QPushButton:hover { background-color: rgba(0, 0, 0, 0.08); } 
            QPushButton:disabled { 
                background-color: rgba(0, 0, 0, 0.02); 
                color: rgba(0, 0, 0, 0.3); 
            }
        """
        
        self.prev_button = QPushButton("◀ Anterior")
        self.prev_button.setAutoDefault(False)
        self.prev_button.setStyleSheet(btn_style)
        
        self.page_info_label = QLabel("")
        self.page_info_label.setAlignment(Qt.AlignCenter)
        self.page_info_label.setStyleSheet("color: #333; font-size: 12px; font-weight: 500;")

        self.next_button = QPushButton("Siguiente ▶")
        self.next_button.setAutoDefault(False)
        self.next_button.setStyleSheet(btn_style)

        nav_layout.addWidget(self.prev_button)
        nav_layout.addStretch(1)
        nav_layout.addWidget(self.page_info_label)
        nav_layout.addStretch(1)
        nav_layout.addWidget(self.next_button)
        
        return nav_layout

    def _create_footer_layout(self):
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 15, 0, 0)
        
        subtotal_label = QLabel("Subtotal")
        subtotal_label.setFont(QFont(FONTS['family_title'], 14, QFont.Weight.Normal))
        subtotal_label.setStyleSheet(f"color: {COLORS['text_secondary']};")

        self.subtotal_input = QLineEdit("$0")
        self.subtotal_input.setFixedWidth(180)
        self.subtotal_input.setFixedHeight(45)
        self.subtotal_input.setAlignment(Qt.AlignRight)
        self.subtotal_input.setFont(QFont(FONTS['family'], 18, QFont.Weight.Bold))
        self.subtotal_input.setStyleSheet(f"""
            QLineEdit {{
                color: {COLORS['text_primary']};
                background-color: white;
                border: 1px solid {COLORS['border_medium']};
                border-radius: 8px;
                padding-right: 10px;
            }}
            QLineEdit:focus {{
                border: 2px solid {COLORS['border_focus']};
            }}
        """)

        self.apply_discount_button = QPushButton(QIcon(get_icon_path("actualizar.png")), "")
        self.apply_discount_button.setFixedSize(45, 45)
        self.apply_discount_button.setIconSize(QSize(22, 22))
        self.apply_discount_button.setCursor(Qt.PointingHandCursor)
        self.apply_discount_button.setAutoDefault(False)
        self.apply_discount_button.setStyleSheet(STYLES['button_secondary_full'].replace("font-weight: bold;", ""))

        self.confirm_button = QPushButton("Confirmar Venta")
        self.confirm_button.setFixedHeight(45)
        self.confirm_button.setFont(QFont(FONTS['family'], 11, QFont.Weight.Bold))
        self.confirm_button.setCursor(Qt.PointingHandCursor)
        self.confirm_button.setAutoDefault(False)
        self.confirm_button.setStyleSheet(STYLES['button_success_full'])
        
        footer_layout.addWidget(subtotal_label)
        footer_layout.addSpacing(10)
        footer_layout.addWidget(self.subtotal_input)
        footer_layout.addWidget(self.apply_discount_button)
        footer_layout.addStretch()
        footer_layout.addWidget(self.confirm_button)
        return footer_layout

    def _connect_signals(self):
        self.isbn_input.returnPressed.connect(self._add_book_item)
        self.disc_btn.clicked.connect(self._add_disc_item)
        self.promo_btn.clicked.connect(self._add_promo_item)
        self.confirm_button.clicked.connect(self._confirm_sale)
        self.subtotal_input.textChanged.connect(self._format_subtotal_input)
        self.subtotal_input.editingFinished.connect(self._finalize_subtotal_edit)
        self.apply_discount_button.clicked.connect(self._finalize_subtotal_edit)
        self.prev_button.clicked.connect(self._prev_page)
        self.next_button.clicked.connect(self._next_page)
    
    def _expand_and_recenter(self):
        """Expande la ventana para mostrar la lista de artículos y la centra."""
        if self.is_content_expanded:
            return

        self.items_container.setVisible(True)
        self.footer_container.setVisible(True)
        self.page_nav_container.setVisible(True)
        
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
        
        # --- Lógica para añadir items y navegar a su página ---
        # Guardamos el ID para encontrarlo después
        item_id = item_data.get('id')

        quantity = item_data.get('cantidad', 1)
        for _ in range(quantity):
            single_item = item_data.copy()
            single_item['cantidad'] = 1 
            self.raw_sale_items.append(single_item)

        if not self.is_content_expanded:
            self._expand_and_recenter()
        
        # Agrupar para encontrar la página del nuevo item
        grouped_items = self._group_items(self.raw_sale_items)
        try:
            # Encontrar el índice del grupo al que pertenece el nuevo item
            group_keys = [g['id'] for g in grouped_items]
            item_index_in_groups = group_keys.index(item_id)
            # Calcular a qué página corresponde
            self.current_page = item_index_in_groups // self.NUM_ITEMS_PER_PAGE
        except ValueError:
            # Si algo falla, vamos a la última página como fallback
            total_groups = len(grouped_items)
            self.current_page = (total_groups - 1) // self.NUM_ITEMS_PER_PAGE if total_groups > 0 else 0

        self._update_all_views()

    def _update_all_views(self):
        base_total = self._calculate_base_total()
        display_total = self.manual_total if self.manual_total is not None else base_total

        self._update_subtotal_display(display_total)

        items_to_display = self.raw_sale_items
        if self.manual_total is not None:
            items_to_display = self._get_adjusted_items(self.raw_sale_items, self.manual_total)

        self._redraw_sale_list(items_to_display)
        self._update_navigation()

    def _redraw_sale_list(self, items_to_display):
        """Redibuja la lista de artículos en venta en la rejilla."""
        # Limpiar layout existente
        while self.items_layout.count():
            child = self.items_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        grouped_items = self._group_items(items_to_display)
        
        # Paginación
        start_index = self.current_page * self.NUM_ITEMS_PER_PAGE
        end_index = start_index + self.NUM_ITEMS_PER_PAGE
        page_item_groups = grouped_items[start_index:end_index]

        # Añadir widgets de artículos
        for i, item_data in enumerate(page_item_groups):
            widget = SaleItemWidget(item_data)
            widget.remove_item.connect(self._remove_item_by_id)
            row, col = divmod(i, 2)
            self.items_layout.addWidget(widget, row, col)

        # Rellenar con marcadores de posición
        num_items = len(page_item_groups)
        for i in range(num_items, self.NUM_ITEMS_PER_PAGE):
            placeholder = PlaceholderWidget()
            row, col = divmod(i, 2)
            self.items_layout.addWidget(placeholder, row, col)

        self.items_container.setVisible(len(items_to_display) > 0)
        self.footer_container.setVisible(len(items_to_display) > 0)

    def _group_items(self, items_list):
        """Agrupa los artículos por ID, sumando las cantidades."""
        grouped = {}
        for item in items_list:
            group_key = item.get('id')
            if group_key not in grouped:
                # Si no existe, creamos una entrada base. Hacemos una copia para no mutar el original.
                first_item = item.copy()
                first_item['cantidad'] = 0
                grouped[group_key] = first_item
            
            # Sumamos la cantidad del artículo actual.
            grouped[group_key]['cantidad'] += item.get('cantidad', 1)
            
        return list(grouped.values())

    def _remove_item_by_id(self, item_id_to_remove):
        """Elimina una sola unidad de un artículo de la venta por su ID."""
        # Al eliminar un item, cualquier descuento manual se resetea para evitar inconsistencias.
        self.manual_total = None

        item_found = False
        for i, item in enumerate(self.raw_sale_items):
            if item.get('id') == item_id_to_remove:
                self.raw_sale_items.pop(i)
                item_found = True
                break
        
        if item_found:
            self._update_all_views()
        
        # Si la lista de venta queda vacía, volvemos al estado inicial
        if not self.raw_sale_items and self.is_content_expanded:
            self._collapse_to_initial_state()

    def _collapse_to_initial_state(self):
        """Contrae la ventana a su estado inicial, ocultando la lista y el pie de página."""
        self.is_content_expanded = False
        self.items_container.setVisible(False)
        self.footer_container.setVisible(False)
        self.page_nav_container.setVisible(False)
        QTimer.singleShot(0, self._reposition_window)

    def _update_navigation(self):
        total_groups = len(self._group_items(self.raw_sale_items))
        has_items = total_groups > 0
        
        self.page_nav_container.setVisible(has_items)

        if not has_items:
            return

        total_pages = (total_groups - 1) // self.NUM_ITEMS_PER_PAGE + 1
        
        self.page_info_label.setText(f"Página {self.current_page + 1} de {total_pages}")
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < total_pages - 1)

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._update_all_views()

    def _next_page(self):
        total_groups = len(self._group_items(self.raw_sale_items))
        total_pages = (total_groups - 1) // self.NUM_ITEMS_PER_PAGE + 1
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self._update_all_views()

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
        """Añade un CD a la venta, pidiendo precio y cantidad."""
        dialog = PriceInputDialog(self, title="Añadir Disco", show_quantity=True, default_price=5000)
        if dialog.exec() == QDialog.Accepted:
            price, quantity = dialog.get_values()
            
            if price > 0 and quantity > 0:
                disc_data = {
                    'id': f'disc_{int(price)}',  # ID dinámico para agrupar por precio
                    'titulo': 'Disco Musical',
                    'precio': price,
                    'cantidad': quantity
                }
                self.add_item_to_sale(disc_data)

    def _add_promo_item(self):
        """Añade un artículo de promoción con precio y ID fijos."""
        promo_data = {
            'id': 'promo_10000',
            'titulo': 'Promoción de Libro',
            'precio': 10000,
            'cantidad': 1
        }
        self.add_item_to_sale(promo_data)

    def _confirm_sale(self):
        """
        Confirma la venta, procesa los artículos y cierra el diálogo.
        """
        if not self.raw_sale_items:
            QMessageBox.warning(self, "Venta Vacía", "No hay artículos en la lista para vender.")
            return

        total_amount = self.manual_total if self.manual_total is not None else self._calculate_base_total()
        final_items = self._group_items(self.raw_sale_items)
        
        # Llamar al servicio de venta para procesar la transacción
        success, message = self.sell_service.process_sale(
            items=final_items,
            total_amount=total_amount
        )

        if success:
            QMessageBox.information(self, "Venta Exitosa", message)
            self.accept()  # Cierra el diálogo con éxito
        else:
            QMessageBox.critical(self, "Error en la Venta", message)

    def _initial_reposition(self):
        self.adjustSize()
        self._center_window()

    def _calculate_base_total(self):
        """Calcula el total a partir de los precios originales de los items."""
        return sum(item.get('precio', 0) for item in self.raw_sale_items)

    def _update_subtotal_display(self, amount):
        """Actualiza el QLineEdit del subtotal sin emitir señales."""
        self.subtotal_input.blockSignals(True)
        self.subtotal_input.setText(f"${format_price(amount)}")
        self.subtotal_input.blockSignals(False)

    def _format_subtotal_input(self):
        """Da formato al texto del subtotal con separadores de miles mientras se escribe."""
        line_edit = self.subtotal_input
        line_edit.blockSignals(True)
        
        text = line_edit.text()
        cursor_pos = line_edit.cursorPosition()
        
        clean_text = "".join(filter(str.isdigit, text))
        
        if clean_text:
            number = int(clean_text)
            formatted_text = f"${format_price(number)}"
        else:
            formatted_text = "$"
            
        line_edit.setText(formatted_text)
        
        length_diff = len(formatted_text) - len(text)
        new_cursor_pos = cursor_pos + length_diff
        line_edit.setCursorPosition(max(1, new_cursor_pos))
        
        line_edit.blockSignals(False)

    def _finalize_subtotal_edit(self):
        """Se activa al terminar de editar para aplicar el total manual."""
        raw_text = ''.join(filter(str.isdigit, self.subtotal_input.text()))
        new_total = float(raw_text) if raw_text else 0.0
        
        base_total = self._calculate_base_total()

        if abs(new_total - base_total) < 0.01:
            self.manual_total = None
        else:
            self.manual_total = new_total
        
        self._update_all_views()

    def _get_adjusted_items(self, base_items, target_total):
        """Devuelve una nueva lista de items con precios ajustados proporcionalmente."""
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