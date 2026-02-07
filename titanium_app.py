import streamlit as st
import pandas as pd
import requests
import json
import os
import datetime
import pytz
import random

# --- TITANIUM KEYVAULT ---
ODDS_API_KEY = "01dc7be6ca076e6b79ac4f54001d142d"  # DO NOT LEAK THIS

# --- CONFIGURATION ---
st.set_page_config(page_title="TITANIUM V36 OMEGA", layout="wide", page_icon="💀")

# --- CSS STYLING ---
st.markdown("""
<style>
    .stApp {background-color: #050505; color: #e0e0e0;}
    div.stButton > button {width: 100%; background-color: #880000; color: white; font-weight: bold; border: 1px solid #ff0000;}
    div.stButton > button:hover {background-color: #ff0000; color: black;}
    .reportview-container .main .block-container {padding-top: 2rem;}
    h1 {color: #ff3333; text-transform: uppercase; font-family: monospace;}
    .success-box {border-left: 5px solid #00ff00; background-color: #112211; padding: 10px;}
    .audit-box {border-left: 5px solid #ffaa00; background-color: #221100; padding: 10px;}
</style>
""", unsafe_allow_html=True)

# --- V36 KERNEL LOADER ---
@st.cache_data
def load_protocol():
    """Parses TITANIUM_V34.json."""
    file_path = "titanium_v34.json"
    if not os.path.exists(file_path): 
        # FALLBACK CONFIG IF FILE MISSING
        return {"filters": {"odds_collar": {"min": -180, "max": 150}, "nhl": {"fade_list": ["Penguins"]}}}
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except: return None

# --- GUERRILLA SCRAPER (NBA) ---
@st.cache_data(ttl=3600)
def fetch_nba_stats():
    """
    ATTEMPTS LIVE SCRAPE.
    FALLS BACK TO 'STATIC BUNKER' IF BLOCKED.
    """
    db = {}
    # 1. LIVE ATTEMPT
    try:
        url = "http://www.espn.com/nba/hollinger/statistics"
        header = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        dfs = pd.read_html(requests.get(url, headers=header).text, header=1)
        df = dfs[0]
        df = df[df['TEAM'] != 'TEAM'] # Clean headers
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
    
    # 2. STATIC BUNKER (UPDATED FEB 2026)
    return {
        "Boston Celtics": {"NetRtg": 9.2, "Pace": 98.5, "DefRtg": 110.5},
        "Oklahoma City Thunder": {"NetRtg": 7.8, "Pace": 101.2, "DefRtg": 111.4},
        "Denver Nuggets": {"NetRtg": 5.1, "Pace": 97.5, "DefRtg": 113.8},
        "Minnesota Timberwolves": {"NetRtg": 5.9, "Pace": 98.0, "DefRtg": 109.5},
        "New York Knicks": {"NetRtg": 4.5, "Pace": 96.2, "DefRtg": 112.5},
        "Cleveland Cavaliers": {"NetRtg": 4.8, "Pace": 98.5, "DefRtg": 110.2},
        "L.A. Clippers": {"NetRtg": 2.8, "Pace": 97.9, "DefRtg": 114.5},
        "Philadelphia 76ers": {"NetRtg": 3.0, "Pace": 99.1, "DefRtg": 113.2},
        "Phoenix Suns": {"NetRtg": 3.5, "Pace": 99.8, "DefRtg": 114.8},
        "Milwaukee Bucks": {"NetRtg": -1.2, "Pace": 102.1, "DefRtg": 116.8},
        "Dallas Mavericks": {"NetRtg": -1.8, "Pace": 101.8, "DefRtg": 117.2},
        "L.A. Lakers": {"NetRtg": 0.9, "Pace": 100.8, "DefRtg": 115.5},
        "Golden State Warriors": {"NetRtg": 1.5, "Pace": 100.2, "DefRtg": 114.5},
        "Sacramento Kings": {"NetRtg": 1.2, "Pace": 100.5, "DefRtg": 116.2},
        "New Orleans Pelicans": {"NetRtg": 0.2, "Pace": 99.2, "DefRtg": 113.8},
        "Houston Rockets": {"NetRtg": 1.9, "Pace": 99.5, "DefRtg": 111.8},
        "Orlando Magic": {"NetRtg": 1.8, "Pace": 98.2, "DefRtg": 110.5},
        "Miami Heat": {"NetRtg": 0.5, "Pace": 96.8, "DefRtg": 112.8},
        "Indiana Pacers": {"NetRtg": 1.1, "Pace": 103.8, "DefRtg": 119.5},
        "Atlanta Hawks": {"NetRtg": -2.0, "Pace": 102.8, "DefRtg": 119.8},
        "Brooklyn Nets": {"NetRtg": -4.8, "Pace": 98.2, "DefRtg": 116.8},
        "Toronto Raptors": {"NetRtg": -5.5, "Pace": 100.2, "DefRtg": 118.5},
        "Chicago Bulls": {"NetRtg": -4.0, "Pace": 99.0, "DefRtg": 115.8},
        "Memphis Grizzlies": {"NetRtg": 3.2, "Pace": 100.2, "DefRtg": 112.8},
        "Utah Jazz": {"NetRtg": -6.0, "Pace": 99.8, "DefRtg": 119.5},
        "San Antonio Spurs": {"NetRtg": -1.5, "Pace": 101.8, "DefRtg": 115.2},
        "Portland Trail Blazers": {"NetRtg": -7.0, "Pace": 98.5, "DefRtg": 117.8},
        "Charlotte Hornets": {"NetRtg": -6.8, "Pace": 100.8, "DefRtg": 119.2},
        "Washington Wizards": {"NetRtg": -9.0, "Pace": 103.2, "DefRtg": 120.8},
        "Detroit Pistons": {"NetRtg": -7.5, "Pace": 101.2, "DefRtg": 118.8}
    }

