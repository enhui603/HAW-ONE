import base64
import json
import math
import os
import urllib.parse
import urllib.request
import uuid
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st

st.set_page_config(page_title="HAW-ONE", page_icon=os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "haw_sim.png"), layout="wide")

# =====================================================================
# SETTINGS
# =====================================================================
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")
ICONS = os.path.join(ASSETS, "icons")
DATA = os.path.join(HERE, "data")
UPLOADS = os.path.join(DATA, "uploads")
os.makedirs(UPLOADS, exist_ok=True)

POSTS_FILE = os.path.join(DATA, "posts.json")
LEDGER_FILE = os.path.join(DATA, "ledger.csv")
HAWKER_FILE = os.path.join(HERE, "hawker_centres_final.csv")

NEA_URL = "https://www.nea.gov.sg/our-services/hawker-management/becoming-a-hawker"

# Mascot palette
BLUE = "#5B9BD5"   # Haw Bo   -> Seller
PINK = "#E8587A"   # Haw Sim  -> Visitor
INK = "#3B2A33"
CREAM = "#FFF8F0"

# Text size choices (percent of normal). Default is the bigger one.
SIZES = {"A": 100, "A+": 125, "A++": 150}
DEFAULT_SIZE = "A+"

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
    "text_size": ("Text size", "字体大小", "Saiz teks", "எழுத்து அளவு"),
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
    "tab_bc": ("Community Broadcast", "社区广播", "Siaran Komuniti", "சமூக ஒளிபரப்பு"),
    "tab_calc": ("Hawker Calculator", "小贩计算器", "Kalkulator Penjaja", "ஹாக்கர் கணிப்பான்"),
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
    "post_btn": ("Post", "发布", "Hantar", "பதிவிடு"),
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
    "delete": ("Delete", "删除", "Padam", "நீக்கு"),
    "closed_range": ("Closed from {start} to {end}", "休业：{start} 至 {end}",
                     "Tutup dari {start} hingga {end}", "{start} முதல் {end} வரை மூடப்பட்டிருக்கும்"),
    "subscribe": ("Subscribe", "订阅", "Langgan", "பின்தொடர்"),
    "subscribed": ("Subscribed ✓", "已订阅 ✓", "Dilanggan ✓", "பின்தொடர்கிறீர்கள் ✓"),
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
    "add_btn": ("Add entry", "添加", "Tambah", "சேர்"),
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
    "delete_entry": ("Delete an entry", "删除记录", "Padam rekod", "பதிவை நீக்கு"),
    "choose_entry": ("Choose entry", "选择记录", "Pilih rekod", "பதிவைத் தேர்ந்தெடுக்கவும்"),
    "delete_sel": ("Delete selected entry", "删除所选记录", "Padam rekod dipilih",
                   "தேர்ந்தெடுத்த பதிவை நீக்கு"),
    # --- visitor menu ---
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
    "news_title": ("Hawkers News & Social Feed", "小贩新闻与社交动态",
                   "Berita & Suapan Sosial Penjaja", "ஹாக்கர் செய்திகள் & சமூக ஊட்டம்"),
    "news_desc": ("News and updates from the hawker scene.", "小贩界的新闻与最新消息。",
                  "Berita dan kemas kini dari dunia penjaja.",
                  "ஹாக்கர் உலகின் செய்திகளும் புதுப்பிப்புகளும்."),
    "news_sub": ("News and updates.", "新闻与动态。", "Berita dan kemas kini.",
                 "செய்திகள் மற்றும் புதுப்பிப்புகள்."),
    "open": ("Open", "打开", "Buka", "திற"),
    "soon": ("Coming soon.", "敬请期待。", "Akan datang.", "விரைவில் வரும்."),
    # --- favourites ---
    "fav_sub": ("Subscribe to stalls to pin them to the top.", "订阅摊位即可将其置顶。",
                "Langgan gerai untuk menyematkannya di atas.",
                "கடைகளைப் பின்தொடர்ந்தால் அவை மேலே காட்டப்படும்."),
    "your_favs": ("Your favourites", "我的最爱", "Kegemaran anda", "உங்கள் விருப்பங்கள்"),
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
    # --- schedule (cleaning / closure) ---
    "tab_clean": ("Cleaning", "清洁", "Pembersihan", "சுத்தம்"),
    "tab_closure": ("Closure", "休业", "Penutupan", "மூடல்"),
    "soon_title": ("Cleaning in the next 30 days", "未来 30 天的清洁安排",
                   "Pembersihan dalam 30 hari akan datang", "அடுத்த 30 நாட்களில் சுத்தம்"),
    "none_soon": ("No cleaning scheduled in the next 30 days.", "未来 30 天没有清洁安排。",
                  "Tiada pembersihan dijadualkan dalam 30 hari akan datang.",
                  "அடுத்த 30 நாட்களில் சுத்தம் எதுவும் திட்டமிடப்படவில்லை."),
    "find_centre": ("Find a hawker centre", "查找小贩中心", "Cari pusat penjaja",
                    "ஹாக்கர் நிலையத்தைத் தேடுங்கள்"),
    "select_centre": ("Select a hawker centre", "选择小贩中心", "Pilih pusat penjaja",
                      "ஹாக்கர் நிலையத்தைத் தேர்ந்தெடுக்கவும்"),
    "quarter": ("Quarter {n}", "第 {n} 季度", "Suku {n}", "காலாண்டு {n}"),
    "st_done": ("Done", "已完成", "Selesai", "முடிந்தது"),
    "st_now": ("Happening now", "进行中", "Sedang berlangsung", "நடைபெறுகிறது"),
    "st_upcoming": ("Upcoming", "即将到来", "Akan tiba", "வரவிருக்கிறது"),
    "st_tbc": ("To be confirmed", "待定", "Akan dimaklumkan", "உறுதிசெய்யப்படும்"),
    "col_centre": ("Hawker centre", "小贩中心", "Pusat penjaja", "ஹாக்கர் நிலையம்"),
    "col_from": ("From", "开始", "Dari", "தொடக்கம்"),
    "col_to": ("To", "结束", "Hingga", "முடிவு"),
    "col_days": ("Days", "天数", "Hari", "நாட்கள்"),
    "other_works": ("Other works", "其他工程", "Kerja-kerja lain", "பிற பணிகள்"),
    "no_works": ("No other works in 2026.", "2026 年没有其他工程。", "Tiada kerja lain pada 2026.",
                 "2026-இல் பிற பணிகள் இல்லை."),
    "long_closures": ("Longer closures in 2026", "2026 年较长的休业", "Penutupan lebih lama pada 2026",
                      "2026-இல் நீண்ட மூடல்கள்"),
    "stall_closures": ("Closures posted by stalls", "摊主发布的休业通知",
                       "Penutupan yang dihantar oleh gerai", "கடைகள் பதிவிட்ட மூடல்கள்"),
    "none_stall_closures": ("No closures posted yet.", "暂无休业通知。", "Belum ada penutupan dihantar.",
                            "இன்னும் மூடல் அறிவிப்புகள் இல்லை."),
    "data_note": ("Dates are for 2026 and may change.", "日期为 2026 年，可能会有变动。",
                  "Tarikh adalah untuk 2026 dan mungkin berubah.",
                  "தேதிகள் 2026-க்கானவை; மாறக்கூடும்."),
    "closed_2026": ("Closed for all of 2026", "2026 年全年休业", "Tutup sepanjang 2026",
                    "2026 முழுவதும் மூடப்பட்டிருக்கும்"),
    # --- nearby ---
    "map_title": ("Map of hawker centres", "小贩中心地图", "Peta pusat penjaja",
                  "ஹாக்கர் நிலையங்களின் வரைபடம்"),
    "where_are_you": ("Where are you?", "您在哪里？", "Di mana anda?", "நீங்கள் எங்கே இருக்கிறீர்கள்?"),
    "opt_place": ("Type a postal code or place", "输入邮区编号或地点", "Taip poskod atau tempat",
                  "அஞ்சல் குறியீடு அல்லது இடத்தை உள்ளிடவும்"),
    "opt_gps": ("Use my location", "使用我的位置", "Guna lokasi saya", "என் இருப்பிடத்தைப் பயன்படுத்து"),
    "place_ph": ("e.g. 680123 or Bishan MRT", "例如：680123 或 碧山地铁站",
                 "cth: 680123 atau MRT Bishan", "எ.கா. 680123 அல்லது பிஷான் MRT"),
    "pick_result": ("Choose the right place", "选择正确的地点", "Pilih tempat yang betul",
                    "சரியான இடத்தைத் தேர்ந்தெடுக்கவும்"),
    "place_err": ("We couldn't find or look up that place. Check it, or try Use my location.",
                  "找不到或无法查询该地点，请检查，或试试「使用我的位置」。",
                  "Tempat itu tidak dijumpai. Semak semula, atau cuba Guna lokasi saya.",
                  "அந்த இடத்தைக் கண்டுபிடிக்க முடியவில்லை. சரிபார்க்கவும் அல்லது 'என் இருப்பிடம்' முயற்சிக்கவும்."),
    "gps_hint": ("Tap the button, then allow location access in your browser.",
                 "点击按钮，然后在浏览器中允许定位。",
                 "Tekan butang, kemudian benarkan akses lokasi dalam pelayar anda.",
                 "பொத்தானை அழுத்தி, உலாவியில் இருப்பிட அனுமதியை வழங்கவும்."),
    "gps_missing": ("Location is not available here. Please type a postal code instead.",
                    "此处无法使用定位，请改为输入邮区编号。",
                    "Lokasi tidak tersedia di sini. Sila taip poskod.",
                    "இங்கே இருப்பிடம் கிடைக்கவில்லை. அஞ்சல் குறியீட்டை உள்ளிடவும்."),
    "legend": ("Pink dots are hawker centres. Blue dot is you. Red dots are the nearest.",
               "粉红点是小贩中心，蓝点是您，红点是最近的。",
               "Titik merah jambu ialah pusat penjaja. Titik biru ialah anda. Titik merah ialah yang terdekat.",
               "இளஞ்சிவப்புப் புள்ளிகள் ஹாக்கர் நிலையங்கள். நீலப் புள்ளி நீங்கள். சிவப்புப் புள்ளிகள் அருகிலுள்ளவை."),
    "nearest": ("Nearest hawker centres", "最近的小贩中心", "Pusat penjaja terdekat",
                "அருகிலுள்ள ஹாக்கர் நிலையங்கள்"),
    "km_away": ("{km} km away", "距离 {km} 公里", "{km} km jauhnya", "{km} கி.மீ தொலைவில்"),
    "walk_from": ("{min} min walk from {station}", "距离 {station} 步行 {min} 分钟",
                  "{min} minit berjalan kaki dari {station}", "{station}-இலிருந்து நடை {min} நிமிடம்"),
    "stalls_count": ("{food} food stalls · {market} market stalls", "{food} 个熟食摊 · {market} 个巴刹摊位",
                     "{food} gerai makanan · {market} gerai pasar",
                     "{food} உணவுக் கடைகள் · {market} சந்தைக் கடைகள்"),
    "next_clean": ("Next cleaning: {date}", "下次清洁：{date}", "Pembersihan seterusnya: {date}",
                   "அடுத்த சுத்தம்: {date}"),
    "no_more_clean": ("No more cleaning dates in 2026", "2026 年内已无清洁日期",
                      "Tiada lagi tarikh pembersihan pada 2026", "2026-இல் மேலும் சுத்தம் தேதிகள் இல்லை"),
    "works_2026": ("Other works: {start} to {end}", "其他工程：{start} 至 {end}",
                   "Kerja lain: {start} hingga {end}", "பிற பணிகள்: {start} முதல் {end} வரை"),
    "no_data": ("The hawker centre data file is missing.", "找不到小贩中心数据文件。",
                "Fail data pusat penjaja tiada.", "ஹாக்கர் நிலையத் தரவுக் கோப்பு இல்லை."),
}


