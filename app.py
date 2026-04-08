from flask import Flask, jsonify, render_template
import requests
import math
import os

app = Flask(__name__)

API_KEY = os.environ.get("HYPIXEL_API_KEY","")
BASE_URL = "https://api.hypixel.net"

# Hypixel klassische Rang-Farben (Hex)
RANK_COLORS = {
    "MVP++": "#FFAA00",   # Gold
    "MVP+":  "#55FFFF",   # Aqua
    "MVP":   "#55FFFF",   # Aqua
    "VIP+":  "#55FF55",   # Grün
    "VIP":   "#55FF55",   # Grün
    "YOUTUBE": "#FF5555", # Rot
    "ADMIN":   "#FF5555",
    "OWNER":   "#FF5555",
    "MOJANG":  "#FF5555",
    "STAFF":   "#FFAA00",
    "Kein Rang": "#AAAAAA",
}

# SkyBlock Insel-Codes → lesbarer Name
SKYBLOCK_MODES = {
    "dynamic":          "Private Island",
    "hub":              "Hub",
    "farming_1":        "The Barn",
    "farming_2":        "Mushroom Desert",
    "foraging_1":       "The Park",
    "combat_1":         "Spider's Den",
    "combat_2":         "Blazing Fortress",
    "combat_3":         "The End",
    "combat_4":         "Crimson Isle",
    "combat_5":         "Kuudra's Hollow",
    "mining_1":         "Gold Mine",
    "mining_2":         "Deep Caverns",
    "mining_3":         "Dwarven Mines",
    "mining_4":         "Crystal Hollows",
    "mining_5":         "Mineshaft",
    "dungeon_hub":      "Dungeon Hub",
    "dungeon":          "Catacombs",
    "temple":           "Dungeon Hub",
    "garden":           "Garden",
    "rift":             "The Rift",
    "jerrys_workshop":  "Jerry's Workshop",
    "winter":           "Jerry's Workshop",
    "fishing_1":        "Backwater Bayou",
    "banker_3":         "Dark Auction",
    "LOBBY":            "SkyBlock Lobby",
    "lobby":            "SkyBlock Lobby",
}

MODE_NAMES = {
    # Bed Wars
    "EIGHT_ONE":             "Solo",
    "EIGHT_TWO":             "Duos",
    "FOUR_THREE":            "3v3v3v3",
    "FOUR_FOUR":             "4v4v4v4",
    "TWO_FOUR":              "4v4",
    "EIGHT_ONE_RUSH":        "Solo Rush",
    "EIGHT_TWO_RUSH":        "Duos Rush",
    "FOUR_FOUR_RUSH":        "4v4v4v4 Rush",
    "EIGHT_ONE_ULTIMATE":    "Solo Ultimate",
    "EIGHT_TWO_ULTIMATE":    "Duos Ultimate",
    "FOUR_FOUR_ULTIMATE":    "4v4v4v4 Ultimate",
    "EIGHT_TWO_LUCKY":       "Duos Lucky",
    "FOUR_FOUR_LUCKY":       "4v4v4v4 Lucky",
    "EIGHT_TWO_VOIDLESS":    "Duos Voidless",
    "FOUR_FOUR_VOIDLESS":    "4v4v4v4 Voidless",
    "EIGHT_TWO_ARMED":       "Duos Armed",
    "FOUR_FOUR_ARMED":       "4v4v4v4 Armed",
    # Sky Wars
    "ranked_normal":   "Ranked",
    "solo_normal":     "Solo Normal",
    "solo_insane":     "Solo Insane",
    "teams_normal":    "Teams Normal",
    "teams_insane":    "Teams Insane",
    "mega_normal":     "Mega",
    "mega_doubles":    "Mega Doubles",
    # Duels
    "DUEL_CLASSIC":    "Classic 1v1",
    "DUEL_BOW":        "Bow 1v1",
    "DUEL_BLITZ":      "Blitz 1v1",
    "DUEL_BOWSPLEEF":  "Bow Spleef 1v1",
    "DUEL_COMBO":      "Combo 1v1",
    "DUEL_NODEBUFF":   "No Debuff 1v1",
    "DUEL_POTION":     "Potion 1v1",
    "DUEL_SUMO":       "Sumo 1v1",
    "DUEL_UHC":        "UHC 1v1",
    "UHC_DOUBLES":     "UHC 2v2",
    "SW_DUEL":         "SkyWars 1v1",
    "SW_DOUBLES":      "SkyWars 2v2",
    "OP_DUEL":         "OP 1v1",
    "OP_DOUBLES":      "OP 2v2",
    "BRIDGE_DUEL":     "The Bridge 1v1",
    "BRIDGE_DOUBLES":  "The Bridge 2v2",
    "BRIDGE_THREES":   "The Bridge 3v3",
    "BRIDGE_FOUR":     "The Bridge 4v4",
    # Murder Mystery
    "MURDER_CLASSIC":    "Classic",
    "MURDER_DOUBLE_UP":  "Double Up",
    "MURDER_ASSASSINS":  "Assassins",
    "MURDER_INFECTION":  "Infection",
    # Fallback
    "LOBBY": "Lobby",
    "lobby": "Lobby",
}

