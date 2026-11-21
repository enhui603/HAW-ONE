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
# LANGUAGES  (English default, then Chinese, Malay, Tamil)
# =====================================================================
LANGS = ["en", "zh", "ms", "ta"]
LANG_NAMES = {"en": "English", "zh": "中文", "ms": "Bahasa Melayu", "ta": "தமிழ்"}

MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"],
    "zh": [f"{i}月" for i in range(1, 13)],
    "ms": ["Januari", "Februari", "Mac", "April", "Mei", "Jun", "Julai",
           "Ogos", "September", "Oktober", "November", "Disember"],
    "ta": ["ஜனவரி", "பிப்ரவரி", "மார்ச்", "ஏப்ரல்", "மே", "ஜூன்", "ஜூலை",
           "ஆகஸ்ட்", "செப்டம்பர்", "அக்டோபர்", "நவம்பர்", "டிசம்பர்"],
}

# key: (English, Chinese, Malay, Tamil)
TR = {
    "language": ("Language", "语言", "Bahasa", "மொழி"),
    # --- navigation ---
    "back": ("← Back", "← 返回", "← Kembali", "← பின்செல்"),
    "home": ("← Home", "← 首页", "← Utama", "← முகப்பு"),
    # --- landing ---
    "tagline": ("Who are you today?", "请选择您的身份", "Siapa anda hari ini?", "இன்று நீங்கள் யார்?"),
    "seller": ("Seller", "摊主", "Penjaja", "விற்பனையாளர்"),
    "visitor": ("Visitor", "访客", "Pengunjung", "பார்வையாளர்"),
    "seller_desc": ("Stall owner? Bid for a stall or manage yours.",
                    "是摊主吗？竞投摊位或管理您的摊位。",
                    "Pemilik gerai? Bida untuk gerai atau urus gerai anda.",
                    "கடை உரிமையாளரா? கடைக்கு ஏலம் எடுக்கவும் அல்லது உங்கள் கடையை நிர்வகிக்கவும்."),
    "visitor_desc": ("Hungry? Follow your favourite stalls.",
                     "肚子饿了吗？关注您喜爱的摊位。",
                     "Lapar? Ikuti gerai kegemaran anda.",
                     "பசிக்கிறதா? உங்களுக்குப் பிடித்த கடைகளைப் பின்தொடருங்கள்."),
    "btn_seller": ("I'm a Seller", "我是摊主", "Saya Penjaja", "நான் விற்பனையாளர்"),
    "btn_visitor": ("I'm a Visitor", "我是访客", "Saya Pengunjung", "நான் பார்வையாளர்"),
    # --- seller home ---
    "seller_sub": ("What would you like to do?", "您想做什么？", "Apa yang anda ingin lakukan?",
                   "நீங்கள் என்ன செய்ய விரும்புகிறீர்கள்?"),
    "bid_title": ("Bid for Stall", "竞投摊位", "Bida untuk Gerai", "கடைக்கு ஏலம்"),
    "bid_desc": ("Opens the NEA page on becoming a hawker.",
                 "打开国家环境局（NEA）的小贩申请页面。",
                 "Buka halaman NEA tentang cara menjadi penjaja.",
                 "ஹாக்கர் ஆவது குறித்த NEA பக்கத்தைத் திறக்கும்."),
    "bid_btn": ("Go to NEA ↗", "前往 NEA ↗", "Pergi ke NEA ↗", "NEA-க்குச் செல்ல ↗"),
    "login_title": ("Seller Login", "摊主登录", "Log Masuk Penjaja", "விற்பனையாளர் உள்நுழைவு"),
    "login_desc": ("Enter your business UEN to use the seller tools.",
                   "输入您的商业 UEN 以使用摊主工具。",
                   "Masukkan UEN perniagaan anda untuk guna alat penjaja.",
                   "விற்பனையாளர் கருவிகளைப் பயன்படுத்த உங்கள் வணிக UEN-ஐ உள்ளிடவும்."),
    # --- login page ---
    "login_sub": ("Enter your business UEN / secret code.",
                  "请输入您的商业 UEN／秘密代码。",
                  "Masukkan UEN perniagaan / kod rahsia anda.",
                  "உங்கள் வணிக UEN / ரகசியக் குறியீட்டை உள்ளிடவும்."),
    "login_field": ("Business UEN / secret code", "商业 UEN／秘密代码",
                    "UEN perniagaan / kod rahsia", "வணிக UEN / ரகசியக் குறியீடு"),
    "login_btn": ("Log in", "登录", "Log masuk", "உள்நுழை"),
    "login_err": ("We couldn't find that UEN. Please check and try again.",
                  "找不到该 UEN，请检查后重试。",
                  "UEN itu tidak dijumpai. Sila semak dan cuba lagi.",
                  "அந்த UEN கிடைக்கவில்லை. சரிபார்த்து மீண்டும் முயற்சிக்கவும்."),
    "demo_uens": ("Demo UENs to try: {uens}", "可试用的演示 UEN：{uens}",
                  "UEN demo untuk dicuba: {uens}", "முயற்சிக்க டெமோ UEN: {uens}"),
    "logout": ("Log out", "登出", "Log keluar", "வெளியேறு"),
    "admin_sub": ("{centre} · Seller admin", "{centre} · 摊主管理",
                  "{centre} · Pentadbir penjaja", "{centre} · விற்பனையாளர் நிர்வாகம்"),
    # --- seller tabs ---
    "tab_bc": ("📣 Community Broadcast", "📣 社区广播", "📣 Siaran Komuniti", "📣 சமூக ஒளிபரப்பு"),
    "tab_calc": ("🧮 Hawker Calculator", "🧮 小贩计算器", "🧮 Kalkulator Penjaja", "🧮 ஹாக்கர் கணிப்பான்"),
    # --- broadcast ---
    "post_title": ("Post to the Community Broadcast", "发布到社区广播",
                   "Hantar ke Siaran Komuniti", "சமூக ஒளிபரப்பில் பதிவிடுங்கள்"),
    "post_cap": ("Visitors who subscribe to your stall will see this on their page.",
                 "订阅您摊位的访客将在他们的页面看到此内容。",
                 "Pengunjung yang melanggan gerai anda akan melihat ini di halaman mereka.",
                 "உங்கள் கடையைப் பின்தொடரும் பார்வையாளர்கள் தங்கள் பக்கத்தில் இதைக் காண்பார்கள்."),
    "caption_label": ("What's cooking today?", "今天有什么好吃的？", "Apa yang dimasak hari ini?",
                      "இன்று என்ன சமைக்கிறீர்கள்?"),
    "caption_ph": ("Describe your delicacy…", "介绍一下您的美食…", "Terangkan hidangan istimewa anda…",
                   "உங்கள் உணவைப் பற்றி விவரிக்கவும்…"),
    "photos": ("Photos of your delicacies", "美食照片", "Gambar hidangan anda",
               "உங்கள் உணவுகளின் படங்கள்"),
    "closing_cb": ("Include a closure notice", "加入休业通知", "Sertakan notis penutupan",
                   "மூடல் அறிவிப்பைச் சேர்க்கவும்"),
    "closure_dates": ("Closure dates (from → to)", "休业日期（从 → 到）",
                      "Tarikh penutupan (dari → hingga)", "மூடல் தேதிகள் (இருந்து → வரை)"),
    "post_btn": ("📣 Post", "📣 发布", "📣 Hantar", "📣 பதிவிடு"),
    "err_empty": ("Add a description, a photo or a closure notice first.",
                  "请先添加描述、照片或休业通知。",
                  "Sila tambah penerangan, gambar atau notis penutupan dahulu.",
                  "முதலில் விளக்கம், படம் அல்லது மூடல் அறிவிப்பைச் சேர்க்கவும்."),
    "err_dates": ("Please pick both a start and an end date for the closure.",
                  "请选择休业的开始和结束日期。",
                  "Sila pilih tarikh mula dan tarikh akhir penutupan.",
                  "மூடலுக்கான தொடக்க மற்றும் முடிவு தேதிகளைத் தேர்ந்தெடுக்கவும்."),
    "posted": ("Posted!", "已发布！", "Telah dihantar!", "பதிவிடப்பட்டது!"),
    "public_bc": ("Public broadcast", "公开广播", "Siaran awam", "பொது ஒளிபரப்பு"),
    "no_posts_seller": ("No posts yet. Be the first!", "还没有帖子，成为第一个吧！",
                        "Belum ada hantaran. Jadilah yang pertama!",
                        "இன்னும் பதிவுகள் இல்லை. முதலில் நீங்கள் பதிவிடுங்கள்!"),
    "delete": ("🗑️ Delete", "🗑️ 删除", "🗑️ Padam", "🗑️ நீக்கு"),
    "closed_range": ("🔒 Closed from {start} to {end}", "🔒 休业：{start} 至 {end}",
                     "🔒 Tutup dari {start} hingga {end}", "🔒 {start} முதல் {end} வரை மூடப்பட்டிருக்கும்"),
    "subscribe": ("☆ Subscribe", "☆ 订阅", "☆ Langgan", "☆ பின்தொடர்"),
    "subscribed": ("⭐ Subscribed", "⭐ 已订阅", "⭐ Dilanggan", "⭐ பின்தொடர்கிறீர்கள்"),
    # --- calculator ---
    "add_entry": ("Add an entry", "添加记录", "Tambah rekod", "பதிவைச் சேர்க்கவும்"),
    "date": ("Date", "日期", "Tarikh", "தேதி"),
    "type": ("Type", "类别", "Jenis", "வகை"),
    "Earning": ("Earning", "收入", "Pendapatan", "வருமானம்"),
    "Expense": ("Expense", "支出", "Perbelanjaan", "செலவு"),
    "amt": ("Amt (S$)", "金额 (S$)", "Jumlah (S$)", "தொகை (S$)"),
    "desc": ("Description", "说明", "Keterangan", "விளக்கம்"),
    "desc_ph": ("e.g. Chicken supplier", "例如：鸡肉供应商", "cth: Pembekal ayam",
                "எ.கா. கோழி விநியோகஸ்தர்"),
    "add_btn": ("➕ Add entry", "➕ 添加", "➕ Tambah", "➕ சேர்"),
    "err_amt": ("Please enter an amount above 0.", "请输入大于 0 的金额。",
                "Sila masukkan jumlah melebihi 0.", "0-க்கு மேல் தொகையை உள்ளிடவும்."),
    "saved": ("Entry saved.", "记录已保存。", "Rekod disimpan.", "பதிவு சேமிக்கப்பட்டது."),
    "your_numbers": ("Your numbers", "您的数据", "Angka anda", "உங்கள் கணக்குகள்"),
    "view": ("View", "查看", "Paparan", "காட்சி"),
    "Daily": ("Daily", "每日", "Harian", "தினசரி"),
    "Monthly": ("Monthly", "每月", "Bulanan", "மாதாந்திர"),
    "Yearly": ("Yearly", "每年", "Tahunan", "ஆண்டுதோறும்"),
    "pick_day": ("Pick a day", "选择日期", "Pilih hari", "நாளைத் தேர்ந்தெடுக்கவும்"),
    "year": ("Year", "年份", "Tahun", "ஆண்டு"),
    "month": ("Month", "月份", "Bulan", "மாதம்"),
    "m_earn": ("Earnings", "总收入", "Jumlah pendapatan", "மொத்த வருமானம்"),
    "m_exp": ("Expenses", "总支出", "Jumlah perbelanjaan", "மொத்த செலவு"),
    "m_net": ("Net profit", "净利润", "Untung bersih", "நிகர லாபம்"),
    "no_entries": ("No entries for this period yet.", "此期间暂无记录。",
                   "Belum ada rekod untuk tempoh ini.", "இக்காலத்திற்கு இன்னும் பதிவுகள் இல்லை."),
    "delete_entry": ("🗑️ Delete an entry", "🗑️ 删除记录", "🗑️ Padam rekod", "🗑️ பதிவை நீக்கு"),
    "choose_entry": ("Choose entry", "选择记录", "Pilih rekod", "பதிவைத் தேர்ந்தெடுக்கவும்"),
    "delete_sel": ("Delete selected entry", "删除所选记录", "Padam rekod dipilih",
                   "தேர்ந்தெடுத்த பதிவை நீக்கு"),
    # --- visitor ---
    "v_sub": ("What are you looking for today?", "您今天想找什么？", "Apa yang anda cari hari ini?",
              "இன்று நீங்கள் எதைத் தேடுகிறீர்கள்?"),
    "fav_title": ("My Favourite Hawker Stalls", "我喜爱的小贩摊位", "Gerai Penjaja Kegemaran Saya",
                  "எனக்குப் பிடித்த ஹாக்கர் கடைகள்"),
    "fav_desc": ("Follow stalls and see their latest posts.", "关注摊位，查看最新动态。",
                 "Ikuti gerai dan lihat hantaran terkini.",
                 "கடைகளைப் பின்தொடர்ந்து சமீபத்திய பதிவுகளைப் பாருங்கள்."),
    "sched_title": ("Hawker Schedule", "小贩中心时间表", "Jadual Penjaja", "ஹாக்கர் அட்டவணை"),
    "sched_desc": ("Cleaning and closure dates.", "清洁与休业日期。",
                   "Tarikh pembersihan dan penutupan.", "சுத்தம் செய்தல் மற்றும் மூடல் தேதிகள்."),
    "near_title": ("Nearby Hawker", "附近的小贩中心", "Penjaja Berdekatan", "அருகிலுள்ள ஹாக்கர்"),
    "near_desc": ("Find hawker centres around you.", "查找您附近的小贩中心。",
                  "Cari pusat penjaja di sekitar anda.",
                  "உங்களைச் சுற்றியுள்ள ஹாக்கர் நிலையங்களைக் கண்டறியுங்கள்."),
    "queue_title": ("Queue Tracker", "排队追踪", "Penjejak Barisan", "வரிசை கண்காணிப்பு"),
    "queue_desc": ("To be explored.", "有待探索。", "Akan diteroka.", "ஆராயப்பட உள்ளது."),
    "queue_sub": ("See how long the queue is.", "查看排队情况。", "Lihat panjang barisan.",
                  "வரிசை எவ்வளவு நீளம் என்று பாருங்கள்."),
    "news_title": ("Hawkers News & Social Feed", "小贩新闻与社交动态",
                   "Berita & Suapan Sosial Penjaja", "ஹாக்கர் செய்திகள் & சமூக ஊட்டம்"),
    "news_desc": ("News and updates from the hawker scene.", "小贩界的新闻与最新消息。",
                  "Berita dan kemas kini dari dunia penjaja.",
                  "ஹாக்கர் உலகின் செய்திகளும் புதுப்பிப்புகளும்."),
    "news_sub": ("News and updates.", "新闻与动态。", "Berita dan kemas kini.",
                 "செய்திகள் மற்றும் புதுப்பிப்புகள்."),
    "open": ("Open", "打开", "Buka", "திற"),
    "fav_sub": ("Subscribe to stalls to pin them to the top.", "订阅摊位即可将其置顶。",
                "Langgan gerai untuk menyematkannya di atas.",
                "கடைகளைப் பின்தொடர்ந்தால் அவை மேலே காட்டப்படும்."),
    "your_favs": ("⭐ Your favourites", "⭐ 我的最爱", "⭐ Kegemaran anda", "⭐ உங்கள் விருப்பங்கள்"),
    "no_favs": ("No favourites yet. Tap Subscribe on any stall below.",
                "还没有最爱。点击下方任意摊位的「订阅」。",
                "Belum ada kegemaran. Tekan Langgan pada mana-mana gerai di bawah.",
                "இன்னும் விருப்பங்கள் இல்லை. கீழே உள்ள எந்தக் கடையிலும் 'பின்தொடர்' என்பதைத் தட்டவும்."),
    "no_bc": ("No broadcasts yet. Check back soon!", "暂无广播，请稍后再来！",
              "Belum ada siaran. Sila semak semula nanti!",
              "இன்னும் ஒளிபரப்புகள் இல்லை. விரைவில் மீண்டும் பாருங்கள்!"),
    "from_favs": ("From your favourite stalls", "来自您喜爱的摊位",
                  "Daripada gerai kegemaran anda", "உங்களுக்குப் பிடித்த கடைகளிலிருந்து"),
    "discover": ("Discover more stalls", "发现更多摊位", "Terokai lebih banyak gerai",
                 "மேலும் கடைகளைக் கண்டறியுங்கள்"),
    "tab_clean": ("🧹 Cleaning", "🧹 清洁", "🧹 Pembersihan", "🧹 சுத்தம்"),
    "tab_closure": ("🔒 Closure", "🔒 休业", "🔒 Penutupan", "🔒 மூடல்"),
    "clean_soon": ("Cleaning schedule data coming soon.", "清洁时间表数据即将推出。",
                   "Data jadual pembersihan akan datang.", "சுத்தம் செய்யும் அட்டவணை விரைவில் வரும்."),
    "closure_soon": ("Closure schedule data coming soon.", "休业时间表数据即将推出。",
                     "Data jadual penutupan akan datang.", "மூடல் அட்டவணை விரைவில் வரும்."),
    "soon": ("Coming soon.", "敬请期待。", "Akan datang.", "விரைவில் வரும்."),
    "exploring": ("Still being explored.", "仍在探索中。", "Masih diteroka.",
                  "இன்னும் ஆராயப்படுகிறது."),
}


