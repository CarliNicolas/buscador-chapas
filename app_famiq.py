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
    # Limpiamos nombres de columnas quitando comillas y espacios
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

    # Buscamos las columnas por lo que contienen (no importa si es SKU o sku)
    c_sku = next((c for c in df.columns if 'sku' in c.lower()), None)
    c_esp = next((c for c in df.columns if 'espesor' in c.lower()), None)
    c_pkg = next((c for c in df.columns if 'kg' in c.lower()), None)
    c_pun = next((c for c in df.columns if 'unidad' in c.lower()), None)
    c_cal = next((c for c in df.columns if 'calidad' in c.lower()), None)
    c_ino = next((c for c in df.columns if 'inox' in c.lower() or 'sale' in c.lower()), None)

    # Procesamos números
    df['pkg_n'] = df[c_pkg].apply(extraer_num) if c_pkg else 0.0
    df['pun_n'] = df[c_pun].apply(extraer_num) if c_pun else 0.0
    df['esp_n'] = df[c_esp].apply(extraer_num) if c_esp else 0.0
    
    # Solo dejamos lo que tenga precio
    df = df[df['pkg_n'] > 0].copy()
    
    return df, c_sku, c_cal, c_esp, c_ino

st.title("🔍 Buscador de Chapas (Precios Reales)")

datos = cargar_datos()

if datos:
    df, col_sku, col_cal, col_esp, col_ino = datos
    
    st.sidebar.header("Filtros")
    
    # Filtro de Calidad
    opciones_cal = sorted([str(x) for x in df[col_cal].unique() if x]) if col_cal else []
    cal_sel = st.sidebar.multiselect("Calidad:", opciones_cal, default=opciones_cal)

    # Filtro de Espesor
    min_e, max_e = float(df['esp_n'].min()), float(df['esp_n'].max())
    esp_sel = st.sidebar.slider("Espesor (mm):", min_e, max_e, (min_e, max_e))

    solo_ofertas = st.sidebar.checkbox("💥 Ver solo Liquidaciones")

    # Aplicar Filtros
    mask = (df['esp_n'] >= esp_sel[0]) & (df['esp_n'] <= esp_sel[1])
    if cal_sel and col_cal: mask &= df[col_cal].astype(str).isin(cal_sel)
    if solo_ofertas and col_ino:
        mask &= (df[col_ino].str.contains('%|sale', case=False, na=False))

    res = df[mask].sort_values('pkg_n', ascending=True)

    st.subheader(f"Se encontraron {len(res)} chapas con precio")
    
    res_v = res.copy()
    res_v['USD/Kg'] = res_v['pkg_n'].map('${:.2f}'.format)
    res_v['Total'] = res_v['pun_n'].map('${:.2f}'.format)
    
    # ARREGLO DEL SKU: Aseguramos que el SKU sea la primera columna
    columnas_finales = []
    if col_sku: columnas_finales.append(col_sku)
    if col_cal: columnas_finales.append(col_cal)
    if col_esp: columnas_finales.append(col_esp)
    
    # Agregamos Ancho y Largo si existen
    for c in ['Ancho', 'Largo']:
        if c in res_v.columns: columnas_finales.append(c)
        
    if col_ino: columnas_finales.append(col_ino)
    columnas_finales += ['USD/Kg', 'Total']
    
    st.dataframe(res_v[columnas_finales], use_container_width=True, hide_index=True)
    
    # Botón de Descarga
    csv = res_v[columnas_finales].to_csv(index=False).encode('latin-1')
    st.download_button("📥 Descargar esta lista", csv, "gangas_famiq.csv", "text/csv")
else:
    st.warning("No se encontró el archivo .csv.")
