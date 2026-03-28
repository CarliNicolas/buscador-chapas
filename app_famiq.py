import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Buscador de Chapas - Famiq", page_icon="🔍", layout="wide")

@st.cache_data
def cargar_datos():
    # 1. Leer archivo
    df = pd.read_csv("datos.csv", encoding="latin-1", sep=None, engine='python', on_bad_lines='skip')
    
    # 2. Limpiar nombres de columnas (quitar comillas y espacios)
    df.columns = [str(c).replace('"', '').strip() for c in df.columns]

    # 3. Función para extraer números de textos como "USD 3,44" o "0,5 mm"
    def extraer_numero(txt):
        if pd.isna(txt) or txt == "": return 0.0
        # Quitamos todo menos números, comas y puntos
        limpio = "".join(c for c in str(txt) if c.isdigit() or c in ',.')
        if not limpio: return 0.0
        # Manejo de decimales (si hay coma y punto, el punto es de miles)
        if ',' in limpio and '.' in limpio:
            limpio = limpio.replace('.', '').replace(',', '.')
        else:
            limpio = limpio.replace(',', '.')
        try: return float(limpio)
        except: return 0.0

    # 4. Procesar columnas clave
    # Buscamos las columnas aunque tengan nombres ligeramente distintos
    col_esp = next((c for c in df.columns if 'espesor' in c.lower()), None)
    col_pkg = next((c for c in df.columns if 'kg' in c.lower()), None)
    col_pun = next((c for c in df.columns if 'unidad' in c.lower()), None)
    col_cal = next((c for c in df.columns if 'calidad' in c.lower()), None)
    col_oferta = next((c for c in df.columns if 'inox' in c.lower() or 'oferta' in c.lower()), None)

    # Convertir a números reales
    df['Precio_Kg_num'] = df[col_pkg].apply(extraer_numero) if col_pkg else 0.0
    df['Precio_Un_num'] = df[col_pun].apply(extraer_numero) if col_pun else 0.0
    df['Espesor_num'] = df[col_esp].apply(extraer_numero) if col_esp else 0.0
    
    # Descuento
    if col_oferta:
        df['Desc_val'] = df[col_oferta].apply(lambda x: 1 if '%' in str(x) or 'sale' in str(x).lower() else 0)
    else:
        df['Desc_val'] = 0

    return df, col_cal, col_esp, col_oferta

st.title("🛠️ Buscador de Chapas para Papá")

try:
    df, col_cal, col_esp, col_oferta = cargar_datos()

    # Sidebar
    st.sidebar.header("Filtros")
    
    # Filtro Calidad
    c_cal = col_cal if col_cal else df.columns[0]
    lista_cal = sorted([str(x).strip() for x in df[c_cal].unique() if x and str(x).strip() != ""])
    cal_sel = st.sidebar.multiselect("Calidad:", lista_cal, default=lista_cal[:1] if lista_cal else [])

    # Filtro Espesor
    lista_esp = sorted([x for x in df['Espesor_num'].unique() if x > 0])
    if lista_esp:
        esp_sel = st.sidebar.select_slider("Espesor (mm):", options=lista_esp, value=(min(lista_esp), max(lista_esp)))
    else:
        esp_sel = (0.0, 100.0)

    solo_ofertas = st.sidebar.checkbox("💥 Ver solo Liquidaciones")

    # Filtros
    mask = (df['Espesor_num'] >= esp_sel[0]) & (df['Espesor_num'] <= esp_sel[1])
    if cal_sel: mask &= df[c_cal].str.strip().isin(cal_sel)
    if solo_ofertas: mask &= (df['Desc_val'] > 0)

    res = df[mask].sort_values('Precio_Kg_num', ascending=True)

    # Tabla Final
    st.subheader(f"Se encontraron {len(res)} chapas")
    
    # Limpiamos la visualización
    res_v = res.copy()
    res_v['USD / Kg'] = res_v['Precio_Kg_num'].map('${:.2f}'.format)
    res_v['Precio Unidad'] = res_v['Precio_Un_num'].map('${:.2f}'.format)
    
    # Elegimos qué columnas mostrar (sin las columnas _num de servicio)
    cols_finales = [c for c in [c_cal, col_esp, 'Ancho', 'Largo', col_oferta] if c and c in res_v.columns]
    cols_finales += ['USD / Kg', 'Precio Unidad']

    st.dataframe(res_v[cols_finales], use_container_width=True, hide_index=True)

except Exception as e:
    st.error("Hubo un error al organizar la tabla.")
    st.write(e)
