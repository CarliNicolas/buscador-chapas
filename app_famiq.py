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
    c_pkg = next((c for c in df.columns if 'kg' in c.lower()), None)
    c_pun = next((c for c in df.columns if 'unidad' in c.lower()), None)
    c_cal = next((c for c in df.columns if 'calidad' in c.lower()), None)
    c_ino = next((c for c in df.columns if 'inox' in c.lower() or 'sale' in c.lower()), None)

    df['pkg_n'] = df[c_pkg].apply(extraer_num) if c_pkg else 0.0
    df['pun_n'] = df[c_pun].apply(extraer_num) if c_pun else 0.0
    df['esp_n'] = df[c_esp].apply(extraer_num) if c_esp else 0.0
    
    df = df[df['pkg_n'] > 0].copy()
    
    return df, c_sku, c_cal, c_esp, c_ino

st.title("🔍 Buscador de Chapas para Papá")

datos = cargar_datos()

if datos:
    df, col_sku, col_cal, col_esp, col_ino = datos
    
    st.sidebar.header("Filtros")
    
    # Filtro de Calidad
    opciones_cal = sorted([str(x) for x in df[col_cal].unique() if x]) if col_cal else []
    cal_sel = st.sidebar.multiselect("Calidad:", opciones_cal, default=opciones_cal)

    # --- CAMBIO A RANGO ESCRITO ---
    st.sidebar.subheader("Rango de Espesor (mm)")
    min_e_file = float(df['esp_n'].min())
    max_e_file = float(df['esp_n'].max())
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        esp_min = st.number_input("Desde:", min_value=0.0, max_value=max_e_file, value=min_e_file, step=0.1)
    with col2:
        esp_max = st.number_input("Hasta:", min_value=0.0, max_value=max_e_file, value=max_e_file, step=0.1)

    solo_ofertas = st.sidebar.checkbox("💥 Ver solo Liquidaciones")

    # Aplicar Filtros
    mask = (df['esp_n'] >= esp_min) & (df['esp_n'] <= esp_max)
    if cal_sel and col_cal: mask &= df[col_cal].astype(str).isin(cal_sel)
    if solo_ofertas and col_ino:
        mask &= (df[col_ino].str.contains('%|sale', case=False, na=False))

    res = df[mask].sort_values('pkg_n', ascending=True)

    st.subheader(f"Se encontraron {len(res)} chapas")
    
    res_v = res.copy()
    res_v['USD/Kg'] = res_v['pkg_n'].map('${:.2f}'.format)
    res_v['Total'] = res_v['pun_n'].map('${:.2f}'.format)
    
    columnas_finales = []
    if col_sku: columnas_finales.append(col_sku)
    if col_cal: columnas_finales.append(col_cal)
    if col_esp: columnas_finales.append(col_esp)
    
    for c in ['Ancho', 'Largo']:
        if c in res_v.columns: columnas_finales.append(c)
        
    if col_ino: columnas_finales.append(col_ino)
    columnas_finales += ['USD/Kg', 'Total']
    
    st.dataframe(res_v[columnas_finales], use_container_width=True, hide_index=True)
    
    csv = res_v[columnas_finales].to_csv(index=False).encode('latin-1')
    st.download_button("📥 Descargar resultados", csv, "gangas_famiq.csv", "text/csv")
else:
    st.error("Archivo no encontrado.")
    
