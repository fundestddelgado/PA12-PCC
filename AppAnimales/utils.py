import pandas as pd
import tkinter as tk
from tkinter import messagebox, ttk 
import datos_globales 

# ----------------------------------------------------------------------
# 1. FUNCIONES AUXILIARES DE LÓGICA
# ----------------------------------------------------------------------

def asegurar_tipo_numerico(col):
    """
    Intenta convertir una Serie de pandas (columna) a números enteros (int) 
    cuando el tipo original es float o complex, rellenando NaN con 0.
    """
    try:
        if col.dtype.kind in "fc":  # float ('f') o complex ('c')
            if col.dropna().empty:
                return col
            return col.fillna(0).astype(int) 
        return col
    except Exception:
        return col

def actualizar_species_list():
    """
    Devuelve la lista actual de especies únicas, filtrando nulos y ordenándolas
    alfabéticamente. 
    """
    if datos_globales.df is None or datos_globales.df.empty:
        return []
    # Elimina valores nulos, asegura que sean strings, obtiene únicos y ordena
    return sorted(datos_globales.df["Especie"].dropna().astype(str).unique().tolist())


# ----------------------------------------------------------------------
# 2. FUNCIONES DE LÓGICA DE NEGOCIO (Usando Importación Local de main)
# ----------------------------------------------------------------------

def iniciar_modificar_eliminar(tabla_widget, mostrar_frame_func, root_window, actualizar_tabla_func):
    """
    Inicia el flujo de modificación o eliminación: verifica la existencia de datos 
    y que haya una fila seleccionada en el Treeview 'tabla'. 
    """ 
    if datos_globales.df is None or datos_globales.df.empty:
        messagebox.showerror("Error", "No hay datos. Cargue o ingrese animales primero.")
        return
        
    mostrar_frame_func("tabla") 
    seleccion = tabla_widget.selection()
    
    if not seleccion:
        messagebox.showinfo("Aviso", "Primero seleccione una fila en la tabla (clic sobre la fila) y luego pulse 'Modificar / Eliminar' de nuevo.")
        return
    iid = seleccion[0]
    abrir_dialogo_modificar_eliminar(int(iid), root_window, actualizar_tabla_func)

