#===========================================================================================================================================================================                             
                                                                                # BIBLIOTECAS
#===========================================================================================================================================================================
import numpy as np
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster
from PIL import Image

#===========================================================================================================================================================================                             
                                                                                # TÍTULO
#==========================================================================================================================================================================

st.set_page_config(page_title="Fome Zero", page_icon="🍽️", layout="wide")

# ==================================================================================================================================================================#
#                                                                     LIMPEZA E FEATURE ENGINEERING
# ==================================================================================================================================================================#
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

    # CARREGAMENTO DOS DADOS
    df = pd.read_csv("dataset/zomato.csv")
    
    # LIMPEZA E ORGANIZAÇÃO

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

#===========================================================================================================================================================================                             
                                                                                # SIDEBAR
#===========================================================================================================================================================================
   
st.logo("images/logo.png")

#----------------------------------------------
        #Página Inicial
#----------------------------------------------
def home():
    
    with st.sidebar:
        st.markdown("# Zomato - Dashboard")
        st.markdown("---")
        
#----------------------------------------------
        #Filtros
#----------------------------------------------
        df_filtros = df_limpo.copy()
        df_culinaria_filtro = df_culinaria.copy()
        
        #Filtro de Preço
        
        min_val = df_filtros["average_cost_for_two_real"].min()
        max_val = df_filtros["average_cost_for_two_real"].max()
      
        sel_preco = st.slider(
            "Faixa de Preço (R$)",
            min_value=min_val,
            max_value=max_val,
            value=(min_val, max_val)
        )

        #Aplicação do filtro

        df_filtros = df_filtros.loc[(df_filtros["average_cost_for_two_real"] >= sel_preco[0]) & (df_filtros["average_cost_for_two_real"] <= sel_preco[1])]
    
        # Filtro de Culinarias
        todas_culinarias = sorted(list(df_culinaria_filtro["cuisines"].unique()))
        sel_culinarias = st.multiselect("Culinárias", todas_culinarias)

        #Aplicação do Filtro

        if sel_culinarias:
            df_culinaria_filtro = df_culinaria_filtro[df_culinaria_filtro["cuisines"].isin(sel_culinarias)]
            df_filtros = df_filtros[df_filtros["restaurant_id"].isin(df_culinaria_filtro["restaurant_id"])]

    
        #Buscar Restaurante
        sel_texto = st.text_input("Buscar Restaurante por Nome")

        #Aplicação do Filtro

        if sel_texto:
            df_filtros = df_filtros[df_filtros["restaurant_name"].str.contains(sel_texto, case=False, na=False)]
        
        
    st.title("Fome Zero Dashboard")
    st.markdown("### Métricas Gerais")

#----------------------------------------------
    # Medidas 
#----------------------------------------------
    
    with st.container():
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1: st.metric("Restaurantes", df_filtros["restaurant_id"].nunique())
        with col2: st.metric("Países", df_filtros["country_name"].nunique())
        with col3: st.metric("Cidades", df_filtros["city"].nunique())
        with col4: 
            votos = df_filtros["votes"].sum()
            st.metric("Avaliações", f"{votos:,.0f}".replace(",", "."))
        with col5: st.metric("Culinárias", df_filtros["cuisines"].nunique())
            
 #---------------------------------------------------
    st.markdown("---")
 #---------------------------------------------------
    
#----------------------------------------------
    # Mapa 
#----------------------------------------------
        
    st.markdown("### 🗺️ Visão Geográfica")
    mapa = create_map(df_filtros)
    folium_static(mapa, width=1024, height=600)

#----------------------------------------------
    #Paginas
#----------------------------------------------
pages = {
    "Geral": [st.Page(home, title="Home", icon="🏠")],
    "Sobre": [
        st.Page("pages/0_como_utilizar.py", title="Como Utilizar", icon="❔"),
    ],
    "Análises": [
        st.Page("pages/1_paises.py", title="Visão Países", icon="🌍"),
        st.Page("pages/2_cidades.py", title="Visão Cidades", icon="🏙️"),
        st.Page("pages/3_restaurantes.py", title="Visão Restaurantes", icon="🍽️"),
    ],
}

pg = st.navigation(pages)

pg.run()
















