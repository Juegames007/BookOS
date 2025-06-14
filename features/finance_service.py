from typing import List, Tuple
from core.interfaces import DataManagerInterface
from core.models import Ingreso, Egreso

class FinanceService:
    def __init__(self, data_manager: DataManagerInterface):
        """
        Inicializa el servicio de finanzas.

        Args:
            data_manager: Una instancia que implementa DataManagerInterface.
        """
        self.data_manager = data_manager

    def get_finances_by_date(self, date: str) -> Tuple[List[Ingreso], List[Egreso]]:
        """
        Obtiene los ingresos y egresos para una fecha específica.

        Args:
            date: La fecha en formato 'YYYY-MM-DD'.

        Returns:
            Una tupla conteniendo la lista de ingresos y la lista de egresos.
        """
        ingresos = self.data_manager.get_ingresos_by_date(date)
        egresos = self.data_manager.get_egresos_by_date(date)
        return ingresos, egresos

    def update_ingreso(self, id_ingreso: int, monto: float, concepto: str, metodo_pago: str) -> bool:
        """
        Actualiza un registro de ingreso existente.
        """
        return self.data_manager.update_ingreso(id_ingreso, monto, concepto, metodo_pago)

    def update_egreso(self, id_egreso: int, monto: float, concepto: str, metodo_pago: str) -> bool:
        """
        Actualiza un registro de egreso existente.
        """
        return self.data_manager.update_egreso(id_egreso, monto, concepto, metodo_pago) 