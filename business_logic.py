"""
Business logic and event handlers for the Grade 5 Learning Dashboard.
Manages data flow, calculations, and database synchronization.
"""

import streamlit as st
import datetime
from typing import Dict, List, Any, Tuple
from supabase import Client

import utils
from config import WEEKDAY_MAP, VAULT_CATALOG, REWARD_SETTINGS


# ==========================================
# Database Initialization & Setup
# ==========================================
def initialize_supabase() -> Client:
    """
    Initialize and validate Supabase connection.
    
    Returns:
        Supabase client instance
        
    Raises:
        Exception if credentials are missing or invalid
    """
    url = None
    key = None
    
    try:
        url = st.secrets["connections"]["supabase"]["supabase_url"]
        key = st.secrets["connections"]["supabase"]["supabase_key"]
    except Exception:
        pass
    
    if not url or not key:
        try:
            url = st.secrets.get("supabase_url") or st.secrets.get("SUPABASE_URL")
            key = st.secrets.get("supabase_key") or st.secrets.get("SUPABASE_KEY")
        except Exception:
            pass
    
    if not url or not key:
        raise Exception("Supabase credentials not found in secrets")
    
    from supabase import create_client
    
    final_url = str(url).strip().rstrip("/")
    final_key = str(key).strip()
    
    try:
        supabase = create_client(final_url, final_key)
        return supabase
    except Exception as e:
        raise Exception(f"Supabase Initialization Error: {str(e)}")


def load_weekly_data(supabase: Client, current_sunday: datetime.date) -> Tuple[Dict, Dict]:
    """
    Load all weekly package data from database.
    
    Args:
        supabase: Supabase client instance
        current_sunday: The Sunday date of the current week
        
    Returns:
        Tuple of (package_data_list, weekly_data)
        
    Raises:
        Exception if package data cannot be loaded
    """
    try:
        response = supabase.table("weekly_packages") \
            .select("*") \
            .eq("week_starting_date", str(current_sunday)) \
            .execute()
        
        package_data_list = response.data
        
        if not package_data_list:
            return [], {}
        
        raw_data = package_data_list[0].get('package_data', {})
        weekly_data = utils.parse_weekly_data(raw_data)
        
        return package_data_list, weekly_data
    
    except Exception as e:
        raise Exception(f"Failed to load weekly data: {str(e)}")


def extract_row_data(package_data_list: List[Dict]) -> Dict[str, Any]:
    """
    Extract and validate all fields from package row data.
    
    Args:
        package_data_list: List of package data from Supabase
        
    Returns:
        Validated row data dictionary
    """
    row_data = package_data_list[0] if package_data_list else {}
    
    char_stats = utils.validate_char_stats(row_data.get('character_stats'))
    db_attempts = utils.validate_dict_field(row_data.get('quiz_attempts'))
    db_mastered = utils.validate_list_field(row_data.get('mastered_quizzes'))
    db_claims = utils.validate_list_field(row_data.get('claimed_rewards'))
    db_journal = utils.validate_dict_field(row_data.get('journal_logs'))
    db_unlocked_achvs = utils.validate_list_field(row_data.get('unlocked_achievements'))
    
    return {
        "char_stats": char_stats,
        "db_attempts": db_attempts,
        "db_mastered": db_mastered,
        "db_claims": db_claims,
        "db_journal": db_journal,
        "db_unlocked_achvs": db_unlocked_achvs,
    }


# ==========================================
# Journal Operations
# ==========================================
def handle_journal_save(
    supabase: Client,
    current_sunday: datetime.date,
    journal_entry: Dict[str, str],
    db_journal: Dict,
    char_stats: Dict,
) -> bool:
    """
    Handle journal entry save and reward allocation.
    
    Args:
        supabase: Supabase client
        current_sunday: The Sunday date of the week
        journal_entry: The journal entry to save
        db_journal: Current journal data
        char_stats: Character stats to update
        
    Returns:
        True if successful, False otherwise
    """
    journal_date_str = utils.get_journal_date_key()
    is_first_entry_today = utils.is_first_journal_entry_today(db_journal)
    
    # Save entry
    db_journal[journal_date_str] = journal_entry
    
    # Apply rewards only on first entry
    if is_first_entry_today:
        xp_reward = REWARD_SETTINGS["journal_entry"]["xp"]
        gold_reward = REWARD_SETTINGS["journal_entry"]["gold"]
        
        char_stats, level_ups = utils.apply_reward(char_stats, xp_reward, gold_reward)
        
        if level_ups > 0:
            st.toast(f"👑 LEVEL UP! You have ascended to Level {char_stats['level']}!")
    
    # Sync to database
    return utils.update_weekly_package(
        supabase,
        current_sunday,
        {
            "journal_logs": db_journal,
            "character_stats": char_stats,
        }
    )


