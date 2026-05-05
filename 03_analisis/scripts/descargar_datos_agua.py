# descargar_datos_agua.py — ejecutar UNA sola vez
# Descarga la capa de cuerpos de agua de Natural Earth y la guarda
# en 01_datos_crudos para uso permanente del proyecto

import urllib.request
import zipfile
import shutil
from pathlib import Path

DIR_AGUA = Path("01_datos_crudos/natural_earth_agua")
DIR_AGUA.mkdir(parents=True, exist_ok=True)

archivos = [
    {
        "nombre": "ne_10m_lakes",
        "url": "https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_lakes.zip",
        "descripcion": "Lagos y lagunas (incluye Laguna de Términos)"
    },
    {
        "nombre": "ne_10m_ocean",
        "url": "https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_ocean.zip",
        "descripcion": "Océanos y mares"
    },
    {
        "nombre": "ne_10m_land",
        "url": "https://naturalearth.s3.amazonaws.com/10m_physical/ne_10m_land.zip",
        "descripcion": "Polígonos de tierra firme (excluye automáticamente agua)"
    },
]

for archivo in archivos:
    ruta_zip  = DIR_AGUA / f"{archivo['nombre']}.zip"
    ruta_shp  = DIR_AGUA / f"{archivo['nombre']}.shp"

    if ruta_shp.exists():
        print(f"  Ya existe: {archivo['nombre']}.shp — omitiendo")
        continue

    print(f"  Descargando {archivo['nombre']}...")
    print(f"  {archivo['descripcion']}")
    try:
        urllib.request.urlretrieve(archivo["url"], ruta_zip)
        print(f"  Descomprimiendo...")
        with zipfile.ZipFile(ruta_zip, "r") as z:
            z.extractall(DIR_AGUA)
        ruta_zip.unlink()
        print(f"  ✓ {archivo['nombre']} guardado en {DIR_AGUA}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

# Verificar qué quedó
print("\nArchivos descargados:")
for f in sorted(DIR_AGUA.glob("*.shp")):
    print(f"  {f.name}")
    

import geopandas as gpd
from shapely.ops import unary_union

# Cargar municipios
gdf_mun = gpd.read_file("01_datos_crudos/2025_1_04_MUN/2025_1_04_MUN.shp")
if gdf_mun.crs.to_epsg() != 4326:
    gdf_mun = gdf_mun.to_crs(epsg=4326)
estado = unary_union(gdf_mun.geometry)

# Revisar lagos
lagos = gpd.read_file("01_datos_crudos/natural_earth_agua/ne_10m_lakes.shp")
if lagos.crs.to_epsg() != 4326:
    lagos = lagos.to_crs(epsg=4326)

lagos_camp = lagos[lagos.intersects(estado)]
print(f"\nLagos que intersectan Campeche: {len(lagos_camp)}")
print(lagos_camp[["name","scalerank"]].to_string())