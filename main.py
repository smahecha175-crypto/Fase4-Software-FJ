"""Simulación de 12 operaciones de Software FJ (sin base de datos).

Ejecutar:  python main.py
Los errores y eventos se guardan en logs/eventos.log
"""
from excepciones import ErrorSoftwareFJ, logger
from modelos import AlquilerEquipo, Asesoria, Cliente, Reserva, ReservaSala

clientes, servicios, reservas = [], [], []


def operacion(n, titulo, accion):
    """Ejecuta una operación; ante cualquier error lo registra y el programa continúa."""
    print(f"\n[{n:02d}] {titulo}")
    try:
        resultado = accion()
    except ErrorSoftwareFJ as e:
        logger.error("Op %02d '%s': %s: %s", n, titulo, type(e).__name__, e)
        print(f"     ERROR controlado -> {type(e).__name__}: {e}")
        if e.__cause__:
            print(f"     Causa original   -> {type(e.__cause__).__name__}: {e.__cause__}")
    except Exception as e:  # error inesperado: se registra y el sistema sigue activo
        logger.critical("Op %02d '%s': error inesperado %r", n, titulo, e)
        print(f"     ERROR inesperado registrado -> {e!r}")
    else:
        logger.info("Op %02d '%s' exitosa.", n, titulo)
        print(f"     OK -> {resultado}")
        return resultado
    finally:
        logger.info("Op %02d finalizada.", n)


def registrar_cliente(*args):
    c = Cliente(*args)
    clientes.append(c)
    return c.describir()


def registrar_servicio(servicio):
    servicios.append(servicio)
    return servicio.describir()


def crear_servicio(clase, *args):
    return registrar_servicio(clase(*args))


def reservar(cliente, servicio, horas, descuento=0.0, **kw):
    r = Reserva(cliente, servicio, horas, **kw)
    reservas.append(r)
    costo = r.procesar(descuento)
    return f"{r.describir()} | costo ${costo:,.2f}"


def main():
    logger.info("=== Inicio de la simulación ===")
    ana = bruno = None

    # --- Clientes ---
    operacion(1, "Registrar cliente válido (Ana)",
              lambda: registrar_cliente("Ana Torres", "ana@correo.com", "3001234567"))
    ana = clientes[0] if clientes else None
    operacion(2, "Registrar cliente con correo inválido",
              lambda: registrar_cliente("Pedro Gómez", "pedro-sin-arroba", "3009876543"))
    operacion(3, "Registrar cliente con teléfono inválido",
              lambda: registrar_cliente("Luis Pérez", "luis@correo.com", "123"))
    operacion(4, "Registrar cliente válido (Bruno)",
              lambda: registrar_cliente("Bruno Díaz", "bruno@correo.com", "3112223344"))
    bruno = clientes[1] if len(clientes) > 1 else None

    # --- Servicios ---
    sala = equipo = asesoria = None
    operacion(5, "Crear sala válida",
              lambda: crear_servicio(ReservaSala, "Sala Innovación", 50000, 10))
    sala = servicios[0] if servicios else None
    operacion(6, "Crear servicio con tarifa negativa",
              lambda: crear_servicio(AlquilerEquipo, "Portátil", -100, "Portátil"))
    operacion(7, "Crear alquiler de equipo y asesoría válidos",
              lambda: (crear_servicio(AlquilerEquipo, "Proyector", 20000, "Proyector 4K"),
                       crear_servicio(Asesoria, "Arquitectura de software", 80000, "senior"))[1])
    equipo, asesoria = servicios[1], servicios[2]

    # --- Reservas ---
    operacion(8, "Reserva exitosa de sala (con descuento 10 %)",
              lambda: reservar(ana, sala, 3, descuento=0.10, personas=8))
    operacion(9, "Reserva fallida: personas exceden capacidad (excepción encadenada)",
              lambda: reservar(ana, sala, 2, personas=25))
    operacion(10, "Reserva fallida: falta parámetro 'personas'",
              lambda: reservar(bruno, sala, 2))
    equipo.disponible = False
    operacion(11, "Reserva fallida: equipo no disponible",
              lambda: reservar(bruno, equipo, 5))
    equipo.disponible = True
    operacion(12, "Reserva exitosa de asesoría senior",
              lambda: reservar(bruno, asesoria, 2))
    operacion(13, "Cancelar dos veces la misma reserva",
              lambda: (reservas[0].cancelar(), reservas[0].cancelar()))
    operacion(14, "Cálculo inconsistente (descuento 150 %)",
              lambda: reservar(ana, equipo, 4, descuento=1.5))

    print("\n=== Resumen ===")
    print(f"Clientes: {len(clientes)} | Servicios: {len(servicios)} | Reservas: {len(reservas)}")
    for r in reservas:
        print(" -", r.describir())
    logger.info("=== Fin de la simulación ===")
    print("\nEl sistema terminó sin interrupciones. Revise logs/eventos.log")


if __name__ == "__main__":
    main()
