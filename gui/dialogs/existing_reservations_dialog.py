from PySide6.QtWidgets import (QDialog, QVBoxLayout, QListWidget, QListWidgetItem, 
                             QWidget, QHBoxLayout, QLabel, QPushButton, QFrame,
                             QSizePolicy, QStackedWidget, QLineEdit, QMessageBox, QButtonGroup,
                             QGraphicsDropShadowEffect, QInputDialog)
from PySide6.QtGui import (QFont, QPainter, QColor, QBrush, QPen, QFontMetrics,
                         QFontDatabase, QPainterPath, QPixmap)
from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QPoint, QEasingCurve, Property
from datetime import datetime
from features.reservation_service import ReservationService
from gui.resources.sfsymbols import SFSymbols
from gui.common.utils import format_price

class ElidedLabel(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumWidth(1)

    def paintEvent(self, event):
        painter = QPainter(self)
        metrics = self.fontMetrics()
        elided_text = metrics.elidedText(self.text(), Qt.ElideRight, self.width())
        painter.drawText(self.rect(), self.alignment() | Qt.AlignVCenter, elided_text)

class ReservationItemWidget(QFrame):
    def __init__(self, reservation_data, parent=None):
        super().__init__(parent)
        self.reservation_data = reservation_data
        self.setCursor(Qt.PointingHandCursor)
        self.is_checked = False
        self.init_ui()
        self.setProperty("checked", self.is_checked)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(102, 126, 234, 40))
        shadow.setOffset(0, 2)
        shadow.setEnabled(False)
        self.setGraphicsEffect(shadow)
        self.shadow_effect = shadow

    def setChecked(self, checked):
        if self.is_checked != checked:
            self.is_checked = checked
            self.shadow_effect.setEnabled(checked)
            self.setProperty("checked", checked)
            self.style().unpolish(self)
            self.style().polish(self)
            self.update()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        icon_label = QLabel(self)
        icon = SFSymbols.get_icon("person.add", color="white")
        icon_label.setPixmap(icon.pixmap(QSize(28, 28)))
        icon_label.setFixedSize(42, 42)
        icon_label.setStyleSheet("background-color: #333; border-radius: 21px;")
        icon_label.setAlignment(Qt.AlignCenter)
        
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0,0,0,0)
        content_layout.setSpacing(15)

        client_title_label = QLabel("Nombre del cliente:")
        client_title_label.setFont(QFont("Montserrat", 11, QFont.Weight.DemiBold))
        client_title_label.setStyleSheet("color: #4A5568;")
        
        client_name_label = ElidedLabel(self.reservation_data.get('cliente_nombre', 'N/A'))
        client_name_label.setFont(QFont("Montserrat", 11))
        client_name_label.setStyleSheet("color: #1A202C;")
        client_name_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

        res_id_widget = QWidget()
        res_id_layout = QHBoxLayout(res_id_widget)
        res_id_layout.setContentsMargins(0,0,0,0)
        res_id_layout.setSpacing(8)
        res_id_layout.setAlignment(Qt.AlignRight)

        res_title_label = QLabel("Num Reserva:")
        res_title_label.setFont(QFont("Montserrat", 11, QFont.Weight.DemiBold))
        res_title_label.setStyleSheet("color: #4A5568;")
        
        res_id_label = QLabel(str(self.reservation_data.get('id_reserva', 'N/A')))
        res_id_label.setFont(QFont("Montserrat", 11))
        res_id_label.setStyleSheet("color: #1A202C;")
        
        res_id_layout.addWidget(res_title_label)
        res_id_layout.addWidget(res_id_label)

        content_layout.addWidget(client_title_label)
        content_layout.addWidget(client_name_label, 1)
        content_layout.addWidget(res_id_widget)

        content_widget.setObjectName("contentWidget")

        main_layout.addWidget(icon_label)
        main_layout.addWidget(content_widget, 1)

        self.setObjectName("ReservationItemWidget")
        # Nivel 3: Elementos individuales - Color sólido más destacado
        self.setStyleSheet("""
            #ReservationItemWidget { 
                background-color: rgba(255, 255, 255, 0.85); 
                border: 2px solid #E2E8F0; 
                border-radius: 14px; 
            }
            #ReservationItemWidget:hover { 
                border-color: #667EEA;
                background-color: rgba(255, 255, 255, 0.95);
            }
            #ReservationItemWidget[checked="true"] {
                background-color: rgba(235, 244, 255, 0.9);
                border: 2px solid rgba(102, 126, 234, 0.9);
            }
            #contentWidget, #contentWidget * {
                background: transparent;
                border: none;
            }
        """)

    def sizeHint(self):
        return QSize(super().sizeHint().width(), 75)

