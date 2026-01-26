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

st.set_page_config(page_title="Visão Cidades", page_icon="🏙️", layout="wide")

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

#Grafico 1 - Quantidade de culinárias únicas por cidade

def culinaria_por_cidade(df1):

    cidade_culinaria_unica = df_culinaria.groupby(["city","country_name"])["cuisines"].nunique().sort_values(ascending = False).reset_index()
    
    fig = px.bar(
        cidade_culinaria_unica.head(),
        x = "cuisines",
        y = "city",
        color = "country_name",
        title = "Culinárias por cidade",
        text = "cuisines",
        orientation = "h"
    )
    
    fig.update_layout(
        yaxis={'categoryorder':'total ascending'},
        separators=",.",
        xaxis_title="Culinarias",
        yaxis_title=None,
        showlegend=True 
    )
    
    fig.update_traces(
        texttemplate="%{text:,.0f}", 
        textposition="outside"
    )

    return fig




#Grafico 2 - Quantidade de restaurantes que aceitam reservas por cidade

def cidade_com_reserva(df1):

    cidade_com_reserva = df1.groupby(["city","country_name"])["has_table_booking"].sum().sort_values(ascending = False).reset_index()
    
    
    fig = px.bar(
        cidade_com_reserva.head(),
        x="has_table_booking",
        y="city",
        color="country_name",
        text="has_table_booking",
        title="Restaurantes com Reserva",
        orientation="h"
    )
    
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        separators=",.",
        xaxis_title="Quantidade de restaurantes",
        yaxis_title=None,
        showlegend=True
    )
    
    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside"
    )
    
    return fig
    
#Grafico 3 - Quantidade de restaurantes que aceitam entregas por cidade
    
def cidade_com_entregas(df1):

    cidade_com_entregas= df1.groupby(["city","country_name"])["is_delivering_now"].sum().sort_values(ascending = False).reset_index()
    
    
    fig = px.bar(
        cidade_com_entregas.head(),
        x="is_delivering_now",
        y="city",
        color="country_name",
        text="is_delivering_now",
        title="Restaurantes com Delivery",
        orientation="h"
    )
    
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        separators=",.",
        xaxis_title="Quantidade de restaurantes",
        yaxis_title=None,
        showlegend=True
    )
    
    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside"
    )
    
    return fig
    
#Grafico 4 - Quantidade de restaurantes que aceitam pedidos online por cidade

def cidade_pedido_online(df1):
    
    cidade_pedido_online= df1.groupby(["city","country_name"])["has_online_delivery"].sum().sort_values(ascending = False).reset_index()
    
    fig = px.bar(
        cidade_pedido_online.head(),
        x="has_online_delivery",
        y="city",
        color="country_name",
        text="has_online_delivery",
        title="Restaurantes com Pedidos Online",
        orientation="h"
    )
    
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        separators=",.",
        xaxis_title="Quantidade de restaurantes",
        yaxis_title=None,
        showlegend=True
    )
    
    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside"
    )
    
    return fig

#Grafico 5 - Restaurantes com maiores valores médios para dois por cidade

def cidade_maior_valor_final (df1):
    

    cidade_maior_valor_final = df1.groupby(["city","country_name"])["average_cost_for_two_real"].mean().sort_values(ascending = False).reset_index()
    
    fig = px.bar(
        cidade_maior_valor_final.head(),
        x="average_cost_for_two_real",
        y="city",
        color="country_name",
        text="average_cost_for_two_real",
        title="Cidades com Maior Custo Médio em Real para Dois",
        orientation='h'       
    )
    
    
    fig.update_layout(
        yaxis={'categoryorder':'total ascending'},
        separators=",.",
        xaxis_title="Custo Médio (R$)",
        yaxis_title=None,
        showlegend=True 
    )
    
    fig.update_traces(
        texttemplate='R$ %{text:,.2f}', 
        textposition='auto',
        cliponaxis=False
    )
    
    return fig

#Grafico 6 - Quantidade de restaurantes com avaliação maior que 4 por cidade

