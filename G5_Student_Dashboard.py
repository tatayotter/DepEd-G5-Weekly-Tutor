import streamlit as st
from supabase import create_client, Client
import datetime
import json

# ==========================================
# 1. Page Configuration & Setup
# ==========================================
st.set_page_config(
    page_title="Grade 5 Learning Tavern",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling to give a cleaner dark gaming aesthetic
st.markdown("""
<style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .quest-card { padding: 20px; border-radius: 12px; background-color: #111; border: 1px solid #333; margin-bottom: 15px; }
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

# Fetch or initialize rewards claim list log
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
tab_board, tab_vault = st.tabs(["🏰 Quest Board Landing Hub", "🏪 The Gold Token Rewards Vault"])

# ----------------------------------------------------
# TAB A: THE VISUAL QUEST BOARD
# ----------------------------------------------------
with tab_board:
    # Check if a lesson viewport is actively running or if we should draw the map board
    if st.session_state["active_quest_uid"] is None:
        st.title("🗺️ Active Campaign Map")
        st.markdown("Select an open, active quest card from the schedule below to begin your training.")
        st.markdown("---")

        # Render rows of Day Schedules
        for day_idx, day_name in weekday_map.items():
            is_today = (current_weekday_name == day_name)
            day_header = f"📆 {day_name} Objectives" + (" ⚡ (CURRENT RUN)" if is_today else "")
            
            with st.expander(day_header, expanded=is_today or current_weekday_name == "General Review Mode"):
                day_subjects = weekly_data.get(day_name, {})
                
                if not day_subjects:
                    st.caption("No quests registered for this specific calendar path.")
                else:
                    # Layout active subject cards side-by-side using columns
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
                                
                                # Card action navigation entry trigger
                                if st.button("📜 Enter Module", key=f"btn_{uid}"):
                                    st.session_state["active_quest_uid"] = uid
                                    st.rerun()
                            st.markdown("---")
                            
    else:
        # RESOLVE VIEWPORT ROUTING FOR AN ACTIVE SUBJECT RUN
        active_uid = st.session_state["active_quest_uid"]
        act_day, act_sub = active_uid.split("_", 1)
        
        subject_data = weekly_data.get(act_day, {}).get(act_sub, {})
        quiz_data = subject_data.get('quiz', [])
        
        # Instantiate session keys
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
        
        # SCREEN VIEW A: Study Scroll Reading Window
        if not st.session_state[q_active_key] and not st.session_state[q_sub_key]:
            st.info("📖 Read through the core scrolls carefully. When ready to face the challenge, hit 'Start Quest Challenge' below.")
            clean_md = subject_data.get('summary_markdown', '').replace(r'\n', '\n')
            st.markdown(clean_md)
            
            st.markdown("---")
            if st.button("⚔️ Lock Notes & Start Quest Challenge"):
                st.session_state[q_active_key] = True
                st.rerun()
                
        # SCREEN VIEW B: Active Question Forms Block
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
                        
                        # Increment attempt logs immediately
                        current_attempts = db_attempts.get(active_uid, 0) + 1
                        db_attempts[active_uid] = current_attempts
                        
                        level_up = False
                        xp_earned, gold_earned = 0, 0
                        
                        # Handle perfect score rewards calculations
                        if score == len(quiz_data):
                            xp_earned = 200
                            gold_earned = 50
                            
                            if current_attempts == 1:
                                xp_earned += 100
                                gold_earned += 25 # Flawless run speed bonus loot
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
                            
                        # Commit update parameters back to Supabase rows
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

            # Post submission feedback display cards
            if st.session_state[q_sub_key]:
                f_score = st.session_state[q_score_key]
                t_items = len(quiz_data)
                
                if f_score == t_items:
                    st.balloons()
                    st.success("🏆 Perfect Score! You have successfully mastered this assignment module and locked it out!")
                    st.session_state["active_quest_uid"] = None # Redirects path clear back to board
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
        "jollibee_burger": {"name": "🍔 Jollibee Yumburger Reward", "cost": 250, "desc": "Claim a real-world Jollibee hamburger snack ordered by Tatay."},
        "ai_lording": {"name": "🧙‍♂️ 30-Min AI Lording Sandbox", "cost": 150, "desc": "Unlocks 30 minutes of advanced AI prompt mastery using Google Gemini to construct custom worlds and stories."}
    }
    
    current_gold_balance = char_stats.get('gold', 0)
    
    shop_cols = st.columns(3)
    for idx, (item_id, item_meta) in enumerate(vault_catalog.items()):
        with shop_cols[idx]:
            st.markdown(f"### {item_meta['name']}")
            st.markdown(f"### 🪙 {item_meta['cost']} Gold")
            st.caption(item_meta['desc'])
            st.write("---")
            
            # Check affordability rules
            if current_gold_balance >= item_meta['cost']:
                if st.button(f"🛒 Purchase Quest Reward", key=f"buy_{item_id}"):
                    # Deduct balance sheets
                    new_deducted_gold = current_gold_balance - item_meta['cost']
                    char_stats['gold'] = new_deducted_gold
                    
                    # Log claims timestamps records profiles
                    claim_entry = {
                        "item_id": item_id,
                        "item_name": item_meta['name'],
                        "claimed_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    db_claims.append(claim_entry)
                    
                    # Push deduction transactions payload back to database row updates
                    try:
                        supabase.table("weekly_packages").update({
                            "character_stats": char_stats,
                            "claimed_rewards": db_claims
                        }).eq("week_starting_date", str(current_sunday)).execute()
                        
                        st.success(f"🎉 Successfully unlocked: {item_meta['name']}! Show this screen to Tatay to redeem your prize.")
                        st.balloons()
                        st.rerun()
                    except Exception:
                        st.error("⚠️ Transaction pipeline error during bank write phase.")
            else:
                st.button("🔒 Locked (Insufficient Gold Tokens)", disabled=True, key=f"lock_{item_id}")

    # RENDER PERMANENT REDEMPTION HISTORY LOGS
    if db_claims:
        st.markdown("---")
        st.subheader("📜 Character Purchase History Logs (Show to Tatay to Redeem)")
        for claim in reversed(db_claims):
            st.info(f"✨ **{claim['item_name']}** — Unlocked on `{claim['claimed_at']}` | Status: *Ready for Tatay to fulfill*")
