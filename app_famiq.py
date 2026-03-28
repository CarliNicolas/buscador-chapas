import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Buscador de Chapas - Famiq", page_icon="🔍", layout="wide")

@st.cache_data
def cargar_datos():
    # 1. Leer el archivo intentando separar bien las columnas
    df = pd.read_csv("datos.csv", encoding="latin-1", sep=None, engine='python', on_bad_lines='skip')
    
    # 2. Limpiar nombres de columnas: quitar comillas, espacios y saltos de línea
    df.columns = [str(c).replace('"', '').replace('\n', ' ').strip() for c in df.columns]

    # 3. Función para limpiar el contenido de las celdas
    def limpiar_texto(x):
        if pd.isna(x): return ""
        return str(x).replace('"', '').replace('USD', '').replace('\n', ' ').strip()

    for col in df.columns:
        df[col] = df[col].apply(limpiar_texto)

    # 4. Buscador inteligente de columnas (para que no falle por el nombre exacto)
    def encontrar(lista_posibles):
        for p in lista_posibles:
            for c in df.columns:
                if p.lower() in c.lower(): return c
        return None

    c_sku = encontrar(['sku'])
    c_esp = encontrar(['espesor', 'esp'])
    c_cal = encontrar(['calidad', 'cal'])
    c_anc = encontrar(['ancho'])
    c_lar = encontrar(['largo'])
    c_pkg = encontrar(['precio / kg', 'kg'])
    c_pun = encontrar(['precio / unidad', 'unidad'])
    c_ino = encontrar(['inoxsale', 'oferta'])

    # 5. Convertir a números
    def a_num(x):
        if not x: return 0.0
        # Quitamos todo lo que no sea número, coma o punto
        limpio = "".join(c for c in str(x) if c.isdigit() or c in ',.')
        if not limpio: return 0.0
        # Si tiene puntos y comas, asumimos formato latino (1.000,00)
        if '.' in limpio and ',' in limpio:
            limpio = limpio.replace('.', '').replace(',', '.')
        else:
            limpio = limpio.replace(',', '.')
        try: return float(limpio)
        except: return 0.0

    # Creamos columnas numéricas auxiliares
    df['esp_n'] = df[c_esp].apply(a_num) if c_esp else 0.0
    df['pkg_n'] = df[c_pkg].apply(a_num) if c_pkg else 0.0
    df['pun_n'] = df[c_pun].apply(a_num) if c_pun else 0.0
    df['desc_n'] = df[c_ino].apply(lambda x: 1 if '%' in str(x) or 'sale' in str(x).lower() else 0) if c_ino else 0

    return df, c_sku, c_esp, c_cal, c_anc, c_lar, c_ino

st.title("🛠️ Buscador de Chapas para Papá")

try:
    df, c_sku, c_esp, c_cal, c_anc, c_lar, c_ino = cargar_datos()

    # Filtros laterales
    st.sidebar.header("Filtros")
    
    # Calidad
    col_cal = c_cal if c_cal else df.columns[0]
    opciones_cal = sorted([x for x in df[col_cal].unique() if x])
    cal_sel = st.sidebar.multiselect("Seleccionar Calidad:", opciones_cal, default=opciones_cal[:1] if opciones_cal else [])

    # Espesor
    lista_esp = sorted([x for x in df['esp_n'].unique() if x > 0])
    if lista_esp:
        esp_sel = st.sidebar.select_slider("Espesor (mm):", options=lista_esp, value=(min(lista_esp), max(lista_esp)))
    else:
        esp_sel = (0.0, 500.0)

    solo_ofertas = st.sidebar.checkbox("💥 Ver solo Liquidaciones")

    # Aplicar filtros
    mask = (df['esp_n'] >= esp_sel[0]) & (df['esp_n'] <= esp_sel[1])
    if cal_sel: mask &= df[col_cal].isin(cal_sel)
    if solo_ofertas: mask &= (df['desc_n'] > 0)

    res = df[mask].sort_values('pkg_n', ascending=True)

    # Mostrar Tabla
    st.subheader(f"Resultados: {len(res)} chapas")
    
    # Seleccionamos qué mostrar al usuario
    ver = [c for c in [c_sku, c_cal, c_esp, c_anc, c_lar, c_ino] if c]
    res_mostrar = res[ver].copy()
    res_mostrar['USD / Kg'] = res['pkg_n'].map('${:.2f}'.format)
    res_mostrar['Precio Total'] = res['pun_n'].map('${:.2f}'.format)

    st.dataframe(res_mostrar, use_container_width=True, hide_index=True)

except Exception as e:
    st.error("Todavía hay un problema con el formato del archivo.")
    st.write("Asegurate de que el archivo en GitHub se llame 'datos.csv'")
    st.info("Error detectado: " + str(e))
