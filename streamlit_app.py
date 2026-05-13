import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
import time
from math import radians, cos, sin, asin, sqrt

def haversine(lat1, lon1, lat2, lon2):
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None: return 0.0
    lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
    return round(2 * asin(sqrt(a := sin((lat2-lat1)/2)**2 + cos(lat1) * cos(lat2) * sin((lon2-lon1)/2)**2)) * 6371000, 2)

st.title("🛰️ Auditor CCT: Nivel Número Exterior")

file = st.file_uploader("Sube tu archivo", type=["xlsx", "csv"])

if file:
    df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
    df.columns = df.columns.str.strip()
    
    col1, col2 = st.columns(2)
    with col1:
        c_cct = st.selectbox("Columna CCT: (CLAVECCT)", df.columns, index=list(df.columns).index('CLAVECCT') if 'CLAVECCT' in df.columns else 0)
        c_via = st.selectbox("Calle (IC_VIA):", df.columns, index=list(df.columns).index('IC_VIA') if 'IC_VIA' in df.columns else 0)
        c_next = st.selectbox("Número Ext (I_NEXT):", df.columns, index=list(df.columns).index('I_NEXT') if 'I_NEXT' in df.columns else 0)
        c_mun = st.selectbox("Municipio (IC_MUN):", df.columns, index=list(df.columns).index('IC_MUN') if 'IC_MUN' in df.columns else 0)
        c_est = st.selectbox("Municipio (IC_ENT):", df.columns, index=list(df.columns).index('IC_ENT') if 'IC_ENT' in df.columns else 0)
        c_cp = st.selectbox("Código Postal (I_CVCP):", df.columns, index=list(df.columns).index('I_CVCP') if 'I_CVCP' in df.columns else 0)
    with col2:
        c_lat_orig = st.selectbox("Latitud (I_LAT):", df.columns, index=list(df.columns).index('I_LAT') if 'I_LAT' in df.columns else 0)
        c_long_orig = st.selectbox("Longitud (I_LONG):", df.columns, index=list(df.columns).index('I_LONG') if 'I_LONG' in df.columns else 0)

    if st.button("🚀 Iniciar Auditoría Detallada"):
        geolocator = Nominatim(user_agent="auditor_cct_precision")
        df['LAT_MAPA'], df['LON_MAPA'], df['DISTANCIA_M'], df['VEREDICTO'] = 0.0, 0.0, 0.0, "PENDIENTE"

        bar = st.progress(0)
        for i, row in df.iterrows():
            bar.progress((i + 1) / len(df))
            
            # --- EL CAMBIO ESTÁ AQUÍ ---
            # Si el número es 0 o SN, mandamos solo la calle. Si tiene número, lo pegamos.
            num_ext = str(row[c_next]).strip()
            calle_completa = f"{row[c_via]} {num_ext}" if num_ext not in ['0', 'SN', 'nan', 'None'] else str(row[c_via])
            
            query = {"street": calle_completa, 
                     "city": str(row[c_mun]), 
                     "postalcode": str(row[c_cp]).split('.')[0], # Limpiar si viene como float (ej. 55000.0)
                     "state": str(row[c_est]), 
                     "country": "Mexico"}
            
            try:
                time.sleep(1.2)
                loc = geolocator.geocode(query, timeout=10)
                if loc:
                    df.at[i, 'LAT_MAPA'], df.at[i, 'LON_MAPA'] = loc.latitude, loc.longitude
                    d = haversine(row[c_lat_orig], row[c_long_orig], loc.latitude, loc.longitude)
                    df.at[i, 'DISTANCIA_M'] = d
                    df.at[i, 'VEREDICTO'] = "✅ OK" if d < 100 else "⚠️ DESVIADO"
                else:
                    df.at[i, 'VEREDICTO'] = "❌ NO ENCONTRADO"
            except:
                df.at[i, 'VEREDICTO'] = "⚠️ ERROR RED"

        st.dataframe(df[[c_cct,c_via, c_next, 'DISTANCIA_M', 'VEREDICTO']])
