"""
Dashboard de prueba - Estadísticas Mundial (datos sintéticos)
Ejecutar con: streamlit run main_app.py
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --------------------------------------------------------------------------
# CONFIGURACIÓN GENERAL
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Mundial (datos sintéticos)",
    page_icon="⚽",
    layout="wide",
)

# --------------------------------------------------------------------------
# ACCESO CON CÓDIGO
# --------------------------------------------------------------------------
CODIGO_ACCESO = "4650"

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.title("⚽ Dashboard Mundial - Acceso restringido")
    with st.form("form_acceso"):
        codigo_ingresado = st.text_input("Código de acceso", type="password")
        enviar = st.form_submit_button("Ingresar")
    if enviar:
        if codigo_ingresado == CODIGO_ACCESO:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.error("Código incorrecto. Intenta de nuevo.")
    st.stop()

st.title("⚽ Dashboard de prueba - Mundial (datos 100% sintéticos)")
st.caption(
    "Todos los datos de este tablero se generan aleatoriamente al vuelo con fines "
    "de demostración técnica. No representan estadísticas reales de ningún equipo, "
    "jugador ni organización."
)

# --------------------------------------------------------------------------
# GENERACIÓN DE DATOS SINTÉTICOS (200 registros, 8 columnas, tipos mixtos)
# --------------------------------------------------------------------------
@st.cache_data
def generar_datos(semilla: int, sesgo_argentina: float = 20.0, n: int = 200) -> pd.DataFrame:
    rng = np.random.default_rng(semilla)

    equipos = [
        "Argentina", "Brasil", "Francia", "Alemania", "España",
        "Inglaterra", "Portugal", "Países Bajos", "Uruguay", "Colombia",
        "Croacia", "Marruecos", "Japón", "Estados Unidos", "México",
    ]
    confederaciones = {
        "Argentina": "CONMEBOL", "Brasil": "CONMEBOL", "Uruguay": "CONMEBOL", "Colombia": "CONMEBOL",
        "Francia": "UEFA", "Alemania": "UEFA", "España": "UEFA", "Inglaterra": "UEFA",
        "Portugal": "UEFA", "Países Bajos": "UEFA", "Croacia": "UEFA",
        "Marruecos": "CAF", "Japón": "AFC", "Estados Unidos": "CONCACAF", "México": "CONCACAF",
    }
    fases = ["Grupos", "Octavos", "Cuartos", "Semifinal", "Final"]

    equipo_col = rng.choice(equipos, size=n)

    df = pd.DataFrame({
        "equipo": equipo_col,                                                   # categórica (texto)
        "confederacion": [confederaciones[e] for e in equipo_col],              # categórica (texto)
        "fase": rng.choice(fases, size=n, p=[0.45, 0.25, 0.15, 0.10, 0.05]),      # categórica ordinal
        "goles_favor": rng.poisson(1.6, size=n),                                # entero (discreta)
        "goles_contra": rng.poisson(1.1, size=n),                               # entero (discreta)
        "posesion_pct": np.clip(rng.normal(50, 10, size=n), 20, 85).round(1),    # float continua
        "fecha_partido": pd.to_datetime("2026-06-11") + pd.to_timedelta(
            rng.integers(0, 30, size=n), unit="D"
        ),                                                                       # fecha
        "gano_partido": rng.choice([True, False], size=n, p=[0.5, 0.5]),         # booleana
    })

    # ---- Variable ilustrativa: "índice de decisiones arbitrales favorables" ----
    # Se genera de forma ALEATORIA para todos los equipos. Para fines puramente
    # demostrativos (mostrar cómo se vería un sesgo en un gráfico), se le añade
    # un pequeño desplazamiento artificial a Argentina. Esto es un dato FICTICIO
    # de prueba, no una afirmación real sobre la FIFA ni sobre ningún equipo.
    base_idx = rng.normal(50, 12, size=n)
    ajuste_demo = np.where(df["equipo"] == "Argentina", sesgo_argentina, 0)  # sesgo artificial de demo
    df["indice_arbitral_sintetico"] = np.clip(base_idx + ajuste_demo, 0, 100).round(1)

    return df


with st.sidebar:
    st.markdown("### 🎓 EAFIT 2026 — Ciencia de Datos")
    st.caption("Julio de 2026")
    st.markdown("---")
    st.header("⚙️ Controles de simulación")
    semilla = st.number_input("Semilla aleatoria", min_value=0, max_value=9999, value=42)
    sesgo_argentina = 40.0  # sesgo artificial de demo fijado al máximo
    if st.button("🔄 Regenerar datos sintéticos"):
        st.cache_data.clear()
    st.markdown("---")

df = generar_datos(semilla, sesgo_argentina)

# --------------------------------------------------------------------------
# FILTRO GLOBAL POR SELECCIÓN (para análisis estratégico por equipo)
# --------------------------------------------------------------------------
st.subheader("🎯 Panel de decisión estratégica")
equipos_disponibles = sorted(df["equipo"].unique())
equipos_seleccionados = st.multiselect(
    "Filtrar por selección(es) para el análisis",
    options=equipos_disponibles,
    default=equipos_disponibles,
)
fases_disponibles = sorted(df["fase"].unique())
fases_seleccionadas = st.multiselect(
    "Filtrar por fase del torneo",
    options=fases_disponibles,
    default=fases_disponibles,
)

df_filtrado = df[df["equipo"].isin(equipos_seleccionados) & df["fase"].isin(fases_seleccionadas)]

if df_filtrado.empty:
    st.warning("No hay datos para la selección actual. Ajusta los filtros.")
    st.stop()

st.caption(f"Registros tras filtro: {df_filtrado.shape[0]} de {df.shape[0]}")

# ---- Tarjetas de decisión estratégica por selección ----
resumen_equipo = (
    df_filtrado.groupby("equipo")
    .agg(
        partidos=("equipo", "count"),
        goles_favor_prom=("goles_favor", "mean"),
        goles_contra_prom=("goles_contra", "mean"),
        posesion_prom=("posesion_pct", "mean"),
        pct_victorias=("gano_partido", "mean"),
    )
    .assign(
        diferencial_goles=lambda d: d["goles_favor_prom"] - d["goles_contra_prom"],
        pct_victorias=lambda d: (d["pct_victorias"] * 100).round(1),
    )
    .round(2)
    .sort_values("diferencial_goles", ascending=False)
)

st.markdown("**Ranking estratégico (ordenado por diferencial de goles):**")
st.dataframe(
    resumen_equipo,
    width="stretch",
    column_config={
        "diferencial_goles": st.column_config.ProgressColumn(
            "Diferencial de goles",
            min_value=float(resumen_equipo["diferencial_goles"].min()),
            max_value=float(resumen_equipo["diferencial_goles"].max()),
            format="%.2f",
        ),
        "pct_victorias": st.column_config.ProgressColumn(
            "% Victorias", min_value=0, max_value=100, format="%.1f%%",
        ),
    },
)
st.caption(
    "Lectura estratégica: equipos con diferencial de goles alto y buena posesión "
    "son candidatos a mantener el esquema táctico actual; los de diferencial negativo "
    "y baja posesión son candidatos a revisión táctica o de plantilla."
)

st.markdown("---")

with st.expander("📄 Ver muestra de datos crudos filtrados (8 columnas)"):
    st.dataframe(df_filtrado, width="stretch", height=300)
    st.caption(f"Filas: {df_filtrado.shape[0]} | Columnas: {df_filtrado.shape[1]} | Tipos: {dict(df_filtrado.dtypes.astype(str))}")

st.markdown("---")

# --------------------------------------------------------------------------
# ESQUEMA DE MÉTRICAS
# --------------------------------------------------------------------------
tab_cuanti, tab_cuali, tab_graf, tab_tiempo, tab_umbral = st.tabs(
    ["📊 Estadística cuantitativa", "🗂️ Estadística cualitativa", "📈 Análisis gráfico",
     "⏱️ Serie de tiempo", "🎯 Umbrales interactivos"]
)

num_cols = df_filtrado.select_dtypes(include=[np.number]).columns.tolist()
try:
    cat_cols = df_filtrado.select_dtypes(include=["object", "str", "bool"]).columns.tolist()
except TypeError:
    cat_cols = df_filtrado.select_dtypes(include=["object", "bool"]).columns.tolist()

# ---- TAB 1: CUANTITATIVA ----
with tab_cuanti:
    st.subheader("Resumen estadístico de variables numéricas")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Goles a favor (media)", f"{df_filtrado['goles_favor'].mean():.2f}")
    c2.metric("Goles en contra (media)", f"{df_filtrado['goles_contra'].mean():.2f}")
    c3.metric("Posesión promedio %", f"{df_filtrado['posesion_pct'].mean():.1f}")
    c4.metric("Desv. estándar posesión", f"{df_filtrado['posesion_pct'].std():.1f}")

    st.dataframe(df_filtrado[num_cols].describe().T, width="stretch")

    st.subheader("Matriz de correlación")
    corr = df_filtrado[num_cols].corr(numeric_only=True)
    fig_corr = px.imshow(
        corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
        title="Correlación entre variables numéricas",
    )
    st.plotly_chart(fig_corr, width="stretch")

# ---- TAB 2: CUALITATIVA ----
with tab_cuali:
    st.subheader("Distribución de variables categóricas")
    col_cat = st.selectbox("Selecciona una variable categórica", cat_cols, index=0)
    conteo = df_filtrado[col_cat].value_counts().reset_index()
    conteo.columns = [col_cat, "frecuencia"]
    conteo["porcentaje"] = (conteo["frecuencia"] / conteo["frecuencia"].sum() * 100).round(1)
    st.dataframe(conteo, width="stretch")

    fig_pie = px.pie(conteo, names=col_cat, values="frecuencia", title=f"Distribución de {col_cat}", hole=0.35)
    st.plotly_chart(fig_pie, width="stretch")

    st.markdown(f"**Moda de `{col_cat}`:** {df_filtrado[col_cat].mode().iloc[0]}")

# ---- TAB 3: ANÁLISIS GRÁFICO DINÁMICO ----
with tab_graf:
    st.subheader("Explorador dinámico de variables")
    colA, colB, colC = st.columns(3)
    with colA:
        var_x = st.selectbox("Variable eje X", df_filtrado.columns, index=df_filtrado.columns.get_loc("equipo"))
    with colB:
        var_y = st.selectbox("Variable eje Y", num_cols, index=num_cols.index("goles_favor"))
    with colC:
        tipo_grafico = st.selectbox(
            "Tipo de gráfico", ["Barras", "Dispersión", "Caja (Box)", "Histograma"]
        )

    color_por = st.selectbox("Colorear por", ["(ninguno)"] + cat_cols, index=0)
    color_arg = None if color_por == "(ninguno)" else color_por

    if tipo_grafico == "Barras":
        agg = df_filtrado.groupby(var_x, as_index=False)[var_y].mean()
        fig = px.bar(agg, x=var_x, y=var_y, title=f"{var_y} promedio por {var_x}", color=var_x)
    elif tipo_grafico == "Dispersión":
        fig = px.scatter(df_filtrado, x=var_x, y=var_y, color=color_arg, title=f"{var_y} vs {var_x}")
    elif tipo_grafico == "Caja (Box)":
        fig = px.box(df_filtrado, x=var_x, y=var_y, color=color_arg, title=f"Distribución de {var_y} por {var_x}")
    else:  # Histograma
        fig = px.histogram(df_filtrado, x=var_y, color=color_arg, nbins=30, title=f"Histograma de {var_y}")

    st.plotly_chart(fig, width="stretch")

# ---- TAB SERIE DE TIEMPO ----
with tab_tiempo:
    st.subheader("Evolución en el tiempo")
    var_serie = st.selectbox("Variable a graficar en el tiempo", num_cols, index=num_cols.index("goles_favor"), key="var_serie")
    agrupar_serie_por = st.selectbox(
        "Desagregar serie por", ["(promedio general)"] + cat_cols, index=0, key="agrupar_serie"
    )

    if agrupar_serie_por == "(promedio general)":
        serie = df_filtrado.groupby("fecha_partido", as_index=False)[var_serie].mean().sort_values("fecha_partido")
        fig_serie = px.line(
            serie, x="fecha_partido", y=var_serie, markers=True,
            title=f"Evolución diaria de {var_serie} (promedio general)",
        )
    else:
        serie = (
            df_filtrado.groupby(["fecha_partido", agrupar_serie_por], as_index=False)[var_serie]
            .mean()
            .sort_values("fecha_partido")
        )
        fig_serie = px.line(
            serie, x="fecha_partido", y=var_serie, color=agrupar_serie_por, markers=True,
            title=f"Evolución diaria de {var_serie} por {agrupar_serie_por}",
        )

    # Media móvil de 3 partidos sobre el promedio general, como apoyo a la lectura de tendencia
    serie_general = df_filtrado.groupby("fecha_partido", as_index=False)[var_serie].mean().sort_values("fecha_partido")
    serie_general["media_movil_3"] = serie_general[var_serie].rolling(3, min_periods=1).mean()
    fig_serie.add_trace(
        go.Scatter(
            x=serie_general["fecha_partido"], y=serie_general["media_movil_3"],
            mode="lines", name="Media móvil (3 fechas)", line=dict(dash="dot", color="black"),
        )
    )
    st.plotly_chart(fig_serie, width="stretch")
    st.caption("La línea punteada negra es una media móvil de 3 fechas sobre el promedio general, útil para leer la tendencia.")

# ---- TAB 4: UMBRALES INTERACTIVOS ----
with tab_umbral:
    st.subheader("Gráfico de barras con línea de umbral")
    var_umbral = st.selectbox("Variable numérica para evaluar", num_cols, index=num_cols.index("indice_arbitral_sintetico"))
    agrupar_por = st.selectbox("Agrupar por", cat_cols, index=cat_cols.index("equipo"))
    umbral = st.slider(
        "Valor de umbral",
        float(df_filtrado[var_umbral].min()), float(df_filtrado[var_umbral].max()),
        float(df_filtrado[var_umbral].mean()),
    )

    agg = df_filtrado.groupby(agrupar_por, as_index=False)[var_umbral].mean().sort_values(var_umbral, ascending=False)
    agg["supera_umbral"] = agg[var_umbral] > umbral

    fig_umbral = px.bar(
        agg, x=agrupar_por, y=var_umbral, color="supera_umbral",
        color_discrete_map={True: "crimson", False: "steelblue"},
        title=f"{var_umbral} promedio por {agrupar_por} (umbral = {umbral:.1f})",
    )
    fig_umbral.add_hline(y=umbral, line_dash="dash", line_color="black", annotation_text="Umbral")
    st.plotly_chart(fig_umbral, width="stretch")

    n_supera = int(agg["supera_umbral"].sum())
    st.metric(f"Categorías de '{agrupar_por}' que superan el umbral", n_supera)

    if var_umbral == "indice_arbitral_sintetico":
        st.caption(
            "Recordatorio: este índice es completamente sintético y se generó con el "
            "desplazamiento artificial fijado al máximo (+40) para fines de demostración "
            "visual. No refleja datos reales de arbitraje ni decisiones de la FIFA."
        )

st.markdown("---")
st.caption("Dashboard de prueba generado con Streamlit + Plotly. Datos 100% sintéticos y regenerables desde la barra lateral.")