def cur_lang():
    return st.session_state.get("lang", "en")


def t(key, **kw):
    text = TR[key][LANGS.index(cur_lang())]
    return text.format(**kw) if kw else text


def fmt_date(d):
    """d is a date or datetime. Month names follow the chosen language."""
    lang = cur_lang()
    if lang == "zh":
        return f"{d.year}年{d.month}月{d.day}日"
    return f"{d.day} {MONTHS[lang][d.month - 1]} {d.year}"


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
st.session_state.setdefault("lang", "en")
st.session_state.setdefault("view", "landing")
st.session_state.setdefault("seller_uen", None)
st.session_state.setdefault("subs", [])      # visitor's subscribed stall UENs


def go(view):
    st.session_state.view = view


def logout():
    st.session_state.seller_uen = None
    st.session_state.view = "seller_home"


def language_picker():
    _, right = st.columns([3, 1.2])
    right.selectbox(t("language"), LANGS, key="lang",
                    format_func=lambda c: LANG_NAMES[c], label_visibility="collapsed")


def page_header(title, subtitle, mascot, back_to, back_label_key="back", key="x"):
    prefix = "b" if mascot == "haw_bo" else "p"
    st.button(t(back_label_key), key=f"{prefix}_back_{key}", on_click=go, args=(back_to,))
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
    """One broadcast post card. (Posts are shown in the language the seller wrote them.)"""
    with st.container(border=True):
        left, right = st.columns([3, 1.4], vertical_alignment="center")
        left.markdown(f"**{p['stall']}** · {p['centre']}")
        posted = datetime.fromisoformat(p["time"])
        left.caption(f"{fmt_date(posted)}, {posted.strftime('%H:%M')}")

        if show_subscribe:
            subscribed = p["uen"] in st.session_state.subs
            right.button(t("subscribed") if subscribed else t("subscribe"),
                         key=f"p_sub_{key_prefix}_{p['id']}",
                         on_click=toggle_sub, args=(p["uen"],), use_container_width=True)
        if owner_uen and owner_uen == p["uen"]:
            right.button(t("delete"), key=f"b_del_{key_prefix}_{p['id']}",
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
            st.warning(t("closed_range",
                         start=fmt_date(datetime.fromisoformat(p["closure_start"])),
                         end=fmt_date(datetime.fromisoformat(p["closure_end"]))))


# =====================================================================
# PAGE 1: LANDING
# =====================================================================
def landing():
    st.markdown("<p class='title'>HAW<span>-</span>ONE</p>", unsafe_allow_html=True)
    st.markdown(f"<p class='tagline'>{t('tagline')}</p>", unsafe_allow_html=True)
    c1, c2 = st.columns(2, gap="large")
    with c1:
        with st.container(key="card_blue_seller"):
            st.image(os.path.join(ASSETS, "haw_bo.png"), width=230)
            st.markdown(f"<p class='role-name'>🧑‍🍳 {t('seller')}</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='role-desc'>{t('seller_desc')}</p>", unsafe_allow_html=True)
            st.button(t("btn_seller"), key="b_seller", use_container_width=True,
                      on_click=go, args=("seller_home",))
    with c2:
        with st.container(key="card_pink_visitor"):
            st.image(os.path.join(ASSETS, "haw_sim.png"), width=230)
            st.markdown(f"<p class='role-name'>🚶 {t('visitor')}</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='role-desc'>{t('visitor_desc')}</p>", unsafe_allow_html=True)
            st.button(t("btn_visitor"), key="p_visitor", use_container_width=True,
                      on_click=go, args=("visitor_home",))


# =====================================================================
# PAGE 2: SELLER
# =====================================================================
def seller_home():
    page_header(t("seller"), t("seller_sub"), "haw_bo", "landing", "home", key="seller_home")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        menu_card("blue", "bid", "📝", t("bid_title"), t("bid_desc"), t("bid_btn"), link=NEA_URL)
    with c2:
        menu_card("blue", "login", "🔑", t("login_title"), t("login_desc"), t("login_title"),
                  on_click=go, args=("seller_login",))


def seller_login():
    page_header(t("login_title"), t("login_sub"), "haw_bo", "seller_home", key="seller_login")
    with st.form("login_form"):
        code = st.text_input(t("login_field"), type="password")
        ok = st.form_submit_button(t("login_btn"), type="primary")
    if ok:
        code = code.strip().upper()
        if code in STALLS:
            st.session_state.seller_uen = code
            st.session_state.view = "seller_admin"
            st.rerun()
        else:
            st.error(t("login_err"))
    st.caption(t("demo_uens", uens=", ".join(STALLS.keys())))


def seller_admin():
    uen = st.session_state.seller_uen
    if uen not in STALLS:
        st.session_state.view = "seller_login"
        st.rerun()
    stall = STALLS[uen]

    page_header(stall["name"], t("admin_sub", centre=stall["centre"]), "haw_bo",
                "seller_home", "back", key="seller_admin")
    st.button(t("logout"), key="b_logout", on_click=logout)

    tab_bc, tab_calc = st.tabs([t("tab_bc"), t("tab_calc")])
    with tab_bc:
        seller_broadcast(uen, stall)
    with tab_calc:
        seller_calculator(uen)


def seller_broadcast(uen, stall):
    st.subheader(t("post_title"))
    st.caption(t("post_cap"))
    with st.form("post_form", clear_on_submit=True):
        caption = st.text_area(t("caption_label"), placeholder=t("caption_ph"))
        photos = st.file_uploader(t("photos"), type=["png", "jpg", "jpeg"],
                                  accept_multiple_files=True)
        closing = st.checkbox(t("closing_cb"))
        dates = st.date_input(t("closure_dates"), value=(date.today(), date.today()))
        submitted = st.form_submit_button(t("post_btn"), type="primary")

    if submitted:
        has_range = isinstance(dates, (tuple, list)) and len(dates) == 2
        if not caption.strip() and not photos and not closing:
            st.error(t("err_empty"))
        elif closing and not has_range:
            st.error(t("err_dates"))
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
            st.success(t("posted"))

    st.divider()
    st.subheader(t("public_bc"))
    posts = load_posts()
    if not posts:
        st.info(t("no_posts_seller"))
    for p in posts:
        render_post(p, "seller", owner_uen=uen)


def seller_calculator(uen):
    st.subheader(t("add_entry"))
    with st.form("ledger_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([1.3, 1.2, 1, 2])
        d = c1.date_input(t("date"), value=date.today())
        typ = c2.selectbox(t("type"), ["Earning", "Expense"], format_func=lambda k: t(k))
        amt = c3.number_input(t("amt"), min_value=0.0, step=0.5, format="%.2f")
        desc = c4.text_input(t("desc"), placeholder=t("desc_ph"))
        added = st.form_submit_button(t("add_btn"), type="primary")

    if added:
        if amt <= 0:
            st.error(t("err_amt"))
        else:
            df = load_ledger()
            row = {"uen": uen, "id": uuid.uuid4().hex[:8], "date": d.isoformat(),
                   "type": typ, "amount": float(amt), "description": desc.strip()}
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
            save_ledger(df)
            st.success(t("saved"))

    st.divider()
    st.subheader(t("your_numbers"))
    df = load_ledger()
    mine = df[df["uen"] == uen].copy()
    mine["date"] = pd.to_datetime(mine["date"])
    mine["amount"] = mine["amount"].astype(float)

    view = st.radio(t("view"), ["Daily", "Monthly", "Yearly"], horizontal=True,
                    format_func=lambda k: t(k))
    today = date.today()
    years = sorted(set(mine["date"].dt.year.tolist()) | {today.year})
    month_name = lambda m: MONTHS[cur_lang()][m - 1]

    if view == "Daily":
        day = st.date_input(t("pick_day"), value=today, key="calc_day")
        sel = mine[mine["date"].dt.date == day]
        group = None
    elif view == "Monthly":
        a, b = st.columns(2)
        y = a.selectbox(t("year"), years, index=years.index(today.year), key="calc_m_year")
        m = b.selectbox(t("month"), list(range(1, 13)), index=today.month - 1,
                        format_func=month_name, key="calc_month")
        sel = mine[(mine["date"].dt.year == y) & (mine["date"].dt.month == m)]
        group = sel["date"].dt.day
    else:
        y = st.selectbox(t("year"), years, index=years.index(today.year), key="calc_y_year")
        sel = mine[mine["date"].dt.year == y]
        group = sel["date"].dt.month

    earn = sel.loc[sel["type"] == "Earning", "amount"].sum()
    exp = sel.loc[sel["type"] == "Expense", "amount"].sum()
    net = earn - exp
    m1, m2, m3 = st.columns(3)
    m1.metric(t("m_earn"), f"S${earn:,.2f}")
    m2.metric(t("m_exp"), f"S${exp:,.2f}")
    m3.metric(t("m_net"), f"S${net:,.2f}")

    if sel.empty:
        st.info(t("no_entries"))
        return

    if group is not None:
        chart = (sel.assign(period=group).groupby(["period", "type"])["amount"].sum()
                 .unstack(fill_value=0).reindex(columns=["Earning", "Expense"], fill_value=0))
        chart.columns = [t("Earning"), t("Expense")]
        st.bar_chart(chart)

    show = sel.sort_values("date").copy()
    table = pd.DataFrame({
        t("date"): show["date"].apply(fmt_date),
        t("type"): show["type"].map(lambda k: t(k)),
        t("amt"): show["amount"],
        t("desc"): show["description"],
    })
    st.dataframe(table, hide_index=True, use_container_width=True)

    with st.expander(t("delete_entry")):
        labels = {r["id"]: f"{fmt_date(r['date'])} · {t(r['type'])} · S${r['amount']:.2f} · {r['description']}"
                  for _, r in sel.sort_values("date").iterrows()}
        pick = st.selectbox(t("choose_entry"), list(labels.keys()), format_func=lambda k: labels[k])
        if st.button(t("delete_sel"), key="b_del_entry"):
            df = load_ledger()
            save_ledger(df[df["id"] != pick])
            st.rerun()


# =====================================================================
# PAGE 2: VISITOR
# =====================================================================
def visitor_home():
    page_header(t("visitor"), t("v_sub"), "haw_sim", "landing", "home", key="visitor_home")
    items = [
        ("fav", "⭐", "fav_title", "fav_desc", "v_fav"),
        ("sched", "🗓️", "sched_title", "sched_desc", "v_sched"),
        ("near", "📍", "near_title", "near_desc", "v_near"),
        ("queue", "⏱️", "queue_title", "queue_desc", "v_queue"),
        ("news", "📰", "news_title", "news_desc", "v_news"),
    ]
    for i in range(0, len(items), 2):
        cols = st.columns(2, gap="large")
        for col, (key, emoji, title, desc, target) in zip(cols, items[i:i + 2]):
            with col:
                menu_card("pink", key, emoji, t(title), t(desc), t("open"),
                          on_click=go, args=(target,))


def visitor_favourites():
    page_header(t("fav_title"), t("fav_sub"), "haw_sim", "visitor_home", key="v_fav")
    subs = st.session_state.subs

    st.markdown(f"#### {t('your_favs')}")
    if subs:
        st.write("  ".join(f"`{STALLS[u]['name']}`" for u in subs if u in STALLS))
    else:
        st.caption(t("no_favs"))

    posts = load_posts()
    if not posts:
        st.info(t("no_bc"))
        return

    fav_posts = [p for p in posts if p["uen"] in subs]
    other_posts = [p for p in posts if p["uen"] not in subs]

    if fav_posts:
        st.markdown(f"#### {t('from_favs')}")
        for p in fav_posts:
            render_post(p, "fav", show_subscribe=True)
    if other_posts:
        st.markdown(f"#### {t('discover')}")
        for p in other_posts:
            render_post(p, "other", show_subscribe=True)


def visitor_schedule():
    page_header(t("sched_title"), t("sched_desc"), "haw_sim", "visitor_home", key="v_sched")
    t1, t2 = st.tabs([t("tab_clean"), t("tab_closure")])
    with t1:
        st.info(t("clean_soon"))
    with t2:
        st.info(t("closure_soon"))


def coming_soon(title, subtitle, note, key):
    page_header(title, subtitle, "haw_sim", "visitor_home", key=key)
    st.info(note)


# =====================================================================
# ROUTER
# =====================================================================
language_picker()

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
    coming_soon(t("near_title"), t("near_desc"), t("soon"), "v_near")
elif view == "v_queue":
    coming_soon(t("queue_title"), t("queue_sub"), t("exploring"), "v_queue")
elif view == "v_news":
    coming_soon(t("news_title"), t("news_sub"), t("soon"), "v_news")
else:
    go("landing")
    st.rerun()
