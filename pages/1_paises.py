#====================================================================================================================================================================                             
#                                                                              BIBLIOTECAS
#====================================================================================================================================================================
import numpy as np
import pandas as pd
import streamlit as st
import folium
import plotly.express as px
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster
from PIL import Image

#===================================================================================================================================================================                             
#                                                                                 TÍTULO
#===================================================================================================================================================================

st.set_page_config(page_title="Visão Países", page_icon="🌍", layout="wide")

# ==================================================================================================================================================================
#                                                                       LIMPEZA E FEATURE ENGINEERING
# ==================================================================================================================================================================
@st.cache_data
def load_data():
    ''' Função para realizar a limpeza, ordenação e criação ou modificação de colunas no dataframe:
        1 - cria uma cópia do dataframe
        2 - Cria uma variável para alocar as colunas do tipo texto
        3 - Percorre a variável (lista) e, para cada item, aplicar a padronização de texto e substituição dos valores de texto NaN por none
        4 - retorna o data frame limpo
    
        Parâmetro: Data frame a ser limpo
    
        Retorno: Data frame com colunas do tipo objetos limpas e padronizadas para letra minúscula
    '''

# =============================================
#            CARREGAMENTO
# =============================================
    df = pd.read_csv("dataset/zomato.csv")
    
# =============================================
#         LIMPEZA E NORMALIZAÇÃO
# =============================================

    # Criar cópia do dataframe e retirar colunas não usadas
    df1 = df.copy()
    # Verifica se as colunas existem antes de remover para evitar erros
    cols_to_drop = ["Locality Verbose", "Switch to order menu"]
    df1 = df1.drop([c for c in cols_to_drop if c in df1.columns], axis=1)
    
    df1.drop_duplicates(inplace=True)
    
    # Organizar as colunas 
    df1.columns = df1.columns.str.lower().str.strip().str.replace(' ', '_')
    
    # Preencher Valores nulos de variáveis importantes
    df1["cuisines"] = df1["cuisines"].fillna("Not Informed")
    
    # Deletar valores nulos não utilizáveis
    valores_nulos = ['NaN', 'nan', 'None', 'none', 'NA', 'n/a', 'N/A', '', ' ']
    df1.replace(valores_nulos, np.nan, inplace=True)
    df1 = df1.loc[df1["average_cost_for_two"] != 0, :]
    
    # Feature Engineering
    
    # Criar a coluna: "Country name" , substituindo o código postal pelo nome do país
    countries = {
        1: "India",
        14: "Australia",
        30: "Brazil",
        37: "Canada",
        94: "Indonesia",
        148: "New Zealand",
        162: "Philippines",
        166: "Qatar",
        184: "Singapore",
        189: "South Africa",
        191: "Sri Lanka",
        208: "Turkey",
        214: "United Arab Emirates",
        215: "United Kingdom",
        216: "United States of America"
    }
    
    df1["country_name"] = df1["country_code"].map(countries).copy()
    
    # Classificar as cores baseado no "rating_color"
    colors = {
        "3F7E00": "darkgreen",
        "5BA829": "green",
        "9ACD32": "lightgreen",
        "CDD614": "orange",
        "FFBA00": "red",
        "CBCBC8": "darkred",
        "FF7800": "darkred",
    }
    
    df1["color"] = df1["rating_color"].map(colors).copy()
    
    # Criar uma coluna de classificação para cada range de preço
    classificacao = {
        1: "cheap",
        2: "normal",
        3: "gourmet",
        4: "caro"
    }
    
    df1["price_type"] = df1["price_range"].map(classificacao).copy()
    
    # Coluna de recomendação baseado na quantidade de votos
    quantile_25 = df1["votes"].quantile(0.25)
    quantile_75 = df1["votes"].quantile(0.75)
    mediana = df1["votes"].median()
    
    def recomendacao(linha):
        vote = linha["votes"]
        rating = linha["aggregate_rating"]
    
        if rating > 4 and vote > quantile_75:
            return "muito recomendado"
        elif (rating >= 4) or (rating >= 3 and vote >= mediana):
            return "recomendado"
        elif rating < 3:
            return "pouco recomendado"
        else:
            return "Neutro"
            
    df1["recomendation"] = df1.apply(recomendacao, axis=1).copy()
    
    # Criação de coluna de conversão de moedas para R$
    conversoes = {
        'Botswana Pula(P)': 0.41,
        'Brazilian Real(R$)': 1.0,
        'Dollar($)': 5.44,
        'Emirati Diram(AED)': 1.48,
        'Indian Rupees(Rs.)': 0.065,
        'Indonesian Rupiah(IDR)': 0.00034,
        'NewZealand($)': 3.14,
        'Pounds(£)': 7.25,
        'Qatari Rial(QR)': 1.49,
        'Rand(R)': 0.32,
        'Sri Lankan Rupee(LKR)': 0.018,
        'Turkish Lira(TL)': 0.13
    }
    
    def conversao(linha):
        moedas = linha["currency"]
        valor = linha["average_cost_for_two"]
        
        if moedas in conversoes:
            return valor * conversoes[moedas]
        else:
            return None # Retorna None se não achar a moeda

    df1["average_cost_for_two_real"] = df1.apply(conversao, axis=1).copy()

    # Remoção de Outlier
    if "Australia" in df1["country_name"].values:
        outlier = df1.loc[df1["country_name"] == "Australia", "average_cost_for_two_real"].idxmax()
        df1 = df1.drop(outlier)
        
    #Criação de um Dataframe auxiliar para aplicação do filtro de culinárias
    df_culinaria = df1.copy()
    df_culinaria["cuisines"] = df_culinaria["cuisines"].astype(str).apply(lambda x: x.split(","))
    df_culinaria = df_culinaria.explode("cuisines")
    df_culinaria["cuisines"] = df_culinaria["cuisines"].str.strip()

    return df1,df_culinaria

        #Criação de um mapa dos restaurantes
