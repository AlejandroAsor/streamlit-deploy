import streamlit as st
import pandas as pd
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder
from sqlalchemy import create_engine, inspect
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from keyword_variants import keyword_variants

st.set_page_config(
    page_title="Panorama del Empleo en Tecnología: 17 Países en Análisis",
    layout="wide",
    initial_sidebar_state="expanded",
)


db_config = st.secrets["database"]
db_names = st.secrets["databases"]

def get_keywords_connection():
    db_endpoint = db_config["endpoint"]
    db_name = db_names["keywords1"]
    db_user = db_config["user"]
    db_password = db_config["password"]
    db_port = db_config["port"]

    connection_string = f'postgresql://{db_user}:{db_password}@{db_endpoint}:{db_port}/{db_name}'
    return create_engine(connection_string)


def load_statistics(categories=None, country=None, sort_column='offer_count_title'):
    engine = get_keywords_connection()

    if country and country != "Todos los países":
        # Si se especifica un país, usar country_statistics
        table_name = "country_statistics"
        where_clause = f"WHERE country = '{country}'"
        if categories:
            categories_str = "', '".join(categories)
            where_clause += f" AND category IN ('{categories_str}')"
    else:
        # Si no se especifica un país, usar general_statistics
        table_name = "general_statistics"
        where_clause = ""
        if categories:
            categories_str = "', '".join(categories)
            where_clause = f"WHERE category IN ('{categories_str}')"

    # Añadir cláusula para excluir filas donde la columna de ordenamiento es nula
    non_null_clause = f" AND {sort_column} IS NOT NULL" if sort_column != "offer_count_title" else ""

    query = f"""
    SELECT * FROM {table_name}
    {where_clause}{non_null_clause}
    ORDER BY {sort_column} DESC
    """
    with engine.connect() as connection:
        df = pd.read_sql(query, connection)
    return df


def get_computrabajo_connection():
    db_endpoint = db_config["endpoint"]
    db_name = db_names["computrabajo"]
    db_user = db_config["user"]
    db_password = db_config["password"]
    db_port = db_config["port"]

    connection_string = f'postgresql://{db_user}:{db_password}@{db_endpoint}:{db_port}/{db_name}'
    return create_engine(connection_string)

def get_elempleo_connection():
    db_endpoint = db_config["endpoint"]
    db_name = db_names["elempleo"]
    db_user = db_config["user"]
    db_password = db_config["password"]
    db_port = db_config["port"]

    connection_string = f'postgresql://{db_user}:{db_password}@{db_endpoint}:{db_port}/{db_name}'
    return create_engine(connection_string)

def load_keywords():
    keywords = []
    for primary, variants in keyword_variants.items():
        for variant in variants:
            keywords.append({"primary": primary, "variant": variant})
    return pd.DataFrame(keywords)

# Función para verificar la existencia de la tabla
def table_exists(engine, table_name):
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

# Función para obtener los job_id asociados a una palabra clave
def fetch_job_ids_by_keyword(keyword):
    engine = get_keywords_connection()
    query = """
    SELECT job_id::text
    FROM job_keywords jk
    JOIN keywords k ON jk.keyword_id = k.id
    WHERE k.keyword = %s
    """
    with engine.connect() as connection:
        df_job_ids = pd.read_sql(query, connection, params=(keyword,))
    return df_job_ids['job_id'].tolist()


def load_job_data():
    engine_computrabajo = get_computrabajo_connection()
    engine_elempleo = get_elempleo_connection()

    query = """
    SELECT date_trunc('day', date_scraped) AS date_day, COUNT(*) AS count
    FROM job_listings
    WHERE date_scraped IS NOT NULL
    GROUP BY date_trunc('day', date_scraped)
    ORDER BY date_trunc('day', date_scraped);
    """

    with engine_computrabajo.connect() as conn:
        df_computrabajo = pd.read_sql(query, conn)

    with engine_elempleo.connect() as conn:
        df_elempleo = pd.read_sql(query, conn)

    # Combinando los resultados
    df_total = pd.concat([df_computrabajo, df_elempleo])

    # Verificar y limpiar datos antes de la conversión
    print("Datos antes de la conversión:")
    print(df_total.head())
    print(df_total['date_day'].unique())

    # Convertir a datetime, manejando errores
    df_total['date_day'] = pd.to_datetime(df_total['date_day'], errors='coerce')
    print("Datos después de la conversión:")
    print(df_total.head())

    # Eliminar filas donde 'date_day' es NaT
    df_total = df_total.dropna(subset=['date_day'])

    # Agrupar por día y sumar conteos
    df_total = df_total.groupby('date_day').sum().reset_index()

    return df_total

