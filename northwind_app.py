import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Carregar dados
customers = pd.read_csv("customers.csv", sep=";")
orders = pd.read_csv("orders.csv", sep=";")
order_details = pd.read_csv("order_details.csv", sep=";")
products = pd.read_csv("products.csv", sep=";")

# Calcular a distribuição de pedidos por ano e mês
orders["order_date"] = pd.to_datetime(orders["order_date"])
orders["year"] = orders["order_date"].dt.year
orders["month"] = orders["order_date"].dt.month
pedidos_por_ano_mes = orders.groupby(["year", "month"])["order_id"].count().reset_index()
pedidos_por_ano_mes_pivot = pedidos_por_ano_mes.pivot(index="year", columns="month", values="order_id").fillna(0)

# Calcular a frequência de compras por cliente
frequencia_compras_distribuicao = orders.groupby("customer_id").size().value_counts().reset_index()
frequencia_compras_distribuicao.columns = ["frequencia_compras", "numero_clientes"]

# Calcular o total gasto por cada pedido
order_details["total"] = order_details["unit_price"] * order_details["quantity"] * (1 - order_details["discount"])

# Mesclar a tabela orders com order_details para obter o total gasto por cada pedido
orders_totals = orders.merge(order_details.groupby("order_id")["total"].sum().reset_index(), on="order_id")

# Calcular RFM
rfm = orders_totals.groupby("customer_id").agg({
    "order_date": lambda x: (pd.to_datetime("now") - pd.to_datetime(x.max())).days,
    "order_id": "count",
    "total": "sum"
}).reset_index()
rfm.columns = ["customer_id", "recencia", "frequencia", "total"]
niveis_r = range(5, 0, -1)
niveis_f = range(1, 6)
niveis_m = range(1, 6)
r_quintis = pd.qcut(rfm["recencia"], q=5, labels=niveis_r)
f_quintis = pd.qcut(rfm["frequencia"], q=5, labels=niveis_f)
m_quintis = pd.qcut(rfm["total"], q=5, labels=niveis_m)
rfm = rfm.assign(R=r_quintis, F=f_quintis, M=m_quintis)
rfm["R"] = rfm["R"].astype("int64")
rfm["F"] = rfm["F"].astype("int64")
rfm["M"] = rfm["M"].astype("int64")
rfm["RFM_score"] = rfm[["R", "F", "M"]].sum(axis=1)
rfm["FM_media"] = rfm[["F", "M"]].mean(axis=1).round().astype("int64")

def classificar(df):
    if (df["FM_media"] == 5) and (df["R"] == 1):
        return "Não posso perdê-lo"
    elif (df["FM_media"] == 5) and ((df["R"] == 3) or (df["R"] == 4)):
        return "Cliente leal"
    elif (df["FM_media"] == 5) and (df["R"] == 5):
        return "Campeão"
    elif (df["FM_media"] == 4) and (df["R"] >= 3):
        return "Cliente leal"    
    elif (df["FM_media"] == 3) and (df["R"] == 3):
        return "Precisa de atenção"    
    elif ((df["FM_media"] == 3) or (df["FM_media"] == 2)) and (df["R"] > 3):
        return "Lealdade potencial" 
    elif ((df["FM_media"] == 2) or (df["FM_media"] == 1)) and (df["R"] == 1):
        return "Perdido"     
    elif (df["FM_media"] == 2) and (df["R"] == 2):
        return "Hibernando"     
    elif ((df["FM_media"] == 2) or (df["FM_media"] == 1)) and (df["R"] == 3):
        return "Prestes a hibernar"
    elif (df["FM_media"] == 1) and (df["R"] == 2):
        return "Perdido"
    elif (df["FM_media"] == 1) and (df["R"] == 4):
        return "Promissor"       
    elif (df["FM_media"] == 1) and (df["R"] == 5):
        return "Recentes"  
    else:
        return "Em risco"
rfm["Classe"] = rfm.apply(classificar, axis=1)
rfm_classificacao = rfm["Classe"].value_counts()

# Título da Aplicação
st.title("Análise de Indicadores da Northwind")