GAME_NAMES = {
    "BEDWARS":       "Bed Wars",
    "SKYWARS":       "Sky Wars",
    "DUELS":         "Duels",
    "MURDERMYSTERY": "Murder Mystery",
    "SKYBLOCK":      "SkyBlock",
    "HOUSING":       "Housing",
    "ARCADE":        "Arcade",
    "TNTGAMES":      "TNT Games",
    "UHCCHAMPIONS":  "UHC Champions",
    "SPEEDUHC":      "Speed UHC",
    "MEGAWALLS":     "Mega Walls",
    "VAMPIREZ":      "VampireZ",
    "WALLS":         "Walls",
    "PAINTBALL":     "Paintball",
    "QUAKE":         "Quakecraft",
    "ARENA":         "Arena Brawl",
    "SURVIVAL_GAMES":"Blitz SG",
    "BUILDBATTLE":   "Build Battle",
    "BATTLEGROUND":  "Warlords",
    "GINGERBREAD":   "Turbo Kart Racers",
    "MAIN":          "Hauptlobby",
}


def get_uuid(username: str):
    r = requests.get(f"https://api.mojang.com/users/profiles/minecraft/{username}", timeout=5)
    if r.status_code == 200:
        data = r.json()
        return data.get("id"), data.get("name")
    return None, None


def hypixel_get(endpoint: str, params: dict = None):
    if params is None:
        params = {}
    params["key"] = API_KEY
    r = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=5)
    if r.status_code == 200:
        data = r.json()
        if data.get("success"):
            return data
    return None


def format_number(n):
    if n is None:
        return "0"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(int(n))


def calc_network_level(xp: float) -> int:
    if xp <= 0:
        return 1
    level = 1 + (-8750 + math.sqrt(8750**2 + 5000 * xp)) / 2500
    return int(level)


def get_rank(player: dict) -> dict:
    """Gibt {'label': 'MVP++', 'color': '#FFAA00'} zurück"""
    prefix = player.get("prefix")
    if prefix:
        clean = ""
        i = 0
        while i < len(prefix):
            if prefix[i] == "§" and i + 1 < len(prefix):
                i += 2
            else:
                clean += prefix[i]
                i += 1
        label = clean.strip("[] ")
        return {"label": label, "color": RANK_COLORS.get(label, "#FF5555")}

    monthly = player.get("monthlyPackageRank", "")
    rank    = player.get("newPackageRank", "")
    rank_map = {"MVP_PLUS": "MVP+", "MVP": "MVP", "VIP_PLUS": "VIP+", "VIP": "VIP"}

    if monthly == "SUPERSTAR":
        label = "MVP++"
    else:
        label = rank_map.get(rank, "Kein Rang")

    return {"label": label, "color": RANK_COLORS.get(label, "#AAAAAA")}


