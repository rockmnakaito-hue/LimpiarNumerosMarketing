import io
import pandas as pd
import streamlit as st
from pathlib import Path

# --- Funciones de utilidad ---
def normalize_to_us_e164(raw: str, keep_plus: bool=True) -> str:
    """Convierte número en formato +1XXXXXXXXXX o 1XXXXXXXXXX"""
    if pd.isna(raw):
        return ""
    s = str(raw)
    digits = "".join(ch for ch in s if ch.isdigit())

    if len(digits) == 11 and digits.startswith("1"):
        core = digits[1:]
    elif len(digits) == 10:
        core = digits
    else:
        return ""

    return (f"+1{core}") if keep_plus else (f"1{core}")

def build_phonumber_column(df: pd.DataFrame, column: str, keep_plus=True) -> pd.DataFrame:
    """Crea un DataFrame con una sola columna 'phonumber' a partir de la seleccionada"""
    if column not in df.columns:
        raise ValueError(f"La columna '{column}' no existe en el archivo.")
    df_result = pd.DataFrame()
    df_result["phonumber"] = df[column].apply(lambda x: normalize_to_us_e164(x, keep_plus=keep_plus))
    return df_result

# --- Interfaz Streamlit ---
st.set_page_config(page_title="Normalizador de teléfonos Compinche", page_icon="📱")

st.title("📱 Normalizador de Teléfonos")
st.write("Sube el archivo exportado de Compinche (.xlsx o .csv), elige la columna que contiene los teléfonos y generaremos un archivo con la columna **phonumber** estandarizada.")

uploaded = st.file_uploader("Elige un archivo", type=["xlsx","xls","csv"])
keep_plus = st.toggle("Usar formato con '+' (+1XXXXXXXXXX)", value=True)

if uploaded is not None:
    suffix = Path(uploaded.name).suffix.lower()
    try:
        if suffix in [".xlsx", ".xls"]:
            df = pd.read_excel(uploaded)
        else:
            try:
                df = pd.read_csv(uploaded)
            except Exception:
                df = pd.read_csv(uploaded, encoding="latin-1")
    except Exception as e:
        st.error(f"No se pudo leer el archivo: {e}")
        st.stop()

    # Mostrar selección de columna
    column_choice = st.selectbox("Selecciona la columna que contiene los números de teléfono:", df.columns)

    # Generar resultado
    df_out = build_phonumber_column(df, column_choice, keep_plus=keep_plus)

    st.subheader("👀 Vista previa del resultado")
    st.dataframe(df_out.head(20))   # 👈 solo phonumber

    # Exportar CSV
    out_buf = io.BytesIO()
    df_out.to_csv(out_buf, index=False)
    out_buf.seek(0)

    st.download_button(
        label="📥 Descargar archivo CSV",
        data=out_buf,
        file_name="compinche_normalizado.csv",
        mime="text/csv"
    )