def nota_acima(df1):
    
    nota_acima = df1[df1["aggregate_rating"] >4]
    
    cidade_nota_alta = nota_acima.groupby(["country_name", "city"])["aggregate_rating"].count().sort_values(ascending=False).reset_index()
    
    fig = px.bar(
        cidade_nota_alta.head(),
        x = "aggregate_rating",
        y = "city",
        color = "country_name",
        title = "Cidades com Restaurantes de Nota Superior a 4",
        text = "aggregate_rating"
    )
    fig.update_layout(
        yaxis={'categoryorder':'total ascending'},
        separators=",.",
        xaxis_title="Quantidade de Restaurantes",
        yaxis_title=None,
        showlegend=True 
    )
    
    fig.update_traces(
        texttemplate='%{text:,.0f}', 
        textposition='outside'
    )
    return fig




#Grafico 7 - Quantidade de restaurantes com avaliação menor que 2.5 por cidade

def nota_abaixo(df1):

    nota_abaixo = df1[df1["aggregate_rating"] < 2.5]
    
    cidade_nota_baixa = nota_abaixo.groupby(["country_name", "city"])["aggregate_rating"].count().sort_values(ascending=False).reset_index()
    
    fig = px.bar(
        cidade_nota_baixa.head(),
        x = "aggregate_rating",
        y = "city",
        color = "country_name",
        title = "Cidades com Restaurantes de nota inferior a 2.5",
        text = "aggregate_rating"
    )
    fig.update_layout(
        yaxis={'categoryorder':'total ascending'},
        separators=",.",
        xaxis_title="Quantidade de Restaurantes",
        yaxis_title=None,
        showlegend=True 
    )
    
    fig.update_traces(
        texttemplate='%{text:,.0f}', 
        textposition='outside'
    )

    return fig


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
        sel_paises = st.multiselect("Países", paises_unicos, default=paises_unicos, disabled=True)
        sel_paises = paises_unicos
    else:
        sel_paises = st.multiselect("Países", paises_unicos, default=paises_unicos)

    # Filtro Preço
    min_val = float(df_limpo["average_cost_for_two_real"].min())
    max_val = float(df_limpo["average_cost_for_two_real"].max())
    
    sel_preco = st.slider("Faixa de Preço (R$)", min_value=min_val, max_value=max_val, value=(min_val, max_val))

#==================================================================================================================================================================#
#                                                                      LÓGICA DE FILTRAGEM
# ==================================================================================================================================================================#

df_filtered = df_limpo.copy()

if sel_paises:
    df_filtered = df_filtered.loc[df_filtered["country_name"].isin(sel_paises)]

df_filtered = df_filtered.loc[df_filtered["average_cost_for_two_real"].between(sel_preco[0], sel_preco[1])]

# Lógica especifica para o gráfico de culinária (dataset explodido)
df_filtered_culinaria = df_culinaria.copy()

if sel_paises:
    df_filtered_culinaria = df_filtered_culinaria.loc[df_filtered_culinaria["country_name"].isin(sel_paises)]

df_filtered_culinaria = df_filtered_culinaria.loc[df_filtered_culinaria["average_cost_for_two_real"].between(sel_preco[0], sel_preco[1])]

#==================================================================================================================================================================#
#                                                                      DASHBOARD
# ==================================================================================================================================================================#

st.title("📊 Visão Cidades")

# SEÇÃO GERAL
st.markdown("### Geral")
with st.container():
    col1, = st.columns(1)
    
    with col1:
        fig = culinaria_por_cidade(df_filtered_culinaria)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# SEÇÃO SERVIÇOS
st.markdown("### Serviços")
with st.container():
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig = cidade_pedido_online(df_filtered)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = cidade_com_reserva(df_filtered)
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        fig = cidade_com_entregas(df_filtered)
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# SEÇÃO AVALIAÇÕES
st.markdown("### Avaliações")
with st.container():
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig = cidade_maior_valor_final(df_filtered)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = nota_acima(df_filtered)
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        fig = nota_abaixo(df_filtered)
        st.plotly_chart(fig, use_container_width=True)


    
    