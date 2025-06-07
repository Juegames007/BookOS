# ARCHIVO MODIFICADO: juegames007/bookos/BookOS-e73bc84f0a94b0c519fddbb143bbf5041f6aa9c0/gui/dialogs/reservation_dialog.py

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
        self.setFixedHeight(50)  # Altura fija de una sola fila
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 8px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 10, 0)
        layout.setSpacing(10)
        
        # Información del libro en una sola línea
        book_info_text = f"{self.title if self.title else 'Libro sin título'} - ISBN: {self.isbn}"
        
        self.info_label = QLabel(book_info_text)
        self.info_label.setFont(QFont("Arial", 10))
        self.info_label.setStyleSheet("color: #333; border: none; background: transparent;")
        self.info_label.setWordWrap(False)  # No wrap para mantener en una línea
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        # Botón de eliminar con ícono
        self.remove_button = QPushButton()
        self.remove_button.setFixedSize(30, 30)
        
        # Cargar el ícono de eliminar
        try:
            icon_pixmap = QPixmap("gui/dialogs/icono_eliminar.png")
            if not icon_pixmap.isNull():
                # Escalar el ícono al tamaño del botón
                scaled_pixmap = icon_pixmap.scaled(16, 16, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.remove_button.setIcon(QIcon(scaled_pixmap))
            else:
                self.remove_button.setText("×")  # Fallback si no se puede cargar el ícono
        except:
            self.remove_button.setText("×")  # Fallback en caso de error
            
        self.remove_button.setStyleSheet("""
            QPushButton {
                background-color: #ff4444;
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #cc3333;
            }
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
        self.setMinimumSize(500, 400)  # Tamaño inicial más pequeño
        self.setMaximumWidth(500)
        self.resize(500, 400)  # Tamaño inicial

        self.font_family = FONTS.get("family", "Arial")
        self._drag_pos = QPoint()
        self.top_bar_height = 50
        self.reserved_books = []
        self.current_page = 0
        self.books_per_page = 3

        # Lógica para el efecto de desenfoque (blur)
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
        """Configura la interfaz de usuario del diálogo."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(0)
        
        # Contenedor principal con glassmorphism
        container_frame = QFrame()
        container_frame.setObjectName("containerFrame")
        container_frame.setStyleSheet(f"""
            QFrame#containerFrame {{
                background-color: rgba(255, 255, 255, 0.25);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 16px;
                backdrop-filter: blur(20px);
            }}
        """)
        main_layout.addWidget(container_frame)

        container_layout = QVBoxLayout(container_frame)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # --- Barra Superior ---
        top_bar = QFrame()
        top_bar.setFixedHeight(self.top_bar_height)
        top_bar.setStyleSheet("background-color: transparent;")
        
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(30, 10, 25, 0)

        # Título
        title_label = QLabel("Reserve Book")
        title_font = QFont(self.font_family, 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white; background: transparent; border: none; margin-top: 5px;")

        # Botón para ver reservaciones
        self.view_reservations_button = QPushButton("View Reservations")
        self.view_reservations_button.setFixedHeight(36)
        self.view_reservations_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 18px;
                padding: 0 20px;
                color: white;
                font-size: 12px;
                font-weight: 500;
                margin-top: 8px;
                margin-right: 15px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
        """)
        self.view_reservations_button.setCursor(Qt.CursorShape.PointingHandCursor)

        # Botón de cerrar (X)
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(32, 32)
        self.close_button.setFont(QFont(self.font_family, 16, QFont.Weight.Bold))
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 16px;
                color: white;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        self.close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_button.clicked.connect(self.reject)

        top_bar_layout.addWidget(title_label)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(self.view_reservations_button)
        top_bar_layout.addWidget(self.close_button)

        container_layout.addWidget(top_bar)

        # --- Contenido Principal ---
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 20, 30, 30)
        content_layout.setSpacing(20)

        # Información del cliente
        client_info_layout = QHBoxLayout()
        client_info_layout.setSpacing(15)

        # Nombre del cliente
        self.client_name_input = QLineEdit()
        self.client_name_input.setPlaceholderText("Client Name")
        self.client_name_input.setFixedHeight(45)
        
        # Teléfono del cliente
        self.client_phone_input = QLineEdit()
        self.client_phone_input.setPlaceholderText("Client Phone Number")
        self.client_phone_input.setFixedHeight(45)

        # Estilo para los inputs
        input_style = """
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 0 15px;
                font-size: 14px;
                color: #333;
            }
            QLineEdit:focus {
                border: 2px solid rgba(74, 144, 226, 0.8);
                background-color: rgba(255, 255, 255, 0.95);
            }
        """
        
        self.client_name_input.setStyleSheet(input_style)
        self.client_phone_input.setStyleSheet(input_style)

        client_info_layout.addWidget(self.client_name_input)
        client_info_layout.addWidget(self.client_phone_input)
        content_layout.addLayout(client_info_layout)

        # Input para ISBN
        self.isbn_input = QLineEdit()
        self.isbn_input.setPlaceholderText("Enter ISBN and press Enter to add book")
        self.isbn_input.setFixedHeight(45)
        self.isbn_input.setStyleSheet(input_style)
        self.isbn_input.returnPressed.connect(self.add_book_by_isbn)
        content_layout.addWidget(self.isbn_input)

        # Área de libros reservados con navegación por páginas
        self.books_section = QWidget()
        self.books_section_layout = QVBoxLayout(self.books_section)
        self.books_section_layout.setContentsMargins(0, 10, 0, 0)
        self.books_section_layout.setSpacing(10)
        
        self.books_label = QLabel("Reserved Books:")
        self.books_label.setFont(QFont(self.font_family, 14, QFont.Weight.Bold))
        self.books_label.setStyleSheet("color: white; background: transparent;")
        self.books_section_layout.addWidget(self.books_label)

        # Contenedor fijo para los libros
        self.books_display = QFrame()
        self.books_display.setMinimumHeight(50)  # Altura mínima
        self.books_display.setMaximumHeight(170)  # Altura máxima # Altura fija para 3 libros + espaciado
        self.books_display.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
            }
        """)

        # Layout para los libros visibles - CORREGIDO
        self.visible_books_layout = QVBoxLayout(self.books_display)
        self.visible_books_layout.setContentsMargins(8, 8, 8, 8)  # Márgenes uniformes
        self.visible_books_layout.setSpacing(8)
        # NO agregamos stretch aquí - eso empuja todo hacia abajo
        
        self.books_section_layout.addWidget(self.books_display)
        
        # Navegación de páginas
        self.page_nav = QFrame()
        self.page_nav_layout = QHBoxLayout(self.page_nav)
        self.page_nav_layout.setContentsMargins(0, 5, 0, 0)
        
        self.prev_button = QPushButton("◀")
        self.prev_button.setFixedSize(30, 25)
        self.prev_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 12px;
                color: white;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:disabled {
                background-color: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.5);
            }
        """)
        self.prev_button.clicked.connect(self.prev_page)
        
        self.page_info = QLabel("")
        self.page_info.setStyleSheet("color: white; background: transparent;")
        self.page_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.next_button = QPushButton("▶")
        self.next_button.setFixedSize(30, 25)
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 12px;
                color: white;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
            }
            QPushButton:disabled {
                background-color: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.5);
            }
        """)
        self.next_button.clicked.connect(self.next_page)
        
        self.page_nav_layout.addWidget(self.prev_button)
        self.page_nav_layout.addStretch()
        self.page_nav_layout.addWidget(self.page_info)
        self.page_nav_layout.addStretch()
        self.page_nav_layout.addWidget(self.next_button)
        
        self.books_section_layout.addWidget(self.page_nav)
        content_layout.addWidget(self.books_section)
        
        # Inicialmente oculta
        self.books_section.hide()
        self.update_books_section_visibility()

        # Botón de confirmar reserva
        self.confirm_button = QPushButton("Confirm Reservation")
        self.confirm_button.setFixedHeight(50)
        self.confirm_button.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;
                color: white;
                border: none;
                border-radius: 25px;
                font-size: 16px;
                font-weight: bold;
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

    def update_books_section_visibility(self):
        """Actualiza la visibilidad de los elementos de la sección de libros"""
        has_books = len(self.reserved_books) > 0
        self.books_label.setVisible(has_books)
        self.books_display.setVisible(has_books)
        self.page_nav.setVisible(has_books and len(self.reserved_books) > self.books_per_page)

    def add_book_by_isbn(self):
        """Añade un libro por ISBN"""
        isbn = self.isbn_input.text().strip()
        if not isbn:
            return
        
        # Aquí deberías implementar la lógica para buscar el libro por ISBN
        # Por ahora, simularemos encontrar el libro
        title = f"Book with ISBN {isbn}"  # Esto debería venir de tu base de datos
        
        self.add_book_widget(isbn, title)
        self.isbn_input.clear()

    def _adjust_dialog_size(self):
        """Ajusta el tamaño del diálogo según el número de libros"""
        if not self.reserved_books:
            self.resize(500, 400)
            return
        
        # Calcular libros visibles en la página actual
        start_idx = self.current_page * self.books_per_page
        end_idx = min(start_idx + self.books_per_page, len(self.reserved_books))
        visible_books = end_idx - start_idx
        
        base_height = 400  # Altura base sin libros
        
        if visible_books == 1:
            dialog_height = base_height + 150  # Espacio para 1 libro + controles
        elif visible_books == 2:
            dialog_height = base_height + 200  # Espacio para 2 libros + controles
        else:  # 3 libros
            dialog_height = base_height + 250  # Espacio para 3 libros + controles
        
        self.resize(500, dialog_height)

    def add_book_widget(self, isbn, title):
        """Añade un widget de libro a la lista"""
        book_widget = BookItemWidget(isbn, title)
        book_widget.remove_requested.connect(self.remove_book_widget)
        self.reserved_books.append(book_widget)
        
        # Mostrar la sección de libros al agregar el primer libro
        if len(self.reserved_books) == 1:
            self.books_section.show()
            # Redimensionar el diálogo de manera más compacta inicialmente
            self.resize(500, 520)  # Tamaño más pequeño para 1 libro
        
        # Actualizar visibilidad y vista
        self.update_books_section_visibility()
        
        # Ir a la última página si se añadió un libro
        if len(self.reserved_books) > 0:
            total_pages = (len(self.reserved_books) - 1) // self.books_per_page
            self.current_page = total_pages
            self.update_books_display()
            
            # Ajustar tamaño del diálogo según número de libros
            self._adjust_dialog_size()

    def remove_book_widget(self, book_widget):
        """Elimina un widget de libro de la lista"""
        if book_widget in self.reserved_books:
            self.reserved_books.remove(book_widget)
            book_widget.deleteLater()
            
            # Ajustar la página actual si es necesario
            if self.reserved_books:
                total_pages = (len(self.reserved_books) - 1) // self.books_per_page
                if self.current_page > total_pages:
                    self.current_page = max(0, total_pages)
                self.update_books_display()
                self._adjust_dialog_size()  # Usar el nuevo método
            else:
                self.current_page = 0
                # Ocultar sección y redimensionar diálogo cuando no hay libros
                self.books_section.hide()
                self.resize(500, 400)
            
            # Actualizar visibilidad
            self.update_books_section_visibility()

    def update_books_display(self):
        """Actualiza la visualización de libros según la página actual"""
        # Limpiar el layout actual
        while self.visible_books_layout.count():
            child = self.visible_books_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
        
        if not self.reserved_books:
            return
        
        # Calcular qué libros mostrar
        start_idx = self.current_page * self.books_per_page
        end_idx = min(start_idx + self.books_per_page, len(self.reserved_books))
        visible_books_count = end_idx - start_idx
        
        # Añadir los libros de la página actual
        for i in range(start_idx, end_idx):
            book_widget = self.reserved_books[i]
            self.visible_books_layout.addWidget(book_widget)
        
        # Ajustar altura del contenedor según el número de libros visibles
        # Cada libro tiene 50px de altura + 8px de espaciado + márgenes
        book_height = 50
        spacing = 8
        margins = 16  # 8 top + 8 bottom
        
        if visible_books_count == 1:
            container_height = book_height + margins
        elif visible_books_count == 2:
            container_height = (book_height * 2) + spacing + margins
        else:  # 3 o más libros
            container_height = (book_height * min(visible_books_count, 3)) + (spacing * (min(visible_books_count, 3) - 1)) + margins
        
        self.books_display.setFixedHeight(container_height)
        
        # Solo añadir stretch si tenemos menos de 3 libros visibles
        if visible_books_count < 3:
            self.visible_books_layout.addStretch()
        
        # Actualizar navegación
        self.update_navigation()

    def update_navigation(self):
        """Actualiza los controles de navegación"""
        if not self.reserved_books:
            self.page_info.setText("")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            return
        
        total_pages = (len(self.reserved_books) - 1) // self.books_per_page + 1
        self.page_info.setText(f"Page {self.current_page + 1} of {total_pages}")
        
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < total_pages - 1)

    def prev_page(self):
        """Navegar a la página anterior"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_books_display()
            self._adjust_dialog_size()

    def next_page(self):
        """Navegar a la página siguiente"""
        total_pages = (len(self.reserved_books) - 1) // self.books_per_page + 1
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.update_books_display()
            self._adjust_dialog_size()

    def confirm_reservation(self):
        """Confirma la reserva"""
        client_name = self.client_name_input.text().strip()
        client_phone = self.client_phone_input.text().strip()
        
        if not client_name or not client_phone:
            # Aquí deberías mostrar un mensaje de error
            return
        
        if not self.reserved_books:
            # Aquí deberías mostrar un mensaje de error
            return
        
        # Implementar lógica de guardado de reserva
        # ...
        
        self.accept()

    # --- Funciones para el comportamiento de la ventana (Blur y Arrastre) ---

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
        """Manejar el scroll con la rueda del mouse para navegar páginas"""
        if self.reserved_books and len(self.reserved_books) > self.books_per_page:
            if event.angleDelta().y() > 0:  # Scroll hacia arriba
                self.prev_page()
            else:  # Scroll hacia abajo
                self.next_page()
            event.accept()
        else:
            super().wheelEvent(event)

    def keyPressEvent(self, event):
        """Manejar navegación con flechas del teclado"""
        if event.key() == Qt.Key.Key_Left or event.key() == Qt.Key.Key_Up:
            self.prev_page()
            event.accept()
        elif event.key() == Qt.Key.Key_Right or event.key() == Qt.Key.Key_Down:
            self.next_page()
            event.accept()
        else:
            super().keyPressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = QPoint()