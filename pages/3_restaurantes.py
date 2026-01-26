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

st.set_page_config(page_title="Visão Restaurantes", page_icon="🍽️", layout="wide")

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

#===========================================================================================================================================================================                             
#                                                                                FILTROS
#===========================================================================================================================================================================
with st.sidebar:
  
    st.logo("images/logo.png")
        
    st.markdown("# Filtros")
    
    paises_unicos = sorted(list(df_limpo["country_name"].unique()))
    
    on_paises = st.checkbox('Selecionar Todos os Países', value=True)

    if on_paises:
        sel_paises = st.multiselect("Escolha os Países", paises_unicos, default=paises_unicos, disabled=True)
        sel_paises = paises_unicos
    else:
        sel_paises = st.multiselect("Escolha os Países", paises_unicos, default=paises_unicos)
    
    if sel_paises:
        cidades_disponiveis = sorted(list(df_limpo.loc[df_limpo["country_name"].isin(sel_paises), "city"].unique()))
    else:
        cidades_disponiveis = sorted(list(df_limpo["city"].unique()))
    
    on_cidades = st.checkbox('Selecionar Todas as Cidades', value=True)

    if on_cidades:
        sel_cidades = st.multiselect("Escolha as Cidades", cidades_disponiveis, default=cidades_disponiveis, disabled=True)
        sel_cidades = cidades_disponiveis
    else:
        sel_cidades = st.multiselect("Escolha as Cidades", cidades_disponiveis, default=cidades_disponiveis)

    if sel_paises:
        culinarias_disponiveis = sorted(list(df_culinaria.loc[df_culinaria["country_name"].isin(sel_paises), "cuisines"].unique()))
    else:
        culinarias_disponiveis = sorted(list(df_culinaria["cuisines"].unique()))
        
    on_culinarias = st.checkbox('Selecionar Todas as Culinárias', value=True)

    if on_culinarias:
        sel_culinarias = st.multiselect("Escolha as Culinárias", culinarias_disponiveis, default=culinarias_disponiveis, disabled=True)
        sel_culinarias = culinarias_disponiveis
    else:
        sel_culinarias = st.multiselect("Escolha as Culinárias", culinarias_disponiveis, default=culinarias_disponiveis)
    
    min_val = float(df_limpo["average_cost_for_two_real"].min())
    max_val = float(df_limpo["average_cost_for_two_real"].max())
    
    sel_preco = st.slider("Faixa de Preço (R$)", min_value=min_val, max_value=max_val, value=(min_val, max_val))


df_filtered_cuisines = df_culinaria.copy()

if sel_paises:
    df_filtered_cuisines = df_filtered_cuisines.loc[df_filtered_cuisines["country_name"].isin(sel_paises)]

if sel_cidades:
    df_filtered_cuisines = df_filtered_cuisines.loc[df_filtered_cuisines["city"].isin(sel_cidades)]

df_filtered_cuisines = df_filtered_cuisines.loc[df_filtered_cuisines["average_cost_for_two_real"].between(sel_preco[0], sel_preco[1])]

if sel_culinarias:
    df_filtered_cuisines = df_filtered_cuisines.loc[df_filtered_cuisines["cuisines"].isin(sel_culinarias)]

df_filtered_main = df_limpo.copy()

if sel_paises:
    df_filtered_main = df_filtered_main.loc[df_filtered_main["country_name"].isin(sel_paises)]

if sel_cidades:
    df_filtered_main = df_filtered_main.loc[df_filtered_main["city"].isin(sel_cidades)]

df_filtered_main = df_filtered_main.loc[df_filtered_main["average_cost_for_two_real"].between(sel_preco[0], sel_preco[1])]

#===========================================================================================================================================================================
#                                                                                PÁGINA
#===========================================================================================================================================================================
st.title("🍽️ Visão Restaurantes & Culinárias")

st.markdown("### Melhores Culinárias")

metrics_df = df_filtered_cuisines.groupby("cuisines").agg({'aggregate_rating': 'mean', 'votes': 'sum'}).sort_values(['aggregate_rating', 'votes'], ascending=[False, False]).head(5).reset_index()

