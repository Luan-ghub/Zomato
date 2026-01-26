import streamlit as st


st.markdown("""
### Bem-vindo ao Dashboard Fome Zero
Este Dashboard foi feito utilizando o dataset da empresa Zomato.
O arquivo com as análises feitas e/ou do dataset utilizado estão abaixo para download.

**Como navegar:**
1. Use o menu lateral à esquerda para navegar entre as páginas de análise.
2. Utilize os filtros na barra lateral para refinar os dados por País, Culinária ou Preço.
3. Os gráficos são interativos: passe o mouse para ver detalhes.
""")
st.markdown("---")

st.markdown("### 📂 Arquivos")

col1, col2 = st.columns(2)

data_csv = None
try:
    with open("dataset/zomato.csv", "rb") as f:
        data_csv = f.read()
except FileNotFoundError:
    try:
        with open("zomato.csv", "rb") as f:
            data_csv = f.read()
    except:
        pass

data_ipynb = None
try:
    with open("dataset/project_fome_zero.ipynb", "rb") as f:
        data_ipynb = f.read()
except:
    pass

with col1:
    if data_csv:
        st.download_button(
            label="📥 Download Dataset (Zomato.csv)",
            data=data_csv,
            file_name="zomato.csv",
            mime="text/csv"
        )
    else:
        st.warning("Arquivo Zomato.csv não encontrado.")

with col2:
    if data_ipynb:
        st.download_button(
            label="📓 Download Análises (Jupyter Notebook)",
            data=data_ipynb,
            file_name="dataset/project_fome_zero.ipynb",
            mime="application/x-ipynb+json"
        )
    else:
        st.warning("Arquivo Jupyter Notebook não encontrado.")