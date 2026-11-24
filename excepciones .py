"""Excepciones personalizadas y configuración de logs de Software FJ."""
import logging
import os

# ---------------------------------------------------------------------------
# Configuración del archivo de logs (único uso de archivos permitido)
# ---------------------------------------------------------------------------
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename=os.path.join("logs", "eventos.log"),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger("SoftwareFJ")


class ErrorSoftwareFJ(Exception):
    """Excepción base de la aplicación."""


class ClienteInvalidoError(ErrorSoftwareFJ):
    """Datos de cliente inválidos o incompletos."""


class ServicioInvalidoError(ErrorSoftwareFJ):
    """Parámetros de servicio inválidos."""


class ServicioNoDisponibleError(ErrorSoftwareFJ):
    """El servicio solicitado no está disponible."""


class ReservaInvalidaError(ErrorSoftwareFJ):
    """Intento de reserva incorrecto."""


class OperacionNoPermitidaError(ErrorSoftwareFJ):
    """Operación no permitida para el estado actual."""


class CalculoInconsistenteError(ErrorSoftwareFJ):
    """Cálculo de costos con resultados inconsistentes."""
