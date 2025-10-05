import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import numpy as np

# -----------------------
# Variables globales
# -----------------------
df = pd.DataFrame(columns=["Especie", "Cantidad", "Año", "Provincia"])
ruta_archivo = None

# -----------------------
# Utilidades
# -----------------------
def asegurar_tipo_numerico(col):
    """Intenta convertir columna a enteros cuando sea posible (evita floats por NaN)."""
    try:
        if col.dtype.kind in "fc":  # float o complex
            # si todos son NaN -> retorna columna como está
            if col.dropna().empty:
                return col
            return col.fillna(0).astype(int)
        return col
    except Exception:
        return col

def actualizar_species_list():
    """Devuelve la lista actual de especies únicas ordenadas (para comboboxes)."""
    if df is None or df.empty:
        return []
    # eliminar valores nulos y devolver únicos ordenados
    return sorted(df["Especie"].dropna().astype(str).unique().tolist())

# -----------------------
# Funciones de archivo
# -----------------------
def cargar_excel():
    global df, ruta_archivo
    ruta = filedialog.askopenfilename(filetypes=[("Archivos Excel", "*.xlsx *.xls")])
    if not ruta:
        return
    try:
        df_temp = pd.read_excel(ruta)
        columnas_validas = ["Especie", "Cantidad", "Año", "Provincia"]
        for col in columnas_validas:
            if col not in df_temp.columns:
                df_temp[col] = ""
        df_temp = df_temp[columnas_validas].copy()
        # normalizar tipos
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
        df = df_temp
        ruta_archivo = ruta
        actualizar_tabla()
        messagebox.showinfo("Éxito", "Archivo cargado exitosamente.")
        mostrar_frame("tabla")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{e}")
# ==============================
# Funciones de navegación
# ==============================
def mostrar_frame(nombre):
    """Muestra un frame y oculta los demás"""
    for f in frames.values():
        f.pack_forget()
    frames[nombre].pack(fill="both", expand=True)

def guardar_excel():
    global df, ruta_archivo
    if ruta_archivo:
        try:
            df.to_excel(ruta_archivo, index=False)
            messagebox.showinfo("Éxito", "Cambios guardados en el archivo.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")
    else:
        ruta = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                            filetypes=[("Archivos Excel", "*.xlsx")])
        if ruta:
            df.to_excel(ruta, index=False)
            ruta_archivo = ruta
            messagebox.showinfo("Éxito", "Archivo guardado exitosamente.")

# -----------------------
# Tabla (Treeview)
# -----------------------
def actualizar_tabla():
    """Rellena el Treeview con los datos de df y actualiza listas dependientes."""
    tabla.delete(*tabla.get_children())
    if df is None or df.empty:
        tabla["columns"] = []
        return
    tabla["columns"] = list(df.columns)
    for col in df.columns:
        tabla.heading(col, text=col)
        tabla.column(col, width=140, anchor="center")
    # usar índice actual del DataFrame como iid (string)
    for i, row in df.reset_index(drop=True).iterrows():
        values = [row[col] for col in df.columns]
        tabla.insert("", "end", iid=str(i), values=values)
    # actualizar comboboxes "selectores" si existen
    # no hay combobox global, las ventanas de selección usan actualizar_species_list()

# -----------------------
# Ingresar Animal (solo aquí se escribe libremente)
# -----------------------
def agregar_animal():
    global df
    especie = entry_nombre.get().strip()
    cantidad = entry_cantidad.get().strip()
    anio = entry_anio.get().strip()
    provincia = entry_provincia.get().strip()

    # validaciones
    if not especie:
        messagebox.showerror("Error", "Ingrese el nombre de la especie.")
        return
    try:
        cantidad_i = int(cantidad)
        anio_i = int(anio)
    except Exception:
        messagebox.showerror("Error", "Cantidad y Año deben ser números enteros.")
        return
    nueva_fila = pd.DataFrame([[especie, cantidad_i, anio_i, provincia]],
                              columns=["Especie", "Cantidad", "Año", "Provincia"])
    df = pd.concat([df, nueva_fila], ignore_index=True)
    actualizar_tabla()
    limpiar_campos_agregar()
    messagebox.showinfo("Éxito", "Animal ingresado correctamente.")

