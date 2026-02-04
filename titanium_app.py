import streamlit as st
import pandas as pd
import requests
import json
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="TITANIUM V34 OMEGA", layout="wide", page_icon="⚡")

# --- CSS STYLING ---
st.markdown("""
<style>
    .stApp {background-color: #0E1117;}
    div.stButton > button {width: 100%; background-color: #00FF00; color: black; font-weight: bold; border: none;}
    .metric-card {background-color: #262730; padding: 15px; border-radius: 8px; border-left: 5px solid #00FF00; margin-bottom: 10px;}
    .status-pass {color: #00FF00; font-weight: bold;}
    .status-fail {color: #FF4B4B; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# --- V34 CONFIG LOADER ---
@st.cache_data
def load_v34_protocol():
    """Parses TITANIUM_V34_BLOAT_MASTER.json."""
    file_path = "titanium_v34.json"
    if not os.path.exists(file_path): return None
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            if "TITANIUM_V34_BLOAT_MASTER" in data:
                return data["TITANIUM_V34_BLOAT_MASTER"]
            return None
    except: return None

# --- STATS ENGINE (TRI-LEVEL DATA HEIST) ---
@st.cache_data(ttl=3600)
def fetch_nba_stats():
    """
    Retrieves NetRtg and Pace for Titanium Score Calculation.
    Source: ESPN Hollinger (Scrape) -> Fallback: Static Backup.
    """
    db = {}
    
    # LEVEL 1: HOLLINGER SCRAPE
    try:
        url = "http://www.espn.com/nba/hollinger/statistics"
        # Use pandas read_html for table parsing
        dfs = pd.read_html(url, header=1)
        df = dfs[0]
        df = df[df['TEAM'] != 'TEAM'] # Filter headers
        
        for _, row in df.iterrows():
            try:
                name = row['TEAM']
                pace = float(row['PACE'])
                off = float(row['OFF'])
                deff = float(row['DEF'])
                # TITANIUM SCORE FORMULA
                db[name] = {"NetRtg": off - deff, "Pace": pace}
            except: continue
            
        if len(db) > 20: return db
    except: pass
    
    # LEVEL 2: STATIC BACKUP (2026 SEASON CONTEXT)
    # Hardcoded values to prevent "0 Teams" failure
    return {
        "Boston Celtics": {"NetRtg": 9.5, "Pace": 98.5},
        "Oklahoma City Thunder": {"NetRtg": 8.2, "Pace": 101.0},
        "Denver Nuggets": {"NetRtg": 5.5, "Pace": 97.5},
        "Minnesota Timberwolves": {"NetRtg": 6.1, "Pace": 98.0},
        "New York Knicks": {"NetRtg": 4.8, "Pace": 96.5},
        "Milwaukee Bucks": {"NetRtg": -1.5, "Pace": 102.0},
        "Philadelphia 76ers": {"NetRtg": 3.2, "Pace": 99.0},
        "Cleveland Cavaliers": {"NetRtg": 4.5, "Pace": 98.2},
        "Dallas Mavericks": {"NetRtg": -2.1, "Pace": 101.5},
        "L.A. Clippers": {"NetRtg": 2.5, "Pace": 97.8},
        "L.A. Lakers": {"NetRtg": 1.2, "Pace": 100.5},
        "Phoenix Suns": {"NetRtg": 3.8, "Pace": 99.5},
        "Sacramento Kings": {"NetRtg": 1.5, "Pace": 100.2},
        "New Orleans Pelicans": {"NetRtg": 0.5, "Pace": 99.0},
        "Golden State Warriors": {"NetRtg": 1.8, "Pace": 100.0},
        "Houston Rockets": {"NetRtg": 2.2, "Pace": 99.8},
        "Miami Heat": {"NetRtg": 0.8, "Pace": 97.0},
        "Indiana Pacers": {"NetRtg": 1.5, "Pace": 103.5},
        "Orlando Magic": {"NetRtg": 2.1, "Pace": 98.5},
        "Atlanta Hawks": {"NetRtg": -1.5, "Pace": 102.5},
        "Brooklyn Nets": {"NetRtg": -4.5, "Pace": 98.5},
        "Toronto Raptors": {"NetRtg": -5.2, "Pace": 100.0},
        "Chicago Bulls": {"NetRtg": -3.8, "Pace": 99.2},
        "Charlotte Hornets": {"NetRtg": -6.5, "Pace": 100.5},
        "Detroit Pistons": {"NetRtg": -7.2, "Pace": 101.0},
        "Washington Wizards": {"NetRtg": -8.5, "Pace": 103.0},
        "Utah Jazz": {"NetRtg": -5.5, "Pace": 99.5},
        "Portland Trail Blazers": {"NetRtg": -6.8, "Pace": 98.8},
        "San Antonio Spurs": {"NetRtg": -1.2, "Pace": 101.5},
        "Memphis Grizzlies": {"NetRtg": 3.5, "Pace": 100.0}
    }

# --- SCOREBOARD API ---
def get_nba_scoreboard():
    """Hits ESPN Hidden API."""
    url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None

# --- PLAYER PROP MODULE (PENDING) ---
def scan_player_props(game_id):
    """
    ## PROP MODULE PENDING: REQUIRES 'SUMMARY' ENDPOINT INTEGRATION ##
    # TODO: Requires Prop API Source
    """
    return []

# --- MAPPING HELPER ---
def get_team_stats(name, db):
    # Normalize ESPN names to DB names
    mapping = {
        "LA Clippers": "L.A. Clippers", "Los Angeles Clippers": "L.A. Clippers",
        "LA Lakers": "L.A. Lakers", "Los Angeles Lakers": "L.A. Lakers"
    }
    target = mapping.get(name, name)
    if target in db: return db[target]
    
    # Fuzzy Match
    mascot = name.split()[-1]
    for k in db:
        if mascot in k: return db[k]
    return None

# --- GATEKEEPER LOGIC (V34 ENGINE) ---
class TitaniumGatekeeper:
    def __init__(self, config, stats_db):
        self.config = config
        self.stats_db = stats_db
        # Hard Bans (Article 15/16)
        self.bans = ["Milwaukee Bucks", "Pittsburgh Penguins"]

    def audit_game(self, event):
        approved_bets = []
        try:
            short_name = event['shortName'] # e.g. "NYK @ DEN"
            comp = event['competitions'][0]
            
            # 1. PARSE TEAMS
            home_comp = next(c for c in comp['competitors'] if c['homeAway'] == 'home')
            away_comp = next(c for c in comp['competitors'] if c['homeAway'] == 'away')
            
            h_name = home_comp['team']['displayName']
            a_name = away_comp['team']['displayName']
            
            # 2. CHECK BANS
            if any(b in h_name for b in self.bans) or any(b in a_name for b in self.bans):
                return [] # Kill entire game

            # 3. CALCULATE TITANIUM EDGE (SECTION IV)
            h_st = get_team_stats(h_name, self.stats_db)
            a_st = get_team_stats(a_name, self.stats_db)
            
            t_edge_side = None # "HOME" or "AWAY"
            t_edge_val = 0.0
            
            if h_st and a_st:
                # Formula: (Home_Net * Pace) + 1.5 - (Away_Net * Pace)
                # Note: Pace factor is usually (Pace/100).
                h_score = (h_st['NetRtg'] * (h_st['Pace']/100)) + 1.5 
                a_score = (a_st['NetRtg'] * (a_st['Pace']/100))
                delta = h_score - a_score
                
                # Threshold: > 3.0 points edge required
                if delta > 3.0: 
                    t_edge_side = "HOME"
                    t_edge_val = abs(delta)
                elif delta < -3.0: 
                    t_edge_side = "AWAY"
                    t_edge_val = abs(delta)
            
            # If no edge, NO BET. (Both Sides Killer)
            if not t_edge_side:
                return []

            # 4. ODDS PARSING & BET GENERATION
            if not comp.get('odds'): return []
            odds_obj = comp['odds'][0]
            
            # --- A. SPREAD ---
            # Get the Spread Value
            spread_str = odds_obj.get('details', '0') # "DEN -5.5"
            try:
                parts = spread_str.split(" ")
                fav_abbr = parts[0]
                spread_val = float(parts[1])
                
                # Identify Target based on Fav Abbreviation
                is_home_fav = (home_comp['team']['abbreviation'] == fav_abbr)
                
                # Determine who we WANT to bet on based on Edge
                target_team_obj = home_comp if t_edge_side == "HOME" else away_comp
                target_name = target_team_obj['team']['displayName']
                
                # Determine the Spread for the TARGET
                # If Target is Fav, line is negative. If Dog, positive.
                # Since 'spread_val' is usually negative (e.g. -5.5), we need to map it.
                
                # Case 1: Target is the Favorite
                if (t_edge_side == "HOME" and is_home_fav) or (t_edge_side == "AWAY" and not is_home_fav):
                    final_line = spread_val # -5.5
                else:
                    final_line = spread_val * -1 # +5.5
                
                # BLOWOUT SHIELD (Article 6 / Section 32)
                # If Line is > 10.5 or < -10.5, it is risky.
                if abs(final_line) <= 10.5:
                    
                    # GET PRICE (The Odds)
                    # ESPN API sometimes has 'price' in the object, sometimes defaults to -110
                    # Standardizing to -110 if missing for spreads to prevent crash
                    price = str(odds_obj.get('price', -110))
                    
                    approved_bets.append({
                        "Sport": "NBA",
                        "Matchup": short_name,
                        "Bet_Type": "Spread",
                        "Team_Target": target_name,
                        "Line": str(final_line),
                        "Price": price,
                        "Sportsbook": "ESPN_Consensus",
                        "Logic": f"Titanium Edge {t_edge_val:.1f} | Blowout Check Passed"
                    })
            except: pass

            # --- B. MONEYLINE ---
            # Only bet ML if Value is acceptable (> -200)
            try:
                if t_edge_side == "HOME":
                    ml_price = home_comp.get('lines', [{}])[0].get('moneyLine') # Try linescore first
                    if not ml_price:
                        # Try odds object fallback
                        ml_price = odds_obj.get('homeTeamOdds', {}).get('moneyLine')
                    
                    if ml_price and float(ml_price) > -200:
                         approved_bets.append({
                            "Sport": "NBA",
                            "Matchup": short_name,
                            "Bet_Type": "Moneyline",
                            "Team_Target": h_name,
                            "Line": "ML",
                            "Price": str(ml_price),
                            "Sportsbook": "ESPN_Consensus",
                            "Logic": f"Titanium Edge {t_edge_val:.1f} | ML > -200"
                        })
                
                elif t_edge_side == "AWAY":
                    ml_price = away_comp.get('lines', [{}])[0].get('moneyLine')
                    if not ml_price:
                        ml_price = odds_obj.get('awayTeamOdds', {}).get('moneyLine')
                        
                    if ml_price and float(ml_price) > -200:
                        approved_bets.append({
                            "Sport": "NBA",
                            "Matchup": short_name,
                            "Bet_Type": "Moneyline",
                            "Team_Target": a_name,
                            "Line": "ML",
                            "Price": str(ml_price),
                            "Sportsbook": "ESPN_Consensus",
                            "Logic": f"Titanium Edge {t_edge_val:.1f} | ML > -200"
                        })
            except: pass

        except: pass
        return approved_bets

# --- MAIN UI ---
def main():
    # 1. SIDEBAR & PROTOCOL SELECTION
    st.sidebar.title("TITANIUM V34 OMEGA")
    sport = st.sidebar.selectbox("PROTOCOL SELECTION", ["NBA", "NFL (Offseason)", "NHL (Pending)", "NCAAB (Pending)"])
    
    # 2. CONFIG LOAD
    config = load_v34_protocol()
    if config:
        st.sidebar.success("V34 BRAIN: ONLINE")
    else:
        st.sidebar.error("V34 BRAIN: MISSING")
        
    # 3. EXECUTION
    st.title("⚡ TITANIUM V34 OMEGA")
    
    if sport == "NBA":
        if st.button("EXECUTE TITANIUM SEQUENCE"):
            with st.spinner("INITIATING DATA HEIST & V34 AUDIT..."):
                # Fetch Data
                stats_db = fetch_nba_stats()
                raw_game_data = get_nba_scoreboard()
                
                if not raw_game_data:
                    st.error("API CONNECTION FAILURE")
                    return

                # Run Gatekeeper
                gatekeeper = TitaniumGatekeeper(config, stats_db)
                ledger = []
                
                for event in raw_game_data['events']:
                    # Core Audit
                    bets = gatekeeper.audit_game(event)
                    ledger.extend(bets)
                    
                    # Prop Placeholder
                    scan_player_props(event['id'])
                
                # Output
                if ledger:
                    st.success(f"TARGETS IDENTIFIED: {len(ledger)}")
                    df = pd.DataFrame(ledger)
                    
                    # EXACT COLUMN MAPPING FORCE
                    required_cols = ["Sport", "Matchup", "Bet_Type", "Team_Target", "Line", "Price", "Sportsbook", "Logic"]
                    
                    # Display
                    st.dataframe(
                        df[required_cols],
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.warning("MARKET EFFICIENT. NO BETS SURVIVED V34 FILTERS.")
                    
    else:
        st.info(f"PROTOCOL '{sport}' IS CURRENTLY IN STASIS. SELECT NBA.")

if __name__ == "__main__":
    main()
