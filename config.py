"""
Configuration and constants for the Grade 5 Learning Dashboard.
"""

import os
from typing import Dict

# ==========================================
# Page Configuration
# ==========================================
PAGE_CONFIG = {
    "page_title": "Grade 5 Learning Hall",
    "page_icon": "⚔️",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# ==========================================
# Supabase Configuration
# ==========================================
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# ==========================================
# Game Mechanics Configuration
# ==========================================
REWARD_SETTINGS = {
    "journal_entry": {"xp": 50, "gold": 50},
    "quest_perfect": {"xp": 200, "gold": 50},
    "quest_second_attempt": {"xp": 50, "gold": 0},
    "quest_first_attempt_bonus": {"xp": 100, "gold": 25},
}

LEVEL_CONFIG = {
    "base_xp_threshold": 500,
    "xp_per_level": 100,
}

# ==========================================
# Vault Catalog
# ==========================================
VAULT_CATALOG: Dict[str, Dict] = {
    "voucher_30m": {
        "name": "🎮 30-Min Gaming Voucher",
        "cost": 100,
        "desc": "Unlocks 30 minutes of console gaming or modding runtime privileges.",
    },
    "jollibee_burger": {
        "name": "🍔 Jollibee Yumburger Reward",
        "cost": 250,
        "desc": "Claim a real-world Jollibee hamburger snack ordered by Tatay. (Limit: 1 per week)",
    },
    "ai_lording": {
        "name": "🧙‍♂️ 30-Min AI Lording Sandbox",
        "cost": 100,
        "desc": "Unlocks 30 minutes of advanced AI prompt mastery using Google Gemini.",
    },
}

# Weekly item limits
VAULT_LIMITS = {
    "jollibee_burger": 1,  # 1 per week
}

# ==========================================
# Weekday Mapping
# ==========================================
WEEKDAY_MAP = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
}

