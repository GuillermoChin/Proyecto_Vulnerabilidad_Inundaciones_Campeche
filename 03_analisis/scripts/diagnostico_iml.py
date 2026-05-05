# diagnostico_iml.py — ejecutar una sola vez para inspeccionar el IML
import xlrd
from pathlib import Path

ruta = Path("01_datos_crudos/IML_2020/IML_2020.xls")
wb   = xlrd.open_workbook(str(ruta))

print("=" * 60)
print("HOJAS EN EL ARCHIVO IML_2020.xls")
print("=" * 60)

for i, nombre in enumerate(wb.sheet_names()):
    hoja = wb.sheet_by_index(i)
    print(f"\nHoja {i}: '{nombre}' — {hoja.nrows} filas x {hoja.ncols} cols")
    print("  Filas 0 a 7 (primeras 5 columnas):")
    for fila in range(min(8, hoja.nrows)):
        celdas = [str(hoja.cell_value(fila, j))[:25]
                  for j in range(min(5, hoja.ncols))]
        print(f"    fila {fila}: {celdas}")