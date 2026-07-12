"""
Grade 5 Learning Dashboard - Main Application
A gamified learning platform for Grade 5 students with RPG mechanics.
"""

import streamlit as st
import datetime

from config import WEEKDAY_MAP, VAULT_CATALOG
import ui_components
import business_logic
import utils


# ==========================================
# Application Initialization
# ==========================================
def main():
    """Main application entry point."""
    
    # Configure page
    ui_components.configure_page()
    business_logic.initialize_session_state()
    
    # Initialize Supabase
    try:
        supabase = business_logic.initialize_supabase()
    except Exception as e:
        st.error(f"🔒 {str(e)}")
        st.stop()
    
    # Get current week
    current_sunday = utils.get_current_sunday()
    current_weekday_name = business_logic.get_current_weekday_name()
    
    # Load weekly data
    try:
        package_data_list, weekly_data = business_logic.load_weekly_data(supabase, current_sunday)
    except Exception as e:
        st.error(f"Failed to load package data: {str(e)}")
        st.stop()
    
    # Handle empty package state
    if not package_data_list:
        st.info(f"✨ Great job checking in! Your study package for the week of **{current_sunday.strftime('%B %d, %Y')}** is currently being prepared.")
        st.stop()
    
    # Extract and validate data
    row_data = business_logic.extract_row_data(package_data_list)
    char_stats = row_data["char_stats"]
    db_attempts = row_data["db_attempts"]
    db_mastered = row_data["db_mastered"]
    db_claims = row_data["db_claims"]
    db_journal = row_data["db_journal"]
    db_unlocked_achvs = row_data["db_unlocked_achvs"]
    
    # ==========================================
    # SIDEBAR: Hero Profile & Journal
    # ==========================================
    ui_components.render_hero_profile(char_stats, current_weekday_name)
    
    # Journal save callback
    def on_journal_save(journal_inputs: dict):
    """Callback triggered when the student seals their daily journal."""
    import utils
    from config import REWARD_SETTINGS
    
    # 1. Generate today's date string identifier (e.g., "2026-07-12")
    date_key = utils.get_journal_date_key()
    
    # 2. Check if an entry already exists for today to prevent double rewards
    # We load db_journal from our active session state tracking array
    current_journal = st.session_state.get("db_journal", {})
    
    if date_key in current_journal:
        st.sidebar.warning("⚠️ Journal already sealed for today!")
        return False

    # 3. Append the new input values under today's key
    current_journal[date_key] = {
        "done_today": journal_inputs.get("done_today", ""),
        "tomorrow_plan": journal_inputs.get("tomorrow_plan", ""),
        "hardest_challenge": journal_inputs.get("hardest_challenge", ""),
        "gratitude": journal_inputs.get("gratitude", ""),
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    # 4. Award daily reflection points to the stats dictionary
    updated_stats = st.session_state.get("char_stats", {}).copy()
    xp_reward = REWARD_SETTINGS["journal_entry"]["xp"]
    gold_reward = REWARD_SETTINGS["journal_entry"]["gold"]
    
    updated_stats["xp"] = updated_stats.get("xp", 0) + xp_reward
    updated_stats["gold"] = updated_stats.get("gold", 0) + gold_reward
    
    # Manage level up recalculation tracking boundaries
    import business_logic
    business_logic.process_level_up(updated_stats)
    
    # 5. Commit both blocks together to Supabase
    try:
        current_sunday = utils.get_current_sunday()
        response = supabase.table("weekly_packages").update({
            "db_journal": current_journal,
            "character_stats": updated_stats
        }).eq("week_starting_date", str(current_sunday)).execute()
        
        if response.data:
            # Sync session state so components switch immediately to read-only view
            st.session_state["db_journal"] = current_journal
            st.session_state["char_stats"] = updated_stats
            return True
        else:
            return False
            
    except Exception as e:
        st.error(f"Supabase Sync Error: {str(e)}")
        return False
    
    ui_components.render_journal_section(db_journal, char_stats, current_sunday, on_journal_save)
    ui_components.render_sidebar_navigation(st.session_state)
    
    # ==========================================
    # MAIN INTERFACE: Tabs
    # ==========================================
    tab_board, tab_vault, tab_admin = st.tabs([
        "🏰 Quest Board Landing Hub",
        "🏪 The Gold Token Rewards Vault",
        "🔑 Tatay Admin"
    ])
    
    # ==========================================
    # TAB 1: Quest Board
    # ==========================================
    with tab_board:
        render_quest_board_tab(
            supabase, current_sunday, weekly_data, db_mastered,
            db_attempts, current_weekday_name, char_stats
        )
    
    # ==========================================
    # TAB 2: Rewards Vault
    # ==========================================
    with tab_vault:
        render_vault_tab(supabase, current_sunday, char_stats, db_claims)
    
    # ==========================================
    # TAB 3: Admin Panel
    # ==========================================
    with tab_admin:
        render_admin_tab(
            supabase, current_sunday, weekly_data, db_mastered,
            db_attempts, char_stats, db_claims
        )
    
    # ==========================================
    # Achievements Display (Below Tabs)
    # ==========================================
    render_achievements_section(
        supabase, current_sunday, char_stats, db_mastered,
        db_journal, db_claims, db_unlocked_achvs
    )


def render_quest_board_tab(
    supabase, current_sunday, weekly_data, db_mastered,
    db_attempts, current_weekday_name, char_stats
):
    """Render the quest board tab."""
    
    if st.session_state["active_quest_uid"] is None:
        # Display available quests
        ui_components.render_quest_board_header()
        
        for day_idx, day_name in WEEKDAY_MAP.items():
            is_today = (current_weekday_name == day_name)
            day_subjects = weekly_data.get(day_name, {})
            
            def on_quest_select(uid):
                st.session_state["active_quest_uid"] = uid
                st.rerun()
            
            ui_components.render_day_section(
                day_name, day_subjects, db_mastered, db_attempts,
                is_today, on_quest_select
            )
    
    else:
        # Display active quest module
        active_uid = st.session_state["active_quest_uid"]
        act_day, act_sub = active_uid.split("_", 1)
        subject_data = weekly_data.get(act_day, {}).get(act_sub, {})
        
        def on_quiz_submit(submission_data):
            score, wrong_items, success = business_logic.handle_quiz_submission(
                supabase, current_sunday, submission_data,
                db_attempts, db_mastered, char_stats
            )
            
            if success:
                # Update session state for results display
                state_keys = submission_data["session_state_keys"]
                st.session_state[state_keys["score_key"]] = score
                st.session_state[state_keys["fb_key"]] = wrong_items
                st.session_state[state_keys["ans_key"]] = submission_data["user_choices"]
                st.session_state[state_keys["sub_key"]] = True
                st.rerun()
            else:
                st.error("⚠️ Database sync connection loss recorded.")
        
        ui_components.render_quest_module(
            active_uid, subject_data, st.session_state, on_quiz_submit
        )


def render_vault_tab(supabase, current_sunday, char_stats, db_claims):
    """Render the vault rewards tab."""
    
    ui_components.render_vault_header()
    
    def on_item_purchase(item_id):
        if business_logic.handle_item_purchase(supabase, current_sunday, item_id, char_stats, db_claims):
            item = VAULT_CATALOG.get(item_id)
            st.success(f"🎉 Unlocked: {item['name']}! Notified Tatay.")
            st.balloons()
            st.rerun()
        else:
            st.error("⚠️ Transaction pipeline write failure.")
    
    ui_components.render_vault_catalog(
        VAULT_CATALOG, char_stats, db_claims, on_item_purchase
    )
    
    ui_components.render_claims_history(db_claims)


def render_admin_tab(
    supabase, current_sunday, weekly_data, db_mastered,
    db_attempts, char_stats, db_claims
):
    """Render the admin control panel tab."""
    
    ui_components.render_admin_panel_header()
    
    # Authentication gate
    if not ui_components.render_admin_authentication():
        return
    
    # Build quest matrix
    matrix_data = business_logic.build_quest_status_matrix(
        weekly_data, db_mastered, db_attempts
    )
    
    # Render stats
    total_quests = sum(len(weekly_data.get(day, {})) for day in WEEKDAY_MAP.values())
    ui_components.render_admin_stats(len(db_mastered), total_quests, char_stats.get('level', 1))
    ui_components.render_quest_status_matrix(matrix_data)
    
    # Admin action callbacks
    def on_quest_reset(reset_target):
        if business_logic.handle_quest_reset(supabase, current_sunday, reset_target, db_mastered, db_attempts, st.session_state):
            st.success(f"Successfully unlocked {reset_target}! Re-syncing dashboard layout...")
            st.rerun()
        else:
            st.error(f"Failed to commit override modifications.")
    
    def on_claim_fulfill(claim_id):
        if business_logic.handle_claim_fulfillment(supabase, current_sunday, claim_id, db_claims):
            st.success("Reward stamped as delivered!")
            st.rerun()
        else:
            st.error("Failed to update status column.")
    
    def on_bounty_grant(bounty_name, gold_amount):
        if business_logic.handle_bounty_grant(supabase, current_sunday, bounty_name, gold_amount, char_stats, db_claims):
            st.success(f"🎉 Successfully awarded 🪙 {gold_amount} Gold for: '{bounty_name}'!")
            st.balloons()
            st.rerun()
        else:
            st.error(f"Failed to deposit transaction bounty parameters.")
    
    def on_stats_update(new_stats):
        if business_logic.handle_stats_update(supabase, current_sunday, new_stats):
            st.success("Character attributes successfully modified!")
            st.session_state["active_quest_uid"] = None
            for key in list(st.session_state.keys()):
                if "run_" in key or "active_" in key:
                    del st.session_state[key]
            st.rerun()
        else:
            st.error(f"Failed to sync structural profile overrides.")
    
    # Render admin forms
    ui_components.render_admin_forms(
        matrix_data, db_claims, char_stats,
        on_quest_reset, on_claim_fulfill, on_bounty_grant, on_stats_update
    )
    
    # --- PASTE THE NEW CODE HERE ---
    st.markdown("---")
    st.subheader("📖 Adventurer's Daily Journal Log Archives")
    
    # Read directly from session state
    current_journal_db = st.session_state.get("db_journal", {})
    
    if not current_journal_db:
        st.info("📭 The character has not committed any daily reflection scrolls for this week.")
    else:
        st.caption("Review daily progress submissions chronologically:")
        # Sort history keys so that the most recent entries are on top
        for date_key in sorted(current_journal_db.keys(), reverse=True):
            log = current_journal_db[date_key]
            with st.expander(f"📜 Entry Scroll: {date_key}", expanded=False):
                st.markdown(f"**⚔️ Completed Tasks:** {log.get('done_today', 'Not logged')}")
                st.markdown(f"**🗺️ Upcoming Plans:** {log.get('tomorrow_plan', 'Not logged')}")
                st.markdown(f"**🐉 Tough Encounters:** {log.get('hardest_challenge', 'Not logged')}")
                st.markdown(f"**💎 Expressed Gratitude:** *\"{log.get('gratitude', 'Not logged')}\"*")


def render_achievements_section(
    supabase, current_sunday, char_stats, db_mastered,
    db_journal, db_claims, db_unlocked_achvs
):
    """Render the achievements section."""
    
    from config import ACHIEVEMENT_DEFINITIONS
    
    ui_components.render_achievements_header()
    
    # Process achievements
    newly_unlocked, db_unlocked_achvs, char_stats, total_score = business_logic.handle_achievements(
        supabase, current_sunday, char_stats, db_mastered,
        db_journal, db_claims, db_unlocked_achvs
    )
    
    # Display new unlocks
    for achievement in newly_unlocked:
        st.success(
            f"🎉 NEW TROPHY UNLOCKED: {achievement['title']}! "
            f"Awarded +✨ {achievement['points']} XP & +🪙 {achievement['gold']} Gold!"
        )
    
    # Render stats and grid
    ui_components.render_achievements_stats(total_score, len(db_unlocked_achvs), len(ACHIEVEMENT_DEFINITIONS))
    ui_components.render_achievement_grid(ACHIEVEMENT_DEFINITIONS, db_unlocked_achvs)


if __name__ == "__main__":
    main()
