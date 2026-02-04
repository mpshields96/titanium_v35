import streamlit as st
import pandas as pd
import requests
import json
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="TITANIUM V34.3 COMMAND", layout="wide", page_icon="⚡")

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

# --- NBA STATS ENGINE (NBA ONLY) ---
@st.cache_data(ttl=3600)
def fetch_nba_stats():
    """Retrieves NetRtg and Pace for NBA Titanium Score Calculation."""
    db = {}
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
    
    # STATIC BACKUP
    return {
        "Boston Celtics": {"NetRtg": 9.5, "Pace": 98.5},
        "Oklahoma City Thunder": {"NetRtg": 8.2, "Pace": 101.0},
        "Denver Nuggets": {"NetRtg": 5.5, "Pace": 97.5},
        "New York Knicks": {"NetRtg": 4.8, "Pace": 96.5},
        "Milwaukee Bucks": {"NetRtg": -1.5, "Pace": 102.0},
        "L.A. Lakers": {"NetRtg": 1.2, "Pace": 100.5}
    }

# --- MULTI-SPORT API ---
def get_live_data(sport):
    """Hits ESPN Hidden API based on Sport Selection."""
    urls = {
        "NBA": "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard",
        "NHL": "https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard",
        "NCAAB": "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
    }
    url = urls.get(sport)
    if not url: return None
    
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        return r.json() if r.status_code == 200 else None
    except: return None

# --- HELPER: TEAM MAPPING ---
def get_nba_team_stats(name, db):
    mapping = {
        "LA Clippers": "L.A. Clippers", "Los Angeles Clippers": "L.A. Clippers",
        "LA Lakers": "L.A. Lakers", "Los Angeles Lakers": "L.A. Lakers"
    }
    target = mapping.get(name, name)
    if target in db: return db[target]
    mascot = name.split()[-1]
    for k in db:
        if mascot in k: return db[k]
    return None

