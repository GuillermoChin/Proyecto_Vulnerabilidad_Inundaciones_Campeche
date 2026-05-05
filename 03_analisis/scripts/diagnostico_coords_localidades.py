# diagnostico_coords_localidades.py — ejecutar una sola vez
import pandas as pd
import geopandas as gpd
from pathlib import Path

# Cargar shapefile de localidades
shp = Path("01_datos_crudos/04_campeche/conjunto_de_datos/04l.shp")
gdf = gpd.read_file(shp, engine="fiona", encoding="latin-1")

# Reproyectar a WGS84
if gdf.crs and gdf.crs.to_epsg() != 4326:
    print(f"  CRS original: {gdf.crs} — reproyectando a WGS84")
    gdf = gdf.to_crs(epsg=4326)
else:
    print(f"  CRS: {gdf.crs}")

gdf["LON"] = gdf.geometry.centroid.x
gdf["LAT"] = gdf.geometry.centroid.y

print(f"\nTotal localidades shapefile: {len(gdf)}")
print(f"Rango LON: [{gdf['LON'].min():.4f} — {gdf['LON'].max():.4f}]")
print(f"Rango LAT: [{gdf['LAT'].min():.4f} — {gdf['LAT'].max():.4f}]")
print(f"\nCampeche debería estar aprox:")
print(f"  LON: -92.5 a -89.5")
print(f"  LAT:  17.8 a  20.8")

# Detectar puntos fuera del rango esperado
fuera = gdf[
    (gdf["LON"] < -93) | (gdf["LON"] > -89) |
    (gdf["LAT"] < 17)  | (gdf["LAT"] > 21)
]
print(f"\nLocalidades con coords fuera del rango esperado: {len(fuera)}")
if len(fuera) > 0:
    print(fuera[["CVEGEO","NOMGEO","LON","LAT"]].head(10).to_string())

# Ver distribución de localidades por municipio
print(f"\nLocalidades por municipio (CVE_MUN):")
print(gdf.groupby("CVE_MUN").size().sort_values(ascending=False).to_string())

# Cargar shapefile municipal para comparar bbox
shp_mun = Path("01_datos_crudos/2025_1_04_MUN/2025_1_04_MUN.shp")
gdf_mun = gpd.read_file(shp_mun)
if gdf_mun.crs and gdf_mun.crs.to_epsg() != 4326:
    gdf_mun = gdf_mun.to_crs(epsg=4326)
bbox = gdf_mun.total_bounds
print(f"\nBBox shapefile municipal (WGS84):")
print(f"  lon_min={bbox[0]:.4f} lat_min={bbox[1]:.4f}")
print(f"  lon_max={bbox[2]:.4f} lat_max={bbox[3]:.4f}")

# Contar cuántas localidades caen DENTRO del polígono estatal
from shapely.ops import unary_union
from shapely.geometry import Point
estado = unary_union(gdf_mun.geometry)
gdf["DENTRO"] = gdf.apply(
    lambda r: estado.contains(Point(r["LON"], r["LAT"])), axis=1
)
print(f"\nLocalidades dentro del polígono estatal: "
      f"{gdf['DENTRO'].sum()} / {len(gdf)}")
print(f"Localidades FUERA del polígono estatal:  "
      f"{(~gdf['DENTRO']).sum()}")

# Mostrar las que están fuera
fuera_pol = gdf[~gdf["DENTRO"]]
if len(fuera_pol) > 0:
    print(f"\nEjemplos fuera del polígono:")
    print(fuera_pol[["CVEGEO","NOMGEO","LON","LAT"]].head(10).to_string())