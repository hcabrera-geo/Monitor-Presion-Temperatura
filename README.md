# Monitor de Presión y Temperatura 📊

Aplicación interactiva en Python para procesar y visualizar datos de sensores de presión y temperatura desde archivos CSV.

## Características ✨

- 📁 **Carga de archivos CSV** - Sube tus datos fácilmente
- 📈 **Gráficas interactivas** - Visualiza presión y temperatura en el tiempo
- 🔍 **Filtrado por fecha** - Selecciona rangos específicos de datos
- 📊 **Filtrado por variable** - Muestra solo presión, solo temperatura, o ambas
- 📋 **Tabla de datos** - Visualiza los datos en formato tabular
- 📉 **Estadísticas** - Calcula promedio, desviación estándar y porcentajes

## Requisitos 📋

- Python 3.8 o superior
- Las librerías especificadas en `requirements.txt`

## Instalación 🚀

1. Navega a la carpeta del proyecto:
```bash
cd "c:\Users\hcabr\Apps\Presión Reservorio"
```

2. Crea un entorno virtual (recomendado):
```bash
python -m venv venv
venv\Scripts\activate
```

3. Instala las dependencias:
```bash
pip install -r requirements.txt
```

## Uso 💻

Ejecuta la aplicación con:
```bash
streamlit run app.py
```

La aplicación se abrirá en tu navegador (generalmente en `http://localhost:8501`)

## Formato del archivo CSV 📄

Tu archivo CSV debe contener al menos las siguientes columnas en este orden:

| Fecha | Hora | Presión | Temperatura | ... |
|-------|------|---------|-------------|-----|
| m/d/yyyy | hh:mm:ss | valor | valor | ... |
| 3/15/2024 | 10:30:45 | 2.5 | 25.3 | ... |

- **Fecha**: Formato m/d/yyyy (ej: 3/15/2024)
- **Hora**: Formato hh:mm:ss (ej: 10:30:45)
- **Presión**: Valores numéricos en Bar (ej: 2.5)
- **Temperatura**: Valores numéricos en °C (ej: 25.3)

Nota: La aplicación solo usará las primeras 4 columnas, aunque tu archivo tenga más datos.

## Funcionalidades Detalladas 🎯

### 1. Carga de datos
- Arrastra y suelta un archivo CSV o selecciónalo del explorador
- La aplicación automáticamente procesa y valida los datos

### 2. Información del dataset
- Número total de registros
- Rango de fechas disponibles
- Rangos de valores para presión y temperatura

### 3. Filtrado
- **Rango de fechas**: Selecciona fecha de inicio y fin
- **Variables**: Elige qué variables mostrar (presión, temperatura o ambas)

### 4. Visualización
- Las gráficas son interactivas (zoom, pan, hover para valores exactos)
- Las gráficas se adaptan según las variables seleccionadas
- Tabla con todos los datos del rango filtrado

### 5. Estadísticas
- Presión promedio y desviación estándar
- Temperatura promedio y desviación estándar
- Porcentaje de datos en el rango actual

## Ejemplo de archivo CSV 📝

```csv
Fecha,Hora,Presión,Temperatura,Nota
3/15/2024,10:30:45,2.45,25.3,OK
3/15/2024,10:31:45,2.46,25.4,OK
3/15/2024,10:32:45,2.47,25.5,OK
3/15/2024,10:33:45,2.46,25.4,OK
3/15/2024,10:34:45,2.45,25.3,OK
```

## Solución de problemas 🔧

**Error: "Error al procesar el archivo"**
- Verifica que el archivo esté en formato CSV
- Asegúrate de que las fechas están en formato m/d/yyyy
- Verifica que los valores de presión y temperatura sean números válidos

**Las gráficas no muestran datos**
- Comprueba que seleccionaste al menos una variable para mostrar
- Verifica que hay registros en el rango de fechas seleccionado

**La aplicación es lenta con muchos datos**
- Esto es normal con miles de registros. Filtra por rangos de fecha más pequeños

## Tecnologías utilizadas 🛠️

- **Streamlit** - Framework para crear aplicaciones web interactivas
- **Pandas** - Procesamiento y análisis de datos
- **Plotly** - Gráficas interactivas
- **NumPy** - Operaciones numéricas

## Licencia 📜

Uso libre para propósitos personales y educativos.

---

**¡Disfruta analizando tus datos de sensores!** 🎉
