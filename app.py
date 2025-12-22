import streamlit as st
import google.generativeai as genai
from PIL import Image
from supabase import create_client, Client
import time
import hashlib

# --- CONFIGURAÇÃO INICIAL ---
try:
    favicon = Image.open("favicon.png")
except:
    favicon = "🏗️"

st.set_page_config(page_title="TechPost AI - Pro", page_icon=favicon, layout="wide")

# --- VARIÁVEIS GLOBAIS ---
MODELO_IA = "gemini-2.5-flash" 

# --- CSS (Estilo Profissional) ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-weight: 600; 
        color: white; 
    }
    div[data-testid="stForm"] {
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 20px;
    }
    /* Estilo para os botões do histórico parecerem links/itens de menu */
    div[data-testid="stSidebar"] .stButton>button {
        background-color: transparent;
        color: #dbdbdb;
        border: 1px solid rgba(255, 255, 255, 0.1);
        height: auto;
        padding: 10px;
        text-align: left;
        font-weight: 400;
    }
    div[data-testid="stSidebar"] .stButton>button:hover {
        border-color: #FF4B4B;
        color: #FF4B4B;
    }
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO COM BANCO DE DADOS (SUPABASE) ---
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ Erro ao conectar no Supabase: {e}")
        return None

supabase = init_supabase()

# --- OPÇÕES DE TOM ---
TONE_OPTIONS = {
    "Polêmico/Provocador": "Crie um texto que desafie o senso comum...",
    "Educativo/Mentor": "Adote um tom de professor experiente...",
    "Storytelling/Pessoal": "Escreva como se estivesse contando uma história pessoal...",
    "Analítico/Dados": "Seja direto, frio e focado em fatos..."
}

# --- FUNÇÕES AUXILIARES ---
def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hash(password, hashed_text):
    return make_hash(password) == hashed_text

# --- FUNÇÕES DE BD ---
def create_user(email, password):
    if not supabase: return None
    email = email.lower().strip()
    password_hash = make_hash(password)
    try:
        existing = supabase.table("users").select("*").eq("email", email).execute()
        if len(existing.data) > 0: return "exists"
        new_user = {"email": email, "password": password_hash, "credits": 3, "is_vip": False}
        data = supabase.table("users").insert(new_user).execute()
        return data.data[0]
    except: return None

def login_user(email, password):
    if not supabase: return None
    email = email.lower().strip()
    try:
        data = supabase.table("users").select("*").eq("email", email).execute()
        if len(data.data) > 0:
            user = data.data[0]
            if check_hash(password, user.get('password', '')): return user
            else: return "wrong_pass"
        else: return "not_found"
    except: return None

def descontar_credito(email):
    if not supabase: return
    user = supabase.table("users").select("credits").eq("email", email).execute()
    if user.data:
        creditos_atuais = user.data[0]['credits']
        supabase.table("users").update({"credits": creditos_atuais - 1}).eq("email", email).execute()

def registrar_post(email, plataforma, texto, titulo):
    """Salva o post e o título gerado."""
    if not supabase: return
    try:
        supabase.table("posts").insert({
            "user_email": email, 
            "platform": plataforma, 
            "content": texto,
            "title": titulo
        }).execute()
    except Exception as e:
        print(f"Erro ao salvar post: {e}")

def buscar_historico(email):
    """Busca os posts do usuário ordenados por data."""
    if not supabase: return []
    try:
        # Pega ID, Título, Plataforma, Conteúdo e Data
        data = supabase.table("posts").select("*").eq("user_email", email).order("created_at", desc=True).execute()
        return data.data
    except:
        return []

# --- POP-UP ---
@st.dialog("🎁 Seu Saldo Acabou!")
def mostrar_popup_venda():
    st.write("Você utilizou seu post gratuito!")
    st.write("Para continuar, torne-se VIP.")
    st.markdown(f"### 🔥 Apenas R$ 29,90")
    st.link_button("👉 DESBLOQUEAR AGORA", "https://pay.kiwify.com.br/tR0h1UK", type="primary")

