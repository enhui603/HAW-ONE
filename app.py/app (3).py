import base64
import json
import os
import uuid
from datetime import date, datetime

import pandas as pd
import streamlit as st

st.set_page_config(page_title="HAW-ONE", page_icon="🦁", layout="wide")

# =====================================================================
# SETTINGS
# =====================================================================
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
DATA = os.path.join(HERE, "data")
UPLOADS = os.path.join(DATA, "uploads")
os.makedirs(UPLOADS, exist_ok=True)

POSTS_FILE = os.path.join(DATA, "posts.json")
LEDGER_FILE = os.path.join(DATA, "ledger.csv")

NEA_URL = "https://www.nea.gov.sg/our-services/hawker-management/becoming-a-hawker"

# Mascot palette
BLUE = "#5B9BD5"   # Haw Bo   -> Seller
PINK = "#E8587A"   # Haw Sim  -> Visitor
INK = "#3B2A33"
CREAM = "#FFF8F0"

# DEMO registry of participating stalls (UEN -> stall).
# These are made-up examples. Replace with your real list / database later.
STALLS = {
    "53000001A": {"name": "Ah Seng Chicken Rice", "centre": "Maxwell Food Centre"},
    "53000002B": {"name": "Mdm Lim Laksa", "centre": "Tiong Bahru Market"},
    "53000003C": {"name": "Uncle Raj Prata", "centre": "Old Airport Road Food Centre"},
    "53000004D": {"name": "Sunrise Satay", "centre": "Lau Pa Sat"},
}

LEDGER_COLS = ["uen", "id", "date", "type", "amount", "description"]

# =====================================================================
# STYLE
# =====================================================================
def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


bg = b64(os.path.join(ASSETS, "background.jpg"))

