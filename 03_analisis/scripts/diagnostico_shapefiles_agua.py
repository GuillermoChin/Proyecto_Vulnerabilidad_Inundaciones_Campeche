# diagnostico_shapefiles_agua.py
import geopandas as gpd
from pathlib import Path

carpeta = Path("01_datos_crudos/04_campeche/conjunto_de_datos")
shapefiles = list(carpeta.glob("*.shp"))

print("Shapefiles disponibles y sus columnas:")
for shp in sorted(shapefiles):
    try:
        gdf = gpd.read_file(shp, rows=2)
        print(f"\n  {shp.name}")
        print(f"    Columnas: {list(gdf.columns)}")
        print(f"    CRS: {gdf.crs}")
        print(f"    Tipo geom: {gdf.geometry.geom_type.unique()}")
        if "TIPOCUERP" in gdf.columns or "TIPO" in gdf.columns:
            col = "TIPOCUERP" if "TIPOCUERP" in gdf.columns else "TIPO"
            gdf_full = gpd.read_file(shp, rows=10)
            print(f"    Valores {col}: {gdf_full[col].unique()}")
    except Exception as e:
        print(f"  {shp.name} — ERROR: {e}")