# --- GERADOR IA ---
def gerar_post_ia(arquivo, contexto, publico, objetivo, canal, tom_key):
    model = genai.GenerativeModel(MODELO_IA)
    instrucao_tom = TONE_OPTIONS[tom_key]
    
    # Prompt ajustado para retornar Título separado do Conteúdo
    prompt = f"""
    Atue como um Especialista em {canal} e Ghostwriter Sênior.
    CONTEXTO: {contexto}
    PÚBLICO: {publico} | OBJETIVO: {objetivo} | TOM: {instrucao_tom}
    
    ---
    MISSÃO:
    Transformar o conteúdo bruto e o contexto abaixo em uma postagem de alta performance e autoridade.
    1. Crie um TÍTULO curto e atrativo para o histórico (máx 4 palavras).
    2. Crie o POST completo seguindo as regras de viralização.
    
    ---
    REGRAS DE ESCRITA (OBRIGATÓRIO):
    1. INÍCIO (HOOK): A primeira frase deve ser um gancho magnético, mas profissional.
    2. CORPO (FLUIDEZ): Estruture o texto em parágrafos normais e coesos (2 a 4 frases por parágrafo). EVITE o estilo "uma frase por linha".
    3. ESTILO: Seja autêntico. Evite clichês corporativos.
    4. FORMATO (TEXTO LIMPO): NÃO use absolutamente nenhuma formatação de markdown (*, #). Entregue apenas o texto puro.
    5. FINAL: Termine com uma pergunta (Call to Action) e 3-5 hashtags.

    ---
    FORMATO DE RESPOSTA OBRIGATÓRIO (Use exatamente estes separadores):
    
    TITULO_GERADO: [Escreva o título aqui]
    CONTEUDO_GERADO:
    [Escreva o post aqui, com gancho, corpo fluido, sem markdown e com hashtags]
    """
    
    content = [prompt]
    if arquivo:
        content.append({"mime_type": arquivo.type, "data": arquivo.getvalue()})
        
    raw_text = model.generate_content(content).text
    
    # Processamento para separar Título do Texto
    titulo = "Novo Post"
    texto_final = raw_text
    
    if "TITULO_GERADO:" in raw_text and "CONTEUDO_GERADO:" in raw_text:
        partes = raw_text.split("CONTEUDO_GERADO:")
        cabecalho = partes[0]
        texto_final = partes[1].strip()
        
        # Extrai o título limpo
        titulo = cabecalho.replace("TITULO_GERADO:", "").strip().replace("*", "")
    
    return titulo, texto_final

# --- STATE ---
if 'user' not in st.session_state: st.session_state['user'] = None
if 'view_mode' not in st.session_state: st.session_state['view_mode'] = 'criar' # 'criar' ou 'ver'
if 'post_visualizado' not in st.session_state: st.session_state['post_visualizado'] = None
if 'popup_ativo' not in st.session_state: st.session_state['popup_ativo'] = False

# =========================================================
# TELA 1: LOGIN / CADASTRO
# =========================================================
if not st.session_state['user']:
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        try: st.image("logo.png", width=200) 
        except: st.title("🚀 TechPost AI")
        st.info("💡 Acesse para gerar seu Post Gratuito")

        tab_login, tab_signup = st.tabs(["Entrar", "Criar Conta"])

        with tab_login:
            with st.form("login_form"):
                email_login = st.text_input("E-mail:")
                pass_login = st.text_input("Senha:", type="password")
                if st.form_submit_button("Entrar"):
                    if not email_login or not pass_login:
                        st.warning("Preencha tudo.")
                    else:
                        with st.spinner("Entrando..."):
                            resp = login_user(email_login, pass_login)
                            if isinstance(resp, dict):
                                st.session_state['user'] = resp
                                st.rerun()
                            else:
                                st.error("Erro no login. Verifique seus dados.")

        with tab_signup:
            with st.form("signup_form"):
                email_new = st.text_input("E-mail:")
                pass_new = st.text_input("Senha:", type="password")
                pass_conf = st.text_input("Confirmar Senha:", type="password")
                if st.form_submit_button("Criar Conta"):
                    if pass_new != pass_conf: st.error("Senhas não batem.")
                    else:
                        with st.spinner("Criando..."):
                            resp = create_user(email_new, pass_new)
                            if isinstance(resp, dict):
                                st.session_state['user'] = resp
                                st.success("Criado!")
                                time.sleep(1)
                                st.rerun()
                            elif resp == "exists":
                                st.error("E-mail já existe.")

