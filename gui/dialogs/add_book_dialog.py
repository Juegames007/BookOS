"""
Diálogo para agregar un nuevo libro al inventario.

Este módulo implementa la interfaz para añadir un nuevo libro o aumentar
la cantidad de un libro existente. Permite buscar libros por ISBN utilizando
la API integrada, y completar los datos automáticamente o manualmente.
"""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QWidget, QMessageBox, QSizePolicy,
    QSpacerItem, QGraphicsBlurEffect # Añadido QGraphicsBlurEffect
)
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QBrush, QMouseEvent # Añadido QMouseEvent
from PySide6.QtCore import Qt, QPoint, Signal, QPropertyAnimation, QEasingCurve, Property, QTimer
from typing import Dict, Any, List # Añadido List

from gui.common.styles import BACKGROUND_IMAGE_PATH, COLORS, FONTS, STYLES #
from features.book_service import BookService #
from core.validator import Validator #

class CustomToggleSwitch(QWidget): #
    toggled = Signal(bool)

    def __init__(self, parent=None, discapacidad_color_on=QColor("#34C759"), discapacidad_color_off=QColor("#E9E9EA"), circulo_color=QColor("white")): #
        super().__init__(parent)
        self.setCheckable(True)
        self._checked = False
        self.setFixedHeight(22)
        self.setFixedWidth(40)

        self._discapacidad_color_on = discapacidad_color_on
        self._discapacidad_color_off = discapacidad_color_off
        self._circulo_color = circulo_color

        self._margen_circulo = 2
        self._radio_circulo = (self.height() - 2 * self._margen_circulo) / 2

        self._posicion_circulo_manual = self._get_posicion_calculada_circulo()

        self._posicion_circulo_anim = QPropertyAnimation(self, b"posicion_circulo_propiedad", self)
        self._posicion_circulo_anim.setDuration(150)
        self._posicion_circulo_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def isCheckable(self): #
        return True

    def setCheckable(self, checkable): #
        pass

    def isChecked(self): #
        return self._checked

    def setChecked(self, checked): #
        if self._checked != checked:
            self._checked = checked
            self._actualizar_animacion_circulo()
            self.toggled.emit(self._checked)
            self.update()

    def toggle(self): #
        self.setChecked(not self.isChecked())

    def mousePressEvent(self, event): #
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()
        super().mousePressEvent(event)

    def paintEvent(self, event): #
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        radio_fondo = rect.height() / 2
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

    def _actualizar_animacion_circulo(self): #
        self._posicion_circulo_anim.stop()
        start_x = getattr(self, '_posicion_circulo_manual', self._get_posicion_calculada_circulo())
        end_x = self._get_posicion_calculada_circulo()
        
        self._posicion_circulo_anim.setStartValue(start_x)
        self._posicion_circulo_anim.setEndValue(end_x)
        self._posicion_circulo_anim.start()

    def _get_posicion_calculada_circulo(self): #
        if not self.isChecked():
            return self._margen_circulo + self._radio_circulo
        else:
            return self.width() - self._margen_circulo - self._radio_circulo

    def _get_posicion_circulo_actual(self): #
        return self._get_posicion_calculada_circulo()

    def _set_posicion_circulo_propiedad(self, pos): #
        self._posicion_circulo_manual = pos
        self.update()

    def _get_posicion_circulo_propiedad(self): #
        return getattr(self, '_posicion_circulo_manual', self._get_posicion_calculada_circulo())

    posicion_circulo_propiedad = Property(float, _get_posicion_circulo_propiedad, _set_posicion_circulo_propiedad)


