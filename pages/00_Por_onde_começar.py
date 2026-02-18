import streamlit as st

# Configuração da página
st.set_page_config(page_title="Guia de Início - Cirurgia", page_icon="📖", layout="wide")

st.title("📖 Guia de Início - Especialidades Cirúrgicas")
st.markdown("---")

# --- SECÇÃO 1: PREPARAR A PLANILHA ---
st.header("1️⃣ Preparar a sua Planilha")

# Instrução de Obtenção de Listas
st.markdown("### 📋 Obtenção de Listas Pessoais")
st.write("Antes de começar, certifique-se de que extraiu as listagens operatórias corretas do sistema hospitalar.")
st.link_button("Ver Instruções de Obtenção de Listas 📄", "https://drive.google.com/file/d/1admteRooOe45rFAppOeU9kOrffbg0Mbq/view?usp=drive_link")

# CORREÇÃO AQUI: Mudado de stdio para html
st.markdown("<br>", unsafe_allow_html=True)

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("### 📑 Passo 1: Criar a sua cópia")
    st.write("Clique no botão abaixo para abrir o modelo oficial de Cirurgia e faça uma cópia para o seu Google Drive pessoal.")
    st.link_button("Abrir Template de Cirurgia ↗️", "https://docs.google.com/spreadsheets/d/1VBtrI-2r1jySl7dLi78R9srOa1ojSNIytscOyuOyJ68/edit?gid=1772153325#gid=1772153325")
    
    st.warning("""
    **💡 Nomes das Abas:** Se usar a sua própria planilha, garanta que as abas se chamam exatamente:  
    `Cirurgia`, `Ajudas`, `Honorários`.  
    *(O sistema diferencia maiúsculas de minúsculas).*
    """)

with col_b:
    st.markdown("### 🔑 Passo 2: Dar acesso ao sistema")
    st.write("Para que o sistema consiga escrever os dados, vá ao botão **Partilhar** da sua planilha e adicione este e-mail como **Editor**:")
    st.code("pdf-extractor@gen-lang-client-0404678969.iam.gserviceaccount.com", language="text")

st.markdown("---")

# --- SECÇÃO 2: ATIVAÇÃO ---
st.header("2️⃣ Ativar a Ligação")

st.markdown("### 🔗 Vincular no App")
st.write("O sistema utiliza uma ligação direta de alta velocidade via API Gemini 2.0.")
st.info("Vá à página **🏠 Home** no menu lateral e cole o **Link da sua Planilha** (o URL completo da cópia que criou no Passo 1).")

# --- SECÇÃO 3: ONDE CARREGAR CADA RELATÓRIO ---
st.markdown("---")
st.header("3️⃣ Onde carregar os seus relatórios?")
st.write("Selecione a página correta no menu lateral de acordo com o que deseja processar:")

c1, c2, c3 = st.columns(3)

with c1:
    st.info("### ✂️ Cirurgia Principal\nProcessamento de mapas operatórios onde figurou como cirurgião.")

with c2:
    st.success("### 🤝 Ajudas\nExtração de atos onde participou como 1º ou 2º ajudante.")

with c3:
    st.warning("### 💰 Honorários\nListagens de pagamentos e extratos recebidos.")

# --- SECÇÃO 4: REGRAS DE OURO ---
st.markdown("---")
st.header("💡 Regras de Ouro")

st.markdown("""
* **Fórmulas Pessoais:** Pode criar as suas fórmulas de cálculo nas **Colunas A e B**. O sistema escreve sempre a partir da **Coluna C**.
* **Privacidade Total:** Os dados são processados e enviados diretamente para o Google Sheets. Nenhum PDF é armazenado.
* **Qualidade do PDF:** Utilize PDFs digitais originais para garantir 100% de precisão nos códigos cirúrgicos.
* **Engine:** Sistema atualizado com o motor **Gemini 2.0 Flash**, otimizado para nomenclaturas médicas complexas.
""")

st.markdown("---")
st.caption("Sistema de Apoio Cirúrgico | v4.0 (2026)")
