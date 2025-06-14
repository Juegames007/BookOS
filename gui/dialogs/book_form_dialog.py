"""
Diálogo base reutilizable para formularios de libros.

Este módulo implementa una interfaz genérica para agregar o modificar libros.
Funciona en diferentes modos ('ADD', 'MODIFY') para adaptar su título y comportamiento.
Contiene la UI completa y la lógica de interacción del formulario.
"""

import platform
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame, QWidget, QMessageBox, QSizePolicy,
    QSpacerItem, QGraphicsBlurEffect
)
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor, QBrush, QMouseEvent
from PySide6.QtCore import Qt, QPoint, Signal, QTimer, Property, QEasingCurve, QPropertyAnimation
from typing import Dict, Any, Optional

from gui.common.styles import COLORS, FONTS, STYLES
from features.book_service import BookService
from core.validator import Validator

class CustomToggleSwitch(QWidget):
    """Un widget de interruptor (toggle switch) personalizado."""
    toggled = Signal(bool)

    def __init__(self, parent=None, discapacidad_color_on=QColor("#34C759"), discapacidad_color_off=QColor("#E9E9EA"), circulo_color=QColor("white")):
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

    def isCheckable(self): return True
    def setCheckable(self, checkable): pass
    def isChecked(self): return self._checked
    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self._actualizar_animacion_circulo()
            self.toggled.emit(self._checked)
            self.update()
    def toggle(self): self.setChecked(not self.isChecked())
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton: self.toggle()
        super().mousePressEvent(event)
    def paintEvent(self, event):
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect(); radio_fondo = rect.height() / 2
        posicion_circulo_actual_para_pintar = getattr(self, '_posicion_circulo_manual', self._get_posicion_calculada_circulo())
        painter.setBrush(QBrush(self._discapacidad_color_on if self.isChecked() else self._discapacidad_color_off))
        painter.setPen(Qt.PenStyle.NoPen); painter.drawRoundedRect(rect, radio_fondo, radio_fondo)
        painter.setBrush(QBrush(self._circulo_color)); painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPoint(int(posicion_circulo_actual_para_pintar), int(rect.center().y())), int(self._radio_circulo), int(self._radio_circulo))
    def _actualizar_animacion_circulo(self):
        self._posicion_circulo_anim.stop()
        self._posicion_circulo_anim.setStartValue(getattr(self, '_posicion_circulo_manual', self._get_posicion_calculada_circulo()))
        self._posicion_circulo_anim.setEndValue(self._get_posicion_calculada_circulo()); self._posicion_circulo_anim.start()
    def _get_posicion_calculada_circulo(self): return self.width() - self._margen_circulo - self._radio_circulo if self.isChecked() else self._margen_circulo + self._radio_circulo
    def _set_posicion_circulo_propiedad(self, pos): self._posicion_circulo_manual = pos; self.update()
    def _get_posicion_circulo_propiedad(self): return getattr(self, '_posicion_circulo_manual', self._get_posicion_calculada_circulo())
    posicion_circulo_propiedad = Property(float, _get_posicion_circulo_propiedad, _set_posicion_circulo_propiedad)

