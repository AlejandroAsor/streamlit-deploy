# import streamlit as st
# import pandas as pd
# import plotly.express as px
# from st_aggrid import AgGrid, GridOptionsBuilder
# from sqlalchemy import create_engine, inspect
# from datetime import datetime, timedelta
# from sqlalchemy import create_engine
# from keyword_variants import keyword_variants
#
# st.set_page_config(
#     page_title="Panorama del Empleo en Tecnología: 17 Países en Análisis",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )
#
#
# db_config = st.secrets["database"]
# db_names = st.secrets["databases"]
#
# def get_keywords_connection():
#     db_endpoint = db_config["endpoint"]
#     db_name = db_names["keywords1"]
#     db_user = db_config["user"]
#     db_password = db_config["password"]
#     db_port = db_config["port"]
#
#     connection_string = f'postgresql://{db_user}:{db_password}@{db_endpoint}:{db_port}/{db_name}'
#     return create_engine(connection_string)
#
# def load_statistics():
#     engine = get_keywords_connection()
#     query = """
#     SELECT * FROM general_statistics
#     ORDER BY offer_count_title DESC
#     """
#     with engine.connect() as connection:
#         df = pd.read_sql(query, connection)
#     return df
#
# def get_computrabajo_connection():
#     db_endpoint = db_config["endpoint"]
#     db_name = db_names["computrabajo"]
#     db_user = db_config["user"]
#     db_password = db_config["password"]
#     db_port = db_config["port"]
#
#     connection_string = f'postgresql://{db_user}:{db_password}@{db_endpoint}:{db_port}/{db_name}'
#     return create_engine(connection_string)
#
# def get_elempleo_connection():
#     db_endpoint = db_config["endpoint"]
#     db_name = db_names["elempleo"]
#     db_user = db_config["user"]
#     db_password = db_config["password"]
#     db_port = db_config["port"]
#
#     connection_string = f'postgresql://{db_user}:{db_password}@{db_endpoint}:{db_port}/{db_name}'
#     return create_engine(connection_string)
#
# def load_keywords():
#     keywords = []
#     for primary, variants in keyword_variants.items():
#         for variant in variants:
#             keywords.append({"primary": primary, "variant": variant})
#     return pd.DataFrame(keywords)
#
# # Función para verificar la existencia de la tabla
# def table_exists(engine, table_name):
#     inspector = inspect(engine)
#     return table_name in inspector.get_table_names()
#
# # Función para obtener los job_id asociados a una palabra clave
# def fetch_job_ids_by_keyword(keyword):
#     engine = get_keywords_connection()
#     query = """
#     SELECT job_id::text
#     FROM job_keywords jk
#     JOIN keywords k ON jk.keyword_id = k.id
#     WHERE k.keyword = %s
#     """
#     with engine.connect() as connection:
#         df_job_ids = pd.read_sql(query, connection, params=(keyword,))
#     return df_job_ids['job_id'].tolist()
#
# # Función para obtener detalles de trabajos
# def fetch_job_details(job_ids):
#     if not job_ids:
#         return pd.DataFrame()
#
#     # Convertir lista de job_ids a texto
#     job_ids_str = [str(job_id) for job_id in job_ids]
#
#     # Calcular la fecha de hace un mes
#     one_month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
#
#     # Obtener detalles de trabajos desde computrabajo
#     engine_comp = get_computrabajo_connection()
#     query_comp = """
#     SELECT title AS titulo, url, date_scraped
#     FROM job_listings
#     WHERE id::text = ANY(%s) AND date_scraped >= %s
#     """
#     with engine_comp.connect() as connection:
#         df_jobs_comp = pd.read_sql(query_comp, connection, params=(job_ids_str, one_month_ago))
#
#     # Obtener detalles de trabajos desde elempleo
#     engine_elempleo = get_elempleo_connection()
#     query_elempleo = """
#     SELECT titulo, url, date_scraped
#     FROM job_listings
#     WHERE id::text = ANY(%s) AND date_scraped >= %s
#     """
#     with engine_elempleo.connect() as connection:
#         df_jobs_elempleo = pd.read_sql(query_elempleo, connection, params=(job_ids_str, one_month_ago))
#
#     # Combinar los resultados
#     df_jobs = pd.concat([df_jobs_comp, df_jobs_elempleo], ignore_index=True)
#
#     # Asegurar que date_scraped es del tipo datetime
#     df_jobs['date_scraped'] = pd.to_datetime(df_jobs['date_scraped'])
#
#     # Ordenar por date_scraped
#     df_jobs.sort_values(by='date_scraped', ascending=False, inplace=True)
#
#     return df_jobs
#
# # Menú desplegable
# st.sidebar.header("🛠️Secciones")
# options = ["Estadísticas Generales", "Ofertas", "Documentacion"]
# selection = st.sidebar.radio("Select Option", options)
#
# # Título de la página
# st.title("🛠️Panorama del Empleo en Tecnología: 17 Países en Análisis")
#
# if selection == "Estadísticas Generales":
#     st.subheader("Estadísticas Generales")
#     # Cargar estadísticas desde la base de datos
#     df_stats = load_statistics()
#
#     # Seleccionar tipo de visualización
#     st.header("🔧 Tipo de Visualización")
#     visualization_type = st.radio("Elige el tipo de visualización", [
#         "Tabla", "Gráfico de Barras", "Gráfico de Torta"
#     ])
#
#     # Solo mostrar selección de columnas si el tipo de visualización es "Tabla"
#     if visualization_type == "Tabla":
#         # Seleccionar columnas para mostrar
#         all_columns = df_stats.columns.tolist()
#
#         select_all = st.checkbox("Seleccionar todas las columnas", value=True)
#         if select_all:
#             selected_columns = all_columns
#         else:
#             selected_columns = st.multiselect("Selecciona las columnas para mostrar", all_columns, default=all_columns[:7])
#
#         # Filtrar datos según la selección del usuario
#         df_page = df_stats[selected_columns]
#     else:
#         df_page = df_stats
#
#     # Visualizar datos según la selección del usuario
#     if visualization_type == "Tabla":
#         # Crear opciones de la tabla AgGrid
#         gb = GridOptionsBuilder.from_dataframe(df_page)
#         gb.configure_default_column(wrapText=True, autoHeight=True)
#         grid_options = gb.build()
#         AgGrid(df_page, gridOptions=grid_options, height=500, width='100%')
#
#     elif visualization_type == "Gráfico de Barras":
#         df_bar = df_page.head(100)  # Limitar a los primeros 100 resultados
#         fig = px.bar(df_bar, x='offer_count_title', y='keyword', title='Gráfico de Barras', height=2000)
#         fig.update_layout(yaxis={'categoryorder': 'total ascending'})  # Ordenar las barras
#         st.plotly_chart(fig)
#
#     elif visualization_type == "Gráfico de Torta":
#         df_pie = df_page.head(10)  # Limitar a los primeros 10 resultados
#         fig = px.pie(df_pie, names='keyword', values='offer_count_title', title='Gráfico de Torta')
#         st.plotly_chart(fig)
#
# elif selection == "Ofertas":
#     st.subheader("Ofertas")
#     st.header("🔧 Seleccionar Palabra Clave")
#
#     # Columnas para controles en línea
#     col1, col2, col3 = st.columns(3)
#
#     with col1:
#         # Cargar palabras clave y permitir la selección
#         df_keywords = load_keywords()
#         keyword_options = df_keywords['primary'].unique().tolist()
#         selected_keyword = st.selectbox("Selecciona una palabra clave", keyword_options)
#
#     # Obtener las variantes de la palabra clave seleccionada
#     selected_variants = keyword_variants[selected_keyword]
#
#     # Obtener los job_ids asociados a las variantes de la palabra clave seleccionada
#     job_ids = []
#     for variant in selected_variants:
#         job_ids.extend(fetch_job_ids_by_keyword(variant))
#
#     # Obtener detalles de trabajos para los job_ids obtenidos
#     df_jobs = fetch_job_details(job_ids)
#
#     with col2:
#         # Permitir al usuario seleccionar la cantidad de ítems por página
#         items_per_page = st.selectbox('Ítems por página', options=[5, 10, 20, 50, 100], index=1)
#
#     with col3:
#         # Paginación
#         total_items = len(df_jobs)
#         total_pages = (total_items // items_per_page) + 1 if total_items % items_per_page != 0 else total_items // items_per_page
#         page = st.number_input('Página', min_value=1, max_value=total_pages, value=1)
#
#     start_idx = (page - 1) * items_per_page
#     end_idx = start_idx + items_per_page
#
#     # Mostrar detalles de trabajos en formato de lista con título y enlace
#     if not df_jobs.empty:
#         for idx, job in df_jobs.iloc[start_idx:end_idx].iterrows():
#             st.markdown(f"""
#                 <div style='border: 1px solid #ddd; padding: 10px; margin-bottom: 10px; border-radius: 5px;'>
#                     <h3><a href='{job["url"]}' target='_blank'>{selected_keyword}: {job['titulo']}</a></h3>
#                 </div>
#                 """, unsafe_allow_html=True)
#     else:
#         st.write("No se encontraron ofertas para la palabra clave seleccionada.")
#
# elif selection == "Recoleccion de Data":
#     st.subheader("Documentacion")
#
#




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


