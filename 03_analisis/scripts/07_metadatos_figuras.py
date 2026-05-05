# =============================================================================
# 07_metadatos_figuras.py
# Proyecto: Índice de Vulnerabilidad Socioterritorial ante Inundaciones
#           Municipios de Campeche, México
# Autores:  Guillermo Adrián Chin Canché (ITESCAM)
#           Javier Pan Barcel (UAC-EPOMEX)
#           Katia Ruiz Canul (ITESCAM)
# Versión:  1.0.0
# Fecha:    2026
# -----------------------------------------------------------------------------
# Descripción:
#   Genera un archivo TXT con todos los metadatos editoriales de cada
#   figura y mapa del proyecto: título sugerido, subtítulo, descripción
#   metodológica, nota al pie, pie de figura, tabla de acrónimos y
#   nota sobre Dzitbalché. Este archivo es la fuente de referencia para
#   construir las leyendas y notas en el manuscrito del artículo.
#
#   Salida: 04_outputs/tablas/metadatos_figuras.txt
# =============================================================================

import sys
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
from config import DIR_TABLAS

# ── Tabla de acrónimos ────────────────────────────────────────────────────────
ACRONIMOS = {
    "CK": "Calkiní*",
    "CA": "Campeche",
    "CR": "Carmen",
    "CH": "Champotón",
    "HE": "Hecelchakán",
    "HO": "Hopelchén",
    "PA": "Palizada",
    "TE": "Tenabo",
    "ES": "Escárcega",
    "CL": "Calakmul",
    "CN": "Candelaria",
    "SY": "Seybaplaya",
}

# ── Nota Dzitbalché ───────────────────────────────────────────────────────────
NOTA_DZITBALCHE = (
    "* El municipio de Dzitbalché fue creado recientemente por segregación "
    "del municipio de Calkiní. El Censo de Población y Vivienda 2020 (INEGI) "
    "y el Índice de Marginación por Localidad 2020 (CONAPO) no registran a "
    "Dzitbalché como municipio independiente, por lo que sus datos se "
    "encuentran integrados en los valores correspondientes a Calkiní. "
    "Esta limitación se discute en el apartado de consideraciones metodológicas."
)