def abrir_dialogo_modificar_eliminar(idx, root_window, actualizar_tabla_func):
    """
    Abre una ventana Toplevel para Modificar o Eliminar el registro seleccionado.
    """  
    try:
        datos_globales.df["Especie"] = datos_globales.df["Especie"].astype(str)
        fila = datos_globales.df.reset_index(drop=True).iloc[idx]
    except Exception:
        messagebox.showerror("Error", "Selección inválida.")
        return

    win = tk.Toplevel(root_window) # Usa 'root' importada localmente
    win.title("Modificar o Eliminar registro")
    win.geometry("420x320")

    tk.Label(win, text="Registro seleccionado", font=("Arial", 12, "bold")).pack(pady=6)
    
    def accion_eliminar():
        confirm = messagebox.askyesno("Confirmar", "¿Eliminar este registro?")
        if confirm:
            try:
                # Lógica de eliminación usando df de datos_globales
                condiciones = (datos_globales.df["Especie"] == fila["Especie"]) & (datos_globales.df["Cantidad"] == fila["Cantidad"]) & (datos_globales.df["Año"] == fila["Año"]) & (datos_globales.df["Provincia"] == fila["Provincia"])
                indices = datos_globales.df[condiciones].index
                if len(indices) > 0:
                    datos_globales.df.drop(indices[0], inplace=True)
                else:
                    datos_globales.df.drop(datos_globales.df.index[idx], inplace=True)
                
                datos_globales.df.reset_index(drop=True, inplace=True)
            except Exception:
                messagebox.showerror("Error", "No se pudo eliminar el registro.")
                return
            actualizar_tabla_func() 
            messagebox.showinfo("Éxito", "Registro eliminado.")
            win.destroy()
    
    def accion_modificar():
        win_mod = tk.Toplevel(win)
        win_mod.title("Modificar registro")
        win_mod.geometry("420x360")

        tk.Label(win_mod, text="Edite los campos y presione Guardar", font=("Arial", 11)).pack(pady=6)
        frm = tk.Frame(win_mod)
        frm.pack(pady=6)

        # Definición de los Entry widgets (no son los globales, son locales)
        tk.Label(frm, text="Especie:").grid(row=0, column=0, sticky="e", pady=6, padx=6)
        ent_especie = tk.Entry(frm, width=30)
        ent_especie.grid(row=0, column=1, pady=6)
        ent_especie.insert(0, str(fila["Especie"]))
        # ... (resto de Entry widgets) ...
        tk.Label(frm, text="Cantidad:").grid(row=1, column=0, sticky="e", pady=6, padx=6)
        ent_cantidad = tk.Entry(frm, width=30)
        ent_cantidad.grid(row=1, column=1, pady=6)
        ent_cantidad.insert(0, str(fila["Cantidad"]))

        tk.Label(frm, text="Año:").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        ent_anio = tk.Entry(frm, width=30)
        ent_anio.grid(row=2, column=1, pady=6)
        ent_anio.insert(0, str(fila["Año"]))

        tk.Label(frm, text="Provincia:").grid(row=3, column=0, sticky="e", padx=6, pady=6)
        ent_prov = tk.Entry(frm, width=30)
        ent_prov.grid(row=3, column=1, pady=6)
        ent_prov.insert(0, str(fila["Provincia"]))


        def guardar_cambios():
            # ... (Lógica de validación) ...
            nuevo_nombre = ent_especie.get().strip()
            try:
                nuevo_cant = int(ent_cantidad.get())
                nuevo_anio = int(ent_anio.get())
            except Exception:
                messagebox.showerror("Error", "Cantidad y Año deben ser números enteros.")
                return
            nueva_prov = ent_prov.get().strip()
            
            try:
                # Modificación de datos globales
                condiciones = (datos_globales.df["Especie"] == fila["Especie"]) & (datos_globales.df["Cantidad"] == fila["Cantidad"]) & (datos_globales.df["Año"] == fila["Año"]) & (datos_globales.df["Provincia"] == fila["Provincia"])
                indices = datos_globales.df[condiciones].index
                idx_real = indices[0] if len(indices) > 0 else datos_globales.df.index[idx]
                
                datos_globales.df.at[idx_real, "Especie"] = nuevo_nombre
                datos_globales.df.at[idx_real, "Cantidad"] = nuevo_cant
                datos_globales.df.at[idx_real, "Año"] = nuevo_anio
                datos_globales.df.at[idx_real, "Provincia"] = nueva_prov
                
                actualizar_tabla_func()
                messagebox.showinfo("Éxito", "Registro modificado.")
                win_mod.destroy()
                win.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar: {e}")

        ttk.Button(win_mod, text="Guardar", command=guardar_cambios).pack(pady=12)
        ttk.Button(win_mod, text="Cancelar", command=win_mod.destroy).pack()

    # ... (Botones y labels de info) ...
    frame_info = tk.Frame(win)
    frame_info.pack(pady=4)
    labels = ["Especie", "Cantidad", "Año", "Provincia"]
    for i, col in enumerate(labels):
        tk.Label(frame_info, text=f"{col}:", anchor="w", width=12).grid(row=i, column=0, sticky="w", padx=6, pady=4)
        tk.Label(frame_info, text=str(fila[col]), anchor="w", width=25, bg="white", relief="sunken").grid(row=i, column=1, padx=6, pady=4)
    
    frame_bot = tk.Frame(win)
    frame_bot.pack(pady=12)
    ttk.Button(frame_bot, text="Modificar", command=accion_modificar, width=12).grid(row=0, column=0, padx=8)
    ttk.Button(frame_bot, text="Eliminar", command=accion_eliminar, width=12).grid(row=0, column=1, padx=8)
    ttk.Button(frame_bot, text="Cerrar", command=win.destroy, width=12).grid(row=0, column=2, padx=8)


def agregar_animal(entry_nombre_widget, entry_cantidad_widget, entry_anio_widget, entry_provincia_widget, actualizar_tabla_func, limpiar_campos_func):
    """
    Valida las entradas de los campos, crea una nueva fila, la añade al 
    DataFrame global y actualiza la GUI.
    """
    especie = entry_nombre_widget.get().strip()
    cantidad = entry_cantidad_widget.get().strip()
    anio = entry_anio_widget.get().strip()
    provincia = entry_provincia_widget.get().strip()

    # Validación de datos
    if not especie:
        messagebox.showerror("Error", "Ingrese el nombre de la especie.")
        return
    try:
        cantidad_i = int(cantidad)
        anio_i = int(anio)
    except Exception:
        messagebox.showerror("Error", "Cantidad y Año deben ser números enteros.")
        return
        
    # Concatenación del nuevo registro al DataFrame
    nueva_fila = pd.DataFrame([[especie, cantidad_i, anio_i, provincia]],
                              columns=["Especie", "Cantidad", "Año", "Provincia"])
    datos_globales.df = pd.concat([datos_globales.df, nueva_fila], ignore_index=True)
    
    actualizar_tabla_func()
    limpiar_campos_func()
    messagebox.showinfo("Éxito", "Animal ingresado correctamente.")