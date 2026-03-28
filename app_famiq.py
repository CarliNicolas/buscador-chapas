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
    
    def desc_num(x):
        nums = re.findall(r'\d+', str(x))
        return int(nums[0]) if nums else 0
    df['desc_val'] = df[c_ino].apply(desc_num) if c_ino else 0

    df = df[df['pkg_n'] > 0.1].copy()

    if c_cal and c_esp:
        mediana = df.groupby([c_cal, 'esp_n'])['pkg_n'].transform('median')
        df['score_rentabilidad'] = (mediana / df['pkg_n']) * (1 + (df['desc_val'] / 100))
        df['es_anomalia'] = df['pkg_n'] < (mediana * 0.4)
    
    return df, c_sku, c_cal, c_esp, c_anc, c_lar, c_ino

datos = cargar_datos()

if datos:
    df, col_sku, col_cal, col_esp, col_anc, col_lar, col_ino = datos
    
    # --- LÓGICA DE MEMORIA (SESSION STATE) ---
    medidas_pre = {
        "Manual / Ver todas": (None, None),
        "1000 x 2000 mm": (1000.0, 2000.0),
        "1220 x 2440 mm": (1220.0, 2440.0),
        "1250 x 2500 mm": (1250.0, 2500.0),
        "1500 x 3000 mm": (1500.0, 3000.0)
    }

    def actualizar_medidas():
        sel = st.session_state.medida_rapida
        anc_p, lar_p = medidas_pre[sel]
        if anc_p:
            st.session_state.anc_min = anc_p
            st.session_state.anc_max = anc_p
            st.session_state.lar_min = lar_p
            st.session_state.lar_max = lar_p
        else:
            st.session_state.anc_min = float(df['anc_n'].min())
            st.session_state.anc_max = float(df['anc_n'].max())
            st.session_state.lar_min = float(df['lar_n'].min())
            st.session_state.lar_max = float(df['lar_n'].max())

    # Inicializar valores si no existen
    if 'anc_min' not in st.session_state:
        st.session_state.anc_min = float(df['anc_n'].min())
        st.session_state.anc_max = float(df['anc_n'].max())
        st.session_state.lar_min = float(df['lar_n'].min())
        st.session_state.lar_max = float(df['lar_n'].max())

    st.title("🔍 Buscador de Chapas para Papá")

    st.sidebar.header("Medidas Estándar")
    st.sidebar.selectbox("Elegir medida rápida:", list(medidas_pre.keys()), key="medida_rapida", on_change=actualizar_medidas)

    st.sidebar.header("Filtros de Precisión")
    
    # Espesor
    st.sidebar.subheader("Espesor (mm)")
    c1, c2 = st.sidebar.columns(2)
    with c1: esp_min = st.number_input("E. Min:", 0.0, 500.0, float(df['esp_n'].min()), 0.1)
    with c2: esp_max = st.number_input("E. Max:", 0.0, 500.0, float(df['esp_n'].max()), 0.1)

    # Ancho y Largo - Ahora usan la memoria de Session State
    max_a_limit = max(float(df['anc_n'].max()), 20000.0)
    max_l_limit = max(float(df['lar_n'].max()), 20000.0)
    
    st.sidebar.subheader("Ancho (mm)")
    c3, c4 = st.sidebar.columns(2)
    with c3: anc_min = st.number_input("A. Min:", 0.0, max_a_limit, key="anc_min")
    with c4: anc_max = st.number_input("A. Max:", 0.0, max_a_limit, key="anc_max")
    
    st.sidebar.subheader("Largo (mm)")
    c5, c6 = st.sidebar.columns(2)
    with c5: lar_min = st.number_input("L. Min:", 0.0, max_l_limit, key="lar_min")
    with c6: lar_max = st.number_input("L. Max:", 0.0, max_l_limit, key="lar_max")

    st.sidebar.header("Opciones Especiales")
    orden_rentable = st.sidebar.checkbox("⭐ Ordenar por mejor Oportunidad", value=True)
    ver_anomalias = st.sidebar.checkbox("🚨 Errores de tipeo (Muy baratos)")
    solo_ofertas = st.sidebar.checkbox("💥 Solo Liquidaciones")

    # --- APLICAR FILTROS ---
    mask = (df['esp_n'] >= esp_min) & (df['esp_n'] <= esp_max)
    mask &= (df['anc_n'] >= anc_min) & (df['anc_n'] <= anc_max)
    mask &= (df['lar_n'] >= lar_min) & (df['lar_n'] <= lar_max)
    
    if ver_anomalias: mask &= (df['es_anomalia'] == True)
    if solo_ofertas and col_ino: mask &= (df['desc_val'] > 0)

    res = df[mask].copy()

    if orden_rentable:
        res = res.sort_values('score_rentabilidad', ascending=False)
    else:
        res = res.sort_values('pkg_n', ascending=True)

    st.subheader(f"Se encontraron {len(res)} resultados")

    res_v = res.copy()
    res_v['USD/Kg'] = res_v['pkg_n'].map('${:.2f}'.format)
    res_v['Total'] = res_v['pun_n'].map('${:.2f}'.format)
    
    columnas_finales = [c for c in [col_sku, col_cal, col_esp, col_anc, col_lar, col_ino] if c]
    columnas_finales += ['USD/Kg', 'Total']
    
    st.dataframe(res_v[columnas_finales], use_container_width=True, hide_index=True)
    
    csv = res_v[columnas_finales].to_csv(index=False).encode('latin-1')
    st.download_button("📥 Descargar", csv, "famiq.csv", "text/csv")
else:
    st.error("Archivo no encontrado.")
    
