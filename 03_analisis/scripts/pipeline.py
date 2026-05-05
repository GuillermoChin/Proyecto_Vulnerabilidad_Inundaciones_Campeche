# =============================================================================
# pipeline.py
# Proyecto: Índice de Vulnerabilidad Socioterritorial ante Inundaciones
#           Municipios de Campeche, México
# Autores:  Guillermo Adrián Chin Canché (ITESCAM)
#           Javier Pan Barcel (UAC-EPOMEX)
#           [Nombre] [Apellido Katia] ([Institución])
# Versión:  1.0.0
# Fecha:    2026
# -----------------------------------------------------------------------------
# Descripción:
#   Script maestro de ejecución. Corre todos los scripts del análisis
#   en orden secuencial, registra el tiempo de cada etapa y genera
#   un log de ejecución en 04_outputs/log_pipeline.txt.
#   Puede ejecutarse completo o desde un paso específico.
#
#   Uso:
#     python pipeline.py             → Ejecuta todo desde el inicio
#     python pipeline.py --desde 3  → Ejecuta desde el script 03 en adelante
#     python pipeline.py --solo 6   → Ejecuta únicamente el script 06
#
#   Orden de ejecución:
#     01_cargar_iter.py
#     02_cargar_iml.py
#     03_limpiar_datos.py
#     04_normalizar.py
#     05_calcular_indice.py
#     06_visualizaciones.py
# =============================================================================

import sys
import time
import argparse
import datetime
import traceback
from pathlib import Path

# ── Agregar carpeta de scripts al path ───────────────────────────────────────
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from config import DIR_TABLAS

# ── Registro de scripts en orden ─────────────────────────────────────────────
PIPELINE = [
    (1, "01_cargar_iter",      "Carga y filtrado del ITER Censo 2020"),
    (2, "02_cargar_iml",       "Carga y agregación del IML CONAPO 2020"),
    (3, "03_limpiar_datos",    "Limpieza, merge e integración de fuentes"),
    (4, "04_normalizar",       "Normalización min-max de variables"),
    (5, "05_calcular_indice",  "Cálculo del índice compuesto y ranking"),
    (6, "06_visualizaciones",  "Visualizaciones y reporte completo"),
]


# =============================================================================
# UTILIDADES DE LOG
# =============================================================================

class Logger:
    """
    Escribe simultáneamente en consola y en archivo de log.
    """
    def __init__(self, ruta_log: Path):
        DIR_TABLAS.mkdir(parents=True, exist_ok=True)
        self.ruta  = ruta_log
        self.lineas = []

    def write(self, texto: str) -> None:
        print(texto)
        self.lineas.append(texto)

    def flush(self) -> None:
        with open(self.ruta, "w", encoding="utf-8") as f:
            f.write("\n".join(self.lineas))

    def linea(self, char="=", n=60) -> None:
        self.write(char * n)

    def titulo(self, texto: str) -> None:
        self.linea()
        self.write(f"  {texto}")
        self.linea()


# =============================================================================
# EJECUCIÓN DE SCRIPTS
# =============================================================================

def ejecutar_script(nombre_modulo: str, descripcion: str,
                    log: Logger) -> tuple[bool, float]:
    """
    Importa y ejecuta el main() de un script del pipeline.
    Devuelve (éxito: bool, tiempo_segundos: float).
    """
    inicio = time.time()
    try:
        modulo = __import__(nombre_modulo)
        # Recargar por si ya fue importado antes en la misma sesión
        import importlib
        modulo = importlib.reload(modulo)
        modulo.main()
        elapsed = time.time() - inicio
        log.write(f"  ✓ {nombre_modulo:<28} {elapsed:>6.1f}s")
        return True, elapsed

    except FileNotFoundError as e:
        elapsed = time.time() - inicio
        log.write(f"  ✗ {nombre_modulo:<28} ERROR — Archivo no encontrado")
        log.write(f"    {e}")
        return False, elapsed

    except Exception as e:
        elapsed = time.time() - inicio
        log.write(f"  ✗ {nombre_modulo:<28} ERROR — {type(e).__name__}")
        log.write(f"    {e}")
        log.write("")
        log.write("  Traceback completo:")
        for linea in traceback.format_exc().splitlines():
            log.write(f"    {linea}")
        return False, elapsed


