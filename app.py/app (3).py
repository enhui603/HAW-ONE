import base64
import os
import streamlit as st

st.set_page_config(page_title="HAW-ONE", page_icon="🦁", layout="wide")

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")

# Mascot palette
BLUE = "#5B9BD5"     # Haw Bo
PINK = "#E8587A"     # Haw Sim
INK = "#3B2A33"      # mascot outline colour
CREAM = "#FFF8F0"


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


bg = b64(os.path.join(ASSETS, "background.jpg"))

st.markdown(
    f"""
    <style>
    [data-testid="stHeader"] {{ background: transparent; }}
    .stApp {{
        background: url(data:image/jpeg;base64,{bg}) center / cover fixed;
    }}
    /* main white panel */
    .block-container {{
        max-width: 1000px;
        margin-top: 2rem;
        padding: 2rem 2.5rem 2.5rem;
        background: {CREAM};
        border: 4px solid {INK};
        border-radius: 32px;
        box-shadow: 10px 10px 0 {INK};
    }}
    .title {{ text-align:center; font-size:4rem; font-weight:900; letter-spacing:4px;
             color:{INK}; margin:0; line-height:1.1; }}
    .title span {{ color:{PINK}; }}
    .tagline {{ text-align:center; font-size:1.25rem; color:{INK}; margin:.3rem 0 1.5rem; }}
    .role-name {{ text-align:center; font-size:1.6rem; font-weight:800; color:{INK}; margin:0; }}
    .role-desc {{ text-align:center; color:{INK}; opacity:.75; margin:0 0 .6rem; }}
    /* role cards */
    .st-key-seller_card, .st-key-visitor_card {{
        border: 3px solid {INK}; border-radius: 24px; padding: 1rem;
    }}
    .st-key-seller_card {{ background: #EAF3FC; }}
    .st-key-visitor_card {{ background: #FDEBF0; }}
    .st-key-seller_btn button, .st-key-visitor_btn button {{
        color: white; font-weight: 800; border: 3px solid {INK}; border-radius: 999px;
        box-shadow: 3px 3px 0 {INK};
    }}
    .st-key-seller_btn button {{ background: {BLUE}; }}
    .st-key-visitor_btn button {{ background: {PINK}; }}
    .st-key-seller_btn button:hover, .st-key-visitor_btn button:hover {{
        color: white; filter: brightness(1.08); border-color: {INK};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

if "role" not in st.session_state:
    st.session_state.role = None


def set_role(role):
    st.session_state.role = role


def go_home():
    st.session_state.role = None


# ---------- Placeholder pages: paste your real dashboard code here ----------
def seller_page():
    st.header("Seller dashboard")
    st.info("Seller pages go here.")


def visitor_page():
    st.header("Visitor dashboard")
    st.info("Visitor pages go here.")


# ---------- First page ----------
def landing():
    st.markdown("<p class='title'>HAW<span>-</span>ONE</p>", unsafe_allow_html=True)
    st.markdown("<p class='tagline'>Who are you today?</p>", unsafe_allow_html=True)

    c1, c2 = st.columns(2, gap="large")

    with c1:
        with st.container(key="seller_card"):
            st.image(os.path.join(ASSETS, "haw_bo.png"), width=230)
            st.markdown("<p class='role-name'>🧑‍🍳 Seller</p>", unsafe_allow_html=True)
            st.markdown("<p class='role-desc'>Stall owner? Check insights and plan maintenance.</p>",
                        unsafe_allow_html=True)
            st.button("I'm a Seller", key="seller_btn", use_container_width=True,
                      on_click=set_role, args=("Seller",))

    with c2:
        with st.container(key="visitor_card"):
            st.image(os.path.join(ASSETS, "haw_sim.png"), width=230)
            st.markdown("<p class='role-name'>🚶 Visitor</p>", unsafe_allow_html=True)
            st.markdown("<p class='role-desc'>Hungry? Discover hawker centres and stalls.</p>",
                        unsafe_allow_html=True)
            st.button("I'm a Visitor", key="visitor_btn", use_container_width=True,
                      on_click=set_role, args=("Visitor",))


# ---------- Router ----------
if st.session_state.role is None:
    landing()
else:
    with st.sidebar:
        st.title("HAW-ONE")
        st.write(f"Viewing as: **{st.session_state.role}**")
        st.button("🔄 Switch role", on_click=go_home, use_container_width=True)
    seller_page() if st.session_state.role == "Seller" else visitor_page()
