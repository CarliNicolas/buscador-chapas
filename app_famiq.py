import streamlit as st
import pandas as pd
import numpy as np

# Configuración inicial de la app
st.set_page_config(page_title="Buscador de Gangas - Famiq", page_icon="🔍", layout="wide")

# Función para cargar y limpiar los datos (se guarda en caché para que sea ultra rápido)
@st.cache_data
def cargar_datos():
    # Cargar el archivo
    df = pd.read_csv("datos.csv", encoding="latin-1")
    
    # Limpiar precios
    def limpiar_precio(x):
        if pd.isna(x): return np.nan
        x = str(x).replace('USD', '').replace('\n', '').strip()
        x = x.replace('.', '').replace(',', '.')
        try: return float(x)
        except: return np.nan
        
    df['Precio USD/Kg'] = df['Precio / Kg'].apply(limpiar_precio)
    df['Precio Final USD'] = df['Precio / Unidad'].apply(limpiar_precio)
    
    # Limpiar dimensiones
    def limpiar_dim(x):
        if pd.isna(x): return np.nan
        x = str(x).lower().replace('mm', '').replace(',', '.').strip()
        try: return float(x)
        except: return np.nan

    df['Espesor (mm)'] = df['Espesor'].apply(limpiar_dim)
    df['Ancho (mm)'] = df['Ancho'].apply(limpiar_dim)
    df['Largo (mm)'] = df['Largo'].apply(limpiar_dim)
    
    # Extraer porcentaje de descuento para ordenar
    df['Descuento %'] = df['Inoxsale'].apply(lambda x: int(str(x).split('%')[0]) if 'OFF' in str(x) else 0)
    
    return df

# --- INTERFAZ DE LA APLICACIÓN ---

st.title("🛠️ Buscador Inteligente de Chapas - Famiq")
st.markdown("Filtra por medidas, calidad o espesor para encontrar las mejores oportunidades del listado.")

# Cargar los datos
df = cargar_datos()

# --- BARRA LATERAL (Filtros) ---
st.sidebar.header("Filtros de Búsqueda")

# 1. Filtro de Calidad (ej. 304, 430)
calidades_disponibles = df['Calidad'].dropna().unique().tolist()
calidad_seleccionada = st.sidebar.multiselect("Calidad del Acero:", calidades_disponibles, default=["304", "430"])

# 2. Filtro de Espesor
min_esp = float(df['Espesor (mm)'].min())
max_esp = float(df['Espesor (mm)'].max())
espesor_rango = st.sidebar.slider("Espesor (mm):", min_value=min_esp, max_value=max_esp, value=(min_esp, max_esp), step=0.1)

# 3. Filtro de Ancho y Largo
min_ancho, max_ancho = float(df['Ancho (mm)'].min()), float(df['Ancho (mm)'].max())
ancho_rango = st.sidebar.slider("Rango de Ancho (mm):", min_ancho, max_ancho, (min_ancho, max_ancho), step=100.0)

min_largo, max_largo = float(df['Largo (mm)'].min()), float(df['Largo (mm)'].max())
largo_rango = st.sidebar.slider("Rango de Largo (mm):", min_largo, max_largo, (min_largo, max_largo), step=100.0)

# 4. Solo Ofertas
solo_ofertas = st.sidebar.checkbox("💥 Mostrar SOLO artículos con descuento (Inoxsale)")

# --- APLICAR FILTROS ---
df_filtrado = df.copy()

if calidad_seleccionada:
    df_filtrado = df_filtrado[df_filtrado['Calidad'].isin(calidad_seleccionada)]

df_filtrado = df_filtrado[
    (df_filtrado['Espesor (mm)'] >= espesor_rango[0]) & (df_filtrado['Espesor (mm)'] <= espesor_rango[1]) &
    (df_filtrado['Ancho (mm)'] >= ancho_rango[0]) & (df_filtrado['Ancho (mm)'] <= ancho_rango[1]) &
    (df_filtrado['Largo (mm)'] >= largo_rango[0]) & (df_filtrado['Largo (mm)'] <= largo_rango[1])
]

if solo_ofertas:
    df_filtrado = df_filtrado[df_filtrado['Descuento %'] > 0]

# --- MOSTRAR RESULTADOS ---
st.subheader(f"Resultados encontrados: {len(df_filtrado)} chapas")

# Ordenar por el mejor precio por kilo por defecto
df_mostrar = df_filtrado[['SKU', 'Calidad', 'Espesor', 'Ancho', 'Largo', 'Inoxsale', 'Precio USD/Kg', 'Precio Final USD']]
df_mostrar = df_mostrar.sort_values(by=['Precio USD/Kg'])

# Mostrar la tabla en la app
st.dataframe(
    df_mostrar.style.format({'Precio USD/Kg': '${:.2f}', 'Precio Final USD': '${:.2f}'}),
    use_container_width=True,
    hide_index=True
)

st.success("💡 **Tip:** Las filas de arriba son las más baratas por kilo dentro de tus medidas seleccionadas.")
