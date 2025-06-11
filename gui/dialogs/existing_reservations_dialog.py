from PySide6.QtWidgets import (QDialog, QVBoxLayout, QListWidget, QListWidgetItem, 
                             QWidget, QHBoxLayout, QLabel, QPushButton, QFrame,
                             QSizePolicy)
from PySide6.QtGui import QFont, QPainter, QColor, QBrush, QPen, QFontMetrics
from PySide6.QtCore import Qt, QSize
from features.reservation_service import ReservationService
from gui.resources.sfsymbols import SFSymbols

class ElidedLabel(QLabel):
    """
    Un QLabel que trunca (elide) su texto con '...' si es demasiado largo
    para caber en el ancho disponible.
    """
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setMinimumWidth(1)

    def paintEvent(self, event):
        painter = QPainter(self)
        metrics = self.fontMetrics()
        elided_text = metrics.elidedText(self.text(), Qt.ElideRight, self.width())
        painter.drawText(self.rect(), self.alignment() | Qt.AlignVCenter, elided_text)

class ReservationItemWidget(QPushButton):
    """
    Un widget de botón personalizado para mostrar un único elemento de reserva.
    Es un botón para que toda el área sea clickeable.
    """
    def __init__(self, reservation_data, parent=None):
        super().__init__(parent)
        self.reservation_data = reservation_data
        self.setCursor(Qt.PointingHandCursor)
        self.init_ui()

    def create_info_block(self, top_text, bottom_text, bottom_font_size_px=14, is_bold=False, use_elided_label=False):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        top_label = QLabel(top_text.upper())
        top_label.setStyleSheet("font-size: 10px; color: #888; font-weight: bold;")
        
        if use_elided_label:
            bottom_label = ElidedLabel(bottom_text)
        else:
            bottom_label = QLabel(bottom_text)

        style = f"font-size: {bottom_font_size_px}px; color: #333;"
        if is_bold:
            style += " font-weight: bold;"
        bottom_label.setStyleSheet(style)
        
        layout.addWidget(top_label)
        layout.addWidget(bottom_label)
        
        return widget

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Icono
        icon_label = QLabel(self)
        icon = SFSymbols.get_icon("person.add", color="white") 
        icon_label.setPixmap(icon.pixmap(QSize(28, 28)))
        icon_label.setFixedSize(42, 42)
        icon_label.setStyleSheet("background-color: #333; border-radius: 21px;")
        icon_label.setAlignment(Qt.AlignCenter)

        # Nombre del cliente (ahora como un bloque de info)
        client_name_block = self.create_info_block(
            "Cliente",
            self.reservation_data['cliente_nombre'],
            bottom_font_size_px=16,
            is_bold=True,
            use_elided_label=True
        )

        # Bloque de información derecha (ID, Teléfono y Fechas)
        info_widget = QWidget()
        info_layout = QHBoxLayout(info_widget)
        info_layout.setContentsMargins(0,0,0,0)
        info_layout.setSpacing(20)

        # ID de la reserva
        res_id_block = self.create_info_block(
            "Reserva", 
            f"#{self.reservation_data['id_reserva']}"
        )

        # Teléfono del cliente
        phone_block = self.create_info_block(
            "Teléfono",
            self.reservation_data.get('cliente_telefono', 'N/A')
        )

        # Fecha de reserva
        try:
            fecha_reserva = self.reservation_data['fecha_reserva'].split(' ')[0]
            dates_text = f"{fecha_reserva}"
        except (KeyError, IndexError):
            dates_text = "N/A"
            
        dates_block = self.create_info_block(
            "F. Reserva", 
            dates_text
        )
        
        info_layout.addWidget(res_id_block)
        info_layout.addWidget(phone_block)
        info_layout.addWidget(dates_block)
        
        info_widget.setMinimumWidth(320) # Evita que el layout se comprima demasiado

        main_layout.addWidget(icon_label)
        main_layout.addWidget(client_name_block, 4) # Factor de estiramiento 2: Dar más espacio al nombre
        main_layout.addStretch(1) # Factor de estiramiento 1: Menos al espacio en blanco
        main_layout.addWidget(info_widget)
        
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 150);
                border: 1px solid #E0E0E0;
                border-radius: 12px;
                text-align: left;
            }
            QPushButton:hover {
                border-color: #007AFF;
            }
        """)

    def sizeHint(self):
        # Forzamos una altura fija para que QListWidget sepa cuánto espacio reservar.
        # Esto soluciona el problema de los widgets superpuestos.
        return QSize(super().sizeHint().width(), 85)

class ExistingReservationsDialog(QDialog):
    """
    Diálogo para mostrar una lista de todas las reservas existentes.
    """
    def __init__(self, reservation_service: ReservationService, parent=None):
        super().__init__(parent)
        self.reservation_service = reservation_service
        
        # --- Configuración de la ventana sin marco ---
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.init_ui()
        self.load_reservations()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fondo semi-transparente
        painter.setBrush(QColor(240, 242, 245, 150))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 15, 15)

    def init_ui(self):
        self.setWindowTitle("Reservas Existentes")
        self.setMinimumSize(750, 460)

        # Layout principal que envuelve todo
        self.root_layout = QVBoxLayout(self)
        self.root_layout.setContentsMargins(1, 1, 1, 1)

        # Contenedor del contenido principal con bordes redondeados
        container = QFrame(self)
        container.setObjectName("container")
        container.setStyleSheet("background: transparent; border: none;")
        self.root_layout.addWidget(container)

        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(15)

        # --- Barra de título personalizada ---
        title_bar = QHBoxLayout()
        
        # Botón de retroceso
        back_button = QPushButton()
        back_icon = SFSymbols.get_icon("chevron.backward", color="#333")
        back_button.setIcon(back_icon)
        back_button.setIconSize(QSize(22, 22))
        back_button.setCursor(Qt.PointingHandCursor)
        back_button.setFixedSize(30, 30)
        back_button.setStyleSheet("""
            QPushButton { 
                background-color: #E0E0E0; 
                border: none; 
                border-radius: 15px; 
            }
            QPushButton:hover { background-color: #CACACA; }
        """)
        back_button.clicked.connect(self.close)

        # Título
        title_label = QLabel("Reservas")
        font = QFont()
        font.setPointSize(22)
        font.setWeight(QFont.Weight.Bold)
        title_label.setFont(font)
        title_label.setStyleSheet("color: #111; background-color: transparent; padding-left: 5px;")
        
        title_bar.addWidget(back_button)
        title_bar.addWidget(title_label)
        title_bar.addStretch()

        # Lista de reservas
        self.list_widget = QListWidget()
        self.list_widget.setSpacing(15)
        self.list_widget.setStyleSheet("""
            QListWidget { border: none; background-color: transparent; }
            QListWidget::item { border: none; }
            QListWidget::item:selected { background-color: transparent; border: none; }
        """)
        self.list_widget.setFocusPolicy(Qt.NoFocus)
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # --- Estilo de la barra de desplazamiento ---
        self.list_widget.verticalScrollBar().setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 10px;
                margin: 10px 0 10px 0;
            }
            QScrollBar::handle:vertical {
                background: #CCCCCC;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #AAAAAA;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 10px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        
        main_layout.addLayout(title_bar)
        main_layout.addSpacing(15)
        main_layout.addWidget(self.list_widget)
        self.setLayout(self.root_layout)

    def load_reservations(self):
        self.list_widget.clear()
        try:
            reservations = self.reservation_service.get_all_reservations()
            if not reservations:
                no_res_label = QLabel("No hay reservas existentes.")
                no_res_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                font = QFont()
                font.setPointSize(14)
                no_res_label.setFont(font)
                no_res_label.setStyleSheet("color: #666; background-color: transparent;")
                
                list_item = QListWidgetItem(self.list_widget)
                list_item.setSizeHint(QSize(self.list_widget.width(), 100))
                self.list_widget.addItem(list_item)
                self.list_widget.setItemWidget(list_item, no_res_label)
                return

            for reservation in reservations:
                item_widget = ReservationItemWidget(reservation)
                list_item = QListWidgetItem(self.list_widget)
                list_item.setSizeHint(item_widget.sizeHint())
                self.list_widget.addItem(list_item)
                self.list_widget.setItemWidget(list_item, item_widget)
        except Exception as e:
            print(f"Error al cargar las reservas: {e}")
            error_label = QLabel(f"Error al cargar las reservas: {e}")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            list_item = QListWidgetItem(self.list_widget)
            list_item.setSizeHint(error_label.sizeHint())
            self.list_widget.addItem(list_item)
            self.list_widget.setItemWidget(list_item, error_label) 