class BookFormDialog(QDialog):
    save_requested = Signal(dict)

    def __init__(self, book_service: BookService, mode: str = 'ADD', initial_isbn: Optional[str] = None, parent=None, blur_effect=None):
        super().__init__(parent)
        self.book_service = book_service
        self.mode = mode.upper()
        self.initial_isbn = initial_isbn
        self.setWindowTitle(" ")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.font_family = FONTS["family"]
        self._drag_pos = QPoint()
        self.title_bar_height = 50
        self.ultimo_isbn_procesado_con_enter = None
        self.ultima_posicion_ingresada = None
        self.original_book_data: Optional[Dict[str, Any]] = None
        self.detail_widgets_container = None
        self.action_buttons_container = None
        
        self._blur_effect = blur_effect
        if self._blur_effect:
            self._blur_effect.setEnabled(False)
        
        self._setup_ui()
        self._configure_for_mode()
        self._actualizar_estilo_guardar_button()
        self._initial_load()

    def _setup_ui(self):
        self.animation = QPropertyAnimation(self, b"maximumHeight")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        main_dialog_layout = QVBoxLayout(self)
        main_dialog_layout.setContentsMargins(0, 0, 0, 0)
        main_dialog_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.unified_form_frame = QFrame()
        self.unified_form_frame.setObjectName("unifiedFormFrame")
        label_text_color = COLORS.get('text_primary', '#202427')
        sub_label_text_color = COLORS.get('text_secondary', '#454545')

        self.unified_form_frame.setStyleSheet(f"""
            QFrame#unifiedFormFrame {{
                background-color: {COLORS.get('background_light', 'rgba(255, 255, 255, 0.8)')} !important;
                border-radius: 16px !important;
                border: 0.5px solid white !important;
                padding: 20px;
            }}
            QLabel#dialogTitleLabel {{
                color: {label_text_color} !important;
                background: transparent !important;
                font-size: {FONTS.get('size_xlarge', 20)}px;
                font-weight: bold;
                padding-bottom: 0px;
            }}
            QLabel.fieldLabel {{
                color: {label_text_color} !important;
                background: transparent !important;
                font-size: {FONTS.get('size_normal', 11)}px;
                padding-bottom: 3px;
                font-weight: bold;
            }}
            QLabel#toggleLabel {{
                color: {sub_label_text_color} !important;
                background: transparent !important;
                font-size: {FONTS.get('size_small', 10)}px;
            }}
            QLineEdit {{
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid {COLORS.get('border_medium', 'rgba(190, 190, 190, 150)')};
                font-size: {FONTS.get('size_normal', 11)}px;
                min-height: 36px;
                border-radius: 6px;
                padding-left: 8px; padding-right: 8px;
                color: {COLORS.get('text_primary', "#1F2224")};
            }}
            QLineEdit::placeholder {{
                color: {COLORS.get('text_placeholder', '#A0A0A0')};
            }}
            QLineEdit:disabled {{
                background-color: rgba(230, 230, 230, 0.8);
                color: {COLORS.get('text_disabled', '#909090')};
            }}
            QLineEdit:focus {{
                border: 1.5px solid {COLORS.get('border_focus', '#0078D7')};
            }}
        """)
        self.unified_form_frame.setFixedWidth(440)
        self.frame_layout = QVBoxLayout(self.unified_form_frame)
        self.frame_layout.setSpacing(10)
        self.frame_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        title_toggle_row_layout = QHBoxLayout()
        self.title_label_internal = QLabel("Formulario Libro")
        self.title_label_internal.setObjectName("dialogTitleLabel")
        title_toggle_row_layout.addWidget(self.title_label_internal)
        title_toggle_row_layout.addStretch(1)
        self.cerrar_label_toggle = QLabel("Cerrar al guardar:")
        self.cerrar_label_toggle.setObjectName("toggleLabel")
        title_toggle_row_layout.addWidget(self.cerrar_label_toggle)
        self.cerrar_al_terminar_toggle = CustomToggleSwitch(
            discapacidad_color_on=QColor(COLORS.get('accent_green', '#2ECC71')),
            discapacidad_color_off=QColor(COLORS.get('gray_medium', '#D3D3D3'))
        )
        self.cerrar_al_terminar_toggle.setChecked(True)
        title_toggle_row_layout.addWidget(self.cerrar_al_terminar_toggle)
        self.frame_layout.addLayout(title_toggle_row_layout)
        self.frame_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        isbn_label = QLabel("ISBN:"); isbn_label.setObjectName("fieldLabel")
        palette_isbn = isbn_label.palette()
        palette_isbn.setColor(isbn_label.foregroundRole(), QColor(COLORS.get('text_primary', '#202427')))
        isbn_label.setPalette(palette_isbn)
        self.isbn_input = QLineEdit(); self.isbn_input.setPlaceholderText("Ingresar ISBN y presionar Enter")
        self.isbn_input.returnPressed.connect(self.buscar_isbn)
        self.frame_layout.addWidget(isbn_label)
        self.frame_layout.addWidget(self.isbn_input)
        
        self.detail_widgets_container = QWidget()
        details_layout = QVBoxLayout(self.detail_widgets_container)
        details_layout.setContentsMargins(0, 10, 0, 0); details_layout.setSpacing(8)

        def create_field(label, placeholder, on_enter=None):
            w = QWidget(); l = QVBoxLayout(w); l.setContentsMargins(0,0,0,0); l.setSpacing(1)
            lbl = QLabel(label); lbl.setObjectName("fieldLabel")
            palette_lbl = lbl.palette()
            palette_lbl.setColor(lbl.foregroundRole(), QColor(COLORS.get('text_primary', '#202427')))
            lbl.setPalette(palette_lbl)
            inp = QLineEdit(); inp.setPlaceholderText(placeholder)
            if on_enter: inp.returnPressed.connect(on_enter)
            l.addWidget(lbl); l.addWidget(inp)
            return w, inp
        
        title_w, self.titulo_input = create_field("Título:", "Título del libro", lambda: self.autor_input.setFocus())
        author_w, self.autor_input = create_field("Autor:", "Autor(es) del libro", lambda: self.editorial_input.setFocus())
        editorial_w, self.editorial_input = create_field("Editorial:", "Editorial", lambda: self.categorias_input.setFocus())
        categories_w, self.categorias_input = create_field("Categoría(s):", "Categorías (separadas por coma)", lambda: self.precio_input.setFocus())
        price_w, self.precio_input = create_field("Precio:", "Precio (ej: 15000)", lambda: self.posicion_input.setFocus())
        self.precio_input.editingFinished.connect(self._formatear_texto_precio)
        position_w, self.posicion_input = create_field("Posición:", "Ubicación física (ej: 01A)", self.guardar_libro)
        image_url_w, self.imagen_input = create_field("URL Imagen:", "URL de la imagen (opcional)")
        
        row1 = QHBoxLayout(); row1.addWidget(title_w); row1.addWidget(author_w)
        row2 = QHBoxLayout(); row2.addWidget(editorial_w); row2.addWidget(categories_w)
        row3 = QHBoxLayout(); row3.addWidget(price_w); row3.addWidget(position_w)
        details_layout.addLayout(row1); details_layout.addLayout(row2); details_layout.addLayout(row3)
        details_layout.addWidget(image_url_w)
        image_url_w.setVisible(False)

        self.frame_layout.addWidget(self.detail_widgets_container)
        self.detail_widgets_container.setVisible(False)
        
        self.action_buttons_container = QWidget()
        button_layout = QHBoxLayout(self.action_buttons_container)
        button_layout.setContentsMargins(0, 15, 0, 0); button_layout.setSpacing(10)
        
        self.cancelar_button = QPushButton("Cancelar")
        self.cancelar_button.setFixedHeight(38)
        self.cancelar_button.setStyleSheet(STYLES.get("button_danger_full", "").replace("border-radius: 5px", "border-radius: 6px"))
        self.cancelar_button.clicked.connect(self.reject)
        self.cancelar_button.setAutoDefault(False)
        
        self.guardar_button = QPushButton("Guardar")
        self.guardar_button.setFixedHeight(38)
        self.guardar_button.clicked.connect(self.guardar_libro)
        self.guardar_button.setAutoDefault(False)

        button_layout.addStretch(1)
        button_layout.addWidget(self.cancelar_button)
        button_layout.addWidget(self.guardar_button)
        button_layout.addStretch(1)
        
        self.frame_layout.addWidget(self.action_buttons_container)
        self.action_buttons_container.setVisible(False)

        main_dialog_layout.addStretch(1)
        main_dialog_layout.addWidget(self.unified_form_frame)
        main_dialog_layout.addStretch(1)
        
        self.setLayout(main_dialog_layout)

    def _initial_load(self):
        """Carga inicial de datos si se proporciona un ISBN."""
        if self.initial_isbn:
            self.isbn_input.setText(self.initial_isbn)
            self.buscar_isbn()
        else:
            self.adjustSize()
            self._recenter()
            self.isbn_input.setFocus()

    def _recenter(self):
        """Centra el diálogo en la ventana principal."""
        if self.parent():
            parent_geom = self.parent().geometry()
            self.move(parent_geom.x() + (parent_geom.width() - self.width()) // 2,
                      parent_geom.y() + (parent_geom.height() - self.height()) // 2)

    def _configure_for_mode(self):
        if self.mode == 'ADD':
            self.title_label_internal.setText("Agregar")
            self.guardar_button.setText("Guardar")
        elif self.mode == 'MODIFY':
            self.title_label_internal.setText("Modificar")
            self.guardar_button.setText("Actualizar")

    def buscar_isbn(self):
        isbn = self.isbn_input.text().strip()
        if not Validator.is_valid_isbn(isbn):
            QMessageBox.warning(self, "Error de Validación", "El ISBN ingresado no es válido.")
            return
        search_result = self.book_service.buscar_libro_por_isbn(isbn)
        status = search_result["status"]
        book_details = search_result.get("book_details")

        if status in ["encontrado_completo", "encontrado_en_libros"]:
            self.original_book_data = book_details
        else:
            self.original_book_data = None
            
        if self.mode == 'MODIFY' and status in ['no_encontrado', 'solo_api']:
            QMessageBox.critical(self, "Error", f"El libro con ISBN '{isbn}' debe existir en la base de datos local para poder modificarlo.")
            self._reset_for_next_book()
            return
        self.ultimo_isbn_procesado_con_enter = isbn
        
        if status in ["encontrado_completo", "encontrado_en_libros"]:
            titulo_libro = book_details.get("Título", "Desconocido")
            if self.mode == 'ADD':
                pos = search_result.get("inventory_entries", [{}])[0].get("posicion", "N/A")
                msg_box = QMessageBox(self); msg_box.setWindowTitle("Libro Existente")
                msg_box.setText(f'El libro "<b>{titulo_libro}</b>" ya existe.'); msg_box.setInformativeText("¿Qué deseas hacer?")
                msg_box.setIcon(QMessageBox.Icon.Question)
                btn_agregar_unidad = msg_box.addButton("Aumentar Unidad", QMessageBox.ButtonRole.YesRole)
                btn_editar_o_nueva = msg_box.addButton("Editar/Nueva Posición", QMessageBox.ButtonRole.NoRole)
                msg_box.addButton(QMessageBox.StandardButton.Cancel); msg_box.exec()
                clicked_button = msg_box.clickedButton()
                if clicked_button == btn_agregar_unidad:
                    success, _, cantidad = self.book_service.guardar_libro_en_inventario(isbn, pos)
                    if success:
                        QMessageBox.information(self, "Éxito", f"Se incrementó la cantidad en la posición {pos}. Nueva cantidad: {cantidad}")
                        if self.cerrar_al_terminar_toggle.isChecked(): self.accept()
                        else: self._reset_for_next_book()
                    else: QMessageBox.warning(self, "Error", "No se pudo incrementar la cantidad.")
                elif clicked_button == btn_editar_o_nueva:
                    self._fill_form_fields(book_details, make_editable=True)
                    self.posicion_input.setText(pos)
                    self.titulo_input.setFocus()
                else: self._reset_for_next_book()
            elif self.mode == 'MODIFY':
                self._fill_form_fields(book_details, make_editable=True)
                self.isbn_input.setReadOnly(True)
                self.titulo_input.setFocus()
        elif status == "solo_api":
            QMessageBox.information(self, "Información de Libro Obtenida", "Datos encontrados en línea. Por favor, verifique y complete la información.")
            self._fill_form_fields(book_details, make_editable=True)
            self.precio_input.setFocus()
        elif status == "no_encontrado":
            if self.mode == 'MODIFY':
                QMessageBox.critical(self, "Error", f"No se encontró el libro con ISBN {isbn} para modificar.")
                self._reset_for_next_book()
            else:
                QMessageBox.information(self, "Libro no Encontrado", "Por favor, ingrese los datos manualmente.")
                self._fill_form_fields({}, make_editable=True)
                self.titulo_input.setFocus()

    def guardar_libro(self):
        titulo = self.titulo_input.text().strip()
        posicion = self.posicion_input.text().strip().upper()
        precio_limpio = self._limpiar_valor_precio(self.precio_input.text())
        if not all([titulo, posicion, precio_limpio]):
            QMessageBox.warning(self, "Campos Incompletos", "Título, Precio y Posición son obligatorios."); return
        if int(precio_limpio) < 1000:
             QMessageBox.warning(self, "Error", "El precio debe ser igual o mayor a 1000."); self.precio_input.setFocus(); self.precio_input.selectAll(); return
        if posicion not in self.book_service.posiciones_validas:
            QMessageBox.warning(self, "Dato Inválido", f"La posición '{posicion}' no es válida. Use el formato 01A-99J."); return
        book_data = {
            "ISBN": self.isbn_input.text().strip(), "Título": titulo, "Autor": self.autor_input.text().strip(),
            "Editorial": self.editorial_input.text().strip(), "Imagen": self.imagen_input.text().strip(),
            "Categorías": [cat.strip() for cat in self.categorias_input.text().split(",") if cat.strip()],
            "Precio": int(precio_limpio), "Posición": posicion
        }
        self.save_requested.emit(book_data)

    def _enable_blur(self, enable: bool):
        if self._blur_effect:
            self._blur_effect.setEnabled(enable)

    def exec(self):
        self._enable_blur(True)
        self.adjustSize()
        self._recenter()
        result = super().exec()
        self._enable_blur(False)
        return result
    
    def reject(self):
        self._enable_blur(False)
        super().reject()
    
    def closeEvent(self, event):
        self._enable_blur(False)
        super().closeEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and event.pos().y() < self.title_bar_height:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft(); event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos); event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = QPoint(); event.accept()

    def _fill_form_fields(self, details, make_editable):
        self.titulo_input.setText(details.get("Título", "")); self.titulo_input.setReadOnly(not make_editable)
        self.autor_input.setText(details.get("Autor", "")); self.autor_input.setReadOnly(not make_editable)
        self.editorial_input.setText(details.get("Editorial", "")); self.editorial_input.setReadOnly(not make_editable)
        self.categorias_input.setText(", ".join(details.get("Categorías", []))); self.categorias_input.setReadOnly(not make_editable)
        precio = details.get("Precio", ""); self.precio_input.setText(str(precio)); self._formatear_texto_precio()
        self.precio_input.setReadOnly(not make_editable)
        self.posicion_input.setReadOnly(not make_editable)
        self.imagen_input.setText(details.get("Imagen", "")); self.imagen_input.setReadOnly(not make_editable)
        
        if not self.detail_widgets_container.isVisible():
            self.detail_widgets_container.setVisible(True)
            self.animation.setTargetObject(self.detail_widgets_container)
            self.animation.setStartValue(0)
            self.animation.setEndValue(self.detail_widgets_container.sizeHint().height())
            self.animation.start()
        
        self.action_buttons_container.setVisible(True)
        self.guardar_button.setEnabled(make_editable)
        self._actualizar_estilo_guardar_button()
        
        QTimer.singleShot(10, self.adjustSize)
        QTimer.singleShot(11, self._recenter)
        
    def _reset_for_next_book(self):
        for field in [self.titulo_input, self.autor_input, self.editorial_input, self.categorias_input, self.precio_input, self.posicion_input, self.imagen_input]:
            field.clear(); field.setReadOnly(True)
        self.isbn_input.clear(); self.isbn_input.setReadOnly(False)
        
        if self.detail_widgets_container.isVisible():
            self.detail_widgets_container.setVisible(False)
        self.action_buttons_container.setVisible(False)
        self.guardar_button.setEnabled(False)
        self._actualizar_estilo_guardar_button()
        
        QTimer.singleShot(10, self.adjustSize)
        QTimer.singleShot(11, self._recenter)
        self.isbn_input.setFocus()
    
    def _formatear_texto_precio(self):
        try:
            valor = int("".join(filter(str.isdigit, self.precio_input.text())))
            self.precio_input.setText(f"{valor:,}".replace(",", "."))
        except (ValueError, TypeError): pass

    def _limpiar_valor_precio(self, texto): return "".join(filter(str.isdigit, texto))
        
    def _actualizar_estilo_guardar_button(self):
        is_enabled = self.guardar_button.isEnabled()
        style_key = "button_primary_full" if is_enabled else "button_disabled"
        style = STYLES.get(style_key, "").replace("border-radius: 5px", "border-radius: 6px")
        self.guardar_button.setStyleSheet(style)
        self.guardar_button.setCursor(Qt.CursorShape.PointingHandCursor if is_enabled else Qt.CursorShape.ArrowCursor)