# --- HELPER: TIME & MAP ---
def format_time(iso_string):
    try:
        dt = datetime.datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        cst = dt.astimezone(pytz.timezone("US/Central"))
        return cst.strftime("%I:%M %p")
    except: return "TBD"

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

# --- THE DIVERSITY ENGINE ---
def force_diversity(ledger, limit):
    """
    The Round-Robin Draft.
    Prevents Correlation Risk.
    """
    if not ledger: return []
    
    # 1. Bucket the bets
    buckets = {}
    for bet in ledger:
        b_type = bet['Type']
        if "Spread" in b_type or "Run Line" in b_type or "Puck Line" in b_type or "Handicap" in b_type:
            key = "Spread"
        elif "Moneyline" in b_type or "3-Way" in b_type:
            key = "Moneyline"
        elif "Total" in b_type:
            if "Under" in bet['Target'] or "Under" in bet['Line'] or "U " in bet['Line']: key = "Total_Under"
            else: key = "Total_Over"
        else:
            key = "Prop" 
        
        if key not in buckets: buckets[key] = []
        buckets[key].append(bet)

    # 2. Sort each bucket by Value
    for k in buckets:
        buckets[k].sort(key=lambda x: x.get('Sort_Val', 0), reverse=True)

    # 3. Round Robin Draft
    final_list = []
    draft_order = ["Spread", "Total_Over", "Total_Under", "Prop", "Moneyline"]
    
    while len(final_list) < limit:
        added_this_round = False
        for k in draft_order:
            if len(final_list) >= limit: break
            if k in buckets and buckets[k]:
                final_list.append(buckets[k].pop(0))
                added_this_round = True
        
        if not added_this_round:
            remaining = []
            for k in buckets: remaining.extend(buckets[k])
            remaining.sort(key=lambda x: x.get('Sort_Val', 0), reverse=True)
            needed = limit - len(final_list)
            final_list.extend(remaining[:needed])
            break
            
    return final_list