def parsear_argumentos() -> argparse.Namespace:
    """
    Define y parsea los argumentos de línea de comandos.
    """
    parser = argparse.ArgumentParser(
        description="Pipeline de análisis — IVS Campeche",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Ejemplos:\n"
            "  python pipeline.py              # Todo desde el inicio\n"
            "  python pipeline.py --desde 3    # Desde el script 03\n"
            "  python pipeline.py --solo 6     # Solo el script 06\n"
        )
    )
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument(
        "--desde", type=int, metavar="N",
        help="Ejecutar desde el script número N (1-6)"
    )
    grupo.add_argument(
        "--solo", type=int, metavar="N",
        help="Ejecutar únicamente el script número N (1-6)"
    )
    return parser.parse_args()


def filtrar_pipeline(args: argparse.Namespace) -> list:
    """
    Filtra los scripts a ejecutar según los argumentos recibidos.
    """
    if args.solo:
        seleccion = [p for p in PIPELINE if p[0] == args.solo]
        if not seleccion:
            print(f"  ⚠ No existe el script número {args.solo}")
            sys.exit(1)
        return seleccion

    if args.desde:
        seleccion = [p for p in PIPELINE if p[0] >= args.desde]
        if not seleccion:
            print(f"  ⚠ No hay scripts a partir del número {args.desde}")
            sys.exit(1)
        return seleccion

    return PIPELINE


# =============================================================================
# MAIN
# =============================================================================

def main():
    ahora    = datetime.datetime.now()
    fecha_str = ahora.strftime("%Y-%m-%d %H:%M:%S")
    ruta_log  = DIR_TABLAS / "log_pipeline.txt"
    log       = Logger(ruta_log)

    args     = parsear_argumentos()
    scripts  = filtrar_pipeline(args)

    # ── Encabezado ────────────────────────────────────────────────────────────
    log.titulo("PIPELINE — ÍNDICE DE VULNERABILIDAD SOCIOTERRITORIAL")
    log.write(f"  Inicio:   {fecha_str}")
    log.write(f"  Scripts:  {len(scripts)} de {len(PIPELINE)} en el pipeline")
    log.write(f"  Log:      {ruta_log}")
    log.linea()

    # ── Ejecución ─────────────────────────────────────────────────────────────
    log.write("")
    log.write("  ETAPA                          TIEMPO   ESTADO")
    log.write("  " + "-" * 55)

    resultados  = []
    tiempo_total = 0.0
    hubo_error   = False

    for num, modulo, descripcion in scripts:
        log.write(f"\n{'='*60}")
        log.write(f"  PASO {num}: {descripcion}")
        log.write(f"{'='*60}")

        exito, elapsed = ejecutar_script(modulo, descripcion, log)
        resultados.append((num, modulo, exito, elapsed))
        tiempo_total += elapsed

        if not exito:
            hubo_error = True
            log.write("")
            log.write("  ⛔ Pipeline detenido por error en este paso.")
            log.write("     Revisa el traceback anterior, corrige y")
            log.write("     reinicia con: python pipeline.py --desde "
                      f"{num}")
            break

    # ── Resumen final ─────────────────────────────────────────────────────────
    fin_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log.write("")
    log.linea()
    log.write("  RESUMEN DE EJECUCIÓN")
    log.linea()
    log.write(f"  Inicio:        {fecha_str}")
    log.write(f"  Fin:           {fin_str}")
    log.write(f"  Tiempo total:  {tiempo_total:.1f}s "
              f"({tiempo_total/60:.1f} min)")
    log.write(f"  Scripts OK:    "
              f"{sum(1 for r in resultados if r[2])}/{len(resultados)}")
    log.write("")

    for num, modulo, exito, elapsed in resultados:
        estado = "✓ OK" if exito else "✗ ERROR"
        log.write(f"  Paso {num}  {modulo:<28} {elapsed:>6.1f}s  {estado}")

    log.write("")
    if hubo_error:
        log.write("  ⛔ Pipeline completado CON ERRORES")
        log.write(f"     Revisa: {ruta_log}")
    else:
        log.write("  ✓ Pipeline completado exitosamente")
        log.write("")
        log.write("  Outputs generados:")
        log.write(f"    02_datos_procesados/  → tablas CSV procesadas")
        log.write(f"    04_outputs/figuras/   → figuras de publicación")
        log.write(f"    04_outputs/mapas/     → mapa coroplético")
        log.write(f"    04_outputs/tablas/    → tablas y reporte TXT")

    log.linea()
    log.flush()

    print(f"\n  Log guardado en: {ruta_log}")
    sys.exit(1 if hubo_error else 0)


if __name__ == "__main__":
    main()