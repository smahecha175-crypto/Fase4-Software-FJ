"""Modelos orientados a objetos de Software FJ: entidades, clientes, servicios y reservas."""
import re
from abc import ABC, abstractmethod
from itertools import count

from excepciones import (
    CalculoInconsistenteError,
    ClienteInvalidoError,
    OperacionNoPermitidaError,
    ReservaInvalidaError,
    ServicioInvalidoError,
    ServicioNoDisponibleError,
    logger,
)

IVA = 0.19  # Impuesto por defecto


# ---------------------------------------------------------------------------
# Clase abstracta general
# ---------------------------------------------------------------------------
class EntidadBase(ABC):
    """Entidad general del sistema: todas tienen un identificador y una descripción."""

    _contadores = {}  # un contador por familia (Cliente, Servicio, Reserva)

    def __init__(self):
        familia = next(c for c in type(self).__mro__ if EntidadBase in c.__bases__)
        self._id = next(EntidadBase._contadores.setdefault(familia, count(1)))

    @property
    def id(self):
        return self._id

    @abstractmethod
    def describir(self) -> str:
        """Devuelve una descripción legible de la entidad."""


# ---------------------------------------------------------------------------
# Cliente (encapsulación + validaciones)
# ---------------------------------------------------------------------------
class Cliente(EntidadBase):
    """Cliente con datos personales encapsulados y validados."""

    _PATRON_CORREO = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")

    def __init__(self, nombre, correo, telefono):
        super().__init__()
        self.__nombre = self._validar_nombre(nombre)
        self.__correo = self._validar_correo(correo)
        self.__telefono = self._validar_telefono(telefono)

    @staticmethod
    def _validar_nombre(nombre):
        if not isinstance(nombre, str) or len(nombre.strip()) < 3:
            raise ClienteInvalidoError("Nombre inválido: mínimo 3 caracteres.")
        return nombre.strip()

    @classmethod
    def _validar_correo(cls, correo):
        if not isinstance(correo, str) or not cls._PATRON_CORREO.match(correo):
            raise ClienteInvalidoError(f"Correo inválido: {correo!r}")
        return correo

    @staticmethod
    def _validar_telefono(telefono):
        if not isinstance(telefono, str) or not telefono.isdigit() or len(telefono) != 10:
            raise ClienteInvalidoError(f"Teléfono inválido (10 dígitos): {telefono!r}")
        return telefono

    @property
    def nombre(self):
        return self.__nombre

    @property
    def correo(self):
        return self.__correo

    @property
    def telefono(self):
        return self.__telefono

    def describir(self):
        return f"Cliente #{self.id}: {self.__nombre} <{self.__correo}>"


# ---------------------------------------------------------------------------
# Servicio abstracto y servicios especializados (herencia + polimorfismo)
# ---------------------------------------------------------------------------
class Servicio(EntidadBase, ABC):
    """Clase abstracta de servicio con tarifa por hora."""

    def __init__(self, nombre, tarifa_hora, disponible=True):
        super().__init__()
        if not isinstance(nombre, str) or not nombre.strip():
            raise ServicioInvalidoError("El servicio requiere un nombre.")
        if not isinstance(tarifa_hora, (int, float)) or tarifa_hora <= 0:
            raise ServicioInvalidoError(f"Tarifa inválida: {tarifa_hora!r}")
        self._nombre = nombre.strip()
        self._tarifa_hora = float(tarifa_hora)
        self.disponible = disponible

    @property
    def nombre(self):
        return self._nombre

    @abstractmethod
    def validar_parametros(self, horas, **kwargs):
        """Valida los parámetros específicos de cada servicio."""

    def calcular_costo(self, horas, impuesto=IVA, descuento=0.0):
        """Costo base + impuesto - descuento.

        Sobrecarga simulada con parámetros opcionales:
        calcular_costo(h)                    -> con IVA por defecto
        calcular_costo(h, impuesto=0)        -> sin impuesto
        calcular_costo(h, descuento=0.10)    -> con descuento del 10 %
        """
        if not 0 <= descuento < 1:
            raise CalculoInconsistenteError(f"Descuento fuera de rango: {descuento}")
        if impuesto < 0:
            raise CalculoInconsistenteError(f"Impuesto negativo: {impuesto}")
        total = self._costo_base(horas) * (1 + impuesto) * (1 - descuento)
        if total <= 0:
            raise CalculoInconsistenteError("El costo calculado no es positivo.")
        return round(total, 2)

    @abstractmethod
    def _costo_base(self, horas):
        """Costo antes de impuestos y descuentos (polimórfico)."""


