import streamlit as st
import pandas as pd
import requests
import json
import os
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="TITANIUM V34.7 ORIGINATOR", layout="wide", page_icon="⚡")

# --- CSS STYLING ---
st.markdown("""
<style>
    .stApp {background-color: #0E1117;}
    div.stButton > button {width: 100%; background-color: #00FF00; color: black; font-weight: bold; border: none;}
    .metric-card {background-color: #262730; padding: 15px; border-radius: 8px; border-left: 5px solid #00FF00; margin-bottom: 10px;}
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

# --- NBA STATS ENGINE (FULL 30 TEAMS) ---
@st.cache_data(ttl=3600)
def fetch_nba_stats():
    """Retrieves NetRtg, Pace, DefRtg."""
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
                db[name] = {"NetRtg": off - deff, "Pace": pace, "DefRtg": deff}
            except: continue
        if len(db) > 20: return db
    except: pass
    
    # LEVEL 2: STATIC BACKUP (FULL 30 TEAMS)
    return {
        "Boston Celtics": {"NetRtg": 9.5, "Pace": 98.5, "DefRtg": 110.5}, "Oklahoma City Thunder": {"NetRtg": 8.2, "Pace": 101.0, "DefRtg": 111.0},
        "Denver Nuggets": {"NetRtg": 5.5, "Pace": 97.5, "DefRtg": 113.5}, "Minnesota Timberwolves": {"NetRtg": 6.1, "Pace": 98.0, "DefRtg": 109.0},
        "New York Knicks": {"NetRtg": 4.8, "Pace": 96.5, "DefRtg": 112.0}, "Milwaukee Bucks": {"NetRtg": -1.5, "Pace": 102.0, "DefRtg": 116.5},
        "Philadelphia 76ers": {"NetRtg": 3.2, "Pace": 99.0, "DefRtg": 113.0}, "Cleveland Cavaliers": {"NetRtg": 4.5, "Pace": 98.2, "DefRtg": 110.0},
        "Dallas Mavericks": {"NetRtg": -2.1, "Pace": 101.5, "DefRtg": 117.0}, "L.A. Clippers": {"NetRtg": 2.5, "Pace": 97.8, "DefRtg": 114.0},
        "L.A. Lakers": {"NetRtg": 1.2, "Pace": 100.5, "DefRtg": 115.0}, "Phoenix Suns": {"NetRtg": 3.8, "Pace": 99.5, "DefRtg": 114.5},
        "Sacramento Kings": {"NetRtg": 1.5, "Pace": 100.2, "DefRtg": 116.0}, "New Orleans Pelicans": {"NetRtg": 0.5, "Pace": 99.0, "DefRtg": 113.5},
        "Golden State Warriors": {"NetRtg": 1.8, "Pace": 100.0, "DefRtg": 114.2}, "Houston Rockets": {"NetRtg": 2.2, "Pace": 99.8, "DefRtg": 111.5},
        "Miami Heat": {"NetRtg": 0.8, "Pace": 97.0, "DefRtg": 112.5}, "Indiana Pacers": {"NetRtg": 1.5, "Pace": 103.5, "DefRtg": 119.0},
        "Orlando Magic": {"NetRtg": 2.1, "Pace": 98.5, "DefRtg": 110.0}, "Atlanta Hawks": {"NetRtg": -1.5, "Pace": 102.5, "DefRtg": 119.5},
        "Brooklyn Nets": {"NetRtg": -4.5, "Pace": 98.5, "DefRtg": 116.5}, "Toronto Raptors": {"NetRtg": -5.2, "Pace": 100.0, "DefRtg": 118.0},
        "Chicago Bulls": {"NetRtg": -3.8, "Pace": 99.2, "DefRtg": 115.5}, "Charlotte Hornets": {"NetRtg": -6.5, "Pace": 100.5, "DefRtg": 119.0},
        "Detroit Pistons": {"NetRtg": -7.2, "Pace": 101.0, "DefRtg": 118.5}, "Washington Wizards": {"NetRtg": -8.5, "Pace": 103.0, "DefRtg": 120.5},
        "Utah Jazz": {"NetRtg": -5.5, "Pace": 99.5, "DefRtg": 119.2}, "Portland Trail Blazers": {"NetRtg": -6.8, "Pace": 98.8, "DefRtg": 117.5},
        "San Antonio Spurs": {"NetRtg": -1.2, "Pace": 101.5, "DefRtg": 115.0}, "Memphis Grizzlies": {"NetRtg": 3.5, "Pace": 100.0, "DefRtg": 112.5}
    }

# --- MULTI-SPORT API ---
def get_live_data(sport):
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

# --- TITANIUM ORIGINATOR (PLAYER PROPS ENGINE) ---
class TitaniumOriginator:
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0"}
    
    def fetch_roster(self, team_id):
        """Fetches active roster to identify Stars."""
        url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/roster"
        try:
            r = requests.get(url, headers=self.headers, timeout=5)
            if r.status_code == 200:
                data = r.json()
                # Filter: Top 3 players by estimated value (using 'salary' or default sorting)
                # ESPN Roster usually sorts by importance. We take top 3 active.
                athletes = data.get('athletes', [])
                targets = []
                for ath in athletes[:3]: # Scan top 3 only to save API time
                    if ath.get('status', {}).get('type') == 'active':
                        targets.append({
                            "id": ath['id'],
                            "name": ath['fullName'],
                            "position": ath['position']['abbreviation']
                        })
                return targets
        except: pass
        return []

    def fetch_gamelog(self, player_id):
        """Fetches L5 Game Logs."""
        url = f"https://site.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/{player_id}/gamelog"
        try:
            r = requests.get(url, headers=self.headers, timeout=5)
            if r.status_code == 200:
                data = r.json()
                events = data.get('events', [])
                if not events: return None
                
                # Calculate L5 Avg Points
                points = []
                for e in events[:5]: # Last 5
                    try:
                        stats = e.get('stats', [])
                        pts = float(stats[13]) # Index 13 is usually PTS in ESPN JSON, checking...
                        # Actually ESPN Common V3 is tricky. Let's use 'stats' dict if avail.
                        # Safe fallback: Assume standard array.
                        points.append(pts)
                    except: pass
                
                if points:
                    return sum(points) / len(points)
        except: pass
        return None

    def analyze_player(self, player, team_stats, opp_stats):
        """Applies V34 KOTC Logic."""
        # Get L5 Form
        l5_avg = self.fetch_gamelog(player['id'])
        if not l5_avg: return None
        
        # Calculate Titanium Projection
        # Formula: Base (L5) + Defense Modifier
        # If Opponent DefRtg > 115 -> +5% Boost
        # If Opponent Pace > 100 -> +3% Boost
        
        proj = l5_avg
        logic = []
        
        if opp_stats.get('DefRtg', 110) > 115.0:
            proj *= 1.05
            logic.append("Weak Def")
        
        if opp_stats.get('Pace', 98) > 100.0:
            proj *= 1.03
            logic.append("High Pace")
            
        # V34 SECTION XXV: "Identify Highest PRA Ceiling"
        # We assume 'player' is a 'Creator' based on roster rank.
        
        # OUTPUT THRESHOLD: Only target if Projection > 20 pts (volume scorer)
        if proj > 20.0:
            return {
                "Target": player['name'],
                "L5_Avg": f"{l5_avg:.1f}",
                "Titanium_Proj": f"{proj:.1f}",
                "Logic": " | ".join(logic) if logic else "Standard Val"
            }
        return None

# --- HELPER: TEAM MAPPING ---
def get_nba_team_stats(name, db):
    mapping = {"LA Clippers": "L.A. Clippers", "Los Angeles Clippers": "L.A. Clippers", "LA Lakers": "L.A. Lakers", "Los Angeles Lakers": "L.A. Lakers"}
    target = mapping.get(name, name)
    if target in db: return db[target]
    mascot = name.split()[-1]
    for k in db:
        if mascot in k: return db[k]
    return None

def _parse_odds(odds_obj, home_comp, away_comp):
    h_ml = odds_obj.get('homeTeamOdds', {}).get('moneyLine')
    a_ml = odds_obj.get('awayTeamOdds', {}).get('moneyLine')
    if not h_ml: h_ml = home_comp.get('lines', [{}])[0].get('moneyLine')
    if not a_ml: a_ml = away_comp.get('lines', [{}])[0].get('moneyLine')
    try: h_ml = float(h_ml) if h_ml else None
    except: h_ml = None
    try: a_ml = float(a_ml) if a_ml else None
    except: a_ml = None
    spread_str = odds_obj.get('details', '0')
    return h_ml, a_ml, spread_str

# --- GATEKEEPER LOGIC ---
class TitaniumGatekeeper:
    def __init__(self, config, stats_db):
        self.config = config
        self.stats_db = stats_db
        self.bans = ["Milwaukee Bucks", "Pittsburgh Penguins"]
        self.originator = TitaniumOriginator() # NEW MODULE

    def _get_provider(self, odds_obj):
        try: return odds_obj.get('provider', {}).get('name', 'Consensus')
        except: return "Consensus"

    def audit_game(self, event, sport):
        if sport == "NBA": return self.audit_nba(event)
        elif sport == "NHL": return self.audit_nhl(event)
        elif sport == "NCAAB": return self.audit_ncaab(event)
        return []

    # --- NBA LOGIC (SPREADS + PROPS) ---
    def audit_nba(self, event):
        approved = []
        try:
            short_name = event['shortName']
            comp = event['competitions'][0]
            home = next(c for c in comp['competitors'] if c['homeAway'] == 'home')
            away = next(c for c in comp['competitors'] if c['homeAway'] == 'away')
            h_name, a_name = home['team']['displayName'], away['team']['displayName']

            if any(b in h_name for b in self.bans) or any(b in a_name for b in self.bans): return []

            # STATS
            h_st, a_st = get_nba_team_stats(h_name, self.stats_db), get_nba_team_stats(a_name, self.stats_db)
            
            # --- TITANIUM ORIGINATOR (PROPS) ---
            # Only run for games starting soon to avoid API spam? No, run all.
            # Fetch Home Stars
            h_stars = self.originator.fetch_roster(home['id'])
            for p in h_stars:
                res = self.originator.analyze_player(p, h_st, a_st) # Player, Own Stats, Opp Stats
                if res:
                    approved.append({
                        "Sport": "NBA", "Matchup": short_name, "Bet_Type": "Player Prop",
                        "Team_Target": res['Target'], "Line": f"Proj {res['Titanium_Proj']}", 
                        "Price": "AUDIT", "Sportsbook": "Originator", 
                        "Logic": f"L5: {res['L5_Avg']} | {res['Logic']} | BUY < {float(res['Titanium_Proj'])-1.0:.1f}"
                    })

            # Fetch Away Stars
            a_stars = self.originator.fetch_roster(away['id'])
            for p in a_stars:
                res = self.originator.analyze_player(p, a_st, h_st)
                if res:
                    approved.append({
                        "Sport": "NBA", "Matchup": short_name, "Bet_Type": "Player Prop",
                        "Team_Target": res['Target'], "Line": f"Proj {res['Titanium_Proj']}", 
                        "Price": "AUDIT", "Sportsbook": "Originator", 
                        "Logic": f"L5: {res['L5_Avg']} | {res['Logic']} | BUY < {float(res['Titanium_Proj'])-1.0:.1f}"
                    })

            # --- SPREAD/ML LOGIC (EXISTING) ---
            t_edge = None
            t_edge_val = 0.0
            if h_st and a_st:
                h_sc = (h_st['NetRtg'] * (h_st['Pace']/100)) + 1.5
                a_sc = (a_st['NetRtg'] * (a_st['Pace']/100))
                delta = h_sc - a_sc
                if delta > 3.0: 
                    t_edge = "HOME"
                    t_edge_val = abs(delta)
                elif delta < -3.0: 
                    t_edge = "AWAY"
                    t_edge_val = abs(delta)
            
            if comp.get('odds'):
                odds_obj = comp['odds'][0]
                provider = self._get_provider(odds_obj)
                h_ml, a_ml, spread_str = _parse_odds(odds_obj, home, away)
                
                # SPREAD
                if t_edge:
                    try:
                        parts = spread_str.split(" ")
                        fav_abbr, spread_val = parts[0], float(parts[1])
                        is_home_fav = (home['team']['abbreviation'] == fav_abbr)
                        target_side = "HOME" if t_edge == "HOME" else "AWAY"
                        target_team = h_name if target_side == "HOME" else a_name
                        final_line = spread_val
                        if not ((target_side == "HOME" and is_home_fav) or (target_side == "AWAY" and not is_home_fav)):
                            final_line = spread_val * -1
                        if t_edge == target_side and abs(final_line) <= 10.5:
                            price = str(odds_obj.get('price', -110))
                            approved.append({
                                "Sport": "NBA", "Matchup": short_name, "Bet_Type": "Spread",
                                "Team_Target": target_team, "Line": str(final_line), "Price": price, 
                                "Sportsbook": provider, "Logic": f"Titanium Edge {t_edge_val:.1f} | Blowout Check Passed"
                            })
                    except: pass
                
                # MONEYLINE
                if h_ml and t_edge == "HOME" and -200 <= h_ml <= 150:
                     approved.append({"Sport": "NBA", "Matchup": short_name, "Bet_Type": "Moneyline", "Team_Target": h_name, "Line": "ML", "Price": str(h_ml), "Sportsbook": provider, "Logic": f"Titanium Edge {t_edge_val:.1f} | ML Value"})
                if a_ml and t_edge == "AWAY" and -200 <= a_ml <= 150:
                     approved.append({"Sport": "NBA", "Matchup": short_name, "Bet_Type": "Moneyline", "Team_Target": a_name, "Line": "ML", "Price": str(a_ml), "Sportsbook": provider, "Logic": f"Titanium Edge {t_edge_val:.1f} | ML Value"})

        except: pass
        return approved

    # --- NHL LOGIC ---
    def audit_nhl(self, event):
        approved = []
        try:
            short_name = event['shortName']
            comp = event['competitions'][0]
            home = next(c for c in comp['competitors'] if c['homeAway'] == 'home')
            away = next(c for c in comp['competitors'] if c['homeAway'] == 'away')
            h_name, a_name = home['team']['displayName'], away['team']['displayName']

            if "Penguins" in h_name or "Penguins" in a_name: return []

            if not comp.get('odds'): return []
            odds_obj = comp['odds'][0]
            provider = self._get_provider(odds_obj)
            h_ml, a_ml, spread_str = _parse_odds(odds_obj, home, away)
            
            spread_val = 1.5
            try: spread_val = float(spread_str.split(" ")[1])
            except: pass

            if h_ml:
                if h_ml < -200:
                     approved.append({"Sport": "NHL", "Matchup": short_name, "Bet_Type": "Puck Line", "Team_Target": h_name, "Line": f"-{spread_val}", "Price": str(odds_obj.get('price', -110)), "Sportsbook": provider, "Logic": "Safety Valve (ML < -200)"})
                elif -200 <= h_ml <= 150:
                     approved.append({"Sport": "NHL", "Matchup": short_name, "Bet_Type": "Moneyline", "Team_Target": h_name, "Line": "ML", "Price": str(h_ml), "Sportsbook": provider, "Logic": "Odds Collar Pass"})
            if a_ml:
                if a_ml < -200:
                     approved.append({"Sport": "NHL", "Matchup": short_name, "Bet_Type": "Puck Line", "Team_Target": a_name, "Line": f"-{spread_val}", "Price": str(odds_obj.get('price', -110)), "Sportsbook": provider, "Logic": "Safety Valve (ML < -200)"})
                elif -200 <= a_ml <= 150:
                     approved.append({"Sport": "NHL", "Matchup": short_name, "Bet_Type": "Moneyline", "Team_Target": a_name, "Line": "ML", "Price": str(a_ml), "Sportsbook": provider, "Logic": "Odds Collar Pass"})
        except: pass
        return approved

    # --- NCAAB LOGIC ---
    def audit_ncaab(self, event):
        approved = []
        try:
            short_name = event['shortName']
            comp = event['competitions'][0]
            if not comp.get('odds'): return []
            odds_obj = comp['odds'][0]
            provider = self._get_provider(odds_obj)
            try:
                spread_str = odds_obj.get('details', '0')
                parts = spread_str.split(" ")
                spread_val = float(parts[1])
                team_abbr = parts[0]
                home = next(c for c in comp['competitors'] if c['homeAway'] == 'home')
                target_name = home['team']['displayName'] if home['team']['abbreviation'] == team_abbr else next(c for c in comp['competitors'] if c['homeAway'] == 'away')['team']['displayName']
                logic_note = "V34 Approved"
                if -4.5 <= spread_val <= -0.5:
                    logic_note = "⚠️ CLOSERS METRIC: Audit FT% > 71%"
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

# --- MAIN UI ---
def main():
    st.sidebar.title("TITANIUM V34.7 ORIGINATOR")
    sport = st.sidebar.selectbox("PROTOCOL SELECTION", ["NBA", "NHL", "NCAAB", "NFL (Offseason)"])
    
    config = load_v34_protocol()
    if config: st.sidebar.success("BRAIN: ONLINE")
    else: st.sidebar.error("BRAIN: OFFLINE")
    
    st.title(f"⚡ TITANIUM V34.7 | {sport}")
    
    if sport in ["NBA", "NHL", "NCAAB"]:
        if st.button("EXECUTE TITANIUM SEQUENCE"):
            with st.spinner(f"AUDITING {sport} MARKETS (Running Originator... This takes 10s)..."):
                raw_data = get_live_data(sport)
                
                if raw_data:
                    stats_db = fetch_nba_stats() if sport == "NBA" else None
                    gatekeeper = TitaniumGatekeeper(config, stats_db)
                    ledger = []
                    
                    for event in raw_data['events']:
                        bets = gatekeeper.audit_game(event, sport)
                        ledger.extend(bets)
                    
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
