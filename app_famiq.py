import streamlit as st
import pandas as pd
import re
import os

st.set_page_config(page_title="Buscador de Gangas - Famiq", layout="wide")

@st.cache_data
def cargar_datos():
    archivos = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not archivos: return None
    
    df = pd.read_csv(archivos[0], encoding="latin-1", sep=None, engine='python', on_bad_lines='skip')
    df.columns = [str(c).replace('"', '').strip() for c in df.columns]

    def extraer_num(txt):
        txt = str(txt)
        if pd.isna(txt) or "CONSULTAR" in txt.upper(): return 0.0
        numeros = re.findall(r'[\d.,]+', txt)
        if not numeros: return 0.0
        val = numeros[-1]
        if ',' in val and '.' in val: val = val.replace('.', '').replace(',', '.')
        elif ',' in val: val = val.replace(',', '.')
        try: return float(val)
        except: return 0.0

    c_sku = next((c for c in df.columns if 'sku' in c.lower()), None)
    c_esp = next((c for c in df.columns if 'espesor' in c.lower()), None)
    c_anc = next((c for c in df.columns if 'ancho' in c.lower()), None)
    c_lar = next((c for c in df.columns if 'largo' in c.lower()), None)
    c_pkg = next((c for c in df.columns if 'kg' in c.lower()), None)
    c_pun = next((c for c in df.columns if 'unidad' in c.lower()), None)
    c_cal = next((c for c in df.columns if 'calidad' in c.lower()), None)
    c_ino = next((c for c in df.columns if 'inox' in c.lower() or 'sale' in c.lower()), None)

    df['pkg_n'] = df[c_pkg].apply(extraer_num) if c_pkg else 0.0
    df['pun_n'] = df[c_pun].apply(extraer_num) if c_pun else 0.0
    df['esp_n'] = df[c_esp].apply(extraer_num) if c_esp else 0.0
    df['anc_n'] = df[c_anc].apply(extraer_num) if c_anc else 0.0
    df['lar_n'] = df[c_lar].apply(extraer_num) if c_lar else 0.0
    
    df = df[df['pkg_n'] > 0.1].copy() # Filtramos precios basura menores a 0.1 USD

    # --- LÓGICA DE IA (Detección de Anomalías) ---
    # Calculamos el precio promedio por Calidad y Espesor
    if c_cal and c_esp:
        stats = df.groupby([c_cal, 'esp_n'])['pkg_n'].transform('median')
        # Si el precio es menos del 40% del precio normal para esa chapa, es una anomalía
        df['es_anomalia'] = df['pkg_n'] < (stats * 0.4)
    
    return df, c_sku, c_cal, c_esp, c_anc, c_lar, c_ino

st.title("🔍 Buscador de Chapas para Papá")

datos = cargar_datos()

if datos:
    df, col_sku, col_cal, col_esp, col_anc, col_lar, col_ino = datos
    
    st.sidebar.header("Medidas Estándar")
    medidas_pre = {
        "Manual / Ver todas": (None, None),
        "1000 x 2000 mm": (1000, 2000),
        "1220 x 2440 mm": (1220, 2440),
        "1250 x 2500 mm": (1250, 2500),
        "1500 x 3000 mm": (1500, 3000)
    }
    seleccion = st.sidebar.selectbox("Medida rápida:", list(medidas_pre.keys()))
    anc_pre, lar_pre = medidas_pre[seleccion]

    st.sidebar.header("Filtros de Precisión")
    
    # Espesor
    min_e, max_e = float(df['esp_n'].min()), float(df['esp_n'].max())
    c1, c2 = st.sidebar.columns(2)
    with c1: esp_min = st.number_input("E. Min:", 0.0, max_e, min_e, 0.1)
    with c2: esp_max = st.number_input("E. Max:", 0.0, max_e, max_e, 0.1)

    # Ancho y Largo
    min_a, max_a = float(df['anc_n'].min()), float(df['anc_n'].max())
    min_l, max_l = float(df['lar_n'].min()), float(df['lar_n'].max())
    
    with st.sidebar:
        c3, c4 = st.columns(2)
        with c3: anc_min = st.number_input("A. Min:", 0.0, max_a, float(anc_pre) if anc_pre else min_a)
        with c4: anc_max = st.number_input("A. Max:", 0.0, max_a, float(anc_pre) if anc_pre else max_a)
        
        c5, c6 = st.columns(2)
        with c5: lar_min = st.number_input("L. Min:", 0.0, max_l, float(lar_pre) if lar_pre else min_l)
        with c6: lar_max = st.number_input("L. Max:", 0.0, max_l, float(lar_pre) if lar_pre else max_l)

    st.sidebar.header("Detección Especial")
    # EL FILTRO DE IA
    ver_anomalias = st.sidebar.checkbox("🚨 Errores de tipeo (Muy baratos)")
    solo_ofertas = st.sidebar.checkbox("💥 Solo Liquidaciones")

    # --- APLICAR FILTROS ---
    mask = (df['esp_n'] >= esp_min) & (df['esp_n'] <= esp_max)
    mask &= (df['anc_n'] >= anc_min) & (df['anc_n'] <= anc_max)
    mask &= (df['lar_n'] >= lar_min) & (df['lar_n'] <= lar_max)
    
    if ver_anomalias:
        mask &= (df['es_anomalia'] == True)
    
    if solo_ofertas and col_ino:
        mask &= (df[col_ino].str.contains('%|sale', case=False, na=False))

    res = df[mask].sort_values('pkg_n', ascending=True)

    st.subheader(f"Se encontraron {len(res)} resultados")
    if ver_anomalias and len(res) > 0:
        st.warning("⚠️ Estos precios son tan bajos que podrían ser errores de carga de Famiq. ¡Aprovechá antes de que los corrijan!")

    # Formatear tabla
    res_v = res.copy()
    res_v['USD/Kg'] = res_v['pkg_n'].map('${:.2f}'.format)
    res_v['Total'] = res_v['pun_n'].map('${:.2f}'.format)
    
    columnas_finales = []
    if col_sku: columnas_finales.append(col_sku)
    if col_cal: columnas_finales.append(col_cal)
    if col_esp: columnas_finales.append(col_esp)
    if col_anc: columnas_finales.append(col_anc)
    if col_lar: columnas_finales.append(col_lar)
    columnas_finales += ['USD/Kg', 'Total']
    
    # Pintar de rojo si es anomalia
    def highlight_errors(s):
        return ['background-color: #ffcccc' if s.es_anomalia else '' for _ in s]

    st.dataframe(res_v[columnas_finales], use_container_width=True, hide_index=True)
    
    csv = res_v[columnas_finales].to_csv(index=False).encode('latin-1')
    st.download_button("📥 Descargar resultados", csv, "busqueda_famiq.csv", "text/csv")
else:
    st.error("Archivo no encontrado.")
