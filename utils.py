"""
Utility functions for the Grade 5 Learning Dashboard.
Handles database operations, calculations, and data transformations.
"""

import datetime
import json
from typing import Dict, List, Tuple, Any, Optional
from supabase import Client


# ==========================================
# Supabase Database Operations
# ==========================================
def fetch_weekly_package(
    supabase: Client, week_starting_date: datetime.date
) -> Optional[Dict[str, Any]]:
    """
    Fetch the weekly package for a given week.
    
    Args:
        supabase: Supabase client instance
        week_starting_date: The Sunday date of the week
        
    Returns:
        Package data dictionary or None if not found
    """
    try:
        response = supabase.table("weekly_packages") \
            .select("*") \
            .eq("week_starting_date", str(week_starting_date)) \
            .execute()
        return response.data[0] if response.data else None
    except Exception as e:
        raise Exception(f"Failed to fetch weekly package: {str(e)}")


def update_weekly_package(
    supabase: Client,
    week_starting_date: datetime.date,
    updates: Dict[str, Any]
) -> bool:
    """
    Update the weekly package data in Supabase.
    
    Args:
        supabase: Supabase client instance
        week_starting_date: The Sunday date of the week
        updates: Dictionary of fields to update
        
    Returns:
        True if successful, False otherwise
    """
    try:
        supabase.table("weekly_packages").update(updates).eq(
            "week_starting_date", str(week_starting_date)
        ).execute()
        return True
    except Exception as e:
        print(f"Database sync error: {str(e)}")
        return False


# ==========================================
# Date and Time Utilities
# ==========================================
def get_current_sunday() -> datetime.date:
    """
    Calculate the most recent Sunday (Philippines timezone aware).
    
    Returns:
        The Sunday date of the current week
    """
    today = datetime.date.today()
    sunday_offset = (today.weekday() + 1) % 7
    return today - datetime.timedelta(days=sunday_offset)


def get_journal_date_key() -> str:
    """
    Get today's date as a string key for journal entries.
    
    Returns:
        Today's date in YYYY-MM-DD format
    """
    return str(datetime.date.today())


# ==========================================
# Character Statistics Management
# ==========================================
def initialize_char_stats() -> Dict[str, int]:
    """
    Initialize default character statistics.
    
    Returns:
        Default character stats dictionary
    """
    return {"level": 1, "xp": 0, "gold": 0}


def validate_char_stats(char_stats: Any) -> Dict[str, int]:
    """
    Validate and normalize character stats from database.
    
    Args:
        char_stats: Character stats from database (may be malformed)
        
    Returns:
        Valid character stats dictionary
    """
    if not isinstance(char_stats, dict):
        return initialize_char_stats()
    return {
        "level": int(char_stats.get("level", 1)),
        "xp": int(char_stats.get("xp", 0)),
        "gold": int(char_stats.get("gold", 0)),
    }


def calculate_xp_threshold(level: int) -> int:
    """
    Calculate XP threshold needed for next level.
    
    Args:
        level: Current level
        
    Returns:
        XP threshold for the next level
    """
    from config import LEVEL_CONFIG
    return LEVEL_CONFIG["base_xp_threshold"] + (level * LEVEL_CONFIG["xp_per_level"])


def process_level_up(char_stats: Dict[str, int]) -> int:
    """
    Process level ups based on current XP.
    
    Args:
        char_stats: Character statistics dictionary
        
    Returns:
        Number of level ups that occurred
    """
    level_ups = 0
    level = char_stats.get("level", 1)
    current_xp = char_stats.get("xp", 0)
    
    while current_xp >= calculate_xp_threshold(level):
        current_xp -= calculate_xp_threshold(level)
        level += 1
        level_ups += 1
    
    char_stats["level"] = level
    char_stats["xp"] = current_xp
    
    return level_ups


def apply_reward(
    char_stats: Dict[str, int],
    xp_earned: int,
    gold_earned: int
) -> Tuple[Dict[str, int], int]:
    """
    Apply XP and gold rewards, process level ups.
    
    Args:
        char_stats: Character statistics dictionary
        xp_earned: XP to award
        gold_earned: Gold to award
        
    Returns:
        Tuple of (updated char_stats, number_of_level_ups)
    """
    char_stats["xp"] = char_stats.get("xp", 0) + xp_earned
    char_stats["gold"] = char_stats.get("gold", 0) + gold_earned
    
    level_ups = process_level_up(char_stats)
    
    return char_stats, level_ups


# ==========================================
# Weekly Data Processing
# ==========================================
def parse_weekly_data(raw_data: Any) -> Dict[str, Dict]:
    """
    Parse and validate weekly package data from database.
    
    Args:
        raw_data: Raw data from database (may be JSON string or dict)
        
    Returns:
        Parsed weekly data dictionary
    """
    if isinstance(raw_data, str):
        try:
            return json.loads(raw_data)
        except Exception:
            return {}
    elif isinstance(raw_data, dict):
        return raw_data
    return {}