# --- ODDS API ENGINE ---
class OddsAPIEngine:
    def __init__(self, api_key, config):
        self.key = api_key
        self.config = config
        self.base = "https://api.the-odds-api.com/v4/sports"
        self.collar_min = config['filters']['odds_collar']['min']
        self.collar_max = config['filters']['odds_collar']['max']

    def fetch_events(self, sport_key):
        url = f"{self.base}/{sport_key}/events?apiKey={self.key}&regions=us&markets=h2h"
        try: return requests.get(url).json()
        except: return []

    def fetch_batch_odds(self, sport_key):
        url = f"{self.base}/{sport_key}/odds?apiKey={self.key}&regions=us&markets=h2h,spreads,totals&oddsFormat=american"
        try: return requests.get(url).json()
        except: return []

    def fetch_game_props(self, sport, event_id):
        market_str = "h2h,spreads,totals"
        if sport == "NBA": market_str += ",player_points"
        if sport == "NFL": market_str += ",player_pass_yds,player_rush_yds,player_reception_yds"
        
        # NBA/NFL have different endpoint keys
        sport_key = "basketball_nba" if sport == "NBA" else "americanfootball_nfl"
        
        url = f"{self.base}/{sport_key}/events/{event_id}/odds?apiKey={self.key}&regions=us&markets={market_str}&oddsFormat=american"
        try: return requests.get(url).json()
        except: return None

    # --- PARSERS ---
    
    def parse_nfl_game(self, data):
        ledger = []
        bookmakers = data.get('bookmakers', [])
        if not bookmakers: return []
        dk_book = next((b for b in bookmakers if b['key'] == 'draftkings'), bookmakers[0])
        
        current_spread_val = 0 
        
        for market in dk_book.get('markets', []):
            if market['key'] == 'spreads':
                for outcome in market['outcomes']:
                    line = outcome['point']
                    price = outcome['price']
                    current_spread_val = abs(line) # Capture for Blowout Shield
                    if self.collar_min <= price <= self.collar_max:
                        sort_val = 50
                        # Key Number Boost
                        if abs(line) == 3.0 or abs(line) == 7.0: sort_val = 95
                        elif abs(line) in [2.5, 3.5, 6.5, 7.5]: sort_val = 85
                        
                        directive = "Audit."
                        if sort_val > 60: directive = f"⚠️ KEY NUMBER ({line})."
                        ledger.append({"Sport": "NFL", "Type": "Spread", "Target": outcome['name'], "Line": line, "Price": price, "Book": dk_book['title'], "Audit_Directive": directive, "Sort_Val": sort_val})

            elif market['key'] == 'h2h':
                for outcome in market['outcomes']:
                    if self.collar_min <= outcome['price'] <= self.collar_max:
                        ledger.append({"Sport": "NFL", "Type": "Moneyline", "Target": outcome['name'], "Line": "ML", "Price": outcome['price'], "Book": dk_book['title'], "Audit_Directive": "Check Injuries.", "Sort_Val": 60})

            elif market['key'] == 'totals':
                for outcome in market['outcomes']:
                     if -120 <= outcome['price'] <= 150:
                        ledger.append({"Sport": "NFL", "Type": "Total", "Target": "Game Total", "Line": f"{outcome['name']} {outcome['point']}", "Price": outcome['price'], "Book": dk_book['title'], "Audit_Directive": "💨 WEATHER.", "Sort_Val": 55})

            elif 'player_' in market['key']:
                prop_type = market['key'].replace('player_', '').replace('_yds', ' Yds').title()
                for outcome in market['outcomes']:
                    line = outcome['point']
                    price = outcome['price']
                    side = outcome['name']
                    if self.collar_min <= price <= self.collar_max:
                        # Volume Filters
                        valid_vol = False
                        if prop_type == "Pass Yds" and line > 225.0: valid_vol = True
                        if prop_type == "Rush Yds" and line > 45.0: valid_vol = True
                        if prop_type == "Reception Yds" and line > 45.0: valid_vol = True
                        
                        if valid_vol:
                            # Blowout Shield
                            if current_spread_val > 10.5 and side == "Over": continue 
                            
                            sort_val = 70
                            directive = "Prop Check."
                            if current_spread_val > 10.5 and side == "Under": 
                                directive = "✅ BLOWOUT SHIELD: Under Safe."
                                sort_val = 90
                                
                            ledger.append({"Sport": "NFL", "Type": prop_type, "Target": outcome['description'], "Line": f"{side} {line}", "Price": price, "Book": dk_book['title'], "Audit_Directive": directive, "Sort_Val": sort_val})
        return ledger

    def parse_nba_game(self, data, h_team, a_team, stats_db):
        ledger = []
        bookmakers = data.get('bookmakers', [])
        if not bookmakers: return []
        dk_book = next((b for b in bookmakers if b['key'] == 'draftkings'), bookmakers[0])
        
        # Stats logic
        h_st = get_nba_team_stats(h_team, stats_db)
        a_st = get_nba_team_stats(a_team, stats_db)
        # Default average if missing
        if not h_st: h_st = {"DefRtg": 114, "Pace": 99, "NetRtg": 0}
        if not a_st: a_st = {"DefRtg": 114, "Pace": 99, "NetRtg": 0}

        for market in dk_book.get('markets', []):
            if market['key'] == 'spreads':
                for outcome in market['outcomes']:
                    line = outcome['point']
                    price = outcome['price']
                    
                    # NetRtg Calculation
                    h_sc = (h_st['NetRtg'] * (h_st['Pace']/100)) + 1.5 # Home Court
                    a_sc = (a_st['NetRtg'] * (a_st['Pace']/100))
                    proj_margin = h_sc - a_sc
                    target_team = h_team if proj_margin > 0 else a_team
                    
                    if outcome['name'] == target_team and abs(line) <= 12.5 and self.collar_min <= price <= self.collar_max:
                        edge = abs(proj_margin) - abs(line)
                        if edge > 0:
                            sort_val = 50 + (edge * 10)
                            ledger.append({"Sport": "NBA", "Type": "Spread", "Target": outcome['name'], "Line": line, "Price": price, "Book": dk_book['title'], "Audit_Directive": f"NetRtg Edge ({edge:.1f}).", "Sort_Val": sort_val})

            elif market['key'] == 'totals':
                for outcome in market['outcomes']:
                    side = outcome['name']
                    line = outcome['point']
                    combined_pace = h_st['Pace'] + a_st['Pace']
                    
                    if self.collar_min <= outcome['price'] <= self.collar_max:
                        # Hard Integers
                        if side == "Over" and combined_pace > 202.0:
                            sort_val = 70 + (combined_pace - 202)
                            ledger.append({"Sport": "NBA", "Type": "Total", "Target": f"{h_team}/{a_team}", "Line": f"O {line}", "Price": outcome['price'], "Book": dk_book['title'], "Audit_Directive": f"PACE ALERT: {combined_pace:.1f}.", "Sort_Val": sort_val})
                        elif side == "Under" and combined_pace < 194.0:
                            sort_val = 70 + (194 - combined_pace)
                            ledger.append({"Sport": "NBA", "Type": "Total", "Target": f"{h_team}/{a_team}", "Line": f"U {line}", "Price": outcome['price'], "Book": dk_book['title'], "Audit_Directive": f"SLUDGE ALERT: {combined_pace:.1f}.", "Sort_Val": sort_val})

            elif market['key'] == 'player_points':
                for outcome in market['outcomes']:
                    if outcome['name'] == "Over" and outcome['point'] > 18.5 and self.collar_min <= outcome['price'] <= self.collar_max:
                        sort_val = 50
                        msg = ""
                        # DefRtg Attack
                        if h_st['DefRtg'] > 115: 
                            msg = f"vs {h_team} (Def {h_st['DefRtg']})"
                            sort_val = 80
                        elif a_st['DefRtg'] > 115: 
                            msg = f"vs {a_team} (Def {a_st['DefRtg']})"
                            sort_val = 80
                        
                        if msg:
                            ledger.append({"Sport": "NBA", "Type": "Player Prop", "Target": outcome['description'], "Line": f"Over {outcome['point']}", "Price": outcome['price'], "Book": dk_book['title'], "Audit_Directive": f"KOTC: {msg}.", "Sort_Val": sort_val})
        return ledger

    def parse_batch_generic(self, games, sport):
        candidates = []
        fade_list = self.config['filters']['nhl']['fade_list']
        
        for game in games:
            bookmakers = game.get('bookmakers', [])
            if not bookmakers: continue
            dk_book = next((b for b in bookmakers if b['key'] == 'draftkings'), bookmakers[0])
            h_team, a_team = game['home_team'], game['away_team']
            
            # Blacklists
            if sport == "NHL" and any(x in h_team or x in a_team for x in fade_list): continue
            
            time_str = format_time(game['commence_time'])
            matchup = f"{a_team} @ {h_team}"
            
            for market in dk_book.get('markets', []):
                # NHL LOGIC (FIXED: STRICT COLLAR)
                if sport == "NHL":
                    if market['key'] == 'h2h': # Moneyline
                         for outcome in market['outcomes']:
                            price = outcome['price']
                            # STRICT -180 to +150 only
                            if self.collar_min <= price <= self.collar_max:
                                sort_val = 60
                                directive = "Goalie Check."
                                # Value Logic: Slight Home Dog or Reasonable Home Fav
                                if outcome['name'] == h_team and -140 < price < 130:
                                    sort_val = 75
                                    directive = "Home Ice Value."
                                
                                candidates.append({
                                    "Sport": "NHL", "Time": time_str, "Matchup": matchup, 
                                    "Type": "Moneyline", "Target": outcome['name'], "Line": "ML", 
                                    "Price": price, "Book": dk_book['title'], 
                                    "Audit_Directive": directive, "Sort_Val": sort_val
                                })
                    
                    elif market['key'] == 'spreads': # Puck Line
                        for outcome in market['outcomes']:
                            price = outcome['price']
                            if self.collar_min <= price <= self.collar_max:
                                sort_val = 65
                                directive = "PL Value."
                                # Logic: Catching +1.5 at a reasonable price
                                if outcome['point'] == 1.5 and price > -170:
                                    sort_val = 80
                                    directive = "Safety Valve PL."
                                    
                                candidates.append({
                                    "Sport": "NHL", "Time": time_str, "Matchup": matchup, 
                                    "Type": "Puck Line", "Target": outcome['name'], 
                                    "Line": outcome['point'], "Price": price, 
                                    "Book": dk_book['title'], "Audit_Directive": directive, 
                                    "Sort_Val": sort_val
                                })

                # NCAAB LOGIC (FIXED: V36 MADNESS)
                elif sport == "NCAAB":
                    if market['key'] == 'spreads':
                        for outcome in market['outcomes']:
                            line = outcome['point']
                            price = outcome['price']
                            
                            if not (self.collar_min <= price <= self.collar_max): continue
                            
                            # Filter: Blowout Shield (CBB Specific)
                            if abs(line) > 22.5: continue
                            
                            sort_val = 60
                            audit_msg = "Std CBB Line."
                            
                            # STRATEGY 1: THE HOME DOG (High Value)
                            if outcome['name'] == h_team and line > 0:
                                sort_val = 85
                                audit_msg = f"🐶 HOME DOG (+{line})."
                            
                            # STRATEGY 2: THE ROAD FAVORITE TRAP (Fade)
                            elif outcome['name'] == a_team and -4.0 <= line < 0:
                                sort_val = 40 # Penalty
                                audit_msg = "⚠️ SHORT ROAD FAV (Trap risk)."
                                
                            # STRATEGY 3: RANKED KILLER (Proxy)
                            elif line < -12.0 and line > -18.0:
                                sort_val = 75
                                audit_msg = "🔨 HEAVY FAVORITE (Talent Gap)."

                            candidates.append({
                                "Sport": "NCAAB", "Time": time_str, "Matchup": matchup, 
                                "Type": "Spread", "Target": outcome['name'], "Line": line, 
                                "Price": price, "Book": dk_book['title'], 
                                "Audit_Directive": audit_msg, "Sort_Val": sort_val
                            })
                            
                    elif market['key'] == 'totals':
                        for outcome in market['outcomes']:
                            line = outcome['point']
                            price = outcome['price']
                            side = outcome['name']
                            
                            if not (-115 <= price <= 115): continue
                            
                            sort_val = 55
                            audit_msg = "Tempo Check."
                            
                            # STRATEGY 4: THE ROCK FIGHT (Under)
                            if line < 128.0 and side == "Under":
                                sort_val = 80
                                audit_msg = f"🧱 ROCK FIGHT (<128)."
                            
                            # STRATEGY 5: THE TRACK MEET (Over)
                            elif line > 160.0 and side == "Over":
                                sort_val = 75
                                audit_msg = f"🚀 TRACK MEET (>160)."
                                
                            candidates.append({
                                "Sport": "NCAAB", "Time": time_str, "Matchup": matchup, 
                                "Type": "Total", "Target": f"Game {side}", "Line": f"{side} {line}", 
                                "Price": price, "Book": dk_book['title'], 
                                "Audit_Directive": audit_msg, "Sort_Val": sort_val
                            })

                # SOCCER LOGIC (FIXED: STRICT COLLAR)
                elif sport == "SOCCER":
                    if market['key'] == 'h2h':
                        for outcome in market['outcomes']:
                            price = outcome['price']
                            
                            # STRICT -180 to +150. (This nukes most Draws)
                            if self.collar_min <= price <= self.collar_max:
                                sort_val = 70
                                directive = "Lineup Audit."
                                
                                # If a Draw survives the collar (rare, but possible for +140ish)
                                if outcome['name'] == "Draw":
                                    sort_val = 85
                                    directive = "VALUE DRAW."
                                # If a Favorite is within range (e.g. -150)
                                elif price < 0:
                                    sort_val = 80
                                    directive = "Strong Fav (In Range)."
                                    
                                candidates.append({
                                    "Sport": "SOCCER", "Time": time_str, "Matchup": matchup, 
                                    "Type": "3-Way", "Target": outcome['name'], "Line": "ML", 
                                    "Price": price, "Book": dk_book['title'], 
                                    "Audit_Directive": directive, "Sort_Val": sort_val
                                })

        return candidates