def limpiar_campos_agregar():
    entry_nombre.delete(0, tk.END)
    entry_cantidad.delete(0, tk.END)
    entry_anio.delete(0, tk.END)
    entry_provincia.delete(0, tk.END)

# -----------------------
# Mostrar Gráfico (selección por Combobox readonly)
# -----------------------
def abrir_seleccion_especie_para_grafico():
    if df is None or df.empty:
        messagebox.showerror("Error", "No hay datos. Cargue o ingrese animales primero.")
        return

    especies = actualizar_species_list()
    if not especies:
        messagebox.showerror("Error", "No hay especies disponibles.")
        return

    win = tk.Toplevel(root)
    win.title("Seleccione especie para gráfico")
    win.geometry("350x140")
    tk.Label(win, text="Seleccione la especie:", font=("Arial", 11)).pack(pady=8)
    cb = ttk.Combobox(win, values=especies, state="readonly", width=30)
    cb.pack()
    cb.set(especies[0])

    def btn_mostrar():
        espec = cb.get()
        win.destroy()
        mostrar_grafico(espec)

    ttk.Button(win, text="Mostrar gráfico", command=btn_mostrar).pack(pady=10)


def mostrar_grafico(especie):
    # grafico de barras por año (agregar por año si hay múltiples entradas)
    filtrado = df[df["Especie"] == especie].copy()
    if filtrado.empty:
        messagebox.showerror("Error", "No se encontraron registros para esa especie.")
        return
    agrupado = filtrado.groupby("Año", as_index=True)["Cantidad"].sum().sort_index()
    if agrupado.empty:
        messagebox.showerror("Error", "No hay datos por año para graficar.")
        return
    plt.figure(figsize=(8, 4.5))
    plt.bar(agrupado.index.astype(int), agrupado.values)
    plt.title(f"Evolución de {especie}")
    plt.xlabel("Año")
    plt.ylabel("Cantidad")
    plt.tight_layout()
    plt.show()

# -----------------------
# Modificar / Eliminar (selección desde tabla)
# -----------------------
def iniciar_modificar_eliminar():
    if df is None or df.empty:
        messagebox.showerror("Error", "No hay datos. Cargue o ingrese animales primero.")
        return
    mostrar_frame("tabla")
    seleccion = tabla.selection()
    if not seleccion:
        messagebox.showinfo("Aviso", "Primero seleccione una fila en la tabla (clic sobre la fila) y luego pulse 'Modificar / Eliminar' de nuevo.")
        return
    iid = seleccion[0]
    abrir_dialogo_modificar_eliminar(int(iid))