# --- GATEKEEPER LOGIC ---
class TitaniumGatekeeper:
    def __init__(self, config, stats_db):
        self.config = config
        self.stats_db = stats_db # Only used for NBA
        self.bans = ["Milwaukee Bucks", "Pittsburgh Penguins"]

    def _get_provider(self, odds_obj):
        """Extracts sportsbook name."""
        try:
            return odds_obj.get('provider', {}).get('name', 'Consensus')
        except: return "Consensus"

    def audit_game(self, event, sport):
        """Router for Sport-Specific Logic."""
        if sport == "NBA":
            return self.audit_nba(event)
        elif sport == "NHL":
            return self.audit_nhl(event)
        elif sport == "NCAAB":
            return self.audit_ncaab(event)
        return []

    # --- NBA LOGIC ---
    def audit_nba(self, event):
        approved = []
        try:
            short_name = event['shortName']
            comp = event['competitions'][0]
            home = next(c for c in comp['competitors'] if c['homeAway'] == 'home')
            away = next(c for c in comp['competitors'] if c['homeAway'] == 'away')
            h_name, a_name = home['team']['displayName'], away['team']['displayName']

            # BANS
            if any(b in h_name for b in self.bans) or any(b in a_name for b in self.bans): return []

            # TITANIUM SCORE
            h_st, a_st = get_nba_team_stats(h_name, self.stats_db), get_nba_team_stats(a_name, self.stats_db)
            t_edge = None
            if h_st and a_st:
                h_sc = (h_st['NetRtg'] * (h_st['Pace']/100)) + 1.5
                a_sc = (a_st['NetRtg'] * (a_st['Pace']/100))
                delta = h_sc - a_sc
                if delta > 3.0: t_edge = "HOME"
                elif delta < -3.0: t_edge = "AWAY"

            if not comp.get('odds'): return []
            odds_obj = comp['odds'][0]
            provider = self._get_provider(odds_obj)

            # SPREAD
            try:
                spread_str = odds_obj.get('details', '0')
                parts = spread_str.split(" ")
                fav_abbr, spread_val = parts[0], float(parts[1])
                target_team = h_name if home['team']['abbreviation'] == fav_abbr else a_name
                target_side = "HOME" if target_team == h_name else "AWAY"

                if t_edge and t_edge == target_side and abs(spread_val) <= 10.5:
                    approved.append({
                        "Sport": "NBA", "Matchup": short_name, "Bet_Type": "Spread",
                        "Team_Target": target_team, "Line": str(spread_val),
                        "Price": str(odds_obj.get('price', -110)), "Sportsbook": provider,
                        "Logic": "V34 Edge | Blowout Check Passed"
                    })
            except: pass
            
            # MONEYLINE
            try:
                h_ml = float(odds_obj.get('homeTeamOdds', {}).get('moneyLine', -9999))
                a_ml = float(odds_obj.get('awayTeamOdds', {}).get('moneyLine', -9999))
                if t_edge == "HOME" and h_ml > -200:
                    approved.append({"Sport": "NBA", "Matchup": short_name, "Bet_Type": "Moneyline", "Team_Target": h_name, "Line": "ML", "Price": str(h_ml), "Sportsbook": provider, "Logic": "V34 Edge | ML Value"})
                if t_edge == "AWAY" and a_ml > -200:
                    approved.append({"Sport": "NBA", "Matchup": short_name, "Bet_Type": "Moneyline", "Team_Target": a_name, "Line": "ML", "Price": str(a_ml), "Sportsbook": provider, "Logic": "V34 Edge | ML Value"})
            except: pass

        except: pass
        return approved

    # --- NHL LOGIC (NEW) ---
    def audit_nhl(self, event):
        approved = []
        try:
            short_name = event['shortName']
            comp = event['competitions'][0]
            home = next(c for c in comp['competitors'] if c['homeAway'] == 'home')
            away = next(c for c in comp['competitors'] if c['homeAway'] == 'away')
            h_name, a_name = home['team']['displayName'], away['team']['displayName']

            # RULE 1: PENGUINS BAN
            if "Penguins" in h_name or "Penguins" in a_name: return []

            if not comp.get('odds'): return []
            odds_obj = comp['odds'][0]
            provider = self._get_provider(odds_obj)

            # PARSE MONEYLINES
            try:
                h_ml = float(odds_obj.get('homeTeamOdds', {}).get('moneyLine', -9999))
                a_ml = float(odds_obj.get('awayTeamOdds', {}).get('moneyLine', -9999))
                
                # RULE 2: PUCK LINE SAFETY (-200 Barrier)
                # Analyze HOME
                if h_ml < -200:
                    # Must find Puck Line -1.5 (Spread in NHL is PL)
                    spread_str = odds_obj.get('details', '0') # e.g. "PIT -1.5"
                    if "-1.5" in spread_str and home['team']['abbreviation'] in spread_str:
                         approved.append({"Sport": "NHL", "Matchup": short_name, "Bet_Type": "Puck Line", "Team_Target": h_name, "Line": "-1.5", "Price": str(odds_obj.get('price', -110)), "Sportsbook": provider, "Logic": "Safety Valve Active (ML < -200) | Verify Goalie > .910 SV%"})
                elif -200 <= h_ml <= 150: # Odds Collar
                     approved.append({"Sport": "NHL", "Matchup": short_name, "Bet_Type": "Moneyline", "Team_Target": h_name, "Line": "ML", "Price": str(h_ml), "Sportsbook": provider, "Logic": "Odds Collar Pass | Verify Goalie > .910 SV%"})

                # Analyze AWAY
                if a_ml < -200:
                    spread_str = odds_obj.get('details', '0')
                    if "-1.5" in spread_str and away['team']['abbreviation'] in spread_str:
                         approved.append({"Sport": "NHL", "Matchup": short_name, "Bet_Type": "Puck Line", "Team_Target": a_name, "Line": "-1.5", "Price": str(odds_obj.get('price', -110)), "Sportsbook": provider, "Logic": "Safety Valve Active (ML < -200) | Verify Goalie > .910 SV%"})
                elif -200 <= a_ml <= 150:
                     approved.append({"Sport": "NHL", "Matchup": short_name, "Bet_Type": "Moneyline", "Team_Target": a_name, "Line": "ML", "Price": str(a_ml), "Sportsbook": provider, "Logic": "Odds Collar Pass | Verify Goalie > .910 SV%"})

            except: pass
        except: pass
        return approved

    # --- NCAAB LOGIC (NEW) ---
    def audit_ncaab(self, event):
        approved = []
        try:
            short_name = event['shortName']
            comp = event['competitions'][0]
            if not comp.get('odds'): return []
            odds_obj = comp['odds'][0]
            provider = self._get_provider(odds_obj)
            
            # SPREAD LOGIC
            try:
                spread_str = odds_obj.get('details', '0') # "DUKE -3.5"
                parts = spread_str.split(" ")
                spread_val = float(parts[1])
                team_abbr = parts[0]
                
                # Resolve Team Name
                home = next(c for c in comp['competitors'] if c['homeAway'] == 'home')
                target_name = home['team']['displayName'] if home['team']['abbreviation'] == team_abbr else next(c for c in comp['competitors'] if c['homeAway'] == 'away')['team']['displayName']

                # RULE 1: CLOSERS METRIC
                logic_note = "V34 Approved"
                if -4.5 <= spread_val <= -0.5:
                    logic_note = "⚠️ CLOSERS METRIC: Audit FT% > 71%"

                # Odds Collar Check on Spread Price
                price = float(odds_obj.get('price', -110))
                if -180 <= price <= 150:
                    approved.append({
                        "Sport": "NCAAB", "Matchup": short_name, "Bet_Type": "Spread",
                        "Team_Target": target_name, "Line": str(spread_val),
                        "Price": str(price), "Sportsbook": provider, "Logic": logic_note
                    })
            except: pass
        except: pass
        return approved