# ==========================================
# Quiz Submission Operations
# ==========================================
def handle_quiz_submission(
    supabase: Client,
    current_sunday: datetime.date,
    submission_data: Dict,
    db_attempts: Dict,
    db_mastered: List,
    char_stats: Dict,
) -> Tuple[int, List[Dict], bool]:
    """
    Handle quiz submission, scoring, and rewards.
    
    Args:
        supabase: Supabase client
        current_sunday: The Sunday date of the week
        submission_data: Quiz submission data
        db_attempts: Quiz attempts dictionary
        db_mastered: List of mastered quizzes
        char_stats: Character stats
        
    Returns:
        Tuple of (score, wrong_items, success)
    """
    user_choices = submission_data["user_choices"]
    active_uid = submission_data["active_uid"]
    quiz_data = submission_data["quiz_data"]
    
    # Calculate score
    score, wrong_items = utils.calculate_quiz_score(user_choices, quiz_data)
    
    # Update attempts
    current_attempts = db_attempts.get(active_uid, 0) + 1
    db_attempts[active_uid] = current_attempts
    
    # Check for perfect score
    is_perfect = score == len(quiz_data)
    
    if is_perfect:
        # Calculate rewards based on attempt number
        xp_earned, gold_earned = utils.calculate_quest_rewards(
            score,
            len(quiz_data),
            current_attempts
        )
        
        char_stats, level_ups = utils.apply_reward(char_stats, xp_earned, gold_earned)
        
        if level_ups > 0:
            st.toast(f"👑 LEVEL UP! You have ascended to Level {char_stats['level']}!")
        
        # Mark as mastered
        if active_uid not in db_mastered:
            db_mastered.append(active_uid)
    
    # Sync to database
    success = utils.update_weekly_package(
        supabase,
        current_sunday,
        {
            "quiz_attempts": db_attempts,
            "character_stats": char_stats,
            "mastered_quizzes": db_mastered,
        }
    )
    
    return score, wrong_items, success


# ==========================================
# Vault Operations
# ==========================================
def handle_item_purchase(
    supabase: Client,
    current_sunday: datetime.date,
    item_id: str,
    char_stats: Dict,
    db_claims: List,
) -> bool:
    """
    Handle vault item purchase.
    
    Args:
        supabase: Supabase client
        current_sunday: The Sunday date of the week
        item_id: ID of item being purchased
        char_stats: Character stats
        db_claims: Claims list
        
    Returns:
        True if successful
    """
    item = VAULT_CATALOG.get(item_id)
    if not item:
        return False
    
    # Deduct gold
    new_gold = char_stats.get("gold", 0) - item["cost"]
    char_stats["gold"] = new_gold
    
    # Create claim entry
    claim_entry = utils.create_claim_entry(item_id, item["name"])
    db_claims.append(claim_entry)
    
    # Sync to database
    return utils.update_weekly_package(
        supabase,
        current_sunday,
        {
            "character_stats": char_stats,
            "claimed_rewards": db_claims,
        }
    )


# ==========================================
# Achievement Operations
# ==========================================
def handle_achievements(
    supabase: Client,
    current_sunday: datetime.date,
    char_stats: Dict,
    db_mastered: List,
    db_journal: Dict,
    db_claims: List,
    db_unlocked_achvs: List,
) -> Tuple[List[Dict], List[str], Dict, int]:
    """
    Evaluate achievements and process unlocks.
    
    Args:
        supabase: Supabase client
        current_sunday: The Sunday date of the week
        char_stats: Character stats
        db_mastered: List of mastered quests
        db_journal: Journal data
        db_claims: Claims data
        db_unlocked_achvs: Already unlocked achievements
        
    Returns:
        Tuple of (newly_unlocked, updated_unlocked, updated_char_stats, total_score)
    """
    completed_quests_count = len(db_mastered)
    journal_logs_count = len(db_journal)
    rewards_claimed_count = utils.count_rewards_claimed(db_claims)
    tatay_bounties_count = utils.count_tatay_bounties(db_claims)
    
    # Evaluate conditions
    conditions = utils.evaluate_achievement_conditions(
        char_stats,
        completed_quests_count,
        journal_logs_count,
        rewards_claimed_count,
        tatay_bounties_count,
    )
    
    # Process new achievements
    newly_unlocked, updated_unlocked, updated_stats, total_score = utils.process_new_achievements(
        conditions,
        db_unlocked_achvs,
        char_stats,
    )
    
    # Sync if new achievements
    if newly_unlocked:
        utils.update_weekly_package(
            supabase,
            current_sunday,
            {
                "unlocked_achievements": updated_unlocked,
                "character_stats": updated_stats,
            }
        )
    
    return newly_unlocked, updated_unlocked, updated_stats, total_score