def abrir_dialogo_modificar_eliminar(idx):
    # idx es el índice del DataFrame según nuestra tabla (reset_index en actualizar_tabla)
    # obtener fila
    try:
        fila = df.reset_index(drop=True).iloc[idx]
    except Exception:
        messagebox.showerror("Error", "Selección inválida.")
        return

    win = tk.Toplevel(root)
    win.title("Modificar o Eliminar registro")
    win.geometry("420x320")

    tk.Label(win, text="Registro seleccionado", font=("Arial", 12, "bold")).pack(pady=6)
    # Mostrar valores actuales
    frame_info = tk.Frame(win)
    frame_info.pack(pady=4)
    labels = ["Especie", "Cantidad", "Año", "Provincia"]
    for i, col in enumerate(labels):
        tk.Label(frame_info, text=f"{col}:", anchor="w", width=12).grid(row=i, column=0, sticky="w", padx=6, pady=4)
        tk.Label(frame_info, text=str(fila[col]), anchor="w", width=25, bg="white", relief="sunken").grid(row=i, column=1, padx=6, pady=4)

    def accion_eliminar():
        confirm = messagebox.askyesno("Confirmar", "¿Eliminar este registro?")
        if confirm:
            # eliminar del DataFrame original: localizar la fila por contenido y posición
            # Mejor eliminar por índice real: hallar el índice real en df
            try:
                # obtener index en df original usando condiciones de igualdad
                condiciones = (df["Especie"] == fila["Especie"]) & (df["Cantidad"] == fila["Cantidad"]) & (df["Año"] == fila["Año"]) & (df["Provincia"] == fila["Provincia"])
                indices = df[condiciones].index
                if len(indices) > 0:
                    df.drop(indices[0], inplace=True)
                    df.reset_index(drop=True, inplace=True)
                else:
                    # fallback: eliminar por posición (solo si indices no coincide)
                    df.drop(df.index[idx], inplace=True)
                    df.reset_index(drop=True, inplace=True)
            except Exception:
                messagebox.showerror("Error", "No se pudo eliminar el registro.")
                return
            actualizar_tabla()
            messagebox.showinfo("Éxito", "Registro eliminado.")
            win.destroy()

    def accion_modificar():
        win_mod = tk.Toplevel(win)
        win_mod.title("Modificar registro")
        win_mod.geometry("420x360")

        tk.Label(win_mod, text="Edite los campos y presione Guardar", font=("Arial", 11)).pack(pady=6)
        frm = tk.Frame(win_mod)
        frm.pack(pady=6)

        tk.Label(frm, text="Especie:").grid(row=0, column=0, sticky="e", pady=6, padx=6)
        ent_especie = tk.Entry(frm, width=30)
        ent_especie.grid(row=0, column=1, pady=6)
        ent_especie.insert(0, str(fila["Especie"]))

        tk.Label(frm, text="Cantidad:").grid(row=1, column=0, sticky="e", pady=6, padx=6)
        ent_cantidad = tk.Entry(frm, width=30)
        ent_cantidad.grid(row=1, column=1, pady=6)
        ent_cantidad.insert(0, str(fila["Cantidad"]))

        tk.Label(frm, text="Año:").grid(row=2, column=0, sticky="e", pady=6, padx=6)
        ent_anio = tk.Entry(frm, width=30)
        ent_anio.grid(row=2, column=1, pady=6)
        ent_anio.insert(0, str(fila["Año"]))

        tk.Label(frm, text="Provincia:").grid(row=3, column=0, sticky="e", pady=6, padx=6)
        ent_prov = tk.Entry(frm, width=30)
        ent_prov.grid(row=3, column=1, pady=6)
        ent_prov.insert(0, str(fila["Provincia"]))

        def guardar_cambios():
            nuevo_nombre = ent_especie.get().strip()
            try:
                nuevo_cant = int(ent_cantidad.get())
                nuevo_anio = int(ent_anio.get())
            except Exception:
                messagebox.showerror("Error", "Cantidad y Año deben ser números enteros.")
                return
            nueva_prov = ent_prov.get().strip()
            # localizar índice real en df original similar a eliminar
            try:
                condiciones = (df["Especie"] == fila["Especie"]) & (df["Cantidad"] == fila["Cantidad"]) & (df["Año"] == fila["Año"]) & (df["Provincia"] == fila["Provincia"])
                indices = df[condiciones].index
                if len(indices) > 0:
                    idx_real = indices[0]
                else:
                    idx_real = df.index[idx]  # fallback por posición
                df.at[idx_real, "Especie"] = nuevo_nombre
                df.at[idx_real, "Cantidad"] = nuevo_cant
                df.at[idx_real, "Año"] = nuevo_anio
                df.at[idx_real, "Provincia"] = nueva_prov
                actualizar_tabla()
                messagebox.showinfo("Éxito", "Registro modificado.")
                win_mod.destroy()
                win.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar: {e}")

        ttk.Button(win_mod, text="Guardar", command=guardar_cambios).pack(pady=12)
        ttk.Button(win_mod, text="Cancelar", command=win_mod.destroy).pack()

    # botones principales
    frame_bot = tk.Frame(win)
    frame_bot.pack(pady=12)
    ttk.Button(frame_bot, text="Modificar", command=accion_modificar, width=12).grid(row=0, column=0, padx=8)
    ttk.Button(frame_bot, text="Eliminar", command=accion_eliminar, width=12).grid(row=0, column=1, padx=8)
    ttk.Button(frame_bot, text="Cerrar", command=win.destroy, width=12).grid(row=0, column=2, padx=8)

