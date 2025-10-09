# -*- coding: utf-8 -*-
"""
Sistema de Gestión de Animales en Peligro de Extinción
Versión Refactorizada con Arquitectura MVC
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import logging
from typing import Optional, List, Tuple
from datetime import datetime

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTES
# ============================================================================

PROVINCIAS_PANAMA = [
    "Bocas del Toro", "Chiriquí", "Coclé", "Colón", "Darién",
    "Herrera", "Los Santos", "Panamá", "Veraguas", "Panamá Oeste"
]

ESPECIES_PANAMA = [
    "Águila Arpía",
    "Jaguar",
    "Perezoso de Tres Dedos",
    "Tapir Centroamericano",
    "Tortuga Carey",
    "Rana Dorada",
]

COLUMNAS_REQUERIDAS = ["Especie", "Cantidad", "Año", "Provincia"]

# Paleta de colores moderna
COLORS = {
    'primary': '#2E7D32',
    'primary_dark': '#1B5E20',
    'primary_light': '#4CAF50',
    'accent': '#FF6F00',
    'background': '#F5F5F5',
    'card': '#FFFFFF',
    'text': '#212121',
    'text_light': '#757575',
    'success': '#4CAF50',
    'error': '#D32F2F',
    'warning': '#FFA000'
}

# ============================================================================
# MODELO - Lógica de Negocio
# ============================================================================

class GestorAnimales:
    """Maneja la lógica de negocio y los datos de animales en peligro."""

    def __init__(self):
        self.df = pd.DataFrame(columns=COLUMNAS_REQUERIDAS)
        self.ruta_archivo: Optional[str] = None
        self.cambios_sin_guardar = False
        logger.info("GestorAnimales inicializado")

    def cargar_excel(self, ruta: str) -> Tuple[bool, str]:
        """
        Carga datos desde un archivo Excel.

        Returns:
            Tuple[bool, str]: (éxito, mensaje)
        """
        try:
            df_temp = pd.read_excel(ruta)

            # Validar y normalizar columnas
            for col in COLUMNAS_REQUERIDAS:
                if col not in df_temp.columns:
                    df_temp[col] = ""

            df_temp = df_temp[COLUMNAS_REQUERIDAS].copy()

            # Normalizar tipos de datos
            df_temp["Cantidad"] = pd.to_numeric(
                df_temp["Cantidad"], errors="coerce"
            ).fillna(0).astype(int)
            df_temp["Año"] = pd.to_numeric(
                df_temp["Año"], errors="coerce"
            ).fillna(0).astype(int)
            df_temp["Especie"] = df_temp["Especie"].astype(str).str.strip()
            df_temp["Provincia"] = df_temp["Provincia"].astype(str).str.strip()

            # Validar provincias
            df_temp = self._validar_provincias(df_temp)

            self.df = df_temp
            self.ruta_archivo = ruta
            self.cambios_sin_guardar = False

            logger.info(f"Archivo cargado: {ruta} ({len(self.df)} registros)")
            return True, f"Archivo cargado: {len(self.df)} registros"

        except Exception as e:
            logger.error(f"Error al cargar archivo: {e}")
            return False, f"Error al cargar: {str(e)}"

    def _validar_provincias(self, df: pd.DataFrame) -> pd.DataFrame:
        """Valida y corrige nombres de provincias."""
        def corregir_provincia(prov):
            prov = str(prov).strip()
            if prov in PROVINCIAS_PANAMA:
                return prov
            # Buscar coincidencia parcial
            for p in PROVINCIAS_PANAMA:
                if prov.lower() in p.lower() or p.lower() in prov.lower():
                    return p
            return prov  # Mantener original si no hay coincidencia

        df["Provincia"] = df["Provincia"].apply(corregir_provincia)
        return df

    def guardar_excel(self, ruta: Optional[str] = None) -> Tuple[bool, str]:
        """
        Guarda el DataFrame en un archivo Excel.

        Args:
            ruta: Ruta del archivo. Si es None, usa la ruta actual.
        """
        try:
            ruta_final = ruta or self.ruta_archivo
            if not ruta_final:
                return False, "No se especificó una ruta de archivo"

            self.df.to_excel(ruta_final, index=False)
            self.ruta_archivo = ruta_final
            self.cambios_sin_guardar = False

            logger.info(f"Archivo guardado: {ruta_final}")
            return True, "Archivo guardado exitosamente"

        except Exception as e:
            logger.error(f"Error al guardar: {e}")
            return False, f"Error al guardar: {str(e)}"

    def agregar_registro(self, especie: str, cantidad: int,
                        año: int, provincia: str) -> Tuple[bool, str]:
        """Agrega un nuevo registro al DataFrame."""
        # Validaciones
        if not especie or not especie.strip():
            return False, "Debe seleccionar una especie"

        if especie not in ESPECIES_PANAMA:
            return False, "Especie no válida. Debe seleccionar de la lista"

        if cantidad < 0:
            return False, "La cantidad debe ser positiva"

        if not (1900 <= año <= 2100):
            return False, "El año debe estar entre 1900 y 2100"

        if provincia not in PROVINCIAS_PANAMA:
            return False, "Provincia no válida"

        try:
            nueva_fila = pd.DataFrame([[
                especie.strip(), cantidad, año, provincia
            ]], columns=COLUMNAS_REQUERIDAS)

            self.df = pd.concat([self.df, nueva_fila], ignore_index=True)
            self.cambios_sin_guardar = True

            logger.info(f"Registro agregado: {especie}")
            return True, "Registro agregado correctamente"

        except Exception as e:
            logger.error(f"Error al agregar registro: {e}")
            return False, f"Error: {str(e)}"

    def modificar_registro(self, idx: int, especie: str, cantidad: int,
                          año: int, provincia: str) -> Tuple[bool, str]:
        """Modifica un registro existente."""
        if not (0 <= idx < len(self.df)):
            return False, "Índice inválido"

        # Validaciones (mismas que agregar)
        if not especie or not especie.strip():
            return False, "Debe seleccionar una especie"
        if especie not in ESPECIES_PANAMA:
            return False, "Especie no válida. Debe seleccionar de la lista"
        if cantidad < 0:
            return False, "La cantidad debe ser positiva"
        if not (1900 <= año <= 2100):
            return False, "El año debe estar entre 1900 y 2100"
        if provincia not in PROVINCIAS_PANAMA:
            return False, "Provincia no válida"

        try:
            self.df.at[idx, "Especie"] = especie.strip()
            self.df.at[idx, "Cantidad"] = int(cantidad)
            self.df.at[idx, "Año"] = int(año)
            self.df.at[idx, "Provincia"] = provincia
            self.cambios_sin_guardar = True

            logger.info(f"Registro {idx} modificado")
            return True, "Registro modificado correctamente"

        except Exception as e:
            logger.error(f"Error al modificar: {e}")
            return False, f"Error: {str(e)}"

    def eliminar_registro(self, idx: int) -> Tuple[bool, str]:
        """Elimina un registro del DataFrame."""
        if not (0 <= idx < len(self.df)):
            return False, "Índice inválido"

        try:
            especie = self.df.at[idx, "Especie"]
            self.df = self.df.drop(idx).reset_index(drop=True)
            self.cambios_sin_guardar = True

            logger.info(f"Registro eliminado: {especie}")
            return True, "Registro eliminado correctamente"

        except Exception as e:
            logger.error(f"Error al eliminar: {e}")
            return False, f"Error: {str(e)}"

    def obtener_especies(self) -> List[str]:
        """Retorna lista de especies únicas ordenadas."""
        if self.df.empty:
            return []
        return sorted(self.df["Especie"].dropna().unique().tolist())

    def obtener_datos_especie(self, especie: str) -> pd.DataFrame:
        """Retorna datos filtrados por especie."""
        return self.df[self.df["Especie"] == especie].copy()

    def calcular_estadisticas(self, especie: str) -> dict:
        """Calcula estadísticas para una especie."""
        datos = self.obtener_datos_especie(especie)

        if datos.empty:
            return {}

        # Agrupar por año
        por_año = datos.groupby("Año")["Cantidad"].sum().sort_index()

        # Regresión lineal para tendencia
        if len(por_año) > 1:
            x = np.array(por_año.index)
            y = np.array(por_año.values)
            coef = np.polyfit(x, y, 1)
            pendiente = coef[0]

            if pendiente > 5:
                tendencia = "Aumento significativo"
            elif pendiente > 0:
                tendencia = "Aumento moderado"
            elif pendiente < -5:
                tendencia = "Disminución significativa"
            elif pendiente < 0:
                tendencia = "Disminución moderada"
            else:
                tendencia = "Estable"

            # Proyecciones
            ultimo_año = int(x.max())
            proyecciones = []
            for i in range(1, 4):
                año_futuro = ultimo_año + i
                valor = int(round(np.polyval(coef, año_futuro)))
                proyecciones.append((año_futuro, max(0, valor)))
        else:
            tendencia = "Datos insuficientes"
            proyecciones = []

        return {
            'promedio': int(datos["Cantidad"].mean()),
            'total': int(datos["Cantidad"].sum()),
            'registros': len(datos),
            'tendencia': tendencia,
            'proyecciones': proyecciones,
            'por_año': por_año.to_dict(),
            'por_provincia': datos.groupby("Provincia")["Cantidad"].sum().to_dict()
        }

# ============================================================================
# VISTA - Interfaz Gráfica
# ============================================================================

class InterfazPrincipal:
    """Interfaz gráfica principal de la aplicación."""

    def __init__(self, gestor: GestorAnimales):
        self.gestor = gestor
        self.root = tk.Tk()
        self.root.title("🐸 Gestión de Animales en Peligro de Extinción")
        self.root.geometry("1200x700")
        self.root.configure(bg=COLORS['background'])

        # Configurar estilos
        self._configurar_estilos()

        # Frames principales
        self.frames = {}
        self._crear_frames()

        # Widgets
        self.tabla = None
        self.entries = {}

        # Construir interfaz
        self._construir_menu()
        self._construir_tabla()
        self._construir_formulario()
        self._construir_visualizacion()

        # Mostrar menu inicial
        self.mostrar_frame("menu")

        # Protocolo de cierre
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        logger.info("Interfaz inicializada")

    def _configurar_estilos(self):
        """Configura estilos ttk mejorados."""
        style = ttk.Style()
        style.theme_use('clam')

        # Botones
        style.configure('TButton',
            font=('Segoe UI', 10),
            padding=[20, 12],
            background=COLORS['primary'],
            foreground='white',
            borderwidth=0,
            focuscolor='none')
        style.map('TButton',
            background=[('active', COLORS['primary_dark']),
                       ('pressed', COLORS['primary_dark'])])

        # Botón de acento
        style.configure('Accent.TButton',
            background=COLORS['accent'],
            foreground='white')
        style.map('Accent.TButton',
            background=[('active', '#E65100')])

        # Tabla
        style.configure("Treeview",
            font=('Segoe UI', 10),
            rowheight=30,
            fieldbackground=COLORS['card'],
            background=COLORS['card'])
        style.configure("Treeview.Heading",
            font=('Segoe UI', 11, 'bold'),
            background=COLORS['primary'],
            foreground='white',
            relief='flat')
        style.map('Treeview',
            background=[('selected', COLORS['primary_light'])],
            foreground=[('selected', 'white')])

    def _crear_frames(self):
        """Crea los frames principales."""
        for nombre in ["menu", "tabla", "formulario", "visualizacion"]:
            frame = tk.Frame(self.root, bg=COLORS['background'])
            self.frames[nombre] = frame

    def mostrar_frame(self, nombre: str):
        """Muestra el frame especificado."""
        for frame in self.frames.values():
            frame.pack_forget()
        self.frames[nombre].pack(fill="both", expand=True)

    def _construir_menu(self):
        """Construye el menú principal."""
        frame = self.frames["menu"]

        # Contenedor central
        container = tk.Frame(frame, bg=COLORS['card'], padx=60, pady=40)
        container.place(relx=0.5, rely=0.5, anchor="center")

        # Título con emoji
        titulo = tk.Label(container,
            text="🐸 Animales en Peligro",
            font=('Segoe UI', 32, 'bold'),
            bg=COLORS['card'],
            fg=COLORS['primary'])
        titulo.pack(pady=(0, 10))

        subtitulo = tk.Label(container,
            text="Sistema de Gestión y Análisis",
            font=('Segoe UI', 14),
            bg=COLORS['card'],
            fg=COLORS['text_light'])
        subtitulo.pack(pady=(0, 40))

        # Botones del menú
        opciones = [
            ("📁 Cargar Base de Datos", self._accion_cargar, 'TButton'),
            ("📊 Ver Base de Datos", lambda: self._mostrar_tabla(), 'TButton'),
            ("📈 Visualización y Gráficos", lambda: self.mostrar_frame("visualizacion"), 'TButton'),
            ("➕ Agregar Registro", lambda: self.mostrar_frame("formulario"), 'TButton'),
            ("📄 Generar Informe PDF", self._accion_generar_informe, 'Accent.TButton'),
            ("💾 Guardar Cambios", self._accion_guardar, 'TButton'),
            ("❌ Salir", self._on_closing, 'TButton')
        ]

        for texto, comando, estilo in opciones:
            btn = ttk.Button(container, text=texto, command=comando,
                           width=35, style=estilo)
            btn.pack(pady=8)

        # Indicador de cambios
        self.label_estado = tk.Label(frame,
            text="",
            font=('Segoe UI', 10),
            bg=COLORS['background'],
            fg=COLORS['warning'])
        self.label_estado.pack(side="bottom", pady=10)

    def _construir_tabla(self):
        """Construye la vista de tabla."""
        frame = self.frames["tabla"]

        # Header
        header = tk.Frame(frame, bg=COLORS['primary'], height=80)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header,
            text="📊 Base de Datos",
            font=('Segoe UI', 20, 'bold'),
            bg=COLORS['primary'],
            fg='white').pack(side="left", padx=20, pady=20)

        # Botones de acción en header
        btn_frame = tk.Frame(header, bg=COLORS['primary'])
        btn_frame.pack(side="right", padx=20)

        ttk.Button(btn_frame, text="🔄 Refrescar",
                  command=self._actualizar_tabla).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="⬅️ Menú",
                  command=lambda: self.mostrar_frame("menu")).pack(side="left", padx=5)

        # Contenedor de tabla
        table_frame = tk.Frame(frame, bg=COLORS['background'])
        table_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Scrollbars
        scroll_y = ttk.Scrollbar(table_frame, orient="vertical")
        scroll_x = ttk.Scrollbar(table_frame, orient="horizontal")

        # Tabla
        self.tabla = ttk.Treeview(table_frame,
            columns=COLUMNAS_REQUERIDAS,
            show="headings",
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set)

        scroll_y.config(command=self.tabla.yview)
        scroll_x.config(command=self.tabla.xview)

        # Configurar columnas
        for col in COLUMNAS_REQUERIDAS:
            self.tabla.heading(col, text=col)
            self.tabla.column(col, width=200, anchor="center")

        # Layout
        self.tabla.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Doble clic para editar
        self.tabla.bind("<Double-1>", self._on_tabla_doble_clic)

        # Botones de acciones
        btn_container = tk.Frame(frame, bg=COLORS['background'])
        btn_container.pack(fill="x", padx=20, pady=(0, 20))

        ttk.Button(btn_container, text="✏️ Modificar Seleccionado",
                  command=self._accion_modificar).pack(side="left", padx=5)
        ttk.Button(btn_container, text="🗑️ Eliminar Seleccionado",
                  command=self._accion_eliminar).pack(side="left", padx=5)

    def _construir_formulario(self):
        """Construye el formulario de entrada."""
        frame = self.frames["formulario"]

        # Header
        header = tk.Frame(frame, bg=COLORS['primary'], height=80)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header,
            text="➕ Agregar Nuevo Registro",
            font=('Segoe UI', 20, 'bold'),
            bg=COLORS['primary'],
            fg='white').pack(side="left", padx=20, pady=20)

        # Formulario
        form_container = tk.Frame(frame, bg=COLORS['card'])
        form_container.place(relx=0.5, rely=0.5, anchor="center")

        # Campos
        campos = [
            ("Especie:", "especie", "combo"),
            ("Cantidad:", "cantidad", "entry"),
            ("Año:", "año", "entry"),
            ("Provincia:", "provincia", "combo")
        ]

        for i, (label, key, tipo) in enumerate(campos):
            tk.Label(form_container,
                text=label,
                font=('Segoe UI', 12),
                bg=COLORS['card'],
                fg=COLORS['text']).grid(row=i, column=0, sticky="e",
                                       padx=20, pady=15)

            if tipo == "entry":
                widget = tk.Entry(form_container,
                    font=('Segoe UI', 11),
                    width=30,
                    relief='solid',
                    borderwidth=1)
            else:  # combo
                if key == "especie":
                    valores = ESPECIES_PANAMA
                else:
                    valores = PROVINCIAS_PANAMA

                widget = ttk.Combobox(form_container,
                    values=valores,
                    state="readonly",
                    font=('Segoe UI', 11),
                    width=28)
                widget.set(valores[0])

            widget.grid(row=i, column=1, padx=20, pady=15)
            self.entries[key] = widget

        # Botones
        btn_frame = tk.Frame(form_container, bg=COLORS['card'])
        btn_frame.grid(row=len(campos), column=0, columnspan=2, pady=30)

        ttk.Button(btn_frame, text="💾 Guardar",
                  command=self._accion_agregar,
                  style='Accent.TButton').pack(side="left", padx=10)
        ttk.Button(btn_frame, text="🔄 Limpiar",
                  command=self._limpiar_formulario).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="⬅️ Menú",
                  command=lambda: self.mostrar_frame("menu")).pack(side="left", padx=10)

    def _construir_visualizacion(self):
        """Construye la vista de visualización con gráficos mejorados."""
        frame = self.frames["visualizacion"]

        # Header
        header = tk.Frame(frame, bg=COLORS['primary'], height=80)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header,
            text="📈 Visualización y Análisis",
            font=('Segoe UI', 20, 'bold'),
            bg=COLORS['primary'],
            fg='white').pack(side="left", padx=20, pady=20)

        ttk.Button(header, text="⬅️ Menú",
                  command=lambda: self.mostrar_frame("menu")).pack(
                      side="right", padx=20)

        # Contenedor principal
        main_container = tk.Frame(frame, bg=COLORS['background'])
        main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # Panel de control
        control_panel = tk.Frame(main_container, bg=COLORS['card'])
        control_panel.pack(fill="x", pady=(0, 20))

        tk.Label(control_panel,
            text="Seleccione especie:",
            font=('Segoe UI', 12),
            bg=COLORS['card']).pack(side="left", padx=20, pady=15)

        self.combo_especies = ttk.Combobox(control_panel,
            state="readonly",
            font=('Segoe UI', 11),
            width=30)
        self.combo_especies.pack(side="left", padx=10, pady=15)
        self.combo_especies.bind("<<ComboboxSelected>>",
                                lambda e: self._actualizar_visualizacion())

        ttk.Button(control_panel, text="📊 Mostrar Gráficos",
                  command=self._actualizar_visualizacion,
                  style='Accent.TButton').pack(side="left", padx=10)

        # Área de gráficos y estadísticas
        content_frame = tk.Frame(main_container, bg=COLORS['background'])
        content_frame.pack(fill="both", expand=True)

        # Panel izquierdo: Estadísticas
        stats_frame = tk.Frame(content_frame, bg=COLORS['card'], width=300)
        stats_frame.pack(side="left", fill="both", padx=(0, 10))
        stats_frame.pack_propagate(False)

        tk.Label(stats_frame,
            text="📊 Estadísticas",
            font=('Segoe UI', 14, 'bold'),
            bg=COLORS['card'],
            fg=COLORS['primary']).pack(pady=15)

        self.stats_text = tk.Text(stats_frame,
            font=('Segoe UI', 10),
            bg=COLORS['card'],
            relief='flat',
            wrap='word',
            state='disabled')
        self.stats_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Panel derecho: Gráficos
        graph_frame = tk.Frame(content_frame, bg=COLORS['card'])
        graph_frame.pack(side="right", fill="both", expand=True)

        self.canvas_frame = graph_frame

    def _actualizar_visualizacion(self):
        """Actualiza gráficos y estadísticas."""
        especie = self.combo_especies.get()
        if not especie:
            messagebox.showwarning("Aviso", "Seleccione una especie")
            return

        # Obtener datos y estadísticas
        stats = self.gestor.calcular_estadisticas(especie)

        if not stats:
            messagebox.showerror("Error", "No hay datos para esta especie")
            return

        # Actualizar estadísticas
        self._mostrar_estadisticas(stats)

        # Crear gráficos
        self._crear_graficos(especie, stats)

    def _mostrar_estadisticas(self, stats: dict):
        """Muestra estadísticas en el panel."""
        self.stats_text.config(state='normal')
        self.stats_text.delete(1.0, tk.END)

        texto = f"""
