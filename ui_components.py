"""
UI Components for the Grade 5 Learning Dashboard.
Handles rendering of all Streamlit UI elements.
"""

import streamlit as st
import datetime
from typing import Dict, List, Any, Callable


# ==========================================
# Custom Styling
# ==========================================
def apply_custom_styling():
    """Apply custom CSS styling to the dashboard."""
    st.markdown("""
    <style>
        .stButton>button { 
            width: 100%; 
            border-radius: 8px; 
            font-weight: bold; 
        }
        .quest-card { 
            padding: 20px; 
            border-radius: 12px; 
            background-color: #111; 
            border: 1px solid #333; 
            margin-bottom: 15px; 
        }
        .admin-stat { 
            padding: 15px; 
            border-radius: 8px; 
            background-color: #1a1a1a; 
            border-left: 4px solid #deff9a; 
        }
    </style>
    """, unsafe_allow_html=True)


# ==========================================
# Page Configuration
# ==========================================
def configure_page():
    """Configure Streamlit page settings."""
    from config import PAGE_CONFIG
    st.set_page_config(**PAGE_CONFIG)
    apply_custom_styling()


# ==========================================
# Sidebar Components
# ==========================================
def render_hero_profile(char_stats: Dict[str, int], current_weekday_name: str):
    """
    Render the hero profile section in the sidebar.
    
    Args:
        char_stats: Character statistics dictionary
        current_weekday_name: Name of current day or "General Review Mode"
    """
    st.sidebar.title("🛡️ Hero Profile")
    st.sidebar.markdown(f"**Current Day Mode:** `{current_weekday_name}`")
    st.sidebar.markdown("---")
    
    # Metrics Display Panel
    col_lvl, col_xp, col_gld = st.sidebar.columns(3)
    col_lvl.metric("Level", f"Lvl {char_stats.get('level', 1)}")
    col_xp.metric("XP", f"{char_stats.get('xp', 0)}/1000")
    col_gld.metric("Gold Wallet", f"🪙 {char_stats.get('gold', 0)}")
    
    # XP Progress Bar
    st.sidebar.progress(min(char_stats.get('xp', 0) / 1000, 1.0))
    st.sidebar.markdown("---")


def render_journal_section(
    db_journal: Dict[str, Any],
    char_stats: Dict[str, int],
    current_sunday: datetime.date,
    on_save_callback: Callable[[Dict], bool]
) -> bool:
    """
    Render the journal entry section in the sidebar with a true form lock.
    """
    from utils import get_journal_date_key, get_today_journal_entry, is_first_journal_entry_today
    
    st.sidebar.markdown("### 📜 Guild Journal Ledger")
    
    journal_date_str = get_journal_date_key()
    todays_log = get_today_journal_entry(db_journal)
    is_first_entry = is_first_journal_entry_today(db_journal)
    
    # Display status and handle lockout
    if not is_first_entry:
        st.sidebar.success("✅ Journal Sealed for Today!")
        st.sidebar.caption("✨ *Your daily reflection bounty (+🪙 50 Gold) has been securely minted to your wallet.*")
        
        # Display the static sealed review so the student can still read what they wrote
        with st.sidebar.expander("👀 View Today's Sealed Scroll", expanded=False):
            st.markdown(f"**⚔️ Completed:**\n{todays_log.get('done_today', '')}")
            st.markdown(f"**🗺️ Tomorrow's Target:**\n{todays_log.get('tomorrow_plan', '')}")
            st.markdown(f"**🐉 Toughest Foe:**\n{todays_log.get('hardest_challenge', '')}")
            st.markdown(f"**💎 Grateful For:**\n{todays_log.get('gratitude', '')}")
        return True
    
    else:
        st.sidebar.info("📝 Journal Status: Pending Today")
        st.sidebar.caption("🎁 *First entry today rewards: +🪙 50 Gold | +✨ 50 XP*")
    
    # Render interactive form ONLY if no entry exists yet today
    with st.sidebar.expander("✍️ Open Daily Journal Scroll", expanded=True):
        st.caption(f"Date: {datetime.date.today().strftime('%A, %b %d')}")
        
        # Wrapping with a true Streamlit form keeps text inputs in state memory on submit
        with st.form(key="daily_journal_guild_form"):
            j_done = st.text_area(
                "⚔️ What I did today:",
                value=todays_log.get("done_today", ""),
                placeholder="What lessons or activities did you do?",
                key="sb_journal_done_input"
            )
            
            j_tomorrow = st.text_area(
                "🗺️ What I will do tomorrow:",
                value=todays_log.get("tomorrow_plan", ""),
                placeholder="What targets are you tackling next?",
                key="sb_journal_tomorrow_input"
            )
            
            j_challenge = st.text_area(
                "🐉 Hardest challenge today:",
                value=todays_log.get("hardest_challenge", ""),
                placeholder="How did you handle the tough spots?",
                key="sb_journal_challenge_input"
            )
            
            j_gratitude = st.text_input(
                "💎 One thing I'm grateful for:",
                value=todays_log.get("gratitude", ""),
                placeholder="Something fun or kind that happened...",
                key="sb_journal_gratitude_input"
            )
            
            submit_journal = st.form_submit_button("💾 Seal Journal Entry")
            
            if submit_journal:
                # Basic validation to prevent saving completely empty scroll logs
                if not j_done.strip() or not j_tomorrow.strip():
                    st.error("⚠️ The scroll cannot be empty! Record your progress before sealing.")
                    return False
                
                journal_entry = {
                    "done_today": j_done.strip(),
                    "tomorrow_plan": j_tomorrow.strip(),
                    "hardest_challenge": j_challenge.strip(),
                    "gratitude": j_gratitude.strip()
                }
                
                if on_save_callback(journal_entry):
                    st.success("Journal saved successfully!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Failed to sync logs to Supabase.")
                    return False
    
    return True


