import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd 
import datos_globales 

# ----------------------------------------------------------------------
# 1. Definición de Variables de Interfaz Globales (DECLARACIÓN y CONSTRUCCIÓN INICIAL)
# CRÍTICO: Las variables deben tener su valor final antes de ser importadas/usadas.
# ----------------------------------------------------------------------
root = tk.Tk()
root.title("Animales en Peligro de Extinción")
root.geometry("1000x600")
root.configure(bg="#F0F8F0") 

# Configuración de estilos ttk (OK)
style = ttk.Style()
style.theme_use('clam') 

# --- Estilo de Botones (TButton) ---
style.configure('TButton', 
    font=('Verdana', 10, 'bold'), 
    padding=[15, 10, 15, 10],
    background='#4CAF50',      
    foreground='white',        
    relief='raised',
    borderwidth=1)             
style.map('TButton', 
    foreground=[('active', 'white'), ('pressed', 'white')], 
    background=[('active', '#2E7D32'), ('focus', '#2E7D32')],
    relief=[('pressed', 'sunken')])
# --- Estilo de la Tabla (Treeview) ---
style.configure("Treeview.Heading", 
    font=('Verdana', 11, 'bold'), 
    background="#2E7D32",       
    foreground="white")           
style.configure("Treeview", 
    font=('Verdana', 10), 
    rowheight=25,
    fieldbackground='#FFFFFF')   
style.map('Treeview', 
    background=[('selected', '#B0C4DE')])

# Se declaran todas las variables de la GUI
frames = {}
entry_nombre, entry_cantidad, entry_anio, entry_provincia = None, None, None, None
tabla = None 


# ----------------------------------------------------------------------
# 2. FUNCIONES DE CONTROL DE LA GUI (MOVIDAS DE UTILS.PY)
# ----------------------------------------------------------------------

def mostrar_frame(nombre):
    """Muestra el frame de la GUI especificado por 'nombre' y oculta los demás."""
    for f in frames.values(): 
        f.pack_forget()
    frames[nombre].pack(fill="both", expand=True)

def actualizar_tabla():
    """Rellena el Treeview 'tabla' con los datos del DataFrame global."""
    global tabla # Aseguramos que estamos usando la tabla global
    if tabla is None: return # Manejar caso donde aún no está inicializada

    tabla.delete(*tabla.get_children())
    if datos_globales.df is None or datos_globales.df.empty:
        tabla["columns"] = []
        return
        
    tabla["columns"] = list(datos_globales.df.columns)
    for col in datos_globales.df.columns:
        tabla.heading(col, text=col)
        tabla.column(col, width=140, anchor="center")
        
    for i, row in datos_globales.df.reset_index(drop=True).iterrows():
        values = [row[col] for col in datos_globales.df.columns]
        tabla.insert("", "end", iid=str(i), values=values)
    
def limpiar_campos_agregar():
    """Limpia el texto de los widgets Entry utilizados para añadir nuevos registros."""
    global entry_nombre, entry_cantidad, entry_anio, entry_provincia
    if entry_nombre: entry_nombre.delete(0, tk.END) 
    if entry_cantidad: entry_cantidad.delete(0, tk.END)
    if entry_anio: entry_anio.delete(0, tk.END)
    if entry_provincia: entry_provincia.delete(0, tk.END)
    

# ----------------------------------------------------------------------
# 3. Importación de Lógica de Otros Módulos
# ----------------------------------------------------------------------
from utils import (
    agregar_animal,
    iniciar_modificar_eliminar, 
)

from funciones_archivo import cargar_excel 
from funciones_graficos import abrir_seleccion_especie_para_grafico 
from funciones_pdf import abrir_seleccion_especie_para_informe 


# ----------------------------------------------------------------------
# 4. Construcción de Frames (Vistas) y Asignación Final de Widgets
# ----------------------------------------------------------------------

def accion_cargar_excel():
  # 1. Ejecuta la lógica de abrir el diálogo y cargar el archivo
    ruta_cargada = cargar_excel() 
    
    # 2. Si la carga fue exitosa, actualiza la GUI
    if ruta_cargada:
        actualizar_tabla() 
        mostrar_frame("tabla")

frame_menu = tk.Frame(root, 
    bg="#FFFFFF", 
    padx=40,            
    pady=40,          
    bd=5,              
    relief=tk.RIDGE)    
frames["menu"] = frame_menu

tk.Label(frame_menu, 
        text="🐸 Menú Principal", 
        font=("Verdana", 26, "bold"), 
        bg="#FFFFFF", 
        fg="#2E7D32").pack(pady=(0, 30))