# Plot data
def plot_data(df):
    fig = px.line(df, x='date_day', y='count', title='Estado Diario de las Ofertas Laborales Recolectadas',
                  labels={'date_day': 'Fecha', 'count': 'Número de Ofertas Laborales Recopiladas'})
    st.plotly_chart(fig, use_container_width=True)


# Función para obtener detalles de trabajos
def fetch_job_details(job_ids):
    if not job_ids:
        return pd.DataFrame()

    # Convertir lista de job_ids a texto
    job_ids_str = [str(job_id) for job_id in job_ids]

    # Calcular la fecha de hace un mes
    one_month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    # Obtener detalles de trabajos desde computrabajo
    engine_comp = get_computrabajo_connection()
    query_comp = """
    SELECT title AS titulo, url, date_scraped
    FROM job_listings
    WHERE id::text = ANY(%s) AND date_scraped >= %s
    """
    with engine_comp.connect() as connection:
        df_jobs_comp = pd.read_sql(query_comp, connection, params=(job_ids_str, one_month_ago))

    # Obtener detalles de trabajos desde elempleo
    engine_elempleo = get_elempleo_connection()
    query_elempleo = """
    SELECT titulo, url, date_scraped
    FROM job_listings
    WHERE id::text = ANY(%s) AND date_scraped >= %s
    """
    with engine_elempleo.connect() as connection:
        df_jobs_elempleo = pd.read_sql(query_elempleo, connection, params=(job_ids_str, one_month_ago))

    # Combinar los resultados
    df_jobs = pd.concat([df_jobs_comp, df_jobs_elempleo], ignore_index=True)

    # Asegurar que date_scraped es del tipo datetime
    df_jobs['date_scraped'] = pd.to_datetime(df_jobs['date_scraped'])

    # Ordenar por date_scraped
    df_jobs.sort_values(by='date_scraped', ascending=False, inplace=True)

    return df_jobs

# Menú desplegable
st.sidebar.header("🛠️Secciones")
options = ["Estadísticas Generales", "Ofertas", "Recolección de Datos"]
selection = st.sidebar.radio("Select Option", options)

# Título de la página
st.title("🛠️Panorama del Empleo en Tecnología: 17 Países en Análisis")


column_names_in_spanish = {
    'keyword': 'Palabra clave',
    'category': 'Categoría',
    'offer_count_title': 'Ofertas unicas (solo título)',
    'offer_count_content': 'Ofertas unicas (total)',
    'title_frequency': 'Frecuencia en títulos',
    'content_frequency': 'Frecuencia en total',
    'avg_salary_usd': 'Salario prom. (USD)',
    'avg_experience': 'Exp. promedio (años)'
}

