from core.sqlmanager import SQLManager
from typing import Optional

class EgresoService:
    """
    Servicio para gestionar las operaciones relacionadas con los egresos.
    """
    def __init__(self, data_manager: SQLManager):
        """
        Inicializa el servicio de egresos.

        Args:
            data_manager: Una instancia de SQLManager para la interacción con la base de datos.
        """
        self.data_manager = data_manager

    def registrar_egreso(self, monto: float, concepto: str, id_reserva: Optional[int] = None) -> bool:
        """
        Registra un nuevo egreso en la base de datos.

        Args:
            monto: El monto del egreso.
            concepto: La descripción o concepto del egreso.
            id_reserva: Opcionalmente, el ID de una reserva asociada.

        Returns:
            True si el egreso se registró correctamente, False en caso contrario.
        """
        if not concepto or monto <= 0:
            print("Error: El concepto no puede estar vacío y el monto debe ser positivo.")
            return False
            
        query = "INSERT INTO egresos (monto, concepto, id_reserva) VALUES (?, ?, ?)"
        params = (monto, concepto, id_reserva)
        
        try:
            self.data_manager.execute_query(query, params)
            print(f"Egreso registrado: {concepto} - ${monto:,.2f}")
            return True
        except Exception as e:
            print(f"Error al registrar el egreso en la base de datos: {e}")
            return False 