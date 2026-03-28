import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Buscador de Chapas - Famiq", page_icon="🔍", layout="wide")

@st.cache_data
def cargar_datos():
    # 1. Leer el archivo intentando limpiar caracteres de control
    df = pd.read_csv("datos.csv", encoding="latin-1", sep=None, engine='python', on_bad_lines='skip')
    
    # 2. Limpiar nombres de columnas de comillas y espacios
    df.columns = [c.replace('"', '').strip() for c in df.columns]

    # 3. Función para limpiar celdas con "USD \n 1.23" o similares
    def limpiar_valor(x):
        if pd.isna(x): return ""
        # Quitamos comillas, USD, saltos de línea y espacios
        return str(x).replace('"', '').replace('USD', '').replace('\n', '').strip()

    # Limpiar todo el DataFrame de comillas visibles en los datos
    for col in df.columns:
        df[col] = df[col].apply(limpiar_valor)

    # 4. Mapeo de columnas corregido
    col_esp = 'Espesor'
    col_pre_kg = 'Precio / Kg'
    col_pre_un = 'Precio / Unidad'
    col_calidad = 'Calidad'
    col_inox = 'Inoxsale'

    # 5. Convertir a números
    def a_numero(x):
        if not x: return 0.0
        # Cambiamos coma decimal por punto y quitamos puntos de miles
        val = x.replace(' mm', '').replace('.', '').replace(',', '.')
        try: return float(val)
        except: return 0.0

    df['Espesor_num'] = df[col_esp].apply(a_numero) if col_esp in df.columns else 0.0
    df['Precio_Kg_num'] = df[col_pre_kg].apply(a_numero) if col_pre_kg in df.columns else 0.0
    df['Precio_Un_num'] = df[col_pre_un].apply(a_numero) if col_pre_un in df.columns else 0.0
    
    # Descuento
    df['Desc_val'] = df[col_inox].apply(lambda x: int(x.split('%')[0]) if '%' in str(x) else 0) if col_inox in df.columns else 0

    return df

st.title("🛠️ Buscador de Chapas para Papá")

try:
    df = cargar_datos()

    # Filtros
    st.sidebar.header("Filtros")
    
    # Calidad
    calidades = sorted([str(x) for x in df['Calidad'].unique() if x])
    cal_sel = st.sidebar.multiselect("Calidad:", calidades, default=calidades[:1] if calidades else [])

    # Espesor
    lista_esp = sorted([x for x in df['Espesor_num'].unique() if x > 0])
    if lista_esp:
        esp_sel = st.sidebar.select_slider("Espesor (mm):", options=lista_esp, value=(min(lista_esp), max(lista_esp)))
    else:
        esp_sel = (0.0, 100.0)

    solo_ofertas = st.sidebar.checkbox("💥 Ver solo Liquidaciones")

    # Aplicar filtros
    mask = (df['Espesor_num'] >= esp_sel[0]) & (df['Espesor_num'] <= esp_sel[1])
    if cal_sel: mask &= df['Calidad'].isin(cal_sel)
    if solo_ofertas: mask &= (df['Desc_val'] > 0)

    res = df[mask].sort_values('Precio_Kg_num', ascending=True)

    # Mostrar
    st.subheader(f"Resultados: {len(res)}")
    cols_ok = [c for c in ['SKU', 'Calidad', 'Espesor', 'Ancho', 'Largo', 'Inoxsale'] if c in res.columns]
    cols_ok += ['Precio_Kg_num', 'Precio_Un_num']
    
    st.dataframe(
        res[cols_ok].rename(columns={'Precio_Kg_num': 'USD/Kg', 'Precio_Un_num': 'Precio Total'}),
        use_container_width=True,
        hide_index=True
    )

except Exception as e:
    st.error("Error al procesar el archivo.")
    st.write(e)
