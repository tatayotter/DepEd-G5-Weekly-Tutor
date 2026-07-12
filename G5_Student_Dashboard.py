import streamlit as st
from supabase import create_client, Client
import datetime
import json

# ==========================================
# 1. Page Configuration & Setup
# ==========================================
st.set_page_config(
    page_title="Grade 5 Learning Hall",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling to give a cleaner dark gaming aesthetic
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .quest-card { padding: 20px; border-radius: 12px; background-color: #111; border: 1px solid #333; margin-bottom: 15px; }
    .admin-stat { padding: 15px; border-radius: 8px; background-color: #1a1a1a; border-left: 4px solid #deff9a; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. Secure Supabase Client Handshake
# ==========================================
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

if url and key:
    try:
        final_url = str(url).strip().rstrip("/")
        final_key = str(key).strip()
        supabase: Client = create_client(final_url, final_key)
    except Exception as e:
        st.error(f"🔒 Supabase Initialization Error: {str(e)}")
        st.stop()
else:
    st.error("🔒 Secrets Configuration Error: Credentials could not be extracted.")
    st.stop()

# ==========================================
# 3. Calculate Target Sunday Anchor Date (PH Timezone)
# ==========================================
today = datetime.date.today()
sunday_offset = (today.weekday() + 1) % 7
current_sunday = today - datetime.timedelta(days=sunday_offset)

# Fetch package data from Supabase
response = supabase.table("weekly_packages") \
    .select("*") \
    .eq("week_starting_date", str(current_sunday)) \
    .execute()

package_data_list = response.data

# ==========================================
# 4. Handle Empty Package States Safely
# ==========================================
weekly_data = {}
if not package_data_list:
    st.info(f"✨ Great job checking in! Your study package for the week of **{current_sunday.strftime('%B %d, %Y')}** is currently being prepared.")
    st.stop()
else:
    raw_data = package_data_list[0].get('package_data', {})
    if isinstance(raw_data, str):
        try:
            weekly_data = json.loads(raw_data)
        except Exception:
            weekly_data = {}
    else:
        weekly_data = raw_data

# Map Weekdays for scheduling
weekday_map = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday"}
current_weekday_name = weekday_map.get(today.weekday(), "General Review Mode")

# ==========================================
# 5. Extract Core RPG Arrays from Database Row
# ==========================================
row_data = package_data_list[0] if package_data_list else {}

char_stats = row_data.get('character_stats', {"level": 1, "xp": 0, "gold": 0})
if not isinstance(char_stats, dict): char_stats = {"level": 1, "xp": 0, "gold": 0}

db_attempts = row_data.get('quiz_attempts', {})
if not isinstance(db_attempts, dict): db_attempts = {}

db_mastered = row_data.get('mastered_quizzes', [])
if not isinstance(db_mastered, list): db_mastered = []

db_claims = row_data.get('claimed_rewards', [])
if not isinstance(db_claims, list): db_claims = []

# ==========================================
# 6. SIDEBAR HUD: Render Character Status Sheets
# ==========================================
st.sidebar.title("🛡️ Hero Profile")
st.sidebar.markdown(f"**Current Day Mode:** `{current_weekday_name}`")
st.sidebar.markdown("---")

# Metrics Display Panel
col_lvl, col_xp, col_gld = st.sidebar.columns(3)
col_lvl.metric("Level", f"Lvl {char_stats.get('level', 1)}")
col_xp.metric("XP", f"{char_stats.get('xp', 0)}/1000")
col_gld.metric("Gold Wallet", f"🪙 {char_stats.get('gold', 0)}")

# XP Progress Bar gauge
st.sidebar.progress(min(char_stats.get('xp', 0) / 1000, 1.0))
st.sidebar.markdown("---")

# ==========================================
# 📜 SIDEBAR ADVENTURER'S GUILD JOURNAL LOG
# ==========================================
st.sidebar.markdown("### 📜 Guild Journal Ledger")

# Pull or initialize journal structure from database row safely
db_journal = row_data.get('journal_logs', {})
if not isinstance(db_journal, dict): db_journal = {}

# Use today's calendar date string as the absolute unique key mapping
journal_date_str = str(datetime.date.today())
todays_log = db_journal.get(journal_date_str, {})

# 🔍 CHECK DAILY COMPLETION STATUS & RENDER METADATA BADGES
if journal_date_str in db_journal:
    st.sidebar.success("✅ Journal Sealed for Today!")
    st.sidebar.caption("✨ *Your daily reflection bounty (+🪙 50 Gold) has been securely minted to your wallet.*")
else:
    st.sidebar.info("📝 Journal Status: Pending Today")
    st.sidebar.caption("🎁 *First entry today rewards: +🪙 50 Gold | +✨ 50 XP (Available 7 days a week)*")

# Use a clean sidebar expander window to keep input forms organized
with st.sidebar.expander("✍️ Open Daily Journal Scroll", expanded=journal_date_str not in db_journal):
    st.caption(f"Date: {datetime.date.today().strftime('%A, %b %d')}")
    
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
    
    if st.button("💾 Seal Journal Entry", key="btn_sb_save_daily_journal"):
        is_first_entry_today = journal_date_str not in db_journal
        
        # Build payload schema dictionary
        db_journal[journal_date_str] = {
            "done_today": j_done.strip(),
            "tomorrow_plan": j_tomorrow.strip(),
            "hardest_challenge": j_challenge.strip(),
            "gratitude": j_gratitude.strip()
        }
        
        # Process rewards only on the initial daily creation loop
        if is_first_entry_today:
            char_stats['gold'] = char_stats.get('gold', 0) + 50
            new_xp = char_stats.get('xp', 0) + 50
            lvl = char_stats.get('level', 1)
            
            # Handle Level Up threshold rules (Every 1000 XP)
            if new_xp >= 1000:
                lvl += 1
                new_xp -= 1000
                st.toast("👑 LEVEL UP! Your character grew stronger!")
                
            char_stats['xp'] = new_xp
            char_stats['level'] = lvl
        
        try:
            # Commit both the text logs AND his gold coins back to Supabase
            supabase.table("weekly_packages").update({
                "journal_logs": db_journal,
                "character_stats": char_stats
            }).eq("week_starting_date", str(current_sunday)).execute()
            
            st.sidebar.success("Journal saved!")
            st.balloons()
            st.rerun()
        except Exception as je:
            st.sidebar.error(f"Failed to sync logs: {str(je)}")

st.sidebar.markdown("---")

# Track ongoing active view session states
if "active_quest_uid" not in st.session_state:
    st.session_state["active_quest_uid"] = None

# Back Button if viewing a lesson module
if st.session_state["active_quest_uid"]:
    if st.sidebar.button("🔙 Leave Quest / Return to Hub"):
        st.session_state["active_quest_uid"] = None
        st.rerun()

# ==========================================
# 7. MAIN INTERFACE: The Navigation Tabs
# ==========================================
tab_board, tab_vault, tab_admin = st.tabs([
    "🏰 Quest Board Landing Hub", 
    "🏪 The Gold Token Rewards Vault", 
    "🔑 Tatay Admin"
])

# ----------------------------------------------------
# TAB A: THE VISUAL QUEST BOARD
# ----------------------------------------------------
with tab_board:
    if st.session_state["active_quest_uid"] is None:
        st.title("🗺️ Active Campaign Map")
        st.markdown("Select an open, active quest card from the schedule below to begin your training.")
        st.markdown("---")

        for day_idx, day_name in weekday_map.items():
            is_today = (current_weekday_name == day_name)
            day_header = f"📆 {day_name} Objectives" + (" ⚡ (CURRENT RUN)" if is_today else "")
            
            with st.expander(day_header, expanded=is_today or current_weekday_name == "General Review Mode"):
                day_subjects = weekly_data.get(day_name, {})
                
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
                                    st.session_state["active_quest_uid"] = uid
                                    st.rerun()
                            st.markdown("---")
                            
    else:
        active_uid = st.session_state["active_quest_uid"]
        act_day, act_sub = active_uid.split("_", 1)
        
        subject_data = weekly_data.get(act_day, {}).get(act_sub, {})
        quiz_data = subject_data.get('quiz', [])
        
        q_active_key = f"run_act_{active_uid}"
        q_sub_key = f"run_sub_{active_uid}"
        q_score_key = f"run_scr_{active_uid}"
        q_fb_key = f"run_fb_{active_uid}"
        q_ans_key = f"run_ans_{active_uid}"
        
        if q_active_key not in st.session_state: st.session_state[q_active_key] = False
        if q_sub_key not in st.session_state:
            st.session_state[q_sub_key] = False
            st.session_state[q_score_key] = 0
            st.session_state[q_fb_key] = []
            st.session_state[q_ans_key] = {}

        st.title(f"⚔️ Campaign: {act_sub} ({act_day})")
        
        if not st.session_state[q_active_key] and not st.session_state[q_sub_key]:
            st.info("📖 Read through the core scrolls carefully. When ready to face the challenge, hit 'Start Quest Challenge' below.")
            clean_md = subject_data.get('summary_markdown', '').replace(r'\n', '\n')
            st.markdown(clean_md)
            st.markdown("---")
            if st.button("⚔️ Lock Notes & Start Quest Challenge"):
                st.session_state[q_active_key] = True
                st.rerun()
                
        else:
            st.subheader("📝 Answer all evaluation questions:")
            with st.container():
                user_choices = {}
                for i, q in enumerate(quiz_data):
                    st.write(f"**Q{i+1}: {q['question']}**")
                    
                    def_idx = None
                    if st.session_state[q_sub_key]:
                        saved = st.session_state[q_ans_key].get(i)
                        if saved in q['options']: def_idx = q['options'].index(saved)
                        
                    user_choices[i] = st.radio(
                        "Choose the correct answer:", 
                        options=q['options'], 
                        key=f"form_{active_uid}_{i}", 
                        index=def_idx, 
                        disabled=st.session_state[q_sub_key]
                    )
                    st.write("---")
                    
                if not st.session_state[q_sub_key]:
                    if st.button("🚀 Submit Final Evaluation answers"):
                        score = 0
                        wrong_items = []
                        for i, q in enumerate(quiz_data):
                            if user_choices[i] == q['correct_answer']: score += 1
                            else:
                                wrong_items.append({"num": i+1, "q": q['question'], "mine": user_choices[i], "right": q['correct_answer']})
                        
                        current_attempts = db_attempts.get(active_uid, 0) + 1
                        db_attempts[active_uid] = current_attempts
                        
                        level_up = False
                        xp_earned, gold_earned = 0, 0
                        
                        if score == len(quiz_data):
                            xp_earned = 200
                            gold_earned = 50
                            if current_attempts == 1:
                                xp_earned += 100
                                gold_earned += 25
                            elif current_attempts == 2:
                                xp_earned += 50
                                
                            new_xp = char_stats.get('xp', 0) + xp_earned
                            new_gold = char_stats.get('gold', 0) + gold_earned
                            lvl = char_stats.get('level', 1)
                            
                            if new_xp >= 1000:
                                lvl += 1
                                new_xp -= 1000
                                level_up = True
                                
                            char_stats['xp'] = new_xp
                            char_stats['gold'] = new_gold
                            char_stats['level'] = lvl
                            db_mastered.append(active_uid)
                            
                        try:
                            supabase.table("weekly_packages").update({
                                "quiz_attempts": db_attempts,
                                "character_stats": char_stats,
                                "mastered_quizzes": db_mastered
                            }).eq("week_starting_date", str(current_sunday)).execute()
                        except Exception:
                            st.error("⚠️ Database sync connection loss recorded.")
                            
                        st.session_state[q_score_key] = score
                        st.session_state[q_fb_key] = wrong_items
                        st.session_state[q_ans_key] = user_choices
                        st.session_state[q_sub_key] = True
                        st.rerun()

            if st.session_state[q_sub_key]:
                f_score = st.session_state[q_score_key]
                t_items = len(quiz_data)
                
                if f_score == t_items:
                    st.balloons()
                    st.success("🏆 Perfect Score! You have successfully mastered this assignment module and locked it out!")
                    st.session_state["active_quest_uid"] = None
                    if st.button("🏰 Return to Quest Board Hub"): st.rerun()
                else:
                    st.warning(f"📚 You scored {f_score}/{t_items}. Review missed parameters, then unlock notes to re-study.")
                    if st.button("🔓 Unlock Study Scrolls Again"):
                        st.session_state[q_active_key] = False
                        st.session_state[q_sub_key] = False
                        st.rerun()
                        
                    for item in st.session_state[q_fb_key]:
                        with st.expander(f"❌ Question {item['num']}: {item['q']}"):
                            st.write(f"**Your Choice:** `{item['mine']}`")
                            st.write(f"**Correct Target:** `{item['right']}`")

# ----------------------------------------------------
# TAB B: THE REWARDS VAULT SHOP
# ----------------------------------------------------
with tab_vault:
    st.title("🏪 The Gold Token Rewards Vault")
    st.markdown("Exchange your earned digital gold tokens for real-world privileges and power-ups.")
    st.markdown("---")
    
    # Define current catalog profile structures
    vault_catalog = {
        "voucher_30m": {"name": "🎮 30-Min Gaming Voucher", "cost": 100, "desc": "Unlocks 30 minutes of console gaming or modding runtime privileges."},
        "jollibee_burger": {"name": "🍔 Jollibee Yumburger Reward", "cost": 250, "desc": "Claim a real-world Jollibee hamburger snack ordered by Tatay. (Limit: 1 per week)"},
        "ai_lording": {"name": "🧙‍♂️ 30-Min AI Lording Sandbox", "cost": 100, "desc": "Unlocks 30 minutes of advanced AI prompt mastery using Google Gemini to construct custom worlds and stories."}
    }
    
    current_gold_balance = char_stats.get('gold', 0)
    
    # 🔍 SCAN WEEKLY CLAIMS HISTORY FOR THE BURGER LIMIT
    # Counts how many times 'jollibee_burger' appears in his active week row array
    burger_claims_this_week = sum(1 for claim in db_claims if claim.get("item_id") == "jollibee_burger")
    is_burger_locked_by_limit = burger_claims_this_week >= 1
    
    shop_cols = st.columns(3)
    for idx, (item_id, item_meta) in enumerate(vault_catalog.items()):
        with shop_cols[idx]:
            st.markdown(f"### {item_meta['name']}")
            st.markdown(f"### 🪙 {item_meta['cost']} Gold")
            st.caption(item_meta['desc'])
            st.write("---")
            
            # CONDITION 1: Specific verification check for the weekly Jollibee restriction
            if item_id == "jollibee_burger" and is_burger_locked_by_limit:
                st.button("🔒 Locked (Weekly Limit Reached)", disabled=True, key=f"limit_lock_{item_id}")
                st.caption("⚠️ *You can only unlock 1 Jollibee Yumburger per campaign week.*")
            
            # CONDITION 2: Standard balance verification for items that are affordable
            elif current_gold_balance >= item_meta['cost']:
                if st.button(f"🛒 Purchase Quest Reward", key=f"buy_{item_id}"):
                    new_deducted_gold = current_gold_balance - item_meta['cost']
                    char_stats['gold'] = new_deducted_gold
                    
                    claim_entry = {
                        "claim_id": f"claim_{int(datetime.datetime.now().timestamp())}",
                        "item_id": item_id,
                        "item_name": item_meta['name'],
                        "claimed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "Pending"
                    }
                    db_claims.append(claim_entry)
                    
                    try:
                        supabase.table("weekly_packages").update({
                            "character_stats": char_stats,
                            "claimed_rewards": db_claims
                        }).eq("week_starting_date", str(current_sunday)).execute()
                        
                        st.success(f"🎉 Unlocked: {item_meta['name']}! Notified Tatay.")
                        st.balloons()
                        st.rerun()
                    except Exception:
                        st.error("⚠️ Transaction pipeline write failure.")
            
            # CONDITION 3: Insufficient gold fallback lockout state
            else:
                st.button("🔒 Locked (Insufficient Gold)", disabled=True, key=f"lock_{item_id}")

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
# 🏆 AUTOMATED ACCHIEVEMENTS ENGINE (30 DUAL-REWARD TROPHIES)
# ==========================================
st.markdown("---")
st.markdown("### 🏆 Hero Milestones & Achievements")

# Fetch current metrics cleanly for conditional mapping
completed_quests_count = len(db_mastered)
journal_logs_count = len(db_journal)
current_level_stat = char_stats.get('level', 1)
current_gold_stat = char_stats.get('gold', 0)

# Calculate total historic claims from the database tracking array
total_rewards_claimed = len([c for c in db_claims if c.get('item_id') != 'real_world_achievement_grant'])
total_tatay_bounties = len([c for c in db_claims if c.get('item_id') == 'real_world_achievement_grant'])

# Master Matrix definitions mapping 30 distinct structural rewards with both XP and Gold payouts
achievement_definitions = [
    # --- LEVEL PROGRESSION PATHS (1 - 6) ---
    {"id": "lvl_2", "title": "🌱 Novice Squire", "desc": "Ascend and reach Character Level 2.", "points": 50, "gold": 25, "condition": current_level_stat >= 2},
    {"id": "lvl_5", "title": "⚔️ Seasoned Knight", "desc": "Train hard and hit Character Level 5.", "points": 150, "gold": 75, "condition": current_level_stat >= 5},
    {"id": "lvl_10", "title": "🛡️ Guild Champion", "desc": "Cross the threshold to Character Level 10.", "points": 300, "gold": 150, "condition": current_level_stat >= 10},
    {"id": "lvl_15", "title": "👑 Ascended Warlord", "desc": "Unlock elite stats by reaching Character Level 15.", "points": 500, "gold": 250, "condition": current_level_stat >= 15},
    {"id": "lvl_20", "title": "🌌 Immortal Legend", "desc": "Achieve ultimate status at Character Level 20.", "points": 1000, "gold": 500, "condition": current_level_stat >= 20},
    {"id": "lvl_max", "title": "🌟 Demigod of the Realm", "desc": "Break limits to reach Character Level 25 or above.", "points": 1500, "gold": 750, "condition": current_level_stat >= 25},

    # --- QUEST BOARD CAMPAIGNS (7 - 12) ---
    {"id": "qst_1", "title": "🥇 First Blood Victory", "desc": "Master your very first core quest module card with a perfect score.", "points": 50, "gold": 50, "condition": completed_quests_count >= 1},
    {"id": "qst_3", "title": "📚 Dedicated Learner", "desc": "Successfully clear 3 academic assignment modules.", "points": 100, "gold": 50, "condition": completed_quests_count >= 3},
    {"id": "qst_5", "title": "🦅 Strategic Commander", "desc": "Master 5 tactical quest cards on your map screen.", "points": 200, "gold": 100, "condition": completed_quests_count >= 5},
    {"id": "qst_10", "title": "🎓 Master of Scrolls", "desc": "Build an elite portfolio by mastering 10 total modules.", "points": 400, "gold": 200, "condition": completed_quests_count >= 10},
    {"id": "qst_15", "title": "🧙‍♂️ Grand Archivist", "desc": "Shatter expectations by achieving 15 masteries.", "points": 600, "gold": 300, "condition": completed_quests_count >= 15},
    {"id": "qst_20", "title": "🌋 Campaign Conqueror", "desc": "Completely wipe out 20 quest cards across your boards.", "points": 1200, "gold": 600, "condition": completed_quests_count >= 20},

    # --- THE ADVENTURER'S JOURNAL LEDGER (13 - 18) ---
    {"id": "jrn_1", "title": "✍️ First Entry Scripted", "desc": "Log your first daily reflection entry in the Guild Journal.", "points": 50, "gold": 25, "condition": journal_logs_count >= 1},
    {"id": "jrn_3", "title": "📜 Scribe Apprentice", "desc": "Maintain consistency by logging 3 daily journal scrolls.", "points": 100, "gold": 50, "condition": journal_logs_count >= 3},
    {"id": "jrn_5", "title": "📖 Chronicler of Battles", "desc": "Record your travels for 5 days this week.", "points": 150, "gold": 75, "condition": journal_logs_count >= 5},
    {"id": "jrn_7", "title": "🔥 Perfect Weekly Reflection", "desc": "Log your journal every single day for a solid week (7 entries).", "points": 350, "gold": 200, "condition": journal_logs_count >= 7},
    {"id": "jrn_10", "title": "🦅 Wise Philosopher", "desc": "Amass 10 daily journal entries inside your ledger archive.", "points": 500, "gold": 250, "condition": journal_logs_count >= 10},
    {"id": "jrn_15", "title": "👁️ Absolute Self-Awareness", "desc": "Build an unshakeable logging habit with 15 historic entries.", "points": 800, "gold": 400, "condition": journal_logs_count >= 15},

    # --- ECONOMIC FORTUNE & GOLD HOARDING (19 - 24) ---
    {"id": "gld_100", "title": "🪙 Copper Sack", "desc": "Accumulate 100 Gold Coins in your active wallet balance.", "points": 50, "gold": 25, "condition": current_gold_stat >= 100},
    {"id": "gld_300", "title": "💼 Merchant Associate", "desc": "Build up your savings to 300 Gold Coins.", "points": 100, "gold": 50, "condition": current_gold_stat >= 300},
    {"id": "gld_500", "title": "💰 Wealthy Hoarder", "desc": "Cross the massive boundary to 500 Gold Coins.", "points": 200, "gold": 100, "condition": current_gold_stat >= 500},
    {"id": "gld_1000", "title": "💎 Iron Bank Tycoon", "desc": "Amass a fortune of 1,000 active Gold Coins.", "points": 500, "gold": 250, "condition": current_gold_stat >= 1000},
    {"id": "gld_1500", "title": "👑 Golden Sovereign", "desc": "Reach a legendary bank balance of 1,500 Gold Coins.", "points": 800, "gold": 400, "condition": current_gold_stat >= 1500},
    {"id": "gld_2000", "title": "🛡️ Infinite Treasury Lock", "desc": "Hold a staggering 2,000 active Gold Coins simultaneously.", "points": 1200, "gold": 600, "condition": current_gold_stat >= 2000},

    # --- VAULT CHECKOUTS & TATAY DEEDS (25 - 30) ---
    {"id": "vlt_1", "title": "🛒 First Luxury Purchase", "desc": "Buy your very first real-world privilege item from the Rewards Vault.", "points": 50, "gold": 25, "condition": total_rewards_claimed >= 1},
    {"id": "vlt_5", "title": "🎮 Entertainment Tycoon", "desc": "Successfully purchase and claim 5 vault reward packages.", "points": 200, "gold": 100, "condition": total_rewards_claimed >= 5},
    {"id": "vlt_10", "title": "🏰 Living the High Life", "desc": "Cash out a total of 10 real-world reward items over your campaign.", "points": 400, "gold": 200, "condition": total_rewards_claimed >= 10},
    {"id": "bnt_1", "title": "✨ Good Deed Noticed", "desc": "Receive your first custom real-world activity bounty grant from Tatay.", "points": 100, "gold": 50, "condition": total_tatay_bounties >= 1},
    {"id": "bnt_3", "title": "💎 Paragon of Behavior", "desc": "Earn 3 separate real-world achievement grants for excellent deeds.", "points": 250, "gold": 125, "condition": total_tatay_bounties >= 3},
    {"id": "bnt_5", "title": "🌟 Golden Child Legend", "desc": "Earn 5 custom honor grants from Tatay for outstanding helpfulness.", "points": 600, "gold": 300, "condition": total_tatay_bounties >= 5}
]

# Initialize or fix unlocked structure array parameters inside database safely
if 'unlocked_achievements' not in row_data:
    row_data['unlocked_achievements'] = []
db_unlocked_achvs = row_data.get('unlocked_achievements', [])
if not isinstance(db_unlocked_achvs, list): db_unlocked_achvs = []

newly_unlocked = False
total_achievement_score = 0

# Check real-time parameters and handle instant reward allocations
for achv in achievement_definitions:
    if achv["condition"]:
        total_achievement_score += achv["points"]
        
        if achv["id"] not in db_unlocked_achvs:
            db_unlocked_achvs.append(achv["id"])
            
            # 💎 DUAL REWARD DEPOSIT: Inject both XP and Gold Coins into profile structures
            char_stats['xp'] = char_stats.get('xp', 0) + achv["points"]
            char_stats['gold'] = char_stats.get('gold', 0) + achv["gold"]
            
            # Handle the Adaptive Level Progression Engine check formula
            lvl = char_stats.get('level', 1)
            while True:
                xp_threshold_for_next_level = 500 + (lvl * 100)
                if char_stats['xp'] >= xp_threshold_for_next_level:
                    char_stats['xp'] -= xp_threshold_for_next_level
                    lvl += 1
                    st.toast(f"👑 LEVEL UP! You have ascended to Level {lvl}!")
                else:
                    break
            char_stats['level'] = lvl
                
            newly_unlocked = True
            st.success(f"🎉 NEW TROPHY UNLOCKED: {achv['title']}! Awarded +✨ {achv['points']} XP & +🪙 {achv['gold']} Gold!")

# If a milestone is stamped, commit data states upstream to Supabase instantly
if newly_unlocked:
    try:
        supabase.table("weekly_packages").update({
            "unlocked_achievements": db_unlocked_achvs,
            "character_stats": char_stats
        }).eq("week_starting_date", str(current_sunday)).execute()
    except Exception as ae:
        pass

# Render progress numbers to show complete progression scaling
st.markdown(f"**Total Earned Milestone Points:** `✨ {total_achievement_score} Points` | **Unlocked:** `{len(db_unlocked_achvs)} / 30 Trophies`")

# RENDER DYNAMIC GRID VISUAL CONTAINER LABELS
cols_achv = st.columns(3)
for index, achv in enumerate(achievement_definitions):
    with cols_achv[index % 3]:
        if achv["id"] in db_unlocked_achvs:
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

# ----------------------------------------------------
# TAB C: THE TATAY ADMIN CONTROL PANEL (SECURE)
# ----------------------------------------------------
with tab_admin:
    st.title("🔑 Tatay's Admin Control Panel")
    
    # Simple secure PIN entry field
    admin_pin = st.text_input("Enter Admin Access Key:", type="password", placeholder="••••", key="tatay_admin_master_pin_gate")
    
    # Set your custom secret passkey here (Change this to whatever master PIN you want)
    if admin_pin == "735819":
        st.success("🔓 Access Granted. Welcome back, Tatay.")
        st.markdown("---")
        
        adm_col1, adm_col2 = st.columns([1, 1])
        
        # --- LEFT PANEL: PROGRESS MONITOR & STATISTICS ---
        with adm_col1:
            st.subheader("📊 Campaign Progress Logs")
            
            # Aggregate status details
            total_quests = sum(len(weekly_data.get(day, {})) for day in weekday_map.values())
            completed_quests = len(db_mastered)
            
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
                    <span style='font-size:24px; font-weight:bold;'>Level {char_stats.get('level')}</span>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("#### Subject Status Matrix")
            # Loop over all registered tracking fields to print clear tables summaries
            matrix_data = []
            for day_idx, day_name in weekday_map.items():
                day_subjects = weekly_data.get(day_name, {})
                for sub_name in day_subjects.keys():
                    uid = f"{day_name}_{sub_name}"
                    status = "✅ Mastered" if uid in db_mastered else "❌ Incomplete"
                    attempts = db_attempts.get(uid, 0)
                    matrix_data.append({"Day": day_name, "Subject": sub_name, "Status": status, "Attempts": attempts})
            
            st.table(matrix_data)
            
            # --- EMERGENCY QUEST MANIPULATION / RESETS ---
            st.markdown("#### 🔧 Quest Override Vault")
            
            # Create a clean isolated form block to manage multi-reset widget updates safely
            with st.form(key="tatay_quest_override_reset_form"):
                reset_options = ["-- Choose Target --"] + [f"{m['Day']}_{m['Subject']}" for m in matrix_data]
                
                reset_target = st.selectbox(
                    "Select a Quest Module to Reset:", 
                    options=reset_options,
                    key="admin_quest_reset_dropdown"
                )
                
                submit_reset = st.form_submit_button(label="♻️ Force Reset Quest (Allow Retake)")
                
                if submit_reset and reset_target != "-- Choose Target --":
                    # 1. Safe extraction check: ensure target exists before attempting removal
                    if reset_target in db_mastered:
                        db_mastered.remove(reset_target)
                    
                    # 2. Reset attempt counter safely inside the dictionary tracking parameters
                    db_attempts[reset_target] = 0
                        
                    try:
                        # 3. Synchronize your updated tracking structures directly to Supabase
                        supabase.table("weekly_packages").update({
                            "mastered_quizzes": db_mastered,
                            "quiz_attempts": db_attempts
                        }).eq("week_starting_date", str(current_sunday)).execute()
                        
                        # 4. Aggressive memory purge: Wipe out widget state buffers entirely
                        st.session_state["active_quest_uid"] = None
                        
                        # Kill the specific form cache key to allow successive back-to-back operations
                        if "tatay_quest_override_reset_form" in st.session_state:
                            del st.session_state["tatay_quest_override_reset_form"]
                            
                        # Clear specific quiz radio components and drop down memory logs
                        for cache_key in list(st.session_state.keys()):
                            if "run_" in cache_key or "form_" in cache_key or "admin_quest_reset" in cache_key:
                                del st.session_state[cache_key]
                        
                        st.success(f"Successfully unlocked {reset_target}! Re-syncing dashboard layout...")
                        st.rerun()
                    except Exception as re:
                        st.error(f"Failed to commit override modifications: {str(re)}")
                        
        # --- RIGHT PANEL: REWARDS DESK & STATUS EDITOR ---
        with adm_col2:
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
                            for c in db_claims:
                                if c.get("claim_id") == claim['claim_id']:
                                    c["status"] = "Fulfilled"
                                    
                            try:
                                supabase.table("weekly_packages").update({
                                    "claimed_rewards": db_claims
                                }).eq("week_starting_date", str(current_sunday)).execute()
                                st.success("Reward stamped as delivered!")
                                st.rerun()
                            except Exception:
                                st.error("Failed to update status column.")
                    st.markdown("---")

            # ==========================================
            # 🏆 TATAY'S REAL-WORLD ACHIEVEMENT BOUNTY OFFICE
            # ==========================================
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
                    # 1. Update his live character gold balance
                    char_stats['gold'] = char_stats.get('gold', 0) + bounty_gold
                    
                    # 2. Append a unique event record directly into his history ledger tracking array
                    bounty_entry = {
                        "claim_id": f"bounty_{int(datetime.datetime.now().timestamp())}",
                        "item_id": "real_world_achievement_grant",
                        "item_name": f"✨ Tatay Bounty: {bounty_name.strip()} (+🪙 {bounty_gold} Gold)",
                        "claimed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "Fulfilled" # Marked as fulfilled automatically since it's an award
                    }
                    db_claims.append(bounty_entry)
                    
                    try:
                        # 3. Synchronize data row parameters seamlessly to Supabase
                        supabase.table("weekly_packages").update({
                            "character_stats": char_stats,
                            "claimed_rewards": db_claims
                        }).eq("week_starting_date", str(current_sunday)).execute()
                        
                        st.success(f"🎉 Successfully awarded 🪙 {bounty_gold} Gold for: '{bounty_name}'!")
                        st.balloons()
                        st.rerun()
                    except Exception as be:
                        st.error(f"Failed to deposit transaction bounty parameters: {str(be)}")
                    
            # ==========================================
            # 🧙‍♂️ SECURED GOD MODE STATS EDITOR FORM
            # ==========================================
            st.subheader("🧙‍♂️ Character Stats Modifier (God Mode)")
            
            with st.form(key="tatay_godmode_stats_form"):
                new_level = st.number_input(
                    "Character Level:", 
                    min_value=1, 
                    value=int(char_stats.get('level', 1)),
                    key="admin_edit_level_input"
                )
                
                # 🛡️ Switched from st.slider to st.number_input to make 0 and large values bulletproof
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
                    # 🚀 Safe Level Auto-Calculations:
                    # If you enter an XP value of 1000+, it processes the level up rolls automatically
                    final_xp = new_xp
                    final_lvl = new_level
                    
                    while final_xp >= 1000:
                        final_lvl += 1
                        final_xp -= 1000
                        
                    char_stats['level'] = final_lvl
                    char_stats['xp'] = final_xp
                    char_stats['gold'] = new_gold
                    
                    try:
                        # Commit the sanitized profile attributes securely to Supabase
                        supabase.table("weekly_packages").update({
                            "character_stats": char_stats
                        }).eq("week_starting_date", str(current_sunday)).execute()
                        
                        # Clear active navigation states to ensure layout drawing syncs up perfectly
                        st.session_state["active_quest_uid"] = None
                        for key in list(st.session_state.keys()):
                            if "run_" in key or "active_" in key:
                                del st.session_state[key]
                                
                        st.success("Character attributes successfully modified!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to sync structural profile overrides: {str(e)}")
                        
    elif admin_pin != "":
        st.error("🔒 Incorrect Admin Key. Access Denied.")
