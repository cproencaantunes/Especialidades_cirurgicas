import streamlit as st

# Configuração da página (NÃO usar st.set_page_config se já estiver no Home.py, 
# mas se esta for a primeira página a ser lida, pode manter. 
# Recomendo remover se der erro de JavaScript)

st.title("📖 Guia de Início - Especialidades Cirúrgicas")
st.markdown("---")

# --- SECÇÃO 1: PREPARAR A PLANILHA ---
st.header("1️⃣ Preparar a sua Planilha")
col_a, col_b = st.columns(2)

with col_a:
    st.markdown("### 📑 Passo 1: Criar a sua cópia")
    st.write("Clique no botão abaixo para abrir o modelo oficial de Cirurgia e faça uma cópia para o seu Google Drive.")
    # Link atualizado conforme o teu pedido
    st.link_button("Abrir Template de Cirurgia ↗️", "https://docs.google.com/spreadsheets/d/1VBtrI-2r1jySl7dLi78R9srOa1ojSNIytscOyuOyJ68/edit?gid=1772153325#gid=1772153325")

with col_b:
    st.markdown("### 🔑 Passo 2: Dar acesso ao sistema")
    st.write("Para que o sistema consiga escrever os dados, vá ao botão **Partilhar** da sua planilha e adicione este e-mail como **Editor**:")
    st.code("pdf-extractor@gen-lang-client-0404678969.iam.gserviceaccount.com", language="text")

st.markdown("---")

# --- SECÇÃO 2: ATIVAÇÃO ---
st.header("2️⃣ Ativar a Ligação")

st.markdown("### 🔗 Vincular no App")
st.write("O sistema utiliza uma ligação direta de alta velocidade via API Gemini.")
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
    st.warning("### 💰 Honorários\nListagens de pagamentos e extratos recebidos das entidades.")

# --- SECÇÃO 4: REGRAS DE OURO ---
st.markdown("---")
st.header("💡 Regras de Ouro")

st.markdown("""
* **Fórmulas Pessoais:** Pode criar as suas fórmulas de cálculo nas **Colunas A e B**. O sistema escreve sempre a partir da **Coluna C**, preservando os seus cálculos de valores.
* **Privacidade Total:** Os dados são processados e enviados diretamente para o Google Sheets. Nenhum dado de doente é armazenado no nosso servidor.
* **Qualidade do PDF:** Utilize PDFs digitais originais. Evite fotos de papéis, pois a precisão da IA diminui consideravelmente.
* **Engine:** Este sistema corre sobre o motor **Gemini 2.0 Flash (2026 Edition)**, garantindo a extração precisa de procedimentos complexos e códigos.
""")

st.markdown("---")
st.caption("Sistema de Apoio Cirúrgico | v4.0 (2026)")