# Botones usando las funciones (locales e importadas)
ttk.Button(frame_menu, text="1️ Ingresar Excel", width=40, command=accion_cargar_excel).pack(pady=10)
ttk.Button(frame_menu, text="2️ Mostrar Datos", width=40, command=lambda: mostrar_frame("tabla")).pack(pady=8)
ttk.Button(frame_menu, text="3️ Mostrar Gráfico", width=40, command=abrir_seleccion_especie_para_grafico).pack(pady=8)
ttk.Button(frame_menu, text="4️ Ingresar Animal", width=40, command=lambda: mostrar_frame("agregar")).pack(pady=8)
ttk.Button(frame_menu, text="5️ Modificar / Eliminar (seleccionar fila)", width=40, command=lambda: iniciar_modificar_eliminar(tabla, mostrar_frame, root, actualizar_tabla)).pack(pady=8)
ttk.Button(frame_menu, text="6️ Generar Informe PDF", width=40, command=abrir_seleccion_especie_para_informe).pack(pady=8)
ttk.Button(frame_menu, text="7️ Salir", width=40, command=root.quit).pack(pady=8)

# --- Frame Tabla ---
frame_tabla = tk.Frame(root, bg="white")
frames["tabla"] = frame_tabla
tk.Label(frame_tabla, text="📊 Datos del Excel", font=("Verdana", 18, "bold"), bg="white").pack(pady=10)

# ASIGNACIÓN FINAL de la variable global 'tabla'
tabla = ttk.Treeview(frame_tabla, show="headings")
tabla.pack(fill="both", expand=True, padx=20, pady=10)
scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=tabla.yview)
tabla.configure(yscroll=scroll_y.set)
scroll_y.pack(side="right", fill="y")

bot_fila = tk.Frame(frame_tabla, bg="white")
bot_fila.pack(pady=6)
ttk.Button(bot_fila, text="⬅️ Regresar al Menú", command=lambda: mostrar_frame("menu")).pack(side="left", padx=8)
ttk.Button(bot_fila, text="Refrescar tabla", command=actualizar_tabla).pack(side="left", padx=8)
tk.Label(bot_fila, text=" (Seleccione una fila con un clic antes de Modificar/Eliminar)", bg="white").pack(side="left", padx=8)

# --- Frame Agregar ---
frame_agregar = tk.Frame(root, bg="#FFFFFF", padx=30, pady=30, bd=1, relief=tk.SOLID)
frames["agregar"] = frame_agregar
tk.Label(frame_agregar, 
         text="➕ Ingresar Animal", 
         font=("Verdana", 20, "bold"), 
         bg="#FFFFFF", 
         fg="#2E7D32").pack(pady=10)

frm_inputs = tk.Frame(frame_agregar, bg="#FFFFFF")
frm_inputs.pack(pady=6)

# ASIGNACIÓN FINAL CRÍTICA de los Entry widgets globales
tk.Label(frm_inputs, text="Nombre:", bg="#FFFFFF").grid(row=0, column=0, sticky="e", padx=6, pady=6)
entry_nombre = tk.Entry(frm_inputs, width=40)
entry_nombre.grid(row=0, column=1, pady=6)

tk.Label(frm_inputs, text="Cantidad:", bg="#FFFFFF").grid(row=1, column=0, sticky="e", padx=6, pady=6)
entry_cantidad = tk.Entry(frm_inputs, width=40)
entry_cantidad.grid(row=1, column=1, pady=6)

tk.Label(frm_inputs, text="Año:", bg="#FFFFFF").grid(row=2, column=0, sticky="e", padx=6, pady=6)
entry_anio = tk.Entry(frm_inputs, width=40)
entry_anio.grid(row=2, column=1, pady=6)

tk.Label(frm_inputs, text="Provincia:", bg="#FFFFFF").grid(row=3, column=0, sticky="e", padx=6, pady=6)
entry_provincia = tk.Entry(frm_inputs, width=40)
entry_provincia.grid(row=3, column=1, pady=6)

# Botones del Frame Agregar
ttk.Button(frame_agregar, text="Guardar Animal", command=agregar_animal).pack(pady=10)
ttk.Button(frame_agregar, text="⬅️ Regresar al Menú", command=lambda: mostrar_frame("menu")).pack(pady=5)



# ----------------------------------------------------------------------
# 5. INICIO DE LA APLICACIÓN (CRÍTICO)
# ----------------------------------------------------------------------

# Muestra el frame que debe aparecer primero.
mostrar_frame("menu") # Cambiado de "tabla" a "menu" para empezar en el menú.
root.mainloop()