def load_statistics(category=None):
    engine = get_keywords_connection()
    # Modificar la consulta para incluir un filtro por categoría si se proporciona
    if category:
        query = f"""
        SELECT * FROM general_statistics
        WHERE category = '{category}'
        ORDER BY offer_count_title DESC
        """
    else:
        query = """
        SELECT * FROM general_statistics
        ORDER BY offer_count_title DESC
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
options = ["Estadísticas Generales", "Ofertas", "Documentacion"]
selection = st.sidebar.radio("Select Option", options)

# Título de la página
st.title("🛠️Panorama del Empleo en Tecnología: 17 Países en Análisis")

if selection == "Estadísticas Generales":
    st.subheader("Estadísticas Generales")

    # Opción para seleccionar una categoría
    categories = ['Categoria 1', 'Categoria 2', 'Categoria 3']  # Asumiendo que tienes categorías definidas
    selected_category = st.selectbox("Elige una categoría", categories, index=0)

    # Cargar estadísticas desde la base de datos filtrando por categoría
    df_stats = load_statistics(selected_category)

    # Seleccionar tipo de visualización
    st.header("🔧 Tipo de Visualización")
    visualization_type = st.radio("Elige el tipo de visualización", [
        "Tabla", "Gráfico de Barras", "Gráfico de Torta"
    ])

    # Solo mostrar selección de columnas si el tipo de visualización es "Tabla"
    if visualization_type == "Tabla":
        # Seleccionar columnas para mostrar
        all_columns = df_stats.columns.tolist()
        select_all = st.checkbox("Seleccionar todas las columnas", value=True)
        if select_all:
            selected_columns = all_columns
        else:
            selected_columns = st.multiselect("Selecciona las columnas para mostrar", all_columns,
                                              default=all_columns[:7])

        # Filtrar datos según la selección del usuario
        df_page = df_stats[selected_columns]
    else:
        df_page = df_stats

    # Visualizar datos según la selección del usuario
    if visualization_type == "Tabla":
        # Crear opciones de la tabla AgGrid
        gb = GridOptionsBuilder.from_dataframe(df_page)
        gb.configure_default_column(wrapText=True, autoHeight=True)
        grid_options = gb.build()
        AgGrid(df_page, gridOptions=grid_options, height=500, width='100%')

    elif visualization_type == "Gráfico de Barras":
        df_bar = df_page.head(100)  # Limitar a los primeros 100 resultados
        fig = px.bar(df_bar, x='offer_count_title', y='keyword', title='Gráfico de Barras', height=2000)
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})  # Ordenar las barras
        st.plotly_chart(fig)

    elif visualization_type == "Gráfico de Torta":
        df_pie = df_page.head(10)  # Limitar a los primeros 10 resultados
        fig = px.pie(df_pie, names='keyword', values='offer_count_title', title='Gráfico de Torta')
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

elif selection == "Recoleccion de Data":
    st.subheader("Documentacion")