def create_map(df):
    if df.empty: return folium.Map(location=[0,0], zoom_start=2)
    
    mapa = folium.Map(location=[df["latitude"].mean(), df["longitude"].mean()], zoom_start=2)
    marker_cluster = MarkerCluster().add_to(mapa)

    for index, linha in df.iterrows():
        html = f"""
        <div style="width: 250px;">
            <h3 style="text-align: center;"><b>{linha['restaurant_name']}</b></h3>
            <div style="font-size: 12px; margin-top: 10px;">
                <b>Cozinha:</b> {linha['cuisines']}<br>
                <b>Preço:</b> R$ {linha['average_cost_for_two_real']:.2f}<br>
                <b>Nota:</b> {linha['aggregate_rating']}/5.0<br>
                <b>Recomendação:</b> {linha['recomendation']}
            </div>
        </div>"""
        
        folium.Marker(
            location=[linha["latitude"], linha["longitude"]],
            popup=folium.Popup(html, max_width=300),
            icon=folium.Icon(color=linha["color"], icon="home", prefix="fa")
        ).add_to(marker_cluster)

    return mapa

df_limpo, df_culinaria = load_data()

# ==================================================================================================================================================================#
#                                                                    GRÁFICOS
# ==================================================================================================================================================================#

#Grafico 1 - Cidades registradas por país

def cidades_por_pais(df1):
    
    cidades_por_pais = df1.groupby("country_name")["city"].nunique().sort_values(ascending =False).reset_index()
    vencedor = cidades_por_pais.iloc[0]["country_name"]
    
    cidades_por_pais["destaque"] = cidades_por_pais["country_name"].apply(lambda x: "vencedor" if x == vencedor else "outros")
    
    total_cidades = cidades_por_pais["city"].sum()
    cidades_por_pais["percentual"] = (cidades_por_pais["city"] / total_cidades * 100)

    fig = px.bar(
    cidades_por_pais.head(5),
    title = "",
    x = "country_name",
    y = "city",
    color = "destaque",
    color_discrete_map = {"vencedor" : "red", "outros" : "lightgray"}, 
    text = "city",
    custom_data = ["percentual"]
)

    fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title="city",separators=",." )
    fig.update_traces(texttemplate="%{y:,.0f} (%{customdata[0]:.1f}%)",textposition="outside",cliponaxis=False)

    return fig

#Grafico 2 - mais culinarias registradas poor país