def validate_list_field(field: Any) -> List:
    """
    Validate and normalize list fields from database.
    
    Args:
        field: Field from database
        
    Returns:
        Valid list or empty list
    """
    return field if isinstance(field, list) else []


def validate_dict_field(field: Any) -> Dict:
    """
    Validate and normalize dictionary fields from database.
    
    Args:
        field: Field from database
        
    Returns:
        Valid dictionary or empty dictionary
    """
    return field if isinstance(field, dict) else {}


# ==========================================
# Journal Operations
# ==========================================
def initialize_journal_entry() -> Dict[str, str]:
    """
    Initialize a blank journal entry template.
    
    Returns:
        Empty journal entry dictionary
    """
    return {
        "done_today": "",
        "tomorrow_plan": "",
        "hardest_challenge": "",
        "gratitude": "",
    }


def get_today_journal_entry(db_journal: Dict[str, Any]) -> Dict[str, str]:
    """
    Get today's journal entry or initialize a new one.
    
    Args:
        db_journal: Journal data from database
        
    Returns:
        Today's journal entry
    """
    journal_date_key = get_journal_date_key()
    return db_journal.get(journal_date_key, initialize_journal_entry())


def is_first_journal_entry_today(db_journal: Dict[str, Any]) -> bool:
    """
    Check if journal has been filled out today.
    
    Args:
        db_journal: Journal data from database
        
    Returns:
        True if no entry for today exists
    """
    journal_date_key = get_journal_date_key()
    return journal_date_key not in db_journal


# ==========================================
# Quest and Quiz Operations
# ==========================================
def calculate_quiz_score(user_answers: Dict[int, str], quiz_data: List[Dict]) -> Tuple[int, List[Dict]]:
    """
    Calculate quiz score and compile feedback.
    
    Args:
        user_answers: Dictionary mapping question index to user's answer
        quiz_data: List of quiz question dictionaries
        
    Returns:
        Tuple of (score, list_of_wrong_items)
    """
    score = 0
    wrong_items = []
    
    for i, question in enumerate(quiz_data):
        user_answer = user_answers.get(i, "")
        correct_answer = question.get("correct_answer", "")
        
        if user_answer == correct_answer:
            score += 1
        else:
            wrong_items.append({
                "num": i + 1,
                "q": question.get("question", ""),
                "mine": user_answer,
                "right": correct_answer,
            })
    
    return score, wrong_items


def calculate_quest_rewards(
    score: int,
    total_questions: int,
    attempt_number: int
) -> Tuple[int, int]:
    """
    Calculate XP and gold rewards for quest completion.
    
    Args:
        score: Quiz score
        total_questions: Total number of questions
        attempt_number: Which attempt this is (1-based)
        
    Returns:
        Tuple of (xp_earned, gold_earned)
    """
    from config import REWARD_SETTINGS
    
    xp_earned = 0
    gold_earned = 0
    
    # Perfect score
    if score == total_questions:
        xp_earned = REWARD_SETTINGS["quest_perfect"]["xp"]
        gold_earned = REWARD_SETTINGS["quest_perfect"]["gold"]
        
        # First attempt bonus
        if attempt_number == 1:
            xp_earned += REWARD_SETTINGS["quest_first_attempt_bonus"]["xp"]
            gold_earned += REWARD_SETTINGS["quest_first_attempt_bonus"]["gold"]
        
        # Second attempt bonus
        elif attempt_number == 2:
            xp_earned += REWARD_SETTINGS["quest_second_attempt"]["xp"]
    
    return xp_earned, gold_earned


# ==========================================
# Vault and Rewards Operations
# ==========================================
def count_rewards_claimed(db_claims: List[Dict], item_id: str = None) -> int:
    """
    Count number of rewards claimed.
    
    Args:
        db_claims: List of claimed rewards
        item_id: Optional specific item ID to count (None = all items)
        
    Returns:
        Number of claims matching criteria
    """
    if item_id is None:
        # Count all non-bounty items
        return sum(1 for claim in db_claims if claim.get("item_id") != "real_world_achievement_grant")
    else:
        return sum(1 for claim in db_claims if claim.get("item_id") == item_id)


def count_tatay_bounties(db_claims: List[Dict]) -> int:
    """
    Count number of Tatay bounty awards.
    
    Args:
        db_claims: List of claimed rewards
        
    Returns:
        Number of bounty items
    """
    return sum(1 for claim in db_claims if claim.get("item_id") == "real_world_achievement_grant")