def render_sidebar_navigation(session_state):
    """
    Render navigation controls in the sidebar.
    
    Args:
        session_state: Streamlit session state object
    """
    st.sidebar.markdown("---")
    
    if session_state.get("active_quest_uid"):
        if st.sidebar.button("🔙 Leave Quest / Return to Hub"):
            session_state["active_quest_uid"] = None
            st.rerun()


# ==========================================
# Quest Board Components
# ==========================================
def render_quest_board_header():
    """Render the quest board header."""
    st.title("🗺️ Active Campaign Map")
    st.markdown("Select an open, active quest card from the schedule below to begin your training.")
    st.markdown("---")


def render_day_section(
    day_name: str,
    day_subjects: Dict[str, Dict],
    db_mastered: List[str],
    db_attempts: Dict[str, int],
    is_today: bool,
    on_quest_select: Callable[[str], None]
):
    """
    Render a single day's quest section.
    
    Args:
        day_name: Name of the day
        day_subjects: Dictionary of subjects for the day
        db_mastered: List of mastered quest IDs
        db_attempts: Dictionary of attempt counts
        is_today: Whether this is the current day
        on_quest_select: Callback when quest is selected
    """
    day_header = f"📆 {day_name} Objectives" + (" ⚡ (CURRENT RUN)" if is_today else "")
    
    with st.expander(day_header, expanded=is_today):
        if not day_subjects:
            st.caption("No quests registered for this specific calendar path.")
        else:
            card_cols = st.columns(len(day_subjects))
            for idx, (sub_name, sub_payload) in enumerate(day_subjects.items()):
                uid = f"{day_name}_{sub_name}"
                is_done = uid in db_mastered
                attempts = db_attempts.get(uid, 0)
                
                with card_cols[idx]:
                    st.markdown(f"### {sub_name}")
                    if is_done:
                        st.success("🏆 MASTERED (Perfect 5/5)")
                        st.caption("✨ Loot rewards claimed! This module is sealed.")
                    else:
                        st.warning("⚔️ Quest Available")
                        st.markdown(f"🔢 *Attempts logged:* `{attempts}`")
                        st.markdown("🎁 *Loot:* `200 XP | 50 Gold`")
                        
                        if st.button("📜 Enter Module", key=f"btn_{uid}"):
                            on_quest_select(uid)
                    st.markdown("---")


