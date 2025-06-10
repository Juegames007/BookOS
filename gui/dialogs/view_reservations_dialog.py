import sys
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QDialog, QVBoxLayout, QStackedWidget, 
                             QPushButton, QWidget, QFrame, QLabel, QTableWidget,
                             QTableWidgetItem, QAbstractItemView, QHeaderView,
                             QGraphicsDropShadowEffect, QGroupBox, QFormLayout, 
                             QLineEdit, QTextEdit, QHBoxLayout, QMessageBox,
                             QSizePolicy)
from PySide6.QtCore import Qt, QPropertyAnimation, QRect, QPoint, QEasingCurve, Signal
from PySide6.QtGui import QColor, QDoubleValidator, QCursor

from gui.components.elided_label import ElidedLabel

class ViewReservationsDialog(QDialog):
    def __init__(self, reservation_service, parent=None):
        super().__init__(parent)
        self.reservation_service = reservation_service
        self.current_reservation_id = None
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowSystemMenuHint | Qt.WindowType.Popup)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("QDialog { background-color: transparent; }")

        self.setMinimumSize(900, 700)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Shadow effect
        self.shadow = QFrame(self)
        self.shadow.setObjectName("shadow")
        self.shadow.setFrameShape(QFrame.Shape.StyledPanel)
        self.shadow_effect = QGraphicsDropShadowEffect(self)
        self.shadow_effect.setBlurRadius(25)
        self.shadow_effect.setColor(QColor(0, 0, 0, 160))
        self.shadow_effect.setOffset(0, 0)
        self.shadow.setGraphicsEffect(self.shadow_effect)
        self.shadow.setStyleSheet("#shadow { background-color: #F5F5F5; border-radius: 15px; }")
        self.layout.addWidget(self.shadow)
        
        # Content layout within the shadow frame
        self.content_layout = QVBoxLayout(self.shadow)
        self.content_layout.setContentsMargins(25, 20, 25, 20)
        self.content_layout.setSpacing(15)

        # Top bar with close button
        top_bar_layout = QHBoxLayout()
        title_label = QLabel("Gestión de Reservas")
        title_label.setObjectName("dialogTitle")
        title_label.setStyleSheet("#dialogTitle { font-size: 20px; font-weight: bold; color: #333; }")
        
        close_button = QPushButton("✕")
        close_button.setObjectName("closeButton")
        close_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        close_button.setFixedSize(30, 30)
        close_button.setStyleSheet("""
            #closeButton {
                font-family: "Arial";
                font-size: 16px; 
                font-weight: bold;
                color: #888;
                background-color: #E0E0E0; 
                border-radius: 15px;
                border: none;
            }
            #closeButton:hover {
                background-color: #D54B4B;
                color: white;
            }
        """)
        close_button.clicked.connect(self.close)

        top_bar_layout.addWidget(title_label)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(close_button)

        self.content_layout.addLayout(top_bar_layout)

        # Stacked widget for switching between list and detail view
        self.stacked_widget = QStackedWidget(self)
        self.content_layout.addWidget(self.stacked_widget)

        # Create and add pages
        self.list_page = self.create_list_page()
        self.details_page = self.create_details_page()

        self.stacked_widget.addWidget(self.list_page)
        self.stacked_widget.addWidget(self.details_page)

        self.init_animations()

        # Load initial data
        self.load_reservations()

    def create_list_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        list_title = QLabel("Reservas Activas")
        list_title.setObjectName("title")
        list_title.setStyleSheet("#title { font-size: 22px; font-weight: bold; color: #333; margin-bottom: 5px; }")
        layout.addWidget(list_title)
        
        self.reservations_table = QTableWidget()
        self.reservations_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.reservations_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.reservations_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.reservations_table.verticalHeader().setVisible(False)
        self.reservations_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.reservations_table.setAlternatingRowColors(True)
        self.reservations_table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #E0E0E0;
                border-radius: 8px;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #4A90E2;
                color: white;
                font-weight: bold;
                padding: 8px;
                border: none;
            }
            QTableWidget::item {
                padding: 10px 5px;
            }
            QTableWidget::item:selected {
                background-color: #D3E4F8;
                color: #333;
            }
        """)

        self.reservations_table.setColumnCount(5)
        self.reservations_table.setHorizontalHeaderLabels(["ID", "Cliente", "Teléfono", "Fecha de Reserva", "Tiempo Transcurrido"])
        self.reservations_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.reservations_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.reservations_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.reservations_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.reservations_table.setColumnWidth(1, 200)
        self.reservations_table.setColumnWidth(2, 120)

        self.reservations_table.hideColumn(0) # Hide ID column
        
        self.reservations_table.cellDoubleClicked.connect(self.show_reservation_details)
        
        layout.addWidget(self.reservations_table)
        
        return page

    def create_details_page(self):
        page = QWidget()
        main_layout = QVBoxLayout(page)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)

        # --- Top bar with back button ---
        top_bar = QWidget()
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(0,0,0,0)
        back_button = QPushButton("← Volver a la lista")
        back_button.setObjectName("backButton")
        back_button.setStyleSheet("#backButton { font-size: 14px; font-weight: bold; color: #4A90E2; border: none; text-align: left; padding: 0; }")
        back_button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        back_button.clicked.connect(self.show_list_page)
        
        self.details_title = ElidedLabel("Detalles de la Reserva")
        self.details_title.setObjectName("title")
        self.details_title.setStyleSheet("#title { font-size: 22px; font-weight: bold; color: #333; }")
        
        top_bar_layout.addWidget(back_button)
        top_bar_layout.addSpacing(20)
        top_bar_layout.addWidget(self.details_title)
        top_bar_layout.addStretch()
        main_layout.addWidget(top_bar)

        # --- Main content area (scrollable) ---
        content_splitter = QHBoxLayout()
        
        # --- Left Column: Client and Books ---
        left_column = QVBoxLayout()
        
        # Client Details Group
        client_group = QGroupBox("Datos del Cliente")
        client_layout = QFormLayout(client_group)
        self.detail_client_name = QLabel()
        self.detail_client_phone = QLabel()
        client_layout.addRow("Nombre:", self.detail_client_name)
        client_layout.addRow("Teléfono:", self.detail_client_phone)
        left_column.addWidget(client_group)
        
        # Reserved Books Group
        books_group = QGroupBox("Libros Reservados")
        books_layout = QVBoxLayout(books_group)
        self.detail_books_table = QTableWidget()
        self.detail_books_table.setColumnCount(4)
        self.detail_books_table.setHorizontalHeaderLabels(["ISBN", "Título", "Cant.", "Precio Unit."])
        self.detail_books_table.verticalHeader().setVisible(False)
        self.detail_books_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.detail_books_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.detail_books_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.detail_books_table.setColumnWidth(1, 250)
        books_layout.addWidget(self.detail_books_table)
        left_column.addWidget(books_group)
        
        content_splitter.addLayout(left_column, 2)
        content_splitter.addSpacing(20)

        # --- Right Column: Financial and Actions ---
        right_column = QVBoxLayout()
        
        # Financial Status Group
        financial_group = QGroupBox("Estado Financiero")
        financial_layout = QFormLayout(financial_group)
        self.detail_total_amount = QLabel()
        self.detail_paid_amount = QLabel()
        self.detail_pending_amount = QLabel()
        financial_layout.addRow("Monto Total:", self.detail_total_amount)
        financial_layout.addRow("Monto Abonado:", self.detail_paid_amount)
        financial_layout.addRow("Saldo Pendiente:", self.detail_pending_amount)
        right_column.addWidget(financial_group)

        # Actions Group
        actions_group = QGroupBox("Acciones")
        actions_layout = QVBoxLayout(actions_group)
        
        # Add Deposit
        deposit_layout = QHBoxLayout()
        self.deposit_input = QLineEdit()
        self.deposit_input.setPlaceholderText("Monto a abonar")
        self.deposit_input.setValidator(QDoubleValidator(0, 9999999, 2))
        add_deposit_button = QPushButton("Añadir Abono")
        add_deposit_button.setAutoDefault(False)
        add_deposit_button.clicked.connect(self.handle_add_deposit)
        deposit_layout.addWidget(self.deposit_input)
        deposit_layout.addWidget(add_deposit_button)
        actions_layout.addLayout(deposit_layout)

        # Complete Payment
        self.complete_payment_button = QPushButton("Completar Pago y Vender")
        self.complete_payment_button.setAutoDefault(False)
        self.complete_payment_button.clicked.connect(self.handle_complete_sale)
        actions_layout.addWidget(self.complete_payment_button)
        
        actions_layout.addSpacing(20)
        
        # Cancel options
        cancel_refund_button = QPushButton("Cancelar y Devolver Dinero")
        cancel_refund_button.setAutoDefault(False)
        cancel_refund_button.setStyleSheet("background-color: #E67E22; color: white; font-weight: bold; border-radius: 5px; padding: 5px;")
        cancel_refund_button.clicked.connect(self.handle_cancel_with_refund)
        cancel_forfeit_button = QPushButton("Cancelar (Cliente no retiró)")
        cancel_forfeit_button.setAutoDefault(False)
        cancel_forfeit_button.setStyleSheet("background-color: #C0392B; color: white; font-weight: bold; border-radius: 5px; padding: 5px;")
        cancel_forfeit_button.clicked.connect(self.handle_cancel_without_refund)
        
        actions_layout.addWidget(cancel_refund_button)
        actions_layout.addWidget(cancel_forfeit_button)
        
        right_column.addWidget(actions_group)
        right_column.addStretch()

        content_splitter.addLayout(right_column, 1)
        main_layout.addLayout(content_splitter)
        
        return page

    def populate_details_page(self, details: dict):
        if not details:
            # Handle case where details are not found
            QMessageBox.warning(self, "Error", "No se pudieron cargar los detalles de la reserva.")
            self.show_list_page()
            return

        self.current_reservation_id = details['id_reserva']
        
        # Populate client info
        self.details_title.setText(f"Detalles de la Reserva #{self.current_reservation_id}")
        self.detail_client_name.setText(details.get('cliente_nombre', 'N/A'))
        self.detail_client_phone.setText(details.get('cliente_telefono', 'N/A'))

        # Populate financial info
        total = details.get('monto_total', 0)
        paid = details.get('monto_abonado', 0)
        pending = total - paid
        self.detail_total_amount.setText(f"${total:,.2f}")
        self.detail_paid_amount.setText(f"${paid:,.2f}")
        self.detail_pending_amount.setText(f"${pending:,.2f}")
        self.detail_pending_amount.setStyleSheet("font-weight: bold; color: #D35400;")

        # Enable or disable complete payment button
        self.complete_payment_button.setEnabled(pending <= 0)
        if pending > 0:
            self.complete_payment_button.setText(f"Pagar Saldo (${pending:,.2f}) y Vender")
        else:
            self.complete_payment_button.setText("Convertir a Venta")

        # Populate books table
        books = details.get('libros', [])
        self.detail_books_table.setRowCount(len(books))
        for row, book in enumerate(books):
            self.detail_books_table.setItem(row, 0, QTableWidgetItem(book.get('libro_isbn')))
            self.detail_books_table.setItem(row, 1, QTableWidgetItem(book.get('titulo')))
            self.detail_books_table.setItem(row, 2, QTableWidgetItem(str(book.get('cantidad'))))
            self.detail_books_table.setItem(row, 3, QTableWidgetItem(f"${book.get('precio_unitario'):,.2f}"))

    def init_animations(self):
        self.animation = QPropertyAnimation(self.stacked_widget, b"pos")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def format_time_elapsed(self, date_str):
        if not date_str:
            return "N/A"
        
        # SQLite format is usually 'YYYY-MM-DD HH:MM:SS'
        reservation_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        elapsed = now - reservation_date

        days = elapsed.days
        hours, remainder = divmod(elapsed.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        if days > 0:
            return f"{days} día(s)"
        if hours > 0:
            return f"{hours} hora(s)"
        return f"{minutes} minuto(s)"

    def load_reservations(self):
        self.reservations_table.setRowCount(0)
        try:
            reservations = self.reservation_service.get_all_active_reservations()
            if not reservations:
                # You could show a message here if you want
                return

            self.reservations_table.setRowCount(len(reservations))
            for row, res in enumerate(reservations):
                time_elapsed = self.format_time_elapsed(res['fecha_reserva'])
                
                self.reservations_table.setItem(row, 0, QTableWidgetItem(str(res['id_reserva'])))
                self.reservations_table.setItem(row, 1, QTableWidgetItem(res['cliente_nombre']))
                self.reservations_table.setItem(row, 2, QTableWidgetItem(res['cliente_telefono']))
                self.reservations_table.setItem(row, 3, QTableWidgetItem(res['fecha_reserva']))
                self.reservations_table.setItem(row, 4, QTableWidgetItem(time_elapsed))

        except Exception as e:
            print(f"Error al cargar las reservas en el diálogo: {e}")
            # Optionally, show a QMessageBox to the user

    def show_reservation_details(self, row, column):
        id_item = self.reservations_table.item(row, 0)
        if not id_item:
            return
            
        reservation_id = int(id_item.text())
        
        details = self.reservation_service.get_reservation_details(reservation_id)
        if details:
            self.populate_details_page(details)
            self.slide_to_page(self.details_page)
        else:
            QMessageBox.critical(self, "Error", f"No se encontró la reserva con ID {reservation_id}.")

    def show_list_page(self):
        self.slide_to_page(self.list_page)

    def handle_add_deposit(self):
        if not self.current_reservation_id:
            return

        amount_str = self.deposit_input.text().strip()
        if not amount_str:
            QMessageBox.warning(self, "Entrada inválida", "Por favor, ingrese un monto para abonar.")
            return

        try:
            amount = float(amount_str.replace(',', ''))
            if amount <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            QMessageBox.warning(self, "Monto inválido", "Por favor, ingrese un número válido y positivo.")
            return

        reply = QMessageBox.question(self, "Confirmar Abono", 
                                     f"¿Está seguro de que desea añadir un abono de ${amount:,.2f} a la reserva #{self.current_reservation_id}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.reservation_service.add_deposit_to_reservation(self.current_reservation_id, amount)
            if success:
                QMessageBox.information(self, "Éxito", message)
                self.deposit_input.clear()
                # Refresh details
                details = self.reservation_service.get_reservation_details(self.current_reservation_id)
                self.populate_details_page(details)
            else:
                QMessageBox.critical(self, "Error", message)

    def handle_complete_sale(self):
        if not self.current_reservation_id:
            return

        details = self.reservation_service.get_reservation_details(self.current_reservation_id)
        if not details:
            QMessageBox.critical(self, "Error", "No se pudieron obtener los detalles de la reserva.")
            return

        total = details.get('monto_total', 0)
        paid = details.get('monto_abonado', 0)
        pending_payment = total - paid

        question_str = f"¿Desea convertir la reserva #{self.current_reservation_id} en una venta final?"
        if pending_payment > 0:
             question_str = f"El saldo pendiente es de ${pending_payment:,.2f}. ¿Desea registrar el pago y convertir la reserva en una venta final?"
        
        reply = QMessageBox.question(self, "Confirmar Venta", question_str, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.reservation_service.convert_reservation_to_sale(self.current_reservation_id, pending_payment)
            if success:
                QMessageBox.information(self, "Éxito", message)
                self.load_reservations()
                self.show_list_page()
            else:
                QMessageBox.critical(self, "Error", message)
    
    def handle_cancel_with_refund(self):
        self._execute_cancel_action(with_refund=True)

    def handle_cancel_without_refund(self):
        self._execute_cancel_action(with_refund=False)

    def _execute_cancel_action(self, with_refund: bool):
        if not self.current_reservation_id:
            return

        action_text = "cancelar la reserva y devolver el dinero" if with_refund else "cancelar la reserva (el cliente no retiró)"
        
        reply = QMessageBox.question(self, "Confirmar Cancelación", 
                                     f"¿Está seguro de que desea {action_text}?\nEsta acción no se puede deshacer.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.reservation_service.cancel_reservation(self.current_reservation_id, with_refund)
            if success:
                QMessageBox.information(self, "Éxito", message)
                self.load_reservations()
                self.show_list_page()
            else:
                QMessageBox.critical(self, "Error", message)

    def slide_to_page(self, widget_to_show):
        current_index = self.stacked_widget.currentIndex()
        target_index = self.stacked_widget.indexOf(widget_to_show)

        if current_index == target_index:
            return

        current_widget = self.stacked_widget.widget(current_index)
        
        width = self.stacked_widget.width()
        
        # Position new widget before animating
        if target_index > current_index: # To details
            p = widget_to_show.pos()
            widget_to_show.move(p.x() + width, p.y())
        else: # To list
            p = widget_to_show.pos()
            widget_to_show.move(p.x() - width, p.y())
            
        self.stacked_widget.setCurrentWidget(widget_to_show)
        widget_to_show.show()
        widget_to_show.raise_()

        self.animation.setTargetObject(current_widget)
        self.animation.setEndValue(QPoint(current_widget.x() - width if target_index > current_index else current_widget.x() + width, current_widget.y()))
        
        anim2 = QPropertyAnimation(widget_to_show, b"pos")
        anim2.setDuration(300)
        anim2.setEasingCurve(QEasingCurve.Type.InOutCubic)
        anim2.setStartValue(widget_to_show.pos())
        anim2.setEndValue(QPoint(0,0)) # Final position for both

        self.animation.start()
        anim2.start()

if __name__ == '__main__':
    # This is for testing purposes
    class MockReservationService:
        def get_all_active_reservations(self):
            from datetime import datetime, timedelta
            now = datetime.now()
            return [
                {'id_reserva': 1, 'cliente_nombre': 'Juan Perez', 'cliente_telefono': '555-1234', 'fecha_reserva': (now - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'), 'monto_total': 500.0, 'monto_abonado': 100.0},
                {'id_reserva': 2, 'cliente_nombre': 'Ana Gomez', 'cliente_telefono': '555-5678', 'fecha_reserva': (now - timedelta(hours=5)).strftime('%Y-%m-%d %H:%M:%S'), 'monto_total': 350.0, 'monto_abonado': 50.0},
            ]
        
        def get_reservation_details(self, reservation_id):
            if reservation_id == 1:
                return {
                    'id_reserva': 1,
                    'cliente_nombre': 'Juan Perez',
                    'cliente_telefono': '555-1234',
                    'fecha_creacion': '2023-10-26 10:00:00',
                    'monto_total': 500.0,
                    'monto_abonado': 100.0,
                    'notas': 'Cliente vendrá el fin de semana.',
                    'libros': [
                        {'libro_isbn': '978-0321765723', 'titulo': 'The C++ Programming Language', 'cantidad': 1, 'precio_unitario': 500.0}
                    ]
                }
            if reservation_id == 2:
                 return {
                    'id_reserva': 2,
                    'cliente_nombre': 'Ana Gomez',
                    'cliente_telefono': '555-5678',
                    'fecha_creacion': '2023-10-27 12:00:00',
                    'monto_total': 350.0,
                    'monto_abonado': 350.0,
                    'notas': 'Pago completo, solo retirar.',
                    'libros': [
                        {'libro_isbn': '978-0134494166', 'titulo': 'Clean Architecture', 'cantidad': 1, 'precio_unitario': 350.0}
                    ]
                }
            return None
        
        def add_deposit_to_reservation(self, reservation_id, amount):
            print(f"Adding deposit: {amount} to {reservation_id}")
            # In a real scenario, you'd update the data source.
            # For the mock, we can't easily change the state, so we just simulate success.
            return True, "Abono de prueba añadido."

        def cancel_reservation(self, reservation_id, with_refund):
            print(f"Canceling reservation {reservation_id} with refund: {with_refund}")
            return True, "Reserva de prueba cancelada."

        def convert_reservation_to_sale(self, reservation_id, final_payment):
            print(f"Converting reservation {reservation_id} to sale with final payment: {final_payment}")
            return True, "Reserva de prueba convertida a venta."

    app = QApplication(sys.argv)
    service = MockReservationService()
    dialog = ViewReservationsDialog(service)
    dialog.show()
    sys.exit(app.exec()) 