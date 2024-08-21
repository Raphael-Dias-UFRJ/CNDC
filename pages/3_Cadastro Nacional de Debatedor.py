import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from pyUFbr.baseuf import ufbr
import random

#Display the title and the description
st.title('CADASTRO NACIONAL DE DEBATEDOR COMPETITIVO')
st.markdown('Os dados pessoais coletados para o cadastro serao utilizados para: \n\n(1) viabilizar rastreailidade de debatedor entre diferentes torneios para acompanhamento pessoal do debatedor ou de sua Sociedade de Debates;\n\n (2) fornecer dados para elaboração de pesquisas de diversidade no movimento de debates, pesquisas de evolução da competição e demais estudos de cunho estratégico para planejamento de melhores políticas de expansão.\n\n Os dados são tratados conforme a Lei Geral de Proteção de Dados Pessoais.')

#Conexão com o sheets
conn = st.connection('gsheets', type=GSheetsConnection)

#Busca por dados
existing_data = conn.read(worksheet='CNDC', usecols = list(range(14)), ttl=5)
existing_data = existing_data.dropna(how='all')

#Lista de seleções
Cor_raça = [
    "Branca",
    "Preta",
    "Amarela",
    "Parda",
    "Indígena",
    "Não declarada"
]

sds = [
    'SDUFRJ',
    'Hermenêutica',
    'SDdUFC',
    'SDS',
    'Senatus',
    'Octógono',
    'SDdTB',
    'GDO',
    'SDP',
    'SDdUFSC',
    'SDUFES',
    'Veritas',
    'SDUERJ'
]

id_genero = [
    "Homem Cis",
    "Mulher Cis",
    "Homem Trans",
    "Mulher Trans",
    "Não Binário",
    "Gênero Fluido",
    "Outro",
]



#Criação de um novo debatedor
with st.form(key="debatedor_form"):
    nome = st.text_input(label="Nome Completo")
    instituicao = st.selectbox("Sociedade de Debates", options=sds, index=None)
    nascimento = st.date_input("Data de Nascimento")
    primeiro_torneio = st.text_input(label="Primeiro Torneio")
    data_primeiro_torneio = st.date_input(label="Data do Primeiro Torneio (Primeiro Dia)")
    genero = st.selectbox("Identidade de Gênero", options=id_genero, index=None)
    cor_raça = st.selectbox("Cor/Raça", options=Cor_raça, index=None)
    estado_origem = st.selectbox("Estado de Origem", options=ufbr.list_uf, index = None)
    cidade_origem = st.text_input(label = "Cidade de Origem")
    email = st.text_input(label="Email")
    telefone = st.text_input(label="Telefone")
    cadastrar = st.form_submit_button(label = "Cadastrar")


if float(str(data_primeiro_torneio)[5]+str(data_primeiro_torneio)[6])>6:
    mes_codigo_cndc = "2"
else:
    mes_codigo_cndc = "1"

ano_codigo_cndc = str(data_primeiro_torneio)[2]+str(data_primeiro_torneio)[3]

random_numbers = [str(random.randint(0, 9)) for _ in range(3)]
valor_unico_cndc = ''.join(random_numbers)

cndc = mes_codigo_cndc + ano_codigo_cndc + valor_unico_cndc





if cadastrar:
        #Check existing CNDC
        while existing_data["cndc_code"].astype(str).str.contains(cndc).any():
            random_numbers = [str(random.randint(0, 9)) for _ in range(3)]
            valor_unico_cndc = ''.join(random_numbers)
            cndc = mes_codigo_cndc + ano_codigo_cndc + valor_unico_cndc

        # Check if all mandatory fields are filled
        if not nome or not instituicao or not primeiro_torneio or not data_primeiro_torneio or not genero or not cor_raça or not cidade_origem or not estado_origem or not email or not telefone:
            st.warning("Por favor, preencha todos os campos para seguir com Cadastro")
            st.stop()
        elif existing_data["email"].astype(str).str.contains(email).any():
            st.warning("Já Existe um debatedor com esse e-mail cadastrado")
            st.stop()
        else:
            # Create a new row of vendor data
            debater_data = pd.DataFrame(
                [
                    {
                        "cndc_code": cndc,
                        "nome": nome,
                        "instituicao": instituicao,
                        "Data de Nascimento": nascimento,
                        "primeiro_torneio": primeiro_torneio,
                        "data_primeiro_torneio": data_primeiro_torneio.strftime("%d-%m-%y"),
                        "genero": genero,
                        "cor_raça": cor_raça,
                        "cidade_origem": cidade_origem,
                        "estado_origem": estado_origem,
                        "email": email,
                        "telefone": telefone,
                    }
                ]
            )

            # Add the new vendor data to the existing data
            updated_df = pd.concat([existing_data, debater_data], ignore_index=True)

            # Update Google Sheets with the new vendor data
            conn.update(worksheet="CNDC", data=updated_df)

            st.success("Cadastro realizado! Muito em breve será possível rastrear seu rendimento em diferentes torneios!")