def render_quest_module(
    active_uid: str,
    subject_data: Dict[str, Any],
    session_state: Dict,
    on_submit_callback: Callable[[Dict], None]
):
    """
    Render the quest module interface.
    
    Args:
        active_uid: Active quest UID
        subject_data: Subject data for the quest
        session_state: Streamlit session state
        on_submit_callback: Callback for quiz submission
    """
    act_day, act_sub = active_uid.split("_", 1)
    quiz_data = subject_data.get('quiz', [])
    
    q_active_key = f"run_act_{active_uid}"
    q_sub_key = f"run_sub_{active_uid}"
    q_score_key = f"run_scr_{active_uid}"
    q_fb_key = f"run_fb_{active_uid}"
    q_ans_key = f"run_ans_{active_uid}"
    
    # Initialize session state keys
    if q_active_key not in session_state:
        session_state[q_active_key] = False
    if q_sub_key not in session_state:
        session_state[q_sub_key] = False
        session_state[q_score_key] = 0
        session_state[q_fb_key] = []
        session_state[q_ans_key] = {}
    
    st.title(f"⚔️ Campaign: {act_sub} ({act_day})")
    
    # Study phase
    if not session_state[q_active_key] and not session_state[q_sub_key]:
        st.info("📖 Read through the core scrolls carefully. When ready to face the challenge, hit 'Start Quest Challenge' below.")
        clean_md = subject_data.get('summary_markdown', '').replace(r'\n', '\n')
        st.markdown(clean_md)
        st.markdown("---")
        if st.button("⚔️ Lock Notes & Start Quest Challenge"):
            session_state[q_active_key] = True
            st.rerun()
    
    # Quiz phase
    else:
        st.subheader("📝 Answer all evaluation questions:")
        with st.container():
            user_choices = {}
            for i, q in enumerate(quiz_data):
                st.write(f"**Q{i+1}: {q['question']}**")
                
                def_idx = None
                if session_state[q_sub_key]:
                    saved = session_state[q_ans_key].get(i)
                    if saved in q['options']:
                        def_idx = q['options'].index(saved)
                
                user_choices[i] = st.radio(
                    "Choose the correct answer:",
                    options=q['options'],
                    key=f"form_{active_uid}_{i}",
                    index=def_idx,
                    disabled=session_state[q_sub_key]
                )
                st.write("---")
            
            # Submit button (only if not submitted)
            if not session_state[q_sub_key]:
                if st.button("🚀 Submit Final Evaluation answers"):
                    on_submit_callback({
                        "user_choices": user_choices,
                        "active_uid": active_uid,
                        "quiz_data": quiz_data,
                        "session_state_keys": {
                            "score_key": q_score_key,
                            "fb_key": q_fb_key,
                            "ans_key": q_ans_key,
                            "sub_key": q_sub_key,
                        }
                    })
        
        # Results phase
        if session_state[q_sub_key]:
            render_quest_results(
                active_uid,
                session_state[q_score_key],
                len(quiz_data),
                session_state[q_fb_key],
                session_state
            )


def render_quest_results(
    active_uid: str,
    score: int,
    total: int,
    wrong_items: List[Dict],
    session_state: Dict
):
    """
    Render quiz results and feedback.
    
    Args:
        active_uid: Active quest UID
        score: Quiz score
        total: Total questions
        wrong_items: List of incorrect answers
        session_state: Streamlit session state
    """
    if score == total:
        st.balloons()
        st.success("🏆 Perfect Score! You have successfully mastered this assignment module and locked it out!")
        session_state["active_quest_uid"] = None
        if st.button("🏰 Return to Quest Board Hub"):
            st.rerun()
    else:
        st.warning(f"📚 You scored {score}/{total}. Review missed parameters, then unlock notes to re-study.")
        if st.button("🔓 Unlock Study Scrolls Again"):
            q_active_key = f"run_act_{active_uid}"
            q_sub_key = f"run_sub_{active_uid}"
            session_state[q_active_key] = False
            session_state[q_sub_key] = False
            st.rerun()
        
        for item in wrong_items:
            with st.expander(f"❌ Question {item['num']}: {item['q']}"):
                st.write(f"**Your Choice:** `{item['mine']}`")
                st.write(f"**Correct Target:** `{item['right']}`")