def cur_lang():
    return st.session_state.get("lang", "en")


def t(key, **kw):
    text = TR[key][LANGS.index(cur_lang())]
    return text.format(**kw) if kw else text


def fmt_date(d):
    """d is a date / datetime / Timestamp. Month names follow the chosen language."""
    lang = cur_lang()
    if lang == "zh":
        return f"{d.year}年{d.month}月{d.day}日"
    return f"{d.day} {MONTHS[lang][d.month - 1]} {d.year}"


def today_sg():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Asia/Singapore")).date()
    except Exception:
        return date.today()


# =====================================================================
# VISUAL HELPERS (icons, divider)
# =====================================================================
@st.cache_data
def b64_file(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def icon_html(name, size=40):
    path = os.path.join(ICONS, f"{name}.svg")
    if not os.path.exists(path):
        return ""
    return (f"<img src='data:image/svg+xml;base64,{b64_file(path)}' width='{size}' height='{size}' "
            f"class='icon' alt=''>")


def section_title(text, icon):
    st.markdown(f"<div class='sec'>{icon_html(icon, 40)}<h3>{text}</h3></div>", unsafe_allow_html=True)


def divider():
    path = os.path.join(ASSETS, "divider.svg")
    if os.path.exists(path):
        st.markdown(f"<img class='wave' src='data:image/svg+xml;base64,{b64_file(path)}' alt=''>",
                    unsafe_allow_html=True)
    else:
        st.divider()


# =====================================================================
# STATE
# =====================================================================
st.session_state.setdefault("lang", "en")
st.session_state.setdefault("fsize", DEFAULT_SIZE)
st.session_state.setdefault("view", "landing")
st.session_state.setdefault("seller_uen", None)
st.session_state.setdefault("subs", [])      # visitor's subscribed stall UENs

# =====================================================================
# STYLE  (fun font, bigger text, transitions)
# =====================================================================
bg = b64_file(os.path.join(ASSETS, "background.jpg"))
pct = SIZES.get(st.session_state.fsize, 125)

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;700&family=Noto+Sans+Tamil:wght@400;700&display=swap');

    html {{ font-size: {pct}% !important; }}

    /* fun rounded font (falls back to Noto for Chinese / Tamil) */
    .stApp, .stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
    .stApp button, .stApp input, .stApp textarea, .stApp a,
    .stApp [data-baseweb="select"] div, .stApp [data-testid="stMetricValue"],
    .stApp [data-testid="stMetricLabel"], .stApp [role="tab"], .stApp table {{
        font-family: 'Fredoka', 'Noto Sans SC', 'Noto Sans Tamil', sans-serif !important;
    }}

    [data-testid="stHeader"] {{ background: transparent; }}
    .stApp {{ background: url(data:image/jpeg;base64,{bg}) center / cover fixed; }}
    .block-container {{
        max-width: 1000px; margin-top: 2rem; padding: 2rem 2.5rem 2.5rem;
        background: {CREAM}; border: 4px solid {INK}; border-radius: 32px;
        box-shadow: 10px 10px 0 {INK};
    }}
    .stApp p, .stApp label {{ color: {INK}; }}

    .title {{ text-align:center; font-size:4rem; font-weight:700; letter-spacing:4px;
             color:{INK}; margin:0; line-height:1.1; }}
    .title span {{ color:{PINK}; display:inline-block; animation: wiggle 2.4s ease-in-out infinite; }}
    .tagline {{ text-align:center; font-size:1.25rem; color:{INK}; margin:.3rem 0 1.5rem; }}
    .role-name {{ text-align:center; font-size:1.5rem; font-weight:600; color:{INK}; margin:.2rem 0 0; }}
    .role-desc {{ text-align:center; color:{INK}; opacity:.8; margin:0 0 .6rem; }}
    .card-icon {{ text-align:center; }}
    .page-title {{ font-size:2rem; font-weight:700; color:{INK}; margin:0; }}
    .page-sub {{ color:{INK}; opacity:.8; margin:0 0 1rem; }}
    .sec {{ display:flex; align-items:center; gap:.7rem; margin:.6rem 0 .3rem; }}
    .sec h3 {{ margin:0; padding:0; color:{INK}; font-weight:600; }}
    .wave {{ width:100%; height:18px; margin:.8rem 0; display:block; }}
    .chip {{ display:inline-block; padding:.15rem .8rem; border-radius:999px; font-weight:600;
            border:2px solid {INK}; font-size:.85rem; }}
    .chip.done {{ background:#E5E1E3; }}
    .chip.now {{ background:{PINK}; color:white; }}
    .chip.upcoming {{ background:#CFE3F7; }}
    .chip.tbc {{ background:#FFE9A8; }}

    /* role / menu cards */
    [class*="st-key-card_blue"], [class*="st-key-card_pink"] {{
        border: 3px solid {INK}; border-radius: 24px; padding: 1rem; margin-bottom: .6rem;
        transition: transform .2s ease, box-shadow .2s ease;
    }}
    [class*="st-key-card_blue"] {{ background: #EAF3FC; }}
    [class*="st-key-card_pink"] {{ background: #FDEBF0; }}
    [class*="st-key-card_blue"]:hover, [class*="st-key-card_pink"]:hover {{
        transform: translateY(-6px) scale(1.01); box-shadow: 6px 8px 0 {INK};
    }}
    [class*="st-key-card_"] [data-testid="stImage"] {{ display:flex; justify-content:center; }}

    /* buttons: keys starting with b_ are blue, p_ are pink */
    [class*="st-key-b_"] button, [class*="st-key-p_"] button,
    [data-testid="stLinkButton"] a {{
        color: white !important; font-weight: 600; border: 3px solid {INK};
        border-radius: 999px; box-shadow: 3px 3px 0 {INK};
        transition: transform .15s ease, box-shadow .15s ease, filter .15s ease;
    }}
    [class*="st-key-b_"] button {{ background: {BLUE}; }}
    [class*="st-key-p_"] button {{ background: {PINK}; }}
    [data-testid="stLinkButton"] a {{ background: {BLUE}; }}
    [class*="st-key-b_"] button:hover, [class*="st-key-p_"] button:hover,
    [data-testid="stLinkButton"] a:hover {{
        filter: brightness(1.08); color: white; border-color: {INK}; transform: translateY(-2px);
        box-shadow: 3px 5px 0 {INK};
    }}
    [class*="st-key-b_"] button:active, [class*="st-key-p_"] button:active,
    [data-testid="stLinkButton"] a:active {{ transform: translate(2px, 2px); box-shadow: 1px 1px 0 {INK}; }}

    /* entrance animations (play whenever a page or card appears) */
    @keyframes fadeUp {{ from {{ opacity:0; transform: translateY(18px); }} to {{ opacity:1; transform:none; }} }}
    @keyframes bob {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-8px); }} }}
    @keyframes wiggle {{ 0%,100% {{ transform: rotate(-6deg); }} 50% {{ transform: rotate(6deg) scale(1.15); }} }}
    .title, .tagline, .page-title, .page-sub, .sec, .wave {{ animation: fadeUp .5s ease both; }}
    [class*="st-key-card_"] {{ animation: fadeUp .55s ease both; }}
    [data-testid="stColumn"]:nth-child(2) [class*="st-key-card_"] {{ animation-delay: .12s; }}
    [data-testid="stVerticalBlockBorderWrapper"] {{ animation: fadeUp .45s ease both; }}
    [data-testid="stTabs"] {{ animation: fadeUp .45s ease both; }}
    [class*="st-key-card_"] [data-testid="stImage"] img,
    [class*="st-key-mascot_"] img {{ animation: bob 3.2s ease-in-out infinite; }}

    /* respect people who prefer no motion */
    @media (prefers-reduced-motion: reduce) {{
        * {{ animation: none !important; transition: none !important; }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =====================================================================
# NAVIGATION HELPERS
# =====================================================================
def go(view):
    st.session_state.view = view


def logout():
    st.session_state.seller_uen = None
    st.session_state.view = "seller_home"


def top_bar():
    left, right = st.columns([1.3, 1], vertical_alignment="center")
    left.radio(t("text_size"), list(SIZES.keys()), key="fsize", horizontal=True)
    right.selectbox(t("language"), LANGS, key="lang", format_func=lambda c: LANG_NAMES[c])


def page_header(title, subtitle, mascot, back_to, back_label_key="back", key="x"):
    prefix = "b" if mascot == "haw_bo" else "p"
    st.button(t(back_label_key), key=f"{prefix}_back_{key}", on_click=go, args=(back_to,))
    c1, c2 = st.columns([1, 6], vertical_alignment="center")
    with c1:
        with st.container(key=f"mascot_{key}"):
            st.image(os.path.join(ASSETS, f"{mascot}.png"), width=110)
    c2.markdown(f"<p class='page-title'>{title}</p><p class='page-sub'>{subtitle}</p>",
                unsafe_allow_html=True)


def menu_card(color, key, icon, title, desc, button_label, on_click=None, args=(), link=None):
    """A card with an icon, title, description and one button."""
    prefix = "b" if color == "blue" else "p"
    with st.container(key=f"card_{color}_{key}"):
        st.markdown(f"<div class='card-icon'>{icon_html(icon, 72)}</div>", unsafe_allow_html=True)
        st.markdown(f"<p class='role-name'>{title}</p>", unsafe_allow_html=True)
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


@st.cache_data
def load_hawkers():
    """Hawker centre data (cleaning dates, other works, location, nearest MRT)."""
    if not os.path.exists(HAWKER_FILE):
        return None
    df = pd.read_csv(HAWKER_FILE)
    for col in [c for c in df.columns if c.endswith("date")]:
        df[col] = pd.to_datetime(df[col], format="%d/%m/%y", errors="coerce")
    return df


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
        left, right = st.columns([3, 1.5], vertical_alignment="center")
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
            st.markdown(f"<p class='role-name'>{t('seller')}</p>", unsafe_allow_html=True)
            st.markdown(f"<p class='role-desc'>{t('seller_desc')}</p>", unsafe_allow_html=True)
            st.button(t("btn_seller"), key="b_seller", use_container_width=True,
                      on_click=go, args=("seller_home",))
    with c2:
        with st.container(key="card_pink_visitor"):
            st.image(os.path.join(ASSETS, "haw_sim.png"), width=230)
            st.markdown(f"<p class='role-name'>{t('visitor')}</p>", unsafe_allow_html=True)
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
        menu_card("blue", "bid", "bid", t("bid_title"), t("bid_desc"), t("bid_btn"), link=NEA_URL)
    with c2:
        menu_card("blue", "login", "login", t("login_title"), t("login_desc"), t("login_title"),
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
    section_title(t("post_title"), "megaphone")
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

    divider()
    section_title(t("public_bc"), "news")
    posts = load_posts()
    if not posts:
        st.info(t("no_posts_seller"))
    for p in posts:
        render_post(p, "seller", owner_uen=uen)


def seller_calculator(uen):
    section_title(t("add_entry"), "plus")
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

    divider()
    section_title(t("your_numbers"), "chart")
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
        ("fav", "star", "fav_title", "fav_desc", "v_fav"),
        ("sched", "calendar", "sched_title", "sched_desc", "v_sched"),
        ("near", "pin", "near_title", "near_desc", "v_near"),
        ("news", "news", "news_title", "news_desc", "v_news"),
    ]
    for i in range(0, len(items), 2):
        cols = st.columns(2, gap="large")
        for col, (key, icon, title, desc, target) in zip(cols, items[i:i + 2]):
            with col:
                menu_card("pink", key, icon, t(title), t(desc), t("open"),
                          on_click=go, args=(target,))


def visitor_favourites():
    page_header(t("fav_title"), t("fav_sub"), "haw_sim", "visitor_home", key="v_fav")
    subs = st.session_state.subs

    section_title(t("your_favs"), "star")
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
        section_title(t("from_favs"), "megaphone")
        for p in fav_posts:
            render_post(p, "fav", show_subscribe=True)
    if other_posts:
        section_title(t("discover"), "search")
        for p in other_posts:
            render_post(p, "other", show_subscribe=True)


# ---------- Hawker Schedule (uses hawker_centres_final.csv) ----------
QUARTERS = ["q1", "q2", "q3", "q4"]


def quarter_status(start, end, today):
    if pd.isna(start) or pd.isna(end):
        return "tbc"
    if end.date() < today:
        return "done"
    if start.date() <= today <= end.date():
        return "now"
    return "upcoming"


def chip(status):
    return f"<span class='chip {status}'>{t('st_' + status)}</span>"


def upcoming_cleaning(hc, today, days=30):
    rows = []
    limit = today + timedelta(days=days)
    for _, r in hc.iterrows():
        for q in QUARTERS:
            s, e = r[f"{q}_cleaningstartdate"], r[f"{q}_cleaningenddate"]
            if pd.isna(s) or pd.isna(e):
                continue
            if e.date() >= today and s.date() <= limit:
                rows.append({"name": r["name"], "start": s, "end": e,
                             "days": int(r[f"{q}_days"]) if not pd.isna(r[f"{q}_days"]) else None})
    return pd.DataFrame(rows).sort_values("start") if rows else pd.DataFrame()


def visitor_schedule():
    page_header(t("sched_title"), t("sched_desc"), "haw_sim", "visitor_home", key="v_sched")
    hc = load_hawkers()
    tab1, tab2 = st.tabs([t("tab_clean"), t("tab_closure")])
    today = today_sg()

    with tab1:
        if hc is None:
            st.warning(t("no_data"))
        else:
            section_title(t("soon_title"), "sparkle")
            soon = upcoming_cleaning(hc, today)
            if soon.empty:
                st.info(t("none_soon"))
            else:
                st.dataframe(pd.DataFrame({
                    t("col_centre"): soon["name"],
                    t("col_from"): soon["start"].apply(fmt_date),
                    t("col_to"): soon["end"].apply(fmt_date),
                    t("col_days"): soon["days"],
                }), hide_index=True, use_container_width=True)

            divider()
            section_title(t("find_centre"), "search")
            names = sorted(hc["name"].tolist())
            choice = st.selectbox(t("select_centre"), names, label_visibility="collapsed")
            row = hc[hc["name"] == choice].iloc[0]
            if bool(row["closed_all_2026"]):
                st.warning(t("closed_2026"))
            cols = st.columns(2)
            for i, q in enumerate(QUARTERS):
                s, e = row[f"{q}_cleaningstartdate"], row[f"{q}_cleaningenddate"]
                status = quarter_status(s, e, today)
                with cols[i % 2]:
                    with st.container(border=True):
                        st.markdown(f"**{t('quarter', n=i + 1)}**")
                        if status == "tbc":
                            st.write("—")
                        elif s == e:
                            st.write(fmt_date(s))
                        else:
                            st.write(f"{fmt_date(s)} → {fmt_date(e)}")
                        st.markdown(chip(status), unsafe_allow_html=True)
            if bool(row["other_works_in_2026"]):
                st.info(t("works_2026", start=fmt_date(row["other_works_startdate"]),
                          end=fmt_date(row["other_works_enddate"])))
            st.caption(t("data_note"))

    with tab2:
        if hc is not None:
            section_title(t("long_closures"), "lock")
            works = hc[hc["other_works_in_2026"] | hc["closed_all_2026"]].sort_values("other_works_startdate")
            if works.empty:
                st.info(t("no_works"))
            else:
                st.dataframe(pd.DataFrame({
                    t("col_centre"): works["name"],
                    t("col_from"): works["other_works_startdate"].apply(fmt_date),
                    t("col_to"): works["other_works_enddate"].apply(fmt_date),
                }), hide_index=True, use_container_width=True)
            divider()

        section_title(t("stall_closures"), "megaphone")
        closures = [p for p in load_posts() if p.get("closure_start")]
        if not closures:
            st.info(t("none_stall_closures"))
        for p in closures:
            with st.container(border=True):
                st.markdown(f"**{p['stall']}** · {p['centre']}")
                st.warning(t("closed_range",
                             start=fmt_date(datetime.fromisoformat(p["closure_start"])),
                             end=fmt_date(datetime.fromisoformat(p["closure_end"]))))


# ---------- Nearby Hawker (uses hawker_centres_final.csv) ----------
def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


@st.cache_data(ttl=3600)
def onemap_search(query):
    """Look up a Singapore postal code / place using OneMap (free public search)."""
    url = ("https://www.onemap.gov.sg/api/common/elastic/search?" +
           urllib.parse.urlencode({"searchVal": query, "returnGeom": "Y",
                                   "getAddrDetails": "Y", "pageNum": 1}))
    try:
        with urllib.request.urlopen(url, timeout=8) as resp:
            data = json.load(resp)
        return [{"label": r.get("ADDRESS") or r.get("SEARCHVAL"),
                 "lat": float(r["LATITUDE"]), "lon": float(r["LONGITUDE"])}
                for r in data.get("results", [])[:6]]
    except Exception:
        return None


def get_user_location():
    """Returns (lat, lon) or None."""
    mode = st.radio(t("where_are_you"), ["place", "gps"], horizontal=True,
                    format_func=lambda k: t("opt_place") if k == "place" else t("opt_gps"),
                    label_visibility="collapsed")
    if mode == "place":
        q = st.text_input(t("opt_place"), placeholder=t("place_ph"), label_visibility="collapsed")
        if q.strip():
            results = onemap_search(q.strip())
            if not results:
                st.error(t("place_err"))
                return None
            labels = [r["label"] for r in results]
            idx = 0
            if len(results) > 1:
                pick = st.selectbox(t("pick_result"), labels)
                idx = labels.index(pick)
            return results[idx]["lat"], results[idx]["lon"]
        return None

    # GPS mode (needs the optional streamlit-geolocation package)
    try:
        from streamlit_geolocation import streamlit_geolocation
    except Exception:
        st.info(t("gps_missing"))
        return None
    st.caption(t("gps_hint"))
    try:
        loc = streamlit_geolocation()
        if loc and loc.get("latitude") and loc.get("longitude"):
            return float(loc["latitude"]), float(loc["longitude"])
    except Exception:
        st.info(t("gps_missing"))
    return None


def visitor_nearby():
    page_header(t("near_title"), t("near_desc"), "haw_sim", "visitor_home", key="v_near")
    hc = load_hawkers()
    if hc is None:
        st.warning(t("no_data"))
        return
    today = today_sg()

    section_title(t("where_are_you"), "pin")
    user = get_user_location()

    # distances
    hc = hc.copy()
    nearest = pd.DataFrame()
    if user:
        hc["km"] = hc.apply(lambda r: haversine_km(user[0], user[1], r["latitude_hc"], r["longitude_hc"]), axis=1)
        nearest = hc.nsmallest(5, "km")

    # map
    divider()
    section_title(t("map_title"), "map")
    pts = pd.DataFrame({"lat": hc["latitude_hc"], "lon": hc["longitude_hc"],
                        "color": PINK, "size": 120})
    if not nearest.empty:
        pts.loc[nearest.index, "color"] = "#D62839"
        pts.loc[nearest.index, "size"] = 260
        pts = pd.concat([pts, pd.DataFrame([{"lat": user[0], "lon": user[1],
                                             "color": BLUE, "size": 320}])], ignore_index=True)
    st.map(pts, latitude="lat", longitude="lon", color="color", size="size", height=420)
    st.caption(t("legend"))

    if nearest.empty:
        return

    divider()
    section_title(t("nearest"), "pin")
    for _, r in nearest.iterrows():
        with st.container(border=True):
            st.markdown(f"**{r['name']}**")
            st.caption(r["address_myenv"])
            st.write(t("km_away", km=f"{r['km']:.1f}"))
            station = str(r["STATION_NA"]).title().replace(" Mrt", " MRT").replace(" Lrt", " LRT")
            st.write(t("walk_from", min=int(round(r["walk_min"])), station=station))
            st.write(t("stalls_count", food=int(r["no_of_food_stalls"]), market=int(r["no_of_market_stalls"])))

            nxt = None
            for q in QUARTERS:
                s = r[f"{q}_cleaningstartdate"]
                if not pd.isna(s) and s.date() >= today:
                    nxt = s if nxt is None or s < nxt else nxt
            if bool(r["closed_all_2026"]):
                st.warning(t("closed_2026"))
            elif nxt is not None:
                st.write(t("next_clean", date=fmt_date(nxt)))
            else:
                st.write(t("no_more_clean"))
            if bool(r["other_works_in_2026"]) and not bool(r["closed_all_2026"]):
                st.info(t("works_2026", start=fmt_date(r["other_works_startdate"]),
                          end=fmt_date(r["other_works_enddate"])))


def coming_soon(title, subtitle, note, key):
    page_header(title, subtitle, "haw_sim", "visitor_home", key=key)
    st.info(note)


# =====================================================================
# ROUTER
# =====================================================================
top_bar()

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
    visitor_nearby()
elif view == "v_news":
    coming_soon(t("news_title"), t("news_sub"), t("soon"), "v_news")
else:
    go("landing")
    st.rerun()
