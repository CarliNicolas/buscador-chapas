import streamlit as st
import pandas as pd
import numpy as np

# Configuración de la página
st.set_page_config(page_title="Buscador de Chapas - Famiq", page_icon="🔍", layout="wide")

@st.cache_data
def cargar_datos():
    # 1. Leer el archivo con detección automática de separador
    try:
        df = pd.read_csv("datos.csv", encoding="latin-1", sep=None, engine='python', on_bad_lines='skip')
    except:
        # Si falla latin-1, intentamos utf-8 por las dudas
        df = pd.read_csv("datos.csv", encoding="utf-8", sep=None, engine='python', on_bad_lines='skip')
    
    # 2. Limpieza de nombres de columnas
    df.columns = [str(c).strip() for c in df.columns]

    # 3. Mapeo de columnas (Busca el nombre real)
    def buscar_columna(posibles_nombres):
        for nombre in posibles_nombres:
            if nombre in df.columns:
                return nombre
        return None

    col_espesor = buscar_columna(['Espesor', 'ESPESOR', 'espesor'])
    col_ancho = buscar_columna(['Ancho', 'ANCHO', 'ancho'])
    col_largo = buscar_columna(['Largo', 'LARGO', 'largo'])
    col_precio_kg = buscar_columna(['Precio / Kg', 'PRECIO / KG', 'Precio/Kg', 'Precio_Kg'])
    col_precio_un = buscar_columna(['Precio / Unidad', 'PRECIO / UNIDAD', 'Precio/Unidad', 'Precio_Unidad'])
    col_calidad = buscar_columna(['Calidad', 'CALIDAD', 'calidad'])
    col_oferta = buscar_columna(['Inoxsale', 'INOXSALE', 'inoxsale', 'Oferta'])

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

    # 5. Procesar datos
    df['Precio USD/Kg'] = df[col_precio_kg].apply(limpiar_precio) if col_precio_kg else 0.0
    df['Precio Final USD'] = df[col_precio_un].apply(limpiar_precio) if col_precio_un else 0.0
    df['Espesor_num'] = df[col_espesor].apply(limpiar_dim) if col_espesor else 0.0
    df['Ancho_num'] = df[col_ancho].apply(limpiar_dim) if col_ancho else 0.0
    df['Largo_num'] = df[col_largo].apply(limpiar_dim) if col_largo else 0.0

    if col_oferta:
        df['Descuento %'] = df[col_oferta].apply(lambda x: int(str(x).split('%')[0]) if 'OFF' in str(x) else 0)
    else:
        df['Descuento %'] = 0

    return df, col_calidad, col_espesor, col_oferta

# --- INTERFAZ ---
st.title("🛠️ Buscador de Chapas para Papá")

try:
    df, col_calidad, col_espesor, col_oferta = cargar_datos()

    # --- FILTROS (VALORES POR DEFECTO PARA EVITAR ERRORES) ---
    st.sidebar.header("Filtros")
    
    # Calidad
    calidad_sel = []
    if col_calidad:
        calidades = sorted([str(x) for x in df[col_calidad].unique() if pd.notna(x)])
        calidad_sel = st.sidebar.multiselect("Calidad:", calidades, default=calidades[:1])
    
    # Espesor
    lista_esp = sorted([float(x) for x in df['Espesor_num'].unique() if x > 0])
    if lista_esp:
        esp_sel = st.sidebar.select_slider("Espesor (mm):", options=lista_esp, value=(min(lista_esp), max(lista_esp)))
    else:
        # Si no hay espesores, creamos un rango genérico para que no falle
        esp_sel = (0.0, 999.0)
    
    solo_ofertas = st.sidebar.checkbox("💥 Ver solo Liquidaciones")

    # --- APLICAR MÁSCARA ---
    mask = (df['Espesor_num'] >= esp_sel[0]) & (df['Espesor_num'] <= esp_sel[1])
    if calidad_sel:
        mask &= df[col_calidad].isin(calidad_sel)
    if solo_ofertas:
        mask &= (df['Descuento %'] > 0)

    df_final = df[mask].sort_values('Precio USD/Kg', ascending=True)

    # --- MOSTRAR TABLA ---
    # Columnas que queremos mostrar si existen
    columnas_finales = []
    for c in [col_calidad, col_espesor, 'Ancho', 'Largo', col_oferta]:
        if c and c in df.columns: columnas_finales.append(c)
    
    columnas_finales.extend(['Precio USD/Kg', 'Precio Final USD'])

    st.subheader(f"Resultados ({len(df_final)} encontrados)")
    st.dataframe(
        df_final[columnas_finales].style.format({'Precio USD/Kg': '${:.2f}', 'Precio Final USD': '${:.2f}'}),
        use_container_width=True,
        hide_index=True
    )

except Exception as e:
    st.error("Error al mostrar los datos.")
    st.write("Detalle técnico para revisar:", e)
