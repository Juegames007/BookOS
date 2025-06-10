from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPainter, QColor

class ReservationOptionsDialog(QDialog):
    """
    Diálogo para elegir entre crear una nueva reserva o ver las existentes.
    """
    new_reservation_requested = Signal()
    view_reservations_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Opciones de Reserva")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 220)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        container_frame = QFrame(self)
        container_frame.setObjectName("containerFrame")
        container_frame.setStyleSheet("""
            QFrame#containerFrame {
                background-color: rgba(255, 255, 255, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.4);
                border-radius: 16px;
            }
        """)
        
        frame_layout = QVBoxLayout(container_frame)
        frame_layout.setContentsMargins(25, 20, 25, 25)
        frame_layout.setSpacing(20)

        title_label = QLabel("¿Qué quieres hacer?")
        title_font = QFont("Montserrat", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #000; background: transparent;")

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        button_style = """
            QPushButton { 
                background-color: #4A90E2; 
                color: #FFFFFF; 
                border: none; 
                border-radius: 12px; 
                font-size: 14px; 
                font-weight: bold;
                padding: 12px 20px;
            }
            QPushButton:hover { background-color: #357ABD; }
            QPushButton:pressed { background-color: #2E6DA4; }
        """

        self.add_button = QPushButton("Crear Nueva Reserva")
        self.add_button.setStyleSheet(button_style)
        self.add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_button.clicked.connect(self.create_new_triggered)

        self.view_button = QPushButton("Ver Reservas Existentes")
        self.view_button.setStyleSheet(button_style.replace("#4A90E2", "#555555").replace("#357ABD", "#444444").replace("#2E6DA4", "#333333"))
        self.view_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.view_button.clicked.connect(self.view_existing_triggered)

        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.view_button)

        frame_layout.addWidget(title_label)
        frame_layout.addLayout(buttons_layout)
        
        main_layout.addWidget(container_frame)

    def create_new_triggered(self):
        self.new_reservation_requested.emit()
        self.accept()

    def view_existing_triggered(self):
        self.view_reservations_requested.emit()
        self.accept() 