class ReservedItemWidget(QFrame):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.init_ui()

    def init_ui(self):
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.setStyleSheet("""
            ReservedItemWidget {
                background-color: rgba(255, 255, 255, 0.7);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 10px;
                padding: 8px;
            }
        """)
        self.setMinimumHeight(75)

        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(12)

        icon_label = QLabel(self)
        
        item_id = self.item_data.get('libro_isbn', '')
        if item_id.startswith('promo_'):
            icon_path = "app/imagenes/descuento.png"
        elif item_id.startswith('disc_'):
            icon_path = "app/imagenes/dvd.png"
        else:
            icon_path = "app/imagenes/libro.png"

        pixmap = QPixmap(icon_path)
        icon_label.setPixmap(pixmap.scaled(QSize(32, 32), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setFixedSize(42, 42)
        icon_label.setStyleSheet("background-color: #EAEAEA; border-radius: 21px; border: none;")
        icon_label.setAlignment(Qt.AlignCenter)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setContentsMargins(0,0,0,0)

        title = self.item_data.get('titulo', 'Artículo desconocido')
        title_label = ElidedLabel(title)
        title_label.setFont(QFont("Montserrat", 10, QFont.Weight.DemiBold))
        title_label.setStyleSheet("color: #1A202C; background: transparent; border: none;")

        quantity = self.item_data.get('cantidad', 1)
        price = self.item_data.get('precio_unitario', 0)
        details_text = f"Cantidad: {quantity}  |  Precio Unit.: {format_price(price)}"
        details_label = QLabel(details_text)
        details_label.setFont(QFont("Montserrat", 9))
        details_label.setStyleSheet("color: #4A5568; background: transparent; border: none;")

        text_layout.addWidget(title_label)
        text_layout.addWidget(details_label)
        text_layout.addStretch()

        main_layout.addWidget(icon_label)
        main_layout.addLayout(text_layout, 1)

class ExistingReservationsDialog(QDialog):
    def __init__(self, reservation_service: ReservationService, parent=None):
        super().__init__(parent)
        self.reservation_service = reservation_service
        self._current_view_pos = QPoint(0,0)
        self.is_moving_forward = False
        self.current_reservation_items = []
        self.current_items_page = 0
        self.items_per_page = 6
        self.current_reservation_id = None
        self.current_reservation_details = None
        self.needs_list_refresh = False

        if QFontDatabase.addApplicationFont(":/fonts/Montserrat-Regular.ttf") == -1:
            print("Warning: Could not load Montserrat-Regular.ttf")
        if QFontDatabase.addApplicationFont(":/fonts/Montserrat-Bold.ttf") == -1:
            print("Warning: Could not load Montserrat-Bold.ttf")
        if QFontDatabase.addApplicationFont(":/fonts/Montserrat-SemiBold.ttf") == -1:
            print("Warning: Could not load Montserrat-SemiBold.ttf")

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.setObjectName("ReservationsDialog")
        self.init_ui()
        self.load_reservations()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(226, 232, 240, 100))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 15, 15)

    @Property(QPoint)
    def current_view_pos(self):
        return self._current_view_pos

    @current_view_pos.setter
    def current_view_pos(self, pos):
        self._current_view_pos = pos
        current_widget = self.stacked_widget.currentWidget()
        
        if self.is_moving_forward:
            target_widget = self.stacked_widget.widget(self.stacked_widget.currentIndex() + 1)
            if current_widget:
                current_widget.move(pos - QPoint(self.width(), 0))
            if target_widget:
                target_widget.move(pos)
        else: # Moving backward
            target_widget = self.stacked_widget.widget(self.stacked_widget.currentIndex() - 1)
            if current_widget:
                current_widget.move(pos + QPoint(self.width(), 0))
            if target_widget:
                target_widget.move(pos)

    def init_ui(self):
        self.setWindowTitle("Reservas Existentes")
        self.setMinimumSize(750, 540)
        
        # Nivel 1: Dialogo principal - Fondo más claro

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(25, 20, 25, 20)
        self.main_layout.setSpacing(15)
        
        self.stacked_widget = QStackedWidget()
        self._create_list_view()
        self.stacked_widget.addWidget(self.list_view_widget)
        
        self.slide_out_anim = QPropertyAnimation(self, b"current_view_pos")
        self.slide_out_anim.setDuration(300)
        self.slide_out_anim.setEasingCurve(QEasingCurve.InOutCubic)
        
        self.slide_in_anim = QPropertyAnimation(self, b"current_view_pos")
        self.slide_in_anim.setDuration(300)
        self.slide_in_anim.setEasingCurve(QEasingCurve.InOutCubic)

        self.main_layout.addWidget(self.stacked_widget)
        self.setLayout(self.main_layout)

    def _create_list_view(self):
        self.list_view_widget = QWidget()
        self.list_view_widget.setStyleSheet("background: transparent;")
        list_layout = QVBoxLayout(self.list_view_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(15)
        
        title_bar = QHBoxLayout()
        back_button = QPushButton()
        back_icon = SFSymbols.get_icon("chevron.backward", color="#333")
        back_button.setIcon(back_icon)
        back_button.setIconSize(QSize(22, 22))
        back_button.setCursor(Qt.PointingHandCursor)
        back_button.setFixedSize(30, 30)
        back_button.setStyleSheet("QPushButton { background-color: #E0E0E0; border: none; border-radius: 15px; } QPushButton:hover { background-color: #CACACA; }")
        back_button.clicked.connect(self.close)
        
        title_label = QLabel("Reservas")
        font = QFont(); font.setPointSize(22); font.setWeight(QFont.Weight.Bold)
        title_label.setFont(font)
        title_label.setStyleSheet("color: #111; background-color: transparent; padding-left: 5px;")
        
        title_bar.addWidget(back_button)
        title_bar.addWidget(title_label)
        title_bar.addStretch()
        list_layout.addLayout(title_bar)
        
        # Nivel 2: Contenedor intermedio con fondo distintivo
        list_container = QFrame()
        list_container.setObjectName("listContainer")
        list_container.setStyleSheet("""
            #listContainer { 
                background-color: rgba(247, 250, 252, 0.63); 
                border-radius: 16px; 
                border: 2px solid #CBD5E0;
            }
        """)
        
        container_layout = QVBoxLayout(list_container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(12)
        
        self.list_widget = QListWidget()
        self.list_widget.viewport().setAutoFillBackground(False)
        self.list_widget.setSpacing(12)
        # El QListWidget ahora solo es el fondo para los items, sin bordes propios
        self.list_widget.setStyleSheet("""
            QListWidget { 
                background-color: transparent; 
                border: none;
                outline: none;
            }
            QListWidget::viewport {
                background: transparent;
            }
            QListWidget::item {
                border: none;
                background: transparent;
            }
        """)
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_widget.verticalScrollBar().setStyleSheet("QScrollBar:vertical { border: none; background: transparent; width: 10px; margin: 10px 0 10px 0; } QScrollBar::handle:vertical { background: #CCCCCC; min-height: 20px; border-radius: 5px; } QScrollBar::handle:vertical:hover { background: #AAAAAA; } QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; height: 10px; } QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }")
        
        self.list_widget.itemClicked.connect(self.on_reservation_activated)
        self.list_widget.itemActivated.connect(self.on_reservation_activated)
        self.list_widget.currentItemChanged.connect(self.on_current_item_changed)
        
        container_layout.addWidget(self.list_widget)
        list_layout.addWidget(list_container)

    def on_current_item_changed(self, current, previous):
        if previous:
            prev_widget = self.list_widget.itemWidget(previous)
            if prev_widget:
                prev_widget.setChecked(False)
        if current:
            curr_widget = self.list_widget.itemWidget(current)
            if curr_widget:
                curr_widget.setChecked(True)

    def on_reservation_activated(self, item):
        widget = self.list_widget.itemWidget(item)
        if widget:
            self.show_detail_view(widget.reservation_data)

    def show_detail_view(self, reservation_data):
        reservation_id = reservation_data['id_reserva']
        details = self.reservation_service.get_reservation_details(reservation_id)
        
        if not details:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los detalles para la reserva #{reservation_id}.")
            return

        self.current_reservation_id = reservation_id
        self.current_reservation_details = details
        self.current_reservation_items = details.get('libros', [])
        self.current_items_page = 0

        self.detail_view_widget = self._build_detail_widget(details)
        
        new_widget_index = self.stacked_widget.addWidget(self.detail_view_widget)
        self.slide_to_widget_index(new_widget_index)

    def _build_detail_widget(self, details):
        widget = QWidget()
        widget.setStyleSheet("background: transparent; border: none;")

        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        content_panel = QFrame()
        content_panel.setStyleSheet("background-color: rgba(255, 255, 255, 0.85); border-radius: 15px;")
        
        panel_layout = QVBoxLayout(content_panel)
        panel_layout.setContentsMargins(25, 20, 25, 20)
        panel_layout.setSpacing(10)

        # --- Header Section ---
        header_layout = QVBoxLayout()
        header_layout.setSpacing(15)

        # Title Bar (Back button, Icon, Title)
        title_bar = QHBoxLayout()
        
        back_button = QPushButton()
        back_icon = SFSymbols.get_icon("chevron.backward", color="#333")
        back_button.setIcon(back_icon)
        back_button.setIconSize(QSize(22, 22))
        back_button.setCursor(Qt.PointingHandCursor)
        back_button.setFixedSize(30, 30)
        back_button.setStyleSheet("background-color: #E0E0E0; border-radius: 15px;")
        back_button.clicked.connect(self.show_list_view)
        
        icon_bg = QFrame()
        icon_bg.setFixedSize(40, 40)
        icon_bg.setStyleSheet("background-color: #E0E7FF; border-radius: 20px;")
        icon_bg_layout = QVBoxLayout(icon_bg)
        icon_bg_layout.setContentsMargins(0,0,0,0)
        icon = SFSymbols.get_icon("person.add", color="#4338CA")
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(24, 24))
        icon_label.setAlignment(Qt.AlignCenter)
        icon_bg_layout.addWidget(icon_label)

        title_label = QLabel("Detalles de la Reserva")
        title_label.setFont(QFont("Montserrat", 20, QFont.Bold))
        title_label.setStyleSheet("color: #111; background-color: transparent;")
        
        title_bar.addWidget(back_button)
        title_bar.addSpacing(15)
        title_bar.addWidget(icon_bg)
        title_bar.addSpacing(10)
        title_bar.addWidget(title_label)
        title_bar.addStretch()

        # Customer Info Bar
        customer_info_layout = QHBoxLayout()
        customer_info_layout.setSpacing(20)

        client_name = details.get('cliente_nombre', 'N/A')
        client_phone = details.get('cliente_telefono', 'N/A')
        reservation_id = details.get('id_reserva', 'N/A')
        
        try:
            # First, try to parse with time, then fall back to date only
            try:
                dt_obj = datetime.strptime(details['fecha_reserva'], '%Y-%m-%d %H:%M:%S')
                reservation_date = dt_obj.strftime('%d/%m/%Y a las %H:%M')
            except ValueError:
                dt_obj = datetime.strptime(details['fecha_reserva'], '%Y-%m-%d')
                reservation_date = dt_obj.strftime('%d/%m/%Y')
        except (KeyError, ValueError, TypeError):
            reservation_date = details.get('fecha_reserva', 'N/A')

        customer_info_layout.addWidget(self._create_info_label("Cliente", client_name), 1)
        customer_info_layout.addWidget(self._create_info_label("Teléfono", client_phone), 1)
        customer_info_layout.addWidget(self._create_info_label("Fecha Reserva", reservation_date), 1)
        customer_info_layout.addWidget(self._create_info_label("Nº Reserva", str(reservation_id)), 1)

        header_layout.addLayout(title_bar)
        header_layout.addLayout(customer_info_layout)
        
        panel_layout.addLayout(header_layout)

        # Separator Line
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #CBD5E0; margin-top: 5px; margin-bottom: 5px;")
        panel_layout.addWidget(line)

        # --- Items Section ---
        items_section_layout = QVBoxLayout()
        items_section_layout.setSpacing(10)
        items_section_layout.setContentsMargins(0, 10, 0, 0)

        items_title = QLabel("Artículos en la Reserva")
        items_title.setFont(QFont("Montserrat", 12, QFont.Weight.Bold))
        items_title.setStyleSheet("color: #333; background: transparent;")
        items_section_layout.addWidget(items_title)

        items_columns_layout = QHBoxLayout()
        items_columns_layout.setSpacing(15)
        
        self.left_items_layout = QVBoxLayout()
        self.right_items_layout = QVBoxLayout()
        self.left_items_layout.setSpacing(10)
        self.right_items_layout.setSpacing(10)

        items_columns_layout.addLayout(self.left_items_layout, 1)
        items_columns_layout.addLayout(self.right_items_layout, 1)
        items_section_layout.addLayout(items_columns_layout)

        # Pagination and Action controls
        page_nav_layout = QHBoxLayout()
        page_nav_layout.setContentsMargins(0, 15, 0, 0)
        page_nav_layout.setSpacing(15)

        self.prev_button = QPushButton("◀ Anterior")
        self.prev_button.setCursor(Qt.PointingHandCursor)
        self.prev_button.clicked.connect(self._prev_page)

        self.next_button = QPushButton("Siguiente ▶")
        self.next_button.setCursor(Qt.PointingHandCursor)
        self.next_button.clicked.connect(self._next_page)
        
        for btn in [self.prev_button, self.next_button]:
            btn.setStyleSheet("""
                QPushButton { 
                    background-color: #E2E8F0; border: 1px solid #CBD5E0; 
                    border-radius: 8px; padding: 8px 12px; font-size: 12px;
                }
                QPushButton:hover { background-color: #CBD5E0; }
                QPushButton:disabled { background-color: #F7FAFC; color: #A0AEC0; border-color: #E2E8F0; }
            """)

        # --- Center Action Buttons ---
        self.confirm_button = QPushButton("Confirmar Venta")
        self.confirm_button.setCursor(Qt.PointingHandCursor)
        self.confirm_button.clicked.connect(self._confirm_reservation_action)
        self.confirm_button.setStyleSheet("""
            QPushButton { 
                background-color: #4CAF50; color: white; border: none; 
                border-radius: 8px; padding: 8px 12px; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
        """)

        self.cancel_button = QPushButton("Cancelar Reserva")
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.clicked.connect(self._cancel_reservation_action)
        self.cancel_button.setStyleSheet("""
            QPushButton { 
                background-color: #F44336; color: white; border: none; 
                border-radius: 8px; padding: 8px 12px; font-size: 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #da190b; }
        """)

        center_buttons_layout = QHBoxLayout()
        center_buttons_layout.setSpacing(10)
        center_buttons_layout.addWidget(self.confirm_button)
        center_buttons_layout.addWidget(self.cancel_button)
        center_buttons_layout.setAlignment(Qt.AlignCenter)

        page_nav_layout.addWidget(self.prev_button)
        page_nav_layout.addStretch()
        page_nav_layout.addLayout(center_buttons_layout)
        page_nav_layout.addStretch()
        page_nav_layout.addWidget(self.next_button)
        items_section_layout.addLayout(page_nav_layout)
        
        panel_layout.addLayout(items_section_layout)
        panel_layout.addStretch(1) # Re-add stretch
        main_layout.addWidget(content_panel)

        self._update_reserved_items_display()
        
        return widget

    def _create_info_label(self, title, value):
        widget = QWidget()
        widget.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Montserrat", 10, QFont.Weight.DemiBold))
        title_label.setStyleSheet("color: #6B7280;")

        value_label = QLabel(value)
        value_label.setFont(QFont("Montserrat", 12))
        value_label.setStyleSheet("color: #1F2937;")
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        return widget

    def _create_detail_group_box(self, title, content_widget):
        frame = QFrame()
        frame.setFrameShape(QFrame.NoFrame)
        layout = QVBoxLayout(frame)
        title_label = QLabel(title.upper())
        font = QFont(); font.setPointSize(10); font.setWeight(QFont.Weight.Bold);
        title_label.setFont(font)
        title_label.setStyleSheet("color: #666;")
        layout.addWidget(title_label)
        layout.addWidget(content_widget)
        return frame

    def show_list_view(self):
        self.slide_to_widget_index(0)

    def slide_to_widget_index(self, index):
        if self.stacked_widget.currentIndex() == index or self.slide_in_anim.state() == QPropertyAnimation.Running:
            return

        width = self.stacked_widget.width()
        self.is_moving_forward = index > self.stacked_widget.currentIndex()
        
        target_widget = self.stacked_widget.widget(index)
        if not target_widget:
            return

        target_widget.setGeometry(self.stacked_widget.rect())
        target_widget.show()
        target_widget.raise_()

        if self.is_moving_forward:
            self.slide_in_anim.setStartValue(QPoint(width, 0))
            self.slide_in_anim.setEndValue(QPoint(0, 0))
            target_widget.move(width, 0)
        else: # backwards
            self.slide_in_anim.setStartValue(QPoint(-width, 0))
            self.slide_in_anim.setEndValue(QPoint(0, 0))
            target_widget.move(-width, 0)

        def on_animation_finished():
            self.stacked_widget.setCurrentIndex(index)
            if index == 0 and hasattr(self, 'detail_view_widget') and self.detail_view_widget:
                self.stacked_widget.removeWidget(self.detail_view_widget)
                self.detail_view_widget.deleteLater()
                self.detail_view_widget = None
                if hasattr(self, 'needs_list_refresh') and self.needs_list_refresh:
                    self.load_reservations()
                    self.needs_list_refresh = False

        self.slide_in_anim.finished.connect(on_animation_finished, Qt.SingleShotConnection)
        self.slide_in_anim.start()

    def _clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self._clear_layout(item.layout())

    def _update_reserved_items_display(self):
        self._clear_layout(self.left_items_layout)
        self._clear_layout(self.right_items_layout)

        total_items = len(self.current_reservation_items)
        if total_items == 0:
            self.prev_button.hide()
            self.next_button.hide()
            self.confirm_button.hide()
            self.cancel_button.hide()
            no_items_label = QLabel("No hay artículos en esta reserva.")
            no_items_label.setStyleSheet("color: #6A7280; font-style: italic; background: transparent;")
            no_items_label.setAlignment(Qt.AlignCenter)
            self.left_items_layout.addWidget(no_items_label)
            return

        total_pages = (total_items + self.items_per_page - 1) // self.items_per_page
        is_paginated = total_pages > 1
        
        self.prev_button.setVisible(is_paginated)
        self.next_button.setVisible(is_paginated)

        self.prev_button.setEnabled(self.current_items_page > 0)
        self.next_button.setEnabled(self.current_items_page < total_pages - 1)

        start_index = self.current_items_page * self.items_per_page
        end_index = start_index + self.items_per_page
        
        page_items = self.current_reservation_items[start_index:end_index]

        for i, item_data in enumerate(page_items):
            item_widget = ReservedItemWidget(item_data)
            if i % 2 == 0:
                self.left_items_layout.addWidget(item_widget)
            else:
                self.right_items_layout.addWidget(item_widget)
        
        self.left_items_layout.addStretch(1)
        self.right_items_layout.addStretch(1)

    def _next_page(self):
        total_items = len(self.current_reservation_items)
        total_pages = (total_items + self.items_per_page - 1) // self.items_per_page
        if self.current_items_page < total_pages - 1:
            self.current_items_page += 1
            self._update_reserved_items_display()

    def _prev_page(self):
        if self.current_items_page > 0:
            self.current_items_page -= 1
            self._update_reserved_items_display()

    def _confirm_reservation_action(self):
        if not self.current_reservation_id or not self.current_reservation_details:
            return

        reply = QMessageBox.question(self, "Confirmar Venta",
                                     "<b>¡Alto!</b><br><br>¿Estás seguro de que quieres confirmar que la reserva se ha pagado por completo y convertirla en una venta final?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.No:
            return
            
        total_amount = self.current_reservation_details.get('monto_total', 0)
        paid_amount = self.current_reservation_details.get('monto_abonado', 0)
        due_amount = total_amount - paid_amount

        final_payment, ok = QInputDialog.getDouble(self, "Pago Final", f"Monto restante: {format_price(due_amount)}<br>Ingrese el pago final recibido:", 
                                                   due_amount, 0, 10000000, 2)
        if ok:
            success, message = self.reservation_service.convert_reservation_to_sale(
                self.current_reservation_id, final_payment)
            
            if success:
                QMessageBox.information(self, "Éxito", message)
                self.needs_list_refresh = True
                self.show_list_view()
            else:
                QMessageBox.critical(self, "Error", f"No se pudo completar la operación:\n{message}")

    def _cancel_reservation_action(self):
        if not self.current_reservation_id:
            return

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Cancelar Reserva")
        msg_box.setText("<b>¿Estás seguro de que quieres cancelar esta reserva?</b>")
        msg_box.setInformativeText("Cancelar la reserva devolverá los libros al inventario. "
                                   "El dinero abonado por el cliente puede registrarse como un egreso (si se devuelve) "
                                   "o ignorarse. Esta acción no se puede deshacer.")
        msg_box.setIcon(QMessageBox.Warning)
        refund_button = msg_box.addButton("Sí, con devolución", QMessageBox.YesRole)
        no_refund_button = msg_box.addButton("Sí, sin devolución", QMessageBox.NoRole)
        msg_box.addButton("No cancelar", QMessageBox.RejectRole)
        
        msg_box.exec()
        
        clicked_button = msg_box.clickedButton()
        if clicked_button == refund_button:
            with_refund = True
        elif clicked_button == no_refund_button:
            with_refund = False
        else:
            return

        success, message = self.reservation_service.cancel_reservation(self.current_reservation_id, with_refund)
        if success:
            QMessageBox.information(self, "Éxito", message)
            self.needs_list_refresh = True
            self.show_list_view()
        else:
            QMessageBox.critical(self, "Error", f"No se pudo completar la operación:\n{message}")

    def load_reservations(self):
        reservations = self.reservation_service.get_all_reservations()
        if reservations is None:
            QMessageBox.critical(self, "Error de base de datos", "No se pudieron cargar las reservas.")
            return

        self.list_widget.clear()
        for i, reservation in enumerate(reservations):
            item = QListWidgetItem(self.list_widget)
            widget = ReservationItemWidget(reservation)

            item.setSizeHint(widget.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
            self.list_widget.setFocus()

    def closeEvent(self, event):
        self.accept()