# ── Metadatos por figura ──────────────────────────────────────────────────────
FIGURAS = [
    {
        "id":          "fig01_ranking_ivs",
        "archivo":     "04_outputs/figuras/fig01_ranking_ivs.png",
        "tipo":        "Figura de publicación",
        "titulo":      (
            "Índice de Vulnerabilidad Socioterritorial ante Inundaciones "
            "en los municipios de Campeche, México (2020)"
        ),
        "subtitulo":   (
            "Ranking de municipios ordenado de mayor a menor vulnerabilidad. "
            "Las barras representan el valor del IVS para cada municipio y "
            "el color indica el nivel de vulnerabilidad asignado."
        ),
        "descripcion": (
            "Gráfica de barras horizontales que representa el Índice de "
            "Vulnerabilidad Socioterritorial (IVS) calculado para los 12 "
            "municipios del estado de Campeche a partir del Censo de "
            "Población y Vivienda 2020 (INEGI) y el Índice de Marginación "
            "por Localidad 2020 (CONAPO). El IVS integra dos dimensiones: "
            "Vulnerabilidad Social (VS, peso=0.6) y Exposición Física "
            "(EF, peso=0.4), compuestas por 8 variables normalizadas "
            "mediante el método min-max. La línea punteada indica la "
            "media del IVS para el estado."
        ),
        "pie_figura":  (
            "Fuente: elaboración propia con datos del Censo de Población "
            "y Vivienda 2020 (INEGI) e Índice de Marginación por Localidad "
            "2020 (CONAPO). IVS = Índice de Vulnerabilidad Socioterritorial. "
            "Niveles: Muy Alto ≥ p80; Alto = p60–p80; Medio = p40–p60; "
            "Bajo = p20–p40; Muy Bajo < p20 (clasificación por quintiles)."
        ),
        "nota_al_pie": NOTA_DZITBALCHE,
    },
    {
        "id":          "fig02_dimensiones_barras",
        "archivo":     "04_outputs/figuras/fig02_dimensiones_barras.png",
        "tipo":        "Figura de publicación",
        "titulo":      (
            "Comparación de las dimensiones del IVS por municipio: "
            "Vulnerabilidad Social y Exposición Física, Campeche, México (2020)"
        ),
        "subtitulo":   (
            "Valores normalizados de las dimensiones Vulnerabilidad Social "
            "(DIM_VS) y Exposición Física (DIM_EF) para cada municipio. "
            "Los municipios se ordenan de mayor a menor IVS."
        ),
        "descripcion": (
            "Gráfica de barras agrupadas que desagrega el IVS en sus dos "
            "dimensiones componentes para cada municipio. La Dimensión de "
            "Vulnerabilidad Social (DIM_VS) integra indicadores de "
            "analfabetismo, carencias de servicios básicos en vivienda y "
            "acceso a salud. La Dimensión de Exposición Física (DIM_EF) "
            "integra densidad de población, carencia de electricidad y "
            "ausencia de bienes en el hogar. Los municipios se identifican "
            "mediante acrónimos de dos letras."
        ),
        "pie_figura":  (
            "Fuente: elaboración propia con datos del Censo de Población "
            "y Vivienda 2020 (INEGI) e IML 2020 (CONAPO). "
            "DIM_VS = Dimensión Vulnerabilidad Social (peso 0.6); "
            "DIM_EF = Dimensión Exposición Física (peso 0.4). "
            "Valores en escala normalizada [0–1]."
        ),
        "nota_al_pie": NOTA_DZITBALCHE,
    },
    {
        "id":          "fig03_heatmap_variables",
        "archivo":     "04_outputs/figuras/fig03_heatmap_variables.png",
        "tipo":        "Figura de publicación",
        "titulo":      (
            "Valores normalizados de las variables del IVS por municipio, "
            "Campeche, México (2020)"
        ),
        "subtitulo":   (
            "Mapa de calor de las ocho variables normalizadas que componen "
            "el IVS. Los municipios se ordenan de mayor (arriba) a menor "
            "(abajo) valor del IVS."
        ),
        "descripcion": (
            "Mapa de calor (heatmap) que muestra los valores normalizados "
            "[0–1] de las 8 variables del índice para los 12 municipios de "
            "Campeche. La línea punteada vertical separa las variables de "
            "la Dimensión de Vulnerabilidad Social (VS1–VS5, izquierda) de "
            "las variables de la Dimensión de Exposición Física (EF1–EF3, "
            "derecha). Valores cercanos a 1 (rojo intenso) indican mayor "
            "vulnerabilidad; valores cercanos a 0 (amarillo) indican menor "
            "vulnerabilidad en esa variable."
        ),
        "pie_figura":  (
            "Fuente: elaboración propia con datos del Censo de Población "
            "y Vivienda 2020 (INEGI) e IML 2020 (CONAPO). "
            "Variables: VS1=Analfabetismo, VS2=Sin agua entubada, "
            "VS3=Sin drenaje, VS4=Piso de tierra, VS5=Sin derechohabiencia, "
            "EF1=Densidad de población, EF2=Sin electricidad, "
            "EF3=Sin bienes en el hogar. Normalización min-max [0–1]."
        ),
        "nota_al_pie": NOTA_DZITBALCHE,
    },
    {
        "id":          "fig04_mapa_cloropletico",
        "archivo":     "04_outputs/mapas/fig04_mapa_cloropletico.png",
        "tipo":        "Mapa de publicación",
        "titulo":      (
            "Distribución espacial del Índice de Vulnerabilidad "
            "Socioterritorial ante Inundaciones, Campeche, México (2020)"
        ),
        "subtitulo":   (
            "Mapa coroplético del IVS para los 12 municipios de Campeche. "
            "La intensidad del color refleja el nivel de vulnerabilidad "
            "de cada municipio."
        ),
        "descripcion": (
            "Mapa coroplético que representa la distribución espacial del "
            "Índice de Vulnerabilidad Socioterritorial (IVS) en el estado "
            "de Campeche. Los polígonos municipales están coloreados según "
            "el valor del IVS calculado, utilizando una escala continua "
            "de amarillo (menor vulnerabilidad) a rojo (mayor "
            "vulnerabilidad). Los municipios se identifican mediante "
            "acrónimos de dos letras. La cartografía base corresponde al "
            "Marco Geoestadístico Nacional 2025 (INEGI)."
        ),
        "pie_figura":  (
            "Fuente: elaboración propia con datos del Censo de Población "
            "y Vivienda 2020 (INEGI), IML 2020 (CONAPO) y Marco "
            "Geoestadístico Nacional 2025 (INEGI). Proyección: "
            "coordenadas geográficas WGS84. Paleta: YlOrRd (Amarillo–Rojo)."
        ),
        "nota_al_pie": NOTA_DZITBALCHE,
    },
    {
        "id":          "fig05_mapa_interpolado",
        "archivo":     "04_outputs/mapas/fig05_mapa_interpolado.png",
        "tipo":        "Mapa de publicación / exploratorio",
        "titulo":      (
            "Superficie continua de vulnerabilidad ante inundaciones "
            "estimada por interpolación espacial, Campeche, México (2020)"
        ),
        "subtitulo":   (
            "Estimación continua del IVS a partir de los valores calculados "
            "para las localidades de Campeche mediante interpolación por "
            "distancia inversa ponderada (IDW)."
        ),
        "descripcion": (
            "Mapa de superficie que representa la distribución espacial "
            "continua de la vulnerabilidad ante inundaciones en el estado "
            "de Campeche. A diferencia del mapa coroplético (Fig. 4), este "
            "mapa utiliza los valores calculados por localidad para "
            "generar una superficie interpolada mediante el método de "
            "distancia inversa ponderada (IDW, Inverse Distance Weighting), "
            "lo que permite visualizar gradientes de vulnerabilidad "
            "dentro y entre municipios. La superficie se recorta al "
            "límite estatal de Campeche."
        ),
        "pie_figura":  (
            "Fuente: elaboración propia con datos del Censo de Población "
            "y Vivienda 2020 (INEGI) e IML 2020 (CONAPO). Método de "
            "interpolación: IDW (potencia=2, vecinos=8). Resolución de "
            "la cuadrícula: 0.05° (~5.5 km). Proyección: WGS84. "
            "El mapa es de carácter exploratorio complementario al "
            "análisis municipal."
        ),
        "nota_al_pie": NOTA_DZITBALCHE,
    },
    {
        "id":          "exp01_dispersion_vs_ef",
        "archivo":     "04_outputs/figuras/exp01_dispersion_vs_ef.png",
        "tipo":        "Figura exploratoria",
        "titulo":      (
            "Relación entre las dimensiones de Vulnerabilidad Social y "
            "Exposición Física del IVS, municipios de Campeche (2020)"
        ),
        "subtitulo":   (
            "Diagrama de dispersión que muestra la relación entre DIM_VS "
            "y DIM_EF. La línea diagonal representa la igualdad entre "
            "ambas dimensiones."
        ),
        "descripcion": (
            "Diagrama de dispersión que permite identificar municipios "
            "donde ambas dimensiones son consistentes (puntos cercanos "
            "a la diagonal) y municipios con perfiles asimétricos "
            "(puntos alejados de la diagonal). Los puntos sobre la "
            "diagonal indican mayor vulnerabilidad social que física "
            "y viceversa."
        ),
        "pie_figura":  (
            "Fuente: elaboración propia. DIM_VS = Dimensión Vulnerabilidad "
            "Social; DIM_EF = Dimensión Exposición Física. "
            "Escala normalizada [0–1]. El color de cada punto indica "
            "el nivel de vulnerabilidad asignado al municipio."
        ),
        "nota_al_pie": NOTA_DZITBALCHE,
    },
    {
        "id":          "exp02_boxplot_variables",
        "archivo":     "04_outputs/figuras/exp02_boxplot_variables.png",
        "tipo":        "Figura exploratoria",
        "titulo":      (
            "Distribución de las variables normalizadas del IVS entre "
            "los municipios de Campeche, México (2020)"
        ),
        "subtitulo":   (
            "Diagrama de caja y bigotes de las 8 variables normalizadas "
            "del índice. La línea punteada indica el punto medio de la "
            "escala normalizada (0.5)."
        ),
        "descripcion": (
            "Diagrama de caja (boxplot) que muestra la dispersión de "
            "cada variable normalizada entre los 12 municipios. Las "
            "variables con mayor rango intercuartílico tienen mayor "
            "poder discriminatorio en el índice. Útil para identificar "
            "qué variables generan mayor diferenciación entre municipios."
        ),
        "pie_figura":  (
            "Fuente: elaboración propia con datos del Censo 2020 (INEGI) "
            "e IML 2020 (CONAPO). N=12 municipios. "
            "Escala normalizada min-max [0–1]."
        ),
        "nota_al_pie": "",
    },
    {
        "id":          "exp03_correlacion_iml_ivs",
        "archivo":     "04_outputs/figuras/exp03_correlacion_iml_ivs.png",
        "tipo":        "Figura exploratoria — Validación externa",
        "titulo":      (
            "Correlación entre el Índice de Marginación Municipal "
            "(CONAPO 2020) y el IVS calculado, municipios de Campeche"
        ),
        "subtitulo":   (
            "Validación externa del IVS mediante correlación de Pearson "
            "con el Índice de Marginación Municipal (IML) de CONAPO."
        ),
        "descripcion": (
            "Diagrama de dispersión que contrasta el IVS calculado en "
            "este estudio con el Índice de Marginación Municipal (IML) "
            "de CONAPO 2020, una medida oficial e independiente de "
            "carencias socioeconómicas. Una correlación alta y positiva "
            "entre ambos índices proporciona evidencia de validez de "
            "constructo para el IVS propuesto."
        ),
        "pie_figura":  (
            "Fuente: elaboración propia. r = coeficiente de correlación "
            "de Pearson. La línea punteada representa la tendencia lineal. "
            "Nota: con N=12, interpretar con cautela el valor de r."
        ),
        "nota_al_pie": NOTA_DZITBALCHE,
    },
    {
        "id":          "exp04_radar_municipios",
        "archivo":     "04_outputs/figuras/exp04_radar_municipios.png",
        "tipo":        "Figura exploratoria",
        "titulo":      (
            "Perfil de vulnerabilidad por variable para los municipios "
            "con mayor y menor IVS, Campeche, México (2020)"
        ),
        "subtitulo":   (
            "Gráfica de radar donde cada vértice representa uno de los "
            "6 municipios seleccionados y cada línea de color representa "
            "una variable normalizada del índice."
        ),
        "descripcion": (
            "Gráfica de radar (spider chart) con estructura invertida: "
            "los vértices representan los 6 municipios seleccionados "
            "(3 con mayor IVS y 3 con menor IVS) y cada línea de color "
            "representa una variable normalizada del índice. Esta "
            "representación permite identificar qué variables impulsan "
            "la vulnerabilidad en cada municipio extremo y comparar "
            "perfiles de vulnerabilidad entre municipios."
        ),
        "pie_figura":  (
            "Fuente: elaboración propia. Se muestran los 3 municipios "
            "con mayor IVS (mayor vulnerabilidad) y los 3 con menor IVS "
            "(menor vulnerabilidad). Cada línea de color representa una "
            "variable normalizada del índice [0–1]."
        ),
        "nota_al_pie": NOTA_DZITBALCHE,
    },
]


