import pickle
from pathlib import Path
import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

import streamlit_authenticator as stauth

st.set_page_config(
    page_title="Acompanhamento do Campeonato das Sociedades",
    page_icon=":trophy:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

names = ["Master","SDUFRJ","Hermenêutica","SDdUFC","SDS","Senatus","GDO","SDP","SDdUFSC"]
usernames = ["master","sdufrj","hermeneutica","sddufc","sds","senatus","gdo","sdp","sddufsc"]

file_path = Path(__file__).parent / "hashed_pw.pkl"
with file_path.open("rb") as file:
    hashed_passwords = pickle.load(file)

credentials = {"usernames":{}}

for un, name, pw in zip(usernames, names, hashed_passwords):
    user_dict = {"name":name,"password":pw}
    credentials["usernames"].update({un:user_dict})

authenticator = stauth.Authenticate(credentials, 'sd_dashboard', 'auth', cookie_expiry_days=30)

name, authentication_status, username = authenticator.login()

if authentication_status == False:
    st.error("Usuário/senha inválidos")

if authentication_status == None:
    st.warning("Por favor, faça o login")

if authentication_status:
    #Display the title and the description
    try:
    # check if the key exists in session state
        _ = st.session_state.keep_graphics
    except AttributeError:
        # otherwise set it to false
        st.session_state.keep_graphics = False

    st.write('# PAINEL DE ACOMPANHAMENTO DO CAMEONATO DAS SOCIEDADES')
    st.write('### Confira o andamento da maior competição entre as Sociedades de Debates do Brasil!')
    st.sidebar.caption('Login como: ' + name)
    st.divider()

    #Conexão com o sheets
    conn = st.connection('gsheets', type=GSheetsConnection)

    #Bases utilizadas
    delegacoes = conn.read(worksheet='TdS_Delegações', usecols = list(range(2)), ttl=5).dropna(how='all')
    rodadas = conn.read(worksheet='TdS_Rodadas', usecols = list(range(6)), ttl=5).dropna(how='all')
    resultados = conn.read(worksheet='TdS_Resultados', usecols = list(range(8)), ttl=5).dropna(how='all')
    juizes = conn.read(worksheet='TdS_Juizes', usecols = list(range(5)), ttl=5).dropna(how='all')
    temporario_rodada = conn.read(worksheet='TdS_Suporte', usecols = list(range(6)), ttl=5).dropna(how='all')

    #Lista de equipes
    lista_rodadas = rodadas['Rodada'].unique()
    sds = delegacoes['instituicao'].unique()
    sds = pd.DataFrame(sds, columns=['Instituição'])
    sds.set_index('Instituição', inplace=True)
    sds["Pontos"] = 0
    sds["N de Primeiros"] = 0
    sds["Total Sps"] = 0
    sds['Juizes Enviados'] = 0

    juizes['Juiz_cargo'] = juizes['Juiz'] + juizes['Posição']
    juizes['Juizes'] = juizes[['Rodada','Sala','Juiz_cargo']].groupby(['Rodada','Sala'])['Juiz_cargo'].transform(lambda x: ','.join(x))
    juizes_sintetico = juizes.drop(columns=['Juiz','Posição','Juiz_cargo'])
    juizes_sintetico = juizes[['Rodada','Sala','Juizes']].drop_duplicates().reset_index(drop=True).set_index('Rodada')

    partidas_agregado = resultados[['Rodada','Sala','Instituição','Casa','Classificação','Sps']].groupby(['Rodada','Sala','Instituição','Casa']).agg({'Classificação':'max', 'Sps':'sum'}).reset_index()
    tabela_partidas = partidas_agregado.pivot(index=['Rodada', 'Sala'], columns='Casa', values='Instituição').reset_index()
    tabela_partidas = tabela_partidas[['Rodada','Sala','1° GOVERNO','1ª OPOSIÇÃO','2° GOVERNO','2ª OPOSIÇÃO']].set_index('Rodada')
    tabela_resultado = partidas_agregado.pivot(index='Instituição', columns='Rodada', values='Classificação').reset_index('Instituição')

    base_resultados = partidas_agregado.copy()
    base_resultados['Resultado'] = base_resultados['Instituição'] + ' - ' + base_resultados['Classificação'].astype(str)
    base_resultados = base_resultados.pivot(index=['Rodada','Sala'], columns='Casa', values='Resultado').reset_index()
    base_resultados = pd.merge(base_resultados, juizes_sintetico, on=['Sala','Rodada'], how='left').reset_index(drop=True).set_index('Rodada')
    base_resultados = base_resultados[['Sala','1° GOVERNO','1ª OPOSIÇÃO','2° GOVERNO','2ª OPOSIÇÃO','Juizes']]
    rodada_corrente = base_resultados[base_resultados['Juizes'].isna()].index[0]
    data_rodada_corrente = rodadas[rodadas['Rodada'] == rodada_corrente]['Data'].reset_index(drop=True)[0]
    base_resultados = base_resultados[base_resultados['Juizes'].notna()]

    juizes_rodada = rodadas[rodadas["Rodada"] == int(rodada_corrente)]['Escalação Juízes'].reset_index(drop=True)[0]
    juizes_rodada = juizes_rodada.split('; ')
    juizes_rodada = pd.DataFrame(juizes_rodada, columns=['Juizes'])

    #----------- DEFINIÇÃO DE DELEGAÇÃO DO LOGIN ----------------
    if name != 'Master':
        debatedores = delegacoes[delegacoes['instituicao'] == name]['Nome']


    for index, row in partidas_agregado.iterrows():
        equipe = row['Instituição']
        resultado = row['Classificação']
        sds.loc[equipe, 'Total Sps'] += row['Sps']
        if resultado == '1°':
            sds.loc[equipe, 'Pontos'] += 3
            sds.loc[equipe, 'N de Primeiros'] += 1
        elif resultado == '2°':
            sds.loc[equipe, 'Pontos'] += 2
        elif resultado == '3°':
            sds.loc[equipe, 'Pontos'] += 1
        elif resultado == '4°':
            sds.loc[equipe, 'Pontos'] += 0

    for indez, row in juizes.iterrows():
        equipe = row['SD']
        if equipe != 'Condeb':
            sds.loc[equipe, 'Juizes Enviados'] += 1

    sds.sort_values(['Pontos', 'N de Primeiros', 'Total Sps'], ascending=[False, False, False], inplace=True)
    sds.reset_index(inplace=True)
    sds.index += 1
    sds['Colocação'] = sds.index
    sds.set_index('Colocação', inplace=True)

    #----------- ATUALIZAÇÃO DE DEBATEDOR DA PARTIDA ----------------

    if name == 'Master':
        st.sidebar.write('### usuário Administrador')
        st.sidebar.dataframe(temporario_rodada[temporario_rodada['rodada'] == int(rodada_corrente)])
    else:
        st.sidebar.write('### Escalação de Equipe (Rodada ' + str(int(rodada_corrente)) + ')')

        with st.form(key="escalacao_form"):
            with st.sidebar:
                debatedor_1 = st.sidebar.selectbox('Debatedor 1', debatedores, index=None)
                debatedor_2 = st.sidebar.selectbox('Debatedor 2', debatedores, index=None)
                if juizes_rodada[juizes_rodada['Juizes'] == str(name)].empty:
                    st.sidebar.caption('### SD não escalada para enviar juiz para esta rodada')
                    juiz = ''
                    email_juiz = ''
                else:
                    juiz = st.sidebar.text_input('Juiz Representante')
                    email_juiz = st.sidebar.text_input('Email do Juiz')
                cadastrar = st.form_submit_button(label = "Cadastrar")
        if cadastrar:
            if not debatedor_1 or not debatedor_2:
                st.warning("Por favor, preencha todos os campos para seguir com Cadastro")
                st.stop()
            else:
                cadastro_rodada = pd.DataFrame([
                    {
                        'rodada': int(rodada_corrente),
                        'delegação': name,
                        'membro 1': debatedor_1,
                        'membro 2': debatedor_2,
                        'juiz': juiz,
                        'e-mail juiz':email_juiz
                    }
                ]
                )
                updated_df = pd.concat([temporario_rodada, cadastro_rodada], ignore_index=True)
                conn.update(worksheet='TdS_Suporte', data=updated_df)
                st.sidebar.success('Escalação Cadastrada!')

    col5, col6,col7 = st.columns(3)

    with col6:
        st.write('### TABELA DA COMPETIÇÃO')
        sds

    st.divider()

    col1, col2, col10 = st.columns(3)
    with col1:
        st.write('### CHAVEAMENTO')
        tabela_partidas

    with col10:
        st.write('### CALENDARIO')
        calendario = rodadas[['Rodada','Data','Horário','Escalação Juízes']].set_index('Rodada')
        calendario

    st.write('#### Próxima Rodada: ' + str(int(rodada_corrente)) + '(' + str(data_rodada_corrente) + ')')
    st.divider()

    col3, col4 = st.columns(2)
    with col3:
        st.write('### RESULTADOS GERAIS')
        base_resultados

    with col4:
        st.write('### RESULTADOS POR RODADA')
        tabela_resultado = tabela_resultado.set_index('Instituição')
        tabela_resultado

    authenticator.logout('Logout','sidebar')
