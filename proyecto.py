import os
import tempfile
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import numpy as np

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False


df = pd.DataFrame(columns=["Especie", "Cantidad", "Año", "Provincia"])
ruta_archivo = None
logo_img_tk = None

# Lista de especies y provincias permitidas (según tu petición)
ESPECIES_PERMITIDAS = [
    "Jaguar",
    "Manatí del Caribe",
    "Tapir Centroamericano",
    "Tortuga Carey",
    "Águila Harpía"
]

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

# -----------------------
# Utilidades
# -----------------------
def asegurar_tipo_numerico(col):
    """Intenta convertir columna a enteros cuando sea posible (evita floats por NaN)."""
    try:
        if col.dtype.kind in "fc":  # float o complex
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
    return sorted(df["Especie"].dropna().astype(str).unique().tolist())

# -----------------------
# Validaciones
# -----------------------
def validar_especie(especie):
    """Verifica que la especie esté en la lista permitida."""
    if especie in ESPECIES_PERMITIDAS:
        return True
    return False

def validar_cantidad(cantidad_texto):
    """Verifica que la cantidad sea un entero positivo (>=0)."""
    try:
        v = int(cantidad_texto)
        return v >= 0
    except Exception:
        return False

def validar_anio(anio_texto):
    """Verifica formato de año: exactamente 4 dígitos entre 1000 y 9999 (puedes ajustar rango)."""
    if not anio_texto.isdigit() or len(anio_texto) != 4:
        return False
    try:
        v = int(anio_texto)
        return 1000 <= v <= 9999
    except Exception:
        return False

def validar_provincia(prov):
    """Verifica que la provincia esté dentro de las provincias de Panamá definidas."""
    return prov in PROVINCIAS_PANAMA

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
    # tabla principal (frame_tabla)
    tabla.delete(*tabla.get_children())
    if df is None or df.empty:
        tabla["columns"] = []
    else:
        tabla["columns"] = list(df.columns)
        for col in df.columns:
            tabla.heading(col, text=col)
            tabla.column(col, width=160, anchor="center")
        for i, row in df.reset_index(drop=True).iterrows():
            values = [row[col] for col in df.columns]
            tabla.insert("", "end", iid=str(i), values=values)

    # tabla del panel modificar (si existe)
    try:
        tabla_mod.delete(*tabla_mod.get_children())
        if df is None or df.empty:
            tabla_mod["columns"] = []
        else:
            tabla_mod["columns"] = list(df.columns)
            for col in df.columns:
                tabla_mod.heading(col, text=col)
                tabla_mod.column(col, width=140, anchor="center")
            for i, row in df.reset_index(drop=True).iterrows():
                values = [row[col] for col in df.columns]
                tabla_mod.insert("", "end", iid=str(i), values=values)
    except Exception:
        # tabla_mod puede no existir aún ( antes de crear frame modificar )
        pass

# -----------------------
# Ingresar Animal
# -----------------------
def agregar_animal():
    global df
    especie = entry_nombre.get().strip()
    cantidad = entry_cantidad.get().strip()
    anio = entry_anio.get().strip()
    provincia = entry_provincia.get().strip()

    # Validaciones añadidas: solo especies/provincias permitidas
    if not especie:
        messagebox.showerror("Error", "Ingrese el nombre de la especie.")
        return
    if not validar_especie(especie):
        messagebox.showerror("Error", f"Especie no permitida. Especies permitidas:\n{', '.join(ESPECIES_PERMITIDAS)}")
        return
    if not validar_cantidad(cantidad):
        messagebox.showerror("Error", "Cantidad debe ser un número entero >= 0.")
        return
    if not validar_anio(anio):
        messagebox.showerror("Error", "Año inválido. Debe tener formato de 4 dígitos, p.ej. 2045.")
        return
    if not validar_provincia(provincia):
        messagebox.showerror("Error", f"Provincia inválida. Provincias permitidas:\n{', '.join(PROVINCIAS_PANAMA)}")
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
# Mostrar Gráfico
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
    win.geometry("360x150")
    tk.Label(win, text="Seleccione la especie:", font=("Arial", 11)).pack(pady=8)
    cb = ttk.Combobox(win, values=especies, state="readonly", width=32)
    cb.pack()
    cb.set(especies[0])

    def btn_mostrar():
        espec = cb.get()
        win.destroy()
        mostrar_grafico(espec)

    ttk.Button(win, text="Mostrar gráfico", command=btn_mostrar).pack(pady=10)