def translate_mode(game_raw: str, mode_raw: str) -> str:
    """Übersetzt den rohen Mode-Code abhängig vom Spiel."""
    if game_raw == "SKYBLOCK":
        return SKYBLOCK_MODES.get(mode_raw, mode_raw.replace("_", " ").title())
    return MODE_NAMES.get(mode_raw, mode_raw.replace("_", " ").title())


def build_game_stats(player: dict) -> list:
    s  = player.get("stats", {})
    bw = s.get("Bedwars", {})
    sw = s.get("SkyWars", {})
    mm = s.get("MurderMystery", {})

    def ratio(a, b):
        return round(a / b, 2) if b else 0

    return [
        {
            "name": "Bed Wars", "icon": "🛏️",
            "stats": [
                {"label": "Wins",            "value": format_number(bw.get("wins_bedwars", 0))},
                {"label": "Kills",           "value": format_number(bw.get("kills_bedwars", 0))},
                {"label": "K/D",             "value": ratio(bw.get("kills_bedwars", 0), bw.get("deaths_bedwars", 1))},
                {"label": "W/L",             "value": ratio(bw.get("wins_bedwars", 0), bw.get("losses_bedwars", 1))},
                {"label": "Betten zerstört", "value": format_number(bw.get("beds_broken_bedwars", 0))},
                {"label": "Final Kills",     "value": format_number(bw.get("final_kills_bedwars", 0))},
            ],
        },
        {
            "name": "Sky Wars", "icon": "☁️",
            "stats": [
                {"label": "Wins",  "value": format_number(sw.get("wins", 0))},
                {"label": "Kills", "value": format_number(sw.get("kills", 0))},
                {"label": "K/D",   "value": ratio(sw.get("kills", 0), sw.get("deaths", 1))},
                {"label": "W/L",   "value": ratio(sw.get("wins", 0), sw.get("losses", 1))},
                {"label": "Souls", "value": format_number(sw.get("souls", 0))},
            ],
        },
        {
            "name": "Murder Mystery", "icon": "🔪",
            "stats": [
                {"label": "Wins",         "value": format_number(mm.get("wins", 0))},
                {"label": "Kills",        "value": format_number(mm.get("kills", 0))},
                {"label": "Spiele",       "value": format_number(mm.get("games", 0))},
                {"label": "Als Mörder",   "value": format_number(mm.get("murderer_wins", 0))},
                {"label": "Als Detektiv", "value": format_number(mm.get("detective_wins", 0))},
            ],
        },
    ]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/player/<username>")
def player_stats(username):
    uuid_raw, real_name = get_uuid(username)
    if not uuid_raw:
        return jsonify({"error": f"Spieler '{username}' nicht gefunden."}), 404

    data = hypixel_get("player", {"uuid": uuid_raw})
    if not data:
        return jsonify({"error": "Spieler hat Hypixel noch nie gespielt oder ist nicht auffindbar."}), 404

    player = data.get("player", {})
    xp     = player.get("networkExp", 0)
    rank   = get_rank(player)

    status_data  = hypixel_get("status", {"uuid": uuid_raw})
    session      = status_data.get("session", {}) if status_data else {}
    online       = session.get("online", False)
    game_raw     = session.get("gameType", "")
    mode_raw     = session.get("mode", "")
    map_name     = session.get("map")

    game_display = GAME_NAMES.get(game_raw, game_raw.replace("_", " ").title()) if game_raw else None
    mode_display = translate_mode(game_raw, mode_raw) if mode_raw else None

    result = {
        "uuid":               uuid_raw,
        "username":           player.get("displayname", real_name),
        "rank":               rank["label"],
        "rank_color":         rank["color"],
        "level":              calc_network_level(xp),
        "karma":              format_number(player.get("karma", 0)),
        "achievement_points": format_number(player.get("achievementPoints", 0)),
        "skin_url":           f"https://mc-heads.net/avatar/{uuid_raw}/128",
        "body_url":           f"https://mc-heads.net/body/{uuid_raw}/256",
        "games":              build_game_stats(player),
        "status": {
            "online": online,
            "game":   game_display,
            "mode":   mode_display,
            "map":    map_name,
        },
    }

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
