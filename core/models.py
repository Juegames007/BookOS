from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Ingreso:
    id_ingreso: int
    monto: float
    concepto: str
    metodo_pago: str
    fecha: str
    id_reserva: Optional[int] = None
    id_venta: Optional[int] = None
    id_detalle_venta: Optional[int] = None

@dataclass
class Egreso:
    id_egreso: int
    monto: float
    concepto: str
    metodo_pago: str
    fecha: str
    id_reserva: Optional[int] = None 