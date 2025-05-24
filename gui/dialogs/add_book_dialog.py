"""
Diálogo para agregar un nuevo libro al inventario.

Este módulo implementa la interfaz para añadir un nuevo libro o aumentar
la cantidad de un libro existente. Permite buscar libros por ISBN utilizando
la API integrada, y completar los datos automáticamente o manualmente.
"""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QLineEdit, QPushButton, QFrame, QWidget, QMessageBox, QSizePolicy, QCheckBox
)
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QBrush
from PySide6.QtCore import Qt, QPoint, Signal, QRectF, Property, QPropertyAnimation, QEasingCurve
from typing import Dict, Any

from gui.common.styles import BACKGROUND_IMAGE_PATH, COLORS, FONTS, STYLES
from features.book_service import BookService
from core.validator import Validator

class CustomToggleSwitch(QWidget):
    toggled = Signal(bool)

    def __init__(self, parent=None, discapacidad_color_on=QColor("#34C759"), discapacidad_color_off=QColor("#E9E9EA"), circulo_color=QColor("white")):
        super().__init__(parent)
        self.setCheckable(True)
        self._checked = False
        self.setFixedHeight(22) # Altura fija para el toggle
        self.setFixedWidth(40)  # Ancho fijo

        self._discapacidad_color_on = discapacidad_color_on
        self._discapacidad_color_off = discapacidad_color_off
        self._circulo_color = circulo_color

        self._margen_circulo = 2
        self._radio_circulo = (self.height() - 2 * self._margen_circulo) / 2

        # Inicializar _posicion_circulo_manual ANTES de crear QPropertyAnimation
        self._posicion_circulo_manual = self._get_posicion_calculada_circulo()

        self._posicion_circulo_anim = QPropertyAnimation(self, b"posicion_circulo_propiedad", self)
        self._posicion_circulo_anim.setDuration(150) # Duración de la animación en ms
        self._posicion_circulo_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def isCheckable(self):
        return True # Siempre es checkable

    def setCheckable(self, checkable):
        pass # No hace nada, siempre es checkable

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self._actualizar_animacion_circulo()
            self.toggled.emit(self._checked)
            self.update() # Repintar

    def toggle(self):
        self.setChecked(not self.isChecked())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        radio_fondo = rect.height() / 2
        # Usar _posicion_circulo_manual para pintar, ya que es actualizado por la animación
        posicion_circulo_actual_para_pintar = getattr(self, '_posicion_circulo_manual', self._get_posicion_calculada_circulo())

        if self.isChecked():
            painter.setBrush(QBrush(self._discapacidad_color_on))
        else:
            painter.setBrush(QBrush(self._discapacidad_color_off))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, radio_fondo, radio_fondo)

        painter.setBrush(QBrush(self._circulo_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPoint(int(posicion_circulo_actual_para_pintar), int(rect.center().y())),
                              int(self._radio_circulo), int(self._radio_circulo))

    def _actualizar_animacion_circulo(self):
        self._posicion_circulo_anim.stop()
        # El valor inicial de la animación ahora es la posición manual actual
        start_x = getattr(self, '_posicion_circulo_manual', self._get_posicion_calculada_circulo())
        end_x = self._get_posicion_calculada_circulo() # El destino es la posición calculada basada en el nuevo estado _checked
        
        self._posicion_circulo_anim.setStartValue(start_x)
        self._posicion_circulo_anim.setEndValue(end_x)
        self._posicion_circulo_anim.start()

    def _get_posicion_calculada_circulo(self):
        """Devuelve la posición X del centro del círculo basada en el estado _checked y dimensiones."""
        if not self.isChecked():
            return self._margen_circulo + self._radio_circulo
        else:
            return self.width() - self._margen_circulo - self._radio_circulo

    def _get_posicion_circulo_actual(self):
        """Devuelve la posición calculada del círculo. No depende de la animación directamente."""
        return self._get_posicion_calculada_circulo()

    def _set_posicion_circulo_propiedad(self, pos):
        self._posicion_circulo_manual = pos
        self.update()

    def _get_posicion_circulo_propiedad(self):
        """Getter para la propiedad de animación. Usa _posicion_circulo_manual o la posición calculada."""
        return getattr(self, '_posicion_circulo_manual', self._get_posicion_calculada_circulo())

    posicion_circulo_propiedad = Property(float, _get_posicion_circulo_propiedad, _set_posicion_circulo_propiedad)

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
        self.ultimo_isbn_para_advertencia = None
        self.advertencia_isbn_mostrada_recientemente = False
        self.ultima_posicion_ingresada = None # Asegurar que esté inicializada
        
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
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0,0,0,0)
        content_container.setMaximumWidth(600)

        # --- Título del Diálogo y Toggle "Cerrar al terminar" ---
        title_row_layout = QHBoxLayout() # Layout para toda la fila del título

        # Grupo para centrar Icono y Título "Agregar Libro"
        title_group_layout = QHBoxLayout()
        # title_group_layout.setContentsMargins(0,0,0,0) # Opcional, si se necesita ajuste fino

        # icon_label = QLabel()
        # project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        # icon_path = os.path.join(project_root, "app", "imagenes", "agregar.png")
        # if os.path.exists(icon_path):
        #     pixmap = QPixmap(icon_path)
        #     icon_label.setPixmap(pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        #     icon_label.setStyleSheet("background-color: transparent;")
        #     title_group_layout.addWidget(icon_label)
        #     title_group_layout.addSpacing(10)
        # else:
        #     print(f"Advertencia: No se pudo cargar el icono en: {icon_path}")

        title_label = QLabel("              Agregar Libro") # Quitar espacios extra si el icono se elimina
        try:
            title_font = QFont(FONTS["family_title"], FONTS["size_large_title"], QFont.Weight.Normal)
        except KeyError:
            try:
                title_font = QFont(FONTS["family_fallback"], FONTS["size_large_title"], QFont.Weight.Normal)
            except KeyError:
                title_font = QFont()
                title_font.setPointSize(FONTS.get("size_large_title", 24))
                title_font.setWeight(QFont.Weight.Normal)
        title_font.setItalic(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {COLORS['text_primary']}; background-color: transparent; padding-bottom: 0px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        title_group_layout.addWidget(title_label)
        
        # Añadir el grupo del título al layout de la fila, con stretches para centrarlo
        title_row_layout.addStretch(1) 
        title_row_layout.addLayout(title_group_layout)
        title_row_layout.addStretch(1)

        # Toggle "Cerrar al terminar" (se mantiene a la derecha del todo por los stretches anteriores)
        cerrar_label = QLabel("Cerrar:")
        cerrar_label.setFont(QFont(self.font_family, FONTS.get("size_small", 10)))
        cerrar_label.setStyleSheet(f"color: {COLORS['text_secondary']}; background-color: transparent; margin-right: 5px;")
        cerrar_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        title_row_layout.addWidget(cerrar_label)

        self.cerrar_al_terminar_toggle = CustomToggleSwitch(discapacidad_color_on=QColor(COLORS.get('primary', '#007BFF')), discapacidad_color_off=QColor(COLORS.get('gray_medium', '#adb5bd')))
        self.cerrar_al_terminar_toggle.setChecked(True)
        title_row_layout.addWidget(self.cerrar_al_terminar_toggle)
        
        content_layout.addLayout(title_row_layout) 
        content_layout.addSpacing(15) 
        
        # --- Sección de ISBN y Búsqueda (sin el toggle aquí) ---
        isbn_section_frame = QFrame() 
        isbn_section_frame.setStyleSheet(f""" 
            QFrame {{
                background-color: {COLORS['background_light']}; 
                border-radius: 15px;
                border: 1px solid {COLORS['border_light']};
                padding: 10px;
            }}
        """)
        isbn_section_frame.setMaximumWidth(500) 

        isbn_section_layout = QVBoxLayout(isbn_section_frame)
        isbn_section_layout.setContentsMargins(0,0,0,0)
        isbn_section_layout.setSpacing(8) 
        
        isbn_header_label = QLabel("ISBN:")
        isbn_header_label.setFont(QFont(self.font_family, FONTS["size_medium"], QFont.Weight.Bold))
        isbn_header_label.setStyleSheet(f"color: {COLORS['text_primary']}; background-color: transparent; border: none; padding-left: 2px;")
        isbn_section_layout.addWidget(isbn_header_label)
        
        # Layout solo para input ISBN y botón Buscar
        input_buscar_layout = QHBoxLayout()
        self.isbn_input = QLineEdit()
        self.isbn_input.setPlaceholderText("Ingrese el ISBN")
        self.isbn_input.setFixedHeight(35)
        self.isbn_input.setStyleSheet(STYLES["input_field"] + 
                                    f"QLineEdit::placeholder {{ font-size: 15px; color: {COLORS['text_secondary']}; }}") 
        self.isbn_input.returnPressed.connect(self.buscar_isbn)
        input_buscar_layout.addWidget(self.isbn_input, 3) 
        
        self.buscar_button = QPushButton("Buscar")
        self.buscar_button.setFixedHeight(40)
        self.buscar_button.setFont(QFont(self.font_family, FONTS["size_normal"]))
        self.buscar_button.setStyleSheet(STYLES["button_primary_full"])
        self.buscar_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.buscar_button.clicked.connect(self.buscar_isbn)
        input_buscar_layout.addWidget(self.buscar_button, 1)
        
        isbn_section_layout.addLayout(input_buscar_layout)
        
        content_layout.addWidget(isbn_section_frame, alignment=Qt.AlignmentFlag.AlignHCenter)
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

    def _clear_book_details_fields_and_disable_save(self):
        """Limpia solo los campos de detalles del libro y deshabilita el guardado, manteniendo el ISBN."""
        self.titulo_input.clear()
        self.titulo_input.setReadOnly(True)
        self.autor_input.clear()
        self.autor_input.setReadOnly(True)
        self.editorial_input.clear()
        self.editorial_input.setReadOnly(True)
        self.imagen_input.clear()
        self.imagen_input.setReadOnly(True)
        self.categorias_input.clear()
        self.categorias_input.setReadOnly(True)
        self.precio_input.clear()
        self.precio_input.setReadOnly(True)
        self.posicion_input.clear()
        self.posicion_input.setReadOnly(True)
        
        self.guardar_button.setEnabled(False)
        self._actualizar_estilo_guardar_button()
        # No se toca self.ultimo_isbn_procesado_con_enter aquí
        # El foco se manejará por el llamador después de esta limpieza.

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

    def _fill_form_fields(self, book_details: Dict[str, Any], make_editable: bool):
        """Rellena los campos del formulario con los detalles del libro y los hace editables o no."""
        self.titulo_input.setText(book_details.get("Título", ""))
        self.autor_input.setText(book_details.get("Autor", ""))
        self.editorial_input.setText(book_details.get("Editorial", ""))
        self.imagen_input.setText(book_details.get("Imagen", ""))
        self.categorias_input.setText(", ".join(book_details.get("Categorías", [])))
        # El precio podría necesitar formato si se obtiene de la DB/API
        precio_val = book_details.get("Precio", "")
        self.precio_input.setText(str(precio_val) if precio_val else "")
        if precio_val: self._formatear_texto_precio() # Formatear si hay valor
        
        # La posición no se rellena automáticamente desde 'book_details' genérico,
        # se maneja por separado o se pide al usuario.
        # self.posicion_input.setText(book_details.get("Posición", ""))

        self.titulo_input.setReadOnly(not make_editable)
        self.autor_input.setReadOnly(not make_editable)
        self.editorial_input.setReadOnly(not make_editable)
        self.imagen_input.setReadOnly(not make_editable)
        self.categorias_input.setReadOnly(not make_editable)
        self.precio_input.setReadOnly(not make_editable)
        self.posicion_input.setReadOnly(not make_editable) # Posición siempre editable si se llegó a este punto

        if make_editable:
            self.guardar_button.setEnabled(True)
        self._actualizar_estilo_guardar_button()

    def buscar_isbn(self):
        isbn_actual = self.isbn_input.text().strip()
        
        # Lógica para evitar doble mensaje si la misma condición de error persiste tras una advertencia reciente
        if self.advertencia_isbn_mostrada_recientemente:
            if (not isbn_actual and self.ultimo_isbn_para_advertencia == "") or \
               (isbn_actual and self.ultimo_isbn_para_advertencia is not None and isbn_actual == self.ultimo_isbn_para_advertencia):
                return # Misma condición de error, no repetir mensaje.

        if not isbn_actual:
            QMessageBox.warning(self, "Error", "Por favor ingrese un ISBN.")
            self.isbn_input.setFocus()
            self.ultimo_isbn_para_advertencia = "" # Marcar que el error fue por campo vacío
            self.advertencia_isbn_mostrada_recientemente = True
            return

        if not Validator.is_valid_isbn(isbn_actual):
            QMessageBox.warning(self, "Error", "El ISBN ingresado no es válido. Debe tener 10 o 13 dígitos numéricos.")
            self.isbn_input.selectAll()
            self.isbn_input.setFocus()
            self.ultimo_isbn_para_advertencia = isbn_actual # Marcar el ISBN que causó el error
            self.advertencia_isbn_mostrada_recientemente = True
            return
            
        # Si la validación local pasó, resetear el estado de advertencia reciente
        self.advertencia_isbn_mostrada_recientemente = False
        self.ultimo_isbn_para_advertencia = None

        # Evitar múltiples procesamientos si el botón Guardar ya está activo para este ISBN
        # y el usuario presiona Enter de nuevo. (Esta lógica es para después de una búsqueda exitosa)
        if isbn_actual == self.ultimo_isbn_procesado_con_enter and self.guardar_button.isEnabled():
            return
            
        search_result = self.book_service.buscar_libro_por_isbn(isbn_actual)
        status = search_result["status"]
        book_details = search_result["book_details"]
        inventory_entries = search_result["inventory_entries"]
        
        self.ultimo_isbn_procesado_con_enter = isbn_actual # Marcar como procesado
        # No limpiamos self.posicion_input.clear() aquí para preservar la posición si ya existe

        if status == "encontrado_completo" and inventory_entries:
            # Libro en DB y en al menos una posición de inventario
            first_entry = inventory_entries[0] # Tomamos la primera para el mensaje
            titulo = book_details.get("Título", "Desconocido")
            pos = first_entry["posicion"]
            precio_reg = first_entry["precio_venta_registrado"]
            # Formatear precio para el mensaje
            precio_msg = f"{precio_reg:,}".replace(",", ".")

            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Libro Existente")
            msg_box.setText(f'El libro "<b>{titulo}</b>" ya existe en la posición <b>{pos}</b> (Precio: ${precio_msg}).')
            msg_box.setInformativeText("¿Desea agregar otra unidad en esta posición o editar/agregar en otra parte?")
            msg_box.setIcon(QMessageBox.Icon.Question)
            btn_agregar_unidad = msg_box.addButton("Agregar Unidad Aquí", QMessageBox.ButtonRole.YesRole)
            btn_editar_o_nueva = msg_box.addButton("Editar/Nueva Posición", QMessageBox.ButtonRole.NoRole)
            msg_box.addButton(QMessageBox.StandardButton.Cancel)
            # Estilo general del QMessageBox (podría ser una función de utilidad)
            msg_box.setStyleSheet(""" 
                QMessageBox { background-color: #f0f0f0; font-family: Arial, sans-serif; } 
                QLabel#qt_msgbox_label { font-size: 16px; color: #333; } /* Texto principal */
                QLabel#qt_msgbox_informativeLabel { font-size: 14px; color: #555; } /* Texto informativo */
                QPushButton { padding: 8px 15px; font-size: 14px; border-radius: 5px; }
            """)
            # Estilos específicos para botones (si es necesario, usando objectName)
            # btn_agregar_unidad.setStyleSheet(STYLES.get("button_success_full", "")) 
            # btn_editar_o_nueva.setStyleSheet(STYLES.get("button_primary_full", ""))

            msg_box.exec()

            if msg_box.clickedButton() == btn_agregar_unidad:
                success_inv, message_inv, cantidad_inv = self.book_service.guardar_libro_en_inventario(isbn_actual, pos)
                if success_inv:
                    QMessageBox.information(self, "Éxito", f"Se incrementó la cantidad en la posición {pos}. Nueva cantidad: {cantidad_inv}")
                    if not self.cerrar_al_terminar_toggle.isChecked(): # Modo múltiples
                        self.ultima_posicion_ingresada = pos # Guardar la posición actual
                        self._reset_for_next_book()
                    else: # No modo múltiples (Cerrar al terminar)
                        self.ultima_posicion_ingresada = None # Limpiar al cerrar
                        self.accept()
                else:
                    QMessageBox.warning(self, "Error", message_inv)
            elif msg_box.clickedButton() == btn_editar_o_nueva:
                self._fill_form_fields(book_details, make_editable=True)
                # Llenar la posición existente para que el usuario pueda modificarla o cambiarla
                self.posicion_input.setText(pos) 
                self.precio_input.setFocus() # O el campo que tenga más sentido editar primero
            else: # Cancelar
                self._reset_for_next_book() # O simplemente no hacer nada y dejar el ISBN allí

        elif status == "encontrado_en_libros":
            # Libro en DB pero no en inventario
            QMessageBox.information(self, "Información de Libro Encontrada", 
                                  "Los detalles de este libro se encontraron en la base de datos. Por favor, ingrese precio y posición para añadirlo al inventario.")
            self._fill_form_fields(book_details, make_editable=True)
            self.precio_input.setFocus()
        
        elif status == "solo_api":
            # Libro encontrado solo en API externa
            QMessageBox.information(self, "Información de Libro Obtenida", 
                                  "Se encontraron datos del libro en línea. Verifique y complete la información necesaria.")
            self._fill_form_fields(book_details, make_editable=True)
            self.precio_input.setFocus() # O el primer campo editable que tenga sentido

        elif status == "no_encontrado":
            QMessageBox.information(self, "Libro no encontrado", 
                                  "El libro no fue encontrado. Por favor, ingrese los datos manualmente.")
            # Guardar el valor actual de la posición antes de limpiar/llenar otros campos
            posicion_actual_antes_de_manual = self.posicion_input.text()
            
            # Limpiar campos por si había algo, y hacerlos todos editables
            self._clear_book_details_fields_and_disable_save() # Limpia detalles, pero no el ISBN ni la posición
            self._fill_form_fields({}, make_editable=True) # Para asegurar que estén editables y habilita guardar
            
            # Restaurar la posición que estaba antes, si había alguna
            self.posicion_input.setText(posicion_actual_antes_de_manual)
            # Asegurarse de que la posición sea editable (ya debería serlo por _fill_form_fields)
            self.posicion_input.setReadOnly(False)
            
            self.titulo_input.setFocus()
        
        # Si después de buscar, algún campo que deba ser editable no lo es, forzarlo
        # Esta es una salvaguarda, la lógica anterior debería manejarlo.
        if not self.precio_input.isReadOnly() and not self.posicion_input.isReadOnly():
            self.guardar_button.setEnabled(True)
            self._actualizar_estilo_guardar_button()

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

    def _reset_for_next_book(self):
        """Limpia los campos del formulario para agregar el siguiente libro."""
        self.isbn_input.clear()
        self.titulo_input.clear()
        self.titulo_input.setReadOnly(True)
        self.autor_input.clear()
        self.autor_input.setReadOnly(True)
        self.editorial_input.clear()
        self.editorial_input.setReadOnly(True)
        self.imagen_input.clear()
        self.imagen_input.setReadOnly(True)
        self.categorias_input.clear()
        self.categorias_input.setReadOnly(True)
        self.precio_input.clear()
        self.precio_input.setReadOnly(True)
        self.posicion_input.clear()
        self.posicion_input.setReadOnly(True)
        
        self.guardar_button.setEnabled(False)
        self._actualizar_estilo_guardar_button()
        self.ultimo_isbn_procesado_con_enter = None
        self.isbn_input.setFocus()
        # Simular que la última advertencia fue por ISBN vacío para evitar mensaje por doble enter
        self.advertencia_isbn_mostrada_recientemente = True
        self.ultimo_isbn_para_advertencia = ""
        
        # Lógica para la posición
        if hasattr(self, 'ultima_posicion_ingresada') and self.ultima_posicion_ingresada and \
           hasattr(self, 'cerrar_al_terminar_toggle') and not self.cerrar_al_terminar_toggle.isChecked():
            self.posicion_input.setText(self.ultima_posicion_ingresada)
        else:
            self.posicion_input.clear() # Limpiar si el toggle está activado, no existe el atributo/toggle, o no hay última posición
        self.posicion_input.setReadOnly(True)

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
            success_book_db, message_book_db = self.book_service.guardar_libro(book_info)
            if not success_book_db:
                QMessageBox.critical(self, "Error", message_book_db)
                return
                
            # Guardar en inventario
            success_inv, message_inv, cantidad_inv = self.book_service.guardar_libro_en_inventario(isbn, posicion)
            if success_inv:
                if cantidad_inv > 1:
                    QMessageBox.information(self, "Éxito", f"Se incrementó la cantidad del libro en la posición {posicion}. Nueva cantidad: {cantidad_inv}")
                else:
                    QMessageBox.information(self, "Éxito", "Libro agregado correctamente al inventario.")
                
                if not self.cerrar_al_terminar_toggle.isChecked(): # Modo múltiples
                    self.ultima_posicion_ingresada = posicion # Guardar la posición actual
                    self._reset_for_next_book()
                else: # No modo múltiples (Cerrar al terminar)
                    self.ultima_posicion_ingresada = None # Limpiar al cerrar
                    self.accept()
            else:
                # Si falló guardar en inventario, ¿qué hacer? ¿Revertir el guardado en 'libros'?
                # Por ahora, solo mostramos el error.
                QMessageBox.warning(self, "Error en Inventario", message_inv)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar el libro: {str(e)}")
    
    def resizeEvent(self, event):
        """Actualiza el fondo cuando cambia el tamaño de la ventana."""
        self.update()
        super().resizeEvent(event) 