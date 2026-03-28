import streamlit as st
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="Buscador de Chapas - Famiq", page_icon="🔍", layout="wide")

@st.cache_data
def cargar_datos():
    # 1. Buscador automático de archivo CSV (evita errores de nombres como datos.csv.csv)
    archivos = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not archivos:
        return None, None, None, None
    
    # Abrimos el primer CSV que encuentre
    df = pd.read_csv(archivos[0], encoding="latin-1", sep=None, engine='python', on_bad_lines='skip')
    
    # 2. Limpiar nombres de columnas
    df.columns = [str(c).replace('"', '').replace('\n', ' ').strip() for c in df.columns]

    # 3. Función para extraer números limpios
    def extraer_numero(txt):
        if pd.isna(txt) or txt == "": return 0.0
        limpio = "".join(c for c in str(txt) if c.isdigit() or c in ',.')
        if not limpio: return 0.0
        if ',' in limpio and '.' in limpio:
            limpio = limpio.replace('.', '').replace(',', '.')
        else:
            limpio = limpio.replace(',', '.')
        try: return float(limpio)
        except: return 0.0

    # 4. Encontrar columnas por aproximación
    c_esp = next((c for c in df.columns if 'espesor' in c.lower()), None)
    c_pkg = next((c for c in df.columns if 'kg' in c.lower()), None)
    c_pun = next((c for c in df.columns if 'unidad' in c.lower()), None)
    c_cal = next((c for c in df.columns if 'calidad' in c.lower()), None)
    c_ino = next((c for c in df.columns if 'inox' in c.lower() or 'oferta' in c.lower()), None)

    # Convertir a números
    df['pkg_n'] = df[c_pkg].apply(extraer_numero) if c_pkg else 0.0
    df['pun_n'] = df[c_pun].apply(extraer_numero) if c_pun else 0.0
    df['esp_n'] = df[c_esp].apply(extraer_numero) if c_esp else 0.0
    df['desc_n'] = df[c_ino].apply(lambda x: 1 if '%' in str(x) or 'sale' in str(x).lower() else 0) if c_ino else 0

    return df, c_cal, c_esp, c_ino

st.title("🛠️ Buscador de Chapas para Papá")

df, c_cal, c_esp, c_ino = cargar_datos()

if df is None:
    st.error("❌ No se encontró el archivo de datos en GitHub. Asegurate de que haya un archivo .csv subido.")
else:
    try:
        # Sidebar
        st.sidebar.header("Filtros")
        
        # Filtro Calidad
        col_cal = c_cal if c_cal else df.columns[0]
        lista_cal = sorted([str(x).strip() for x in df[col_cal].unique() if x])
        cal_sel = st.sidebar.multiselect("Calidad:", lista_cal, default=lista_cal[:1] if lista_cal else [])

        # Filtro Espesor
        lista_esp = sorted([x for x in df['esp_n'].unique() if x > 0])
        if lista_esp:
            esp_sel = st.sidebar.select_slider("Espesor (mm):", options=lista_esp, value=(min(lista_esp), max(lista_esp)))
        else:
            esp_sel = (0.0, 500.0)

        solo_ofertas = st.sidebar.checkbox("💥 Ver solo Liquidaciones")

        # Aplicar Filtros
        mask = (df['esp_n'] >= esp_sel[0]) & (df['esp_n'] <= esp_sel[1])
        if cal_sel: mask &= df[col_cal].str.strip().isin(cal_sel)
        if solo_ofertas: mask &= (df['desc_n'] > 0)

        res = df[mask].sort_values('pkg_n', ascending=True)

        # Mostrar Tabla
        st.subheader(f"Resultados: {len(res)} chapas encontradas")
        
        res_v = res.copy()
        res_v['USD / Kg'] = res_v['pkg_n'].map('${:.2f}'.format)
        res_v['Precio Total'] = res_v['pun_n'].map('${:.2f}'.format)
        
        cols_finales = [c for c in [c_cal, c_esp, 'Ancho', 'Largo', c_ino] if c and c in res_v.columns]
        cols_finales += ['USD / Kg', 'Precio Total']

        st.dataframe(res_v[cols_finales], use_container_width=True, hide_index=True)

    except Exception as e:
        st.error("Ocurrió un error al organizar la tabla.")
        st.write(e)
