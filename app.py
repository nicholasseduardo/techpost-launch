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
    /* Estilo do Texto Bloqueado (Blur) */
    .blurred-text {
        color: transparent;
        text-shadow: 0 0 8px rgba(0,0,0,0.5);
        user-select: none;
    }
</style>
""", unsafe_allow_html=True)

# --- VARIÁVEIS GLOBAIS ---
LINK_CHECKOUT = "https://pay.kiwify.com.br/tR0h1UK" 
MODELO_IA = "gemini-2.5-flash" # Atualizado conforme seu teste!

# --- ESTADO (SESSION STATE) ---
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
def gerar_post(imagem, contexto, publico, objetivo, canal):
    model = genai.GenerativeModel(MODELO_IA)
    prompt = f"""
    Atue como Engenheiro Sênior Especialista no {canal}.
    CONTEXTO: {contexto}
    PÚBLICO: {publico}
    OBJETIVO: {objetivo}
    
    DIRETRIZES DE ESCRITA:
    1. Estrutura de Storytelling (Gancho -> Situação -> Solução -> Lição).
    2. Linguagem natural e humana.
    3. SEM formatação markdown (sem negrito **, sem itálico *, sem títulos #).
    4. Use parágrafos curtos.
    5. Finalize com 3 a 5 hashtags estratégicas.
    """
    content = [prompt, imagem] if imagem else [prompt]
    return model.generate_content(content).text

# --- POP-UP DE VENDA (NOVO!) ---
@st.dialog("🎁 Seu Teste Grátis Acabou!")
def mostrar_popup_venda():
    st.write("Esperamos que você goste do resultado! Esta foi sua demonstração gratuita.")
    st.write("Para continuar gerando posts ilimitados e ter acesso a todas as atualizações futuras, adquira a licença vitalícia.")
    st.markdown(f"### 🔥 Apenas R$ 29,90 (Única vez)")
    
    st.link_button("👉 DESBLOQUEAR ACESSO VITALÍCIO", LINK_CHECKOUT, type="primary")
    st.caption("Pagamento via Pix ou Cartão. Liberação imediata.")

# --- BARRA LATERAL (LOGIN & VENDA) ---
with st.sidebar:
    try: st.image("logo.png", use_container_width=True)
    except: st.header("🏗️ TechPost AI")
    
    st.markdown("---")
    
    if not st.session_state['usuario_vip']:
        posts_feitos = st.session_state['contagem_posts']
        
        if posts_feitos == 0:
            st.info("🎁 Você tem 1 Post Grátis!")
        elif posts_feitos >= 1:
            st.warning("⚠️ Teste finalizado.")

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
st.title("Crie posts profissionais a partir de suas histórias!")

if not tem_chave:
    st.error("⚠️ Configure o arquivo secrets.toml com a chave GOOGLE_API_KEY")
    st.stop()

# Inputs
c1, c2, c3 = st.columns(3)
with c1: canal = st.selectbox("Canal", ["LinkedIn", "Instagram"])
with c2: publico = st.selectbox("Público", ["Engenheiros", "Executivos", "Leigos"])
with c3: objetivo = st.selectbox("Objetivo", ["Autoridade Técnica", "Venda de Serviço", "Educativo"])

# Upload e Contexto
col_upl, col_txt = st.columns([1, 2])
with col_upl:
    uploaded_file = st.file_uploader("Imagem (Opcional)", type=["jpg", "png"])
    img = Image.open(uploaded_file) if uploaded_file else None
    if img: st.image(img, use_container_width=True)

with col_txt:
    contexto = st.text_area("O que aconteceu? (Contexto)", height=150, placeholder="Ex: Visitamos a obra do Hospital e identificamos uma falha na impermeabilização...")

# Botão de Ação
if st.button("✨ GERAR RASCUNHO"):
    if not contexto:
        st.warning("Por favor, escreva o contexto para a IA trabalhar.")
    else:
        with st.spinner("Analisando imagem e escrevendo..."):
            try:
                res = gerar_post(img, contexto, publico, objetivo, canal)
                
                st.session_state['ultimo_resultado'] = res
                st.session_state['contagem_posts'] += 1
                
                # Se for o primeiro post e não for VIP, vai abrir o popup no refresh
                # Mas precisamos forçar o popup aparecer AGORA.
                # O st.rerun vai recarregar a página e a lógica lá embaixo vai cuidar disso?
                # O ideal é salvar uma flag "mostrar_popup"
                if not st.session_state['usuario_vip'] and st.session_state['contagem_posts'] == 1:
                    st.session_state['mostrar_popup_agora'] = True
                
                st.rerun()
            except Exception as e:
                st.error(f"Erro na IA: {e}")

# --- RESULTADO E POPUP ---
if st.session_state['ultimo_resultado']:
    st.markdown("---")
    st.subheader("📝 Seu Post:")
    
    texto = st.session_state['ultimo_resultado']
    posts_feitos = st.session_state['contagem_posts']
    is_vip = st.session_state['usuario_vip']
    
    mostrar_completo = is_vip or (posts_feitos <= 1)
    
    if mostrar_completo:
        if not is_vip:
            st.info("💡 Este é seu post gratuito. Copie agora!")
            
        st.text_area("Editor Final", value=texto, height=400)
        st.success("Pronto para publicar! Copie o texto acima.")
        
        # CHECAGEM DO POPUP: Se a flag estiver True, mostra o modal
        if st.session_state.get('mostrar_popup_agora', False):
            mostrar_popup_venda()
            # Importante: Não limpamos a flag imediatamente dentro do fluxo
            # senão o popup fecha se a pessoa clicar fora. Deixamos ele ativo
            # até a pessoa interagir ou recarregar. 
            # (Ou podemos limpar na próxima interação).
            
    else:
        # Paywall (Blur)
        teaser = texto[:180]
        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b;">
            <p style="font-size: 18px; color: #333;">{teaser}...</p>
            <p class="blurred-text">O restante do conteúdo técnico gerado pela IA que vai te economizar horas de trabalho está oculto.</p>
        </div>
        """, unsafe_allow_html=True)
        
        c_lock1, c_lock2 = st.columns([2, 1])
        with c_lock1:
            st.warning("🔒 Teste Grátis Finalizado.")
        with c_lock2:
            st.link_button("Desbloquear Agora (R$ 29,90)", LINK_CHECKOUT, type="primary")