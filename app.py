import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import io
from fpdf import FPDF
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Configuración de la página
st.set_page_config(
    page_title="Monitoreo de Presión y Temperatura Reservorio Ahuachapán",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS para impresión
st.markdown("""
<style>
    .no-print { display: block; }
</style>
""", unsafe_allow_html=True)

st.title("📊 Monitoreo de Presión y Temperatura Reservorio Ahuachapán")
st.markdown("---")

# Sidebar para controles
st.sidebar.header("🔧 Configuración")

# Función para cargar y procesar CSV
def procesar_csv(archivo):
    """Carga y procesa el archivo CSV"""
    try:
        # Leer el CSV (ignorar líneas adicionales, tomar las primeras 4 columnas)
        df = pd.read_csv(archivo)
        
        # Seleccionar solo las primeras 4 columnas
        df = df.iloc[:, :4]
        
        # Renombrar columnas si es necesario
        df.columns = ['Fecha', 'Hora', 'Presión', 'Temperatura']
        
        # Combinar Fecha y Hora en una columna datetime
        df['DateTime'] = pd.to_datetime(
            df['Fecha'] + ' ' + df['Hora'],
            format='%m/%d/%Y %H:%M:%S'
        )
        
        # Convertir columnas numéricas
        df['Presión'] = pd.to_numeric(df['Presión'], errors='coerce')
        df['Temperatura'] = pd.to_numeric(df['Temperatura'], errors='coerce')
        
        # Eliminar filas con valores nulos
        df = df.dropna(subset=['Presión', 'Temperatura', 'DateTime'])
        
        # Ordenar por DateTime
        df = df.sort_values('DateTime')
        
        return df
    
    except Exception as e:
        st.error(f"Error al procesar el archivo: {str(e)}")
        return None


# ============================================================
# FUNCIÓN: Procesar CSV formato DataLogger
# ============================================================
def procesar_csv_datalogger(archivo):
    """Lee CSV de DataLogger (encabezados en fila 17) y detecta canales con datos"""
    try:
        df = pd.read_csv(archivo, skiprows=16, header=0, encoding='latin-1', on_bad_lines='skip')

        # Fecha, Hora + hasta 4 canales de datos (6 cols máximo)
        n_cols = min(len(df.columns), 6)
        df = df.iloc[:, :n_cols]
        n_canales = n_cols - 2
        df.columns = ['Fecha', 'Hora'] + [f'Canal_{i+1}' for i in range(n_canales)]

        # Combinar DateTime (formato dd/mm/yyyy HH:MM:SS)
        df['DateTime'] = pd.to_datetime(
            df['Fecha'].astype(str).str.strip() + ' ' + df['Hora'].astype(str).str.strip(),
            format='%d/%m/%Y %H:%M:%S',
            errors='coerce'
        )
        df = df.dropna(subset=['DateTime'])
        df = df.sort_values('DateTime').reset_index(drop=True)

        # Detectar qué canales tienen datos numéricos
        canales_info = {}
        for i in range(1, n_canales + 1):
            col = f'Canal_{i}'
            if col in df.columns:
                serie = pd.to_numeric(df[col], errors='coerce')
                n_datos = int(serie.notna().sum())
                canales_info[i] = {
                    'col': col,
                    'tiene_datos': n_datos > 0,
                    'n_registros': n_datos
                }

        return df, canales_info

    except Exception as e:
        st.error(f"Error al procesar DataLogger: {str(e)}")
        return None, {}


def generar_pdf_reporte(df_diario, df_filtrado, fecha_min_val, fecha_max_val, presion_min_fecha, presion_max_fecha, temp_min_fecha, temp_max_fecha, mostrar_presion, mostrar_temperatura):
    """Genera un PDF con el reporte incluyendo gráficas"""
    try:
        # Crear gráfica para PDF con matplotlib
        n_rows = sum([mostrar_presion, mostrar_temperatura])
        fig_pdf, axes = plt.subplots(n_rows, 1, figsize=(10, 3 * n_rows), constrained_layout=True)
        if n_rows == 1:
            axes = [axes]
        ax_idx = 0
        if mostrar_presion:
            ax = axes[ax_idx]
            ax.plot(df_filtrado['DateTime'], df_filtrado['Presión'],
                    color='#1f77b4', linewidth=1.5, marker='o', markersize=2)
            ax.set_title("Presión en el Tiempo", fontsize=10)
            ax.set_ylabel("Presión (Bar)")
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
            ax.tick_params(axis='x', rotation=30, labelsize=7)
            ax.grid(True, linestyle='--', alpha=0.5)
            ax_idx += 1
        if mostrar_temperatura:
            ax = axes[ax_idx]
            ax.plot(df_filtrado['DateTime'], df_filtrado['Temperatura'],
                    color='#ff7f0e', linewidth=1.5, marker='o', markersize=2)
            ax.set_title("Temperatura en el Tiempo", fontsize=10)
            ax.set_ylabel("Temperatura (°C)")
            ax.set_xlabel("Fecha y Hora")
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
            ax.tick_params(axis='x', rotation=30, labelsize=7)
            ax.grid(True, linestyle='--', alpha=0.5)
        img_file = io.BytesIO()
        fig_pdf.savefig(img_file, format='png', dpi=120)
        plt.close(fig_pdf)
        img_file.seek(0)

        # --- Constantes de diseño ---
        MARGIN = 15
        PAGE_W = 210
        CONTENT_W = PAGE_W - 2 * MARGIN  # 180mm

        # Paleta de colores
        C_AZUL        = (31, 119, 180)
        C_NARANJA     = (220, 100, 20)
        C_FONDO_CARD  = (240, 246, 252)
        C_BORDE_CARD  = (180, 210, 240)
        C_GRIS_CLARO  = (245, 245, 245)
        C_GRIS_TEXTO  = (80, 80, 80)
        C_BLANCO      = (255, 255, 255)
        C_NEGRO_TABLA = (40, 40, 40)

        # ------------------------------------------------------------------ #
        # Función auxiliar: dibuja una tarjeta de estadística con recuadro   #
        # ------------------------------------------------------------------ #
        def draw_card(pdf, x, y, w, h, title, main_value, detail):
            color = C_AZUL if "resion" in title else C_NARANJA
            # Fondo
            pdf.set_fill_color(*C_FONDO_CARD)
            pdf.set_draw_color(*C_BORDE_CARD)
            pdf.set_line_width(0.3)
            pdf.rect(x, y, w, h, 'FD')
            # Barra de acento izquierda
            pdf.set_fill_color(*color)
            pdf.rect(x, y, 3.5, h, 'F')
            # Título
            pdf.set_xy(x + 6, y + 3)
            pdf.set_font("Arial", "B", 7.5)
            pdf.set_text_color(*C_GRIS_TEXTO)
            pdf.cell(w - 7, 5, title.upper(), 0, 0, "L")
            # Valor principal
            pdf.set_xy(x + 6, y + 9)
            pdf.set_font("Arial", "B", 13)
            pdf.set_text_color(*color)
            pdf.cell(w - 7, 8, main_value, 0, 0, "L")
            # Detalle
            pdf.set_xy(x + 6, y + 19)
            pdf.set_font("Arial", "", 7)
            pdf.set_text_color(*C_GRIS_TEXTO)
            pdf.cell(w - 7, 5, detail, 0, 0, "L")

        # ------------------------------------------------------------------ #
        # Función auxiliar: dibuja el encabezado de página                   #
        # ------------------------------------------------------------------ #
        def draw_header(pdf, full=True):
            h = 32 if full else 20
            pdf.set_fill_color(*C_AZUL)
            pdf.rect(0, 0, PAGE_W, h, 'F')
            if full:
                pdf.set_xy(MARGIN, 6)
                pdf.set_font("Arial", "B", 17)
                pdf.set_text_color(*C_BLANCO)
                pdf.cell(CONTENT_W, 10, "Monitoreo de Presión y Temperatura", 0, 1, "C")
                pdf.set_x(MARGIN)
                pdf.set_font("Arial", "B", 17)
                pdf.cell(CONTENT_W, 7, "Reservorio Ahuachapán", 0, 1, "C")
            else:
                pdf.set_xy(MARGIN, 5)
                pdf.set_font("Arial", "B", 13)
                pdf.set_text_color(*C_BLANCO)
                pdf.cell(CONTENT_W, 10, "Promedios Diarios - Reservorio Ahuachapán", 0, 1, "C")

        # ------------------------------------------------------------------ #
        # Función auxiliar: dibuja el pie de página                          #
        # ------------------------------------------------------------------ #
        def draw_footer(pdf):
            pdf.set_y(-18)
            pdf.set_draw_color(*C_BORDE_CARD)
            pdf.set_line_width(0.3)
            pdf.line(MARGIN, pdf.get_y(), PAGE_W - MARGIN, pdf.get_y())
            pdf.ln(2)
            pdf.set_font("Arial", "I", 7.5)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(CONTENT_W / 2, 5,
                     f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                     0, 0, "L")
            pdf.cell(CONTENT_W / 2, 5,
                     "Monitoreo Reservorio Ahuachapán",
                     0, 0, "R")

        # ================================================================== #
        #  PÁGINA 1                                                           #
        # ================================================================== #
        pdf = FPDF()
        pdf.set_margins(MARGIN, MARGIN, MARGIN)
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()

        draw_header(pdf, full=True)

        # Subtítulo con período y fecha de generación
        pdf.set_xy(MARGIN, 36)
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(*C_GRIS_TEXTO)
        pdf.cell(CONTENT_W / 2, 6,
                 f"Periodo: {fecha_min_val.strftime('%d/%m/%Y')} - {fecha_max_val.strftime('%d/%m/%Y')}",
                 0, 0, "L")
        pdf.cell(CONTENT_W / 2, 6,
                 f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                 0, 1, "R")
        pdf.ln(4)

        # --- Título de sección: Estadísticas ---
        pdf.set_font("Arial", "B", 11)
        pdf.set_text_color(*C_AZUL)
        pdf.cell(CONTENT_W, 7, "Estadisticas del Periodo", 0, 1, "L")
        pdf.set_draw_color(*C_AZUL)
        pdf.set_line_width(0.6)
        pdf.line(MARGIN, pdf.get_y(), MARGIN + 65, pdf.get_y())
        pdf.set_line_width(0.2)
        pdf.ln(5)

        # Calcular valores para las tarjetas
        presion_prom  = df_filtrado['Presión'].mean()
        temp_prom     = df_filtrado['Temperatura'].mean()
        presion_std   = df_filtrado['Presión'].std()
        temp_std      = df_filtrado['Temperatura'].std()
        p_min_g       = df_filtrado['Presión'].min()
        p_max_g       = df_filtrado['Presión'].max()
        t_min_g       = df_filtrado['Temperatura'].min()
        t_max_g       = df_filtrado['Temperatura'].max()

        var_presion_str = "N/D"
        var_temp_str    = "N/D"
        if presion_min_fecha is not None and presion_max_fecha is not None:
            var_p = presion_max_fecha - presion_min_fecha
            var_presion_str = f"{var_p:+.2f} Bar"
        if temp_min_fecha is not None and temp_max_fecha is not None:
            var_t = temp_max_fecha - temp_min_fecha
            var_temp_str = f"{var_t:+.2f} C"

        # Tarjetas: 2 columnas, 2 filas
        CARD_W   = (CONTENT_W - 6) / 2   # gap de 6mm entre columnas
        CARD_H   = 30
        CARD_GAP = 6
        x_izq    = MARGIN
        x_der    = MARGIN + CARD_W + CARD_GAP

        y0 = pdf.get_y()
        draw_card(pdf, x_izq, y0, CARD_W, CARD_H,
                  "Presion Promedio",
                  f"{presion_prom:.2f} Bar",
                  f"Min: {p_min_g:.2f}  |  Max: {p_max_g:.2f}  |  Desv: {presion_std:.2f}")
        draw_card(pdf, x_der, y0, CARD_W, CARD_H,
                  "Temperatura Promedio",
                  f"{temp_prom:.2f} °C",
                  f"Min: {t_min_g:.2f}  |  Max: {t_max_g:.2f}  |  Desv: {temp_std:.2f}")

        y1 = y0 + CARD_H + 4
        rango_fechas = f"Del {fecha_min_val.strftime('%d/%m/%y')} al {fecha_max_val.strftime('%d/%m/%y')}"
        draw_card(pdf, x_izq, y1, CARD_W, CARD_H,
                  "Variación de Presion",
                  var_presion_str,
                  rango_fechas)
        draw_card(pdf, x_der, y1, CARD_W, CARD_H,
                  "Variación de Temperatura",
                  var_temp_str,
                  rango_fechas)

        pdf.set_y(y1 + CARD_H + 8)

        # --- Título de sección: Gráficas ---
        pdf.set_font("Arial", "B", 11)
        pdf.set_text_color(*C_AZUL)
        pdf.cell(CONTENT_W, 7, "Graficas de Datos", 0, 1, "L")
        pdf.set_draw_color(*C_AZUL)
        pdf.set_line_width(0.6)
        pdf.line(MARGIN, pdf.get_y(), MARGIN + 52, pdf.get_y())
        pdf.set_line_width(0.2)
        pdf.ln(5)

        # Imagen de la gráfica con borde
        try:
            y_img  = pdf.get_y()
            img_h  = 105
            pdf.set_draw_color(*C_BORDE_CARD)
            pdf.set_line_width(0.3)
            pdf.rect(MARGIN - 1, y_img - 1, CONTENT_W + 2, img_h + 2)
            pdf.image(img_file, x=MARGIN, y=y_img, w=CONTENT_W, h=img_h)
            pdf.set_y(y_img + img_h + 6)
        except Exception:
            pdf.set_font("Arial", "", 9)
            pdf.set_text_color(*C_GRIS_TEXTO)
            pdf.cell(CONTENT_W, 8, "[Grafica no disponible - instalar kaleido: pip install kaleido]", 0, 1)

        pdf.set_auto_page_break(False)
        draw_footer(pdf)
        pdf.set_auto_page_break(True, margin=20)

        # ================================================================== #
        #  PÁGINA 2: Tabla de promedios diarios                              #
        # ================================================================== #
        pdf.add_page()
        draw_header(pdf, full=False)

        pdf.set_xy(MARGIN, 23)
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(*C_GRIS_TEXTO)
        pdf.cell(CONTENT_W / 2, 6,
                 f"Periodo: {fecha_min_val.strftime('%d/%m/%Y')} - {fecha_max_val.strftime('%d/%m/%Y')}",
                 0, 0, "L")
        pdf.cell(CONTENT_W / 2, 6,
                 f"Total de dias: {len(df_diario)}",
                 0, 1, "R")
        pdf.ln(5)

        # Encabezado de tabla
        col_widths = [28, 23, 23, 23, 27, 22, 22, 12]
        headers    = ["Fecha", "P.Prom", "P.Min", "P.Max", "T.Prom", "T.Min", "T.Max", "Reg."]

        pdf.set_font("Arial", "B", 9)
        pdf.set_fill_color(*C_AZUL)
        pdf.set_text_color(*C_BLANCO)
        pdf.set_draw_color(*C_BORDE_CARD)
        pdf.set_line_width(0.3)
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 9, header, 1, 0, "C", True)
        pdf.ln()

        # Filas de datos
        pdf.set_font("Arial", "", 8)
        pdf.set_text_color(*C_NEGRO_TABLA)
        for idx, row in enumerate(df_diario.itertuples(index=False)):
            if idx % 2 == 0:
                pdf.set_fill_color(*C_GRIS_CLARO)
            else:
                pdf.set_fill_color(*C_BLANCO)
            fecha_str = str(row.Fecha)
            pdf.cell(col_widths[0], 8, fecha_str[:10], 1, 0, "C", True)
            pdf.cell(col_widths[1], 8, f"{row.Presión_Promedio:.2f}", 1, 0, "C", True)
            pdf.cell(col_widths[2], 8, f"{row.Presión_Min:.2f}", 1, 0, "C", True)
            pdf.cell(col_widths[3], 8, f"{row.Presión_Max:.2f}", 1, 0, "C", True)
            pdf.cell(col_widths[4], 8, f"{row.Temperatura_Promedio:.2f}", 1, 0, "C", True)
            pdf.cell(col_widths[5], 8, f"{row.Temperatura_Min:.2f}", 1, 0, "C", True)
            pdf.cell(col_widths[6], 8, f"{row.Temperatura_Max:.2f}", 1, 0, "C", True)
            pdf.cell(col_widths[7], 8, f"{int(row.Presión_Registros)}", 1, 0, "C", True)
            pdf.ln()

        pdf.set_auto_page_break(False)
        draw_footer(pdf)

        # Convertir a bytes
        pdf_bytes = bytes(pdf.output(dest='S'))
        return pdf_bytes

    except Exception as e:
        st.error(f"Error al generar PDF: {str(e)}")
        return None