📊 RESUMEN GENERAL
{'─' * 30}

Total de individuos: {stats['total']:,}
Promedio por registro: {stats['promedio']}
Número de registros: {stats['registros']}

📈 TENDENCIA
{'─' * 30}

{stats['tendencia']}

🔮 PROYECCIONES (3 años)
{'─' * 30}
"""
        self.stats_text.insert(tk.END, texto)

        for año, cantidad in stats['proyecciones']:
            self.stats_text.insert(tk.END, f"\n{año}: {cantidad:,} individuos")

        # Distribución por provincia
        self.stats_text.insert(tk.END, f"\n\n🗺️ POR PROVINCIA\n{'─' * 30}\n")
        for prov, cant in sorted(stats['por_provincia'].items(),
                                key=lambda x: x[1], reverse=True):
            self.stats_text.insert(tk.END, f"\n{prov}: {cant:,}")

        self.stats_text.config(state='disabled')

    def _crear_graficos(self, especie: str, stats: dict):
        """Crea gráficos mejorados con matplotlib."""
        # Limpiar canvas anterior
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()

        # Crear figura con subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        fig.patch.set_facecolor('#FFFFFF')

        # Gráfico 1: Evolución temporal
        años = list(stats['por_año'].keys())
        cantidades = list(stats['por_año'].values())

        ax1.bar(años, cantidades, color=COLORS['primary'], alpha=0.8,
               edgecolor=COLORS['primary_dark'], linewidth=1.5)
        ax1.set_title(f'Evolución de {especie}', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Año', fontsize=11)
        ax1.set_ylabel('Cantidad', fontsize=11)
        ax1.grid(axis='y', alpha=0.3, linestyle='--')

        # Agregar línea de tendencia
        if len(años) > 1:
            z = np.polyfit(años, cantidades, 1)
            p = np.poly1d(z)
            ax1.plot(años, p(años), "--", color=COLORS['accent'],
                    linewidth=2, label='Tendencia')
            ax1.legend()

        # Gráfico 2: Distribución por provincia (top 5)
        provincias = stats['por_provincia']
        top_prov = dict(sorted(provincias.items(),
                              key=lambda x: x[1], reverse=True)[:5])

        colors_prov = [COLORS['primary'], COLORS['primary_light'],
                      COLORS['accent'], '#FFC107', '#9C27B0']

        ax2.pie(top_prov.values(), labels=top_prov.keys(), autopct='%1.1f%%',
               startangle=90, colors=colors_prov[:len(top_prov)])
        ax2.set_title('Top 5 Provincias', fontsize=14, fontweight='bold')

        plt.tight_layout()

        # Integrar en tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)

    def _actualizar_tabla(self):
        """Actualiza el contenido de la tabla."""
        if self.tabla is None:
            return

        # Limpiar tabla
        for item in self.tabla.get_children():
            self.tabla.delete(item)

        # Llenar con datos
        for idx, row in self.gestor.df.iterrows():
            values = [row[col] for col in COLUMNAS_REQUERIDAS]
            self.tabla.insert("", "end", iid=str(idx), values=values)

        logger.info(f"Tabla actualizada: {len(self.gestor.df)} registros")

    def _mostrar_tabla(self):
        """Muestra la tabla y actualiza datos."""
        self._actualizar_tabla()
        self.mostrar_frame("tabla")

    def _limpiar_formulario(self):
        """Limpia los campos del formulario."""
        for key, widget in self.entries.items():
            if isinstance(widget, ttk.Combobox):
                if key == "especie":
                    widget.set(ESPECIES_PANAMA[0])
                else:
                    widget.set(PROVINCIAS_PANAMA[0])
            else:
                widget.delete(0, tk.END)

    def _actualizar_combo_especies(self):
        """Actualiza el combobox de especies."""
        especies = self.gestor.obtener_especies()
        if hasattr(self, 'combo_especies'):
            self.combo_especies['values'] = especies
            if especies:
                self.combo_especies.set(especies[0])

    def _actualizar_indicador_estado(self):
        """Actualiza el indicador de cambios sin guardar."""
        if self.gestor.cambios_sin_guardar:
            self.label_estado.config(
                text="⚠️ Hay cambios sin guardar",
                fg=COLORS['warning'])
        else:
            self.label_estado.config(text="")

    # ========================================================================
    # ACCIONES
    # ========================================================================

    def _accion_cargar(self):
        """Acción: Cargar archivo Excel."""
        ruta = filedialog.askopenfilename(
            title="Seleccionar archivo",
            filetypes=[("Archivos Excel", "*.xlsx *.xls"), ("Todos", "*.*")])

        if not ruta:
            return

        exito, mensaje = self.gestor.cargar_excel(ruta)

        if exito:
            messagebox.showinfo("Éxito", mensaje)
            self._actualizar_tabla()
            self._actualizar_combo_especies()
            self.mostrar_frame("tabla")
        else:
            messagebox.showerror("Error", mensaje)

    def _accion_guardar(self):
        """Acción: Guardar cambios."""
        if self.gestor.df.empty:
            messagebox.showwarning("Aviso", "No hay datos para guardar")
            return

        if self.gestor.ruta_archivo:
            exito, mensaje = self.gestor.guardar_excel()
        else:
            ruta = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel", "*.xlsx")])
            if not ruta:
                return
            exito, mensaje = self.gestor.guardar_excel(ruta)

        if exito:
            messagebox.showinfo("Éxito", mensaje)
            self._actualizar_indicador_estado()
        else:
            messagebox.showerror("Error", mensaje)

    def _accion_agregar(self):
        """Acción: Agregar nuevo registro."""
        try:
            especie = self.entries["especie"].get()
            cantidad = int(self.entries["cantidad"].get())
            año = int(self.entries["año"].get())
            provincia = self.entries["provincia"].get()

            exito, mensaje = self.gestor.agregar_registro(
                especie, cantidad, año, provincia)

            if exito:
                messagebox.showinfo("Éxito", mensaje)
                self._limpiar_formulario()
                self._actualizar_tabla()
                self._actualizar_combo_especies()
                self._actualizar_indicador_estado()
            else:
                messagebox.showerror("Error", mensaje)

        except ValueError:
            messagebox.showerror("Error",
                "Cantidad y Año deben ser números enteros")

    def _accion_modificar(self):
        """Acción: Modificar registro seleccionado."""
        seleccion = self.tabla.selection()

        if not seleccion:
            messagebox.showwarning("Aviso",
                "Seleccione un registro de la tabla")
            return

        idx = int(seleccion[0])
        self._abrir_dialogo_edicion(idx)

    def _accion_eliminar(self):
        """Acción: Eliminar registro seleccionado."""
        seleccion = self.tabla.selection()

        if not seleccion:
            messagebox.showwarning("Aviso",
                "Seleccione un registro de la tabla")
            return

        if not messagebox.askyesno("Confirmar",
                "¿Está seguro de eliminar este registro?"):
            return

        idx = int(seleccion[0])
        exito, mensaje = self.gestor.eliminar_registro(idx)

        if exito:
            messagebox.showinfo("Éxito", mensaje)
            self._actualizar_tabla()
            self._actualizar_combo_especies()
            self._actualizar_indicador_estado()
        else:
            messagebox.showerror("Error", mensaje)

    def _accion_generar_informe(self):
        """Acción: Generar informe PDF."""
        if self.gestor.df.empty:
            messagebox.showwarning("Aviso", "No hay datos para generar informe")
            return

        # Ventana de selección
        win = tk.Toplevel(self.root)
        win.title("Generar Informe PDF")
        win.geometry("400x200")
        win.configure(bg=COLORS['card'])
        win.transient(self.root)
        win.grab_set()

        tk.Label(win,
            text="Seleccione la especie:",
            font=('Segoe UI', 12),
            bg=COLORS['card']).pack(pady=20)

        especies = self.gestor.obtener_especies()
        combo = ttk.Combobox(win, values=especies, state="readonly",
                           font=('Segoe UI', 11), width=30)
        combo.pack(pady=10)
        if especies:
            combo.set(especies[0])

        def generar():
            especie = combo.get()
            win.destroy()
            self._generar_pdf(especie)

        btn_frame = tk.Frame(win, bg=COLORS['card'])
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text="Generar PDF",
                  command=generar,
                  style='Accent.TButton').pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Cancelar",
                  command=win.destroy).pack(side="left", padx=10)

        # INSTRUCCIONES:
# 1. Busca en main.py el método _accion_generar_informe (aproximadamente línea 850)
# 2. Después de ese método, BORRA el método _generar_pdf existente
# 3. PEGA estos TRES métodos en su lugar (mantén la indentación de 4 espacios)

    def _generar_pdf(self, especie: str):
        """Genera el informe PDF con gráficos y diseño mejorado."""
        stats = self.gestor.calcular_estadisticas(especie)

        if not stats:
            messagebox.showerror("Error", "No hay datos para esta especie")
            return

        try:
            # Nombre del archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_pdf = f"Informe_{especie.replace(' ', '_')}_{timestamp}.pdf"

            # Crear gráficos temporales
            import tempfile
            import os

            temp_dir = tempfile.gettempdir()
            grafico1_path = os.path.join(temp_dir, f"grafico_tendencia_{timestamp}.png")
            grafico2_path = os.path.join(temp_dir, f"grafico_provincias_{timestamp}.png")

            # Generar gráficos
            self._generar_graficos_para_pdf(especie, stats, grafico1_path, grafico2_path)

            # Crear documento PDF
            doc = SimpleDocTemplate(nombre_pdf, pagesize=letter,
                                  topMargin=0.5*72, bottomMargin=0.5*72,
                                  leftMargin=0.75*72, rightMargin=0.75*72)
            elements = []
            styles = getSampleStyleSheet()

            # Estilos personalizados
            from reportlab.lib.styles import ParagraphStyle
            from reportlab.lib.enums import TA_CENTER

            titulo_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=24,
                textColor=colors.HexColor(COLORS['primary']),
                spaceAfter=20,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )

            subtitulo_style = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor(COLORS['text_light']),
                spaceAfter=30,
                alignment=TA_CENTER
            )

            seccion_style = ParagraphStyle(
                'SeccionTitle',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.HexColor(COLORS['primary']),
                spaceAfter=12,
                spaceBefore=20,
                fontName='Helvetica-Bold'
            )

            # === PORTADA ===
            elements.append(Spacer(1, 30))
            elements.append(Paragraph("Informe de Conservacion", titulo_style))
            elements.append(Paragraph(f"<b>{especie}</b>", titulo_style))

            # Fecha y hora
            fecha = datetime.now().strftime("%d de %B de %Y, %H:%M")
            elements.append(Paragraph(f"Generado el {fecha}", subtitulo_style))

            # Línea divisoria
            from reportlab.platypus import HRFlowable
            elements.append(HRFlowable(width="100%", thickness=2,
                                      color=colors.HexColor(COLORS['primary'])))
            elements.append(Spacer(1, 20))

            # === RESUMEN EJECUTIVO ===
            elements.append(Paragraph("Resumen Ejecutivo", seccion_style))

            resumen_data = [
                ["Metrica", "Valor"],
                ["Total de individuos registrados", f"{stats['total']:,}"],
                ["Promedio por registro", f"{stats['promedio']:,}"],
                ["Numero total de registros", f"{stats['registros']}"],
                ["Tendencia identificada", stats['tendencia']]
            ]

            tabla_resumen = Table(resumen_data, colWidths=[250, 200])
            tabla_resumen.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORS['primary'])),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 13),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 15),
                ('TOPPADDING', (0, 0), (-1, 0), 15),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor(COLORS['text'])),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, -1), 11),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 1), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1.5, colors.HexColor(COLORS['primary_light'])),
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor(COLORS['primary_dark'])),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                 [colors.white, colors.HexColor('#F5F5F5')])
            ]))
            elements.append(tabla_resumen)
            elements.append(Spacer(1, 25))

            # === GRÁFICO DE EVOLUCIÓN TEMPORAL ===
            elements.append(Paragraph("Evolucion Temporal", seccion_style))
            elements.append(Spacer(1, 10))

            from reportlab.platypus import Image
            if os.path.exists(grafico1_path):
                img = Image(grafico1_path, width=500, height=280)
                elements.append(img)
            elements.append(Spacer(1, 20))

            # === DISTRIBUCIÓN POR AÑO ===
            elements.append(Paragraph("Distribucion Detallada por Ano", seccion_style))
            elements.append(Spacer(1, 10))

            year_data = [["Ano", "Cantidad", "% del Total"]]
            total_cantidad = stats['total']
            for año, cant in sorted(stats['por_año'].items()):
                porcentaje = (cant / total_cantidad * 100) if total_cantidad > 0 else 0
                year_data.append([str(año), f"{cant:,}", f"{porcentaje:.1f}%"])

            tabla_years = Table(year_data, colWidths=[150, 150, 150])
            tabla_years.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORS['primary'])),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('FONTSIZE', (0, 1), (-1, -1), 11),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor(COLORS['primary_light'])),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                 [colors.white, colors.HexColor('#F5F5F5')])
            ]))
            elements.append(tabla_years)
            elements.append(Spacer(1, 25))

            # === GRÁFICO DE DISTRIBUCIÓN POR PROVINCIA ===
            elements.append(Paragraph("Distribucion Geografica", seccion_style))
            elements.append(Spacer(1, 10))

            if os.path.exists(grafico2_path):
                img = Image(grafico2_path, width=450, height=280)
                elements.append(img)
            elements.append(Spacer(1, 20))

            # === TABLA DE PROVINCIAS ===
            prov_data = [["Provincia", "Cantidad", "% del Total"]]
            for prov, cant in sorted(stats['por_provincia'].items(),
                                   key=lambda x: x[1], reverse=True):
                porcentaje = (cant / total_cantidad * 100) if total_cantidad > 0 else 0
                prov_data.append([prov, f"{cant:,}", f"{porcentaje:.1f}%"])

            tabla_prov = Table(prov_data, colWidths=[200, 125, 125])
            tabla_prov.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLORS['accent'])),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('FONTSIZE', (0, 1), (-1, -1), 11),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#FF8F00')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                 [colors.white, colors.HexColor('#FFF3E0')])
            ]))
            elements.append(tabla_prov)
            elements.append(Spacer(1, 25))

            # === PROYECCIONES ===
            if stats['proyecciones']:
                elements.append(Paragraph("Proyecciones Futuras (3 anos)", seccion_style))
                elements.append(Spacer(1, 10))

                nota_style = ParagraphStyle(
                    'Nota',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=colors.HexColor(COLORS['text_light']),
                    spaceAfter=10
                )
                elements.append(Paragraph(
                    "Basado en analisis de regresion lineal de tendencias historicas",
                    nota_style
                ))

                proj_data = [["Ano", "Cantidad Proyectada", "Variacion"]]
                valores_proyectados = [cant for _, cant in stats['proyecciones']]
                valor_actual = list(stats['por_año'].values())[-1] if stats['por_año'] else 0

                for i, (año, cant) in enumerate(stats['proyecciones']):
                    if i == 0:
                        variacion = cant - valor_actual
                    else:
                        variacion = cant - stats['proyecciones'][i-1][1]

                    signo = "+" if variacion >= 0 else ""
                    proj_data.append([
                        str(año),
                        f"{cant:,}",
                        f"{signo}{variacion:,}"
                    ])

                tabla_proj = Table(proj_data, colWidths=[150, 150, 150])
                tabla_proj.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9C27B0')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('TOPPADDING', (0, 0), (-1, -1), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('FONTSIZE', (0, 1), (-1, -1), 11),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#BA68C8')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                     [colors.white, colors.HexColor('#F3E5F5')])
                ]))
                elements.append(tabla_proj)
                elements.append(Spacer(1, 20))

            # === PIE DE PÁGINA ===
            elements.append(Spacer(1, 30))
            elements.append(HRFlowable(width="100%", thickness=1,
                                      color=colors.HexColor(COLORS['text_light'])))
            elements.append(Spacer(1, 10))

            footer_style = ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=9,
                textColor=colors.HexColor(COLORS['text_light']),
                alignment=TA_CENTER
            )
            elements.append(Paragraph(
                "Sistema de Gestion de Animales en Peligro de Extincion - Panama",
                footer_style
            ))
            elements.append(Paragraph(
                f"Documento generado automaticamente el {fecha}",
                footer_style
            ))

            # Generar PDF
            doc.build(elements)

            # Limpiar archivos temporales
            try:
                if os.path.exists(grafico1_path):
                    os.remove(grafico1_path)
                if os.path.exists(grafico2_path):
                    os.remove(grafico2_path)
            except:
                pass

            messagebox.showinfo("Exito",
                f"Informe generado exitosamente:\n{nombre_pdf}")
            logger.info(f"PDF generado: {nombre_pdf}")

        except Exception as e:
            logger.error(f"Error al generar PDF: {e}")
            messagebox.showerror("Error", f"No se pudo generar el PDF:\n{e}")

    def _generar_graficos_para_pdf(self, especie: str, stats: dict,
                                   path1: str, path2: str):
        """Genera los gráficos como archivos PNG para incluir en el PDF."""
        import matplotlib
        matplotlib.use('Agg')  # Backend sin GUI

        # Gráfico 1: Evolución temporal con proyecciones
        fig1, ax1 = plt.subplots(figsize=(10, 5.5))
        fig1.patch.set_facecolor('white')

        años = list(stats['por_año'].keys())
        cantidades = list(stats['por_año'].values())

        # Barras principales
        bars = ax1.bar(años, cantidades, color=COLORS['primary'],
                       alpha=0.8, edgecolor=COLORS['primary_dark'],
                       linewidth=2, label='Datos reales')

        # Añadir valores sobre las barras
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height):,}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')

        # Línea de tendencia
        if len(años) > 1:
            z = np.polyfit(años, cantidades, 1)
            p = np.poly1d(z)
            años_extendidos = list(range(min(años), max(años)+1))
            ax1.plot(años_extendidos, p(años_extendidos), "--",
                    color=COLORS['accent'], linewidth=3,
                    label='Linea de tendencia', alpha=0.8)

            # Proyecciones
            if stats['proyecciones']:
                años_proy = [año for año, _ in stats['proyecciones']]
                cant_proy = [cant for _, cant in stats['proyecciones']]
                ax1.plot(años_proy, cant_proy, 'o--',
                        color='#9C27B0', linewidth=2.5,
                        markersize=8, label='Proyecciones',
                        alpha=0.7)

        ax1.set_title(f'Evolucion de Poblacion: {especie}',
                     fontsize=16, fontweight='bold', pad=20)
        ax1.set_xlabel('Ano', fontsize=13, fontweight='bold')
        ax1.set_ylabel('Cantidad de Individuos', fontsize=13, fontweight='bold')
        ax1.grid(axis='y', alpha=0.3, linestyle='--', linewidth=1)
        ax1.legend(fontsize=11, loc='best', framealpha=0.9)
        ax1.spines['top'].set_visible(False)
        ax1.spines['right'].set_visible(False)

        plt.tight_layout()
        plt.savefig(path1, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()

        # Gráfico 2: Distribución por provincia (top 7)
        fig2, ax2 = plt.subplots(figsize=(9, 5.5))
        fig2.patch.set_facecolor('white')

        provincias = stats['por_provincia']
        top_prov = dict(sorted(provincias.items(),
                              key=lambda x: x[1], reverse=True)[:7])

        colors_prov = [
            COLORS['primary'], COLORS['primary_light'],
            COLORS['accent'], '#FFC107', '#9C27B0',
            '#00BCD4', '#4CAF50'
        ]

        wedges, texts, autotexts = ax2.pie(
            top_prov.values(),
            labels=top_prov.keys(),
            autopct='%1.1f%%',
            startangle=90,
            colors=colors_prov[:len(top_prov)],
            textprops={'fontsize': 11, 'fontweight': 'bold'},
            wedgeprops={'edgecolor': 'white', 'linewidth': 2}
        )

        # Mejorar apariencia de porcentajes
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')

        ax2.set_title(f'Distribucion por Provincia\nTop 7 Regiones',
                     fontsize=16, fontweight='bold', pad=20)

        plt.tight_layout()
        plt.savefig(path2, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()

    def _on_tabla_doble_clic(self, event):
        """Maneja doble clic en la tabla."""
        seleccion = self.tabla.selection()
        if seleccion:
            idx = int(seleccion[0])
            self._abrir_dialogo_edicion(idx)

    def _on_tabla_doble_clic(self, event):
        """Maneja doble clic en la tabla."""
        seleccion = self.tabla.selection()
        if seleccion:
            idx = int(seleccion[0])
            self._abrir_dialogo_edicion(idx)

    def _abrir_dialogo_edicion(self, idx: int):
        """Abre diálogo para editar un registro."""
        if idx >= len(self.gestor.df):
            messagebox.showerror("Error", "Índice inválido")
            return

        fila = self.gestor.df.iloc[idx]

        # Ventana de edición
        win = tk.Toplevel(self.root)
        win.title("Modificar Registro")
        win.geometry("450x400")
        win.configure(bg=COLORS['card'])
        win.transient(self.root)
        win.grab_set()

        tk.Label(win,
            text="✏️ Editar Registro",
            font=('Segoe UI', 16, 'bold'),
            bg=COLORS['card'],
            fg=COLORS['primary']).pack(pady=20)

        # Formulario
        form = tk.Frame(win, bg=COLORS['card'])
        form.pack(pady=10)

        entries_edit = {}
        campos = [
            ("Especie:", "Especie", "combo"),
            ("Cantidad:", "Cantidad", "entry"),
            ("Año:", "Año", "entry"),
            ("Provincia:", "Provincia", "combo")
        ]

        for i, (label, col, tipo) in enumerate(campos):
            tk.Label(form,
                text=label,
                font=('Segoe UI', 11),
                bg=COLORS['card']).grid(row=i, column=0, sticky="e",
                                       padx=15, pady=12)

            if tipo == "entry":
                widget = tk.Entry(form, font=('Segoe UI', 11), width=25)
                widget.insert(0, str(fila[col]))
            else:
                if col == "Especie":
                    valores = ESPECIES_PANAMA
                else:
                    valores = PROVINCIAS_PANAMA

                widget = ttk.Combobox(form, values=valores,
                                     state="readonly", font=('Segoe UI', 11),
                                     width=23)
                # Intentar establecer el valor actual, si no está en la lista, usar el primero
                valor_actual = str(fila[col])
                if valor_actual in valores:
                    widget.set(valor_actual)
                else:
                    widget.set(valores[0])

            widget.grid(row=i, column=1, padx=15, pady=12)
            entries_edit[col] = widget

        def guardar():
            try:
                especie = entries_edit["Especie"].get()
                cantidad = int(entries_edit["Cantidad"].get())
                año = int(entries_edit["Año"].get())
                provincia = entries_edit["Provincia"].get()

                exito, mensaje = self.gestor.modificar_registro(
                    idx, especie, cantidad, año, provincia)

                if exito:
                    messagebox.showinfo("Éxito", mensaje)
                    self._actualizar_tabla()
                    self._actualizar_combo_especies()
                    self._actualizar_indicador_estado()
                    win.destroy()
                else:
                    messagebox.showerror("Error", mensaje)
            except ValueError:
                messagebox.showerror("Error",
                    "Cantidad y Año deben ser números enteros")

        btn_frame = tk.Frame(win, bg=COLORS['card'])
        btn_frame.pack(pady=25)

        ttk.Button(btn_frame, text="💾 Guardar",
                  command=guardar,
                  style='Accent.TButton').pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Cancelar",
                  command=win.destroy).pack(side="left", padx=10)

    def _on_closing(self):
        """Maneja el cierre de la aplicación."""
        if self.gestor.cambios_sin_guardar:
            respuesta = messagebox.askyesnocancel(
                "Cambios sin guardar",
                "Hay cambios sin guardar. ¿Desea guardarlos antes de salir?")

            if respuesta is None:  # Cancelar
                return
            elif respuesta:  # Sí
                if self.gestor.ruta_archivo:
                    self.gestor.guardar_excel()
                else:
                    ruta = filedialog.asksaveasfilename(
                        defaultextension=".xlsx",
                        filetypes=[("Excel", "*.xlsx")])
                    if ruta:
                        self.gestor.guardar_excel(ruta)
                    else:
                        return

        logger.info("Aplicación cerrada")
        self.root.quit()
        self.root.destroy()

    def run(self):
        """Inicia el loop principal de la aplicación."""
        logger.info("Iniciando aplicación")
        self.root.mainloop()

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

def main():
    """Función principal de la aplicación."""
    try:
        # Crear instancias
        gestor = GestorAnimales()
        app = InterfazPrincipal(gestor)

        # Iniciar aplicación
        app.run()

    except Exception as e:
        logger.critical(f"Error crítico: {e}", exc_info=True)
        messagebox.showerror("Error Crítico",
            f"La aplicación encontró un error:\n{e}")

if __name__ == "__main__":
    main()