def restaurantes_por_pais(df1):
    restaurantes_por_pais = df1.groupby("country_name")["restaurant_id"].count().sort_values(ascending = False).reset_index()
    pais_restaurante_vencedor = restaurantes_por_pais.iloc[0]["country_name"]
    restaurantes_por_pais["destaque"] = restaurantes_por_pais["country_name"].apply(lambda x: "vencedor" if x == pais_restaurante_vencedor else "outros")
    
    total_restaurante_por_pais = restaurantes_por_pais["restaurant_id"].sum()
    restaurantes_por_pais["percentual"] = (restaurantes_por_pais["restaurant_id"] / total_restaurante_por_pais * 100)
    
    
    fig = px.bar(
        restaurantes_por_pais.head(5),
        title = "",
        x = "country_name",
        y = "restaurant_id",
        color = "destaque",
        color_discrete_map = {"vencedor" : "red", "outros" : "lightgray"}, 
        text = "restaurant_id",
        custom_data = ["percentual"]
    )
    
    
    fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title="Restaurantes",separators=",." )

    return fig

# Grafico 3 - Culinarias únicas por pais 

def culinarias_por_pais(df1):
    culinaria_por_pais = df1.groupby("country_name")["cuisines"].nunique().sort_values(ascending = False).reset_index()
    culinaria_vencedor = culinaria_por_pais.iloc[0]["country_name"]
    culinaria_por_pais["destaque"] = culinaria_por_pais["country_name"].apply( lambda x : "vencedor" if x == culinaria_vencedor else "outros")
    
    
    total_culinarias = culinaria_por_pais["cuisines"].sum()
    culinaria_por_pais["percentual"] = (culinaria_por_pais["cuisines"]/total_culinarias * 100)
    
    fig = px.bar(
        culinaria_por_pais.head(5),
        title = "",
        x = "country_name",
        y = "cuisines",
        color = "destaque",
        color_discrete_map = {"vencedor" : "red", "outros" : "lightgray"},
        text = "cuisines",
        custom_data = ["percentual"]
    )
    
    fig.update_layout(
        separators=",.",
        showlegend=False,
        xaxis_title=None,
        yaxis_title="Quantidade de avaliações"
    )
    
    fig.update_traces(
        texttemplate="%{y:,.0f} (%{customdata[0]:.1f}%)",
        textposition="outside",
        cliponaxis=False
    )

    return fig

# Grafico 4 - Quantidade de restaurantes que fazem entrega por pais

def paises_por_entregas(df1):

    paises_por_entregas = df1.groupby("country_name")["is_delivering_now"].sum().sort_values(ascending = False).reset_index()
    vencedor_entregas = paises_por_entregas.iloc[0]["country_name"]
    paises_por_entregas["destaque"] = paises_por_entregas["country_name"].apply(lambda x : "vencedor" if x == vencedor_entregas else "outros")
    
    total_entregas = paises_por_entregas["is_delivering_now"].sum()
    paises_por_entregas["percentual"] = (paises_por_entregas["is_delivering_now"] / total_entregas * 100)
    
    fig = px.bar(
    paises_por_entregas.head(5),
    title="",
    x="country_name",
    y="is_delivering_now",
    color="destaque",
    color_discrete_map={"vencedor": "red", "outros": "lightgray"},
    custom_data=["percentual"]
    )
    
    
    fig.update_traces(
    texttemplate="%{y:,.0f} (%{customdata[0]:.1f}%)",
    textposition="outside",
    cliponaxis=False
    )
    
    fig.update_layout(
    separators=",.",
    showlegend=False,
    xaxis_title=None,
    yaxis_title="Restaurantes"
    )

    return fig

# Grafico 5 - Quantidade de restaurantes que fazem reserva por pais
def paises_por_reserva(df1):
    paises_por_reserva = df1.groupby("country_name")["has_table_booking"].sum().sort_values(ascending = False).reset_index()
    vencedor_reserva = paises_por_reserva.iloc[0]["country_name"]
    paises_por_reserva["destaque"] = paises_por_reserva["country_name"].apply(lambda x : "vencedor" if x == vencedor_reserva else "outros")
    
    total_reservas = paises_por_reserva["has_table_booking"].sum()
    paises_por_reserva["percentual"] = (paises_por_reserva["has_table_booking"] / total_reservas * 100)
    
    fig = px.bar(
        paises_por_reserva.head(5),
        title="",
        x="country_name",
        y="has_table_booking",
        color="destaque",
        color_discrete_map={"vencedor": "red", "outros": "lightgray"},
        custom_data=["percentual"]
    )
    
    
    fig.update_traces(
        texttemplate="%{y:,.0f} (%{customdata[0]:.1f}%)",
        textposition="outside",
        cliponaxis=False
    )
    
    fig.update_layout(
        separators=",.",
        showlegend=False,
        xaxis_title=None,
        yaxis_title="Restaurantes"
    )

    return fig

