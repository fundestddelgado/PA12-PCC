import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import messagebox, ttk
import datos_globales 
from utils import actualizar_species_list 



def mostrar_grafico(especie):
    """
    Genera y muestra un gráfico de barras de la cantidad de la 'especie' 
    seleccionada a lo largo de los años.
    """
    # USAMOS: datos_globales.df
    filtrado = datos_globales.df[datos_globales.df["Especie"] == especie].copy()
    
    if filtrado.empty:
        messagebox.showerror("Error", "No se encontraron registros para esa especie.")
        return
    
    # Agrupa por 'Año' y suma las 'Cantidad's. Ordena por año (índice).
    agrupado = filtrado.groupby("Año", as_index=True)["Cantidad"].sum().sort_index()
    
    if agrupado.empty:
        messagebox.showerror("Error", "No hay datos por año para graficar.")
        return
    
    # Configuración y visualización del gráfico
    plt.figure(figsize=(8, 4.5))
    # Asegura que el año sea un entero para el eje X
    plt.bar(agrupado.index.astype(int), agrupado.values) 
    plt.title(f"Evolución de {especie}")
    plt.xlabel("Año")
    plt.ylabel("Cantidad")
    plt.tight_layout()
    plt.show()

def abrir_seleccion_especie_para_grafico(root_window):
    """
    Abre una ventana secundaria (Toplevel) para que el usuario seleccione 
    una especie de un Combobox y luego muestre el gráfico.
    """
    # USAMOS: datos_globales.df
    if datos_globales.df is None or datos_globales.df.empty:
        messagebox.showerror("Error", "No hay datos. Cargue o ingrese animales primero.")
        return

    # Obtiene la lista de especies únicas 
    especies = actualizar_species_list()
    
    if not especies:
        messagebox.showerror("Error", "No hay especies disponibles.")
        return
    
    win = tk.Toplevel(root_window) 
    win.title("Seleccione especie para gráfico")
    win.geometry("350x140")
    tk.Label(win, text="Seleccione la especie:", font=("Arial", 11)).pack(pady=8)
    
    
    # Combobox con la lista de especies
    cb = ttk.Combobox(win, values=especies, state="readonly", width=30)
    cb.pack()
    cb.set(especies[0])

    def btn_mostrar():
        """Función interna para manejar el clic en 'Mostrar gráfico'."""
        espec = cb.get()
        win.destroy()
        mostrar_grafico(espec)

    ttk.Button(win, text="Mostrar gráfico", command=btn_mostrar).pack(pady=10)