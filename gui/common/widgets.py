import os
from PySide6.QtWidgets import (QFrame, QLabel, QSizePolicy, QHBoxLayout, 
                               QWidget, QStackedLayout)
from PySide6.QtGui import QPixmap, QFont, QCursor
from PySide6.QtCore import Signal, Qt, QSize

class CustomButton(QFrame):
    clicked = Signal()

    def __init__(self, icon_path=None, text="", parent=None):
        super().__init__(parent)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(50)
        self.font_family = "San Francisco"
        self.text_color = "#202427"
        self.icon_size = QSize(24, 24)

        # Estilos (igual que la corrección anterior para AttributeError)
        self.style_normal = f"""
            QFrame {{
                background-color: rgba(248, 249, 250, 100);
                border: 1px solid rgba(200, 200, 200, 80);
                border-radius: 10px;
            }}
            /* El estilo de QLabel se aplicará directamente a los QLabel para mayor control */
        """
        self.style_hover = f"""
            QFrame {{
                background-color: rgba(240, 245, 248, 120);
                border: 1px solid rgba(190, 190, 190, 100);
                border-radius: 10px;
            }}
        """
        self.style_pressed = f"""
            QFrame {{
                background-color: rgba(230, 238, 245, 140);
                border: 1px solid rgba(180, 180, 180, 120);
                border-radius: 10px;
            }}
        """
        self.setStyleSheet(self.style_normal)

        # Usar QStackedLayout como layout principal del QFrame
        stacked_layout = QStackedLayout(self)
        # Los márgenes deben estar en el QFrame (por estilo) o en las capas internas, no en el QStackedLayout directamente
        # si queremos que las capas se superpongan completamente.
        stacked_layout.setContentsMargins(0,0,0,0)
        stacked_layout.setStackingMode(QStackedLayout.StackingMode.StackAll) # Todos los widgets son visibles si son transparentes


        # --- Capa 0: Contenedor del Texto Centrado (siempre visible en el fondo) ---
        text_widget_layer = QWidget()
        text_widget_layer.setStyleSheet("background:transparent;") # Asegurar transparencia
        text_layout = QHBoxLayout(text_widget_layer)
        # Estos márgenes definen el área donde el texto se centrará
        text_layout.setContentsMargins(10, 0, 10, 0) # Padding para el texto dentro del botón
        text_layout.setSpacing(0)

        self.text_label = QLabel(text)
        font_botones = QFont(self.font_family, 12)
        self.text_label.setFont(font_botones)
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        # Estilo para el texto, asegurando que sea visible
        self.text_label.setStyleSheet(f"color: {self.text_color}; background:transparent; padding:0px; border:none;")


        text_layout.addStretch(1)
        text_layout.addWidget(self.text_label)
        text_layout.addStretch(1)
        
        stacked_layout.addWidget(text_widget_layer)

        # --- Capa 1: Contenedor del Icono (si existe, encima del texto) ---
        self.icon_label = None # Inicializar
        if icon_path and os.path.exists(icon_path):
            icon_widget_layer = QWidget()
            icon_widget_layer.setStyleSheet("background:transparent;") # La capa del icono también debe ser transparente
            icon_widget_layer.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False) # Que los eventos pasen si esta capa no los maneja

            icon_layout = QHBoxLayout(icon_widget_layer)
            # El icono se alineará a la izquierda, con el mismo margen izquierdo que el texto para consistencia
            icon_layout.setContentsMargins(10, 0, 0, 0) # 10px a la izquierda, 0 en los otros
            icon_layout.setSpacing(0)

            self.icon_label = QLabel()
            self.icon_label.setStyleSheet("background:transparent; border:none; padding:0px;")
            pixmap = QPixmap(icon_path)
            self.icon_label.setPixmap(pixmap.scaled(self.icon_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            self.icon_label.setFixedSize(self.icon_size)
            
            icon_layout.addWidget(self.icon_label, 0, Qt.AlignLeft | Qt.AlignVCenter)
            icon_layout.addStretch(1) # El stretch asegura que el QHBoxLayout llene la capa

            stacked_layout.addWidget(icon_widget_layer)
            # No es necesario setCurrentWidget si usamos StackAll y los widgets superiores son transparentes
            # donde no tienen contenido.
        
        # Si no hay icono, solo la capa de texto está en el stack, y es la única visible.


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