# ============================================================
# FUNCIÓN: Generar PDF para DataLogger (canales dinámicos)
# ============================================================
def generar_pdf_datalogger(df_filt, df_diario_dl, activos, fi_dt, ff_dt):
    """Genera PDF del reporte DataLogger con canales configurables"""
    try:
        # Generar figura combinada para el PDF con matplotlib
        canales_validos = [c for c in activos if c['nombre'] in df_filt.columns]
        n_validos = len(canales_validos)
        if n_validos == 0:
            return None
        fig_dl, axes_dl = plt.subplots(n_validos, 1, figsize=(10, 3 * n_validos), constrained_layout=True)
        if n_validos == 1:
            axes_dl = [axes_dl]
        for idx, c in enumerate(canales_validos):
            col_nombre = c['nombre']
            unidad_label = c['unidad'] if c['unidad'] else ""
            ax = axes_dl[idx]
            ax.plot(df_filt['DateTime'], df_filt[col_nombre],
                    color=c['color'], linewidth=1.5, marker='o', markersize=2)
            titulo = f"{col_nombre} ({unidad_label})" if unidad_label else col_nombre
            ax.set_title(titulo, fontsize=10)
            ax.set_ylabel(titulo)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
            ax.tick_params(axis='x', rotation=30, labelsize=7)
            ax.grid(True, linestyle='--', alpha=0.5)
        axes_dl[-1].set_xlabel("Fecha y Hora")
        img_file = io.BytesIO()
        fig_dl.savefig(img_file, format='png', dpi=120)
        plt.close(fig_dl)
        img_file.seek(0)

        MARGIN     = 15
        PAGE_W     = 210
        CONTENT_W  = PAGE_W - 2 * MARGIN

        C_AZUL        = (31, 119, 180)
        C_NARANJA     = (220, 100, 20)
        C_FONDO_CARD  = (240, 246, 252)
        C_BORDE_CARD  = (180, 210, 240)
        C_GRIS_CLARO  = (245, 245, 245)
        C_GRIS_TEXTO  = (80, 80, 80)
        C_BLANCO      = (255, 255, 255)
        C_NEGRO_TABLA = (40, 40, 40)

        COLORES_TIPO_RGB = {
            "Presión":     C_AZUL,
            "Temperatura": C_NARANJA,
            "Flujo":       (44, 160, 44),
            "Otro":        (148, 103, 189),
        }

        def draw_card_dl(pdf, x, y, w, h, title, main_value, detail, color):
            pdf.set_fill_color(*C_FONDO_CARD)
            pdf.set_draw_color(*C_BORDE_CARD)
            pdf.set_line_width(0.3)
            pdf.rect(x, y, w, h, 'FD')
            pdf.set_fill_color(*color)
            pdf.rect(x, y, 3.5, h, 'F')
            pdf.set_xy(x + 6, y + 3)
            pdf.set_font("Arial", "B", 7.5)
            pdf.set_text_color(*C_GRIS_TEXTO)
            pdf.cell(w - 7, 5, title.upper(), 0, 0, "L")
            pdf.set_xy(x + 6, y + 9)
            pdf.set_font("Arial", "B", 13)
            pdf.set_text_color(*color)
            pdf.cell(w - 7, 8, main_value, 0, 0, "L")
            pdf.set_xy(x + 6, y + 19)
            pdf.set_font("Arial", "", 7)
            pdf.set_text_color(*C_GRIS_TEXTO)
            pdf.cell(w - 7, 5, detail, 0, 0, "L")

        def draw_header_dl(pdf, full=True):
            h = 32 if full else 20
            pdf.set_fill_color(*C_AZUL)
            pdf.rect(0, 0, PAGE_W, h, 'F')
            if full:
                pdf.set_xy(MARGIN, 6)
                pdf.set_font("Arial", "B", 17)
                pdf.set_text_color(*C_BLANCO)
                pdf.cell(CONTENT_W, 10, "Monitoreo - DataLogger", 0, 1, "C")
                pdf.set_x(MARGIN)
                pdf.set_font("Arial", "B", 17)
                pdf.cell(CONTENT_W, 7, "Reservorio Ahuachapán", 0, 1, "C")
            else:
                pdf.set_xy(MARGIN, 5)
                pdf.set_font("Arial", "B", 13)
                pdf.set_text_color(*C_BLANCO)
                pdf.cell(CONTENT_W, 10, "Promedios Diarios - Reservorio Ahuachapán", 0, 1, "C")

        def draw_footer_dl(pdf):
            pdf.set_y(-18)
            pdf.set_draw_color(*C_BORDE_CARD)
            pdf.set_line_width(0.3)
            pdf.line(MARGIN, pdf.get_y(), PAGE_W - MARGIN, pdf.get_y())
            pdf.ln(2)
            pdf.set_font("Arial", "I", 7.5)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(CONTENT_W / 2, 5, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 0, "L")
            pdf.cell(CONTENT_W / 2, 5, "Monitoreo Reservorio Ahuachapán", 0, 0, "R")

        # ===== PÁGINA 1 =====
        pdf = FPDF()
        pdf.set_margins(MARGIN, MARGIN, MARGIN)
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()
        draw_header_dl(pdf, full=True)

        pdf.set_xy(MARGIN, 36)
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(*C_GRIS_TEXTO)
        fecha_ini_str = fi_dt.strftime('%d/%m/%Y')
        fecha_fin_str = ff_dt.strftime('%d/%m/%Y')
        pdf.cell(CONTENT_W / 2, 6, f"Periodo: {fecha_ini_str} - {fecha_fin_str}", 0, 0, "L")
        pdf.cell(CONTENT_W / 2, 6, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, "R")
        pdf.ln(4)

        # Título sección estadísticas
        pdf.set_font("Arial", "B", 11)
        pdf.set_text_color(*C_AZUL)
        pdf.cell(CONTENT_W, 7, "Estadisticas del Periodo", 0, 1, "L")
        pdf.set_draw_color(*C_AZUL)
        pdf.set_line_width(0.6)
        pdf.line(MARGIN, pdf.get_y(), MARGIN + 65, pdf.get_y())
        pdf.set_line_width(0.2)
        pdf.ln(5)

        # Tarjetas: hasta 2 por fila
        CARD_W   = (CONTENT_W - 6) / 2
        CARD_H   = 30
        CARD_GAP = 6
        for idx, c in enumerate(activos):
            col_nombre = c['nombre']
            if col_nombre not in df_filt.columns:
                continue
            serie = df_filt[col_nombre].dropna()
            color = COLORES_TIPO_RGB.get(c['tipo'], C_AZUL)
            unidad = c['unidad']
            main_val = f"{serie.mean():.2f} {unidad}".strip()
            detail   = f"Min: {serie.min():.2f}  |  Max: {serie.max():.2f}  |  Desv: {serie.std():.2f}"
            col_pos = idx % 2
            if col_pos == 0:
                x_card = MARGIN
                y0_fila = pdf.get_y()
            else:
                x_card = MARGIN + CARD_W + CARD_GAP
            if idx % 2 == 0 and idx > 0:
                pdf.set_y(pdf.get_y() + CARD_H + 4)
                y0_fila = pdf.get_y()
            draw_card_dl(pdf, x_card, y0_fila, CARD_W, CARD_H,
                         f"{c['tipo']}: {col_nombre}", main_val, detail, color)

        # Avanzar cursor después de las tarjetas
        pdf.set_y(pdf.get_y() + CARD_H + 8)

        # Título sección gráficas
        pdf.set_font("Arial", "B", 11)
        pdf.set_text_color(*C_AZUL)
        pdf.cell(CONTENT_W, 7, "Graficas de Datos", 0, 1, "L")
        pdf.set_draw_color(*C_AZUL)
        pdf.set_line_width(0.6)
        pdf.line(MARGIN, pdf.get_y(), MARGIN + 52, pdf.get_y())
        pdf.set_line_width(0.2)
        pdf.ln(5)

        try:
            y_img = pdf.get_y()
            img_h = 105
            pdf.set_draw_color(*C_BORDE_CARD)
            pdf.set_line_width(0.3)
            pdf.rect(MARGIN - 1, y_img - 1, CONTENT_W + 2, img_h + 2)
            pdf.image(img_file, x=MARGIN, y=y_img, w=CONTENT_W, h=img_h)
            pdf.set_y(y_img + img_h + 6)
        except Exception:
            pdf.set_font("Arial", "", 9)
            pdf.set_text_color(*C_GRIS_TEXTO)
            pdf.cell(CONTENT_W, 8, "[Grafica no disponible - instalar kaleido: pip install kaleido]", 0, 1)

        pdf.set_auto_page_break(False)
        draw_footer_dl(pdf)
        pdf.set_auto_page_break(True, margin=20)

        # ===== PÁGINA 2: Promedios diarios =====
        pdf.add_page()
        draw_header_dl(pdf, full=False)

        pdf.set_xy(MARGIN, 23)
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(*C_GRIS_TEXTO)
        pdf.cell(CONTENT_W / 2, 6, f"Periodo: {fecha_ini_str} - {fecha_fin_str}", 0, 0, "L")
        pdf.cell(CONTENT_W / 2, 6, f"Total de dias: {len(df_diario_dl)}", 0, 1, "R")
        pdf.ln(5)

        # Encabezado de tabla (Fecha + mean/min/max por canal)
        stat_labels = ["Prom", "Min", "Max"]
        col_fecha_w = 26
        col_stat_w  = 18
        n_stats = len(activos) * 3
        headers_row = ["Fecha"] + [f"{c['nombre'][:6]}.{s}" for c in activos for s in stat_labels]
        col_widths_dl = [col_fecha_w] + [col_stat_w] * n_stats
        # Ajustar si supera el ancho
        total_w = sum(col_widths_dl)
        if total_w > CONTENT_W:
            scale = CONTENT_W / total_w
            col_widths_dl = [round(w * scale, 1) for w in col_widths_dl]

        pdf.set_font("Arial", "B", 8)
        pdf.set_fill_color(*C_AZUL)
        pdf.set_text_color(*C_BLANCO)
        pdf.set_draw_color(*C_BORDE_CARD)
        pdf.set_line_width(0.3)
        for i, h in enumerate(headers_row):
            pdf.cell(col_widths_dl[i], 9, h, 1, 0, "C", True)
        pdf.ln()

        pdf.set_font("Arial", "", 7.5)
        pdf.set_text_color(*C_NEGRO_TABLA)
        for ridx, row in enumerate(df_diario_dl.itertuples(index=False)):
            bg = C_GRIS_CLARO if ridx % 2 == 0 else C_BLANCO
            pdf.set_fill_color(*bg)
            fecha_str = str(getattr(row, 'Fecha', ''))[:10]
            pdf.cell(col_widths_dl[0], 8, fecha_str, 1, 0, "C", True)
            ci = 1
            for c in activos:
                n = c['nombre']
                for stat in ['mean', 'min', 'max']:
                    col_key = f"{n}_{stat}"
                    val = getattr(row, col_key, None)
                    val_str = f"{val:.2f}" if val is not None and val == val else "-"
                    pdf.cell(col_widths_dl[ci], 8, val_str, 1, 0, "C", True)
                    ci += 1
            pdf.ln()

        pdf.set_auto_page_break(False)
        draw_footer_dl(pdf)

        return bytes(pdf.output(dest='S'))

    except Exception as e:
        st.error(f"Error al generar PDF DataLogger: {str(e)}")
        return None