def can_purchase_item(
    char_stats: Dict[str, int],
    item_cost: int,
    item_id: str = None,
    db_claims: List[Dict] = None
) -> bool:
    """
    Check if character can purchase a vault item.
    
    Args:
        char_stats: Character statistics
        item_cost: Cost of the item
        item_id: Optional item ID (for checking limits)
        db_claims: Optional claims list (for checking item limits)
        
    Returns:
        True if purchase is allowed
    """
    from config import VAULT_LIMITS
    
    # Check gold balance
    if char_stats.get("gold", 0) < item_cost:
        return False
    
    # Check item-specific limits
    if item_id and db_claims:
        item_limit = VAULT_LIMITS.get(item_id)
        if item_limit is not None:
            current_count = count_rewards_claimed(db_claims, item_id)
            if current_count >= item_limit:
                return False
    
    return True


def create_claim_entry(item_id: str, item_name: str) -> Dict[str, str]:
    """
    Create a new reward claim entry.
    
    Args:
        item_id: ID of the item being claimed
        item_name: Display name of the item
        
    Returns:
        Claim entry dictionary
    """
    import datetime as dt
    
    return {
        "claim_id": f"claim_{int(dt.datetime.now().timestamp())}",
        "item_id": item_id,
        "item_name": item_name,
        "claimed_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Pending",
    }


def create_bounty_entry(bounty_name: str, gold_amount: int) -> Dict[str, str]:
    """
    Create a new Tatay bounty entry.
    
    Args:
        bounty_name: Name/description of the bounty
        gold_amount: Gold amount awarded
        
    Returns:
        Bounty entry dictionary
    """
    import datetime as dt
    
    return {
        "claim_id": f"bounty_{int(dt.datetime.now().timestamp())}",
        "item_id": "real_world_achievement_grant",
        "item_name": f"✨ Tatay Bounty: {bounty_name} (+🪙 {gold_amount} Gold)",
        "claimed_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Fulfilled",
    }


# ==========================================
# Achievement Operations
# ==========================================
def evaluate_achievement_conditions(
    char_stats: Dict[str, int],
    completed_quests_count: int,
    journal_logs_count: int,
    rewards_claimed_count: int,
    tatay_bounties_count: int,
) -> Dict[str, bool]:
    """
    Evaluate all achievement conditions.
    
    Args:
        char_stats: Character statistics
        completed_quests_count: Number of completed quests
        journal_logs_count: Number of journal entries
        rewards_claimed_count: Number of rewards claimed
        tatay_bounties_count: Number of tatay bounties
        
    Returns:
        Dictionary of achievement_id -> condition_met (bool)
    """
    from config import ACHIEVEMENT_DEFINITIONS
    
    conditions = {}
    current_level = char_stats.get("level", 1)
    current_gold = char_stats.get("gold", 0)
    
    for achievement in ACHIEVEMENT_DEFINITIONS:
        achievement_id = achievement["id"]
        condition_type = achievement["condition_type"]
        condition_value = achievement["condition_value"]
        
        if condition_type == "level":
            conditions[achievement_id] = current_level >= condition_value
        elif condition_type == "quests_completed":
            conditions[achievement_id] = completed_quests_count >= condition_value
        elif condition_type == "journal_entries":
            conditions[achievement_id] = journal_logs_count >= condition_value
        elif condition_type == "gold":
            conditions[achievement_id] = current_gold >= condition_value
        elif condition_type == "rewards_claimed":
            conditions[achievement_id] = rewards_claimed_count >= condition_value
        elif condition_type == "tatay_bounties":
            conditions[achievement_id] = tatay_bounties_count >= condition_value
        else:
            conditions[achievement_id] = False
    
    return conditions


def process_new_achievements(
    achievement_conditions: Dict[str, bool],
    unlocked_achievements: List[str],
    char_stats: Dict[str, int],
) -> Tuple[List[Dict], List[str], Dict[str, int], int]:
    """
    Process newly unlocked achievements and apply rewards.
    
    Args:
        achievement_conditions: Dictionary of achievement_id -> condition_met
        unlocked_achievements: List of already unlocked achievement IDs
        char_stats: Character statistics
        
    Returns:
        Tuple of (newly_unlocked_list, updated_unlocked_achievements, updated_char_stats, total_achievement_score)
    """
    from config import ACHIEVEMENT_DEFINITIONS
    
    newly_unlocked = []
    total_achievement_score = 0
    
    achievement_map = {a["id"]: a for a in ACHIEVEMENT_DEFINITIONS}
    
    for achievement_id, is_met in achievement_conditions.items():
        if is_met:
            achievement = achievement_map.get(achievement_id)
            if achievement:
                total_achievement_score += achievement["points"]
                
                if achievement_id not in unlocked_achievements:
                    unlocked_achievements.append(achievement_id)
                    newly_unlocked.append(achievement)
                    
                    # Apply rewards
                    char_stats["xp"] = char_stats.get("xp", 0) + achievement["points"]
                    char_stats["gold"] = char_stats.get("gold", 0) + achievement["gold"]
                    
                    # Process level ups
                    process_level_up(char_stats)
    
    return newly_unlocked, unlocked_achievements, char_stats, total_achievement_score