def generar_metadatos() -> None:
    """Genera el archivo TXT con todos los metadatos editoriales."""
    DIR_TABLAS.mkdir(parents=True, exist_ok=True)
    ruta  = DIR_TABLAS / "metadatos_figuras.txt"
    ahora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(ruta, "w", encoding="utf-8") as f:

        def linea(char="=", n=72):
            f.write(char * n + "\n")

        def subtitulo(texto):
            f.write(f"\n  >>> {texto}\n")

        # ── Encabezado ────────────────────────────────────────────────────────
        linea()
        f.write("  METADATOS EDITORIALES DE FIGURAS Y MAPAS\n")
        f.write("  Proyecto: Índice de Vulnerabilidad Socioterritorial\n")
        f.write("            ante Inundaciones — Campeche, México\n")
        f.write(f"  Generado: {ahora}\n")
        linea()

        # ── Tabla de acrónimos global ─────────────────────────────────────────
        f.write("\n")
        linea("-")
        f.write("  TABLA DE ACRÓNIMOS (usar en todas las figuras)\n")
        linea("-")
        f.write(f"\n  {'Acrónimo':<10} {'Municipio'}\n")
        f.write(f"  {'-'*40}\n")
        for acr, mun in ACRONIMOS.items():
            f.write(f"  {acr:<10} {mun}\n")
        f.write(f"\n  {NOTA_DZITBALCHE}\n")

        # ── Metadatos por figura ──────────────────────────────────────────────
        for fig in FIGURAS:
            f.write("\n")
            linea()
            f.write(f"  ID:      {fig['id']}\n")
            f.write(f"  Tipo:    {fig['tipo']}\n")
            f.write(f"  Archivo: {fig['archivo']}\n")
            linea()

            subtitulo("TÍTULO SUGERIDO")
            f.write(f"\n  {fig['titulo']}\n")

            subtitulo("SUBTÍTULO / DESCRIPCIÓN CORTA")
            f.write(f"\n  {fig['subtitulo']}\n")

            subtitulo("DESCRIPCIÓN METODOLÓGICA (para sección de métodos)")
            # Wrap manual a 68 caracteres
            desc  = fig["descripcion"]
            words = desc.split()
            linea_actual = "  "
            for word in words:
                if len(linea_actual) + len(word) + 1 > 70:
                    f.write(linea_actual + "\n")
                    linea_actual = "  " + word
                else:
                    linea_actual += (" " if linea_actual != "  " else "") + word
            if linea_actual.strip():
                f.write(linea_actual + "\n")

            subtitulo("PIE DE FIGURA (para usar directamente en el artículo)")
            pie   = fig["pie_figura"]
            words = pie.split()
            linea_actual = "  "
            for word in words:
                if len(linea_actual) + len(word) + 1 > 70:
                    f.write(linea_actual + "\n")
                    linea_actual = "  " + word
                else:
                    linea_actual += (" " if linea_actual != "  " else "") + word
            if linea_actual.strip():
                f.write(linea_actual + "\n")

            if fig.get("nota_al_pie"):
                subtitulo("NOTA AL PIE (*)")
                nota  = fig["nota_al_pie"]
                words = nota.split()
                linea_actual = "  "
                for word in words:
                    if len(linea_actual) + len(word) + 1 > 70:
                        f.write(linea_actual + "\n")
                        linea_actual = "  " + word
                    else:
                        linea_actual += (" " if linea_actual != "  " else "") + word
                if linea_actual.strip():
                    f.write(linea_actual + "\n")

        # ── Pie del archivo ───────────────────────────────────────────────────
        f.write("\n")
        linea()
        f.write(f"  Fin del archivo — generado el {ahora}\n")
        linea()

    print(f"  Metadatos guardados: {ruta.name}")


def main():
    print("=" * 60)
    print("SCRIPT 07 — Metadatos editoriales de figuras")
    print("=" * 60)
    generar_metadatos()
    print("\n✓ Script 07 completado exitosamente\n")


if __name__ == "__main__":
    main()