def mostrar_grafico(especie, guardar_png=None):
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
    if guardar_png:
        plt.savefig(guardar_png, bbox_inches="tight")
        plt.close()
        return guardar_png
    else:
        plt.show()

# -----------------------
# Modificar / Eliminar (nuevo panel)
# -----------------------
def iniciar_modificar_eliminar():
    """Muestra el frame 'modificar' que contiene una tabla completa y panel de edición."""
    # asegurar que exista contenido o al menos la tabla
    if df is None:
        messagebox.showerror("Error", "No hay datos. Cargue o ingrese animales primero.")
        return
    mostrar_frame("modificar")

def on_mod_select(event):
    """Cuando el usuario selecciona una fila en la tabla de modificar, rellenar los campos."""
    sel = tabla_mod.selection()
    if not sel:
        return
    try:
        idx = int(sel[0])
        fila = df.reset_index(drop=True).iloc[idx]
        mod_entry_nombre_var.set(str(fila["Especie"]))
        mod_entry_cantidad_var.set(str(int(fila["Cantidad"])))
        mod_entry_anio_var.set(str(int(fila["Año"])))
        mod_entry_prov_var.set(str(fila["Provincia"]))
    except Exception:
        # selección inválida
        pass

def accion_eliminar_mod():
    sel = tabla_mod.selection()
    if not sel:
        messagebox.showinfo("Aviso", "Seleccione primero una fila a eliminar.")
        return
    idx = int(sel[0])
    confirm = messagebox.askyesno("Confirmar", "¿Eliminar este registro seleccionado?")
    if not confirm:
        return
    try:
        # eliminar por índice real (respetando el df actual)
        df.drop(df.index[idx], inplace=True)
        df.reset_index(drop=True, inplace=True)
        actualizar_tabla()
        messagebox.showinfo("Éxito", "Registro eliminado.")
        # limpiar campos del panel modificar
        mod_entry_nombre_var.set("")
        mod_entry_cantidad_var.set("")
        mod_entry_anio_var.set("")
        mod_entry_prov_var.set("")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo eliminar: {e}")

def accion_modificar_mod():
    sel = tabla_mod.selection()
    if not sel:
        messagebox.showinfo("Aviso", "Seleccione primero una fila a modificar.")
        return
    idx = int(sel[0])
    nuevo_nombre = mod_entry_nombre_var.get().strip()
    nuevo_cant = mod_entry_cantidad_var.get().strip()
    nuevo_anio = mod_entry_anio_var.get().strip()
    nueva_prov = mod_entry_prov_var.get().strip()

    # Validaciones
    if not nuevo_nombre:
        messagebox.showerror("Error", "Ingrese el nombre de la especie.")
        return
    if not validar_especie(nuevo_nombre):
        messagebox.showerror("Error", f"Especie no permitida. Especies permitidas:\n{', '.join(ESPECIES_PERMITIDAS)}")
        return
    if not validar_cantidad(nuevo_cant):
        messagebox.showerror("Error", "Cantidad debe ser un número entero >= 0.")
        return
    if not validar_anio(nuevo_anio):
        messagebox.showerror("Error", "Año inválido. Debe tener formato de 4 dígitos, p.ej. 2045.")
        return
    if not validar_provincia(nueva_prov):
        messagebox.showerror("Error", f"Provincia inválida. Provincias permitidas:\n{', '.join(PROVINCIAS_PANAMA)}")
        return

    try:
        df.at[df.index[idx], "Especie"] = nuevo_nombre
        df.at[df.index[idx], "Cantidad"] = int(nuevo_cant)
        df.at[df.index[idx], "Año"] = int(nuevo_anio)
        df.at[df.index[idx], "Provincia"] = nueva_prov
        df.reset_index(drop=True, inplace=True)
        actualizar_tabla()
        messagebox.showinfo("Éxito", "Registro modificado correctamente.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo guardar la modificación: {e}")

