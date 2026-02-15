import streamlit as st
import google.generativeai as genai
import gspread
import json
import re
import pdfplumber
import time
from datetime import datetime
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURAÇÕES INICIAIS ---
# NOTA: O set_page_config foi removido aqui porque já existe na Home.py

# Lemos a chave mestra e o link do cliente (vindo da Home)
master_api_key = st.secrets.get("GEMINI_API_KEY")
sheet_url = st.session_state.get('sheet_url')

if not master_api_key:
    st.error("❌ Erro Crítico: GEMINI_API_KEY não encontrada nos Secrets.")
    st.stop()

if not sheet_url:
    st.warning("⚠️ Configuração em falta! Por favor, insira o link da sua planilha na página **Home (🏠)**.")
    st.stop()

# --- 2. FUNÇÕES DE SUPORTE ---

def extrair_id_planilha(url):
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    return match.group(1) if match else url

def formatar_data(data_str):
    data_str = str(data_str).strip()
    if not data_str or "DD-MM-YYYY" in data_str.upper() or data_str.lower() == "none":
        return None
    match = re.search(r'(\d{4})-(\d{2})-(\d{2})', data_str)
    if match:
        return f"{match.group(3)}-{match.group(2)}-{match.group(1)}"
    match_pt = re.search(r'(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})', data_str)
    if match_pt:
        d, m, a = match_pt.groups()
        if len(a) == 2: a = "20" + a
        return f"{d.zfill(2)}-{m.zfill(2)}-{a}"
    return None

def extrair_dados_ia_com_espera(texto_pagina, model, max_tentativas=3):
    prompt = """
    Analisa o texto médico cirúrgico.
    REGRAS:
    1. DATA: Formato DD-MM-YYYY.
    2. NOME: Nome completo do doente em MAIÚSCULAS.
    3. PROCESSO: Apenas números do processo clínico.
    4. PROCEDIMENTO: Nome da cirurgia ou ato principal.
    JSON: [{"data": "DD-MM-YYYY", "processo": "123", "nome": "NOME DO DOENTE", "procedimento": "DESCRIÇÃO DO ATO"}]
    """
    for i in range(max_tentativas):
        try:
            response = model.generate_content(
                f"{prompt}\n\nTEXTO:\n{texto_pagina}",
                generation_config={"temperature": 0.0}
            )
            match = re.search(r'\[\s*\{.*\}\s*\]', response.text, re.DOTALL)
            return json.loads(match.group()) if match else []
        except Exception as e:
            if "429" in str(e):
                time.sleep((i + 1) * 2) 
            else:
                return []
    return []

# --- 3. CONEXÃO ---
try:
    genai.configure(api_key=master_api_key)
    model = genai.GenerativeModel("models/gemini-2.0-flash")
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(extrair_id_planilha(sheet_url))
    
    # ALTERADO: Aba agora chama-se 'Cirurgias'
    NOME_FOLHA = 'Cirurgias'
    try:
        worksheet = sh.worksheet(NOME_FOLHA)
    except:
        worksheet = sh.add_worksheet(title=NOME_FOLHA, rows="2000", cols="10")
        # Cabeçalho na Coluna C (Preserva A e B para as tuas fórmulas)
        worksheet.update(range_name="C1", values=[["Data", "Processo", "Nome Completo", "Procedimento / Cirurgia", "Data Extração", "Ficheiro Origem"]])

except Exception as e:
    st.error(f"❌ Erro de Conexão ou Permissão: {e}")
    st.info("Garanta que partilhou a planilha com o e-mail da conta de serviço como EDITOR.")
    st.stop()

# --- 4. INTERFACE ---
st.title("✂️ Extração de Listas de Cirurgias")
st.info("Sistema configurado para escrita a partir da Coluna C. Colunas A e B estão livres para as suas fórmulas.")

arquivos_pdf = st.file_uploader("Carregue os PDFs dos Mapas Operatórios", type=['pdf'], accept_multiple_files=True)

if arquivos_pdf and st.button("🚀 Iniciar Extração Cirúrgica"):
    
    st.info("A verificar registos existentes para evitar duplicados...")
    dados_atuais = worksheet.get_all_values()
    registos_existentes = set()
    
    # Chave de duplicados baseada na Data (Col C), Processo (Col D) e Nome (Col E)
    if len(dados_atuais) > 1:
        for r in dados_atuais[1:]:
            if len(r) >= 5: 
                chave = f"{r[2]}_{r[3]}_{r[4]}" 
                registos_existentes.add(chave)

    novas_linhas = []
    data_hoje = datetime.now().strftime("%d-%m-%Y %H:%M")
    progresso = st.progress(0)
    
    for idx, pdf_file in enumerate(arquivos_pdf):
        ultima_data_valida = ""
        with pdfplumber.open(pdf_file) as pdf:
            for i, pagina in enumerate(pdf.pages):
                texto = pagina.extract_text()
                if not texto: continue
                dados_ia = extrair_dados_ia_com_espera(texto, model)

                for d in dados_ia:
                    dt = formatar_data(d.get('data', ''))
                    if dt: ultima_data_valida = dt
                    else: dt = ultima_data_valida

                    processo = re.sub(r'\D', '', str(d.get('processo', '')))
                    nome = str(d.get('nome', '')).replace('\n', ' ').strip().upper()
                    proc_limpo = str(d.get('procedimento', '')).split('\n')[0].strip()
                    
                    # Filtro de termos indesejados (lixo de cabeçalho)
                    termos_lixo = ["UTILIZADOR", "PÁGINA", "LISTAGEM", "GHCE", "IMPRESSÃO"]
                    e_lixo = any(t in nome for t in termos_lixo)

                    if len(nome) > 3 and dt and not e_lixo:
                        chave_unica = f"{dt}_{processo}_{nome}"
                        
                        if chave_unica not in registos_existentes:
                            novas_linhas.append([
                                dt,           # Coluna C
                                processo,     # Coluna D
                                nome,         # Coluna E
                                proc_limpo,   # Coluna F
                                data_hoje,    # Coluna G
                                pdf_file.name # Coluna H
                            ])
                            registos_existentes.add(chave_unica)
        
        progresso.progress((idx + 1) / len(arquivos_pdf))

    if novas_linhas:
        try:
            proxima_linha = len(dados_atuais) + 1
            # Escrita direta a partir da Coluna C
            worksheet.update(
                range_name=f"C{proxima_linha}", 
                values=novas_linhas
            )
            st.success(f"✅ {len(novas_linhas)} cirurgias novas adicionadas à aba '{NOME_FOLHA}'.")
            st.dataframe(novas_linhas, column_config={"0": "Data", "1": "Processo", "2": "Nome", "3": "Cirurgia"})
        except Exception as e:
            st.error(f"❌ Erro ao escrever na planilha: {e}")
    else:
        st.warning("Não foram encontrados registos novos. Verifique se os PDFs já foram processados anteriormente.")