# --- PLAYER PROP PLACEHOLDER ---
def scan_player_props(game_id):
    """## PROP MODULE PENDING ##"""
    return []

# --- MAIN UI ---
def main():
    st.sidebar.title("TITANIUM V34.3 COMMAND")
    sport = st.sidebar.selectbox("PROTOCOL SELECTION", ["NBA", "NHL", "NCAAB", "NFL (Offseason)"])
    
    config = load_v34_protocol()
    if config: st.sidebar.success("BRAIN: ONLINE")
    else: st.sidebar.error("BRAIN: OFFLINE")
    
    st.title(f"⚡ TITANIUM V34.3 | {sport}")
    
    if sport in ["NBA", "NHL", "NCAAB"]:
        if st.button("EXECUTE TITANIUM SEQUENCE"):
            with st.spinner(f"AUDITING {sport} MARKETS..."):
                raw_data = get_live_data(sport)
                
                if raw_data:
                    # NBA gets stats DB, others get None
                    stats_db = fetch_nba_stats() if sport == "NBA" else None
                    
                    gatekeeper = TitaniumGatekeeper(config, stats_db)
                    ledger = []
                    
                    for event in raw_data['events']:
                        bets = gatekeeper.audit_game(event, sport)
                        ledger.extend(bets)
                        scan_player_props(event['id']) # Placeholder
                    
                    if ledger:
                        st.success(f"TARGETS ACQUIRED: {len(ledger)}")
                        df = pd.DataFrame(ledger)
                        cols = ["Sport", "Matchup", "Bet_Type", "Team_Target", "Line", "Price", "Sportsbook", "Logic"]
                        st.dataframe(df[cols], use_container_width=True, hide_index=True)
                    else:
                        st.warning("MARKET EFFICIENT. NO BETS SURVIVED.")
                else:
                    st.error("API CONNECTION FAILED")
    else:
        st.info("PROTOCOL OFFLINE.")

if __name__ == "__main__":
    main()
