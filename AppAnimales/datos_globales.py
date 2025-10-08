import pandas as pd

# DataFrame que contendrá los datos de la aplicación
df = pd.DataFrame(columns=["Especie", "Cantidad", "Año", "Provincia"])

# Ruta del archivo Excel cargado (inicialmente None)
ruta_archivo = None

PROVINCIAS_PANAMA = [
    "Bocas del Toro",
    "Chiriquí",
    "Coclé",
    "Colón",
    "Darién",
    "Herrera",
    "Los Santos",
    "Panamá",
    "Veraguas",
    "Panamá Oeste"
]