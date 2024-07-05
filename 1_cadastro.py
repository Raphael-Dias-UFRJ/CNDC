import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from pyUFbr.baseuf import ufbr
import random

#Display the title and the description
st.title('CADASTRO NACIONAL DE DEBATEDOR COMPETITIVO')
st.markdown('## Em Desenvolvimento')
st.markdown('## Para acessar a base de torneios, vá para "Torneios" no menu lateral.')
#Conexão com o sheets

