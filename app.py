import io
import pandas as pd
import streamlit as st
from pathlib import Path

STOP_FILE = Path("stop_list.csv")

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

def load_stop_list() -> pd.DataFrame:
    """Carga la lista STOP si existe, usando siempre la primera columna como 'phonumber'"""
    if STOP_FILE.exists():
        try:
            df = pd.read_csv(STOP_FILE)
            if df.shape[1] == 0:  # CSV vacío
                return pd.DataFrame(columns=["phonumber"])
            # Renombrar siempre la primera columna
            first_col = df.columns[0]
            df = df.rename(columns={first_col: "phonumber"})
            df = df[["phonumber"]]
            # Limpiar duplicados y vacíos
            df = df.dropna().drop_duplicates().reset_index(drop=True)
            return df
        except Exception:
            return pd.DataFrame(columns=["phonumber"])
    return pd.DataFrame(columns=["phonumber"])

def save_stop_list(df: pd.DataFrame):
    """Guarda la lista STOP en el archivo local"""
    df.to_csv(STOP_FILE, index=False)

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

    # Exportar CSV normalizado
    out_buf = io.BytesIO()
    df_out.to_csv(out_buf, index=False)
    out_buf.seek(0)

    st.download_button(
        label="📥 Descargar archivo CSV",
        data=out_buf,
        file_name="compinche_normalizado.csv",
        mime="text/csv"
    )

    # --- Quitar números con STOP ---
    st.subheader("🚫 Filtrar con lista STOP")
    stop_list = load_stop_list()

    if st.button("Quitar números con STOP"):
        if not stop_list.empty:
            df_filtered = df_out[~df_out["phonumber"].isin(stop_list["phonumber"])]
            removed_count = len(df_out) - len(df_filtered)

            st.success(f"✅ Se eliminaron {removed_count} números que estaban en la lista STOP.")
            st.dataframe(df_filtered.head(20))

            # Descargar archivo filtrado
            out_buf = io.BytesIO()
            df_filtered.to_csv(out_buf, index=False)
            out_buf.seek(0)

            st.download_button(
                label="📥 Descargar archivo filtrado (sin STOP)",
                data=out_buf,
                file_name="compinche_filtrado.csv",
                mime="text/csv"
            )
        else:
            st.warning("⚠️ La lista STOP está vacía. No se eliminó ningún número.")

# --- Sección de gestión de lista STOP ---
st.sidebar.title("⚙️ Gestión lista STOP")

stop_list = load_stop_list()
st.sidebar.subheader("📋 Lista STOP actual")
st.sidebar.write(f"Total números: {len(stop_list)}")
st.sidebar.dataframe(stop_list.head(20))

uploaded_stop = st.sidebar.file_uploader("Reemplazar lista STOP", type=["csv"], key="stop_uploader")

if uploaded_stop is not None:
    try:
        new_stop = pd.read_csv(uploaded_stop)
        if new_stop.shape[1] == 0:
            st.sidebar.error("❌ El archivo está vacío.")
        else:
            # Siempre tomar la primera columna y llamarla 'phonumber'
            first_col = new_stop.columns[0]
            new_stop = new_stop.rename(columns={first_col: "phonumber"})
            new_stop = new_stop[["phonumber"]]
            # Limpiar duplicados y vacíos
            new_stop = new_stop.dropna().drop_duplicates().reset_index(drop=True)
            
            save_stop_list(new_stop)
            st.sidebar.success(f"✅ Lista STOP reemplazada correctamente. ({len(new_stop)} números)")
            st.sidebar.dataframe(new_stop.head(20))
    except Exception as e:
        st.sidebar.error(f"No se pudo cargar el archivo STOP: {e}")
