import os
import json
import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# Configuración de la página
st.set_page_config(page_title="Dashboard Meteorológico", layout="wide")
st.title("Dashboard de Análisis Meteorológico - OpenWeatherMap")

# ==========================================
# FASE 3: CONSUMO Y VALIDACIÓN DE LA API
# ==========================================

TOKEN_FILE = "token.txt"
JSON_CACHE = "respuesta.json"

# 1. Validar token fuera del código
if not os.path.exists(TOKEN_FILE):
    st.error(f"Error: No se encontró el archivo '{TOKEN_FILE}'. Deteniendo ejecución.")
    st.stop()

with open(TOKEN_FILE, "r") as f:
    api_key = f.read().strip()

if not api_key:
    st.error("Error: El token está vacío o incompleto.")
    st.stop()

# Botón en barra lateral para actualizar datos si se requiere
if st.sidebar.button("Actualizar datos desde la API"):
    if os.path.exists(JSON_CACHE):
        os.remove(JSON_CACHE)

# 2, 3 y 4. Petición HTTP y caché local
if not os.path.exists(JSON_CACHE):
    st.info("Consultando la API de OpenWeatherMap por primera vez...")
    
    # Lista de ciudades principales en el plan gratuito
    cities = [
        "London,UK", "Paris,FR", "Madrid,ES", "Rome,IT", "Berlin,DE",
        "Tokyo,JP", "New York,US", "Mexico City,MX", "Queretaro,MX", "Sydney,AU",
        "Toronto,CA", "Beijing,CN", "Cairo,EG", "Lima,PE", "Bogota,CO"
    ]
    list_data = []

    try:
        for city in cities:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}&lang=es"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                list_data.append(resp.json())
        
        if not list_data:
            st.error("Error: No se pudo obtener datos de ninguna ciudad. Revisa tu token.")
            st.stop()

        # Construir la estructura para el dataframe
        data = {"cnt": len(list_data), "list": list_data}
        
        with open(JSON_CACHE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión: {e}")
        st.stop()
else:
    with open(JSON_CACHE, "r", encoding="utf-8") as f:
        data = json.load(f)

# ==========================================
# FASE 3: LIMPIEZA DOCUMENTADA
# ==========================================
raw_list = data.get("list", [])
parsed_data = []

for item in raw_list:
    parsed_data.append({
        "ciudad": item.get("name"),
        "pais": item.get("sys", {}).get("country"),
        "temp": item.get("main", {}).get("temp"),
        "humedad": item.get("main", {}).get("humidity"),
        "presion": item.get("main", {}).get("pressure"),
        "viento": item.get("wind", {}).get("speed")
    })

df = pd.DataFrame(parsed_data)

len_inicial = len(df)
df_clean = df.dropna().copy()
len_final = len(df_clean)

# Filtro interactivo en la barra lateral
st.sidebar.header("Filtros")
ciudades_seleccionadas = st.sidebar.multiselect(
    "Seleccionar ciudades:",
    options=df_clean["ciudad"].tolist(),
    default=df_clean["ciudad"].tolist()
)

df_filtrado = df_clean[df_clean["ciudad"].isin(ciudades_seleccionadas)].copy()

if df_filtrado.empty:
    st.warning("Selecciona al menos una ciudad en el menú lateral para visualizar los datos.")
    st.stop()

# Resumen de limpieza y métricas en el dashboard
with st.expander("Ver informe de limpieza de datos"):
    st.write(f"**Registros iniciales:** {len_inicial} | **Registros utilizables:** {len_final} | **Registros perdidos:** {len_inicial - len_final}")
    st.write("**Valores faltantes por columna:**")
    st.write(df.isnull().sum())

col1, col2, col3, col4 = st.columns(4)
col1.metric("Ciudades Analizadas", len(df_filtrado))
col2.metric("Temperatura Media", f"{df_filtrado['temp'].mean():.1f} °C")
col3.metric("Humedad Media", f"{df_filtrado['humedad'].mean():.1f} %")
col4.metric("Viento Medio", f"{df_filtrado['viento'].mean():.1f} m/s")

st.divider()

# ==========================================
# FASE 4: LAS 4 GRÁFICAS (Paleta institucional)
# ==========================================
plt.rcParams['font.sans-serif'] = 'Arial'
plt.rcParams['axes.edgecolor'] = '#B9C3D1'

g_col1, g_col2 = st.columns(2)

# 1. Distribución (Histograma)
with g_col1:
    fig1 = plt.figure(figsize=(8, 5))
    plt.hist(df_filtrado['temp'], bins=25, color='#1C4C9A', edgecolor='white')
    plt.title("Las temperaturas urbanas se concentran entre los 15°C y 25°C", fontsize=11, fontweight='bold', pad=15)
    plt.xlabel("Temperatura (°C)")
    plt.ylabel("Número de ciudades")
    plt.grid(axis='y', linestyle='--', alpha=0.5, color='#B9C3D1')
    plt.tight_layout()
    st.pyplot(fig1)

# 2. Comparación (Barras)
with g_col2:
    top_paises = df_filtrado.groupby('pais')['viento'].mean().nlargest(10).reset_index()
    colores_barras = ['#1C4C9A'] + ['#B9C3D1'] * (len(top_paises) - 1)

    fig2 = plt.figure(figsize=(9, 5))
    plt.barh(top_paises['pais'][::-1], top_paises['viento'][::-1], color=colores_barras[::-1])
    plt.title("Determinados países insulares registran las mayores velocidades promedio de viento", fontsize=11, fontweight='bold', pad=15)
    plt.xlabel("Velocidad media del viento (m/s)")
    plt.ylabel("País (Código ISO)")
    plt.grid(axis='x', linestyle='--', alpha=0.5, color='#B9C3D1')
    plt.tight_layout()
    st.pyplot(fig2)

g_col3, g_col4 = st.columns(2)

# 3. Relación (Dispersión)
with g_col3:
    fig3 = plt.figure(figsize=(8, 5))
    plt.scatter(df_filtrado['temp'], df_filtrado['humedad'], color='#1C4C9A', alpha=0.6)
    plt.title("Se observa una ligera relación inversa entre la temperatura y el porcentaje de humedad", fontsize=11, fontweight='bold', pad=15)
    plt.xlabel("Temperatura (°C)")
    plt.ylabel("Humedad (%)")
    plt.grid(True, linestyle='--', alpha=0.5, color='#B9C3D1')
    plt.tight_layout()
    st.pyplot(fig3)

# 4. Evolución / Categorías
with g_col4:
    fig4 = plt.figure(figsize=(8, 5))
    if len(df_filtrado['viento'].unique()) >= 4:
        df_filtrado['rango_viento'] = pd.qcut(df_filtrado['viento'], q=4, labels=['Calma', 'Bajo', 'Moderado', 'Alto'], duplicates='drop')
        presion_viento = df_filtrado.groupby('rango_viento', observed=False)['presion'].mean().reset_index()
        plt.plot(presion_viento['rango_viento'], presion_viento['presion'], marker='o', color='#1C4C9A', linewidth=2.5)
    else:
        plt.plot(df_filtrado['ciudad'], df_filtrado['presion'], marker='o', color='#1C4C9A', linewidth=2.5)
        plt.xticks(rotation=45)
        
    plt.title("La presión atmosférica se mantiene estable independientemente de la categoría de viento", fontsize=11, fontweight='bold', pad=15)
    plt.xlabel("Categoría de intensidad de viento")
    plt.ylabel("Presión atmosférica promedio (hPa)")
    plt.grid(True, linestyle='--', alpha=0.5, color='#B9C3D1')
    plt.tight_layout()
    st.pyplot(fig4)

st.divider()

# Tabla de datos
st.subheader("Datos Meteorológicos Procesados")
st.dataframe(df_filtrado, use_container_width=True)