import streamlit as st
from streamlit_gsheets import GSheetsConnection
import numpy as np
import pandas as pd

#Display the title and the description
st.title('Base Nacional de Campeonatos - CONDEB')
st.write('Busque resultados, acompanhe seu desempenho e extraia insights úteis para o seu desenvolvimento!')

#Conexão com o sheets
conn = st.connection('gsheets', type=GSheetsConnection)

#Bases utilizadas
cndc = conn.read(worksheet='CNDC', usecols = list(range(14)), ttl=5).dropna(how='all')
campeonatos = conn.read(worksheet='Campeonatos', usecols = list(range(6)), ttl=5).dropna(how='all')
resultados = conn.read(worksheet='resultados', usecols = list(range(7)), ttl=5).dropna(how='all')
st.sidebar.link_button("Faça seu Cadastro Nacional de Debatedor Universitário", 'https://www.instagram.com/condeb.debates/')

with st.form(key="consulta_form"):
    camp = st.multiselect("Selecione o campeonato", campeonatos['nome_camp'])
    camp_code = campeonatos[campeonatos['nome_camp'].isin(camp)]['cod_camp']
    rodada = st.multiselect("Selecione a rodada", resultados['rodada'].unique())
    
    busca = st.form_submit_button(label="Buscar")


if busca:
    mocoes = conn.read(worksheet='mocoes', usecols = list(range(4)), ttl=5).dropna(how='all')
    base_resultados = resultados[(resultados['cod_camp'].isin(camp_code)) & (resultados['rodada'].isin(rodada))]
    resultados_por_rodada = base_resultados.pivot(index=['cod_camp', 'rodada', 'adjudicators'], columns='side', values='team_result').reset_index()
    if len(resultados_por_rodada.columns)>6:
        resultados_por_rodada = resultados_por_rodada[['cod_camp', 'rodada', 'Primeira Defesa', 'Primeira Oposição', 'Segunda Defesa', 'Segunda Oposição','adjudicators']]
        st.markdown("## Resultados Por Rodada")
        st.dataframe(resultados_por_rodada)
        st.divider()
        st.markdown("## Moções Debatidas")
        base_mocoes = mocoes[(mocoes['cod_camp'].isin(camp_code))&(mocoes['rodada'].isin(rodada))]
        st.dataframe(base_mocoes)
    else:
        st.markdown("### Não há resultados para a pesquisa solicitada")