# -----------------------
# Generar informe PDF (selección con combobox readonly)
# -----------------------
def abrir_seleccion_especie_para_informe():
    if df is None or df.empty:
        messagebox.showerror("Error", "No hay datos. Cargue o ingrese animales primero.")
        return

    especies = actualizar_species_list()
    if not especies:
        messagebox.showerror("Error", "No hay especies disponibles.")
        return

    win = tk.Toplevel(root)
    win.title("Seleccione especie para informe")
    win.geometry("350x150")
    tk.Label(win, text="Seleccione la especie:", font=("Arial", 11)).pack(pady=8)
    cb = ttk.Combobox(win, values=especies, state="readonly", width=30)
    cb.pack()
    cb.set(especies[0])

    def btn_generar():
        espec = cb.get()
        win.destroy()
        generar_informe(espec)

    ttk.Button(win, text="Generar informe (PDF)", command=btn_generar).pack(pady=10)


def generar_informe(especie):
    filtrado = df[df["Especie"] == especie].copy()
    if filtrado.empty:
        messagebox.showerror("Error", "No se encontraron registros para esa especie.")
        return

    # preparar datos: tabla por año y provincia (suma de cantidades)
    pivot = filtrado.pivot_table(index="Año", columns="Provincia", values="Cantidad", aggfunc="sum", fill_value=0)
    pivot_reset = pivot.reset_index()

    # promedio global (por entradas)
    promedio = int(round(filtrado["Cantidad"].mean()))

    # proyección simple por año: usar la suma por año y regresión lineal
    series_anual = filtrado.groupby("Año", as_index=True)["Cantidad"].sum().sort_index()
    conclusion = "No hay suficientes datos para proyectar tendencia."
    proyeccion_tabla = []
    if len(series_anual) > 1:
        x = np.array(series_anual.index.astype(int))
        y = np.array(series_anual.values.astype(float))
        # ajustar recta
        coef = np.polyfit(x, y, 1)
        pendiente = coef[0]
        if pendiente > 0:
            conclusion = "La población tiende a aumentar."
        elif pendiente < 0:
            conclusion = "La población tiende a disminuir."
        else:
            conclusion = "La población se mantiene estable."
        # proyectar 3 años siguientes
        ult_a = int(x.max())
        for i in range(1, 4):
            año_fut = ult_a + i
            valor_fut = int(round(np.polyval(coef, año_fut)))
            proyeccion_tabla.append([año_fut, valor_fut])

    # crear PDF
    nombre_pdf = f"Informe_{especie.replace(' ', '_')}.pdf"
    doc = SimpleDocTemplate(nombre_pdf, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"Informe de {especie}", styles["Title"]))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(f"Promedio de cantidad por registro: {promedio}", styles["Normal"]))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Datos por Año y Provincia (sumas):", styles["Heading3"]))
    elements.append(Spacer(1, 6))

    # armar tabla pivot
    encabezado = ["Año"] + list(pivot.columns)
    data_tabla = [encabezado]
    for _, fila in pivot_reset.iterrows():
        row = [int(fila["Año"])] + [int(fila[c]) for c in pivot.columns]
        data_tabla.append(row)

    tabla_pdf = Table(data_tabla, hAlign="LEFT")
    tabla_pdf.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4CAF50")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    elements.append(tabla_pdf)
    elements.append(Spacer(1, 12))

    # proyección
    elements.append(Paragraph("Proyección (suma anual) y conclusión:", styles["Heading3"]))
    elements.append(Paragraph(conclusion, styles["Normal"]))
    elements.append(Spacer(1, 6))
    if proyeccion_tabla:
        data_proj = [["Año proyectado", "Cantidad proyectada"]] + proyeccion_tabla
        tabla_proj = Table(data_proj, hAlign="LEFT")
        tabla_proj.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2196F3")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ]))
        elements.append(tabla_proj)

    try:
        doc.build(elements)
        messagebox.showinfo("Éxito", f"Informe generado: {nombre_pdf}")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo generar el PDF:\n{e}")

# -----------------------
# Interfaz principal
# -----------------------
root = tk.Tk()
root.title("Animales en Peligro de Extinción")
root.geometry("1000x600")
root.configure(bg="#E8F5E9")

frames = {}

# --- Menú Principal ---
frame_menu = tk.Frame(root, bg="#E8F5E9")
frames["menu"] = frame_menu
tk.Label(frame_menu, text="🐾 Menú Principal", font=("Arial", 22, "bold"), bg="#E8F5E9").pack(pady=20)

tk.Button(frame_menu, text="1 Ingresar Excel", width=40, height=2, bg="#4CAF50", fg="white",
          command=cargar_excel).pack(pady=8)