with st.container():
    cols = st.columns(5)
    
    for i, row in metrics_df.iterrows():
        cuisine_name = row['cuisines']
        cuisine_rating = row['aggregate_rating']
        
        best_rest = df_filtered_cuisines[df_filtered_cuisines['cuisines'] == cuisine_name].sort_values(['aggregate_rating', 'votes'], ascending=[False, False]).iloc[0]
        
        col = cols[i]
        col.metric(
            label=f"{cuisine_name}",
            value=f"{cuisine_rating:.2f}/5.0",
            help=f"Melhor Restaurante: {best_rest['restaurant_name']}\nPaís: {best_rest['country_name']}\nCidade: {best_rest['city']}"
        )
        col.caption(f"🏅 {best_rest['restaurant_name']}")
        col.caption(f"📍 {best_rest['city']}, {best_rest['country_name']}")

st.markdown("---")

st.markdown("### Top 5 Restaurantes por Tipo de Culinária")

top_restaurants_per_cuisine = df_filtered_cuisines.sort_values(['cuisines', 'aggregate_rating', 'votes'], ascending=[True, False, False])
top_restaurants_per_cuisine = top_restaurants_per_cuisine.groupby('cuisines').head(5)

cols_to_show = ['restaurant_name', 'country_name', 'city', 'cuisines', 'average_cost_for_two_real', 'aggregate_rating', 'votes']
st.dataframe(
    top_restaurants_per_cuisine[cols_to_show].rename(columns={
        'restaurant_name': 'Restaurante', 
        'country_name': 'País', 
        'city': 'Cidade', 
        'cuisines': 'Culinária',
        'average_cost_for_two_real': 'Custo (R$)',
        'aggregate_rating': 'Nota',
        'votes': 'Votos'
    }),
    use_container_width=True,
    hide_index=True
)

st.markdown("---")

st.markdown("### Ranking de Culinárias")

cuisine_ranking = df_filtered_cuisines.groupby("cuisines").agg({'aggregate_rating': 'mean'}).reset_index()

with st.container():
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Top 10 Melhores Culinárias")
        top_10_best = cuisine_ranking.sort_values('aggregate_rating', ascending=False).head(10)
        fig_best = px.bar(top_10_best, x='cuisines', y='aggregate_rating', text_auto='.2f', color='aggregate_rating', color_continuous_scale='Greens')
        fig_best.update_layout(xaxis_title="Culinária", yaxis_title="Nota Média", showlegend=False)
        st.plotly_chart(fig_best, use_container_width=True)
        
    with col2:
        st.markdown("##### Top 10 Piores Culinárias")
        top_10_worst = cuisine_ranking.sort_values('aggregate_rating', ascending=True).head(10)
        fig_worst = px.bar(top_10_worst, x='cuisines', y='aggregate_rating', text_auto='.2f', color='aggregate_rating', color_continuous_scale='Reds_r')
        fig_worst.update_layout(xaxis_title="Culinária", yaxis_title="Nota Média", showlegend=False)
        st.plotly_chart(fig_worst, use_container_width=True)

st.markdown("---")

st.markdown("### 🗳️ Distribuição de Recomendações")

recom_data = df_filtered_main.groupby(['country_name', 'city', 'recomendation']).size().reset_index(name='count')

fig_recom = px.bar(
    recom_data, 
    x="city", 
    y="count", 
    color="recomendation",
    title="Quantidade de Restaurantes por Tipo de Recomendação e Cidade",
    labels={'city': 'Cidade', 'count': 'Quantidade', 'recomendation': 'Recomendação', 'country_name': 'País'},
    color_discrete_map={
        "muito recomendado": "green",
        "recomendado": "orange",
        "pouco recomendado": "red",
        "Neutro": "gray"
    },
    hover_data=['country_name']
)

fig_recom.update_layout(barmode='stack', xaxis={'categoryorder':'total descending'})
st.plotly_chart(fig_recom, use_container_width=True)