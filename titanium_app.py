import streamlit as st
import pandas as pd
import requests
import json
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="TITANIUM V34.2 COMMAND", layout="wide", page_icon="⚡")

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

# --- STATS ENGINE (REQUIRED FOR LOGIC) ---
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
        dfs = pd.read_html(url, header=1)
        df = dfs[0]
        df = df[df['TEAM'] != 'TEAM']
        for _, row in df.iterrows():
            try:
                name = row['TEAM']
                pace = float(row['PACE'])
                off = float(row['OFF'])
                deff = float(row['DEF'])
                db[name] = {"NetRtg": off - deff, "Pace": pace}
            except: continue
        if len(db) > 20: return db
    except: pass
    
    # LEVEL 2: STATIC BACKUP (2026 CONTEXT)
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
    """
    return []

# --- MAPPING HELPER ---
def get_team_stats(name, db):
    # Map ESPN Scoreboard Names to Hollinger/DB Names
    mapping = {
        "LA Clippers": "L.A. Clippers", "Los Angeles Clippers": "L.A. Clippers",
        "LA Lakers": "L.A. Lakers", "Los Angeles Lakers": "L.A. Lakers"
    }
    target = mapping.get(name, name)
    if target in db: return db[target]
    # Fuzzy
    mascot = name.split()[-1]
    for k in db:
        if mascot in k: return db[k]
    return None

# --- GATEKEEPER LOGIC ---
class TitaniumGatekeeper:
    def __init__(self, config, stats_db):
        self.config = config
        self.stats_db = stats_db
        self.bans = ["Milwaukee Bucks", "Pittsburgh Penguins"]

    def audit_game(self, event):
        approved_bets = []
        try:
            matchup_id = event['id']
            short_name = event['shortName']
            comp = event['competitions'][0]
            
            # Teams
            home = next(c for c in comp['competitors'] if c['homeAway'] == 'home')
            away = next(c for c in comp['competitors'] if c['homeAway'] == 'away')
            h_name = home['team']['displayName']
            a_name = away['team']['displayName']
            
            # 1. BANS
            if any(b in h_name for b in self.bans) or any(b in a_name for b in self.bans):
                return []

            # 2. TITANIUM SCORE CALC
            h_st = get_team_stats(h_name, self.stats_db)
            a_st = get_team_stats(a_name, self.stats_db)
            
            t_edge_side = None
            t_edge_val = 0.0
            
            if h_st and a_st:
                h_score = (h_st['NetRtg'] * (h_st['Pace']/100)) + 1.5 # Home Court
                a_score = (a_st['NetRtg'] * (a_st['Pace']/100))
                delta = h_score - a_score
                
                if delta > 3.0: 
                    t_edge_side = "HOME"
                    t_edge_val = abs(delta)
                elif delta < -3.0: 
                    t_edge_side = "AWAY"
                    t_edge_val = abs(delta)

            # 3. ODDS PARSING
            if not comp.get('odds'): return []
            odds_obj = comp['odds'][0]
            
            # --- EVALUATE SPREAD ---
            try:
                spread_str = odds_obj.get('details', '0')
                parts = spread_str.split(" ")
                fav_abbr = parts[0]
                spread_val = float(parts[1])
                
                # Determine Target Team
                target_team = h_name if home['team']['abbreviation'] == fav_abbr else a_name
                target_side = "HOME" if target_team == h_name else "AWAY"
                
                # Logic: Only bet if Titanium Edge aligns
                if t_edge_side and t_edge_side == target_side:
                    # Blowout Shield
                    if abs(spread_val) <= 10.5:
                         # Default -110 if missing (ESPN generic structure often omits juice on summary)
                        price = "-110" 
                        approved_bets.append({
                            "Sport": "NBA",
                            "Matchup": short_name,
                            "Type": "Spread",
                            "Target": f"{target_team} {spread_val}",
                            "Odds": price,
                            "Logic": f"Titanium Edge {t_edge_val:.1f} | Ban Check Passed"
                        })
            except: pass

            # --- EVALUATE MONEYLINE ---
            try:
                # ESPN Logic: homeTeamOdds.moneyLine / awayTeamOdds.moneyLine
                h_ml = odds_obj.get('homeTeamOdds', {}).get('moneyLine')
                a_ml = odds_obj.get('awayTeamOdds', {}).get('moneyLine')
                
                if h_ml and t_edge_side == "HOME":
                    if h_ml > -200: # Article 4/30
                        approved_bets.append({
                            "Sport": "NBA",
                            "Matchup": short_name,
                            "Type": "Moneyline",
                            "Target": f"{h_name} ML",
                            "Odds": str(h_ml),
                            "Logic": f"Titanium Edge {t_edge_val:.1f} | ML Value > -200"
                        })
                
                if a_ml and t_edge_side == "AWAY":
                     if a_ml > -200:
                        approved_bets.append({
                            "Sport": "NBA",
                            "Matchup": short_name,
                            "Type": "Moneyline",
                            "Target": f"{a_name} ML",
                            "Odds": str(a_ml),
                            "Logic": f"Titanium Edge {t_edge_val:.1f} | ML Value > -200"
                        })
            except: pass
            
        except: pass
        return approved_bets

# --- MAIN UI ---
def main():
    st.title("⚡ TITANIUM V34.2 COMMAND")
    
    # 1. Config & Sidebar
    config = load_v34_protocol()
    if config: st.sidebar.success("BRAIN: ONLINE")
    else: st.sidebar.error("BRAIN: OFFLINE")
    
    sport_selection = st.sidebar.selectbox("Select Protocol", ["NBA", "NFL", "NHL", "NCAAB", "SOCCER"])
    
    # 2. Logic Flow
    if sport_selection == "NBA":
        if st.button("EXECUTE TITANIUM SEQUENCE"):
            with st.spinner("RUNNING V34 AUDIT..."):
                stats_db = fetch_nba_stats()
                raw_data = get_nba_scoreboard()
                
                if raw_data:
                    gatekeeper = TitaniumGatekeeper(config, stats_db)
                    ledger = []
                    
                    for event in raw_data['events']:
                        bets = gatekeeper.audit_game(event)
                        ledger.extend(bets)
                        
                        # Placeholder for future prop integration
                        props = scan_player_props(event['id'])
                        ledger.extend(props)
                    
                    if ledger:
                        st.success(f"TARGETS ACQUIRED: {len(ledger)}")
                        df = pd.DataFrame(ledger)
                        # ENFORCE EXACT COLUMN ORDER
                        cols = ["Sport", "Matchup", "Type", "Target", "Odds", "Logic"]
                        st.dataframe(df[cols], use_container_width=True)
                    else:
                        st.warning("MARKET EFFICIENT. NO BETS SURVIVED.")
                else:
                    st.error("API CONNECTION FAILED")
                    
    else:
        st.warning(f"TITANIUM_{sport_selection} UNDER CONSTRUCTION. AWAITING MANIFEST.")

if __name__ == "__main__":
    main()
