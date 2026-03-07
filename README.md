# Dashboard Zomato - [https://zomatodash.streamlit.app/]

## 1. O Problema de Negócio

**O que é o Zomato?**
O Zomato é uma empresa multinacional que atua como um portal de pesquisa de restaurantes e serviço de entrega de comida. O seu modelo de negócio funciona como um marketplace que liga clientes e restaurantes parceiros, rentabilizando através de taxas de comissão e publicidade.

**O Dataset**
O conjunto de dados utilizado neste projeto contém informações detalhadas sobre restaurantes registados na plataforma em várias partes do mundo. Inclui dados de localização (país, cidade, coordenadas geográficas), características do serviço (se faz entregas, se aceita reservas), tipos de culinária oferecida, custos médios e avaliações dos clientes (notas e total de votos).

**Objetivo**
Através dos dados do Zomato, é possível entender o comportamento do mercado gastronómico global, identificar tendências de consumo e mapear o desempenho de restaurantes e culinárias por região.
Simulando a atuação como um Cientista de Dados da empresa, o meu papel foi processar esta base de dados e desenvolver um dashboard com KPIs e visualizações estratégicas. O objetivo era fornecer respostas a um CEO sobre possíveis métricas do negócio, focando em diferentes visões do negócio.
O resultado foi um Dashboard interativo, totalmente funcional na web, que permite a navegação e filtragem de dados em três níveis de granularidade: Países, Cidades e Restaurantes/Culinárias.

---

## 2. Premissas do Negócio

Para a construção deste projeto, foram adotadas as seguintes premissas:

- **Modelo de Negócio:** Considerou-se a visão de Marketplace.
- **Visões Abordadas:** O projeto focou em três visões principais:
    1. **Visão Países:** Entendimento do alcance global e volume de operações.
    2. **Visão Cidades:** Análise de densidade, diversidade culinária e infraestrutura de serviços.
    3. **Visão Restaurantes:** Avaliação de qualidade popularidade e precificação dos estabelecimentos e tipos de pratos.

---

## 3. Estratégia da Solução

O projeto foi executado através das seguintes etapas:

1. **Entendimento e Planeamento:** Levantamento das principais perguntas de negócio que precisavam de ser respondidas.
2.  **Limpeza de Dados:**
    - Tratamento de valores nulos;
    - Padronização de nomes de colunas;
    - Feature Engineering
3. **Análise Exploratória (EDA):** Criação de protótipos de gráficos no Jupyter Notebook usando a biblioteca *Plotly* para validar as respostas e hipóteses levantadas.
4. **Desenvolvimento do Dashboard:**
    - Estruturação do código `.py` separados (`paises.py`, `cidades.py`, `restaurantes.py`) para organização;
    - Finalização do código voltado ao Streamlit, para fornecer um dashboard interativo e portável para Web.

---

## 4. Top 3 Insights de Dados

Durante a análise exploratória, os principais insights descobertos foram:

> **1. Volume x Qualidade**:
Países com a maior quantidade de restaurantes registados não possuem, necessariamente, a maior nota média geral, ou seja, a qualidade dos serviços e culinária oferecida em cada região não depende, necessariamente, da expansão da cultura gastronômica.


> **2. Serviços**
Cidades onde os restaurantes oferecem maior infraestrutura de reservas e delivery tendem a ter um volume de avaliações significativamente maior, mostrando que a conveniência atrai e retém o utilizador na plataforma.

> **3. Culinárias de nichos e Culinárias populares**
Existem culinárias de nicho, que possuem um ticket médio alto e uma altíssima taxa de aprovação, enquanto culinárias mais populares, como fast foods, têm um volume alto de votos, mas notas médias de avaliação menores. Esse insight que pode gerar marketings direcionados de forma mais fácil para cada uma das formas de culinária.

---

## 5. O Produto Final do Projeto

O produto final é um Dashboard Interativo no Streamlit, acessível a partir de qualquer navegador através do Streamlit Cloud.

**Funcionalidades do App:**

- **Filtros Dinâmicos:** O utilizador pode filtrar toda a aplicação por Países, Cidades, Tipos de Culinária e Faixa de Preço.
- **Navegação em Abas e Secções: É possível verificar as diferentes visões expostas no início do texto nas abas do dashboard**
- **Exportação de Dados:** Uma página dedicada de "Como Utilizar" que permite ao utilizador fazer o download do dataset limpo e do notebook com as análises completas para verificar o trabalho que foi feito mais detalhadamente

🔗 **Link para o Dashboard:** [https://zomatodash.streamlit.app/]

---

## 6. Conclusão e Próximos Passos

O objetivo foi transformar dados brutos numa ferramenta de navegação estratégica e visual permitindo a visualização de diferentes regiões do negócio.

**Próximos Passos (Evolução do Projeto):**
Caso este projeto fosse continuado, gostaria de implementar conhecimentos que irei adquirir futuramente utilizando Machine Learning, com etapas como:

- **Sistema de Recomendação:** Criar um modelo de Machine Learning capaz de recomendar restaurantes aos utilizadores com base no seu histórico de preferências de custo e culinária.
- **Previsão de Notas:** Desenvolver um algoritmo de classificação para prever se um restaurante terá uma nota excelente ou má logo no momento do registo, com base na sua localização, preço e serviços oferecidos.
