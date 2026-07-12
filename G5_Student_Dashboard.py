import streamlit as st
import datetime
import pytz
from supabase import create_client, Client

# ==========================================
# 1. Page Configuration & Setup
# ==========================================
st.set_page_config(
    page_title="Grade 5 Daily Learning Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Header Text
st.title("🎓 Grade 5 Daily Learning Dashboard")
st.markdown("Review your focus areas for today, then complete the quick retrieval quiz to lock in what you learned.")
st.markdown("---")

# ==========================================
# 2. Establish Direct Supabase Database Connection
# ==========================================
# This reads directly from your [connections.supabase] configuration block
try:
    # If using streamlit-supabase-connection package
    from streamlit_supabase_connection import SupabaseConnection
    supabase = st.connection("supabase", type=SupabaseConnection)
except Exception:
    # Fallback to standard client initialization using the connection secrets structure
    try:
        url = st.secrets["connections"]["supabase"]["url"]
        key = st.secrets["connections"]["supabase"]["anon_key"] # or "key" depending on your exact label
        supabase = create_client(url, key)
    except Exception as conn_err:
        st.error("🔒 Critical Error: Connection to cloud database failed. Verify your [connections.supabase] Secrets syntax.")
        st.stop()

# ==========================================
# 3. Calculate Target Sunday Anchor Date (PH Timezone Aware)
# ==========================================
# Force computation to match Philippine Standard Time (PST) to avoid UTC delay bugs
ph_tz = pytz.timezone("Asia/Manila")
today_ph = datetime.datetime.now(ph_tz).date()

# Calculate the start of the week (Sunday) relative to current PH date
days_since_sunday = today_ph.weekday() + 1 if today_ph.weekday() != 6 else 0
current_sunday = today_ph - datetime.timedelta(days=days_since_sunday)

# Fetch package data from Supabase for all columns
response = supabase.table("weekly_packages") \
    .select("*") \
    .eq("week_starting_date", str(current_sunday)) \
    .execute()

package_data_list = response.data

# ==========================================
# 4. Handle Empty Package States Safely
# ==========================================
weekly_data = {}  # Defends script from NameErrors if DB row is missing

if not package_data_list:
    st.info(f"✨ Great job checking in! Your study package for the week of **{current_sunday.strftime('%B %d, %Y')}** is currently being prepared. Enjoy your break time!")
    st.warning(f"🔧 Technical Debug: The app is looking for a row in Supabase where week_starting_date = '{str(current_sunday)}'")
    st.stop()
else:
    # Extract package payload array object
    raw_data = package_data_list[0].get('package_data', {})
    
    # Auto-parse raw JSON strings if stored explicitly as text strings inside Supabase
    if isinstance(raw_data, str):
        import json
        try:
            weekly_data = json.loads(raw_data)
        except Exception:
            st.error("⚠️ System Error: Failed to parse structural weekly JSON payload.")
            st.stop()
    else:
        weekly_data = raw_data

# ==========================================
# 5. Choose Day to Review
# ==========================================
selected_day = st.sidebar.selectbox(
    "📆 Choose Day to Review",
    options=["Monday", "Tuesday", "Wednesday", "Thursday"]
)

day_data = weekly_data.get(selected_day, {})

# ==========================================
# 6. Dynamic Subject Selection with "✅ DONE" Labels
# ==========================================
selected_subject = None
if selected_day and day_data:
    row_data = package_data_list[0] if package_data_list else {}
    
    # Fetch permanent mastery arrays to calculate completion items
    db_mastered = row_data.get('mastered_quizzes', [])
    if not isinstance(db_mastered, list):
        db_mastered = []

    subject_options = []
    subject_mapping = {}

    for sub in day_data.keys():
        subject_uid = f"{selected_day}_{sub}"
        if subject_uid in db_mastered:
            display_label = f"{sub} ✅ DONE"
        else:
            display_label = sub
        
        subject_options.append(display_label)
        subject_mapping[display_label] = sub

    selected_display = st.sidebar.selectbox("📚 Choose Subject", options=subject_options)
    
    if selected_display:
        selected_subject = subject_mapping[selected_display]

# ==========================================
# 7. Render Lesson Summary & Gamified Dynamic Quiz Form (CORE ENGINE)
# ==========================================
if selected_subject:
    subject_uid = f"{selected_day}_{selected_subject}"
    row_data = package_data_list[0] if package_data_list else {}
    
    # Mastered Quizzes Array Read
    db_mastered = row_data.get('mastered_quizzes', [])
    if not isinstance(db_mastered, list):
        db_mastered = []
    
    # 🛑 CRITICAL GATEKEEPER LOCKOUT: Intercept layout rendering if subject is already perfected
    if subject_uid in db_mastered:
        st.subheader(f"🏆 {selected_subject} Mastered!")
        st.success(f"✨ Great job! You have already earned a perfect score and completed this module. Move on to your remaining daily objectives to level up your character sheet!")
        
        char_stats = row_data.get('character_stats', {"level": 1, "xp": 0, "gold": 0})
        if not isinstance(char_stats, dict):
            char_stats = {"level": 1, "xp": 0, "gold": 0}
            
        st.info(f"🎯 Quest Objective: Complete. Current Account Standing: Level {char_stats.get('level')} | 🪙 {char_stats.get('gold')} Gold.")
        st.stop()

    # --- Proceed normally if subject is NOT mastered yet ---
    subject_data = day_data[selected_subject]
    quiz_data = subject_data.get('quiz', [])
    
    # Define session states unique to this specific subject assignment
    quiz_active_key = f"active_{subject_uid}"
    submitted_key = f"submitted_{subject_uid}"
    score_key = f"score_{subject_uid}"
    feedback_key = f"feedback_{subject_uid}"
    saved_answers_key = f"saved_answers_{subject_uid}"
    attempt_count_key = f"attempts_{subject_uid}"
    
    # Initialize states if missing from application browser cache memory
    if quiz_active_key not in st.session_state:
        st.session_state[quiz_active_key] = False
    if submitted_key not in st.session_state:
        st.session_state[submitted_key] = False
        st.session_state[score_key] = 0
        st.session_state[feedback_key] = []
        st.session_state[saved_answers_key] = {}
        st.session_state[attempt_count_key] = 0

    # Load character stats dictionary safely
    char_stats = row_data.get('character_stats', {"level": 1, "xp": 0, "gold": 0})
    if not isinstance(char_stats, dict):
        char_stats = {"level": 1, "xp": 0, "gold": 0}
        
    db_attempts = row_data.get('quiz_attempts', {})
    if not isinstance(db_attempts, dict):
        db_attempts = {}

    # Sync attempt history values to current session memory
    if st.session_state[attempt_count_key] == 0:
        st.session_state[attempt_count_key] = db_attempts.get(subject_uid, 0)

    # 🎮 SIDEBAR HUD: Render Character Sheet metrics
    st.sidebar.markdown("### 🛡️ Character Sheet")
    col_lvl, col_xp, col_gld = st.sidebar.columns(3)
    col_lvl.metric("Level", f"Lvl {char_stats.get('level', 1)}")
    col_xp.metric("XP", f"{char_stats.get('xp', 0)} / 1000")
    col_gld.metric("Gold", f"🪙 {char_stats.get('gold', 0)}")
    
    st.sidebar.progress(min(char_stats.get('xp', 0) / 1000, 1.0))
    st.sidebar.markdown(f"🔢 Attempts Made for this subject: **{st.session_state[attempt_count_key]}**")
    st.sidebar.markdown("---")

    # SIDEBAR CONTROLLER: Anti-Cheat Navigation Buttons
    st.sidebar.markdown("### 🕹️ Quiz Status")
    if st.session_state[submitted_key]:
        st.sidebar.success("✅ Evaluation Complete!")
        if st.sidebar.button("🔓 Open Study Notes Again"):
            st.session_state[quiz_active_key] = False
            st.session_state[submitted_key] = False  
            st.rerun()
    elif st.session_state[quiz_active_key]:
        st.sidebar.warning("🔒 Testing Mode Active")
        st.sidebar.caption("Study notes are locked away.")
    else:
        if st.sidebar.button("⚔️ Start Quest (Hide Notes)"):
            st.session_state[quiz_active_key] = True
            st.rerun()
            
    st.sidebar.markdown("---")

    # ==========================================
    # DISPLAY ROUTING
    # ==========================================
    
    # LAYOUT STATE A: Study / Reading Mode
    if not st.session_state[quiz_active_key] and not st.session_state[submitted_key]:
        st.subheader(f"📖 Reviewing: {selected_subject}")
        st.info("💡 Read through these core concepts and examples carefully. When you are ready to earn rewards, hit the sidebar button to lock the notes and start your quest!")
        
        clean_markdown = subject_data['summary_markdown'].replace(r'\n', '\n')
        st.markdown(clean_markdown)
        
    # LAYOUT STATE B: Quiz Challenge / Response Mode
    else:
        st.subheader(f"⚔️ Active Quest: {selected_subject} Challenge")
        
        if not quiz_data:
            st.info("No quiz items found for this specific subject segment.")
        else:
            with st.container():
                user_answers = {}
                
                for i, q in enumerate(quiz_data):
                    st.write(f"**Q{i+1}: {q['question']}**")
                    
                    # Read saved choice if form is frozen after submission
                    default_idx = None
                    if st.session_state[submitted_key]:
                        saved_val = st.session_state[saved_answers_key].get(i)
                        if saved_val in q['options']:
                            default_idx = q['options'].index(saved_val)
                    
                    user_answers[i] = st.radio(
                        "Select the best option:", 
                        options=q['options'], 
                        key=f"q_{selected_day}_{selected_subject}_{i}", 
                        index=default_idx,
                        disabled=st.session_state[submitted_key]
                    )
                    st.write("---")
                
                if not st.session_state[submitted_key]:
                    submit_button = st.button("🚀 Submit Final Answers")
                else:
                    submit_button = False
                
                # ==========================================
                # REWARDS & EVALUATION ENGINE
                # ==========================================
                if submit_button:
                    unanswered = any(ans is None for ans in user_answers.values())
                    
                    if unanswered:
                        st.warning("⚠️ Please select an answer for all 5 questions before submitting.")
                    else:
                        score = 0
                        wrong_items = []
                        for i, q in enumerate(quiz_data):
                            if user_answers[i] == q['correct_answer']:
                                score += 1
                            else:
                                wrong_items.append({
                                    "num": i + 1,
                                    "question": q['question'],
                                    "your_ans": user_answers[i],
                                    "correct_ans": q['correct_answer']
                                })
                        
                        # Increment attempt state history metrics
                        st.session_state[attempt_count_key] += 1
                        db_attempts[subject_uid] = st.session_state[attempt_count_key]
                        
                        level_up_occurred = False
                        xp_earned = 0
                        gold_earned = 0
                        
                        # Execute reward calculations if a perfect score is met
                        if score == len(quiz_data):
                            xp_earned = 200
                            gold_earned = 50
                            
                            if st.session_state[attempt_count_key] == 1:
                                xp_earned += 100
                                gold_earned += 25  # Flawless Run Loot Payout
                            elif st.session_state[attempt_count_key] == 2:
                                xp_earned += 50
                            
                            new_xp = char_stats.get('xp', 0) + xp_earned
                            new_gold = char_stats.get('gold', 0) + gold_earned
                            current_level = char_stats.get('level', 1)
                            
                            # Scaling Level Engine Threshold Calculation
                            if new_xp >= 1000:
                                current_level += 1
                                new_xp = new_xp - 1000
                                level_up_occurred = True
                            
                            char_stats['xp'] = new_xp
                            char_stats['gold'] = new_gold
                            char_stats['level'] = current_level
                            
                            # Permanently append subject key to mastery checklist list array
                            db_mastered.append(subject_uid)
                            
                            st.session_state[f"levelup_{subject_uid}"] = level_up_occurred
                            st.session_state[f"loot_xp_{subject_uid}"] = xp_earned
                            st.session_state[f"loot_gold_{subject_uid}"] = gold_earned
                        
                        # Save comprehensive payload directly to Supabase cloud entry row
                        try:
                            supabase.table("weekly_packages")\
                                .update({
                                    "quiz_attempts": db_attempts,
                                    "character_stats": char_stats,
                                    "mastered_quizzes": db_mastered
                                })\
                                .eq("week_starting_date", str(current_sunday))\
                                .execute()
                        except Exception as upload_err:
                            st.sidebar.error("⚠️ Failed to synchronize rewards to cloud database.")
                        
                        # Cache local presentation items
                        st.session_state[score_key] = score
                        st.session_state[feedback_key] = wrong_items
                        st.session_state[saved_answers_key] = user_answers
                        st.session_state[submitted_key] = True
                        
                        # Hard refresh resets UI variables to sync sidebar values immediately
                        st.rerun()

            # ==========================================
            # EVALUATION PRESENTATION FRAME
            # ==========================================
            if st.session_state[submitted_key]:
                final_score = st.session_state[score_key]
                total_q = len(quiz_data)
                missed_list = st.session_state[feedback_key]
                
                st.markdown("### 📊 Quest Summary")
                
                if final_score == total_q:
                    if st.session_state.get(f"levelup_{subject_uid}", False):
                        st.balloons()
                        st.success(f"👑 **LEVEL UP! You reached Level {char_stats.get('level')}!** Outstanding growth!")
                    else:
                        st.balloons()
                        st.success(f"🎉 **Perfect Mastery! Score: {final_score}/{total_q}**")
                    
                    xp_got = st.session_state.get(f"loot_xp_{subject_uid}", 200)
                    gold_got = st.session_state.get(f"loot_gold_{subject_uid}", 50)
                    
                    st.markdown(f"""
                    ### 🎁 Quest Loot Awarded:
                    * **✨ Experience:** `+{xp_got} XP`
                    * **🪙 Gold Tokens:** `+{gold_got} Gold`
                    """)
                elif final_score >= 3:
                    st.success(f"👍 Good effort! You scored {final_score}/{total_q}. Review your mistakes below, open the notes, and try again to unlock the gold reward!")
                else:
                    st.warning(f"📚 You scored {final_score}/{total_q}. Let's re-read the study material closely before your next challenge attempt.")
                
                # Display wrong answer analysis dropdown panels
                if missed_list:
                    st.markdown("#### 🔍 Quest Logs: Missed Targets")
                    for item in missed_list:
                        with st.expander(f"❌ Question {item['num']}: {item['question']}"):
                            st.write(f"**Your Answer:** `{item['your_ans']}`")
                            st.write(f"**Correct Answer:** `{item['correct_ans']}`")
