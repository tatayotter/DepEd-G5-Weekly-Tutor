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
    def on_journal_save(journal_entry):
        return business_logic.handle_journal_save(
            supabase, current_sunday, journal_entry, db_journal, char_stats
        )
    
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