st.markdown(
    f"""
    <style>
    [data-testid="stHeader"] {{ background: transparent; }}
    .stApp {{ background: url(data:image/jpeg;base64,{bg}) center / cover fixed; }}
    .block-container {{
        max-width: 1000px; margin-top: 2rem; padding: 2rem 2.5rem 2.5rem;
        background: {CREAM}; border: 4px solid {INK}; border-radius: 32px;
        box-shadow: 10px 10px 0 {INK};
    }}
    .title {{ text-align:center; font-size:4rem; font-weight:900; letter-spacing:4px;
             color:{INK}; margin:0; line-height:1.1; }}
    .title span {{ color:{PINK}; }}
    .tagline {{ text-align:center; font-size:1.25rem; color:{INK}; margin:.3rem 0 1.5rem; }}
    .role-name {{ text-align:center; font-size:1.6rem; font-weight:800; color:{INK}; margin:0; }}
    .role-desc {{ text-align:center; color:{INK}; opacity:.75; margin:0 0 .6rem; }}
    .page-title {{ font-size:2rem; font-weight:900; color:{INK}; margin:0; }}
    .page-sub {{ color:{INK}; opacity:.75; margin:0 0 1rem; }}

    /* role / menu cards */
    [class*="st-key-card_blue"], [class*="st-key-card_pink"] {{
        border: 3px solid {INK}; border-radius: 24px; padding: 1rem; margin-bottom: .6rem;
    }}
    [class*="st-key-card_blue"] {{ background: #EAF3FC; }}
    [class*="st-key-card_pink"] {{ background: #FDEBF0; }}

    /* buttons: keys starting with b_ are blue, p_ are pink */
    [class*="st-key-b_"] button, [class*="st-key-p_"] button,
    [data-testid="stLinkButton"] a {{
        color: white !important; font-weight: 800; border: 3px solid {INK};
        border-radius: 999px; box-shadow: 3px 3px 0 {INK};
    }}
    [class*="st-key-b_"] button {{ background: {BLUE}; }}
    [class*="st-key-p_"] button {{ background: {PINK}; }}
    [data-testid="stLinkButton"] a {{ background: {BLUE}; }}
    [class*="st-key-b_"] button:hover, [class*="st-key-p_"] button:hover,
    [data-testid="stLinkButton"] a:hover {{ filter: brightness(1.08); color: white; border-color: {INK}; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =====================================================================
# STATE + NAVIGATION
# =====================================================================
st.session_state.setdefault("view", "landing")
st.session_state.setdefault("seller_uen", None)
st.session_state.setdefault("subs", [])      # visitor's subscribed stall UENs


def go(view):
    st.session_state.view = view


def logout():
    st.session_state.seller_uen = None
    st.session_state.view = "seller_home"


def page_header(title, subtitle, mascot, back_to, back_label="← Back"):
    st.button(back_label, key=f"{'b' if mascot == 'haw_bo' else 'p'}_back_{title}",
              on_click=go, args=(back_to,))
    c1, c2 = st.columns([1, 6], vertical_alignment="center")
    c1.image(os.path.join(ASSETS, f"{mascot}.png"), width=110)
    c2.markdown(f"<p class='page-title'>{title}</p><p class='page-sub'>{subtitle}</p>",
                unsafe_allow_html=True)


def menu_card(color, key, emoji, title, desc, button_label, on_click=None, args=(), link=None):
    """A card with a title, description and one button."""
    prefix = "b" if color == "blue" else "p"
    with st.container(key=f"card_{color}_{key}"):
        st.markdown(f"<p class='role-name'>{emoji} {title}</p>", unsafe_allow_html=True)
        st.markdown(f"<p class='role-desc'>{desc}</p>", unsafe_allow_html=True)
        if link:
            st.link_button(button_label, link, use_container_width=True)
        else:
            st.button(button_label, key=f"{prefix}_{key}", use_container_width=True,
                      on_click=on_click, args=args)


# =====================================================================
# DATA HELPERS
# =====================================================================
def load_posts():
    if os.path.exists(POSTS_FILE):
        try:
            with open(POSTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_posts(posts):
    with open(POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2)


def load_ledger():
    if os.path.exists(LEDGER_FILE):
        return pd.read_csv(LEDGER_FILE, dtype={"uen": str, "id": str})
    return pd.DataFrame(columns=LEDGER_COLS)


def save_ledger(df):
    df.to_csv(LEDGER_FILE, index=False)


def fmt_date(iso):
    return datetime.fromisoformat(iso).strftime("%d %b %Y")


def toggle_sub(uen):
    subs = st.session_state.subs
    if uen in subs:
        subs.remove(uen)
    else:
        subs.append(uen)


def delete_post(post_id):
    posts = load_posts()
    for p in posts:
        if p["id"] == post_id:
            for img in p.get("images", []):
                try:
                    os.remove(os.path.join(UPLOADS, img))
                except OSError:
                    pass
    save_posts([p for p in posts if p["id"] != post_id])


def render_post(p, key_prefix, show_subscribe=False, owner_uen=None):
    """One broadcast post card."""
    with st.container(border=True):
        left, right = st.columns([3, 1.2], vertical_alignment="center")
        left.markdown(f"**{p['stall']}** · {p['centre']}")
        left.caption(datetime.fromisoformat(p["time"]).strftime("%d %b %Y, %I:%M %p"))

        if show_subscribe:
            subscribed = p["uen"] in st.session_state.subs
            right.button("⭐ Subscribed" if subscribed else "☆ Subscribe",
                         key=f"p_sub_{key_prefix}_{p['id']}",
                         on_click=toggle_sub, args=(p["uen"],), use_container_width=True)
        if owner_uen and owner_uen == p["uen"]:
            right.button("🗑️ Delete", key=f"b_del_{key_prefix}_{p['id']}",
                         on_click=delete_post, args=(p["id"],), use_container_width=True)

        if p.get("caption"):
            st.write(p["caption"])

        imgs = [os.path.join(UPLOADS, i) for i in p.get("images", [])
                if os.path.exists(os.path.join(UPLOADS, i))]
        if imgs:
            cols = st.columns(min(len(imgs), 3))
            for col, path in zip(cols, imgs[:3]):
                col.image(path, use_container_width=True)

        if p.get("closure_start"):
            st.warning(f"🔒 Closed from {fmt_date(p['closure_start'])} to {fmt_date(p['closure_end'])}")


# =====================================================================
# PAGE 1: LANDING
# =====================================================================
def landing():
    st.markdown("<p class='title'>HAW<span>-</span>ONE</p>", unsafe_allow_html=True)
    st.markdown("<p class='tagline'>Who are you today?</p>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        with st.container(key="card_blue_seller"):
            st.image(os.path.join(ASSETS, "haw_bo.png"), width=230)
            st.markdown("<p class='role-name'>🧑‍🍳 Seller</p>", unsafe_allow_html=True)
            st.markdown("<p class='role-desc'>Stall owner? Bid for a stall or manage yours.</p>",
                        unsafe_allow_html=True)
            st.button("I'm a Seller", key="b_seller", use_container_width=True,
                      on_click=go, args=("seller_home",))
    with c2:
        with st.container(key="card_pink_visitor"):
            st.image(os.path.join(ASSETS, "haw_sim.png"), width=230)
            st.markdown("<p class='role-name'>🚶 Visitor</p>", unsafe_allow_html=True)
            st.markdown("<p class='role-desc'>Hungry? Follow your favourite stalls.</p>",
                        unsafe_allow_html=True)
            st.button("I'm a Visitor", key="p_visitor", use_container_width=True,
                      on_click=go, args=("visitor_home",))


# =====================================================================
# PAGE 2: SELLER
# =====================================================================
def seller_home():
    page_header("Seller", "What would you like to do?", "haw_bo", "landing", "← Home")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        menu_card("blue", "bid", "📝", "Bid for Stall",
                  "Opens the NEA page on becoming a hawker.", "Go to NEA ↗", link=NEA_URL)
    with c2:
        menu_card("blue", "login", "🔑", "Seller Login",
                  "Enter your business UEN to use the seller tools.", "Seller Login",
                  on_click=go, args=("seller_login",))


def seller_login():
    page_header("Seller Login", "Enter your business UEN / secret code.", "haw_bo", "seller_home")
    with st.form("login_form"):
        code = st.text_input("Business UEN / secret code", type="password")
        ok = st.form_submit_button("Log in", type="primary")
    if ok:
        code = code.strip().upper()
        if code in STALLS:
            st.session_state.seller_uen = code
            st.session_state.view = "seller_admin"
            st.rerun()
        else:
            st.error("We couldn't find that UEN. Please check and try again.")
    st.caption("Demo UENs to try: " + ", ".join(STALLS.keys()))


def seller_admin():
    uen = st.session_state.seller_uen
    if uen not in STALLS:
        st.session_state.view = "seller_login"
        st.rerun()
    stall = STALLS[uen]

    page_header(stall["name"], f"{stall['centre']} · Seller admin", "haw_bo",
                "seller_home", "← Back")
    st.button("Log out", key="b_logout", on_click=logout)

    tab_bc, tab_calc = st.tabs(["📣 Community Broadcast", "🧮 Hawker Calculator"])
    with tab_bc:
        seller_broadcast(uen, stall)
    with tab_calc:
        seller_calculator(uen)


def seller_broadcast(uen, stall):
    st.subheader("Post to the Community Broadcast")
    st.caption("Visitors who subscribe to your stall will see this on their page.")
    with st.form("post_form", clear_on_submit=True):
        caption = st.text_area("What's cooking today?", placeholder="Describe your delicacy…")
        photos = st.file_uploader("Photos of your delicacies", type=["png", "jpg", "jpeg"],
                                  accept_multiple_files=True)
        closing = st.checkbox("Include a closure notice")
        dates = st.date_input("Closure dates (from → to)", value=(date.today(), date.today()))
        submitted = st.form_submit_button("📣 Post", type="primary")

    if submitted:
        has_range = isinstance(dates, (tuple, list)) and len(dates) == 2
        if not caption.strip() and not photos and not closing:
            st.error("Add a description, a photo or a closure notice first.")
        elif closing and not has_range:
            st.error("Please pick both a start and an end date for the closure.")
        else:
            saved = []
            for up in photos or []:
                ext = os.path.splitext(up.name)[1].lower() or ".jpg"
                name = f"{uuid.uuid4().hex}{ext}"
                with open(os.path.join(UPLOADS, name), "wb") as f:
                    f.write(up.getbuffer())
                saved.append(name)
            post = {
                "id": uuid.uuid4().hex[:10],
                "uen": uen,
                "stall": stall["name"],
                "centre": stall["centre"],
                "time": datetime.now().isoformat(timespec="seconds"),
                "caption": caption.strip(),
                "images": saved,
                "closure_start": dates[0].isoformat() if closing else None,
                "closure_end": dates[1].isoformat() if closing else None,
            }
            posts = load_posts()
            posts.insert(0, post)
            save_posts(posts)
            st.success("Posted!")

    st.divider()
    st.subheader("Public broadcast")
    posts = load_posts()
    if not posts:
        st.info("No posts yet. Be the first!")
    for p in posts:
        render_post(p, "seller", owner_uen=uen)


def seller_calculator(uen):
    st.subheader("Add an entry")
    with st.form("ledger_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([1.3, 1.2, 1, 2])
        d = c1.date_input("Date", value=date.today())
        t = c2.selectbox("Type", ["Earning", "Expense"])
        amt = c3.number_input("Amt (S$)", min_value=0.0, step=0.5, format="%.2f")
        desc = c4.text_input("Description", placeholder="e.g. Chicken supplier")
        added = st.form_submit_button("➕ Add entry", type="primary")

    if added:
        if amt <= 0:
            st.error("Please enter an amount above 0.")
        else:
            df = load_ledger()
            row = {"uen": uen, "id": uuid.uuid4().hex[:8], "date": d.isoformat(),
                   "type": t, "amount": float(amt), "description": desc.strip()}
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            save_ledger(df)
            st.success("Entry saved.")

    st.divider()
    st.subheader("Your numbers")
    df = load_ledger()
    mine = df[df["uen"] == uen].copy()
    mine["date"] = pd.to_datetime(mine["date"])
    mine["amount"] = mine["amount"].astype(float)

    view = st.radio("View", ["Daily", "Monthly", "Yearly"], horizontal=True)
    today = date.today()
    years = sorted(set(mine["date"].dt.year.tolist()) | {today.year})

    if view == "Daily":
        day = st.date_input("Pick a day", value=today, key="calc_day")
        sel = mine[mine["date"].dt.date == day]
        group = None
    elif view == "Monthly":
        a, b = st.columns(2)
        y = a.selectbox("Year", years, index=years.index(today.year), key="calc_m_year")
        m = b.selectbox("Month", list(range(1, 13)), index=today.month - 1,
                        format_func=lambda x: datetime(2000, x, 1).strftime("%B"), key="calc_month")
        sel = mine[(mine["date"].dt.year == y) & (mine["date"].dt.month == m)]
        group = sel["date"].dt.day
    else:
        y = st.selectbox("Year", years, index=years.index(today.year), key="calc_y_year")
        sel = mine[mine["date"].dt.year == y]
        group = sel["date"].dt.month

    earn = sel.loc[sel["type"] == "Earning", "amount"].sum()
    exp = sel.loc[sel["type"] == "Expense", "amount"].sum()
    net = earn - exp
    m1, m2, m3 = st.columns(3)
    m1.metric("Earnings", f"S${earn:,.2f}")
    m2.metric("Expenses", f"S${exp:,.2f}")
    m3.metric("Net profit", f"S${net:,.2f}")

    if sel.empty:
        st.info("No entries for this period yet.")
        return

    if group is not None:
        chart = (sel.assign(period=group).groupby(["period", "type"])["amount"].sum()
                 .unstack(fill_value=0).reindex(columns=["Earning", "Expense"], fill_value=0))
        st.bar_chart(chart)

    show = sel.sort_values("date").copy()
    show["date"] = show["date"].dt.strftime("%d %b %Y")
    st.dataframe(show[["date", "type", "amount", "description"]], hide_index=True,
                 use_container_width=True)

    with st.expander("🗑️ Delete an entry"):
        labels = {r["id"]: f"{r['date'].strftime('%d %b')} · {r['type']} · S${r['amount']:.2f} · {r['description']}"
                  for _, r in sel.sort_values("date").iterrows()}
        pick = st.selectbox("Choose entry", list(labels.keys()), format_func=lambda k: labels[k])
        if st.button("Delete selected entry", key="b_del_entry"):
            df = load_ledger()
            save_ledger(df[df["id"] != pick])
            st.rerun()


# =====================================================================
# PAGE 2: VISITOR
# =====================================================================
def visitor_home():
    page_header("Visitor", "What are you looking for today?", "haw_sim", "landing", "← Home")
    items = [
        ("fav", "⭐", "My Favourite Hawker Stalls", "Follow stalls and see their latest posts.", "v_fav"),
        ("sched", "🗓️", "Hawker Schedule", "Cleaning and closure dates.", "v_sched"),
        ("near", "📍", "Nearby Hawker", "Find hawker centres around you.", "v_near"),
        ("queue", "⏱️", "Queue Tracker", "To be explored.", "v_queue"),
        ("news", "📰", "Hawkers News & Social Feed", "News and updates from the hawker scene.", "v_news"),
    ]
    for i in range(0, len(items), 2):
        cols = st.columns(2, gap="large")
        for col, (key, emoji, title, desc, target) in zip(cols, items[i:i + 2]):
            with col:
                menu_card("pink", key, emoji, title, desc, "Open", on_click=go, args=(target,))


def visitor_favourites():
    page_header("My Favourite Hawker Stalls", "Subscribe to stalls to pin them to the top.",
                "haw_sim", "visitor_home")
    subs = st.session_state.subs

    st.markdown("#### ⭐ Your favourites")
    if subs:
        st.write("  ".join(f"`{STALLS[u]['name']}`" for u in subs if u in STALLS))
    else:
        st.caption("No favourites yet. Tap **Subscribe** on any stall below.")

    posts = load_posts()
    if not posts:
        st.info("No broadcasts yet. Check back soon!")
        return

    fav_posts = [p for p in posts if p["uen"] in subs]
    other_posts = [p for p in posts if p["uen"] not in subs]

    if fav_posts:
        st.markdown("#### From your favourite stalls")
        for p in fav_posts:
            render_post(p, "fav", show_subscribe=True)
    if other_posts:
        st.markdown("#### Discover more stalls")
        for p in other_posts:
            render_post(p, "other", show_subscribe=True)


def visitor_schedule():
    page_header("Hawker Schedule", "Cleaning and closure dates.", "haw_sim", "visitor_home")
    t1, t2 = st.tabs(["🧹 Cleaning", "🔒 Closure"])
    with t1:
        st.info("Cleaning schedule data coming soon.")
    with t2:
        st.info("Closure schedule data coming soon.")


def coming_soon(title, subtitle, note):
    page_header(title, subtitle, "haw_sim", "visitor_home")
    st.info(note)


# =====================================================================
# ROUTER
# =====================================================================
view = st.session_state.view
if view == "landing":
    landing()
elif view == "seller_home":
    seller_home()
elif view == "seller_login":
    seller_login()
elif view == "seller_admin":
    seller_admin()
elif view == "visitor_home":
    visitor_home()
elif view == "v_fav":
    visitor_favourites()
elif view == "v_sched":
    visitor_schedule()
elif view == "v_near":
    coming_soon("Nearby Hawker", "Find hawker centres around you.", "Coming soon.")
elif view == "v_queue":
    coming_soon("Queue Tracker", "See how long the queue is.", "Still being explored.")
elif view == "v_news":
    coming_soon("Hawkers News & Social Feed", "News and updates.", "Coming soon.")
else:
    go("landing")
    st.rerun()