# Grafico 6 - Quantidade avaliações feitas em cada país

def paises_por_avaliacao(df1):
    paises_por_avaliacao = df1.groupby("country_name")["votes"].sum().sort_values(ascending = False).reset_index()
    vencedor_avaliacoes = paises_por_avaliacao.iloc[0]["country_name"]
    paises_por_avaliacao["destaque"] = paises_por_avaliacao["country_name"].apply(lambda x: "vencedor" if x == vencedor_avaliacoes else "outros")
    
    total_votos = paises_por_avaliacao["votes"].sum()
    paises_por_avaliacao["percentual"] = (paises_por_avaliacao["votes"] / total_votos * 100)
    
    
    fig = px.bar(
        paises_por_avaliacao.head(5),
        title="Países com maior quantidade de avaliações feitas",
        x="country_name",
        y="votes",
        color="destaque",
        color_discrete_map={"vencedor": "red", "outros": "lightgray"},
        custom_data=["percentual"]
    )
    
    
    fig.update_traces(
        texttemplate="%{y:,.0f} (%{customdata[0]:.1f}%)",
        textposition="outside",
        cliponaxis=False
    )
    
    fig.update_layout(
        separators=",.",
        showlegend=False,
        xaxis_title=None,
        yaxis_title="Quantidade de avaliações"
    )

    return fig

def paises_por_media(df1):
    
# Grafico 7 - Média de avaliações feitas por país

    paises_por_media = (
        df1.groupby("country_name")["votes"]
        .mean()
        .sort_values(ascending=False)
        .reset_index()
    )
    
    vencedor_media = paises_por_media.iloc[0]["country_name"]
    paises_por_media["destaque"] = paises_por_media["country_name"].apply(
        lambda x: "vencedor" if x == vencedor_media else "outros"
    )
    
    total_media = paises_por_media["votes"].sum()
    paises_por_media["percentual"] = (
        paises_por_media["votes"] / total_media * 100
    )
    
    fig = px.bar(
        paises_por_media.head(5),
        title="",
        x="country_name",
        y="votes",
        color="destaque",
        color_discrete_map={"vencedor": "red", "outros": "lightgray"},
        custom_data=["percentual"]
    )
    
    fig.update_traces(
        texttemplate="%{y:,.1f} (%{customdata[0]:.1f}%)",
        textposition="outside",
        cliponaxis=False
    )
    
    fig.update_layout(
        separators=",.",
        showlegend=False,
        xaxis_title=None,
        yaxis_title="Média de votos"
    )
    return fig

# Grafico 8 - Maior média de nota por país
def paises_maior_nota(df1):
    paises_por_nota = df1.groupby("country_name")["aggregate_rating"].mean().sort_values(ascending = False).reset_index()
    paises_por_nota["aggregate_rating"] = paises_por_nota["aggregate_rating"].map('{:,.2f}'.format)
    return paises_por_nota
    
# Grafico 9 - Menor média de nota por país
def paises_menor_nota(df1):
    paises_por_nota_2 = df1.groupby("country_name")["aggregate_rating"].mean().sort_values(ascending = True).reset_index()
    paises_por_nota_2["aggregate_rating"] = paises_por_nota_2["aggregate_rating"].map('{:,.2f}'.format)
    return paises_por_nota_2
    
# Grafico 10 - Média de preço de um prato pra dois em R$ por país
def media_preco(df1):
    media_preco = df1.groupby("country_name")["average_cost_for_two_real"].mean().sort_values(ascending = False).reset_index()
    media_preco["average_cost_for_two_real"] = media_preco["average_cost_for_two_real"].map('{:,.2f}'.format)
    return media_preco


#==================================================================================================================================================================#
#                                                                      FILTROS
# ==================================================================================================================================================================#