tk.Button(frame_menu, text="2 Mostrar Datos", width=40, height=2, bg="#2196F3", fg="white",
          command=lambda: mostrar_frame("tabla")).pack(pady=8)
tk.Button(frame_menu, text="3 Mostrar Gráfico", width=40, height=2, bg="#9C27B0", fg="white",
          command=abrir_seleccion_especie_para_grafico).pack(pady=8)
tk.Button(frame_menu, text="4 Ingresar Animal", width=40, height=2, bg="#8BC34A", fg="white",
          command=lambda: mostrar_frame("agregar")).pack(pady=8)
tk.Button(frame_menu, text="5 Modificar / Eliminar (seleccionar fila)", width=40, height=2, bg="#FFC107", fg="black",
          command=iniciar_modificar_eliminar).pack(pady=8)
tk.Button(frame_menu, text="6 Generar Informe PDF", width=40, height=2, bg="#795548", fg="white",
          command=abrir_seleccion_especie_para_informe).pack(pady=8)
tk.Button(frame_menu, text="7 Salir", width=40, height=2, bg="#000000", fg="white", command=root.quit).pack(pady=8)

# --- Frame Tabla ---
frame_tabla = tk.Frame(root, bg="white")
frames["tabla"] = frame_tabla
tk.Label(frame_tabla, text="📊 Datos del Excel", font=("Arial", 18, "bold"), bg="white").pack(pady=10)

tabla = ttk.Treeview(frame_tabla, show="headings")
tabla.pack(fill="both", expand=True, padx=20, pady=10)
scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical", command=tabla.yview)
tabla.configure(yscroll=scroll_y.set)
scroll_y.pack(side="right", fill="y")

bot_fila = tk.Frame(frame_tabla, bg="white")
bot_fila.pack(pady=6)
tk.Button(bot_fila, text="⬅ Regresar al Menú", bg="#FF9800", fg="black",
          command=lambda: mostrar_frame("menu")).pack(side="left", padx=8)
tk.Button(bot_fila, text="Refrescar tabla", bg="#2196F3", fg="white",
          command=actualizar_tabla).pack(side="left", padx=8)
tk.Label(bot_fila, text=" (Seleccione una fila con un clic antes de Modificar/Eliminar)", bg="white").pack(side="left", padx=8)

# --- Frame Agregar ---
frame_agregar = tk.Frame(root, bg="#F1F8E9")
frames["agregar"] = frame_agregar
tk.Label(frame_agregar, text="➕ Ingresar Animal", font=("Arial", 18, "bold"), bg="#F1F8E9").pack(pady=10)

frm_inputs = tk.Frame(frame_agregar, bg="#F1F8E9")
frm_inputs.pack(pady=6)
tk.Label(frm_inputs, text="Nombre:", bg="#F1F8E9").grid(row=0, column=0, sticky="e", padx=6, pady=6)
entry_nombre = tk.Entry(frm_inputs, width=40)
entry_nombre.grid(row=0, column=1, pady=6)

tk.Label(frm_inputs, text="Cantidad:", bg="#F1F8E9").grid(row=1, column=0, sticky="e", padx=6, pady=6)
entry_cantidad = tk.Entry(frm_inputs, width=40)
entry_cantidad.grid(row=1, column=1, pady=6)

tk.Label(frm_inputs, text="Año:", bg="#F1F8E9").grid(row=2, column=0, sticky="e", padx=6, pady=6)
entry_anio = tk.Entry(frm_inputs, width=40)
entry_anio.grid(row=2, column=1, pady=6)

tk.Label(frm_inputs, text="Provincia:", bg="#F1F8E9").grid(row=3, column=0, sticky="e", padx=6, pady=6)
entry_provincia = tk.Entry(frm_inputs, width=40)
entry_provincia.grid(row=3, column=1, pady=6)

tk.Button(frame_agregar, text="Agregar", bg="#4CAF50", fg="white", command=agregar_animal).pack(pady=10)
tk.Button(frame_agregar, text="⬅ Regresar", bg="#FF9800", command=lambda: mostrar_frame("menu")).pack(pady=6)

# Mostrar pantalla inicial
mostrar_frame("menu")
root.mainloop()
