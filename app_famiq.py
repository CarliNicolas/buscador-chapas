import streamlit as st
import pandas as pd
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Buscador de Chapas - Famiq", page_icon="🔍", layout="wide")

@st.cache_data
def cargar_datos():
    # 1. Leer el archivo con detección automática de separador
    df = pd.read_csv("datos.csv", encoding="latin-1", sep=None, engine='python', on_bad_lines='skip')
    
    # 2. Limpieza agresiva de nombres de columnas
    df.columns = [str(c).strip() for c in df.columns]

    # 3. Mapeo de columnas (Busca el nombre real aunque varíe un poco)
    def buscar_columna(posibles_nombres):
        for nombre in posibles_nombres:
            if nombre in df.columns:
                return nombre
        return None

    col_espesor = buscar_columna(['Espesor', 'ESPESOR', 'espesor'])
    col_ancho = buscar_columna(['Ancho', 'ANCHO', 'ancho'])
    col_largo = buscar_columna(['Largo', 'LARGO', 'largo'])
    col_precio_kg = buscar_columna(['Precio / Kg', 'PRECIO / KG', 'Precio/Kg'])
    col_precio_un = buscar_columna(['Precio / Unidad', 'PRECIO / UNIDAD', 'Precio/Unidad'])
    col_calidad = buscar_columna(['Calidad', 'CALIDAD', 'calidad'])
    col_oferta = buscar_columna(['Inoxsale', 'INOXSALE', 'inoxsale'])

    # 4. Funciones de limpieza
    def limpiar_precio(x):
        if pd.isna(x): return 0.0
        x = str(x).replace('USD', '').replace('\n', '').strip()
        x = x.replace('.', '').replace(',', '.')
        try: return float(x)
        except: return 0.0

    def limpiar_dim(x):
        if pd.isna(x): return 0.0
        x = str(x).lower().replace('mm', '').replace(',', '.').strip()
        try: return float(x)
        except: return 0.0

    # 5. Procesar datos solo si las columnas existen
    if col_precio_kg: df['Precio USD/Kg'] = df[col_precio_kg].apply(limpiar_precio)
    else: df['Precio USD/Kg'] = 0.0

    if col_precio_un: df['Precio Final USD'] = df[col_precio_un].apply(limpiar_precio)
    else: df['Precio Final USD'] = 0.0
    
    if col_espesor: df['Espesor_num'] = df[col_espesor].apply(limpiar_dim)
    else: df['Espesor_num'] = 0.0

    if col_ancho: df['Ancho_num'] = df[col_ancho].apply(limpiar_dim)
    else: df['Ancho_num'] = 0.0

    if col_largo: df['Largo_num'] = df[col_largo].apply(limpiar_dim)
    else: df['Largo_num'] = 0.0

    # Descuento
    if col_oferta:
        df['Descuento %'] = df[col_oferta].apply(lambda x: int(str(x).split('%')[0]) if 'OFF' in str(x) else 0)
    else:
        df['Descuento %'] = 0

    return df, col_calidad, col_espesor, col_oferta

# --- INTERFAZ ---
st.title("🛠️ Buscador de Chapas para Papá")

try:
    df, col_calidad, col_espesor, col_oferta = cargar_datos()

    # Filtros
    st.sidebar.header("Filtros")
    
    # Filtro Calidad
    if col_calidad:
        calidades = sorted([str(x) for x in df[col_calidad].unique() if pd.notna(x)])
        calidad_sel = st.sidebar.multiselect("Calidad:", calidades, default=calidades[:2] if len(calidades)>1 else calidades)
    
    # Filtro Espesor
    lista_esp = sorted([float(x) for x in df['Espesor_num'].unique() if x > 0])
    if lista_esp:
        esp_sel = st.sidebar.select_slider("Espesor (mm):", options=lista_esp, value=(min(lista_esp), max(lista_esp)))
    
    solo_ofertas = st.sidebar.checkbox("💥 Ver solo Liquidaciones")

    # Filtrado
    mask = (df['Espesor_num'] >= esp_sel[0]) & (df['Espesor_num'] <= esp_sel[1])
    if calidad_sel: mask &= df[col_calidad].isin(calidad_sel)
    if solo_ofertas: mask &= (df['Descuento %'] > 0)

    df_final = df[mask].sort_values('Precio USD/Kg', ascending=True)

    # Mostrar tabla
    cols = [col_calidad, col_espesor, 'Ancho', 'Largo', col_oferta, 'Precio USD/Kg', 'Precio Final USD']
    cols = [c for c in cols if c in df_final.columns or c in ['Precio USD/Kg', 'Precio Final USD']]
    
    st.dataframe(
        df_final[cols].style.format({'Precio USD/Kg': '${:.2f}', 'Precio Final USD': '${:.2f}'}),
        use_container_width=True,
        hide_index=True
    )

except Exception as e:
    st.error("Error de lectura. Revisa que el archivo CSV en GitHub no tenga filas vacías al principio.")
    st.write(e)
