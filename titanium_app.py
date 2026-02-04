import streamlit as st
import pandas as pd
import requests
import json
import os
from originator_engine import TitaniumOriginator

# --- PAGE CONFIG ---
st.set_page_config(page_title="TITANIUM V34 COMMAND", layout="wide", page_icon="⚡")

# --- CSS STYLING ---
st.markdown("""
<style>
    .stApp {background-color: #0E1117;}
    div.stButton > button {width: 100%; background-color: #00FF00; color: black; font-weight: bold; border: none;}
    .metric-card {background-color: #262730; padding: 15px; border-radius: 8px; border-left: 5px solid #00FF00;}
</style>
""", unsafe_allow_html=True)

# --- INITIALIZE ---
originator = TitaniumOriginator()

# --- LOAD V34 BRAIN ---
@st.cache_data
def load_v34_brain():
    try:
        if os.path.exists("titanium_v34.json"):
            with open("titanium_v34.json", "r") as f:
                return json.load(f)
        return None
    except: return None

v34_logic = load_v34_brain()

# --- LIVE DATA ENGINE (ESPN SCRAPER) ---
@st.cache_data(ttl=3600)
def fetch_nba_stats():
    """
    SECTION IV: SCRAPES LIVE DATA FROM ESPN.
    Bypasses nba_api IP blocks by reading simple HTML tables.
    """
    try:
        # ESPN Advanced Stats URL
        url = "https://www.espn.com/nba/stats/team/_/view/advanced"
        
        # User-Agent header to look like a real browser (prevents 403 Forbidden)
        header = {
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Read HTML tables
        dfs = pd.read_html(url, storage_options=header)
        
        # ESPN splits the table into two (Team Names in [0], Stats in [1])
        # We merge them.
        names_df = dfs[0]
        stats_df = dfs[1]
        full_df = pd.concat([names_df, stats_df], axis=1)
        
        db = {}
        for _, row in full_df.iterrows():
            # ESPN Team Names are sometimes "1 Boston Celtics" (numbered). We clean them.
            raw_name = str(row.iloc[0]) # "1 Boston Celtics"
            # Remove rank number if present
            clean_name = ''.join([i for i in raw_name if not i.isdigit()]).strip().replace(".", "")
            
            # Extract Metrics (NetRtg, Pace)
            # ESPN Columns: RK, TEAM, GP, W, L, OFF, DEF, NET, PACE...
            # We map by column name logic or index. 
            # Usually: OFF=5, DEF=6, NET=7, PACE=8 (0-indexed)
            
            try:
                # Find NET and PACE by column headers if possible, else index
                net_rtg = float(row['NET'])
                pace = float(row['PACE'])
                
                # TITANIUM SCORE FORMULA
                t_score = net_rtg * (pace / 100)
                
                db[clean_name] = {
                    "TitaniumScore": t_score,
                    "NetRtg": net_rtg,
                    "Pace": pace
                }
            except: continue
            
        return db
    except Exception as e:
        return {} # Return empty on failure to trigger safe mode

nba_db = fetch_nba_stats()

# --- MAPPING BRIDGE (ODDS API -> ESPN) ---
def get_titanium_stats(odds_api_name, stats_db):
    # Normalize Odds API name
    norm_name = odds_api_name.replace(".", "") # "L.A. Lakers" -> "LA Lakers"
    
    # Direct Key Check
    if norm_name in stats_db: return stats_db[norm_name]
    
    # Fuzzy Match (e.g. "LA Clippers" vs "Los Angeles Clippers")
    # We match the LAST word (Mascot). "Clippers" == "Clippers"
    mascot = norm_name.split()[-1]
    
    for db_key in stats_db.keys():
        if mascot in db_key:
            return stats_db[db_key]
            
    return None

# --- MATH UTILS ---
def implied_prob(odds):
    return 100 / (odds + 100) if odds > 0 else abs(odds) / (abs(odds) + 100)

def calculate_kelly(odds, true_win_prob):
    dec = (100 / implied_prob(odds)) if odds > 0 else (1 + (100/abs(odds)))
    b = dec - 1
    p = true_win_prob
    if b == 0: return 0.0
    f = (b * p - (1-p)) / b
    return max(0.0, min(f * 0.25 * 100, 2.0)) # Quarter Kelly, Max 2u

# --- V34 AUDIT ---
def audit_game_v34(game, sport, logic, stats_db):
    approved = []
    try:
        home, away = game['home_team'], game['away_team']
        book = next((b for b in game['bookmakers'] if b['key'] in ['draftkings', 'fanduel', 'mgm']), game['bookmakers'][0])

        # BANS
        if home in ["Milwaukee Bucks", "Pittsburgh Penguins"] or away in ["Milwaukee Bucks", "Pittsburgh Penguins"]: return []

        # SECTION IV (NBA)
        t_edge = None
        t_conf = 0.0
        
        if sport == "basketball_nba":
            h_st, a_st = get_titanium_stats(home, stats_db), get_titanium_stats(away, stats_db)
            
            # CRITICAL: If Scraper Failed or Map Failed, KILL BET. NO GUESSING.
            if not h_st or not a_st: return [] 
            
            h_score = h_st['TitaniumScore'] + 1.5 # Home Court
            a_score = a_st['TitaniumScore']
            delta = h_score - a_score
            
            if delta > 3.0: 
                t_edge = "HOME"
                t_conf = abs(delta)
            elif delta < -3.0: 
                t_edge = "AWAY"
                t_conf = abs(delta)
            else: return [] # Neutral -> Kill

        for market in book['markets']:
            if market['key'] == 'spreads':
                for outcome in market['outcomes']:
                    name, price, point = outcome['name'], outcome['price'], outcome['point']
                    
                    if price < -180 or price > 150: continue
                    
                    status = "✅ V34 APPROVED"
                    if abs(point) > 10.5: status = "⚠️ BLOWOUT RISK"

                    if sport == "basketball_nba":
                        if t_edge == "HOME" and name != home: continue
                        if t_edge == "AWAY" and name != away: continue

                    units = calculate_kelly(price, implied_prob(price) + (t_conf/100))
                    if units > 0.05:
                        approved.append({
                            "Matchup": f"{away} @ {home}",
                            "Target": name,
                            "Bet": f"Spread {point}",
                            "Odds": price,
                            "Kelly": f"{units:.2f}u",
                            "Status": status
                        })
    except: return []
    return approved

# --- UI ---
st.title("⚡ TITANIUM V34 COMMAND")
try: API_KEY = st.secrets["ODDS_API_KEY"]
except: API_KEY = st.sidebar.text_input("ENTER API KEY", type="password")

# DIAGNOSTICS
if len(nba_db) > 20: st.sidebar.success(f"ESPN FEED: {len(nba_db)} TEAMS")
else: st.sidebar.error("ESPN FEED: FAILURE (Check Logs)")

tab_scan, tab_math = st.tabs(["📡 V34 SCANNER", "🧬 ORIGINATOR"])
with tab_scan:
    if st.button("EXECUTE TITANIUM SEQUENCE"):
        if not API_KEY: st.error("KEY MISSING")
        else:
            with st.spinner("SCRAPING ESPN & AUDITING MARKETS..."):
                # Fetch Odds
                try: 
                    odds_data = requests.get(f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds", params={'apiKey': API_KEY, 'regions': 'us', 'markets': 'h2h,spreads', 'oddsFormat': 'american'}).json()
                except: odds_data = []
                
                if odds_data:
                    ledger = []
                    for g in odds_data:
                        for b in audit_game_v34(g, "basketball_nba", v34_logic, nba_db): ledger.append(b)
                    if ledger:
                        st.success(f"TARGETS: {len(ledger)}")
                        st.dataframe(pd.DataFrame(ledger), use_container_width=True)
                    else: st.warning("NO BETS SURVIVED V34 AUDIT.")
                else: st.error("ODDS API FAILED")
