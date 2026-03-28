import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Buscador de Chapas - Famiq", layout="wide")

@st.cache_data
def cargar_datos():
    import os
    archivos = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not archivos: return None
    
    # Abrir el archivo ignorando errores de codificación
    df = pd.read_csv(archivos[0], encoding="latin-1", sep=None, engine='python', on_bad_lines='skip')
    
    # Limpieza básica de nombres de columnas
    df.columns = [str(c).replace('"', '').strip() for c in df.columns]

    def extraer_solo_numero(txt):
        if pd.isna(txt) or txt == "": return 0.0
        # Buscamos solo los dígitos, comas y puntos
        # Esto ignora "USD", "mm", saltos de línea y comillas
        numeros = re.findall(r'[0-9.,]+', str(txt))
        if not numeros: return 0.0
        
        # Tomamos el último grupo de números (útil si dice "USD 3,44")
        limpio = numeros[-1]
        
        # Formato: si tiene coma y punto, el punto es de miles (1.200,50 -> 1200.50)
        if ',' in limpio and '.' in limpio:
            limpio = limpio.replace('.', '').replace(',', '.')
        else:
            # Si solo tiene coma, es el decimal (0,5 -> 0.5)
            limpio = limpio.replace(',', '.')
            
        try: return float(limpio)
        except: return 0.0

    # Identificar columnas
    c_esp = next((c for c in df.columns if 'espesor' in c.lower()), None)
    c_pkg = next((c for c in df.columns if 'kg' in c.lower()), None)
    c_pun = next((c for c in df.columns if 'unidad' in c.lower()), None)
    c_cal = next((c for c in df.columns if 'calidad' in c.lower()), None)

    # Crear columnas numéricas
    df['esp_n'] = df[c_esp].apply(extraer_solo_numero) if c_esp else 0.0
    df['pkg_n'] = df[c_pkg].apply(extraer_solo_numero) if c_pkg else 0.0
    df['pun_n'] = df[c_pun].apply(extraer_solo_numero) if c_pun else 0.0
    
    return df, c_cal, c_esp

st.title("🛠️ Buscador de Chapas para Papá")

data_pack = cargar_datos()

if data_pack is None:
    st.error("No hay archivo .csv")
else:
    df, c_cal, c_esp = data_pack
    
    st.sidebar.header("Filtros")
    
    # Filtro Calidad (Si no encuentra la columna, usa la primera)
    col_calidad = c_cal if c_cal else df.columns[0]
    lista_calidades = sorted(list(df[col_calidad].astype(str).unique()))
    cal_sel = st.sidebar.multiselect("Calidad:", lista_calidades, default=lista_calidades)

    # Filtro Espesor
    min_e = float(df['esp_n'].min())
    max_e = float(df['esp_n'].max())
    # Si todos son 0, ponemos un rango manual para que no rompa
    if min_e == max_e: max_e = min_e + 10.0
    
    esp_rango = st.sidebar.slider("Espesor (mm):", min_e, max_e, (min_e, max_e))

    # Aplicar filtros
    mask = (df['esp_n'] >= esp_rango[0]) & (df['esp_n'] <= esp_rango[1])
    if cal_sel:
        mask &= df[col_calidad].astype(str).isin(cal_sel)

    res = df[mask].copy()

    st.subheader(f"Se encontraron {len(res)} chapas")
    
    # Formatear para mostrar
    if not res.empty:
        res['USD/Kg'] = res['pkg_n'].map('{:.2f}'.format)
        res['Total'] = res['pun_n'].map('{:.2f}'.format)
        
        # Seleccionar columnas que existen para mostrar
        cols_finales = [c for c in [c_cal, c_esp, 'Ancho', 'Largo', 'Inoxsale'] if c in res.columns]
        cols_finales += ['USD/Kg', 'Total']
        
        st.dataframe(res[cols_finales], use_container_width=True, hide_index=True)
    else:
        st.warning("No hay resultados con esos filtros. Probá ampliando el rango de espesor.")