if selection == "Estadísticas Generales":
    st.subheader("Estadísticas Generales")

    # Primera fila con dos columnas
    col1, col2 = st.columns(2)

    with col1:
        categories = ['Programming Language', 'Role', 'Database']
        category_options = ["Todas las Categorías"] + categories
        selected_category = st.selectbox("🔧 Categorías", category_options)

    with col2:
        country_list = ['Chile', 'Guatemala', 'Mexico', 'El Salvador', 'Peru', 'Colombia', 'Argentina', 'Ecuador', 'Honduras', 'Uruguay', 'Costa Rica', 'Nicaragua', 'Paraguay', 'Panama', 'Bolivia', 'Venezuela', 'Republica Dominicana']
        selected_country = st.selectbox("🔧 País", ["Todos los países"] + sorted(country_list))

    # Segunda fila con dos columnas
    col3, col4 = st.columns(2)

    with col3:
        visualization_type = st.selectbox("🔧 Tipo de Visualización", ["Tabla", "Gráfico de Barras", "Gráfico de Torta"])

    with col4:
        column_options = list(column_names_in_spanish.values())[2:]  # Traducir nombres de columnas
        selected_column = st.selectbox("🔧 Selecciona Columna", column_options)

    if selected_category == "Todas las Categorías":
        selected_categories = categories
    else:
        selected_categories = [selected_category]

    sort_column = list(column_names_in_spanish.keys())[list(column_names_in_spanish.values()).index(selected_column)] if selected_column != "Todas las Columnas" else "offer_count_title"
    df_stats = load_statistics(selected_categories, selected_country, sort_column)

    # Cambiar nombres de columnas al español
    df_stats.rename(columns=column_names_in_spanish, inplace=True)
    sort_column_spanish = column_names_in_spanish.get(sort_column, sort_column)

    # Definir las columnas a mostrar
    columns_to_show = ["Palabra clave", "Categoría"]
    if selected_column != "Todas las Columnas":
        columns_to_show.append(selected_column)  # Añadir la columna seleccionada

    if visualization_type == "Tabla":
        AgGrid(df_stats[columns_to_show], height=500, width='100%', fit_columns_on_grid_load=True)
    elif visualization_type == "Gráfico de Barras":
        fig = px.bar(df_stats.head(100), x=sort_column_spanish, y='Palabra clave', title='Gráfico de Barras', height=2000)
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig)
    elif visualization_type == "Gráfico de Torta":
        fig = px.pie(df_stats.head(10), names='Palabra clave', values=sort_column_spanish, title='Gráfico de Torta')
        st.plotly_chart(fig)

elif selection == "Ofertas":
    st.subheader("Ofertas")
    st.header("🔧 Seleccionar Palabra Clave")

    # Columnas para controles en línea
    col1, col2, col3 = st.columns(3)

    with col1:
        # Cargar palabras clave y permitir la selección
        df_keywords = load_keywords()
        keyword_options = df_keywords['primary'].unique().tolist()
        selected_keyword = st.selectbox("Selecciona una palabra clave", keyword_options)

    # Obtener las variantes de la palabra clave seleccionada
    selected_variants = keyword_variants[selected_keyword]

    # Obtener los job_ids asociados a las variantes de la palabra clave seleccionada
    job_ids = []
    for variant in selected_variants:
        job_ids.extend(fetch_job_ids_by_keyword(variant))

    # Obtener detalles de trabajos para los job_ids obtenidos
    df_jobs = fetch_job_details(job_ids)

    with col2:
        # Permitir al usuario seleccionar la cantidad de ítems por página
        items_per_page = st.selectbox('Ítems por página', options=[5, 10, 20, 50, 100], index=1)

    with col3:
        # Paginación
        total_items = len(df_jobs)
        total_pages = (total_items // items_per_page) + 1 if total_items % items_per_page != 0 else total_items // items_per_page
        page = st.number_input('Página', min_value=1, max_value=total_pages, value=1)

    start_idx = (page - 1) * items_per_page
    end_idx = start_idx + items_per_page

    # Mostrar detalles de trabajos en formato de lista con título y enlace
    if not df_jobs.empty:
        for idx, job in df_jobs.iloc[start_idx:end_idx].iterrows():
            st.markdown(f"""
                <div style='border: 1px solid #ddd; padding: 10px; margin-bottom: 10px; border-radius: 5px;'>
                    <h3><a href='{job["url"]}' target='_blank'>{selected_keyword}: {job['titulo']}</a></h3>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.write("No se encontraron ofertas para la palabra clave seleccionada.")

elif selection == "Recolección de Datos":
    st.subheader("Recolección de Datos")
    current_size = "658,362"
    st.metric(label="Jobs Database Size", value=f"{current_size}")
    df_job_data = load_job_data()
    plot_data(df_job_data)
