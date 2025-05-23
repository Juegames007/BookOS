"""
Diálogo para agregar un nuevo libro al inventario.

Este módulo implementa la interfaz para añadir un nuevo libro o aumentar
la cantidad de un libro existente. Permite buscar libros por ISBN utilizando
la API integrada, y completar los datos automáticamente o manualmente.
"""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QLineEdit, QPushButton, QFrame, QWidget, QMessageBox, QSizePolicy
)
from PySide6.QtGui import QFont, QPixmap, QPainter
from PySide6.QtCore import Qt, QPoint

from gui.common.styles import BACKGROUND_IMAGE_PATH, COLORS, FONTS, STYLES
from features.book_service import BookService
from core.validator import Validator

class AddBookDialog(QDialog):
    """
    Diálogo para agregar un nuevo libro o aumentar la cantidad de un libro existente.
    
    Ofrece una interfaz para ingresar el ISBN de un libro, buscar su información
    en línea, y completar los datos necesarios para guardarlo en la base de datos.
    """
    def __init__(self, book_service: BookService, parent=None):
        """
        Inicializa un nuevo diálogo para agregar libros.
        
        Args:
            book_service: Servicio para la gestión de libros
            parent (QWidget, opcional): Widget padre.
        """
        super().__init__(parent)
        self.setWindowTitle("Agregar Libro")
        self.setMinimumSize(650, 850)
        
        # Configuración de la ventana
        self.font_family = FONTS["family"]
        
        # Almacenar las dependencias inyectadas
        self.book_service = book_service
        self.ultimo_isbn_procesado_con_enter = None
        
        # Configuración del fondo con fallback
        project_root_for_bg = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        specific_background_path = os.path.join(project_root_for_bg, "app", "imagenes", "fondo_agregar.png")

        if os.path.exists(specific_background_path):
            self.background_image_path = specific_background_path
            self.background_pixmap = QPixmap(self.background_image_path)
            if self.background_pixmap.isNull(): # Comprobar si el pixmap es válido aunque el archivo exista
                print(f"Advertencia: No se pudo cargar la imagen de fondo específica: {specific_background_path}. Intentando fallback.")
                self.background_image_path = BACKGROUND_IMAGE_PATH # Fallback a la imagen global
                self.background_pixmap = QPixmap(self.background_image_path)
        else:
            print(f"Advertencia: No se encontró la imagen de fondo específica: {specific_background_path}. Usando fondo global.")
            self.background_image_path = BACKGROUND_IMAGE_PATH # Fallback a la imagen global
        self.background_pixmap = QPixmap(self.background_image_path)
        
        # Comprobación final por si el fondo global tampoco se carga
        if self.background_pixmap.isNull():
            print(f"Advertencia: No se pudo cargar ninguna imagen de fondo. Ruta global intentada: {BACKGROUND_IMAGE_PATH}")
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Configura todos los elementos de la interfaz."""
        # Crear el layout principal directamente en el QDialog
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # Contenedor para centrar el contenido principal y limitar su ancho
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0,0,0,0)
        content_container.setMaximumWidth(600)

        # --- Título del Diálogo ---
        title_label = QLabel("Agregar Libro")
        try:
            title_font = QFont(FONTS["family_title"], FONTS["size_large_title"], QFont.Weight.Normal)
        except KeyError: # Si la fuente 'Roboto' no está definida o no se carga
            try:
                title_font = QFont(FONTS["family_fallback"], FONTS["size_large_title"], QFont.Weight.Normal)
            except KeyError: # Fallback a una fuente genérica si 'Arial' tampoco está
                title_font = QFont() # Fuente por defecto del sistema
                title_font.setPointSize(FONTS.get("size_large_title", 24))
                title_font.setWeight(QFont.Weight.Normal)
                
        # Añadir un poco de cursiva para que se vea más bonito al titulo
        title_font.setItalic(True)

        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {COLORS['text_primary']}; background-color: transparent; padding-bottom: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Cargar el icono
        # Nueva ruta asumiendo que el icono está en app/imagenes/
        # Navega tres niveles hacia arriba desde gui/dialogs/add_book_dialog.py para llegar a la raíz del proyecto
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        icon_path = os.path.join(project_root, "app", "imagenes", "agregar.png")

        if os.path.exists(icon_path):
            icon_label = QLabel()
            pixmap = QPixmap(icon_path)
            icon_label.setPixmap(pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            icon_label.setStyleSheet("background-color: transparent;")
            
            title_layout = QHBoxLayout()
            title_layout.addStretch()
            title_layout.addWidget(icon_label)
            title_layout.addSpacing(10)
            title_layout.addWidget(title_label)
            title_layout.addStretch()
            content_layout.addLayout(title_layout)
        else:
            # Si el icono no se encuentra, solo mostrar el texto del título
            content_layout.addWidget(title_label)
            print(f"Advertencia: No se pudo cargar el icono en: {icon_path}")

        content_layout.addSpacing(10)

        # --- Sección de instrucciones ---
        #instruction_label = QLabel("Ingrese el ISBN y presione Enter o 'Buscar' para continuar")
        #instruction_label.setFont(QFont(self.font_family, FONTS["size_medium"]))
        #instruction_label.setStyleSheet(f"color: {COLORS['text_primary']}; background-color: transparent;")
        #instruction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        #content_layout.addWidget(instruction_label)
        #content_layout.addSpacing(15)
        
        # --- Campo ISBN con diseño destacado ---
        isbn_frame = QFrame()
        isbn_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['background_light']}; 
                border-radius: 15px;
                border: 1px solid {COLORS['border_light']};
                padding: 10px;
            }}
        """)
        isbn_frame.setMaximumWidth(400)
        isbn_layout = QVBoxLayout(isbn_frame)
        
        isbn_header = QLabel("ISBN:")
        isbn_header.setFont(QFont(self.font_family, FONTS["size_medium"], QFont.Weight.Bold))
        isbn_header.setStyleSheet(f"color: {COLORS['text_primary']}; background-color: transparent; border: none;")
        isbn_layout.addWidget(isbn_header)
        
        input_layout = QHBoxLayout()
        self.isbn_input = QLineEdit()
        self.isbn_input.setPlaceholderText("Ingrese el ISBN")
        self.isbn_input.setFixedHeight(35)
        # Comentamos setFont para ver si afecta el tamaño del placeholder
        # self.isbn_input.setFont(QFont(self.font_family, FONTS["size_medium"]))
        
        # Restauramos STYLES["input_field"] y añadimos el estilo del placeholder
        self.isbn_input.setStyleSheet(STYLES["input_field"] + 
                                    f"QLineEdit::placeholder {{ font-size: 15px; color: {COLORS['text_secondary']}; }}") 
        self.isbn_input.returnPressed.connect(self.buscar_isbn)
        
        self.buscar_button = QPushButton("Buscar")
        self.buscar_button.setFixedHeight(40)
        self.buscar_button.setFont(QFont(self.font_family, FONTS["size_normal"]))
        self.buscar_button.setStyleSheet(STYLES["button_primary_full"])
        self.buscar_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.buscar_button.clicked.connect(self.buscar_isbn)
        
        input_layout.addWidget(self.isbn_input)
        input_layout.addWidget(self.buscar_button)
        isbn_layout.addLayout(input_layout)
        
        content_layout.addWidget(isbn_frame, alignment=Qt.AlignmentFlag.AlignHCenter)
        content_layout.addSpacing(20)
        
        # --- Form layout para el resto de los campos ---
        details_frame = QFrame()
        details_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['background_medium']}; 
                border-radius: 15px;
                border: 1px solid {COLORS['border_medium']};
                padding: 15px;
            }}
            QLabel {{
                color: {COLORS['text_secondary']};
                background-color: transparent;
                border: none;
            }}
            QLineEdit {{
                {STYLES['input_field']}
            }}
            QLineEdit:disabled {{
                {STYLES['input_field_disabled']}
            }}
            QLineEdit:focus {{
                {STYLES['input_field_focus']}
            }}
        """)
        details_layout = QVBoxLayout(details_frame)
        
        details_header = QLabel("Detalles del Libro")
        details_header.setFont(QFont(self.font_family, FONTS["size_medium"], QFont.Weight.Bold))
        details_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        details_header.setStyleSheet("color: #303030; margin-bottom: 10px;")
        details_layout.addWidget(details_header)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form_layout.setLabelAlignment(Qt.AlignVCenter)
        
        # Crear y configurar los campos
        # Título
        label_titulo = QLabel("Título:")
        label_titulo.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.titulo_input = QLineEdit()
        self.titulo_input.setFixedHeight(35)
        self.titulo_input.setReadOnly(True)
        self.titulo_input.setPlaceholderText("Se completará después de buscar ISBN")
        self.titulo_input.returnPressed.connect(lambda: self._focus_next_input(self.autor_input))
        form_layout.addRow(label_titulo, self.titulo_input)
        
        # Autor
        label_autor = QLabel("Autor:")
        label_autor.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.autor_input = QLineEdit()
        self.autor_input.setFixedHeight(35)
        self.autor_input.setReadOnly(True)
        self.autor_input.setPlaceholderText("Se completará después de buscar ISBN")
        self.autor_input.returnPressed.connect(lambda: self._focus_next_input(self.editorial_input))
        form_layout.addRow(label_autor, self.autor_input)
        
        # Editorial
        label_editorial = QLabel("Editorial:")
        label_editorial.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.editorial_input = QLineEdit()
        self.editorial_input.setFixedHeight(35)
        self.editorial_input.setReadOnly(True)
        self.editorial_input.setPlaceholderText("Se completará después de buscar ISBN")
        self.editorial_input.returnPressed.connect(lambda: self._focus_next_input(self.imagen_input))
        form_layout.addRow(label_editorial, self.editorial_input)
        
        # URL Imagen
        label_imagen = QLabel("URL Imagen:")
        label_imagen.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        self.imagen_input = QLineEdit()
        self.imagen_input.setFixedHeight(35)
        self.imagen_input.setReadOnly(True)
        self.imagen_input.setPlaceholderText("Se completará después de buscar ISBN")
        self.imagen_input.returnPressed.connect(lambda: self._focus_next_input(self.categorias_input))
        form_layout.addRow(label_imagen, self.imagen_input)
        
        # Categorías
        label_categorias = QLabel("Categorías:")
        label_categorias.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.categorias_input = QLineEdit()
        self.categorias_input.setFixedHeight(35)
        self.categorias_input.setReadOnly(True)
        self.categorias_input.setPlaceholderText("Se completará después de buscar ISBN")
        self.categorias_input.returnPressed.connect(lambda: self._focus_next_input(self.precio_input))
        form_layout.addRow(label_categorias, self.categorias_input)

        # Precio - Vuelve a ser un campo simple en el QFormLayout
        label_precio = QLabel("Precio:")
        label_precio.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        
        self.precio_input = QLineEdit()
        self.precio_input.setFixedHeight(35)
        self.precio_input.setReadOnly(True)
        self.precio_input.setPlaceholderText("Ej: 15.000") # Placeholder actualizado
        self.precio_input.returnPressed.connect(lambda: self._focus_next_input(self.posicion_input))
        self.precio_input.editingFinished.connect(self._formatear_texto_precio) # Formatear al perder foco
        # El estilo se tomará del QFrame details_frame que define estilos para QLineEdit
        # self.precio_input.setStyleSheet(...) # Ya no se aplica estilo inline complejo aquí
        form_layout.addRow(label_precio, self.precio_input) # Añadir directamente al form_layout
        
        # Posición
        label_posicion = QLabel("Posición:")
        label_posicion.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.posicion_input = QLineEdit()
        self.posicion_input.setFixedHeight(35)
        self.posicion_input.setReadOnly(True)
        self.posicion_input.setPlaceholderText("Ej: 01A, 12B, 03C")
        self.posicion_input.returnPressed.connect(self.guardar_libro_on_enter)
        form_layout.addRow(label_posicion, self.posicion_input)
        
        details_layout.addLayout(form_layout)
        content_layout.addWidget(details_frame)
        content_layout.addSpacing(20)
        
        # --- Botones de acción ---
        button_layout = QHBoxLayout()
        self.guardar_button = QPushButton("Guardar")
        self.guardar_button.setEnabled(False)  # Inicialmente deshabilitado
        self.guardar_button.setFixedHeight(40)
        self.guardar_button.setFont(QFont(self.font_family, FONTS["size_normal"]))
        self.guardar_button.clicked.connect(self.guardar_libro)
        
        self.cancelar_button = QPushButton("Cancelar")
        self.cancelar_button.setFixedHeight(40)
        self.cancelar_button.setFont(QFont(self.font_family, FONTS["size_normal"]))
        self.cancelar_button.setStyleSheet(STYLES["button_danger_full"])
        self.cancelar_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancelar_button.clicked.connect(self.reject)
        
        button_layout.addStretch(1)
        button_layout.addWidget(self.guardar_button)
        button_layout.addWidget(self.cancelar_button)
        button_layout.addStretch(1)
        
        content_layout.addLayout(button_layout)

        # Añadir el contenedor de contenido al layout principal del diálogo
        main_layout.addStretch(1)
        main_layout.addWidget(content_container)
        main_layout.addStretch(1)
        
        # Llamada final para ajustar el tamaño
        self.adjustSize()

        # Aplicar estilo inicial al botón guardar
        self._actualizar_estilo_guardar_button()
        
        # Dar foco al campo de ISBN después de configurar todo y ajustar tamaño
        self.isbn_input.setFocus()

    def _actualizar_estilo_guardar_button(self):
        """Actualiza el estilo del botón Guardar según su estado (habilitado/deshabilitado)."""
        if self.guardar_button.isEnabled():
            self.guardar_button.setStyleSheet(STYLES["button_success_full"])
            self.guardar_button.setCursor(Qt.CursorShape.PointingHandCursor) # Mano si habilitado
        else:
            self.guardar_button.setStyleSheet(STYLES["button_disabled"])
            self.guardar_button.setCursor(Qt.CursorShape.ArrowCursor) # Flecha si deshabilitado

    def _focus_next_input(self, next_input_field: QLineEdit):
        """Mueve el foco al siguiente campo de entrada especificado."""
        if next_input_field.isReadOnly(): # Si el siguiente campo está bloqueado (porque no se ha buscado ISBN)
            # Intentamos buscar el siguiente campo editable o el botón guardar
            current_widget = self.focusWidget()
            if current_widget == self.isbn_input: # Si estamos en ISBN, el enter es para buscar
                self.buscar_isbn()
                return

            # Orden de los campos para la navegación con Enter
            ordered_inputs = [
                self.titulo_input, self.autor_input, self.editorial_input,
                self.imagen_input, self.categorias_input, self.precio_input, self.posicion_input
            ]
            try:
                current_index = ordered_inputs.index(current_widget)
                # Buscar el siguiente campo editable
                for i in range(current_index + 1, len(ordered_inputs)):
                    if not ordered_inputs[i].isReadOnly():
                        ordered_inputs[i].setFocus()
                        ordered_inputs[i].selectAll() # Seleccionar texto para fácil edición
                        return
                # Si no hay más campos editables, y el botón guardar está habilitado, enfocarlo.
                if self.guardar_button.isEnabled():
                     self.guardar_button.setFocus() # Esto no dispara el click, solo enfoca
                # Si el botón guardar no está habilitado, no hacer nada o enfocar el primer campo editable
                else:
                    for field in ordered_inputs:
                        if not field.isReadOnly():
                            field.setFocus()
                            field.selectAll()
                            return
                    self.isbn_input.setFocus() # Fallback al ISBN si nada más es editable

            except ValueError: # Si el widget actual no está en la lista (p.ej. un botón)
                self.isbn_input.setFocus() # Fallback
        else:
            next_input_field.setFocus()
            next_input_field.selectAll() # Seleccionar texto para fácil edición

    def guardar_libro_on_enter(self):
        """Intenta guardar el libro si el botón de guardar está habilitado."""
        if self.guardar_button.isEnabled():
            self.guardar_libro()
        # else: Podrías añadir un feedback si el guardado no está listo

    def paintEvent(self, event):
        """Dibuja la imagen de fondo en el diálogo."""
        if not self.background_pixmap.isNull():
            painter = QPainter(self)
            scaled_pixmap = self.background_pixmap.scaled(
                self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            point = QPoint(0, 0)
            if scaled_pixmap.width() > self.width():
                point.setX(int((scaled_pixmap.width() - self.width()) / -2))
            if scaled_pixmap.height() > self.height():
                point.setY(int((scaled_pixmap.height() - self.height()) / -2))
            painter.drawPixmap(point, scaled_pixmap)
        super().paintEvent(event)

    def buscar_isbn(self):
        """
        Busca información del libro a partir del ISBN ingresado.
        
        Utiliza el servicio de libros para buscar datos en línea. 
        Si encuentra el libro, rellena los campos automáticamente.
        Si no lo encuentra, habilita todos los campos para entrada manual.
        """
        isbn_actual = self.isbn_input.text().strip()
        
        if isbn_actual == self.ultimo_isbn_procesado_con_enter and self.guardar_button.isEnabled():
            return

        if not isbn_actual:
            QMessageBox.warning(self, "Error", "Por favor ingrese un ISBN.")
            return

        if not Validator.is_valid_isbn(isbn_actual): # Validar ISBN
            QMessageBox.warning(self, "Error", "El ISBN ingresado no es válido. Debe tener 10 o 13 dígitos numéricos.")
            self.isbn_input.selectAll()
            self.isbn_input.setFocus()
            return
            
        book_data = self.book_service.buscar_libro_por_isbn(isbn_actual)
        
        self.ultimo_isbn_procesado_con_enter = isbn_actual
        
        if book_data:
            # Rellenar campos con la información obtenida
            self.titulo_input.setText(book_data.get("Título", ""))
            self.autor_input.setText(book_data.get("Autor", ""))
            self.editorial_input.setText(book_data.get("Editorial", ""))
            self.imagen_input.setText(book_data.get("Imagen", ""))
            self.categorias_input.setText(", ".join(book_data.get("Categorías", [])))
            
            # Habilitar campos para entrada manual
            self.titulo_input.setReadOnly(False)
            self.autor_input.setReadOnly(False)
            self.editorial_input.setReadOnly(False)
            self.imagen_input.setReadOnly(False)
            self.categorias_input.setReadOnly(False)
            self.precio_input.setReadOnly(False)
            self.posicion_input.setReadOnly(False)
            
            # Habilitar el botón de guardar y actualizar su estilo
            self.guardar_button.setEnabled(True)
            self._actualizar_estilo_guardar_button()
            
            # Enfocar el campo de precio
            self.precio_input.setFocus()
        else:
            # Si no se encuentra el libro, habilitar todos los campos para entrada manual
            QMessageBox.information(self, "Libro no encontrado", 
                                  "El libro no fue encontrado en la base de datos online. Por favor, ingrese los datos manualmente.")
            self.titulo_input.setReadOnly(False)
            self.autor_input.setReadOnly(False)
            self.editorial_input.setReadOnly(False)
            self.imagen_input.setReadOnly(False)
            self.categorias_input.setReadOnly(False)
            self.precio_input.setReadOnly(False)
            self.posicion_input.setReadOnly(False)
            
            # Habilitar el botón de guardar y actualizar su estilo
            self.guardar_button.setEnabled(True)
            self._actualizar_estilo_guardar_button()
            
            self.titulo_input.setFocus()

    def _limpiar_valor_precio(self, texto_con_formato: str) -> str:
        """Elimina los separadores de miles del texto del precio."""
        return texto_con_formato.replace(".", "") # Solo quitar los puntos

    def _formatear_texto_precio(self):
        """Formatea el texto del QLineEdit de precio para mostrar separadores de miles."""
        current_text_limpio = self._limpiar_valor_precio(self.precio_input.text())
        if not current_text_limpio.isdigit():
            # Si después de limpiar no son solo dígitos (podría estar vacío o tener otros caracteres)
            # podríamos optar por limpiarlo o dejarlo como está si la validación al guardar lo maneja.
            # Por ahora, si no es un número válido, no lo formateamos.
            return
        try:
            valor_numerico = int(current_text_limpio)
            # Formato para pesos colombianos (o similar), ej: 1.234.567
            # Usamos f-string con formato de comas y luego reemplazamos comas por puntos.
            texto_formateado = f"{valor_numerico:,}".replace(",", ".")
            self.precio_input.setText(texto_formateado)
        except ValueError:
            # En caso de que la conversión falle, aunque isdigit debería prevenirlo
            pass # No hacer nada, dejar el texto como está.

    def guardar_libro(self):
        """
        Guarda el libro en la base de datos usando el servicio de libros.
        
        Realiza validaciones de los campos obligatorios, incluyendo el precio mínimo,
        y luego guarda el libro y lo añade al inventario.
        """
        # Validar campos obligatorios
        if not self.titulo_input.text().strip():
            QMessageBox.warning(self, "Error", "El título es obligatorio.")
            self.titulo_input.setFocus()
            return
            
        try:
            # Limpiar el texto del precio antes de convertirlo
            precio_texto_limpio = self._limpiar_valor_precio(self.precio_input.text())
            
            if not precio_texto_limpio:
                QMessageBox.warning(self, "Error", "El precio es obligatorio.")
                self.precio_input.setFocus()
                return
            try:
                precio = int(precio_texto_limpio)
            except ValueError:
                QMessageBox.warning(self, "Error", "El precio debe ser un número entero válido (ej: 15000 o 15.000).")
                self.precio_input.setFocus()
                self.precio_input.selectAll()
                return
            
            # Validación del precio mínimo en la GUI
            if precio < 1000:
                QMessageBox.warning(self, "Error", "El precio del libro debe ser igual o mayor a 1000.")
                self.precio_input.setFocus()
                self.precio_input.selectAll()
                return
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error en el precio: {str(e)}")
            self.precio_input.setFocus()
            return
            
        if not self.posicion_input.text().strip():
            QMessageBox.warning(self, "Error", "La posición es obligatoria.")
            self.posicion_input.setFocus()
            return
            
        posicion = self.posicion_input.text().strip().upper()
        if posicion not in self.book_service.posiciones_validas:
            QMessageBox.warning(self, "Error", f"La posición '{posicion}' no es válida. Debe tener el formato: 01A-99J")
            self.posicion_input.setFocus()
            return
            
        try:
            # Preparar datos del libro
            isbn = self.isbn_input.text().strip()
            book_info = {
                "ISBN": isbn,
                "Título": self.titulo_input.text().strip(),
                "Autor": self.autor_input.text().strip(),
                "Editorial": self.editorial_input.text().strip(),
                "Imagen": self.imagen_input.text().strip(),
                "Categorías": [cat.strip() for cat in self.categorias_input.text().split(",") if cat.strip()],
                "Precio": precio,
                "Posición": posicion
            }
            
            # Guardar el libro usando el servicio
            success, message = self.book_service.guardar_libro(book_info)
            if not success:
                QMessageBox.critical(self, "Error", message)
                return
                
            # Guardar en inventario
            success, message, cantidad = self.book_service.guardar_libro_en_inventario(isbn, posicion)
            if success:
                if cantidad > 1:
                    QMessageBox.information(self, "Éxito", f"Se incrementó la cantidad del libro en la posición {posicion}. Nueva cantidad: {cantidad}")
                else:
                    QMessageBox.information(self, "Éxito", "Libro agregado correctamente al inventario.")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", message)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar el libro: {str(e)}")
    
    def resizeEvent(self, event):
        """Actualiza el fondo cuando cambia el tamaño de la ventana."""
        self.update()
        super().resizeEvent(event) 