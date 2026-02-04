import streamlit as st
import pandas as pd
import requests
import json
import os
import time
import numpy as np
from nba_api.stats.endpoints import leaguedashteamstats
from originator_engine import TitaniumOriginator

# --- PAGE CONFIG ---
st.set_page_config(page_title="TITANIUM V34 COMMAND", layout="wide", page_icon="⚡")

# --- CSS STYLING (SMOOTH BRAIN) ---
st.markdown("""
<style>
    .stApp {background-color: #0E1117;}
    div.stButton > button {width: 100%; background-color: #00FF00; color: black; font-weight: bold; border: none;}
    .metric-card {background-color: #262730; padding: 15px; border-radius: 8px; border-left: 5px solid #00FF00;}
    .risk-alert {color: #FF4B4B; font-weight: bold;}
    .safe-bet {color: #00FF00; font-weight: bold;}
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

# --- LIVE DATA ENGINE (NBA API) ---
@st.cache_data(ttl=3600)
def fetch_nba_stats():
    """
    SECTION IV & XXXIV: Retrieves Live Efficiency Metrics.
    """
    try:
        stats = leaguedashteamstats.LeagueDashTeamStats(season='2025-26').get_data_frames()[0]
        db = {}
        for _, row in stats.iterrows():
            name = row['TEAM_NAME']
            # TITANIUM SCORE = (NetRtg) * (Pace / 100)
            t_score = row['NET_RATING'] * (row['PACE'] / 100)
            
            db[name] = {
                "TitaniumScore": t_score,
                "NetRtg": row['NET_RATING'],
                "Pace": row['PACE'],
                "FT_Pct": row['FT_PCT'],       # For Section XXXIV
                "TOV_Pct": row['TM_TOV_PCT'],  # For Section XXXIV
                "Win_Pct": row['W_PCT']        # For Section XIX (Redemption Arc)
            }
        return db
    except: return {}

nba_db = fetch_nba_stats()

# --- HELPER: FUZZY TEAM MATCHING ---
def get_team_data(name, db):
    # Direct match
    if name in db: return db[name]
    # "L.A. Clippers" vs "Los Angeles Clippers"
    mapping = {
        "Los Angeles Clippers": "L.A. Clippers",
        "LA Clippers": "L.A. Clippers",
        "Los Angeles Lakers": "L.A. Lakers",
        "LA Lakers": "L.A. Lakers"
    }
    if name in mapping and mapping[name] in db:
        return db[mapping[name]]
    # Keyword fallback
    for k in db.keys():
        if name.split()[-1] in k: return db[k]
    return None

# --- MATHEMATICAL UTILS (KELLY & EV) ---
def implied_prob(american_odds):
    if american_odds > 0:
        return 100 / (american_odds + 100)
    else:
        return abs(american_odds) / (abs(american_odds) + 100)

def calculate_kelly(odds, true_win_prob, bankroll_fraction=0.25):
    """
    SECTION VI: Fractional Kelly Criterion (0.25x).
    """
    decimal_odds = (100 / implied_prob(odds))
    b = decimal_odds - 1
    p = true_win_prob
    q = 1 - p
    
    if b == 0: return 0.0
    
    f_star = (b * p - q) / b
    kelly_size = f_star * bankroll_fraction
    
    # Cap at 2.0u (10% of Daily Stack implies roughly 2.0u max in V34 logic)
    # V34 says: "Quarter Kelly. HARD CAP is 2.0u"
    if kelly_size < 0: return 0.0
    return min(kelly_size * 100, 2.0) # Assuming 1.0u = 1% risk for simplicity in display

# --- THE V34 LOGIC CORE ---
def audit_game_v34(game, sport, logic, stats_db):
    """
    The Single-Game Logic Gate.
    Input: Raw Game Data.
    Output: List of APPROVED bets with V34 Metadata.
    """
    approved_bets = []
    
    try:
        # 1. IDENTIFY BOOKMAKERS (Sharp vs Soft)
        # We try to find Pinnacle for CLV comparison, else use average
        pinnacle = next((b for b in game['bookmakers'] if b['key'] == 'pinnacle'), None)
        soft_book = next((b for b in game['bookmakers'] if b['key'] in ['draftkings', 'fanduel', 'mgm']), game['bookmakers'][0])
        
        home = game['home_team']
        away = game['away_team']
        
        # 2. BANNED TEAM CHECKS (SECTION XV/XVI)
        # Bucks (Art 16), Penguins (Art 15)
        banned_teams = ["Milwaukee Bucks", "Pittsburgh Penguins"]
        if home in banned_teams or away in banned_teams:
            return [] # HARD BAN
            
        # 3. STATISTICAL EDGE CALCULATION (SECTION IV - NBA)
        t_edge = None # "HOME", "AWAY"
        t_conf = 0.0  # Confidence Score
        
        if sport == "basketball_nba" and stats_db:
            h_stats = get_team_data(home, stats_db)
            a_stats = get_team_data(away, stats_db)
            
            if h_stats and a_stats:
                h_score = h_stats['TitaniumScore'] + 1.5 # Home Court Adjust
                a_score = a_stats['TitaniumScore']
                delta = h_score - a_score
                
                if delta > 4.0: 
                    t_edge = "HOME"
                    t_conf = abs(delta)
                elif delta < -4.0: 
                    t_edge = "AWAY"
                    t_conf = abs(delta)
        
        # 4. MARKET AUDIT
        for market in soft_book['markets']:
            
            # --- MONEYLINE LOGIC ---
            if market['key'] == 'h2h':
                for outcome in market['outcomes']:
                    name = outcome['name']
                    price = outcome['price']
                    
                    # ARTICLE 4: ODDS COLLAR (-180 to +150)
                    if price < -180 or price > 150: continue
                    
                    # SECTION XXX: PUCK LINE SAFETY (NHL)
                    # If NHL ML is valid but "Close to -200", maybe suggest PL?
                    # Logic: If ML is valid here, it's > -180, so it's safe for ML.
                    
                    # SECTION IV FILTER (NBA)
                    if sport == "basketball_nba" and t_edge:
                        if t_edge == "HOME" and name != home: continue
                        if t_edge == "AWAY" and name != away: continue
                        
                    # KELLY SIZING (Approximate Edge)
                    # If we have Pinnacle, calculate CLV Edge
                    clv_edge = 0.0
                    if pinnacle:
                        pin_mkt = next((m for m in pinnacle['markets'] if m['key'] == 'h2h'), None)
                        if pin_mkt:
                            pin_price = next((o['price'] for o in pin_mkt['outcomes'] if o['name'] == name), None)
                            if pin_price:
                                true_prob = implied_prob(pin_price) # Vig-inclusive estimate of "True"
                                my_prob = implied_prob(price)
                                clv_edge = (true_prob - my_prob) * 100 # Rough EV
                    
                    # If no CLV data, use Titanium Confidence for NBA
                    if clv_edge == 0 and sport == "basketball_nba" and t_conf > 0:
                        clv_edge = t_conf # Use score delta as proxy for edge
                        
                    units = calculate_kelly(price, implied_prob(price) + (clv_edge/100))
                    
                    if units > 0.1: # Only show playable bets
                        approved_bets.append({
                            "Matchup": f"{away} @ {home}",
                            "Target": name,
                            "Bet": "Moneyline",
                            "Odds": price,
                            "Kelly (u)": f"{units:.2f}u",
                            "Notes": f"✅ V34 APPROVED"
                        })

            # --- SPREAD LOGIC ---
            if market['key'] == 'spreads':
                for outcome in market['outcomes']:
                    name = outcome['name']
                    price = outcome['price']
                    point = outcome['point']
                    
                    # ARTICLE 4: ODDS COLLAR
                    if price < -180 or price > 150: continue
                    
                    # SECTION XXXII: BLOWOUT SHIELD
                    if abs(point) > 10.5:
                        # Flag, don't ban entirely, but warn
                        note = "⚠️ BLOWOUT RISK"
                    else:
                        note = "✅ V34 APPROVED"

                    # SECTION XXXIV: CLOSERS METRIC (NBA Small Faves)
                    # If Line is -0.5 to -4.5
                    if sport == "basketball_nba" and -4.5 <= point <= -0.5:
                        stats = get_team_data(name, stats_db)
                        if stats:
                            if stats['FT_Pct'] < 0.71 or stats['TOV_Pct'] > 0.18:
                                continue # REJECT: Fails Closers Metric
                                
                    # SECTION IV (NBA Power Score)
                    if sport == "basketball_nba" and t_edge:
                         if t_edge == "HOME" and name != home: continue
                         if t_edge == "AWAY" and name != away: continue

                    approved_bets.append({
                        "Matchup": f"{away} @ {home}",
                        "Target": name,
                        "Bet": f"Spread {point}",
                        "Odds": price,
                        "Kelly (u)": "1.00u", # Standard Flat for spreads usually
                        "Notes": note
                    })
                    
    except Exception as e:
        return []
        
    return approved_bets

# --- API FETCH ---
@st.cache_data(ttl=300)
def fetch_odds(sport, _key):
    if not _key: return None
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
    params = {'apiKey': _key, 'regions': 'us', 'markets': 'h2h,spreads', 'oddsFormat': 'american'}
    try: return requests.get(url, params=params).json()
    except: return []

# --- MAIN UI ---
st.title("⚡ TITANIUM V34 COMMAND")
st.caption("MATH ONLY. NO NARRATIVES. KELLY SCALING ENABLED.")

try:
    API_KEY = st.secrets["ODDS_API_KEY"]
except:
    API_KEY = st.sidebar.text_input("ENTER API KEY", type="password")

if v34_logic:
    st.sidebar.success(f"LOGIC: {v34_logic['TITANIUM_V34_BLOAT_MASTER']['META_HEADER']['VERSION']}")
else:
    st.sidebar.error("CRITICAL: V34 JSON MISSING")

# TABS
tab_scan, tab_math = st.tabs(["📡 V34 SCANNER", "🧬 ORIGINATOR"])

with tab_scan:
    sport_map = {
        "NBA": "basketball_nba", 
        "NHL": "icehockey_nhl", 
        "NFL": "americanfootball_nfl",
        "NCAAB": "basketball_ncaab"
    }
    
    c1, c2 = st.columns([3, 1])
    target = c1.selectbox("TARGET PROTOCOL", list(sport_map.keys()))
    
    if st.button("EXECUTE TITANIUM SEQUENCE"):
        if not API_KEY: st.error("API KEY REQUIRED")
        else:
            with st.spinner("AUDITING MARKET VS V34 IRON LAWS..."):
                data = fetch_odds(sport_map[target], API_KEY)
                
                if data:
                    ledger = []
                    for game in data:
                        # RUN THE GAUNTLET
                        bets = audit_game_v34(game, sport_map[target], v34_logic, nba_db)
                        for b in bets: ledger.append(b)
                    
                    if ledger:
                        df = pd.DataFrame(ledger)
                        st.success(f"IDENTIFIED {len(df)} +EV OPPORTUNITIES")
                        
                        # DISPLAY IN SMOOTH BRAIN TABLE
                        st.dataframe(
                            df,
                            column_config={
                                "Odds": st.column_config.NumberColumn(format="%d"),
                                "Status": st.column_config.TextColumn(width="medium"),
                            },
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.warning("MARKET EFFICIENT. NO BETS SURVIVED AUDIT.")
                else:
                    st.info("NO LIVE GAMES FOUND.")

with tab_math:
    st.header("MANUAL ORIGINATION")
    calc_type = st.radio("ENGINE", ["TRINITY (NBA)", "ATOMIC (NHL)"], horizontal=True)
    
    if calc_type == "TRINITY (NBA)":
        c1, c2 = st.columns(2)
        mean = c1.number_input("Proj Mean", 25.0)
        std = c2.number_input("Std Dev", 6.0)
        line = st.number_input("Vegas Line", 24.5)
        if st.button("RUN TRINITY"):
            prob = originator.run_trinity_simulation(mean, std, line)
            edge = prob - 0.524
            st.metric("Win Probability", f"{prob*100:.1f}%", delta=f"{edge*100:.1f}% Edge")