# También permitir doble-clic en una fila para abrir edición rápida (mantener compatibilidad)
def on_double_click(event):
    item = tabla.selection()
    if item:
        try:
            abrir_dialogo_modificar_eliminar(int(item[0]))
        except Exception:
            pass

# Mantener la función de diálogo original por compatibilidad; la dejamos sin cambios funcionales
def abrir_dialogo_modificar_eliminar(idx):
    try:
        fila = df.reset_index(drop=True).iloc[idx]
    except Exception:
        messagebox.showerror("Error", "Selección inválida.")
        return

    win = tk.Toplevel(root)
    win.title("Modificar o Eliminar registro")
    win.geometry("460x360")
    win.configure(bg="#F7F9F8")

    tk.Label(win, text="Registro seleccionado", font=("Arial", 12, "bold"), bg="#F7F9F8").pack(pady=6)
    frame_info = tk.Frame(win, bg="#F7F9F8")
    frame_info.pack(pady=4)
    labels = ["Especie", "Cantidad", "Año", "Provincia"]
    campos_actuales = []
    for i, col in enumerate(labels):
        tk.Label(frame_info, text=f"{col}:", anchor="w", width=12, bg="#F7F9F8").grid(row=i, column=0, sticky="w", padx=6, pady=4)
        ent = tk.Entry(frame_info, width=30)
        ent.grid(row=i, column=1, padx=6, pady=4)
        ent.insert(0, str(fila[col]))
        campos_actuales.append(ent)

    def accion_eliminar():
        confirm = messagebox.askyesno("Confirmar", "¿Eliminar este registro?")
        if confirm:
            try:
                condiciones = (df["Especie"] == fila["Especie"]) & (df["Cantidad"] == fila["Cantidad"]) & (df["Año"] == fila["Año"]) & (df["Provincia"] == fila["Provincia"])
                indices = df[condiciones].index
                if len(indices) > 0:
                    df.drop(indices[0], inplace=True)
                else:
                    df.drop(df.index[idx], inplace=True)
                df.reset_index(drop=True, inplace=True)
            except Exception:
                messagebox.showerror("Error", "No se pudo eliminar el registro.")
                return
            actualizar_tabla()
            messagebox.showinfo("Éxito", "Registro eliminado.")
            win.destroy()

    def accion_modificar():
        try:
            nuevo_nombre = campos_actuales[0].get().strip()
            nuevo_cant = int(campos_actuales[1].get())
            nuevo_anio = int(campos_actuales[2].get())
            nueva_prov = campos_actuales[3].get().strip()
        except Exception:
            messagebox.showerror("Error", "Cantidad y Año deben ser números enteros.")
            return

        # Validaciones AL USAR EL DIALOGO TAMBIEN
        if not validar_especie(nuevo_nombre):
            messagebox.showerror("Error", f"Especie no permitida. Especies permitidas:\n{', '.join(ESPECIES_PERMITIDAS)}")
            return
        if not validar_provincia(nueva_prov):
            messagebox.showerror("Error", f"Provincia inválida. Provincias permitidas:\n{', '.join(PROVINCIAS_PANAMA)}")
            return
        if len(str(nuevo_anio)) != 4:
            messagebox.showerror("Error", "Año inválido. Debe tener formato de 4 dígitos.")
            return

        try:
            condiciones = (df["Especie"] == fila["Especie"]) & (df["Cantidad"] == fila["Cantidad"]) & (df["Año"] == fila["Año"]) & (df["Provincia"] == fila["Provincia"])
            indices = df[condiciones].index
            if len(indices) > 0:
                idx_real = indices[0]
            else:
                idx_real = df.index[idx]
            df.at[idx_real, "Especie"] = nuevo_nombre
            df.at[idx_real, "Cantidad"] = nuevo_cant
            df.at[idx_real, "Año"] = nuevo_anio
            df.at[idx_real, "Provincia"] = nueva_prov
            actualizar_tabla()
            messagebox.showinfo("Éxito", "Registro modificado.")
            win.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

    frame_bot = tk.Frame(win, bg="#F7F9F8")
    frame_bot.pack(pady=12)
    ttk.Style().configure("Bot.TButton", padding=6)
    ttk.Button(frame_bot, text="Modificar", command=accion_modificar, width=12).grid(row=0, column=0, padx=8)
    ttk.Button(frame_bot, text="Eliminar", command=accion_eliminar, width=12).grid(row=0, column=1, padx=8)
    ttk.Button(frame_bot, text="Cerrar", command=win.destroy, width=12).grid(row=0, column=2, padx=8)

