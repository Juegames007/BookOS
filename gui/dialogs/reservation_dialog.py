import os
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QGraphicsBlurEffect, QLineEdit, QScrollArea, QSpacerItem,
    QSizePolicy, QApplication
)
from PySide6.QtGui import QFont, QMouseEvent, QPixmap, QPainter, QColor, QIcon
from PySide6.QtCore import Qt, QPoint, Signal

# Asumiendo que los estilos y dependencias están accesibles
from gui.common.styles import FONTS, COLORS

class BookItemWidget(QFrame):
    """Widget individual para cada libro en la reserva"""
    remove_requested = Signal(object)
    
    def __init__(self, isbn="", title="", parent=None):
        super().__init__(parent)
        self.isbn = isbn
        self.title = title
        self.setup_ui()
    
    def setup_ui(self):
        self.setFixedHeight(45)  # Altura reducida de 50 a 40
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 8px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 8, 0)  # Márgenes más pequeños
        layout.setSpacing(8)  # Menos espacio entre elementos
        
        book_info_text = f"{self.title if self.title else 'Libro sin título'} - ISBN: {self.isbn}"
        
        self.info_label = QLabel(book_info_text)
        self.info_label.setFont(QFont("Arial", 10))
        self.info_label.setStyleSheet("color: #333; border: none; background: transparent;")
        self.info_label.setWordWrap(False)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.remove_button = QPushButton()
        self.remove_button.setFixedSize(20, 20)
        
        try:
            # Asegúrate que esta ruta es correcta desde donde ejecutas el programa
            icon_path = "gui/dialogs/icono_eliminar.png" 
            icon_pixmap = QPixmap(icon_path)
            if not icon_pixmap.isNull():
                scaled_pixmap = icon_pixmap.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.remove_button.setIcon(QIcon(scaled_pixmap))
            else:
                self.remove_button.setText("×")
        except Exception:
            self.remove_button.setText("×")
            
        self.remove_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4444; color: white; border: none;
                border-radius: 15px; font-size: 16px; font-weight: bold;
            }
            QPushButton:hover { background-color: #cc3333; }
        """)
        self.remove_button.clicked.connect(lambda: self.remove_requested.emit(self))
        
        layout.addWidget(self.info_label)
        layout.addStretch()
        layout.addWidget(self.remove_button)

class ReservationDialog(QDialog):
    """
    Diálogo moderno para gestionar la reserva y visualización de libros apartados.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reservas")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # CAMBIO CLAVE: Tamaño fijo para evitar que se mueva todo
        self.setFixedSize(500, 600)  # Aumentada altura para acomodar paginación

        self.font_family = FONTS.get("family", "Arial")
        self._drag_pos = QPoint()
        self.top_bar_height = 50
        self.reserved_books = []
        self.current_page = 0
        self.books_per_page = 3

        self._blur_effect = None
        if self.parent():
            self._blur_effect = QGraphicsBlurEffect()
            self._blur_effect.setBlurRadius(15)
            self._blur_effect.setEnabled(False)
            target_widget = self.parent().centralWidget() if hasattr(self.parent(), 'centralWidget') else self.parent()
            if target_widget:
                target_widget.setGraphicsEffect(self._blur_effect)

        self._setup_ui()
        self.setModal(True)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(0)
        
        container_frame = QFrame()
        container_frame.setObjectName("containerFrame")
        container_frame.setStyleSheet(f"""
            QFrame#containerFrame {{
                background-color: rgba(255, 255, 255, 0.25);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 16px;
            }}
        """)
        main_layout.addWidget(container_frame)

        container_layout = QVBoxLayout(container_frame)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # TOP BAR - FIJO
        top_bar = QFrame()
        top_bar.setFixedHeight(self.top_bar_height)
        top_bar.setStyleSheet("background-color: transparent;")
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(30, 10, 25, 0)
        title_label = QLabel("Reserve Book")
        title_font = QFont(self.font_family, 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white; background: transparent; border: none; margin-top: 5px;")
        self.view_reservations_button = QPushButton("View Reservations")
        self.view_reservations_button.setFixedHeight(36)
        self.view_reservations_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2); border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 18px; padding: 0 20px; color: white;
                font-size: 12px; font-weight: 500; margin-top: 8px; margin-right: 15px;
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.3); }
        """)
        self.view_reservations_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(32, 32)
        self.close_button.setFont(QFont(self.font_family, 16, QFont.Weight.Bold))
        self.close_button.setStyleSheet("""
            QPushButton { background-color: transparent; border: none; border-radius: 16px; color: white; }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.2); }
        """)
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button.clicked.connect(self.reject)
        top_bar_layout.addWidget(title_label)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.view_reservations_button)
        top_bar_layout.addWidget(self.close_button)
        container_layout.addWidget(top_bar)

        # CONTENT WIDGET CON LAYOUT MEJORADO
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 15, 30, 25)  # Reducidos márgenes
        content_layout.setSpacing(8)  # REDUCIDO: Menos espacio entre secciones principales

        # Estilo MUY agresivo para eliminar todo el espaciado de las etiquetas
        label_style = """
            QLabel { 
                color: rgba(255, 255, 255, 0.9); 
                background-color: transparent; 
                font-size: 11px; 
                font-weight: 500; 
                margin: 0px; 
                padding: 0px;
                border: 0px;
                min-height: 0px;
                max-height: 15px;
            }
        """
        
        input_style = """
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.9); border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px; padding: 0 15px; font-size: 14px; color: #333;
                margin: 0px;
            }
            QLineEdit:focus {
                border: 2px solid rgba(74, 144, 226, 0.8); background-color: rgba(255, 255, 255, 0.95);
            }
        """
        
        # SECCIÓN DE INPUTS CLIENTE - ULTRA OPTIMIZADA
        client_info_layout = QHBoxLayout()
        client_info_layout.setSpacing(15)
        client_info_layout.setContentsMargins(0, 0, 0, 0)
        
        # Layout nombre - SIN ESPACIO
        name_layout = QVBoxLayout()
        name_layout.setSpacing(0)  # CERO espaciado
        name_layout.setContentsMargins(0, 0, 0, 0)
        client_name_label = QLabel("Nombre cliente")
        client_name_label.setStyleSheet(label_style)
        client_name_label.setFixedHeight(15)  # Altura fija muy pequeña
        self.client_name_input = QLineEdit()
        self.client_name_input.setPlaceholderText("Nombre completo")
        self.client_name_input.setFixedHeight(45)
        self.client_name_input.setStyleSheet(input_style)
        name_layout.addWidget(client_name_label)
        name_layout.addWidget(self.client_name_input)
        
        # Layout teléfono - SIN ESPACIO
        phone_layout = QVBoxLayout()
        phone_layout.setSpacing(0)  # CERO espaciado
        phone_layout.setContentsMargins(0, 0, 0, 0)
        client_phone_label = QLabel("Teléfono cliente")
        client_phone_label.setStyleSheet(label_style)
        client_phone_label.setFixedHeight(15)  # Altura fija muy pequeña
        self.client_phone_input = QLineEdit()
        self.client_phone_input.setPlaceholderText("Número de contacto")
        self.client_phone_input.setFixedHeight(45)
        self.client_phone_input.setStyleSheet(input_style)
        phone_layout.addWidget(client_phone_label)
        phone_layout.addWidget(self.client_phone_input)
        
        client_info_layout.addLayout(name_layout)
        client_info_layout.addLayout(phone_layout)
        content_layout.addLayout(client_info_layout)
        
        # SEPARADOR VISUAL entre secciones de cliente e ISBN
        content_layout.addSpacing(2)  # Espaciado específico para separar secciones
        
        # SECCIÓN ISBN - ULTRA OPTIMIZADA
        isbn_layout = QVBoxLayout()
        isbn_layout.setSpacing(0)  # CERO espaciado
        isbn_layout.setContentsMargins(0, 0, 0, 0)
        isbn_label = QLabel("ISBN libro a reservar")
        isbn_label.setStyleSheet(label_style)
        isbn_label.setFixedHeight(15)  # Altura fija muy pequeña
        self.isbn_input = QLineEdit()
        self.isbn_input.setPlaceholderText("Ingresa el ISBN y presiona Enter")
        self.isbn_input.setFixedHeight(45)
        self.isbn_input.setStyleSheet(input_style)
        self.isbn_input.returnPressed.connect(self.add_book_by_isbn)
        isbn_layout.addWidget(isbn_label)
        isbn_layout.addWidget(self.isbn_input)
        content_layout.addLayout(isbn_layout)

        # SECCIÓN DE LIBROS - REESTRUCTURADA
        self.books_section = QWidget()
        # CAMBIO CLAVE: Aumentar altura total para incluir paginación completamente
        self.books_section.setFixedHeight(270)  # Aumentada de 250 a 270
        
        self.books_section_layout = QVBoxLayout(self.books_section)
        self.books_section_layout.setContentsMargins(0, 5, 0, 0)  # Menos margen superior
        self.books_section_layout.setSpacing(6)  # Menos espacio entre elementos
        
        self.books_label = QLabel("Reserved Books:")
        self.books_label.setFont(QFont(self.font_family, 14, QFont.Weight.Bold))
        self.books_label.setStyleSheet("color: white; background: transparent;")
        self.books_section_layout.addWidget(self.books_label)

        # Contenedor para los libros - ALTURA AJUSTADA para dar más espacio a paginación
        self.books_display = QFrame()
        self.books_display.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
            }
        """)
        # CAMBIO CLAVE: Altura optimizada para dejar espacio completo a paginación
        self.books_display.setFixedHeight(170)  # Aumentada de 160 a 170
        
        self.visible_books_layout = QVBoxLayout(self.books_display)
        self.visible_books_layout.setContentsMargins(8, 8, 8, 8)
        self.visible_books_layout.setSpacing(6)
        
        # Mensaje cuando no hay libros
        self.no_books_label = QLabel("No books reserved yet.")
        self.no_books_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); background: transparent; font-style: italic;")
        self.no_books_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.visible_books_layout.addWidget(self.no_books_label)
        
        self.books_section_layout.addWidget(self.books_display)
        
        # CAMBIO CLAVE: Navegación de páginas FUERA del contenedor de libros
        self.page_nav = QFrame()
        self.page_nav.setVisible(False)  # Inicialmente oculto
        self.page_nav.setFixedHeight(40)  # Altura aumentada para que no se recorte
        self.page_nav.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                margin-top: 3px;
            }
        """)
        
        self.page_nav_layout = QHBoxLayout(self.page_nav)
        self.page_nav_layout.setContentsMargins(15, 7, 15, 7)  # Márgenes balanceados
        self.page_nav_layout.setSpacing(12)
        
        btn_style = """
            QPushButton { 
                background-color: rgba(255, 255, 255, 0.2); 
                border: 1px solid rgba(255, 255, 255, 0.3); 
                border-radius: 12px; color: white; font-size: 12px; 
                font-weight: 500;
            } 
            QPushButton:hover { 
                background-color: rgba(255, 255, 255, 0.3); 
            } 
            QPushButton:disabled { 
                background-color: rgba(255, 255, 255, 0.05); 
                color: rgba(255, 255, 255, 0.3); 
            }
        """
        
        self.prev_button = QPushButton("◀ Previous")
        self.prev_button.setFixedSize(85, 28)  # Botones ligeramente más grandes
        self.prev_button.setStyleSheet(btn_style)
        self.prev_button.clicked.connect(self.prev_page)
        
        self.page_info = QLabel("")
        self.page_info.setStyleSheet("color: rgba(255, 255, 255, 0.9); background: transparent; font-size: 12px; font-weight: 500;")
        self.page_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.next_button = QPushButton("Next ▶")
        self.next_button.setFixedSize(85, 28)  # Botones ligeramente más grandes
        self.next_button.setStyleSheet(btn_style)
        self.next_button.clicked.connect(self.next_page)
        
        self.page_nav_layout.addWidget(self.prev_button)
        self.page_nav_layout.addStretch()
        self.page_nav_layout.addWidget(self.page_info)
        self.page_nav_layout.addStretch()
        self.page_nav_layout.addWidget(self.next_button)
        
        # CAMBIO CLAVE: Agregar paginación directamente al layout principal de books_section
        self.books_section_layout.addWidget(self.page_nav)
        
        content_layout.addWidget(self.books_section)

        # BOTÓN CONFIRMAR - FIJO
        self.confirm_button = QPushButton("Confirm Reservation")
        self.confirm_button.setFixedHeight(50)
        self.confirm_button.setStyleSheet("""
            QPushButton { 
                background-color: #4A90E2; color: white; border: none; 
                border-radius: 25px; font-size: 16px; font-weight: bold; 
            } 
            QPushButton:hover { 
                background-color: #357ABD; 
            } 
            QPushButton:pressed { 
                background-color: #2E6DA4; 
            }
        """)
        self.confirm_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.confirm_button.clicked.connect(self.confirm_reservation)
        content_layout.addWidget(self.confirm_button)

        container_layout.addWidget(content_widget)

    def add_book_by_isbn(self):
        isbn = self.isbn_input.text().strip()
        if not isbn:
            return
        
        title = f"Book with ISBN {isbn}"
        self.add_book_widget(isbn, title)
        self.isbn_input.clear()

    def add_book_widget(self, isbn, title):
        book_widget = BookItemWidget(isbn, title)
        book_widget.remove_requested.connect(self.remove_book_widget)
        self.reserved_books.append(book_widget)
        
        # Ir a la última página donde estará el nuevo libro
        total_pages = (len(self.reserved_books) - 1) // self.books_per_page
        self.current_page = total_pages
        
        self.update_books_display()

    def remove_book_widget(self, book_widget):
        if book_widget in self.reserved_books:
            self.reserved_books.remove(book_widget)
            book_widget.deleteLater()
            
            # Ajustar página actual si es necesario
            if self.reserved_books:
                total_pages = (len(self.reserved_books) - 1) // self.books_per_page
                if self.current_page > total_pages:
                    self.current_page = max(0, total_pages)
            else:
                self.current_page = 0
            
            self.update_books_display()

    def update_books_display(self):
        # Limpiar el layout actual
        while self.visible_books_layout.count():
            child = self.visible_books_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
        
        if not self.reserved_books:
            # Mostrar mensaje cuando no hay libros
            self.no_books_label = QLabel("No books reserved yet.")
            self.no_books_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); background: transparent; font-style: italic;")
            self.no_books_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.visible_books_layout.addWidget(self.no_books_label)
        else:
            # Mostrar libros de la página actual
            start_idx = self.current_page * self.books_per_page
            end_idx = min(start_idx + self.books_per_page, len(self.reserved_books))
            
            for i in range(start_idx, end_idx):
                book_widget = self.reserved_books[i]
                self.visible_books_layout.addWidget(book_widget)
            
            # Agregar espaciador para mantener la distribución
            self.visible_books_layout.addStretch()
        
        self.update_navigation()

    def update_navigation(self):
        # Mostrar navegación solo si hay más libros que los que caben en una página
        has_pagination = len(self.reserved_books) > self.books_per_page
        self.page_nav.setVisible(has_pagination)
        
        if not has_pagination:
            return

        total_pages = (len(self.reserved_books) - 1) // self.books_per_page + 1
        self.page_info.setText(f"Page {self.current_page + 1} of {total_pages}")
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < total_pages - 1)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_books_display()

    def next_page(self):
        total_pages = (len(self.reserved_books) - 1) // self.books_per_page
        if self.current_page < total_pages:
            self.current_page += 1
            self.update_books_display()

    def confirm_reservation(self):
        client_name = self.client_name_input.text().strip()
        client_phone = self.client_phone_input.text().strip()
        
        if not client_name or not client_phone or not self.reserved_books:
            print("Faltan datos para la reserva.")
            return
        
        self.accept()

    def _enable_blur(self, enable: bool):
        if self._blur_effect:
            self._blur_effect.setEnabled(enable)

    def exec(self):
        self._enable_blur(True)
        result = super().exec()
        self._enable_blur(False)
        return result

    def reject(self):
        self._enable_blur(False)
        super().reject()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and event.pos().y() < self.top_bar_height:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def wheelEvent(self, event):
        if self.page_nav.isVisible():
            if event.angleDelta().y() > 0:
                self.prev_page()
            else:
                self.next_page()
            event.accept()
        else:
            super().wheelEvent(event)

    def keyPressEvent(self, event):
        if self.page_nav.isVisible():
            if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Up):
                self.prev_page()
                event.accept()
            elif event.key() in (Qt.Key.Key_Right, Qt.Key.Key_Down):
                self.next_page()
                event.accept()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = QPoint()