import streamlit as st
import google.generativeai as genai
from PIL import Image
import datetime

# --- CONFIGURAÇÃO INICIAL ---
try:
    favicon = Image.open("favicon.png")
except:
    favicon = "🏗️"

st.set_page_config(page_title="TechPost AI", page_icon=favicon, layout="wide")

# --- CSS (Estilo Profissional) ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-weight: 600;
    }
    .blurred-text {
        color: transparent;
        text-shadow: 0 0 8px rgba(0,0,0,0.5);
        user-select: none;
    }
</style>
""", unsafe_allow_html=True)

# --- VARIÁVEIS GLOBAIS ---
LINK_CHECKOUT = "https://pay.kiwify.com.br/tR0h1UK" 
MODELO_IA = "gemini-2.5-flash"

# --- ESTADO ---
if 'historico' not in st.session_state: st.session_state['historico'] = []
if 'ultimo_resultado' not in st.session_state: st.session_state['ultimo_resultado'] = ""
if 'usuario_vip' not in st.session_state: st.session_state['usuario_vip'] = False
if 'contagem_posts' not in st.session_state: st.session_state['contagem_posts'] = 0

# --- CONFIG API ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
    tem_chave = True
except:
    tem_chave = False

# --- FUNÇÕES ---
def gerar_post(arquivo, contexto, publico, objetivo, canal):
    model = genai.GenerativeModel(MODELO_IA)
    
    prompt = f"""
    Atue como Engenheiro Sênior Especialista no {canal}.
    CONTEXTO DO USUÁRIO: {contexto}
    PÚBLICO: {publico}
    OBJETIVO: {objetivo}
    
    INSTRUÇÕES:
    1. Analise o arquivo anexo (Imagem ou PDF Técnico) se houver.
    2. Crie um post com estrutura de Storytelling (Gancho -> Situação -> Solução -> Lição).
    3. Linguagem natural e humana.
    4. SEM formatação markdown (sem negrito **, sem itálico *, sem títulos #).
    5. Finalize com 3 a 5 hashtags.
    """
    
    # Prepara o conteúdo para enviar (Imagem ou PDF)
    content = [prompt]
    if arquivo:
        # Cria o objeto blob que a API entende (funciona para PDF e Imagem)
        file_data = {
            "mime_type": arquivo.type,
            "data": arquivo.getvalue()
        }
        content.append(file_data)
        
    return model.generate_content(content).text

# --- POP-UP DE VENDA ---
@st.dialog("🎁 Seu Teste Grátis Acabou!")
def mostrar_popup_venda():
    st.write("Esperamos que você goste do resultado! Esta foi sua demonstração gratuita.")
    st.write("Para continuar gerando posts ilimitados e ter acesso a todas as atualizações futuras, adquira a licença vitalícia.")
    st.markdown(f"### 🔥 Apenas R$ 29,90 (Única vez)")
    
    st.link_button("👉 DESBLOQUEAR ACESSO VITALÍCIO", LINK_CHECKOUT, type="primary")
    st.caption("Pagamento via Pix ou Cartão. Liberação imediata.")

# --- BARRA LATERAL ---
with st.sidebar:
    try: st.image("logo.png", use_container_width=True)
    except: st.header("🏗️ TechPost AI")
    
    st.markdown("---")
    
    if not st.session_state['usuario_vip']:
        posts_feitos = st.session_state['contagem_posts']
        if posts_feitos == 0: st.info("🎁 Você tem 1 Post Grátis!")
        else: st.warning("⚠️ Teste finalizado.")
        
        st.markdown("---")
        senha = st.text_input("Já tenho a senha:", type="password")
        if st.button("Entrar"):
            if "ACCESS_CODE" in st.secrets and senha == st.secrets["ACCESS_CODE"]:
                st.session_state['usuario_vip'] = True
                st.success("Acesso Liberado!")
                st.rerun()
            else:
                st.error("Senha incorreta.")
        
        st.markdown("---")
        st.link_button("Comprar Agora (R$ 29,90)", LINK_CHECKOUT, type="primary")
    else:
        st.success("✅ Membro VIP Ativo")
        if st.button("Sair"):
            st.session_state['usuario_vip'] = False
            st.rerun()

# --- ÁREA PRINCIPAL ---
st.title("Transforme seus projetos em posts profissionais!")

if not tem_chave:
    st.error("⚠️ Configure o arquivo secrets.toml")
    st.stop()

# Inputs
c1, c2, c3 = st.columns(3)
with c1: canal = st.selectbox("Canal", ["LinkedIn", "Instagram"])
with c2: publico = st.selectbox("Público", ["Engenheiros", "Executivos", "Leigos"])
with c3: objetivo = st.selectbox("Objetivo", ["Autoridade Técnica", "Venda", "Educativo"])

# Upload (AGORA ACEITA PDF)
col_upl, col_txt = st.columns([1, 2])
with col_upl:
    uploaded_file = st.file_uploader("Adicionar Imagem ou PDF", type=["jpg", "png", "pdf"])
    
    # Preview inteligente
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            st.info(f"📄 PDF Carregado:\n{uploaded_file.name}")
        else:
            st.image(uploaded_file, use_container_width=True)

with col_txt:
    contexto = st.text_area("Contexto Adicional", height=150, placeholder="Ex: Este é o relatório final de patologia da ponte...")

# Botão de Ação
if st.button("✨ GERAR POST"):
    if not contexto and not uploaded_file:
        st.warning("Adicione um arquivo ou escreva um contexto.")
    else:
        with st.spinner("Lendo arquivo e escrevendo..."):
            try:
                # Passa o arquivo direto (UploadedFile object)
                res = gerar_post(uploaded_file, contexto, publico, objetivo, canal)
                
                st.session_state['ultimo_resultado'] = res
                st.session_state['contagem_posts'] += 1
                
                if not st.session_state['usuario_vip'] and st.session_state['contagem_posts'] == 1:
                    st.session_state['mostrar_popup_agora'] = True
                
                st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")

# --- RESULTADO ---
if st.session_state['ultimo_resultado']:
    st.markdown("---")
    st.subheader("📝 Seu Post:")
    
    texto = st.session_state['ultimo_resultado']
    posts_feitos = st.session_state['contagem_posts']
    is_vip = st.session_state['usuario_vip']
    mostrar_completo = is_vip or (posts_feitos <= 1)
    
    if mostrar_completo:
        if not is_vip: st.info("💡 Este é seu post gratuito.")
        st.text_area("Editor Final", value=texto, height=400)
        st.success("Pronto para publicar!")
        
        if st.session_state.get('mostrar_popup_agora', False):
            mostrar_popup_venda()
            
    else:
        teaser = texto[:180]
        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b;">
            <p style="font-size: 18px; color: #333;">{teaser}...</p>
            <p class="blurred-text">Conteúdo oculto. Adquira a licença para ver a análise completa do PDF.</p>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2 = st.columns([2, 1])
        with c1: st.warning("🔒 Teste Finalizado.")
        with c2: st.link_button("Desbloquear (R$ 29,90)", LINK_CHECKOUT, type="primary")

