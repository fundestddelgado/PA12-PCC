import pandas as pd
from tkinter import filedialog, messagebox
import datos_globales # Contiene df y ruta_archivo

# ¡IMPORTANTE! Eliminamos todas las referencias a funciones de la GUI para evitar
# que se importe y ejecute 'main.py' de nuevo.

def cargar_excel():
    """
    Abre un diálogo para seleccionar un archivo Excel (.xlsx/.xls), lo lee 
    en un DataFrame de pandas, valida y normaliza las columnas esenciales, 
    y actualiza las variables globales df y ruta_archivo.
    
    Returns:
        str | None: La ruta del archivo si la carga fue exitosa, None en caso contrario.
    """
    
    # Abre el diálogo de selección de archivo
    ruta = filedialog.askopenfilename(filetypes=[("Archivos Excel", "*.xlsx *.xls")])
    if not ruta:
        return None # Indica que el usuario canceló
    
    try:
        df_temp = pd.read_excel(ruta)
        columnas_validas = ["Especie", "Cantidad", "Año", "Provincia"]
        
        # 1. Asegura la existencia de las columnas clave
        for col in columnas_validas:
            if col not in df_temp.columns:
                df_temp[col] = "" # Añade columnas faltantes con valores vacíos
        
        # 2. Reordena y toma solo las columnas válidas (hace una copia limpia)
        df_temp = df_temp[columnas_validas].copy()
        
        # 3. Normaliza tipos de datos para 'Cantidad' y 'Año'
        if "Cantidad" in df_temp:
            try:
                df_temp["Cantidad"] = pd.to_numeric(df_temp["Cantidad"], errors="coerce").fillna(0).astype(int)
            except Exception:
                pass
        if "Año" in df_temp:
            try:
                df_temp["Año"] = pd.to_numeric(df_temp["Año"], errors="coerce").fillna(0).astype(int)
            except Exception:
                pass
                
        # 4. Asigna el nuevo DataFrame y la ruta al atributo del módulo.
        datos_globales.df = df_temp
        datos_globales.ruta_archivo = ruta
        
        # Eliminamos: actualizar_tabla() y mostrar_frame("tabla") aquí.
        messagebox.showinfo("Éxito", "Archivo cargado exitosamente.")
        
        return ruta # Retorna la ruta para que main.py sepa que fue exitoso
        
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{e}")
        return None # Retorna None en caso de error

def guardar_excel():
    """
    Guarda el DataFrame global (df) en un archivo Excel.
    """
    if datos_globales.ruta_archivo:
        # Guardar en la ruta existente
        try:
            datos_globales.df.to_excel(datos_globales.ruta_archivo, index=False)
            messagebox.showinfo("Éxito", "Cambios guardados en el archivo.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")
    else:
        # Pedir ruta de guardado por primera vez
        ruta = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                             filetypes=[("Archivos Excel", "*.xlsx")])
        if ruta:
            datos_globales.df.to_excel(ruta, index=False)
            datos_globales.ruta_archivo = ruta 
            messagebox.showinfo("Éxito", "Archivo guardado exitosamente.")