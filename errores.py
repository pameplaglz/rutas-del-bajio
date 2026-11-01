"""Excepciones de dominio y constantes de subestados de rechazo para Rutas del Bajío.

Centraliza la jerarquía de errores personalizados del sistema y las constantes
inmutables de subestados de rechazo para la carga por lotes.
"""

from typing import List, Optional


# Constantes oficiales de subestados de rechazo en procesamiento por lotes
SUBESTADO_CUARENTENA: str = "Rechazo: Cuarentena"
SUBESTADO_FORMATO_INVALIDO: str = "Rechazo: Formato Inválido"
SUBESTADO_RED_FRIO: str = "Rechazo: Red de Frío"
SUBESTADO_PESAJE: str = "Rechazo: Pesaje"
SUBESTADO_DATOS_INVALIDOS: str = "Rechazo: Datos Inválidos"
SUBESTADO_ESTADO_INVALIDO: str = "Rechazo: Estado Inválido"
SUBESTADO_DESCARTE: str = "Rechazo: Descarte"


class ErrorTransicionEstado(ValueError):
    """Se intentó realizar una transición no permitida por la máquina de estados del pedido."""


class ErrorIntegridadReferencial(ValueError):
    """Se intentó eliminar un cliente o una ruta que tiene pedidos asociados activos o históricos."""


class ErrorArchivoLote(ValueError):
    """El archivo CSV no existe, está vacío o sus encabezados no coinciden con el esquema esperado."""


class FilaLoteInvalidaError(ValueError):
    """Una fila individual del lote incumple una o más reglas de limpieza o validación (RL).

    Atributos:
        regla: Identificador de la primera regla incumplida en orden numérico.
        motivo: Descripción detallada de las causas del rechazo.
        subestado_rechazo: Subestado de clasificación asociado a la regla primaria.
        reglas: Lista ordenada con todos los identificadores de reglas violadas por la fila.
    """

    def __init__(
        self,
        regla: str,
        motivo: str,
        subestado_rechazo: str = SUBESTADO_DESCARTE,
        reglas: Optional[List[str]] = None,
    ) -> None:
        super().__init__(f"[{regla}] {motivo}")
        self.regla: str = regla
        self.motivo: str = motivo
        self.subestado_rechazo: str = subestado_rechazo
        self.reglas: List[str] = list(reglas) if reglas is not None else [regla]