# ============================================================
# SELECTOR DE FORMATO
# ============================================================
formato = st.sidebar.radio(
    "📋 Fuente de datos",
    ["GEO-PSI", "DataLogger"],
    horizontal=True
)
st.sidebar.markdown("---")

# ============================================================
# FLUJO: GEO-PSI
# ============================================================
if formato == "GEO-PSI":
    st.sidebar.subheader("📁 Cargar Datos")
    archivos_cargados = st.sidebar.file_uploader(
        "Selecciona uno o más archivos CSV",
        type=['csv'],
        accept_multiple_files=True,
        help="Columnas requeridas: Fecha, Hora, Presión, Temperatura"
    )

    if archivos_cargados:
        lista_dfs = []
        for archivo in archivos_cargados:
            df_temp = procesar_csv(archivo)
            if df_temp is not None and len(df_temp) > 0:
                lista_dfs.append(df_temp)

        if lista_dfs:
            df = pd.concat(lista_dfs, ignore_index=True)
            df = df.sort_values('DateTime').reset_index(drop=True)

            st.sidebar.success(f"✅ {len(archivos_cargados)} archivo(s): {len(df)} registros")

            with st.sidebar.expander("ℹ️ Información de los Datos"):
                st.write(f"**Registros totales:** {len(df)}")
                st.write(f"**Fecha inicio:** {df['DateTime'].min().strftime('%d/%m/%Y %H:%M:%S')}")
                st.write(f"**Fecha fin:** {df['DateTime'].max().strftime('%d/%m/%Y %H:%M:%S')}")
                st.write(f"**Presión (Bar):** {df['Presión'].min():.2f} - {df['Presión'].max():.2f}")
                st.write(f"**Temperatura (°C):** {df['Temperatura'].min():.2f} - {df['Temperatura'].max():.2f}")

            st.sidebar.subheader("🔍 Filtros")
            fecha_min = df['DateTime'].min()
            fecha_max = df['DateTime'].max()
            fecha_inicio = st.sidebar.date_input("Fecha de inicio", value=fecha_min.date(),
                                                  min_value=fecha_min.date(), max_value=fecha_max.date())
            fecha_fin = st.sidebar.date_input("Fecha de fin", value=fecha_max.date(),
                                               min_value=fecha_min.date(), max_value=fecha_max.date())

            st.sidebar.subheader("📈 Variables a mostrar")
            mostrar_presion = st.sidebar.checkbox("Presión (Bar)", value=True)
            mostrar_temperatura = st.sidebar.checkbox("Temperatura (°C)", value=True)

            if not mostrar_presion and not mostrar_temperatura:
                st.warning("⚠️ Selecciona al menos una variable para mostrar")
            else:
                fecha_inicio_dt = pd.Timestamp(fecha_inicio)
                fecha_fin_dt = pd.Timestamp(fecha_fin).replace(hour=23, minute=59, second=59)
                df_filtrado = df[(df['DateTime'] >= fecha_inicio_dt) & (df['DateTime'] <= fecha_fin_dt)].copy()

                if len(df_filtrado) == 0:
                    st.warning("⚠️ No hay datos en el rango de fechas seleccionado")
                else:
                    st.markdown(f"**Mostrando {len(df_filtrado)} registros**")

                    if mostrar_presion:
                        with st.container(border=True):
                            st.markdown("**📈 Presión en el Tiempo**")
                            fig_p = go.Figure()
                            fig_p.add_trace(go.Scatter(
                                x=df_filtrado['DateTime'], y=df_filtrado['Presión'],
                                mode='lines+markers', name='Presión (Bar)',
                                line=dict(color='#1f77b4', width=2), marker=dict(size=4),
                                hovertemplate='<b>Fecha/Hora:</b> %{x|%d/%m/%Y %H:%M:%S}<br><b>Presión:</b> %{y:.2f} Bar<extra></extra>'
                            ))
                            fig_p.update_layout(
                                xaxis_title="Fecha y Hora", yaxis_title="Presión (Bar)",
                                height=340, template='plotly_white', hovermode='x unified',
                                margin=dict(t=20, b=40)
                            )
                            st.plotly_chart(fig_p, use_container_width=True)

                    if mostrar_temperatura:
                        with st.container(border=True):
                            st.markdown("**🌡️ Temperatura en el Tiempo**")
                            fig_t = go.Figure()
                            fig_t.add_trace(go.Scatter(
                                x=df_filtrado['DateTime'], y=df_filtrado['Temperatura'],
                                mode='lines+markers', name='Temperatura (°C)',
                                line=dict(color='#ff7f0e', width=2), marker=dict(size=4),
                                hovertemplate='<b>Fecha/Hora:</b> %{x|%d/%m/%Y %H:%M:%S}<br><b>Temperatura:</b> %{y:.2f} °C<extra></extra>'
                            ))
                            fig_t.update_layout(
                                xaxis_title="Fecha y Hora", yaxis_title="Temperatura (°C)",
                                height=340, template='plotly_white', hovermode='x unified',
                                margin=dict(t=20, b=40)
                            )
                            st.plotly_chart(fig_t, use_container_width=True)

                    st.subheader("📋 Tabla de Datos")
                    df_tabla = df_filtrado[['DateTime', 'Presión', 'Temperatura']].copy()
                    df_tabla['DateTime'] = df_tabla['DateTime'].dt.strftime('%d/%m/%Y %H:%M:%S')
                    df_tabla.columns = ['Fecha y Hora', 'Presión (Bar)', 'Temperatura (°C)']
                    st.dataframe(df_tabla, use_container_width=True, hide_index=True)

                    st.subheader("📅 Promedios Diarios")
                    df_filtrado['Fecha'] = df_filtrado['DateTime'].dt.date
                    df_diario = df_filtrado.groupby('Fecha')[['Presión', 'Temperatura']].agg(['mean', 'min', 'max', 'count'])
                    df_diario.columns = ['Presión_Promedio', 'Presión_Min', 'Presión_Max', 'Presión_Registros',
                                         'Temperatura_Promedio', 'Temperatura_Min', 'Temperatura_Max', 'Temperatura_Registros']
                    df_diario = df_diario.reset_index()
                    df_diario['Fecha'] = df_diario['Fecha'].astype(str)
                    st.dataframe(df_diario, use_container_width=True, hide_index=True, column_config={
                        "Presión_Promedio": st.column_config.NumberColumn(label="Presión Promedio (Bar)", format="%.2f"),
                        "Presión_Min": st.column_config.NumberColumn(label="Presión Mín (Bar)", format="%.2f"),
                        "Presión_Max": st.column_config.NumberColumn(label="Presión Máx (Bar)", format="%.2f"),
                        "Presión_Registros": st.column_config.NumberColumn(label="Registros", format="%d"),
                        "Temperatura_Promedio": st.column_config.NumberColumn(label="Temp. Promedio (°C)", format="%.2f"),
                        "Temperatura_Min": st.column_config.NumberColumn(label="Temp. Mín (°C)", format="%.2f"),
                        "Temperatura_Max": st.column_config.NumberColumn(label="Temp. Máx (°C)", format="%.2f"),
                        "Temperatura_Registros": st.column_config.NumberColumn(label="Registros", format="%d"),
                    })

                    st.subheader("📊 Estadísticas Generales")
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.metric("Presión Promedio", f"{df_filtrado['Presión'].mean():.2f} Bar",
                                  f"{df_filtrado['Presión'].std():.2f} (std)")
                    with col2:
                        st.metric("Temperatura Promedio", f"{df_filtrado['Temperatura'].mean():.2f} °C",
                                  f"{df_filtrado['Temperatura'].std():.2f} (std)")
                    with col3:
                        st.metric("Registros en Rango", f"{len(df_filtrado)}")

                    fecha_min_val = df_filtrado['DateTime'].min()
                    fecha_max_val = df_filtrado['DateTime'].max()
                    df_min_fecha = df_filtrado[df_filtrado['DateTime'].dt.date == fecha_min_val.date()]
                    presion_min_fecha = df_min_fecha['Presión'].iloc[0] if len(df_min_fecha) > 0 else None
                    temp_min_fecha = df_min_fecha['Temperatura'].iloc[0] if len(df_min_fecha) > 0 else None
                    df_max_fecha = df_filtrado[df_filtrado['DateTime'].dt.date == fecha_max_val.date()]
                    presion_max_fecha = df_max_fecha['Presión'].iloc[-1] if len(df_max_fecha) > 0 else None
                    temp_max_fecha = df_max_fecha['Temperatura'].iloc[-1] if len(df_max_fecha) > 0 else None

                    if presion_min_fecha is not None and presion_max_fecha is not None:
                        var_presion = presion_max_fecha - presion_min_fecha
                        var_presion_pct = (var_presion / presion_min_fecha * 100) if presion_min_fecha != 0 else 0
                        with col4:
                            st.metric("Variación Presión", f"{var_presion:.2f} Bar",
                                      f"{var_presion_pct:.2f}% ({fecha_min_val.strftime('%d/%m')} a {fecha_max_val.strftime('%d/%m')})")
                    if temp_min_fecha is not None and temp_max_fecha is not None:
                        var_temp = temp_max_fecha - temp_min_fecha
                        var_temp_pct = (var_temp / temp_min_fecha * 100) if temp_min_fecha != 0 else 0
                        with col5:
                            st.metric("Variación Temperatura", f"{var_temp:.2f} °C",
                                      f"{var_temp_pct:.2f}% ({fecha_min_val.strftime('%d/%m')} a {fecha_max_val.strftime('%d/%m')})")

                    st.markdown("---")
                    col_print, _ = st.columns([1, 4])
                    with col_print:
                        pdf_data = generar_pdf_reporte(
                            df_diario, df_filtrado, fecha_min_val, fecha_max_val,
                            presion_min_fecha, presion_max_fecha,
                            temp_min_fecha, temp_max_fecha,
                            mostrar_presion, mostrar_temperatura
                        )
                        if pdf_data:
                            st.download_button(
                                label="📥 Descargar Reporte en PDF",
                                data=pdf_data,
                                file_name=f"Reporte_{fecha_min_val.strftime('%Y%m%d')}_a_{fecha_max_val.strftime('%Y%m%d')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
        else:
            st.error("No se pudieron procesar los archivos. Verifica que los CSVs sean validos.")
    else:
        st.info("Carga uno o mas archivos CSV de GEO-PSI para comenzar.")

# ============================================================
# FLUJO: DataLogger
# ============================================================
elif formato == "DataLogger":

    # Colores y unidades por tipo de variable
    COLORES_TIPO   = {"Presión": "#1f77b4", "Temperatura": "#ff7f0e", "Flujo": "#2ca02c", "Otro": "#9467bd"}
    UNIDADES_TIPO  = {"Presión": "Bar", "Temperatura": "°C", "Flujo": "m³/h", "Otro": ""}
    TIPOS_VARIABLE = list(COLORES_TIPO.keys())

    st.sidebar.subheader("📁 Cargar Datos DataLogger")
    archivo_dl = st.sidebar.file_uploader(
        "Selecciona archivo CSV de DataLogger",
        type=['csv'],
        key="dl_uploader",
        help="Encabezados en fila 17 · Col 1: Fecha (dd/mm/yyyy) · Col 2: Hora · Col 3-6: Canales de datos"
    )

    if archivo_dl:
        df_raw, canales_info = procesar_csv_datalogger(archivo_dl)

        if df_raw is not None and len(canales_info) > 0:

            # ---- Configuración de canales ----
            st.sidebar.subheader("⚙️ Configuración de Canales")
            config_canales = []
            for i, info in canales_info.items():
                estado_icono = "✅" if info['tiene_datos'] else "⬜"
                with st.sidebar.expander(f"Canal {i} {estado_icono}  —  {info['n_registros']} registros"):
                    activo = st.checkbox("Activo", value=info['tiene_datos'], key=f"dl_{i}_activo")
                    nombre = st.text_input("Nombre de la variable", value=f"Canal {i}", key=f"dl_{i}_nombre")
                    tipo   = st.selectbox("Tipo", TIPOS_VARIABLE, key=f"dl_{i}_tipo")
                    unidad = st.text_input("Unidad / Magnitud",
                                           value=UNIDADES_TIPO.get(tipo, ""),
                                           key=f"dl_{i}_unidad")
                    config_canales.append({
                        'canal': i, 'col': info['col'], 'activo': activo,
                        'nombre': nombre, 'tipo': tipo, 'unidad': unidad,
                        'color': COLORES_TIPO.get(tipo, "#333333")
                    })

            activos = [c for c in config_canales if c['activo']]

            if not activos:
                st.warning("⚠️ Activa al menos un canal en la configuración.")
            else:
                # Construir DataFrame procesado
                df_dl = df_raw[['DateTime']].copy()
                for c in activos:
                    df_dl[c['nombre']] = pd.to_numeric(df_raw[c['col']], errors='coerce')
                nombres_activos = [c['nombre'] for c in activos]
                df_dl = df_dl.dropna(subset=nombres_activos, how='all').reset_index(drop=True)

                st.sidebar.success(f"✅ {len(df_dl)} registros · {len(activos)} canal(es) activo(s)")

                with st.sidebar.expander("ℹ️ Información"):
                    st.write(f"**Fecha inicio:** {df_dl['DateTime'].min().strftime('%d/%m/%Y %H:%M')}")
                    st.write(f"**Fecha fin:** {df_dl['DateTime'].max().strftime('%d/%m/%Y %H:%M')}")
                    for c in activos:
                        serie = df_dl[c['nombre']].dropna()
                        st.write(f"**{c['nombre']}:** {serie.min():.2f} – {serie.max():.2f} {c['unidad']}")

                # ---- Filtro de fechas ----
                st.sidebar.subheader("🔍 Filtro de Fechas")
                f_min = df_dl['DateTime'].min()
                f_max = df_dl['DateTime'].max()
                fecha_inicio_dl = st.sidebar.date_input("Fecha inicio", value=f_min.date(),
                                                         min_value=f_min.date(), max_value=f_max.date(),
                                                         key="dl_fi")
                fecha_fin_dl = st.sidebar.date_input("Fecha fin", value=f_max.date(),
                                                      min_value=f_min.date(), max_value=f_max.date(),
                                                      key="dl_ff")

                fi_dt = pd.Timestamp(fecha_inicio_dl)
                ff_dt = pd.Timestamp(fecha_fin_dl).replace(hour=23, minute=59, second=59)
                df_filt = df_dl[(df_dl['DateTime'] >= fi_dt) & (df_dl['DateTime'] <= ff_dt)].copy()

                if len(df_filt) == 0:
                    st.warning("⚠️ No hay datos en el rango seleccionado.")
                else:
                    st.markdown(f"**Mostrando {len(df_filt)} registros · {len(activos)} canal(es)**")

                    # ---- Gráficas individuales por canal (en recuadros) ----
                    n_act = len(activos)
                    for c in activos:
                        col_nombre = c['nombre']
                        if col_nombre not in df_filt.columns:
                            continue
                        unidad_label = c['unidad'] if c['unidad'] else ""
                        titulo_card = f"**📊 {col_nombre}**" + (f"  —  {unidad_label}" if unidad_label else "")
                        with st.container(border=True):
                            st.markdown(titulo_card)
                            fig_c = go.Figure()
                            fig_c.add_trace(go.Scatter(
                                x=df_filt['DateTime'],
                                y=df_filt[col_nombre],
                                mode='lines+markers',
                                name=f"{col_nombre} ({unidad_label})" if unidad_label else col_nombre,
                                line=dict(color=c['color'], width=2),
                                marker=dict(size=4),
                                hovertemplate=(
                                    f"<b>Fecha/Hora:</b> %{{x|%d/%m/%Y %H:%M:%S}}<br>"
                                    f"<b>{col_nombre}:</b> %{{y:.2f}} {unidad_label}<extra></extra>"
                                )
                            ))
                            fig_c.update_layout(
                                xaxis_title="Fecha y Hora",
                                yaxis_title=f"{col_nombre} ({unidad_label})" if unidad_label else col_nombre,
                                height=300, template='plotly_white', hovermode='x unified',
                                margin=dict(t=20, b=40)
                            )
                            st.plotly_chart(fig_c, use_container_width=True)

                    # ---- Tabla de datos ----
                    st.subheader("📋 Tabla de Datos")
                    df_tabla_dl = df_filt.copy()
                    df_tabla_dl['DateTime'] = df_tabla_dl['DateTime'].dt.strftime('%d/%m/%Y %H:%M:%S')
                    df_tabla_dl = df_tabla_dl.rename(columns={'DateTime': 'Fecha y Hora'})
                    st.dataframe(df_tabla_dl, use_container_width=True, hide_index=True)

                    # ---- Estadísticas por canal ----
                    st.subheader("📊 Estadísticas por Canal")
                    cols_stat = st.columns(min(n_act, 4))
                    for i, c in enumerate(activos):
                        col_nombre = c['nombre']
                        if col_nombre not in df_filt.columns:
                            continue
                        serie = df_filt[col_nombre].dropna()
                        with cols_stat[i % len(cols_stat)]:
                            st.metric(
                                label=f"{c['tipo']}: {col_nombre}",
                                value=f"{serie.mean():.2f} {c['unidad']}",
                                delta=f"σ {serie.std():.2f}  ·  Min {serie.min():.2f}  ·  Max {serie.max():.2f}"
                            )

                    # ---- Promedios diarios por canal ----
                    st.subheader("📅 Promedios Diarios por Canal")
                    df_filt_cp = df_filt.copy()
                    df_filt_cp['Fecha'] = df_filt_cp['DateTime'].dt.date
                    cols_canal = [c['nombre'] for c in activos if c['nombre'] in df_filt_cp.columns]
                    df_diario_dl = df_filt_cp.groupby('Fecha')[cols_canal].agg(['mean', 'min', 'max', 'count']).round(3)
                    df_diario_dl.columns = [f"{col}_{stat}" for col, stat in df_diario_dl.columns]
                    df_diario_dl = df_diario_dl.reset_index()
                    df_diario_dl['Fecha'] = df_diario_dl['Fecha'].astype(str)
                    st.dataframe(df_diario_dl, use_container_width=True, hide_index=True)

                    st.markdown("---")
                    col_print_dl, _ = st.columns([1, 4])
                    with col_print_dl:
                        pdf_data_dl = generar_pdf_datalogger(
                            df_filt, df_diario_dl, activos, fi_dt, ff_dt
                        )
                        if pdf_data_dl:
                            st.download_button(
                                label="📥 Descargar Reporte en PDF",
                                data=pdf_data_dl,
                                file_name=f"Reporte_DL_{fi_dt.strftime('%Y%m%d')}_a_{ff_dt.strftime('%Y%m%d')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )

        elif df_raw is not None:
            st.warning("⚠️ No se detectaron canales de datos en el archivo. Verifica el formato.")
    else:
        st.info("Carga un archivo CSV de DataLogger para comenzar.\n\n"
                "**Formato esperado:** encabezados en fila 17, Fecha (dd/mm/yyyy) en col 1, Hora en col 2, datos en col 3-6.")