# ==========================================
# Vault Components
# ==========================================
def render_vault_header():
    """Render the vault header."""
    st.title("🏪 The Gold Token Rewards Vault")
    st.markdown("Exchange your earned digital gold tokens for real-world privileges and power-ups.")
    st.markdown("---")


def render_vault_catalog(
    vault_catalog: Dict[str, Dict],
    char_stats: Dict[str, int],
    db_claims: List[Dict],
    on_purchase_callback: Callable[[str], None]
):
    """
    Render the vault item catalog.
    
    Args:
        vault_catalog: Dictionary of vault items
        char_stats: Character statistics
        db_claims: List of claimed rewards
        on_purchase_callback: Callback for item purchase
    """
    from utils import can_purchase_item, count_rewards_claimed
    from config import VAULT_LIMITS
    
    current_gold_balance = char_stats.get('gold', 0)
    burger_claims_this_week = count_rewards_claimed(db_claims, "jollibee_burger")
    is_burger_locked_by_limit = burger_claims_this_week >= VAULT_LIMITS.get("jollibee_burger", 1)
    
    shop_cols = st.columns(3)
    for idx, (item_id, item_meta) in enumerate(vault_catalog.items()):
        with shop_cols[idx]:
            st.markdown(f"### {item_meta['name']}")
            st.markdown(f"### 🪙 {item_meta['cost']} Gold")
            st.caption(item_meta['desc'])
            st.write("---")
            
            # Jollibee weekly limit check
            if item_id == "jollibee_burger" and is_burger_locked_by_limit:
                st.button("🔒 Locked (Weekly Limit Reached)", disabled=True, key=f"limit_lock_{item_id}")
                st.caption("⚠️ *You can only unlock 1 Jollibee Yumburger per campaign week.*")
            
            # Standard purchase check
            elif can_purchase_item(char_stats, item_meta['cost'], item_id, db_claims):
                if st.button(f"🛒 Purchase Quest Reward", key=f"buy_{item_id}"):
                    on_purchase_callback(item_id)
            
            # Insufficient gold
            else:
                st.button("🔒 Locked (Insufficient Gold)", disabled=True, key=f"lock_{item_id}")


def render_claims_history(db_claims: List[Dict]):
    """
    Render the purchase history log.
    
    Args:
        db_claims: List of claimed rewards
    """
    if db_claims:
        st.markdown("---")
        st.subheader("📜 Character Purchase History Logs")
        for claim in reversed(db_claims):
            status_symbol = "⏳" if claim.get("status", "Pending") == "Pending" else "✅"
            status_text = "Pending Fulfillment" if claim.get("status", "Pending") == "Pending" else "Fulfillment Completed"
            
            if claim.get("status", "Pending") == "Pending":
                st.info(f"{status_symbol} **{claim['item_name']}** — Purchased on `{claim['claimed_at']}` | Status: *{status_text}*")
            else:
                st.success(f"{status_symbol} **{claim['item_name']}** — Claimed on `{claim['claimed_at']}` | Status: *{status_text}*")


# ==========================================
# Achievement Components
# ==========================================
def render_achievements_header():
    """Render the achievements section header."""
    st.markdown("---")
    st.markdown("### 🏆 Hero Milestones & Achievements")


def render_achievements_stats(
    total_achievement_score: int,
    unlocked_count: int,
    total_count: int
):
    """
    Render achievement statistics.
    
    Args:
        total_achievement_score: Total points earned
        unlocked_count: Number of unlocked achievements
        total_count: Total number of achievements
    """
    st.markdown(f"**Total Earned Milestone Points:** `✨ {total_achievement_score} Points` | **Unlocked:** `{unlocked_count} / {total_count} Trophies`")


