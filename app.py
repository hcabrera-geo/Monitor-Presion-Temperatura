import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import io

# Configuración de la página
st.set_page_config(
    page_title="Monitoreo de Presión y Temperatura Reservorio Ahuachapán",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

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


# Sección de carga de archivo
st.sidebar.subheader("📁 Cargar Datos")
archivos_cargados = st.sidebar.file_uploader(
    "Selecciona uno o más archivos CSV",
    type=['csv'],
    accept_multiple_files=True,
    help="Asegúrate de que los CSV tengan las columnas: Fecha, Hora, Presión, Temperatura"
)

if archivos_cargados:
    # Procesar múltiples archivos
    lista_dfs = []
    
    for archivo in archivos_cargados:
        df_temp = procesar_csv(archivo)
        if df_temp is not None and len(df_temp) > 0:
            lista_dfs.append(df_temp)
    
    if lista_dfs:
        # Concatenar todos los DataFrames
        df = pd.concat(lista_dfs, ignore_index=True)
        # Ordenar por DateTime nuevamente
        df = df.sort_values('DateTime')
        df = df.reset_index(drop=True)
        
        st.sidebar.success(f"✅ {len(archivos_cargados)} archivo(s) cargado(s): {len(df)} registros totales")
        
        # Mostrar información del dataset
        with st.sidebar.expander("ℹ️ Información de los Datos"):
            st.write(f"**Registros totales:** {len(df)}")
            st.write(f"**Fecha inicio:** {df['DateTime'].min().strftime('%d/%m/%Y %H:%M:%S')}")
            st.write(f"**Fecha fin:** {df['DateTime'].max().strftime('%d/%m/%Y %H:%M:%S')}")
            st.write(f"**Presión (Bar) - Rango:** {df['Presión'].min():.2f} - {df['Presión'].max():.2f}")
            st.write(f"**Temperatura (°C) - Rango:** {df['Temperatura'].min():.2f} - {df['Temperatura'].max():.2f}")
            st.write(f"**Archivos procesados:** {len(archivos_cargados)}")
        
        # Filtros
        st.sidebar.subheader("🔍 Filtros")
        
        # Filtro de rango de fechas
        fecha_min = df['DateTime'].min()
        fecha_max = df['DateTime'].max()
        
        fecha_inicio = st.sidebar.date_input(
            "Fecha de inicio",
            value=fecha_min.date(),
            min_value=fecha_min.date(),
            max_value=fecha_max.date()
        )
        
        fecha_fin = st.sidebar.date_input(
            "Fecha de fin",
            value=fecha_max.date(),
            min_value=fecha_min.date(),
            max_value=fecha_max.date()
        )
        
        # Filtro de variables
        st.sidebar.subheader("📈 Variables a mostrar")
        mostrar_presion = st.sidebar.checkbox("Presión (Bar)", value=True)
        mostrar_temperatura = st.sidebar.checkbox("Temperatura (°C)", value=True)
        
        if not mostrar_presion and not mostrar_temperatura:
            st.warning("⚠️ Selecciona al menos una variable para mostrar")
        else:
            # Aplicar filtro de fechas
            fecha_inicio_dt = pd.Timestamp(fecha_inicio)
            fecha_fin_dt = pd.Timestamp(fecha_fin).replace(hour=23, minute=59, second=59)
            
            df_filtrado = df[
                (df['DateTime'] >= fecha_inicio_dt) & 
                (df['DateTime'] <= fecha_fin_dt)
            ].copy()
            
            if len(df_filtrado) == 0:
                st.warning("⚠️ No hay datos en el rango de fechas seleccionado")
            else:
                st.markdown(f"**Mostrando {len(df_filtrado)} registros**")
                
                # Crear gráficas
                if mostrar_presion and mostrar_temperatura:
                    # Dos gráficas: una para presión y otra para temperatura
                    fig = make_subplots(
                        rows=2, cols=1,
                        subplot_titles=("Presión en el Tiempo", "Temperatura en el Tiempo"),
                        specs=[[{"secondary_y": False}], [{"secondary_y": False}]],
                        vertical_spacing=0.12
                    )
                    
                    # Gráfica de Presión
                    fig.add_trace(
                        go.Scatter(
                            x=df_filtrado['DateTime'],
                            y=df_filtrado['Presión'],
                            mode='lines+markers',
                            name='Presión (Bar)',
                            line=dict(color='#1f77b4', width=2),
                            marker=dict(size=4),
                            hovertemplate='<b>Fecha/Hora:</b> %{x|%d/%m/%Y %H:%M:%S}<br><b>Presión:</b> %{y:.2f} Bar<extra></extra>'
                        ),
                        row=1, col=1
                    )
                    
                    # Gráfica de Temperatura
                    fig.add_trace(
                        go.Scatter(
                            x=df_filtrado['DateTime'],
                            y=df_filtrado['Temperatura'],
                            mode='lines+markers',
                            name='Temperatura (°C)',
                            line=dict(color='#ff7f0e', width=2),
                            marker=dict(size=4),
                            hovertemplate='<b>Fecha/Hora:</b> %{x|%d/%m/%Y %H:%M:%S}<br><b>Temperatura:</b> %{y:.2f} °C<extra></extra>'
                        ),
                        row=2, col=1
                    )
                    
                    fig.update_xaxes(title_text="Fecha y Hora", row=2, col=1)
                    fig.update_yaxes(title_text="Presión (Bar)", row=1, col=1)
                    fig.update_yaxes(title_text="Temperatura (°C)", row=2, col=1)
                    
                else:
                    # Una sola gráfica
                    fig = go.Figure()
                    
                    if mostrar_presion:
                        fig.add_trace(
                            go.Scatter(
                                x=df_filtrado['DateTime'],
                                y=df_filtrado['Presión'],
                                mode='lines+markers',
                                name='Presión (Bar)',
                                line=dict(color='#1f77b4', width=2),
                                marker=dict(size=6),
                                hovertemplate='<b>Fecha/Hora:</b> %{x|%d/%m/%Y %H:%M:%S}<br><b>Presión:</b> %{y:.2f} Bar<extra></extra>'
                            )
                        )
                        fig.update_yaxes(title_text="Presión (Bar)")
                    
                    if mostrar_temperatura:
                        fig.add_trace(
                            go.Scatter(
                                x=df_filtrado['DateTime'],
                                y=df_filtrado['Temperatura'],
                                mode='lines+markers',
                                name='Temperatura (°C)',
                                line=dict(color='#ff7f0e', width=2),
                                marker=dict(size=6),
                                hovertemplate='<b>Fecha/Hora:</b> %{x|%d/%m/%Y %H:%M:%S}<br><b>Temperatura:</b> %{y:.2f} °C<extra></extra>'
                            )
                        )
                        fig.update_yaxes(title_text="Temperatura (°C)")
                    
                    fig.update_xaxes(title_text="Fecha y Hora")
                
                fig.update_layout(
                    title="Datos del Sensor",
                    hovermode='x unified',
                    height=600,
                    template='plotly_white'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Mostrar tabla de datos
                st.subheader("📋 Tabla de Datos")
                columnas_mostrar = ['DateTime', 'Presión', 'Temperatura']
                df_tabla = df_filtrado[columnas_mostrar].copy()
                df_tabla['DateTime'] = df_tabla['DateTime'].dt.strftime('%d/%m/%Y %H:%M:%S')
                df_tabla.columns = ['Fecha y Hora', 'Presión (Bar)', 'Temperatura (°C)']
                
                st.dataframe(
                    df_tabla,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Promedios por día
                st.subheader("📅 Promedios Diarios")
                df_filtrado['Fecha'] = df_filtrado['DateTime'].dt.date
                df_diario = df_filtrado.groupby('Fecha')[['Presión', 'Temperatura']].agg(['mean', 'min', 'max', 'count'])
                df_diario.columns = ['Presión_Promedio', 'Presión_Min', 'Presión_Max', 'Presión_Registros',
                                     'Temperatura_Promedio', 'Temperatura_Min', 'Temperatura_Max', 'Temperatura_Registros']
                df_diario = df_diario.reset_index()
                df_diario['Fecha'] = df_diario['Fecha'].astype(str)
                
                # Mostrar tabla de promedios diarios
                st.dataframe(
                    df_diario,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Presión_Promedio": st.column_config.NumberColumn(label="Presión Promedio (Bar)", format="%.2f"),
                        "Presión_Min": st.column_config.NumberColumn(label="Presión Mín (Bar)", format="%.2f"),
                        "Presión_Max": st.column_config.NumberColumn(label="Presión Máx (Bar)", format="%.2f"),
                        "Presión_Registros": st.column_config.NumberColumn(label="Registros Presión", format="%d"),
                        "Temperatura_Promedio": st.column_config.NumberColumn(label="Temperatura Promedio (°C)", format="%.2f"),
                        "Temperatura_Min": st.column_config.NumberColumn(label="Temperatura Mín (°C)", format="%.2f"),
                        "Temperatura_Max": st.column_config.NumberColumn(label="Temperatura Máx (°C)", format="%.2f"),
                        "Temperatura_Registros": st.column_config.NumberColumn(label="Registros Temperatura", format="%d"),
                    }
                )
                
                # Estadísticas
                st.subheader("📊 Estadísticas Generales")
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric(
                        "Presión Promedio",
                        f"{df_filtrado['Presión'].mean():.2f} Bar",
                        f"{df_filtrado['Presión'].std():.2f} (std)"
                    )
                
                with col2:
                    st.metric(
                        "Temperatura Promedio",
                        f"{df_filtrado['Temperatura'].mean():.2f} °C",
                        f"{df_filtrado['Temperatura'].std():.2f} (std)"
                    )
                
                with col3:
                    st.metric(
                        "Registros en Rango",
                        f"{len(df_filtrado)}"
                    )
                
                # Variación entre fecha más antigua y más reciente
                fecha_min_val = df_filtrado['DateTime'].min()
                fecha_max_val = df_filtrado['DateTime'].max()
                
                # Obtener valores en fecha más antigua
                df_min_fecha = df_filtrado[df_filtrado['DateTime'].dt.date == fecha_min_val.date()]
                presion_min_fecha = df_min_fecha['Presión'].iloc[0] if len(df_min_fecha) > 0 else None
                temp_min_fecha = df_min_fecha['Temperatura'].iloc[0] if len(df_min_fecha) > 0 else None
                
                # Obtener valores en fecha más reciente
                df_max_fecha = df_filtrado[df_filtrado['DateTime'].dt.date == fecha_max_val.date()]
                presion_max_fecha = df_max_fecha['Presión'].iloc[-1] if len(df_max_fecha) > 0 else None
                temp_max_fecha = df_max_fecha['Temperatura'].iloc[-1] if len(df_max_fecha) > 0 else None
                
                if presion_min_fecha is not None and presion_max_fecha is not None:
                    var_presion = presion_max_fecha - presion_min_fecha
                    var_presion_pct = (var_presion / presion_min_fecha * 100) if presion_min_fecha != 0 else 0
                    with col4:
                        st.metric(
                            "Variación Presión",
                            f"{var_presion:.2f} Bar",
                            f"{var_presion_pct:.2f}% ({fecha_min_val.strftime('%d/%m')} a {fecha_max_val.strftime('%d/%m')})"
                        )
                
                if temp_min_fecha is not None and temp_max_fecha is not None:
                    var_temp = temp_max_fecha - temp_min_fecha
                    var_temp_pct = (var_temp / temp_min_fecha * 100) if temp_min_fecha != 0 else 0
                    with col5:
                        st.metric(
                            "Variación Temperatura",
                            f"{var_temp:.2f} °C",
                            f"{var_temp_pct:.2f}% ({fecha_min_val.strftime('%d/%m')} a {fecha_max_val.strftime('%d/%m')})"
                           f"{(len(df_filtrado)/len(df)*100):.1f}% del total"
                        )
    else:
        st.error("No se pudieron procesar los archivos. Verifica que los CSVs sean validos.")

else:
    st.info("Carga uno o mas archivos CSV para comenzar. Los archivos deben contener las columnas: Fecha, Hora, Presion, Temperatura")