with st.sidebar:
    try:
        st.logo("images/logo.png")
    except:
        pass
        
    st.markdown ("# Filtros")
    
    # Filtro Países
    paises_unicos = sorted(list(df_limpo["country_name"].unique()))
    on_paises = st.checkbox('Selecionar Todos os Países', value=True)

    if on_paises:
        sel_paises = st.multiselect("Paises", paises_unicos, default=paises_unicos, disabled=True)
        sel_paises = paises_unicos
    else:
        sel_paises = st.multiselect("Paises", paises_unicos, default=paises_unicos)

    # Filtro Culinárias
    if sel_paises:
        culinarias_disponiveis = sorted(list(df_culinaria.loc[df_culinaria["country_name"].isin(sel_paises), "cuisines"].unique()))
    else:
        culinarias_disponiveis = sorted(list(df_culinaria["cuisines"].unique()))

    on_culinarias = st.checkbox('Selecionar Todas as Culinárias', value=True)
    
    if on_culinarias:
        sel_culinarias = st.multiselect("Culinárias", culinarias_disponiveis, default=culinarias_disponiveis, disabled=True)
        sel_culinarias = culinarias_disponiveis
    else:
        sel_culinarias = st.multiselect("Culinárias", culinarias_disponiveis, default=culinarias_disponiveis)
    
    # Filtro Preço
    min_val = float(df_limpo["average_cost_for_two_real"].min())
    max_val = float(df_limpo["average_cost_for_two_real"].max())
    
    sel_preco = st.slider("Faixa de Preço (R$)", min_value=min_val, max_value=max_val, value=(min_val, max_val))

#==================================================================================================================================================================#
#                                                                      FILTROS
# ==================================================================================================================================================================#

# Filtro para gráficos gerais (df_limpo)
df_filtros = df_limpo.copy()

if sel_paises:
    df_filtros = df_filtros[df_filtros["country_name"].isin(sel_paises)]

df_filtros = df_filtros.loc[df_filtros["average_cost_for_two_real"].between(sel_preco[0], sel_preco[1])]

# Filtro para gráficos de culinária (df_culinaria)
df_culinaria_filtro = df_culinaria.copy()

if sel_paises:
    df_culinaria_filtro = df_culinaria_filtro[df_culinaria_filtro["country_name"].isin(sel_paises)]

df_culinaria_filtro = df_culinaria_filtro.loc[df_culinaria_filtro["average_cost_for_two_real"].between(sel_preco[0], sel_preco[1])]

if sel_culinarias:
    df_culinaria_filtro = df_culinaria_filtro[df_culinaria_filtro["cuisines"].isin(sel_culinarias)]
    
    
    ids_validos = df_culinaria_filtro["restaurant_id"].unique()
    df_filtros = df_filtros[df_filtros["restaurant_id"].isin(ids_validos)]

# ==================================================================================================================================================================#
#                                                                           PÁGINA
# ==================================================================================================================================================================#

st.title("📊 Visão Países")

tab_geral, tab_servicos, tab_avaliacao = st.tabs([
    "📊 Visão Geral",
    "🍽️ Restaurantes & Serviços",
    "⭐ Avaliações & Preços"
])
    
# ABA GERAL
with tab_geral:
    with st.container():
        col1, col2, col3 = st.columns(3)
       
        with col1:
            st.markdown("##### Cidades registrados por país")
            fig = cidades_por_pais(df_filtros)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("##### Restaurantes registrados por país")
            fig = restaurantes_por_pais(df_filtros)
            st.plotly_chart(fig, use_container_width=True)

        with col3:
            st.markdown("##### Culinárias únicas registrados por país")
            fig = culinarias_por_pais(df_culinaria_filtro)
            st.plotly_chart(fig, use_container_width=True)

# ABA SERVIÇOS
with tab_servicos:
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Paises com mais restaurantes que efetuam reserva")
            fig = paises_por_reserva(df_filtros)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("##### Paises com mais restaurantes que efetuam entregas")
            fig = paises_por_entregas(df_filtros)
            st.plotly_chart(fig, use_container_width=True)
        
# ABA AVALIAÇÕES
with tab_avaliacao:
    with st.container():
        col1, = st.columns(1)

        with col1:
            st.markdown("##### Média de avaliações feitas por país")
            fig = paises_por_media(df_filtros)
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    with st.container():
        col2, col3, col4 = st.columns(3)

        with col2:
            st.markdown("##### Países com melhor avaliação média")
            maiores_medias = paises_maior_nota(df_filtros)
            st.dataframe(maiores_medias.head(5), use_container_width=True)

        with col3:
            st.markdown("##### Países com pior avaliação média")
            menores_medias = paises_menor_nota(df_filtros)
            st.dataframe(menores_medias.head(5), use_container_width=True)
            
        with col4:
            st.markdown("##### Média de Preço em R$")
            preco_medio = media_preco(df_filtros)
            st.dataframe(preco_medio.head(5), use_container_width=True)


        
        
        

    









