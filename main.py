import streamlit as st
from streamlit_option_menu import option_menu
import sqlite3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from PIL import Image
import io
import atexit
import sys
import os
import base64
import numpy as np
import pandas as pd
import altair as alt
from concurrent.futures import ThreadPoolExecutor
from collections import Counter 


# // class 
class DatabaseManager:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance.init_connection()
        return cls._instance

    def init_connection(self):
        try:
            self.conn = sqlite3.connect("database.db", check_same_thread=False)
            self.cursor = self.conn.cursor()
            atexit.register(self.close_connection)
            self.init_db()
        except sqlite3.Error as e:
            st.error(f"Database initialization error: {e}")
            sys.exit(1)

    def init_db(self):
        try:
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS airdrops (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    status TEXT,
                    category TEXT,
                    website TEXT,
                    twitter TEXT,
                    telegram TEXT,
                    instagram TEXT,
                    discord TEXT,
                    wallet TEXT,
                    notes TEXT)''')
            self.conn.commit()
        except sqlite3.Error as e:
            st.error(f"Table creation error: {e}")

    def execute_query(self, query, params=None):
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor
        except sqlite3.Error as e:
            st.error(f"Query execution error: {e}")
            return None

    def commit(self):
        try:
            self.conn.commit()
        except sqlite3.Error as e:
            st.error(f"Commit error: {e}")

    def close_connection(self):
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
                st.info("Database connection closed.")
        except Exception as e:
            st.error(f"Error closing database: {e}")


db_manager = DatabaseManager()


st.set_page_config(
    page_title="Garapan Empire",
    layout="wide",
    initial_sidebar_state="collapsed"
)


st.markdown("""
<style>
    @import url('https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css');
     
    /* Target semua elemen utama */
    * {
        font-family: 'Maple' !important;
    }
    
    /* Target khusus untuk option menu di sidebar */
    div[data-testid="stSidebar"] * {
        font-family: 'Maple' !important;
    }
    
    /* Target item menu */
    .st-cm, .st-cx, .st-cy {
        font-family: 'Maple' !important;
    }
    
    /* Target hover state */
    div[role="button"]:hover > div[data-testid="stMarkdownContainer"] > p {
        font-family: 'Maple' !important;
    }
    
    /* Target menu aktif */
    .st-eb .st-ec {
        font-family: 'Maple' !important;
    }
    
    .social-icon i {
        font-size: 1.2rem;
        vertical-align: middle;
        margin-right: 10px;
        color: #6c757d;
    }
    
    .website-icon {
        max-width: 20px;
        margin-right: 16px;
    }

    .centered-title {
        text-align: center;
    }
    .stApp {
        background-image: url('static/wp/wallpaper.jpg');
        background-size: cover;
    }
</style>
""", unsafe_allow_html=True)


def load_custom_font():
    try:
        font_path = os.path.join('static', 'fonts', 'maple.otf')
        
        if not os.path.exists(font_path):
            st.error("⚠️ Font file not found!")
            return ""
            
        with open(font_path, "rb") as f:
            font_data = base64.b64encode(f.read()).decode()
            
        return f"""
        <style>
            @font-face {{
                font-family: 'Maple';
                src: url(data:font/ttf;charset=utf-8;base64,{font_data}) format('truetype');
                font-weight: bold;
                font-style: bold;
            }}
            
            /* Apply ke semua elemen */
            * {{
                font-family: 'Maple' !important;
            }}
            
            /* Komponen khusus Streamlit */
            .stTextInput input,
            .stSelectbox select,
            .stTextArea textarea,
            .stNumberInput input,
            .stDateInput input,
            .stMultiSelect div div div,
            .stButton>button {{
                font-family: 'Maple' !important;
            }}
            
            /* Header */
            h1, h2, h3, h4, h5, h6 {{
                font-weight: 700 !important;
            }}
            
            /* Social icons */
            .social-icon {{
                margin: 8px 0;
                padding: 10px;
                border-radius: 5px;
                transition: all 0.3s ease;
            }}
            
            .social-icon:hover {{
                background-color: #f0f2f6;
                transform: translateX(5px);
            }}
        </style>
        """
    except Exception as e:
        st.error(f"🚨 Error loading font: {e}")
        return ""



st.markdown(load_custom_font(), unsafe_allow_html=True)


def get_website_icon(url: str):
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        favicon_url = urljoin(base_url, "/favicon.ico")
        response = requests.get(favicon_url, timeout=5)
        if response.status_code == 200:
            return favicon_url
        
        response = requests.get(base_url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        icon_links = soup.find_all('link', rel=lambda x: x and x.lower() in ['icon', 'shortcut icon', 'apple-touch-icon'])
        
        best_icon = None
        max_size = 0
        for icon in icon_links:
            sizes = icon.get('sizes', '32x32')
            size = int(sizes.split('x')[0]) if sizes else 32
            href = icon.get('href')
            
            if size > max_size:
                max_size = size
                best_icon = href
        
        return urljoin(base_url, best_icon) if best_icon else favicon_url
    
    except Exception as e:
        st.warning(f"Could not retrieve favicon: {e}")
        return None

def social_link(platform: str, url: str):
    if not url:
        return

    icons = {
        "Twitter": "bi-twitter",
        "Telegram": "bi-telegram",
        "Instagram": "bi-instagram",
        "Discord": "bi-discord",
        "Wallet": "bi-wallet2"
    }

    col1, col2 = st.columns([0.02, 0.85])
    with col1:
        st.markdown(f'<i class="bi {icons[platform]}"></i>', unsafe_allow_html=True)
    with col2:
        st.markdown(f"[{platform}]({url})")

# // sidebar ...
with st.sidebar:
    selected = option_menu(
    menu_title="",
    options=["Dashboard", "All Airdrops", "Add New", "Search & Edit"],
    icons=["rocket", "list-task", "plus-circle", "search"],
    menu_icon="rocket",
    orientation="vertical",
    styles={
            "nav-link": {"font-family": "Maple !important", "font-size": "18px"},
            "nav-item": {"padding": "16px"},
            "menu_title": {"font-size": "24px", "color": "blue"},
        },
    default_index=0,
)

if selected == "Dashboard":
    st.title("📊 Garapan Dashboard")

    col1, col2, col3 = st.columns(3)
    with col1:
        cursor = db_manager.execute_query("SELECT COUNT(*) FROM airdrops")
        total_airdrops = cursor.fetchone()[0] if cursor else 0
        st.metric("Total Airdrops", total_airdrops)
    with col2:
        cursor = db_manager.execute_query("SELECT COUNT(*) FROM airdrops WHERE status='Selesai'")
        completed_airdrops = cursor.fetchone()[0] if cursor else 0
        st.metric("Selesai", completed_airdrops)
    with col3:
        cursor = db_manager.execute_query("SELECT COUNT(*) FROM airdrops WHERE status!='Selesai'")
        pending_airdrops = cursor.fetchone()[0] if cursor else 0
        st.metric("Lainnya", pending_airdrops)

    st.markdown("---")
    st.subheader("Distribusi Kategori Airdrop")

    query = "SELECT category FROM airdrops"
    cursor = db_manager.execute_query(query)
    rows = cursor.fetchall() if cursor else []

    kategori_list = []
    for row in rows:
        if row[0]:
            cats = [cat.strip() for cat in row[0].split(",") if cat.strip()]
            kategori_list.extend(cats)

    kategori_counter = Counter(kategori_list)

    if not kategori_counter:
        st.info("Belum ada data kategori Garapan.")
    else:
        df = pd.DataFrame.from_dict(kategori_counter, orient='index', columns=['Count'])
        df = df.reset_index().rename(columns={'index': 'Category'})
        df = df.sort_values("Category")
        chart = alt.Chart(df).mark_bar(size=30).encode(
            x=alt.X('Category:N', sort=None, title='Kategori'),
            y=alt.Y('Count:Q', title='Jumlah Garapan'),
            color=alt.Color('Category:N', scale=alt.Scale(scheme='category10')),
            tooltip=['Category', 'Count']
        ).properties(
            width=750,
            height=400,
            title="kategori Garapan"
        )

        st.altair_chart(chart, use_container_width=True)


elif selected == "All Airdrops":
    st.title("📋 All Garapan")

    cursor = db_manager.execute_query("SELECT * FROM airdrops")
    data = cursor.fetchall() if cursor else []

    def load_icons():
        if 'icons' not in st.session_state or len(st.session_state.icons) != len(data):
            import concurrent.futures
            import requests
            import io
            from PIL import Image
            
            st.session_state.icons = {}
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def fetch_icon(url):
                try:
                    icon_url = get_website_icon(url)
                    if icon_url:
                        response = requests.get(icon_url, timeout=3)
                        return (url, Image.open(io.BytesIO(response.content)))
                    return (url, None)
                except Exception as e:
                    return (url, e)

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = {executor.submit(fetch_icon, airdrop[4]): airdrop[4] for airdrop in data}
                
                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    url = futures[future]
                    try:
                        result = future.result()
                        st.session_state.icons[result[0]] = result[1]
                    except:
                       expanderst.session_state.icons[url] = None
                    
                    progress = (i + 1) / len(data)
                    progress_bar.progress(progress)
                    status_text.info(f"Memuat {i+1}/{len(data)} database...")
            
            progress_bar.empty()
            status_text.empty()
    if data:
        load_icons()

    for airdrop in data:
        with st.expander(f"{airdrop[1]} - {airdrop[2]}"):
            cols = st.columns([0.04, 0.85])
            url = airdrop[4]

            with cols[0]:
                if url in st.session_state.icons:
                    icon = st.session_state.icons[url]
                    if isinstance(icon, Exception):
                        st.error("Gagal memuat ikon")
                    elif icon:
                        st.image(icon, width=40)
                else:
                    st.write("🌐")
            
            with cols[1]:
                st.markdown(f"### <span style='font-size:20px; font-weight:bold;'>{airdrop[1]}</span>", unsafe_allow_html=True)
                st.caption(f"**Status**: {airdrop[2]} | **Kategori**: {airdrop[3]}")
                socials = {
                    5: "Twitter",
                    6: "Telegram",
                    7: "Instagram",
                    8: "Discord",
                    9: "Wallet"                }

                for idx, platform in socials.items():
                    if airdrop[idx]:
                        social_link(platform, airdrop[idx])

                if airdrop[10]:
                    st.markdown("**Catatan:**")
                    st.code(airdrop[10], language="markdown")

elif selected == "Add New":
    st.title("🆕 Add New Garapan")

    with st.form("add_airdrop", clear_on_submit=True):
        name = st.text_input("Project Name*", placeholder="Enter project name")
        status = st.selectbox("Status*", ["Selesai", "Delay", "Belum Berjalan","Sedang Berjalan"])
        category = st.multiselect("Category", ["Whitelist", "Testnet", "Social Media", "Web", "Depin", "Light Node","Mini Apps"])
        website = st.text_input("Website URL*", placeholder="https://")
        twitter = st.text_input("Twitter handler", placeholder="@")
        telegram = st.text_input("Telegram handler", placeholder="@")
        instagram = st.text_input("Instagram handler", placeholder="@")
        discord = st.text_input("Discord handler", placeholder="@")
        wallet = st.text_input("Wallet Address", placeholder="Wallet Address")
        notes = st.text_area("Notes", height=150)

        submitted = st.form_submit_button("💾 Save Airdrop")

        if submitted:
            if not name or not website:
                st.error("Please fill required fields (*)")
            else:
                db_manager.execute_query(
                    "INSERT INTO airdrops (name, status, category, website, twitter, telegram, instagram, discord, wallet, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (name, status, ",".join(category), website, twitter, telegram, instagram, discord, wallet, notes) # Ditambahkan wallet
                )
                db_manager.commit()
                st.success("Airdrop saved successfully!")


elif selected == "Search & Edit":
    st.title("🔍 Search & Edit Garapan")    
    search_query = st.text_input("Search by name", placeholder="Type project name...")
    if search_query:
        cursor = db_manager.execute_query("SELECT * FROM airdrops WHERE name LIKE ?", (f"%{search_query}%",))
        results = cursor.fetchall() if cursor else []
        
        for airdrop in results:
            with st.expander(f"{airdrop[1]} - {airdrop[2]}"):
                with st.form(f"edit_{airdrop[0]}"):
                    name = st.text_input("Project Name", airdrop[1])
                    status = st.selectbox("Status", ["Selesai", "Delay", "Belum Berjalan","Sedang Berjalan"], 
                                        index=["Selesai", "Delay", "Belum Berjalan","Sedang Berjalan"].index(airdrop[2]))
                    category = st.multiselect("Category", ["Whitelist", "Testnet", "Social Media", "Web", "Mini Apps", "Depin", "Light Node"], 
                                            default=airdrop[3].split(","))
                    website = st.text_input("Website URL", airdrop[4])
                    twitter = st.text_input("Twitter URL", airdrop[5])
                    telegram = st.text_input("Telegram URL", airdrop[6])
                    instagram = st.text_input("Instagram URL", airdrop[7])
                    discord = st.text_input("Discord URL", airdrop[8])
                    wallet =  st.text_input("Wallet URL", airdrop[9])
                    notes = st.text_area("Notes", airdrop[10])
                    
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        update_btn = st.form_submit_button("🔄 Update")
                    with col2:
                        delete_btn = st.form_submit_button("🗑️ Delete")

                    if update_btn:
                        db_manager.execute_query(
                            """UPDATE airdrops SET
                            name=?, status=?, category=?, website=?, 
                            twitter=?, telegram=?, instagram=?, discord=?, wallet=?, notes=? # Ditambahkan wallet
                            WHERE id=?""",
                            (name, status, ",".join(category), website, 
                             twitter, telegram, instagram, discord, wallet, notes, airdrop[0])
                        )
                        db_manager.commit()
                        st.success("Updated successfully!")

                    if delete_btn:
                        db_manager.execute_query("DELETE FROM airdrops WHERE id=?", (airdrop[0],))
                        db_manager.commit()
                        st.warning("Airdrop deleted!")

if st.sidebar.button("Close Database Connection"):
    db_manager.close_connection()