# ==========================================
# Achievement Definitions (30 Trophies)
# ==========================================
ACHIEVEMENT_DEFINITIONS = [
    # --- LEVEL PROGRESSION PATHS (1 - 6) ---
    {
        "id": "lvl_2",
        "title": "🌱 Novice Squire",
        "desc": "Ascend and reach Character Level 2.",
        "points": 50,
        "gold": 25,
        "condition_type": "level",
        "condition_value": 2,
    },
    {
        "id": "lvl_5",
        "title": "⚔️ Seasoned Knight",
        "desc": "Train hard and hit Character Level 5.",
        "points": 150,
        "gold": 75,
        "condition_type": "level",
        "condition_value": 5,
    },
    {
        "id": "lvl_10",
        "title": "🛡️ Guild Champion",
        "desc": "Cross the threshold to Character Level 10.",
        "points": 300,
        "gold": 150,
        "condition_type": "level",
        "condition_value": 10,
    },
    {
        "id": "lvl_15",
        "title": "👑 Ascended Warlord",
        "desc": "Unlock elite stats by reaching Character Level 15.",
        "points": 500,
        "gold": 250,
        "condition_type": "level",
        "condition_value": 15,
    },
    {
        "id": "lvl_20",
        "title": "🌌 Immortal Legend",
        "desc": "Achieve ultimate status at Character Level 20.",
        "points": 1000,
        "gold": 500,
        "condition_type": "level",
        "condition_value": 20,
    },
    {
        "id": "lvl_max",
        "title": "🌟 Demigod of the Realm",
        "desc": "Break limits to reach Character Level 25 or above.",
        "points": 1500,
        "gold": 750,
        "condition_type": "level",
        "condition_value": 25,
    },
    # --- QUEST BOARD CAMPAIGNS (7 - 12) ---
    {
        "id": "qst_1",
        "title": "🥇 First Blood Victory",
        "desc": "Master your very first core quest module card with a perfect score.",
        "points": 50,
        "gold": 50,
        "condition_type": "quests_completed",
        "condition_value": 1,
    },
    {
        "id": "qst_3",
        "title": "📚 Dedicated Learner",
        "desc": "Successfully clear 3 academic assignment modules.",
        "points": 100,
        "gold": 50,
        "condition_type": "quests_completed",
        "condition_value": 3,
    },
    {
        "id": "qst_5",
        "title": "🦅 Strategic Commander",
        "desc": "Master 5 tactical quest cards on your map screen.",
        "points": 200,
        "gold": 100,
        "condition_type": "quests_completed",
        "condition_value": 5,
    },
    {
        "id": "qst_10",
        "title": "🎓 Master of Scrolls",
        "desc": "Build an elite portfolio by mastering 10 total modules.",
        "points": 400,
        "gold": 200,
        "condition_type": "quests_completed",
        "condition_value": 10,
    },
    {
        "id": "qst_15",
        "title": "🧙‍♂️ Grand Archivist",
        "desc": "Shatter expectations by achieving 15 masteries.",
        "points": 600,
        "gold": 300,
        "condition_type": "quests_completed",
        "condition_value": 15,
    },
    {
        "id": "qst_20",
        "title": "🌋 Campaign Conqueror",
        "desc": "Completely wipe out 20 quest cards across your boards.",
        "points": 1200,
        "gold": 600,
        "condition_type": "quests_completed",
        "condition_value": 20,
    },
    # --- THE ADVENTURER'S JOURNAL LEDGER (13 - 18) ---
    {
        "id": "jrn_1",
        "title": "✍️ First Entry Scripted",
        "desc": "Log your first daily reflection entry in the Guild Journal.",
        "points": 50,
        "gold": 25,
        "condition_type": "journal_entries",
        "condition_value": 1,
    },
    {
        "id": "jrn_3",
        "title": "📜 Scribe Apprentice",
        "desc": "Maintain consistency by logging 3 daily journal scrolls.",
        "points": 100,
        "gold": 50,
        "condition_type": "journal_entries",
        "condition_value": 3,
    },
    {
        "id": "jrn_5",
        "title": "📖 Chronicler of Battles",
        "desc": "Record your travels for 5 days this week.",
        "points": 150,
        "gold": 75,
        "condition_type": "journal_entries",
        "condition_value": 5,
    },
    {
        "id": "jrn_7",
        "title": "🔥 Perfect Weekly Reflection",
        "desc": "Log your journal every single day for a solid week (7 entries).",
        "points": 350,
        "gold": 200,
        "condition_type": "journal_entries",
        "condition_value": 7,
    },
    {
        "id": "jrn_10",
        "title": "🦅 Wise Philosopher",
        "desc": "Amass 10 daily journal entries inside your ledger archive.",
        "points": 500,
        "gold": 250,
        "condition_type": "journal_entries",
        "condition_value": 10,
    },
    {
        "id": "jrn_15",
        "title": "👁️ Absolute Self-Awareness",
        "desc": "Build an unshakeable logging habit with 15 historic entries.",
        "points": 800,
        "gold": 400,
        "condition_type": "journal_entries",
        "condition_value": 15,
    },
    # --- ECONOMIC FORTUNE & GOLD HOARDING (19 - 24) ---
    {
        "id": "gld_100",
        "title": "🪙 Copper Sack",
        "desc": "Accumulate 100 Gold Coins in your active wallet balance.",
        "points": 50,
        "gold": 25,
        "condition_type": "gold",
        "condition_value": 100,
    },
    {
        "id": "gld_300",
        "title": "💼 Merchant Associate",
        "desc": "Build up your savings to 300 Gold Coins.",
        "points": 100,
        "gold": 50,
        "condition_type": "gold",
        "condition_value": 300,
    },
    {
        "id": "gld_500",
        "title": "💰 Wealthy Hoarder",
        "desc": "Cross the massive boundary to 500 Gold Coins.",
        "points": 200,
        "gold": 100,
        "condition_type": "gold",
        "condition_value": 500,
    },
    {
        "id": "gld_1000",
        "title": "💎 Iron Bank Tycoon",
        "desc": "Amass a fortune of 1,000 active Gold Coins.",
        "points": 500,
        "gold": 250,
        "condition_type": "gold",
        "condition_value": 1000,
    },
    {
        "id": "gld_1500",
        "title": "👑 Golden Sovereign",
        "desc": "Reach a legendary bank balance of 1,500 Gold Coins.",
        "points": 800,
        "gold": 400,
        "condition_type": "gold",
        "condition_value": 1500,
    },
    {
        "id": "gld_2000",
        "title": "🛡️ Infinite Treasury Lock",
        "desc": "Hold a staggering 2,000 active Gold Coins simultaneously.",
        "points": 1200,
        "gold": 600,
        "condition_type": "gold",
        "condition_value": 2000,
    },
    # --- VAULT CHECKOUTS & TATAY DEEDS (25 - 30) ---
    {
        "id": "vlt_1",
        "title": "🛒 First Luxury Purchase",
        "desc": "Buy your very first real-world privilege item from the Rewards Vault.",
        "points": 50,
        "gold": 25,
        "condition_type": "rewards_claimed",
        "condition_value": 1,
    },
    {
        "id": "vlt_5",
        "title": "🎮 Entertainment Tycoon",
        "desc": "Successfully purchase and claim 5 vault reward packages.",
        "points": 200,
        "gold": 100,
        "condition_type": "rewards_claimed",
        "condition_value": 5,
    },
    {
        "id": "vlt_10",
        "title": "🏰 Living the High Life",
        "desc": "Cash out a total of 10 real-world reward items over your campaign.",
        "points": 400,
        "gold": 200,
        "condition_type": "rewards_claimed",
        "condition_value": 10,
    },
    {
        "id": "bnt_1",
        "title": "✨ Good Deed Noticed",
        "desc": "Receive your first custom real-world activity bounty grant from Tatay.",
        "points": 100,
        "gold": 50,
        "condition_type": "tatay_bounties",
        "condition_value": 1,
    },
    {
        "id": "bnt_3",
        "title": "💎 Paragon of Behavior",
        "desc": "Earn 3 separate real-world achievement grants for excellent deeds.",
        "points": 250,
        "gold": 125,
        "condition_type": "tatay_bounties",
        "condition_value": 3,
    },
    {
        "id": "bnt_5",
        "title": "🌟 Golden Child Legend",
        "desc": "Earn 5 custom honor grants from Tatay for outstanding helpfulness.",
        "points": 600,
        "gold": 300,
        "condition_type": "tatay_bounties",
        "condition_value": 5,
    },
]

# ==========================================
# Admin Configuration
# ==========================================
ADMIN_PIN = "735819"

# ==========================================
# UI Constants
# ==========================================
SIDEBAR_WIDTH = "sidebar"
MAIN_CONTENT_WIDTH = "main"

# ==========================================
# Database Table Names
# ==========================================
DB_TABLE_WEEKLY_PACKAGES = "weekly_packages"
