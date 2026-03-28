import streamlit as st
import pandas as pd
import re
import os

st.set_page_config(page_title="Buscador de Chapas - Famiq", layout="wide")

@st.cache_data
def cargar_datos():
    archivos = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not archivos: return None
    
    # Abrir el archivo ignorando errores de codificación
    df = pd.read_csv(archivos[0], encoding="latin-1", sep=None, engine='python', on_bad_lines='skip')
    
    # 1. Limpiar nombres de columnas (quitar comillas y espacios)
    df.columns = [str(c).replace('"', '').strip() for c in df.columns]

    # 2. FUNCIÓN DE LIMPIEZA DEFINITIVA (Saca el USD, el salto de línea y las comas)
    def limpiar_precio_famiq(txt):
        if pd.isna(txt) or txt == "": return 0.0
        # Quitamos "USD", comillas y cualquier letra
        limpio = str(txt).replace('USD', '').replace('"', '').strip()
        # Buscamos solo los números y separadores (. o ,)
        numeros = re.findall(r'[0-9.,]+', limpio)
        if not numeros: return 0.0
        
        val = numeros[-1] # El último grupo de números
        # Si tiene punto y coma (ej: 1.200,50) quitamos el punto y cambiamos coma por punto
        if '.' in val and ',' in val:
            val = val.replace('.', '').replace(',', '.')
        else:
            # Si solo tiene coma (ej: 3,44) la cambiamos por punto
            val = val.replace(',', '.')
            
        try: return float(val)
        except: return 0.0

    # 3. Mapeo de columnas inteligentes
    c_esp = next((c for c in df.columns if 'espesor' in c.lower()), None)
    c_pkg = next((c for c in df.columns if 'kg' in c.lower()), None)
    c_pun = next((c for c in df.columns if 'unidad' in c.lower()), None)
    c_cal = next((c for c in df.columns if 'calidad' in c.lower()), None)
    c_inox = next((c for c in df.columns if 'inox' in c.lower()), None)

    # 4. Convertir columnas a números reales
    df['pkg_n'] = df[c_pkg].apply(limpiar_precio_famiq) if c_pkg else 0.0
    df['pun_n'] = df[c_pun].apply(limpiar_precio_famiq) if c_pun else 0.0
    df['esp_n'] = df[c_esp].apply(limpiar_precio_famiq) if c_esp else 0.0
    
    # Marcar si es liquidación (Inoxsale)
    if c_inox:
        df['es_oferta'] = df[c_inox].apply(lambda x: 1 if '%' in str(x) or 'sale' in str(x).lower() else 0)
    else:
        df['es_oferta'] = 0
    
    return df, c_cal, c_esp, c_inox

st.title("🛠️ Buscador de Chapas para Papá")

pack = cargar_datos()

if pack:
    df, col_calidad, col_espesor, col_inox = pack
    
    # --- BARRA LATERAL ---
    st.sidebar.header("Filtros")
    
    # Calidad (304, 430, etc)
    c_cal = col_calidad if col_calidad else df.columns[0]
    opciones_cal = sorted([str(x) for x in df[c_cal].unique() if x])
    cal_sel = st.sidebar.multiselect("Filtrar por Calidad:", opciones_cal, default=opciones_cal)

    # Espesor (0.5mm, 1mm, etc)
    min_e = float(df['esp_n'].min())
    max_e = float(df['esp_n'].max())
    if min_e == max_e: max_e += 5.0
    esp_sel = st.sidebar.slider("Rango de Espesor (mm):", min_e, max_e, (min_e, max_e))

    solo_ofertas = st.sidebar.checkbox("💥 Ver solo Liquidaciones")

    # --- FILTRADO ---
    mask = (df['esp_n'] >= esp_sel[0]) & (df['esp_n'] <= esp_sel[1])
    if cal_sel: mask &= df[c_cal].astype(str).isin(cal_sel)
    if solo_ofertas: mask &= (df['es_oferta'] > 0)

    res = df[mask].copy()

    # --- RESULTADOS ---
    st.subheader(f"Se encontraron {len(res)} chapas")
    
    # Ordenar por el más barato por kilo
    res = res.sort_values('pkg_n', ascending=True)

    # Formatear la tabla para que se vea linda
    res['Precio x Kg'] = res['pkg_n'].map('${:.2f}'.format)
    res['Precio Total'] = res['pun_n'].map('${:.2f}'.format)
    
    columnas_ver = [c for c in [col_calidad, col_espesor, 'Ancho', 'Largo', col_inox] if c in res.columns]
    columnas_ver += ['Precio x Kg', 'Precio Total']
    
    st.dataframe(res[columnas_ver], use_container_width=True, hide_index=True)
else:
    st.error("No se encontró el archivo de datos.")