# --- MAIN UI ---
def main():
    st.sidebar.title("TITANIUM V36 OMEGA")
    st.sidebar.markdown("---")
    sport = st.sidebar.selectbox("PROTOCOL", ["NBA", "NFL", "NCAAB", "NHL", "SOCCER"])
    
    # Load Protocol
    config = load_protocol()
    if not config: st.error("CONFIG CRASHED.")
    
    odds_engine = OddsAPIEngine(ODDS_API_KEY, config)
    st.title(f"💀 TITANIUM V36 OMEGA | {sport}")

    if st.button(f"EXECUTE {sport} SEQUENCE"):
        with st.spinner(f"SCANNING {sport} MARKETS..."):
            ledger = []
            
            # 1. NBA (Surgical)
            if sport == "NBA":
                stats_db = fetch_nba_stats() # Live Scrape or Bunker
                if len(stats_db) < 10: st.warning("⚠️ USING STATIC DATA (BUNKER MODE)")
                events = odds_engine.fetch_events("basketball_nba")
                for event in events:
                    data = odds_engine.fetch_game_props("NBA", event['id'])
                    if data:
                        bets = odds_engine.parse_nba_game(data, event['home_team'], event['away_team'], stats_db)
                        for b in bets:
                            b['Time'] = format_time(event['commence_time'])
                            b['Matchup'] = f"{event['away_team']} @ {event['home_team']}"
                            ledger.append(b)
                # DIVERSITY DRAFT
                ledger = force_diversity(ledger, 20)

            # 2. NFL (Surgical)
            elif sport == "NFL":
                events = odds_engine.fetch_events("americanfootball_nfl")
                for event in events:
                    data = odds_engine.fetch_game_props("NFL", event['id'])
                    if data:
                        bets = odds_engine.parse_nfl_game(data)
                        for b in bets:
                            b['Time'] = format_time(event['commence_time'])
                            b['Matchup'] = f"{event['away_team']} @ {event['home_team']}"
                            ledger.append(b)
                ledger = force_diversity(ledger, 20)

            # 3. BATCH SPORTS (NCAAB, NHL, SOCCER)
            else:
                key_map = {"NCAAB": "basketball_ncaab", "NHL": "icehockey_nhl", "SOCCER": "soccer_epl"}
                raw_data = odds_engine.fetch_batch_odds(key_map[sport])
                ledger = odds_engine.parse_batch_generic(raw_data, sport)
                
                limit = 12 if sport == "NCAAB" else 6
                ledger = force_diversity(ledger, limit)

            # OUTPUT
            if ledger:
                st.success(f"TARGETS ACQUIRED: {len(ledger)}")
                df = pd.DataFrame(ledger)
                cols = ["Time", "Matchup", "Type", "Target", "Line", "Price", "Audit_Directive"]
                st.dataframe(df[cols], use_container_width=True, hide_index=True)
            else:
                st.warning("MARKET EFFICIENT. ZERO SURVIVORS.")

if __name__ == "__main__":
    main()
