from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from gui.common.styles import FONTS, COLORS

class SellBookDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vender Libro")

        # Configuración para una ventana sin bordes y con fondo transparente
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Contenedor principal para aplicar el fondo y borde redondeado
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
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.main_frame)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Layout interno para el contenido
        content_layout = QVBoxLayout(self.main_frame)
        content_layout.setContentsMargins(25, 0, 25, 25)
        content_layout.setSpacing(15)

        # Título
        title_label = QLabel("Vender Artículos")
        title_font = QFont(FONTS["family_title"], FONTS["size_large_title"], QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {COLORS['text_primary']}; background-color: transparent; margin-top: 22px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        
        content_layout.addWidget(title_label)

        # Placeholder para el resto del contenido
        # Se puede añadir más widgets a content_layout aquí

        self.resize(800, 600) 