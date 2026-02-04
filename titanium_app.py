import streamlit as st
import pandas as pd
import requests
from originator_engine import TitaniumOriginator

# --- PAGE CONFIG ---
st.set_page_config(page_title="TITANIUM V32", layout="wide", page_icon="⚡")

# --- CSS FOR "SMOOTH BRAIN" DARK MODE ---
st.markdown("""
<style>
    .stApp {background-color: #0E1117;}
    div.stButton > button {width: 100%; background-color: #00FF00; color: black; font-weight: bold;}
    [data-testid="stMetricValue"] {font-size: 2rem;}
</style>
""", unsafe_allow_html=True)

# --- INITIALIZE ENGINE ---
originator = TitaniumOriginator()

# --- SECRETS HANDLING (CLOUD SUPPORT) ---
# On Streamlit Cloud, keys live in st.secrets. locally, they might not exist.
try:
    API_KEY = st.secrets["ODDS_API_KEY"]
except:
    API_KEY = st.sidebar.text_input("ENTER API KEY", type="password")

# --- CACHED DATA FETCH ---
@st.cache_data(ttl=300) # Cache for 5 mins
def fetch_odds(sport, _key):
    if not _key: return None
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
    params = {'apiKey': _key, 'regions': 'us', 'markets': 'h2h,spreads', 'oddsFormat': 'american'}
    try:
        return requests.get(url, params=params).json()
    except: return []

# --- MAIN UI ---
st.title("⚡ TITANIUM V32")
st.caption("NEMESIS PROTOCOL | CLOUD DEPLOYMENT")

tab_scan, tab_math = st.tabs(["📡 SCANNER", "🧬 ORIGINATOR"])

with tab_scan:
    st.header("MARKET SCAN")
    sport = st.selectbox("TARGET", ["basketball_nba", "icehockey_nhl", "soccer_epl", "basketball_ncaab"], index=0)

    if st.button("EXECUTE SCAN"):
        if not API_KEY:
            st.error("API KEY MISSING.")
        else:
            with st.spinner("SCANNING..."):
                data = fetch_odds(sport, API_KEY)
                if data:
                    rows = []
                    for g in data:
                        try:
                            book = g['bookmakers'][0]
                            rows.append({
                                "Matchup": f"{g['away_team']} @ {g['home_team']}",
                                "Book": book['title'],
                                "Line": book['markets'][0]['outcomes'][0]['price']
                            })
                        except: continue
                    st.dataframe(pd.DataFrame(rows), use_container_width=True)
                else:
                    st.error("NO DATA / API ERROR")

with tab_math:
    st.header("THE ORIGINATOR")

    calc_type = st.radio("ENGINE", ["TRINITY (NBA)", "ATOMIC (NHL/SOCCER)"], horizontal=True)

    if calc_type == "TRINITY (NBA)":
        c1, c2 = st.columns(2)
        mean = c1.number_input("Proj Mean", 25.0)
        std = c2.number_input("Std Dev", 6.0)
        line = st.number_input("Vegas Line", 24.5)

        if st.button("RUN TRINITY"):
            prob = originator.run_trinity_simulation(mean, std, line)
            edge = prob - 0.524

            st.metric("Titanium Prob", f"{prob*100:.1f}%", delta=f"{edge*100:.1f}% Edge")

            if edge > 0.05:
                st.success("🚨 NUCLEAR EDGE DETECTED")
            else:
                st.warning("NO SIGNIFICANT EDGE")

    else:
        c1, c2 = st.columns(2)
        h_xg = c1.number_input("Home xG", 1.5)
        a_xg = c2.number_input("Away xG", 1.2)

        if st.button("RUN ATOMIC"):
            hw, dr, aw = originator.run_poisson_matrix(h_xg, a_xg)
            c1, c2, c3 = st.columns(3)
            c1.metric("Home", f"{hw*100:.1f}%")
            c2.metric("Draw", f"{dr*100:.1f}%")
            c3.metric("Away", f"{aw*100:.1f}%")