# Visão Geral
st.header("Visão Geral")
st.write(f"**Faturamento Total:** R$ 1265793.04")
st.write(f"**Ticket Médio:** R$ 1525.05")
st.write(f"**Churn Rate:** 8.14%")

# Filtros
st.sidebar.header("Filtros")

# Filtro por Categoria de Produto
categorias = products["category_id"].unique()
categoria_selecionada = st.sidebar.multiselect("Categoria de Produto", categorias, categorias)

# Filtro por Ano
anos = orders["year"].unique()
ano_selecionado = st.sidebar.multiselect("Ano", anos, anos)

# Aplicar Filtros
faturamento_por_categoria_filtrado = order_details[order_details["product_id"].isin(products[products["category_id"].isin(categoria_selecionada)]["product_id"])].groupby("product_id")["total"].sum().reset_index()
faturamento_por_categoria_filtrado = faturamento_por_categoria_filtrado.merge(products[["product_id", "category_id"]], on="product_id").groupby("category_id")["total"].sum().reset_index()
faturamento_por_categoria_filtrado.columns = ["Categoria", "Faturamento"]

pedidos_por_ano_mes_filtrado = orders[orders["year"].isin(ano_selecionado)]
pedidos_por_ano_mes_pivot_filtrado = pedidos_por_ano_mes_filtrado.groupby(["year", "month"])["order_id"].count().reset_index().pivot(index="year", columns="month", values="order_id").fillna(0)

orders_filtrados = orders[orders["year"].isin(ano_selecionado)]
order_details_filtrados = order_details[order_details["order_id"].isin(orders_filtrados["order_id"])]
order_details_filtrados["total"] = order_details_filtrados["unit_price"] * order_details_filtrados["quantity"] * (1 - order_details_filtrados["discount"])

# Faturamento por Categoria de Produto
st.header("Faturamento por Categoria de Produto")
faturamento_por_categoria_filtrado = order_details_filtrados[order_details_filtrados["product_id"].isin(products[products["category_id"].isin(categoria_selecionada)]["product_id"])].groupby("product_id")["total"].sum().reset_index()
faturamento_por_categoria_filtrado = faturamento_por_categoria_filtrado.merge(products[["product_id", "category_id"]], on="product_id").groupby("category_id")["total"].sum().reset_index()
faturamento_por_categoria_filtrado.columns = ["Categoria", "Faturamento"]
st.table(faturamento_por_categoria_filtrado)

plt.figure(figsize=(10, 6))
plt.bar(faturamento_por_categoria_filtrado["Categoria"], faturamento_por_categoria_filtrado["Faturamento"], color="skyblue")
plt.xlabel("Categoria de Produto")
plt.ylabel("Faturamento Total")
plt.title("Faturamento por Categoria de Produto")
st.pyplot(plt)

# Distribuição de Pedidos por Ano e Mês
st.header("Distribuição de Pedidos por Ano e Mês")
plt.figure(figsize=(12, 8))
plt.title("Distribuição de Pedidos por Ano e Mês")
sns.heatmap(pedidos_por_ano_mes_pivot_filtrado, fmt="g", cmap="YlGnBu")
plt.xlabel("Mês")
plt.ylabel("Ano")
st.pyplot(plt)

# Frequência de Compras por Cliente
st.header("Frequência de Compras por Cliente")
plt.figure(figsize=(10, 6))
plt.bar(frequencia_compras_distribuicao["frequencia_compras"], frequencia_compras_distribuicao["numero_clientes"], color="salmon")
plt.xlabel("Frequência de Compras")
plt.ylabel("Número de Clientes")
plt.title("Frequência de Compras por Cliente")
st.pyplot(plt)

# Análise RFM
st.header("Análise RFM dos Clientes")

plt.figure(figsize=(12, 6))
plt.bar(rfm_classificacao.index, rfm_classificacao.values, color="purple")
plt.xlabel("Classe RFM")
plt.ylabel("Número de Clientes")
plt.title("Classificação RFM dos Clientes")
plt.xticks(rotation=45)
st.pyplot(plt)