def render_achievement_grid(
    achievement_definitions: List[Dict],
    unlocked_achievements: List[str]
):
    """
    Render the achievement grid display.
    
    Args:
        achievement_definitions: List of achievement definitions
        unlocked_achievements: List of unlocked achievement IDs
    """
    cols_achv = st.columns(3)
    for index, achv in enumerate(achievement_definitions):
        with cols_achv[index % 3]:
            if achv["id"] in unlocked_achievements:
                st.markdown(f"""
                <div style="border: 2px solid #deff9a; border-radius: 8px; padding: 12px; background-color: #1a2414; margin-bottom: 12px; min-height: 130px;">
                    <h5 style="margin: 0; color: #deff9a;">{achv['title']}</h5>
                    <p style="font-size: 0.8rem; margin: 5px 0; color: #cccccc; line-height: 1.2;">{achv['desc']}</p>
                    <span style="font-size: 0.75rem; font-weight: bold; color: #deff9a;">✅ +{achv['points']} XP & +🪙 {achv['gold']} Gold</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="border: 1px dashed #555555; border-radius: 8px; padding: 12px; background-color: #111111; margin-bottom: 12px; opacity: 0.5; min-height: 130px;">
                    <h5 style="margin: 0; color: #888888;">🔒 Locked Milestone</h5>
                    <p style="font-size: 0.8rem; margin: 5px 0; color: #666666; line-height: 1.2;">{achv['desc']}</p>
                    <span style="font-size: 0.75rem; color: #888888;">🎁 Reward: {achv['points']} XP / 🪙 {achv['gold']} Gold</span>
                </div>
                """, unsafe_allow_html=True)


# ==========================================
# Admin Components
# ==========================================
def render_admin_panel_header():
    """Render the admin panel header."""
    st.title("🔑 Tatay's Admin Control Panel")


def render_admin_authentication() -> bool:
    """
    Render admin authentication gate.
    
    Returns:
        True if authenticated, False otherwise
    """
    from config import ADMIN_PIN
    
    admin_pin = st.text_input(
        "Enter Admin Access Key:",
        type="password",
        placeholder="••••",
        key="tatay_admin_master_pin_gate"
    )
    
    if admin_pin == ADMIN_PIN:
        st.success("🔓 Access Granted. Welcome back, Tatay.")
        st.markdown("---")
        return True
    elif admin_pin != "":
        st.error("🔒 Incorrect Admin Key. Access Denied.")
        return False
    
    return False


def render_admin_stats(completed_quests: int, total_quests: int, level: int):
    """
    Render admin statistics panel.
    
    Args:
        completed_quests: Number of completed quests
        total_quests: Total number of quests
        level: Current character level
    """
    st.subheader("📊 Campaign Progress Logs")
    
    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        st.markdown(f"""
        <div class='admin-stat'>
            <strong>Campaign Completion</strong><br>
            <span style='font-size:24px; font-weight:bold;'>{completed_quests} / {total_quests} Quests</span>
        </div>
        """, unsafe_allow_html=True)
    with col_stat2:
        st.markdown(f"""
        <div class='admin-stat'>
            <strong>Active Level Standing</strong><br>
            <span style='font-size:24px; font-weight:bold;'>Level {level}</span>
        </div>
        """, unsafe_allow_html=True)


def render_quest_status_matrix(matrix_data: List[Dict]):
    """
    Render the quest status matrix table.
    
    Args:
        matrix_data: List of quest status dictionaries
    """
    st.markdown("#### Subject Status Matrix")
    st.table(matrix_data)


def render_admin_forms(
    matrix_data: List[Dict],
    db_claims: List[Dict],
    char_stats: Dict[str, int],
    on_quest_reset: Callable[[str], None],
    on_claim_fulfill: Callable[[str], None],
    on_bounty_grant: Callable[[str, int], None],
    on_stats_update: Callable[[Dict[str, int]], None]
):
    """
    Render all admin control forms.
    
    Args:
        matrix_data: List of quest status data
        db_claims: List of claimed rewards
        char_stats: Current character stats
        on_quest_reset: Callback for quest reset
        on_claim_fulfill: Callback for claim fulfillment
        on_bounty_grant: Callback for bounty grant
        on_stats_update: Callback for stats update
    """
    adm_col1, adm_col2 = st.columns([1, 1])
    
    with adm_col1:
        render_quest_reset_form(matrix_data, on_quest_reset)
    
    with adm_col2:
        render_rewards_fulfillment_desk(db_claims, on_claim_fulfill)
        render_bounty_grant_form(on_bounty_grant)
        render_stats_modifier_form(char_stats, on_stats_update)


