# Dentro de widgets.py

import os
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy
from PySide6.QtGui import QPixmap, QFont, QCursor
from PySide6.QtCore import Signal, Qt, QSize

class CustomButton(QFrame):
    clicked = Signal()

    def __init__(self, icon_path=None, text="", parent=None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed) # Para la altura ya tienes setFixedHeight
        # Mantendré la altura en 50px como estaba en tu archivo,
        # pero si quieres reducirla, este es el lugar (ej. self.setFixedHeight(40))
        self.setFixedHeight(50) 
        self.font_family = "San Francisco"
        self.text_color = "#202427"
        self.icon_size = QSize(24, 24)

        self.style_normal = f"""
            QFrame {{
                background-color: rgba(248, 249, 250, 100);
                border: 1px solid rgba(200, 200, 200, 80);
                border-radius: 10px;
            }}
            QLabel {{
                color: {self.text_color};
                background-color: transparent;
                border: none;
                padding: 0px;
            }}
        """
        self.style_hover = f"""
            QFrame {{
                background-color: rgba(240, 245, 248, 120);
                border: 1px solid rgba(190, 190, 190, 100);
                border-radius: 10px;
            }}
            QLabel {{ color: {self.text_color}; background-color: transparent; border:none; padding: 0px; }}
        """
        self.style_pressed = f"""
            QFrame {{
                background-color: rgba(230, 238, 245, 140);
                border: 1px solid rgba(180, 180, 180, 120);
                border-radius: 10px;
            }}
            QLabel {{ color: {self.text_color}; background-color: transparent; border:none; padding: 0px; }}
        """
        self.setStyleSheet(self.style_normal)

        layout = QHBoxLayout(self)
        # Márgenes del QHBoxLayout DENTRO del CustomButton.
        # Si los botones se sienten muy "apretados" o muy "sueltos" lateralmente 
        # DESPUÉS de aplicar el recorte en MainMenuCard, puedes ajustar estos márgenes.
        # Por ejemplo, para botones más estrechos: layout.setContentsMargins(5, 0, 5, 0)
        layout.setContentsMargins(10, 0, 10, 0) # Mantengo los 10px por ahora
        layout.setSpacing(8) # Espacio entre icono y texto (si ambos existen)

        # --- INICIO DE SECCIÓN CORREGIDA Y PARA CENTRAR ---
        layout.addStretch(1) # 1. Stretch a la izquierda para empujar el contenido al centro

        self.icon_label = QLabel()
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            self.icon_label.setPixmap(pixmap.scaled(self.icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            if icon_path:
                 print(f"Advertencia: No se pudo cargar el icono para CustomButton: {icon_path}")
            # Si no hay icono, no ocupa espacio visual, pero el widget QLabel existe.
            # Aseguramos que no tenga un tamaño mínimo que interfiera.
            self.icon_label.setFixedSize(0,0) 
            # Si no hay icono, y SÍ hay texto, puede que no quieras el espaciado del layout
            # layout.setSpacing(0) # Descomenta si el texto queda muy separado sin icono

        self.text_label = QLabel(text)
        # El tamaño de fuente que habías establecido (12)
        font_botones = QFont(self.font_family, 12) 
        self.text_label.setFont(font_botones)

        layout.addWidget(self.icon_label) # 2. Añadir etiqueta del icono
        layout.addWidget(self.text_label) # 3. Añadir etiqueta del texto

        # Lógica para el arrow_label (si es necesario)
        # Si no hay icono, se muestra la flecha (actualmente vacía).
        # Si quieres que la flecha desaparezca completamente y no afecte el centrado,
        # podrías poner toda esta sección del arrow_label dentro de un 'if False:' o eliminarla.
        if not icon_path:
            self.arrow_label = QLabel("") # Flecha vacía, no será visible
            self.arrow_label.setFont(font_botones)
            self.arrow_label.setFixedWidth(0) # No ocupa espacio si está vacía
            layout.addWidget(self.arrow_label) # 4. Añadir (potencialmente) la flecha
        else:
            self.arrow_label = None

        layout.addStretch(1) # 5. Stretch a la derecha para completar el centrado
        # --- FIN DE SECCIÓN CORREGIDA Y PARA CENTRAR ---

    def enterEvent(self, event):
        self.setStyleSheet(self.style_hover)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.setStyleSheet(self.style_normal)
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.setStyleSheet(self.style_pressed)
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.rect().contains(event.position().toPoint()):
                self.setStyleSheet(self.style_hover)
                self.clicked.emit()
            else:
                self.setStyleSheet(self.style_normal)
        super().mouseReleaseEvent(event)