class AddBookDialog(QDialog): #
    def __init__(self, book_service: BookService, parent=None): #
        super().__init__(parent)
        self.setWindowTitle(" ") 
        # Flags para ventana sin bordes y fondo translúcido
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Para la funcionalidad de arrastre
        self._drag_pos = QPoint()
        self.title_bar_height = 50 # Altura aproximada de la barra de título para el arrastre

        self.font_family = FONTS["family"] #
        self.book_service = book_service #
        self.ultimo_isbn_procesado_con_enter = None
        self.ultimo_isbn_para_advertencia = None
        self.advertencia_isbn_mostrada_recientemente = False
        self.ultima_posicion_ingresada = None
        
        self.detail_widgets_container = None
        self.action_buttons_container = None
        
        project_root_for_bg = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        specific_background_path = os.path.join(project_root_for_bg, "app", "imagenes", "fondo_agregar.png")

        if os.path.exists(specific_background_path):
            self.background_image_path = specific_background_path
        else:
            print(f"Advertencia: No se encontró la imagen de fondo específica: {specific_background_path}. Usando fondo global.")
            self.background_image_path = BACKGROUND_IMAGE_PATH #
        
        self.background_pixmap = QPixmap(self.background_image_path)
        if self.background_pixmap.isNull():
            print(f"ADVERTENCIA MUY IMPORTANTE: No se pudo cargar la imagen de fondo desde: {self.background_image_path}")
            self.setStyleSheet(f"QDialog {{ background-color: {COLORS.get('background_medium', '#E0E0E0')}; }}") #
        
        self._blur_effect = None
        if self.parent():
            self._blur_effect = QGraphicsBlurEffect()
            self._blur_effect.setBlurRadius(15) # Ajusta el radio de desenfoque según sea necesario
            self._blur_effect.setEnabled(False) # Inicialmente deshabilitado
            # Asumimos que el padre (MainWindow) tiene un widget central al que aplicar el blur
            # Si la estructura es diferente, esto necesitará ajustarse
            if hasattr(self.parent(), 'centralWidget') and self.parent().centralWidget():
                 self.parent().centralWidget().setGraphicsEffect(self._blur_effect)
            elif hasattr(self.parent(), 'current_stacked_widget') and self.parent().current_stacked_widget: # Compatibilidad con tu posible MainApp
                 self.parent().current_stacked_widget.setGraphicsEffect(self._blur_effect)
            else: # Fallback: aplicar al padre directamente si no se encuentra un widget central específico
                # Esto podría no ser ideal si el padre tiene otros diálogos o elementos.
                # self.parent().setGraphicsEffect(self._blur_effect)
                print("Advertencia: No se pudo encontrar un widget central en el padre para aplicar el desenfoque.")
        
        self._setup_ui()

    def _enable_blur(self, enable: bool):
        if not self.parent() or not self._blur_effect:
            return

        target_widget = None
        if hasattr(self.parent(), 'centralWidget') and self.parent().centralWidget():
            target_widget = self.parent().centralWidget()
        elif hasattr(self.parent(), 'current_stacked_widget') and self.parent().current_stacked_widget:
            target_widget = self.parent().current_stacked_widget

        if not target_widget:
            return

        if enable:
            # Apply only if not already set or set by someone else
            if target_widget.graphicsEffect() != self._blur_effect:
                target_widget.setGraphicsEffect(self._blur_effect)
            self._blur_effect.setEnabled(True)
        else:
            # Only disable and remove if our effect is currently active
            if target_widget.graphicsEffect() == self._blur_effect:
                self._blur_effect.setEnabled(False) # Disable it first
                target_widget.setGraphicsEffect(None) # Then remove it
        
        target_widget.update()

    def exec(self): # Sobrescribir exec para manejar el desenfoque
        if self.parent():
            self._enable_blur(True)
        result = super().exec()
        # Check parent and blur_effect again, as parent might be closing
        if self.parent() and self._blur_effect:
            self._enable_blur(False)
        return result

    def open(self): # Sobrescribir open si se usa show() + event loop local
        if self.parent():
            self._enable_blur(True)
        super().open()
        # Nota: si se usa show() y no se bloquea, el desenfoque se quitaría al instante.
        # Se necesita manejar la eliminación del desenfoque cuando el diálogo se cierre de verdad.

    def accept(self): # Sobrescribir para quitar el desenfoque
        # Check parent and blur_effect again
        if self.parent() and self._blur_effect:
            self._enable_blur(False)
        super().accept()

    def reject(self): # Sobrescribir para quitar el desenfoque
        # Check parent and blur_effect again
        if self.parent() and self._blur_effect:
            self._enable_blur(False)
        super().reject()
    
    def closeEvent(self, event): # Asegurar que el desenfoque se quite al cerrar
        # Check parent and blur_effect again
        if self.parent() and self._blur_effect:
            self._enable_blur(False)
        super().closeEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and event.pos().y() < self.title_bar_height:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = QPoint()
        event.accept()

    def _setup_ui(self): #
        main_dialog_layout = QVBoxLayout(self)
        main_dialog_layout.setContentsMargins(10, 10, 10, 10)
        main_dialog_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.unified_form_frame = QFrame()
        self.unified_form_frame.setObjectName("unifiedFormFrame")
        label_text_color = COLORS.get('text_primary', '#202427') #
        sub_label_text_color = COLORS.get('text_secondary', '#454545') #

        self.unified_form_frame.setStyleSheet(f"""
            QFrame#unifiedFormFrame {{
                background-color: {COLORS.get('background_light', 'rgba(255, 255, 255, 0.8)')}; /* */
                border-radius: 18px;
                border: 1px solid {COLORS.get('border_light', 'rgba(200, 200, 200, 0.6)')}; /* */
                padding: 20px;
            }}
            QLabel#dialogTitleLabel {{
                color: {label_text_color};
                background-color: transparent;
                font-size: {FONTS.get('size_xlarge', 20)}px; /* */
                font-weight: bold;
                padding-bottom: 0px; 
            }}
            QLabel.fieldLabel {{
                color: {label_text_color};
                background-color: transparent;
                font-size: {FONTS.get('size_normal', 11)}px; /* */
                padding-bottom: 3px;
                font-weight: bold;
            }}
            QLabel#toggleLabel {{
                color: {sub_label_text_color};
                background-color: transparent;
                font-size: {FONTS.get('size_small', 10)}px; /* */
            }}
            QLineEdit {{
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid {COLORS.get('border_medium', 'rgba(190, 190, 190, 150)')}; /* */
                font-size: {FONTS.get('size_normal', 11)}px; /* */
                min-height: 36px;
                border-radius: 6px;
                padding-left: 8px; padding-right: 8px;
            }}
            QLineEdit:disabled {{
                background-color: rgba(230, 230, 230, 0.8);
                color: {COLORS.get('text_disabled', '#909090')}; /* */
            }}
            QLineEdit:focus {{
                border: 1.5px solid {COLORS.get('border_focus', '#0078D7')}; /* */
            }}
        """)
        self.unified_form_frame.setFixedWidth(440)

        self.frame_layout = QVBoxLayout(self.unified_form_frame)
        self.frame_layout.setSpacing(10) 
        self.frame_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        title_toggle_row_layout = QHBoxLayout()
        
        self.title_label_internal = QLabel("Agregar Libro")
        self.title_label_internal.setObjectName("dialogTitleLabel")
        title_toggle_row_layout.addWidget(self.title_label_internal)

        title_toggle_row_layout.addStretch(1)

        self.cerrar_label_toggle = QLabel("Cerrar al guardar:")
        self.cerrar_label_toggle.setObjectName("toggleLabel")
        self.cerrar_label_toggle.setStyleSheet(f"color: {sub_label_text_color}; margin-right: 5px;")
        title_toggle_row_layout.addWidget(self.cerrar_label_toggle)

        self.cerrar_al_terminar_toggle = CustomToggleSwitch(
            discapacidad_color_on=QColor(COLORS.get('accent_green', '#2ECC71')), #
            discapacidad_color_off=QColor(COLORS.get('gray_medium', '#D3D3D3')) #
        )
        self.cerrar_al_terminar_toggle.setChecked(True)
        title_toggle_row_layout.addWidget(self.cerrar_al_terminar_toggle)
        self.frame_layout.addLayout(title_toggle_row_layout)

        # Añadir un espaciador vertical después de la fila del título del diálogo
        self.frame_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))
        
        isbn_label = QLabel("ISBN:")
        isbn_label.setObjectName("fieldLabel")
        self.isbn_input = QLineEdit()
        self.isbn_input.setPlaceholderText("Ingresar ISBN y presionar Enter")
        self.isbn_input.returnPressed.connect(self.buscar_isbn)
        self.frame_layout.addWidget(isbn_label) # Directamente al frame_layout
        self.frame_layout.addWidget(self.isbn_input) # Directamente al frame_layout

        self.detail_widgets_container = QWidget()
        details_layout = QVBoxLayout(self.detail_widgets_container)
        details_layout.setContentsMargins(0, 10, 0, 0) # Revertido el margen superior a 10
        details_layout.setSpacing(8)

        def create_field_widget(label_text: str, placeholder_text: str, return_pressed_lambda=None) -> (QWidget, QLineEdit):
            field_container = QWidget()
            field_layout = QVBoxLayout(field_container)
            field_layout.setContentsMargins(0,0,0,0)
            field_layout.setSpacing(1) 

            label = QLabel(label_text)
            label.setObjectName("fieldLabel")
            
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(placeholder_text)
            if return_pressed_lambda:
                line_edit.returnPressed.connect(return_pressed_lambda)
            
            field_layout.addWidget(label)
            field_layout.addWidget(line_edit)
            return field_container, line_edit

        title_widget, self.titulo_input = create_field_widget("Título:", "Título del libro", lambda: self._focus_next_input(self.autor_input))
        # self.titulo_input.setReadOnly(True) # Inicialmente NO ReadOnly
        
        author_widget, self.autor_input = create_field_widget("Autor:", "Autor(es) del libro", lambda: self._focus_next_input(self.editorial_input))
        # self.autor_input.setReadOnly(True) # Inicialmente NO ReadOnly

        editorial_widget, self.editorial_input = create_field_widget("Editorial:", "Editorial", lambda: self._focus_next_input(self.categorias_input))
        # self.editorial_input.setReadOnly(True) # Inicialmente NO ReadOnly

        categories_widget, self.categorias_input = create_field_widget("Categoría(s):", "Categorías (separadas por coma)", lambda: self._focus_next_input(self.precio_input))
        # self.categorias_input.setReadOnly(True) # Inicialmente NO ReadOnly

        price_widget, self.precio_input = create_field_widget("Precio:", "Precio (ej: 15000)", lambda: self._focus_next_input(self.posicion_input))
        # self.precio_input.setReadOnly(True) # Inicialmente NO ReadOnly
        self.precio_input.editingFinished.connect(self._formatear_texto_precio)

        position_widget, self.posicion_input = create_field_widget("Posición:", "Ubicación física (ej: 01A)", self.guardar_libro_on_enter)
        # self.posicion_input.setReadOnly(True) # Inicialmente NO ReadOnly
        
        image_url_widget, self.imagen_input = create_field_widget("URL Imagen:", "URL de la imagen (opcional)")
        # self.imagen_input.setReadOnly(True) # Inicialmente NO ReadOnly
        image_url_widget.setParent(self) # Asignar padre para evitar recolección prematura
        image_url_widget.setVisible(False) # Ocultar explícitamente el widget

        row1_layout = QHBoxLayout()
        row1_layout.addWidget(title_widget)
        row1_layout.addWidget(author_widget)
        details_layout.addLayout(row1_layout)

        row2_layout = QHBoxLayout()
        row2_layout.addWidget(editorial_widget)
        row2_layout.addWidget(categories_widget)
        details_layout.addLayout(row2_layout)

        row3_layout = QHBoxLayout()
        row3_layout.addWidget(price_widget)
        row3_layout.addWidget(position_widget)
        details_layout.addLayout(row3_layout)

        self.frame_layout.addWidget(self.detail_widgets_container)
        self.detail_widgets_container.setVisible(False)

        self.action_buttons_container = QWidget()
        button_layout = QHBoxLayout(self.action_buttons_container) # Asignar layout directamente
        button_layout.setContentsMargins(0, 15, 0, 0)
        button_layout.setSpacing(10)

        self.cancelar_button = QPushButton("Cancelar")
        self.cancelar_button.setFixedHeight(38)
        self.cancelar_button.setFont(QFont(self.font_family, FONTS.get("size_normal", 11))) #
        self.cancelar_button.setStyleSheet(STYLES.get("button_danger_full", "").replace("border-radius: 5px", "border-radius: 6px")) #
        self.cancelar_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancelar_button.clicked.connect(self.reject)
        self.cancelar_button.setAutoDefault(False) # Prevent becoming auto-default
        
        self.guardar_button = QPushButton("Guardar")
        self.guardar_button.setEnabled(False)
        self.guardar_button.setFixedHeight(38)
        self.guardar_button.setFont(QFont(self.font_family, FONTS.get("size_normal", 11), QFont.Weight.Bold)) #
        self.guardar_button.setAutoDefault(False) # Prevent becoming auto-default
        self.guardar_button.clicked.connect(self.guardar_libro) # Connect to guardar_libro

        button_layout.addStretch(1) 
        button_layout.addWidget(self.cancelar_button) 
        button_layout.addWidget(self.guardar_button)
        button_layout.addStretch(1)

        self.frame_layout.addWidget(self.action_buttons_container)
        self.action_buttons_container.setVisible(False)

        main_dialog_layout.addStretch(1) # Stretch ANTES del frame principal para centrar
        main_dialog_layout.addWidget(self.unified_form_frame)
        main_dialog_layout.addStretch(1) # Stretch DESPUÉS del frame principal para centrar

        self._actualizar_estilo_guardar_button()
        self.isbn_input.setFocus()
        self.adjustSize()

    def _show_details_and_actions(self): #
        if self.detail_widgets_container:
            self.detail_widgets_container.setVisible(True)
        if self.action_buttons_container:
            self.action_buttons_container.setVisible(True)
        self.setMinimumSize(480, 460) # Altura mínima reducida
        self.adjustSize()

    def _actualizar_estilo_guardar_button(self): #
        if self.guardar_button.isEnabled():
            style = STYLES.get("button_primary_full", "") #
            if "QPushButton {" in style:
                style = style.replace("border-radius: 5px;", "border-radius: 6px;")
                if "border-radius: 6px;" not in style:
                    style = style.replace("QPushButton {", "QPushButton { border-radius: 6px;")
            else: style += " border-radius: 6px;"
            self.guardar_button.setStyleSheet(style)
            self.guardar_button.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            disabled_style = STYLES.get("button_disabled", "") #
            if "QPushButton {" in disabled_style:
                if "border-radius: 5px;" in disabled_style: disabled_style = disabled_style.replace("border-radius: 5px;", "border-radius: 6px;")
                elif "border-radius" not in disabled_style: disabled_style = disabled_style.replace("QPushButton {", "QPushButton { border-radius: 6px;")
            else: disabled_style += " border-radius: 6px;"
            self.guardar_button.setStyleSheet(disabled_style)
            self.guardar_button.setCursor(Qt.CursorShape.ArrowCursor)
            
    def paintEvent(self, event): #
        # Comentado para permitir fondo transparente y ver el efecto glassmorphism del frame interno
        # painter = QPainter(self)
        # if not self.background_pixmap.isNull():
        #     scaled_pixmap = self.background_pixmap.scaled(
        #         self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        #     point = QPoint(0, 0)
        #     if scaled_pixmap.width() > self.width(): point.setX(int((scaled_pixmap.width() - self.width()) / -2))
        #     if scaled_pixmap.height() > self.height(): point.setY(int((scaled_pixmap.height() - self.height()) / -2))
        #     painter.drawPixmap(point, scaled_pixmap)
        # else: 
        #     painter.fillRect(self.rect(), QColor(COLORS.get('background_medium', '#D1D1D1'))) #
        super().paintEvent(event) # Importante llamar al evento padre si se necesita para QDialog

    def _fill_form_fields(self, book_details: Dict[str, Any], make_editable: bool): #
        self.titulo_input.setText(book_details.get("Título", ""))
        self.autor_input.setText(book_details.get("Autor", ""))
        self.editorial_input.setText(book_details.get("Editorial", ""))
        self.imagen_input.setText(book_details.get("Imagen", "")) 
        self.categorias_input.setText(", ".join(book_details.get("Categorías", [])))
        precio_val = book_details.get("Precio", "")
        self.precio_input.setText(str(precio_val) if precio_val else "")
        if precio_val: self._formatear_texto_precio() 
        self.titulo_input.setReadOnly(not make_editable)
        self.autor_input.setReadOnly(not make_editable)
        self.editorial_input.setReadOnly(not make_editable)
        self.imagen_input.setReadOnly(not make_editable) 
        self.categorias_input.setReadOnly(not make_editable)
        self.precio_input.setReadOnly(not make_editable)
        self.posicion_input.setReadOnly(not make_editable) 
        if make_editable: self.guardar_button.setEnabled(True)
        self._actualizar_estilo_guardar_button()
        self._show_details_and_actions()

    def _clear_book_details_fields_and_disable_save(self): #
        self.titulo_input.clear(); self.titulo_input.setReadOnly(True)
        self.autor_input.clear(); self.autor_input.setReadOnly(True)
        self.editorial_input.clear(); self.editorial_input.setReadOnly(True)
        self.imagen_input.clear(); self.imagen_input.setReadOnly(True) 
        self.categorias_input.clear(); self.categorias_input.setReadOnly(True)
        self.precio_input.clear(); self.precio_input.setReadOnly(True)
        self.posicion_input.clear(); self.posicion_input.setReadOnly(True)
        self.guardar_button.setEnabled(False)
        self._actualizar_estilo_guardar_button()

    def _reset_for_next_book(self): #
        self.isbn_input.clear()
        self._clear_book_details_fields_and_disable_save() 

        if self.detail_widgets_container:
            self.detail_widgets_container.setVisible(False)
        if self.action_buttons_container:
            self.action_buttons_container.setVisible(False)
        
        self.setMinimumSize(480, 280) 
        self.adjustSize() 

        self.ultimo_isbn_procesado_con_enter = None
        self.isbn_input.setFocus()
        self.advertencia_isbn_mostrada_recientemente = True
        self.ultimo_isbn_para_advertencia = ""
        
        if hasattr(self, 'ultima_posicion_ingresada') and self.ultima_posicion_ingresada and \
           hasattr(self, 'cerrar_al_terminar_toggle') and not self.cerrar_al_terminar_toggle.isChecked():
            self.posicion_input.setText(self.ultima_posicion_ingresada) 
        else:
            self.posicion_input.clear() 

    def _focus_next_input(self, next_input_field: QLineEdit): #
        if next_input_field.isReadOnly():
            current_widget = self.focusWidget()
            if current_widget == self.isbn_input: 
                self.buscar_isbn()
                return

            ordered_inputs = [
                self.titulo_input, 
                self.autor_input, 
                self.editorial_input,
                self.categorias_input, 
                self.precio_input, 
                self.posicion_input,
                self.imagen_input 
            ]
            try:
                if current_widget == self.isbn_input and self.detail_widgets_container.isVisible():
                    if not self.titulo_input.isReadOnly():
                        self.titulo_input.setFocus(); self.titulo_input.selectAll()
                        return
                
                current_index = ordered_inputs.index(current_widget)
                for i in range(current_index + 1, len(ordered_inputs)):
                    if not ordered_inputs[i].isReadOnly():
                        ordered_inputs[i].setFocus()
                        ordered_inputs[i].selectAll() 
                        return
                if self.guardar_button.isEnabled():
                     self.guardar_button.setFocus() 
                else:
                    for field in ordered_inputs: 
                        if not field.isReadOnly():
                            field.setFocus(); field.selectAll()
                            return
                    self.isbn_input.setFocus() 
            except ValueError: 
                if not self.titulo_input.isReadOnly(): 
                    self.titulo_input.setFocus(); self.titulo_input.selectAll()
                else:
                    self.isbn_input.setFocus() 
        else:
            next_input_field.setFocus()
            next_input_field.selectAll()

    def guardar_libro_on_enter(self): #
        if self.guardar_button.isEnabled(): self.guardar_libro()

    def buscar_isbn(self): #
        isbn_actual = self.isbn_input.text().strip()
        
        if self.advertencia_isbn_mostrada_recientemente:
            if (not isbn_actual and self.ultimo_isbn_para_advertencia == "") or \
               (isbn_actual and self.ultimo_isbn_para_advertencia is not None and isbn_actual == self.ultimo_isbn_para_advertencia):
                if not self.detail_widgets_container.isVisible(): self._show_details_and_actions()
                return 

        if not isbn_actual:
            QMessageBox.warning(self, "Error", "Por favor ingrese un ISBN.")
            self.isbn_input.setFocus()
            self.ultimo_isbn_para_advertencia = "" 
            self.advertencia_isbn_mostrada_recientemente = True
            return

        if not Validator.is_valid_isbn(isbn_actual): #
            QMessageBox.warning(self, "Error", "El ISBN ingresado no es válido.")
            self.isbn_input.selectAll(); self.isbn_input.setFocus()
            self.ultimo_isbn_para_advertencia = isbn_actual 
            self.advertencia_isbn_mostrada_recientemente = True
            return
            
        self.advertencia_isbn_mostrada_recientemente = False
        self.ultimo_isbn_para_advertencia = None

        if isbn_actual == self.ultimo_isbn_procesado_con_enter and \
           self.detail_widgets_container.isVisible() and \
           not self.titulo_input.isReadOnly():
             self._focus_next_input(self.titulo_input)
             return
            
        search_result = self.book_service.buscar_libro_por_isbn(isbn_actual) #
        status = search_result["status"]
        book_details = search_result["book_details"]
        inventory_entries = search_result["inventory_entries"]
        
        self.ultimo_isbn_procesado_con_enter = isbn_actual

        self._show_details_and_actions()

        if status == "encontrado_completo" and inventory_entries:
            first_entry = inventory_entries[0] 
            titulo = book_details.get("Título", "Desconocido")
            pos = first_entry["posicion"]
            precio_reg = first_entry["precio_venta_registrado"]
            precio_msg = f"{precio_reg:,}".replace(",", ".")
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Libro Existente")
            msg_box.setText(f'El libro "<b>{titulo}</b>" ya existe en la posición <b>{pos}</b> (Precio: ${precio_msg}).')
            msg_box.setInformativeText("¿Desea agregar otra unidad en esta posición o editar/agregar en otra parte?")
            msg_box.setIcon(QMessageBox.Icon.Question)
            btn_agregar_unidad = msg_box.addButton("Agregar Unidad Aquí", QMessageBox.ButtonRole.YesRole)
            btn_editar_o_nueva = msg_box.addButton("Editar/Nueva Posición", QMessageBox.ButtonRole.NoRole)
            msg_box.addButton(QMessageBox.StandardButton.Cancel)
            msg_box.exec() #
            if msg_box.clickedButton() == btn_agregar_unidad:
                success_inv, message_inv, cantidad_inv = self.book_service.guardar_libro_en_inventario(isbn_actual, pos) #
                if success_inv:
                    QMessageBox.information(self, "Éxito", f"Se incrementó la cantidad en la posición {pos}. Nueva cantidad: {cantidad_inv}")
                    if not self.cerrar_al_terminar_toggle.isChecked(): self.ultima_posicion_ingresada = pos; self._reset_for_next_book()
                    else: self.ultima_posicion_ingresada = None; self.accept()
                else: QMessageBox.warning(self, "Error", message_inv)
            elif msg_box.clickedButton() == btn_editar_o_nueva:
                self._fill_form_fields(book_details, make_editable=True) 
                self.posicion_input.setText(pos) 
                self.precio_input.setFocus(); self.precio_input.selectAll()
            else: self._reset_for_next_book() 
        elif status == "encontrado_en_libros":
            QMessageBox.information(self, "Información de Libro Encontrada", "Los detalles se encontraron. Ingrese precio y posición.")
            self._fill_form_fields(book_details, make_editable=True)
            self.precio_input.setFocus(); self.precio_input.selectAll()
        elif status == "solo_api":
            QMessageBox.information(self, "Información de Libro Obtenida", "Datos encontrados en línea. Verifique y complete.")
            self._fill_form_fields(book_details, make_editable=True)
            self.precio_input.setFocus(); self.precio_input.selectAll()
        elif status == "no_encontrado":
            msg_box_no_encontrado = QMessageBox(self)
            msg_box_no_encontrado.setWindowTitle("Libro no encontrado")
            msg_box_no_encontrado.setText("Ingrese los datos manualmente.")
            msg_box_no_encontrado.setIcon(QMessageBox.Icon.Information)
            # Aplicando estilos al QMessageBox
            msg_box_no_encontrado.setStyleSheet(f"""
                QMessageBox {{
                    background-color: {COLORS.get('background_light', 'rgba(255, 255, 255, 0.9)')};
                    border: 1px solid {COLORS.get('border_light', 'rgba(200, 200, 200, 0.6)')};
                    border-radius: 10px;
                }}
                QLabel {{
                    color: {COLORS.get('text_primary', '#202427')};
                    background-color: transparent;
                    font-size: {FONTS.get('size_normal', 11)}px;
                    /* min-width: 250px; */ /* Eliminado para evitar exceso de espacio */
                }}
                QPushButton {{
                    background-color: {COLORS.get('accent_blue', '#007AFF')};
                    color: white;
                    border-radius: 5px;
                    padding: 6px 12px; /* Ajuste de padding */
                    font-size: {FONTS.get('size_normal', 11)}px;
                    min-height: 28px; /* Altura mínima consistente con otros botones */
                    min-width: 80px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS.get('accent_blue_hover', '#0056b3')};
                }}
                QPushButton:pressed {{
                    background-color: {COLORS.get('accent_blue_pressed', '#004080')}; /* Estilo para presionado */
                }}
            """)
            msg_box_no_encontrado.exec()

            posicion_actual_antes_de_manual = self.posicion_input.text()
            self._clear_book_details_fields_and_disable_save() 
            self._fill_form_fields({}, make_editable=True) 
            
            # Asegurar explícitamente que los campos sean editables
            self.titulo_input.setReadOnly(False)
            self.autor_input.setReadOnly(False)
            self.editorial_input.setReadOnly(False)
            self.categorias_input.setReadOnly(False)
            self.precio_input.setReadOnly(False)
            self.posicion_input.setReadOnly(False) # Ya estaba, pero se mantiene por consistencia
            self.imagen_input.setReadOnly(False) # Aunque oculto, mantenemos su estado lógico

            self.posicion_input.setText(posicion_actual_antes_de_manual)
            
            QTimer.singleShot(0, self.titulo_input.setFocus)
            QTimer.singleShot(0, self.titulo_input.selectAll)
        
        if not self.precio_input.isReadOnly() and not self.posicion_input.isReadOnly():
            self.guardar_button.setEnabled(True)
        self._actualizar_estilo_guardar_button()

    def _limpiar_valor_precio(self, texto_con_formato: str) -> str: #
        return texto_con_formato.replace(".", "")

    def _formatear_texto_precio(self): #
        current_text_limpio = self._limpiar_valor_precio(self.precio_input.text())
        if not current_text_limpio.isdigit(): return
        try:
            valor_numerico = int(current_text_limpio)
            texto_formateado = f"{valor_numerico:,}".replace(",", ".")
            self.precio_input.setText(texto_formateado)
        except ValueError: pass

    def guardar_libro(self): #
        if not self.titulo_input.text().strip():
            QMessageBox.warning(self, "Error", "El título es obligatorio."); self.titulo_input.setFocus(); return
        try:
            precio_texto_limpio = self._limpiar_valor_precio(self.precio_input.text())
            if not precio_texto_limpio:
                QMessageBox.warning(self, "Error", "El precio es obligatorio."); self.precio_input.setFocus(); return
            try: precio = int(precio_texto_limpio)
            except ValueError:
                QMessageBox.warning(self, "Error", "El precio debe ser un número entero válido."); self.precio_input.setFocus(); self.precio_input.selectAll(); return
            if precio < 1000:
                QMessageBox.warning(self, "Error", "El precio debe ser igual o mayor a 1000."); self.precio_input.setFocus(); self.precio_input.selectAll(); return
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error en el precio: {str(e)}"); self.precio_input.setFocus(); return
        if not self.posicion_input.text().strip():
            QMessageBox.warning(self, "Error", "La posición es obligatoria."); self.posicion_input.setFocus(); return
        posicion = self.posicion_input.text().strip().upper()
        if posicion not in self.book_service.posiciones_validas: #
            QMessageBox.warning(self, "Error", f"Posición '{posicion}' no válida. Formato: 01A-99J"); self.posicion_input.setFocus(); return
        try:
            isbn = self.isbn_input.text().strip()
            book_info = { "ISBN": isbn, "Título": self.titulo_input.text().strip(), "Autor": self.autor_input.text().strip(), "Editorial": self.editorial_input.text().strip(), "Imagen": self.imagen_input.text().strip(), "Categorías": [cat.strip() for cat in self.categorias_input.text().split(",") if cat.strip()], "Precio": precio, "Posición": posicion }
            success_book_db, message_book_db = self.book_service.guardar_libro(book_info) #
            if not success_book_db: QMessageBox.critical(self, "Error", message_book_db); return
            success_inv, message_inv, cantidad_inv = self.book_service.guardar_libro_en_inventario(isbn, posicion) #
            if success_inv:
                msg_success = f"Cantidad incrementada en {posicion}. Nueva cantidad: {cantidad_inv}" if cantidad_inv > 1 else "Libro agregado correctamente al inventario."
                QMessageBox.information(self, "Éxito", msg_success)
                if not self.cerrar_al_terminar_toggle.isChecked(): self.ultima_posicion_ingresada = posicion; self._reset_for_next_book()
                else: self.ultima_posicion_ingresada = None; self.accept()
            else: QMessageBox.warning(self, "Error en Inventario", message_inv)
        except Exception as e: QMessageBox.critical(self, "Error", f"Error al guardar el libro: {str(e)}")
    
    def resizeEvent(self, event): #
        self.update()
        super().resizeEvent(event)