def render_quest_reset_form(matrix_data: List[Dict], on_reset: Callable[[str], None]):
    """Render the quest reset form."""
    st.markdown("#### 🔧 Quest Override Vault")
    
    with st.form(key="tatay_quest_override_reset_form"):
        reset_options = ["-- Choose Target --"] + [f"{m['Day']}_{m['Subject']}" for m in matrix_data]
        reset_target = st.selectbox(
            "Select a Quest Module to Reset:",
            options=reset_options,
            key="admin_quest_reset_dropdown"
        )
        
        submit_reset = st.form_submit_button(label="♻️ Force Reset Quest (Allow Retake)")
        
        if submit_reset and reset_target != "-- Choose Target --":
            on_reset(reset_target)


def render_rewards_fulfillment_desk(db_claims: List[Dict], on_fulfill: Callable[[str], None]):
    """Render the rewards fulfillment desk."""
    st.subheader("📥 Rewards Fulfillment Desk")
    
    pending_claims = [c for c in db_claims if c.get("status", "Pending") == "Pending"]
    
    if not pending_claims:
        st.info("☀️ No pending item orders requiring fulfillment.")
    else:
        for claim in pending_claims:
            with st.container():
                st.markdown(f"**🎁 Reward Ordered:** `{claim['item_name']}`")
                st.caption(f"Purchased on: {claim['claimed_at']}")
                
                if st.button("✅ Mark as Fulfilled / Handed Over", key=f"ful_{claim['claim_id']}"):
                    on_fulfill(claim['claim_id'])
            st.markdown("---")


def render_bounty_grant_form(on_grant: Callable[[str, int], None]):
    """Render the Tatay bounty grant form."""
    st.markdown("---")
    st.subheader("🏆 Award Real-World Achievement Bounty")
    st.caption("Reward good behavior, household deeds, or real-world achievements with custom gold!")
    
    with st.form(key="tatay_real_world_bounty_form"):
        bounty_name = st.text_input(
            "📜 Activity Name / Achievement Title:",
            placeholder="e.g., Helping clean up the kitchen table, Good behavior today",
            key="admin_bounty_title_input"
        )
        
        bounty_gold = st.number_input(
            "🪙 Gold Coins to Award:",
            min_value=1,
            value=50,
            step=5,
            key="admin_bounty_gold_input"
        )
        
        submit_bounty = st.form_submit_button(label="🎁 Grant Gold Bounty to Character")
        
        if submit_bounty and bounty_name.strip() != "":
            on_grant(bounty_name.strip(), bounty_gold)


def render_stats_modifier_form(char_stats: Dict[str, int], on_update: Callable[[Dict[str, int]], None]):
    """Render the character stats modifier form."""
    st.subheader("🧙‍♂️ Character Stats Modifier (God Mode)")
    
    with st.form(key="tatay_godmode_stats_form"):
        new_level = st.number_input(
            "Character Level:",
            min_value=1,
            value=int(char_stats.get('level', 1)),
            key="admin_edit_level_input"
        )
        
        new_xp = st.number_input(
            "Experience Points (XP):",
            min_value=0,
            value=int(char_stats.get('xp', 0)),
            step=10,
            key="admin_edit_xp_numerical_input"
        )
        
        new_gold = st.number_input(
            "Gold Tokens Balance:",
            min_value=0,
            value=int(char_stats.get('gold', 0)),
            key="admin_edit_gold_input"
        )
        
        submit_stats_changes = st.form_submit_button(label="💾 Save Modified Profile Stats")
        
        if submit_stats_changes:
            on_update({
                "level": new_level,
                "xp": new_xp,
                "gold": new_gold
            })