# ==========================================
# Admin Operations
# ==========================================
def handle_quest_reset(
    supabase: Client,
    current_sunday: datetime.date,
    reset_target: str,
    db_mastered: List,
    db_attempts: Dict,
    session_state: Dict,
) -> bool:
    """
    Handle admin quest reset.
    
    Args:
        supabase: Supabase client
        current_sunday: The Sunday date of the week
        reset_target: Quest UID to reset
        db_mastered: Mastered list
        db_attempts: Attempts dictionary
        session_state: Streamlit session state
        
    Returns:
        True if successful
    """
    # Remove from mastered if present
    if reset_target in db_mastered:
        db_mastered.remove(reset_target)
    
    # Reset attempts
    db_attempts[reset_target] = 0
    
    # Sync to database
    success = utils.update_weekly_package(
        supabase,
        current_sunday,
        {
            "mastered_quizzes": db_mastered,
            "quiz_attempts": db_attempts,
        }
    )
    
    if success:
        # Clear session state
        session_state["active_quest_uid"] = None
        
        # Clear relevant session keys
        for cache_key in list(session_state.keys()):
            if "run_" in cache_key or "form_" in cache_key:
                del session_state[cache_key]
    
    return success


def handle_claim_fulfillment(
    supabase: Client,
    current_sunday: datetime.date,
    claim_id: str,
    db_claims: List,
) -> bool:
    """
    Handle admin claim fulfillment.
    
    Args:
        supabase: Supabase client
        current_sunday: The Sunday date of the week
        claim_id: ID of claim to fulfill
        db_claims: Claims list
        
    Returns:
        True if successful
    """
    for claim in db_claims:
        if claim.get("claim_id") == claim_id:
            claim["status"] = "Fulfilled"
            break
    
    return utils.update_weekly_package(
        supabase,
        current_sunday,
        {"claimed_rewards": db_claims}
    )


def handle_bounty_grant(
    supabase: Client,
    current_sunday: datetime.date,
    bounty_name: str,
    gold_amount: int,
    char_stats: Dict,
    db_claims: List,
) -> bool:
    """
    Handle admin Tatay bounty grant.
    
    Args:
        supabase: Supabase client
        current_sunday: The Sunday date of the week
        bounty_name: Name of bounty
        gold_amount: Gold to award
        char_stats: Character stats
        db_claims: Claims list
        
    Returns:
        True if successful
    """
    # Award gold
    char_stats["gold"] = char_stats.get("gold", 0) + gold_amount
    
    # Create bounty entry
    bounty_entry = utils.create_bounty_entry(bounty_name, gold_amount)
    db_claims.append(bounty_entry)
    
    return utils.update_weekly_package(
        supabase,
        current_sunday,
        {
            "character_stats": char_stats,
            "claimed_rewards": db_claims,
        }
    )


def handle_stats_update(
    supabase: Client,
    current_sunday: datetime.date,
    new_stats: Dict[str, int],
) -> bool:
    """
    Handle admin character stats modification.
    
    Args:
        supabase: Supabase client
        current_sunday: The Sunday date of the week
        new_stats: New stats values
        
    Returns:
        True if successful
    """
    # Process level ups if XP is high
    final_xp = new_stats.get("xp", 0)
    final_lvl = new_stats.get("level", 1)
    
    while final_xp >= 1000:
        final_lvl += 1
        final_xp -= 1000
    
    updated_stats = {
        "level": final_lvl,
        "xp": final_xp,
        "gold": new_stats.get("gold", 0),
    }
    
    return utils.update_weekly_package(
        supabase,
        current_sunday,
        {"character_stats": updated_stats}
    )


# ==========================================
# Data Loading & State Management
# ==========================================
def get_current_weekday_name() -> str:
    """
    Get the current weekday name or review mode.
    
    Returns:
        Weekday name or "General Review Mode"
    """
    today = datetime.date.today()
    return WEEKDAY_MAP.get(today.weekday(), "General Review Mode")


def build_quest_status_matrix(
    weekly_data: Dict,
    db_mastered: List,
    db_attempts: Dict,
) -> List[Dict]:
    """
    Build a matrix of all quest statuses for admin display.
    
    Args:
        weekly_data: Weekly data dictionary
        db_mastered: List of mastered quest IDs
        db_attempts: Attempts dictionary
        
    Returns:
        List of quest status dictionaries
    """
    matrix_data = []
    for day_name in WEEKDAY_MAP.values():
        day_subjects = weekly_data.get(day_name, {})
        for sub_name in day_subjects.keys():
            uid = f"{day_name}_{sub_name}"
            status = "✅ Mastered" if uid in db_mastered else "❌ Incomplete"
            attempts = db_attempts.get(uid, 0)
            matrix_data.append({
                "Day": day_name,
                "Subject": sub_name,
                "Status": status,
                "Attempts": attempts
            })
    return matrix_data


# ==========================================
# Session State Initialization
# ==========================================
def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "active_quest_uid" not in st.session_state:
        st.session_state["active_quest_uid"] = None
