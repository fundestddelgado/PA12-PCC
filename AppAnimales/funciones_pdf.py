from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from tkinter import messagebox
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import ttk
import datos_globales
from utils import actualizar_species_list

def generar_informe(especie):
    """
    Genera un informe en PDF para una 'especie' específica, incluyendo:
    1. Una tabla dinámica de Cantidad por Año y Provincia.
    2. El promedio global de Cantidad por registro.
    3. Una proyección a 3 años basada en una regresión lineal simple.

    Args:
        especie (str): El nombre de la especie para la cual se genera el informe.
    """
    # Se utiliza .copy() para evitar SettingWithCopyWarning
    filtrado = datos_globales.df[datos_globales.df["Especie"] == especie].copy()
    
    if filtrado.empty:
        messagebox.showerror("Error", "No se encontraron registros para esa especie.")
        return

    # 1. Preparación de datos para la tabla dinámica
    # Suma las cantidades por combinación de Año y Provincia
    pivot = filtrado.pivot_table(index="Año", 
                                 columns="Provincia", 
                                 values="Cantidad", 
                                 aggfunc="sum", 
                                 fill_value=0)
    pivot_reset = pivot.reset_index()

    # 2. Cálculo del promedio global (por entradas)
    promedio = int(round(filtrado["Cantidad"].mean()))

    # 3. Proyección simple por regresión lineal
    series_anual = filtrado.groupby("Año", as_index=True)["Cantidad"].sum().sort_index()
    conclusion = "No hay suficientes datos para proyectar tendencia."
    proyeccion_tabla = []
    
    if len(series_anual) > 1:
        x = np.array(series_anual.index.astype(int)) # Años (variable independiente)
        y = np.array(series_anual.values.astype(float)) # Cantidades (variable dependiente)
        
        # Ajusta la recta de regresión lineal (grado 1)
        coef = np.polyfit(x, y, 1)
        pendiente = coef[0]
        
        # Determina la conclusión basada en la pendiente
        if pendiente > 0:
            conclusion = "La población tiende a aumentar."
        elif pendiente < 0:
            conclusion = "La población tiende a disminuir."
        else:
            conclusion = "La población se mantiene estable."
            
        # Proyecta los 3 años siguientes
        ult_a = int(x.max())
        for i in range(1, 4):
            año_fut = ult_a + i
            # np.polyval evalúa el polinomio (la recta) en el año futuro
            valor_fut = int(round(np.polyval(coef, año_fut)))
            proyeccion_tabla.append([año_fut, valor_fut])

    # --- Creación del PDF ---
    nombre_pdf = f"Informe_{especie.replace(' ', '_')}.pdf"
    doc = SimpleDocTemplate(nombre_pdf, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Título y promedio
    elements.append(Paragraph(f"Informe de {especie}", styles["Title"]))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(f"Promedio de cantidad por registro: {promedio}", styles["Normal"]))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Datos por Año y Provincia (sumas):", styles["Heading3"]))
    elements.append(Spacer(1, 6))

    # 4. Armado y estilo de la tabla pivot para el PDF
    encabezado = ["Año"] + list(pivot.columns)
    data_tabla = [encabezado]
    for _, fila in pivot_reset.iterrows():
        # Asegura que todos los valores sean enteros para la presentación
        row = [int(fila["Año"])] + [int(fila[c]) for c in pivot.columns]
        data_tabla.append(row)

    tabla_pdf = Table(data_tabla, hAlign="LEFT")
    tabla_pdf.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4CAF50")), # Encabezado verde
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    elements.append(tabla_pdf)
    elements.append(Spacer(1, 12))

    # 5. Sección de Proyección
    elements.append(Paragraph("Proyección (suma anual) y conclusión:", styles["Heading3"]))
    elements.append(Paragraph(conclusion, styles["Normal"]))
    elements.append(Spacer(1, 6))
    
    if proyeccion_tabla:
        # Armado y estilo de la tabla de proyección
        data_proj = [["Año proyectado", "Cantidad proyectada"]] + proyeccion_tabla
        tabla_proj = Table(data_proj, hAlign="LEFT")
        tabla_proj.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2196F3")), # Encabezado azul
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ]))
        elements.append(tabla_proj)

    # 6. Construcción final del documento
    try:
        doc.build(elements)
        messagebox.showinfo("Éxito", f"Informe generado: {nombre_pdf}")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo generar el PDF:\n{e}")

def abrir_seleccion_especie_para_informe():
    """
    Abre una ventana secundaria (Toplevel) para que el usuario seleccione 
    una especie de un Combobox y luego genere el informe en PDF.
    """
    if datos_globales.df is None or datos_globales.df.empty:
        messagebox.showerror("Error", "No hay datos. Cargue o ingrese animales primero.")
        return

    # Se asume que 'actualizar_species_list' está disponible
    especies = actualizar_species_list()
    
    if not especies:
        messagebox.showerror("Error", "No hay especies disponibles.")
        return
    from main import root 
    # Creación de la ventana de selección (asumiendo tk y ttk están importados)
    win = tk.Toplevel(root) # Asume que 'root' es accesible
    win.title("Seleccione especie para informe")
    win.geometry("350x150")
    tk.Label(win, text="Seleccione la especie:", font=("Arial", 11)).pack(pady=8)
    
    cb = ttk.Combobox(win, values=especies, state="readonly", width=30)
    cb.pack()
    cb.set(especies[0])

    def btn_generar():
        """Función interna para manejar el clic en 'Generar informe'."""
        espec = cb.get()
        win.destroy()
        generar_informe(espec)

    ttk.Button(win, text="Generar informe (PDF)", command=btn_generar).pack(pady=10)