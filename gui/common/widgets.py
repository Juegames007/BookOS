"""
Módulo de widgets reutilizables para la interfaz gráfica.

Este módulo contiene definiciones de widgets personalizados que se usan en 
múltiples partes de la aplicación. Cada widget está diseñado para mantener 
una apariencia y comportamiento consistentes en toda la aplicación.

Clases:
- CustomButton: Botón personalizado con estilos y efectos visuales.
"""

import os
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PySide6.QtGui import QPixmap, QFont, QCursor
from PySide6.QtCore import Signal, Qt, QSize

class CustomButton(QFrame):
    """
    Botón personalizado con estilo coherente para toda la aplicación.
    
    Esta clase implementa un botón con apariencia personalizada, que incluye:
    - Fondo semitransparente
    - Icono opcional
    - Texto
    - Flecha ">" a la derecha
    - Efectos visuales al pasar el mouse o hacer clic
    
    Señales:
    - clicked: Se emite cuando se hace clic en el botón
    """
    clicked = Signal()

    def __init__(self, icon_path=None, text="", parent=None):
        """
        Inicializa un nuevo botón personalizado.
        
        Args:
            icon_path (str, opcional): Ruta al archivo de icono.
            text (str, opcional): Texto a mostrar en el botón.
            parent (QWidget, opcional): Widget padre.
        """
        super().__init__(parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
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
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(8)

        self.icon_label = QLabel()
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            self.icon_label.setPixmap(pixmap.scaled(self.icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            if icon_path:
                 print(f"Advertencia: No se pudo cargar el icono para CustomButton: {icon_path}")
            self.icon_label.setFixedSize(0,0)
            layout.setSpacing(0)

        self.text_label = QLabel(text)
        font_botones = QFont(self.font_family, 11)
        self.text_label.setFont(font_botones)

        self.arrow_label = QLabel(">")
        self.arrow_label.setFont(font_botones)
        self.arrow_label.setFixedWidth(self.arrow_label.fontMetrics().horizontalAdvance("> ") + 5)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        layout.addStretch(1)
        layout.addWidget(self.arrow_label)

    def enterEvent(self, event):
        """Se activa cuando el cursor entra en el botón."""
        self.setStyleSheet(self.style_hover)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Se activa cuando el cursor sale del botón."""
        self.setStyleSheet(self.style_normal)
        super().leaveEvent(event)
        
    def mousePressEvent(self, event):
        """Se activa cuando se presiona el botón del mouse."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.setStyleSheet(self.style_pressed)
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        """Se activa cuando se suelta el botón del mouse."""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.rect().contains(event.position().toPoint()):
                self.setStyleSheet(self.style_hover)
                self.clicked.emit()
            else:
                self.setStyleSheet(self.style_normal)
        super().mouseReleaseEvent(event) 