# =========================================================
# TELA 2: APLICAÇÃO (LOGADO)
# =========================================================
else:
    user = st.session_state['user']
    creditos = user.get('credits', 0)
    is_vip = user.get('is_vip', False)
    pode_gerar = is_vip or (creditos > 0)
    
    # --- SIDEBAR (HISTÓRICO) ---
    with st.sidebar:
        try: st.image("logo.png", use_container_width=True)
        except: st.header("🏗️ TechPost")
        
        st.caption(f"Logado como: {user['email']}")
        
        # Botão para Novo Post
        if st.button("➕ NOVO POST", type="primary"):
            st.session_state['view_mode'] = 'criar'
            st.session_state['post_visualizado'] = None
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 🕒 Histórico")
        
        # Busca histórico do banco
        historico = buscar_historico(user['email'])
        
        if not historico:
            st.caption("Nenhum post ainda.")
        else:
            # Lista os posts como botões
            for post in historico:
                # Usa o título do banco ou um fallback se estiver vazio
                label = post.get('title') or f"Post {post['id']}"
                if st.button(f" {label}", key=f"hist_{post['id']}"):
                    st.session_state['view_mode'] = 'ver'
                    st.session_state['post_visualizado'] = post
                    st.rerun()

        st.markdown("---")
        if not is_vip:
            st.info(f"Créditos: {creditos}")
            if creditos == 0 and st.button("Adquirir Posts Ilimitados"):
                st.session_state['popup_ativo'] = True
                st.rerun()
                
        if st.button("Sair"):
            st.session_state['user'] = None
            st.rerun()

    # --- MAIN CONTENT ---
    
    # MODO 1: VISUALIZAR POST ANTIGO
    if st.session_state['view_mode'] == 'ver' and st.session_state['post_visualizado']:
        post = st.session_state['post_visualizado']
        st.title(post.get('title', 'Detalhes do Post'))
        st.caption(f"Gerado em: {post.get('created_at', '')[:10]} | Plataforma: {post.get('platform', 'N/A')}")
        
        st.markdown("### 📝 Conteúdo:")
        st.text_area("Copie seu texto:", value=post.get('content', ''), height=400)
        
        if st.button("⬅️ Voltar para Criador"):
            st.session_state['view_mode'] = 'criar'
            st.rerun()

    # MODO 2: CRIAR NOVO POST (FORMULÁRIO)
    else:
        st.title("Crie posts a partir de seus cases")
        
        if not supabase: st.error("Erro BD.")
        try: genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
        except: pass

        with st.form("app_form"):
            c1, c2, c3, c4 = st.columns(4)
            with c1: canal = st.selectbox("Canal", ["LinkedIn", "Instagram"])
            with c2: publico = st.selectbox("Público", ["Engenheiros", "Executivos", "Leigos"])
            with c3: objetivo = st.selectbox("Objetivo", ["Autoridade", "Venda", "Educativo"])
            with c4: tom = st.selectbox("Tom", list(TONE_OPTIONS.keys()))

            c_up, c_txt = st.columns([1,2])
            with c_up: arquivo = st.file_uploader("Anexar", type=["pdf","png","jpg"])
            with c_txt: contexto = st.text_area("Contexto:", height=100)
            
            btn_txt = "GERAR POST" if pode_gerar else "🔒 SALDO INSUFICIENTE"
            submitted = st.form_submit_button(btn_txt)

        if submitted:
            if not pode_gerar:
                st.session_state['popup_ativo'] = True
                st.rerun()
            elif not contexto and not arquivo:
                st.warning("Preencha algo.")
            else:
                with st.spinner("IA Trabalhando..."):
                    try:
                        # 1. Gera Título + Texto
                        titulo_gerado, texto_gerado = gerar_post_ia(arquivo, contexto, publico, objetivo, canal, tom)
                        
                        # 2. Desconta
                        if not is_vip:
                            descontar_credito(user['email'])
                            st.session_state['user']['credits'] -= 1
                            if st.session_state['user']['credits'] == 0:
                                st.session_state['popup_ativo'] = True

                        # 3. Salva no BD com Título
                        registrar_post(user['email'], canal, texto_gerado, titulo_gerado)
                        
                        # 4. Mostra resultado (já muda o modo para ver o post recém criado)
                        # Buscamos o post mais recente para exibir com o formato correto de 'post_visualizado'
                        # ou simplesmente criamos um objeto temporário
                        st.session_state['post_visualizado'] = {
                            'title': titulo_gerado,
                            'content': texto_gerado,
                            'platform': canal,
                            'created_at': 'Agora'
                        }
                        st.session_state['view_mode'] = 'ver'
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro: {e}")

    # POPUP
    if st.session_state.get('popup_ativo'):
        mostrar_popup_venda()
        st.session_state['popup_ativo'] = False