# -----------------------
# Generar informe PDF (con gráfica y estadísticas)
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
    win.geometry("360x150")
    tk.Label(win, text="Seleccione la especie:", font=("Arial", 11)).pack(pady=8)
    cb = ttk.Combobox(win, values=especies, state="readonly", width=32)
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

    # Estadísticas básicas
    cantidades = filtrado["Cantidad"].astype(float)
    promedio = float(cantidades.mean()) if not cantidades.empty else 0.0
    varianza = float(cantidades.var(ddof=0)) if not cantidades.empty else 0.0
    desv = float(cantidades.std(ddof=0)) if not cantidades.empty else 0.0
    minimo = float(cantidades.min()) if not cantidades.empty else 0.0
    maximo = float(cantidades.max()) if not cantidades.empty else 0.0
    mediana = float(cantidades.median()) if not cantidades.empty else 0.0

    # preparar datos: pivot por año y provincia (suma)
    pivot = filtrado.pivot_table(index="Año", columns="Provincia", values="Cantidad", aggfunc="sum", fill_value=0)
    pivot_reset = pivot.reset_index()

    # proyección simple por año: suma por año y regresión lineal
    series_anual = filtrado.groupby("Año", as_index=True)["Cantidad"].sum().sort_index()
    conclusion = "No hay suficientes datos para proyectar tendencia."
    proyeccion_tabla = []
    if len(series_anual) > 1:
        x = np.array(series_anual.index.astype(int))
        y = np.array(series_anual.values.astype(float))
        coef = np.polyfit(x, y, 1)
        pendiente = coef[0]
        if pendiente > 0:
            conclusion = "La población tiende a aumentar."
        elif pendiente < 0:
            conclusion = "La población tiende a disminuir."
        else:
            conclusion = "La población se mantiene estable."
        ult_a = int(x.max())
        for i in range(1, 4):
            año_fut = ult_a + i
            valor_fut = int(round(np.polyval(coef, año_fut)))
            proyeccion_tabla.append([año_fut, valor_fut])

    # crear gráfica y guardarla temporalmente
    tmp_dir = tempfile.gettempdir()
    nombre_png = os.path.join(tmp_dir, f"grafico_{especie.replace(' ', '_')}.png")
    try:
        mostrar_grafico(especie, guardar_png=nombre_png)
    except Exception:
        # fallback: crear una gráfica mínima si falla
        plt.figure(figsize=(6, 3))
        plt.text(0.5, 0.5, "No se pudo generar gráfico", ha="center", va="center")
        plt.axis("off")
        plt.savefig(nombre_png, bbox_inches="tight")
        plt.close()

    # crear PDF
    nombre_pdf = f"Informe_{especie.replace(' ', '_')}.pdf"
    doc = SimpleDocTemplate(nombre_pdf, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    styleN = styles["Normal"]
    styleH = styles["Heading2"]

    elements.append(Paragraph(f"Informe de {especie}", styles["Title"]))
    elements.append(Spacer(1, 8))

    # Estadísticas (formato legible)
    stats_paragraph = (
        f"<b>Estadísticas (sobre 'Cantidad'):</b><br/>"
        f"Promedio: {promedio:.2f} &nbsp;&nbsp;|&nbsp;&nbsp; Varianza: {varianza:.2f} &nbsp;&nbsp;|&nbsp;&nbsp; Desv. Estándar: {desv:.2f}<br/>"
        f"Mínimo: {minimo:.0f} &nbsp;&nbsp;|&nbsp;&nbsp; Máximo: {maximo:.0f} &nbsp;&nbsp;|&nbsp;&nbsp; Mediana: {mediana:.2f}"
    )
    elements.append(Paragraph(stats_paragraph, styleN))
    elements.append(Spacer(1, 8))

    # Insertar la gráfica
    try:
        # Escalar la imagen para que quepa en la página
        img = RLImage(nombre_png, width=460, height=230)
        elements.append(img)
        elements.append(Spacer(1, 10))
    except Exception:
        elements.append(Paragraph("No se pudo insertar la gráfica en el PDF.", styleN))
        elements.append(Spacer(1, 6))

    # Tabla pivot
    elements.append(Paragraph("Datos por Año y Provincia (sumas):", styles["Heading3"]))
    elements.append(Spacer(1, 6))

    encabezado = ["Año"] + list(pivot.columns)
    data_tabla = [encabezado]
    for _, fila in pivot_reset.iterrows():
        row = [int(fila["Año"])] + [int(fila[c]) for c in pivot.columns]
        data_tabla.append(row)

    if len(data_tabla) == 1:
        elements.append(Paragraph("No hay datos tabulares para mostrar.", styleN))
    else:
        tabla_pdf = Table(data_tabla, hAlign="LEFT")
        tabla_pdf.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4CAF50")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ]))
        elements.append(tabla_pdf)
    elements.append(Spacer(1, 12))

    # Proyección y conclusión
    elements.append(Paragraph("Proyección (suma anual) y conclusión:", styles["Heading3"]))
    elements.append(Paragraph(conclusion, styleN))
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
    finally:
        # intentar eliminar la gráfica temporal
        try:
            if os.path.exists(nombre_png):
                os.remove(nombre_png)
        except Exception:
            pass

# -----------------------
# Interfaz principal y estilo
# -----------------------
root = tk.Tk()
root.title("Animales en Peligro de Extinción - Mejora")
root.geometry("1100x680")
root.configure(bg="#EAF5EF")

# Estilos ttk
style = ttk.Style(root)
style.theme_use('clam')  # tema más moderno disponible en muchas instalaciones
style.configure("TButton", font=("Arial", 10, "bold"), padding=6)
style.configure("TLabel", font=("Arial", 10))
style.configure("Treeview", font=("Arial", 10), rowheight=24)
style.configure("Treeview.Heading", font=("Arial", 11, "bold"))

frames = {}

# Cargar logo si existe
def cargar_logo_si_existe():
    global logo_img_tk
    posible = ["logo.png", "logo.gif", "logo.ico"]
    for nombre in posible:
        if os.path.exists(nombre):
            try:
                if PIL_AVAILABLE:
                    img = Image.open(nombre)
                    img = img.resize((120, 120), Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.ANTIALIAS)
                    logo_img_tk = ImageTk.PhotoImage(img)
                else:
                    logo_img_tk = tk.PhotoImage(file=nombre)
                return True
            except Exception:
                continue
    logo_img_tk = None
    return False

cargar_logo_si_existe()

# --- Menú Principal ---
frame_menu = tk.Frame(root, bg="#EAF5EF")
frames["menu"] = frame_menu
frame_menu.pack(fill="both", expand=True)

tk.Label(frame_menu, text="🐾 Menú Principal", font=("Arial", 26, "bold"), bg="#EAF5EF").pack(pady=18)

# contenedor de botones con estilo
btn_frame = tk.Frame(frame_menu, bg="#EAF5EF")
btn_frame.pack(pady=6)

tk.Button(btn_frame, text="1️ Ingresar Excel", width=36, height=2, bg="#4CAF50", fg="white",
          command=cargar_excel, relief="raised").grid(row=0, column=0, padx=12, pady=8)
tk.Button(btn_frame, text="2️ Mostrar Datos", width=36, height=2, bg="#2196F3", fg="white",
          command=lambda: mostrar_frame("tabla"), relief="raised").grid(row=1, column=0, padx=12, pady=8)
# redirigimos a nuevo frame 'modificar' en lugar de abrir directamente el dialogo
tk.Button(btn_frame, text="3️ Mostrar Gráfico", width=36, height=2, bg="#9C27B0", fg="white",
          command=abrir_seleccion_especie_para_grafico, relief="raised").grid(row=2, column=0, padx=12, pady=8)
tk.Button(btn_frame, text="4️ Ingresar Animal", width=36, height=2, bg="#8BC34A", fg="white",
          command=lambda: mostrar_frame("agregar"), relief="raised").grid(row=3, column=0, padx=12, pady=8)
tk.Button(btn_frame, text="5️ Modificar / Eliminar (seleccionar fila)", width=36, height=2, bg="#FFC107", fg="black",
          command=iniciar_modificar_eliminar, relief="raised").grid(row=4, column=0, padx=12, pady=8)
tk.Button(btn_frame, text="6️ Generar Informe PDF", width=36, height=2, bg="#795548", fg="white",
          command=abrir_seleccion_especie_para_informe, relief="raised").grid(row=5, column=0, padx=12, pady=8)
tk.Button(btn_frame, text="7️ Guardar Excel", width=36, height=2, bg="#3E8E41", fg="white",
          command=guardar_excel, relief="raised").grid(row=6, column=0, padx=12, pady=8)
tk.Button(btn_frame, text="8️ Salir", width=36, height=2, bg="#000000", fg="white", command=root.quit, relief="raised").grid(row=7, column=0, padx=12, pady=8)

# logo en esquina superior derecha (si existe)
if logo_img_tk:
    lbl_logo = tk.Label(frame_menu, image=logo_img_tk, bg="#EAF5EF")
    lbl_logo.place(x=940, y=18)
else:
    # mostrar texto decorativo en caso de no haber logo
    tk.Label(frame_menu, text="🌿 Conservación", font=("Arial", 12, "italic"), bg="#EAF5EF").place(x=930, y=40)

# --- Frame Tabla ---
frame_tabla = tk.Frame(root, bg="white")
frames["tabla"] = frame_tabla
tk.Label(frame_tabla, text="📊 Datos del Excel", font=("Arial", 20, "bold"), bg="white").pack(pady=10)

tabla_frame = tk.Frame(frame_tabla, bg="white")
tabla_frame.pack(fill="both", expand=True, padx=12, pady=6)

scroll_y = ttk.Scrollbar(tabla_frame, orient="vertical")
scroll_x = ttk.Scrollbar(tabla_frame, orient="horizontal")

tabla = ttk.Treeview(tabla_frame, show="headings", yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
scroll_y.config(command=tabla.yview)
scroll_x.config(command=tabla.xview)
scroll_y.pack(side="right", fill="y")
scroll_x.pack(side="bottom", fill="x")
tabla.pack(fill="both", expand=True)

bot_fila = tk.Frame(frame_tabla, bg="white")
bot_fila.pack(pady=8)
tk.Button(bot_fila, text="⬅️ Regresar al Menú", bg="#FF9800", fg="black",
          command=lambda: mostrar_frame("menu")).pack(side="left", padx=8)
tk.Button(bot_fila, text="Refrescar tabla", bg="#2196F3", fg="white",
          command=actualizar_tabla).pack(side="left", padx=8)
tk.Label(bot_fila, text=" (Seleccione una fila con un clic antes de Modificar/Eliminar)", bg="white").pack(side="left", padx=8)

# enlazar doble-clic
tabla.bind("<Double-1>", on_double_click)

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
tk.Button(frame_agregar, text="⬅️ Regresar", bg="#FF9800", command=lambda: mostrar_frame("menu")).pack(pady=6)

# -----------------------
# Frame Modificar/Eliminar (nuevo dentro de la interfaz principal)
# -----------------------
frame_modificar = tk.Frame(root, bg="#F5F5F5")
frames["modificar"] = frame_modificar
tk.Label(frame_modificar, text="✏️ Modificar / 🗑️ Eliminar Registros", font=("Arial", 18, "bold"), bg="#F5F5F5").pack(pady=10)

mod_table_frame = tk.Frame(frame_modificar, bg="#F5F5F5")
mod_table_frame.pack(fill="both", expand=True, padx=12, pady=6)

scroll_y_m = ttk.Scrollbar(mod_table_frame, orient="vertical")
scroll_x_m = ttk.Scrollbar(mod_table_frame, orient="horizontal")

tabla_mod = ttk.Treeview(mod_table_frame, show="headings", yscrollcommand=scroll_y_m.set, xscrollcommand=scroll_x_m.set)
scroll_y_m.config(command=tabla_mod.yview)
scroll_x_m.config(command=tabla_mod.xview)
scroll_y_m.pack(side="right", fill="y")
scroll_x_m.pack(side="bottom", fill="x")
tabla_mod.pack(fill="both", expand=True)

# panel de edición en el mismo frame
panel_edicion = tk.Frame(frame_modificar, bg="#F5F5F5")
panel_edicion.pack(pady=10)

tk.Label(panel_edicion, text="Especie:", bg="#F5F5F5").grid(row=0, column=0, sticky="e", padx=6, pady=4)
mod_entry_nombre_var = tk.StringVar()
mod_entry_nombre = ttk.Combobox(panel_edicion, textvariable=mod_entry_nombre_var, values=ESPECIES_PERMITIDAS, state="readonly", width=36)
mod_entry_nombre.grid(row=0, column=1, pady=4)
mod_entry_nombre_var.set(ESPECIES_PERMITIDAS[0])

tk.Label(panel_edicion, text="Cantidad:", bg="#F5F5F5").grid(row=1, column=0, sticky="e", padx=6, pady=4)
mod_entry_cantidad_var = tk.StringVar()
mod_entry_cantidad = tk.Entry(panel_edicion, textvariable=mod_entry_cantidad_var, width=38)
mod_entry_cantidad.grid(row=1, column=1, pady=4)

tk.Label(panel_edicion, text="Año:", bg="#F5F5F5").grid(row=2, column=0, sticky="e", padx=6, pady=4)
mod_entry_anio_var = tk.StringVar()
mod_entry_anio = tk.Entry(panel_edicion, textvariable=mod_entry_anio_var, width=38)
mod_entry_anio.grid(row=2, column=1, pady=4)

tk.Label(panel_edicion, text="Provincia:", bg="#F5F5F5").grid(row=3, column=0, sticky="e", padx=6, pady=4)
mod_entry_prov_var = tk.StringVar()
mod_entry_prov = ttk.Combobox(panel_edicion, textvariable=mod_entry_prov_var, values=PROVINCIAS_PANAMA, state="readonly", width=36)
mod_entry_prov.grid(row=3, column=1, pady=4)
mod_entry_prov_var.set(PROVINCIAS_PANAMA[0])

botones_mod = tk.Frame(frame_modificar, bg="#F5F5F5")
botones_mod.pack(pady=8)
ttk.Button(botones_mod, text="Modificar seleccionado", command=accion_modificar_mod, width=20).grid(row=0, column=0, padx=8)
ttk.Button(botones_mod, text="Eliminar seleccionado", command=accion_eliminar_mod, width=20).grid(row=0, column=1, padx=8)
tk.Button(botones_mod, text="⬅️ Regresar al Menú", bg="#FF9800", command=lambda: mostrar_frame("menu")).grid(row=0, column=2, padx=8)

# enlazar selección en tabla_mod a llenado de campos
tabla_mod.bind("<<TreeviewSelect>>", on_mod_select)

# -----------------------
# Mostrar / ocultar frames
# -----------------------
def mostrar_frame(nombre):
    for f in frames.values():
        f.pack_forget()
    frames[nombre].pack(fill="both", expand=True)

# Mostrar pantalla inicial
mostrar_frame("menu")

# Inicializar tabla vacía
actualizar_tabla()

# Lanzar GUI
root.mainloop()
