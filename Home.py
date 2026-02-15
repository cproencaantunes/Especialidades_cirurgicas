import streamlit as st
import time

# 1. Configuração da página (Deve ser a primeira linha de código)
st.set_page_config(
    page_title="Hub Cirurgia Pro", 
    page_icon="✂️", 
    layout="wide"
)

# 2. Inicializar o estado de autenticação
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# 3. Função de Login
def mostrar_login():
    # O placeholder limpa o ecrã após o login, evitando erros de JavaScript
    placeholder = st.empty()
    
    with placeholder.container():
        st.title("🔐 Acesso Restrito - Cirurgia")
        col1, col2, col3 = st.columns([1,2,1])
        
        with col2:
            with st.form("login_form"):
                user_input = st.text_input("Utilizador")
                pass_input = st.text_input("Password", type="password")
                
                if st.form_submit_button("Entrar"):
                    # Procura as credenciais nos Secrets do Streamlit
                    allowed_users = st.secrets.get("users", {})
                    
                    if user_input in allowed_users and str(allowed_users[user_input]) == pass_input:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = user_input
                        st.success("Autenticado! A carregar...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Credenciais incorretas")

# 4. Verificação de Autenticação
if not st.session_state["authenticated"]:
    mostrar_login()
    st.stop()  # Impede o carregamento do menu lateral e do conteúdo

# --- CONTEÚDO VISÍVEL APENAS APÓS LOGIN ---

st.title(f"✂️ Bem-vindo ao Hub de Cirurgia, Dr. {st.session_state.get('username', '')}")

# Sidebar para configurações globais
with st.sidebar:
    st.header("⚙️ Configuração")
    st.session_state['sheet_url'] = st.text_input(
        "Link da Planilha de Cirurgias (Google Sheets)", 
        value=st.session_state.get('sheet_url', ''),
        placeholder="Cole o link da nova planilha aqui..."
    )
    
    st.divider()
    
    if st.button("🚪 Sair do Sistema"):
        st.session_state["authenticated"] = False
        st.rerun()

# Corpo da página inicial
st.markdown("""
### 🚀 Painel de Gestão Cirúrgica
Utilize as ferramentas no menu lateral para processar os seus documentos.

**Ferramentas disponíveis:**
* **Extração de Mapas:** Converte PDFs de atos cirúrgicos em dados para a sua planilha.
* **Gestão de Ajudas:** Processa relatórios onde atuou como 1º ou 2º ajudante.

---
> **Dica:** Certifique-se de que a sua Planilha Google está partilhada com o e-mail da conta de serviço configurado nos Secrets.
""")

st.success("✅ Sistema pronto. Selecione uma página à esquerda para começar.")