class ReservaSala(Servicio):
    """Reserva de salas con capacidad máxima."""

    def __init__(self, nombre, tarifa_hora, capacidad, disponible=True):
        super().__init__(nombre, tarifa_hora, disponible)
        if not isinstance(capacidad, int) or capacidad <= 0:
            raise ServicioInvalidoError("La capacidad debe ser un entero positivo.")
        self._capacidad = capacidad

    def validar_parametros(self, horas, **kwargs):
        personas = kwargs.get("personas")
        if personas is None:
            raise ServicioInvalidoError("Falta el parámetro 'personas'.")
        if personas > self._capacidad:
            raise ServicioInvalidoError(
                f"La sala admite {self._capacidad} personas, se pidieron {personas}."
            )
        if not 1 <= horas <= 12:
            raise ServicioInvalidoError("Una sala se reserva entre 1 y 12 horas.")

    def _costo_base(self, horas):
        return self._tarifa_hora * horas

    def describir(self):
        return f"Sala '{self._nombre}' (cap. {self._capacidad}) ${self._tarifa_hora:,.0f}/h"


class AlquilerEquipo(Servicio):
    """Alquiler de equipos con cargo fijo de seguro."""

    SEGURO = 15000

    def __init__(self, nombre, tarifa_hora, equipo, disponible=True):
        super().__init__(nombre, tarifa_hora, disponible)
        self._equipo = equipo

    def validar_parametros(self, horas, **kwargs):
        if not 1 <= horas <= 72:
            raise ServicioInvalidoError("Un equipo se alquila entre 1 y 72 horas.")

    def _costo_base(self, horas):
        return self._tarifa_hora * horas + self.SEGURO

    def describir(self):
        return f"Alquiler de {self._equipo} (seguro ${self.SEGURO:,}) ${self._tarifa_hora:,.0f}/h"


class Asesoria(Servicio):
    """Asesoría especializada con recargo por nivel del experto."""

    RECARGOS = {"junior": 1.0, "senior": 1.5, "experto": 2.0}

    def __init__(self, nombre, tarifa_hora, nivel, disponible=True):
        super().__init__(nombre, tarifa_hora, disponible)
        if nivel not in self.RECARGOS:
            raise ServicioInvalidoError(f"Nivel de asesor inválido: {nivel!r}")
        self._nivel = nivel

    def validar_parametros(self, horas, **kwargs):
        if not 1 <= horas <= 8:
            raise ServicioInvalidoError("Una asesoría dura entre 1 y 8 horas.")

    def _costo_base(self, horas):
        return self._tarifa_hora * horas * self.RECARGOS[self._nivel]

    def describir(self):
        return f"Asesoría {self._nivel} '{self._nombre}' ${self._tarifa_hora:,.0f}/h"


# ---------------------------------------------------------------------------
# Reserva
# ---------------------------------------------------------------------------
class Reserva(EntidadBase):
    """Integra cliente, servicio, duración y estado."""

    PENDIENTE, CONFIRMADA, CANCELADA = "pendiente", "confirmada", "cancelada"

    def __init__(self, cliente, servicio, horas, **parametros):
        super().__init__()
        if not isinstance(cliente, Cliente):
            raise ReservaInvalidaError("La reserva requiere un Cliente válido.")
        if not isinstance(servicio, Servicio):
            raise ReservaInvalidaError("La reserva requiere un Servicio válido.")
        if not isinstance(horas, (int, float)) or horas <= 0:
            raise ReservaInvalidaError(f"Duración inválida: {horas!r}")
        self.cliente = cliente
        self.servicio = servicio
        self.horas = horas
        self.parametros = parametros
        self.estado = self.PENDIENTE

    def confirmar(self):
        """Confirma la reserva tras validar disponibilidad y parámetros."""
        if self.estado != self.PENDIENTE:
            raise OperacionNoPermitidaError(
                f"No se puede confirmar una reserva {self.estado}."
            )
        if not self.servicio.disponible:
            raise ServicioNoDisponibleError(f"'{self.servicio.nombre}' no está disponible.")
        try:
            self.servicio.validar_parametros(self.horas, **self.parametros)
        except ServicioInvalidoError as e:
            # Encadenamiento de excepciones
            raise ReservaInvalidaError("Parámetros de reserva rechazados.") from e
        self.estado = self.CONFIRMADA
        logger.info("Reserva #%s confirmada.", self.id)

    def cancelar(self):
        if self.estado == self.CANCELADA:
            raise OperacionNoPermitidaError("La reserva ya estaba cancelada.")
        self.estado = self.CANCELADA
        logger.info("Reserva #%s cancelada.", self.id)

    def procesar(self, descuento=0.0):
        """Confirma y calcula el costo usando try/except/else/finally."""
        costo = None
        try:
            self.confirmar()
            costo = self.servicio.calcular_costo(self.horas, descuento=descuento)
        except (ReservaInvalidaError, ServicioNoDisponibleError,
                OperacionNoPermitidaError, CalculoInconsistenteError) as e:
            if isinstance(e, CalculoInconsistenteError):
                self.estado = self.PENDIENTE  # rollback: no queda confirmada sin costo
            logger.error("Reserva #%s falló: %s (causa: %r)", self.id, e, e.__cause__)
            raise
        else:
            logger.info("Reserva #%s procesada. Costo: %s", self.id, costo)
            return costo
        finally:
            logger.info("Fin de procesamiento de reserva #%s (estado=%s).", self.id, self.estado)

    def describir(self):
        return (f"Reserva #{self.id} [{self.estado}] {self.cliente.nombre} -> "
                f"{self.servicio.nombre} x {self.horas}h")
