import streamlit as st
import pandas as pd
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Buscador de Chapas - Famiq", page_icon="🔍", layout="wide")

@st.cache_data
def cargar_datos():
    # 1. Leer el archivo detectando automáticamente el separador (punto y coma o coma)
    # Usamos latin-1 para que no falle con acentos o símbolos de moneda
    df = pd.read_csv("datos.csv", encoding="latin-1", sep=None, engine='python', on_bad_lines='skip')
    
    # 2. Limpiar espacios invisibles en los nombres de las columnas
    df.columns = df.columns.str.strip()
    
    # 3. Funciones de limpieza de datos
    def limpiar_precio(x):
        if pd.isna(x): return np.nan
        x = str(x).replace('USD', '').replace('\n', '').strip()
        x = x.replace('.', '').replace(',', '.') # Quitar miles y ajustar decimales
        try: return float(x)
        except: return np.nan

    def limpiar_dim(x):
        if pd.isna(x): return np.nan
        x = str(x).lower().replace('mm', '').replace(',', '.').strip()
        try: return float(x)
        except: return np.nan

    # 4. Aplicar limpiezas a las columnas
    # Usamos nombres exactos del CSV de Famiq
    if 'Precio / Kg' in df.columns:
        df['Precio USD/Kg'] = df['Precio / Kg'].apply(limpiar_precio)
    if 'Precio / Unidad' in df.columns:
        df['Precio Final USD'] = df['Precio / Unidad'].apply(limpiar_precio)
    
    df['Espesor_num'] = df['Espesor'].apply(limpiar_dim)
    df['Ancho_num'] = df['Ancho'].apply(limpiar_dim)
    
    # Intentar limpiar Largo si existe la columna
    if 'Largo' in df.columns:
        df['Largo_num'] = df['Largo'].apply(limpiar_dim)
    else:
        df['Largo_num'] = 0

    # 5. Calcular porcentaje de descuento para ordenar por "gangas"
    df['Descuento %'] = df['Inoxsale'].apply(lambda x: int(str(x).split('%')[0]) if 'OFF' in str(x) else 0)
    
    return df

# --- INTERFAZ ---
st.title("🛠️ Buscador de Chapas para Papá")
st.markdown("Busca por medida o calidad para encontrar el mejor precio.")

try:
    df = cargar_datos()

    # --- FILTROS EN BARRA LATERAL ---
    st.sidebar.header("Filtros")
    
    # Filtro de Calidad
    calidades = sorted([str(x) for x in df['Calidad'].unique() if pd.notna(x)])
    calidad_sel = st.sidebar.multiselect("Calidad:", calidades, default=calidades[:2])

    # Filtro de Espesor
    lista_espesores = sorted([float(x) for x in df['Espesor_num'].unique() if x > 0])
    esp_sel = st.sidebar.select_slider("Espesor (mm):", options=lista_espesores, value=(min(lista_espesores), max(lista_espesores)))

    # Filtro de Solo Ofertas
    solo_ofertas = st.sidebar.checkbox("💥 Ver solo Liquidaciones (Inoxsale)")

    # --- LÓGICA DE FILTRADO ---
    mask = (df['Espesor_num'] >= esp_sel[0]) & (df['Espesor_num'] <= esp_sel[1])
    
    if calidad_sel:
        mask &= df['Calidad'].isin(calidad_sel)
    
    if solo_ofertas:
        mask &= (df['Descuento %'] > 0)

    df_final = df[mask].copy()

    # --- MOSTRAR RESULTADOS ---
    st.subheader(f"Se encontraron {len(df_final)} opciones:")
    
    # Ordenar por el precio por kilo más barato (la verdadera ganga)
    df_final = df_final.sort_values('Precio USD/Kg', ascending=True)

    # Columnas a mostrar al usuario
    cols_mostrar = ['SKU', 'Calidad', 'Espesor', 'Ancho', 'Largo', 'Inoxsale', 'Precio USD/Kg', 'Precio Final USD']
    
    # Mostrar tabla amigable
    st.dataframe(
        df_final[cols_mostrar].style.format({'Precio USD/Kg': '${:.2f}', 'Precio Final USD': '${:.2f}'}),
        use_container_width=True,
        hide_index=True
    )

    st.info("💡 Consejo: Las chapas al principio de la lista son las que tienen el mejor precio por kilo.")

except Exception as e:
    st.error("Hubo un problema al cargar los datos. Verifica que el archivo se llame 'datos.csv' en GitHub.")
    st.write(e)
