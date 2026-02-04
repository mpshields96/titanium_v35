import streamlit as st
import pandas as pd
import requests
import json
import os
from originator_engine import TitaniumOriginator

# --- PAGE CONFIG ---
st.set_page_config(page_title="TITANIUM V34 PRIME", layout="wide", page_icon="⚡")

# --- CSS STYLING ---
st.markdown("""
<style>
    .stApp {background-color: #0E1117;}
    div.stButton > button {width: 100%; background-color: #00FF00; color: black; font-weight: bold;}
    .metric-card {background-color: #262730; padding: 10px; border-radius: 5px; margin-bottom: 10px;}
    .pass-check {color: #00FF00; font-weight: bold;}
    .fail-check {color: #FF0000; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# --- INITIALIZE ENGINE ---
originator = TitaniumOriginator()

# --- LOAD V34 BRAIN (BLOAT MASTER) ---
@st.cache_data
def load_v34_brain():
    try:
        if os.path.exists("titanium_v34.json"):
            with open("titanium_v34.json", "r") as f:
                return json.load(f)
        return None
    except Exception as e:
        st.error(f"BRAIN DAMAGE: {e}")
        return None

v34_logic = load_v34_brain()

# --- SECRETS ---
try:
    API_KEY = st.secrets["ODDS_API_KEY"]
except:
    API_KEY = st.sidebar.text_input("ENTER API KEY", type="password")

# --- V34 IRON LAWS IMPLEMENTATION ---
def check_odds_collar(price):
    """
    SECTION_III_THE_IRON_LAWS_REFORGED
    ARTICLE_4_THE_ODDS_COLLAR: STRICT RANGE -180 to +150.
    """
    if price > 0:
        return price <= 150
    else:
        return price >= -180

def check_blowout_filter(spread):
    """
    SECTION_III_THE_IRON_LAWS_REFORGED
    ARTICLE_6_BLOWOUT_FILTER_REDUX & SECTION_XXXII_GARBAGE_TIME_SHIELD
    """
    # Logic: If spread is huge (>10.5), flag it.
    # Note: This is for situational awareness. V34 says 'RAT POISON' is -180 odds, but Section 32 says 10.5 spread.
    if abs(spread) > 10.5:
        return False, "BLOWOUT RISK (Garbage Time Shield)"
    return True, "Safe"

def apply_titanium_filters(game, sport, logic):
    """
    Applies V34 Iron Laws to a single game object.
    DEEP RESEARCH INTEGRATION NOTE: Future phases will add Prop Efficiency checks here.
    """
    approved_bets = []
    
    try:
        book = next((b for b in game['bookmakers'] if b['key'] in ['draftkings', 'fanduel', 'pinnacle']), game['bookmakers'][0])
        
        # 1. Moneyline Audit
        h2h = next((m for m in book['markets'] if m['key'] == 'h2h'), None)
        if h2h:
            for outcome in h2h['outcomes']:
                price = outcome['price']
                name = outcome['name']
                
                # ARTICLE 4: ODDS COLLAR ENFORCEMENT
                if check_odds_collar(price):
                    # SECTION XXX (Puck Line Safety)
                    if sport == "icehockey_nhl" and price < -200:
                        continue 
                    
                    approved_bets.append({
                        "Type": "Moneyline",
                        "Team": name,
                        "Price": price,
                        "Note": "✅ V34 APPROVED"
                    })

        # 2. Spread Audit
        spread = next((m for m in book['markets'] if m['key'] == 'spreads'), None)
        if spread:
            for outcome in spread['outcomes']:
                price = outcome['price']
                point = outcome['point']
                name = outcome['name']
                
                # ARTICLE 4 & ARTICLE 6
                if check_odds_collar(price):
                    is_safe, msg = check_blowout_filter(point)
                    if is_safe:
                        approved_bets.append({
                            "Type": f"Spread {point}",
                            "Team": name,
                            "Price": price,
                            "Note": "✅ V34 APPROVED"
                        })
                    else:
                         # Still listing it but marking as RISKY per Section XXXII
                         approved_bets.append({
                            "Type": f"Spread {point}",
                            "Team": name,
                            "Price": price,
                            "Note": f"⚠️ {msg}"
                        })

    except Exception:
        return []
        
    return approved_bets

# --- CACHED DATA FETCH ---
@st.cache_data(ttl=300)
def fetch_odds(sport, _key):
    if not _key: return None
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
    params = {
        'apiKey': _key,
        'regions': 'us',
        'markets': 'h2h,spreads', 
        'oddsFormat': 'american'
    }
    try:
        return requests.get(url, params=params).json()
    except: return []

# --- MAIN UI ---
st.title("⚡ TITANIUM V34 PRIME")
st.caption("FULL BLOAT MASTER INTEGRATION | SCORCHED EARTH MODE")

if v34_logic:
    st.sidebar.success("V34 BRAIN: ONLINE")
    # Display Version from JSON to prove it loaded the BLOAT MASTER
    version_info = v34_logic["TITANIUM_V34_BLOAT_MASTER"]["META_HEADER"]["VERSION"]
    st.sidebar.caption(f"CORE: {version_info}")
else:
    st.sidebar.error("V34 BRAIN: OFFLINE (JSON MISSING)")

tab_scan, tab_math = st.tabs(["📡 V34 SCANNER", "🧬 ORIGINATOR"])

with tab_scan:
    sport_map = {
        "NBA": "basketball_nba",
        "NHL": "icehockey_nhl",
        "NFL": "americanfootball_nfl",
        "EPL Soccer": "soccer_epl",
        "NCAAB": "basketball_ncaab",
        "Tennis (ATP)": "tennis_atp",
        "MMA": "mma_mixed_martial_arts"
    }
    
    target = st.selectbox("TARGET PROTOCOL", list(sport_map.keys()))
    
    if st.button("EXECUTE V34 SCAN"):
        if not API_KEY:
            st.error("API KEY MISSING.")
        else:
            with st.spinner(f"SCANNING {target} FOR V34 COMPLIANCE..."):
                data = fetch_odds(sport_map[target], API_KEY)
                
                if data:
                    all_targets = []
                    for game in data:
                        valid_plays = apply_titanium_filters(game, sport_map[target], v34_logic)
                        if valid_plays:
                            for play in valid_plays:
                                all_targets.append({
                                    "Matchup": f"{game['away_team']} @ {game['home_team']}",
                                    "Target": play['Team'],
                                    "Bet": play['Type'],
                                    "Odds": play['Price'],
                                    "Status": play['Note']
                                })
                    
                    if all_targets:
                        df = pd.DataFrame(all_targets)
                        st.success(f"TARGETS ACQUIRED: {len(df)}")
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.warning("NO TARGETS PASSED V34 FILTERS (MARKET IS TOXIC OR EMPTY).")  
                else:
                    st.info("NO LIVE GAMES FOUND.")

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
            if edge > 0.05: st.success("🚨 NUCLEAR EDGE DETECTED")
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
