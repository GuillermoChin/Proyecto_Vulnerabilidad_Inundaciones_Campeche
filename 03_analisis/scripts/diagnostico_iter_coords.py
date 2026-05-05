# diagnostico_iter_coords.py — ejecutar una sola vez
import pandas as pd
from pathlib import Path

ruta = Path("01_datos_crudos/iter_04_cpv2020_csv/conjunto_de_datos/conjunto_de_datos_iter_04CSV20.csv")

df = pd.read_csv(ruta, encoding="utf-8-sig", dtype=str, low_memory=False)
df.columns = [c.replace("ï»¿", "").strip() for c in df.columns]

# Solo localidades (no totales municipales)
df_loc = df[(df["MUN"] != "000") & (~df["LOC"].isin(["0000","000"]))].copy()

print(f"Total localidades: {len(df_loc)}")
print(f"\nColumnas de coordenadas disponibles:")
cols_coord = [c for c in df.columns if any(x in c.upper()
              for x in ["LON","LAT","ALT","LONG"])]
print(f"  {cols_coord}")

print(f"\nValores únicos en LONGITUD (primeros 10):")
print(df_loc["LONGITUD"].value_counts().head(10))

print(f"\nValores únicos en LATITUD (primeros 10):")
print(df_loc["LATITUD"].value_counts().head(10))

print(f"\nValores únicos en ALTITUD (primeros 5):")
print(df_loc["ALTITUD"].value_counts().head(5))

# Ver cuántas son numéricas reales
df_loc["LON_NUM"] = pd.to_numeric(df_loc["LONGITUD"], errors="coerce")
df_loc["LAT_NUM"] = pd.to_numeric(df_loc["LATITUD"],  errors="coerce")
print(f"\nLocalidades con LONGITUD numérica válida: {df_loc['LON_NUM'].notna().sum()}")
print(f"Localidades con LATITUD numérica válida:  {df_loc['LAT_NUM'].notna().sum()}")

# Muestra de las primeras 5 filas con coords
df_con = df_loc[df_loc["LON_NUM"].notna()].head(5)
if len(df_con) > 0:
    print(f"\nEjemplo de localidades con coords válidas:")
    print(df_con[["NOM_MUN","NOM_LOC","LONGITUD","LATITUD","POBTOT"]].to_string())
else:
    print("\n⚠ Ninguna localidad tiene coordenadas numéricas válidas")
    print("  Revisando shapefile de localidades como alternativa...")
    shp = Path("01_datos_crudos/04_campeche/conjunto_de_datos/04l.shp")
    print(f"  Shapefile 04l.shp existe: {shp.exists()}")
    shp2 = Path("01_datos_crudos/04_campeche/conjunto_de_datos/04sip.shp")
    print(f"  Shapefile 04sip.shp existe: {shp2.exists()}")