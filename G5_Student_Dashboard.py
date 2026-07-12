import streamlit as st
from supabase import create_client, Client
import datetime
import json
import logging
from typing import Dict, Any, List

# Basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Grade 5 Weekly Study Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 1. Initialize Direct Supabase Connection via Streamlit Secrets
try:
    url = st.secrets["connections"]["supabase"]["supabase_url"]
    key = st.secrets["connections"]["supabase"]["supabase_key"]
    supabase: Client = create_client(url, key)
except Exception as conn_error:
    st.error("🔒 Secrets Configuration Error: Could not read credentials.")
    st.info("💡 **Tatay's Admin Tip:** Ensure your Streamlit Cloud Secrets text box contains the exact fields required.")
    logger.exception("Failed to create Supabase client")
    st.code(str(conn_error))
    st.stop()

st.title("🎓 Grade 5 Daily Learning Dashboard")
st.write("Review your focus areas for today, then complete the quick retrieval quiz to lock in what you learned.")
st.markdown("---")

# 2. Calculate Current Week's Package Date (Sunday Anchor)
today = datetime.date.today()
sunday_offset = (today.weekday() + 1) % 7
current_sunday = today - datetime.timedelta(days=sunday_offset)

# 3. Fetch Weekly Package from Supabase (pull all columns)
try:
    response = (
        supabase.table("weekly_packages")
        .select("*")
        .eq("week_starting_date", str(current_sunday))
        .execute()
    )
    package_data_list = response.data or []
except Exception as e:
    logger.exception("Supabase read failed")
    st.error("⚠️ Could not fetch weekly package from Supabase.")
    st.code(str(e))
    st.stop()

# 4. Handle Empty Package States Safely
weekly_data: Dict[str, Any] = {}

if not package_data_list:
    st.info(f"✨ Great job checking in! Your study package for the week of **{current_sunday.strftime('%B %d, %Y')}** is currently being prepared. Enjoy your break time!")
    st.warning(f"🔧 Technical Debug: The app is looking for a row in Supabase where week_starting_date = '{str(current_sunday)}'")
    st.stop()
else:
    raw_data = package_data_list[0].get("package_data", {}) or {}
    if isinstance(raw_data, str):
        try:
            weekly_data = json.loads(raw_data)
        except Exception:
            logger.exception("Failed to parse package_data JSON")
            weekly_data = {}
    elif isinstance(raw_data, dict):
        weekly_data = raw_data
    else:
        weekly_data = {}

# 5. Map Weekdays to Block Schedule Categories
weekday_map = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday"}
current_weekday_idx = today.weekday()

st.sidebar.header("🕹️ Control Panel")

# Determine the selected_day (user-facing). Use today's mapped day by default.
if current_weekday_idx in weekday_map:
    selected_day = weekday_map[current_weekday_idx]
    st.sidebar.success(f"📆 Today is {selected_day}")
else:
    st.sidebar.info("🏡 Weekend / General Review Mode")
    # Let user pick a weekday to review during weekends or other days
    selected_day = st.sidebar.selectbox("Choose Day to Review", list(weekday_map.values()))

# Safely pull day_data for the selected_day
day_data: Dict[str, Any] = weekly_data.get(selected_day, {}) if weekly_data else {}

# 6. Dynamic Subject Selection with "✅ DONE" Labels
selected_subject = None

# Pull current mastered list from database payload
row_data = package_data_list[0] if package_data_list else {}
db_mastered = row_data.get("mastered_quizzes", []) or []
if not isinstance(db_mastered, list):
    db_mastered = []

# Build subject options from day_data
subject_options: List[str] = []
subject_mapping: Dict[str, str] = {}

if day_data:
    for sub in day_data.keys():
        subject_uid = f"{selected_day}_{sub}"
        display_label = f"{sub} ✅ DONE" if subject_uid in db_mastered else sub
        subject_options.append(display_label)
        subject_mapping[display_label] = sub

if not subject_options:
    st.sidebar.info("No subjects available for the selected day.")
else:
    selected_display = st.sidebar.selectbox("📚 Choose Subject", options=subject_options)
    if selected_display:
        selected_subject = subject_mapping[selected_display]

# ==========================================
# 7. Render Lesson Summary & Gamified Dynamic Quiz Form
# ==========================================
if selected_subject:
    subject_uid = f"{selected_day}_{selected_subject}"

    # Refresh the row data and safe reads
    row_data = package_data_list[0] if package_data_list else {}
    db_mastered = row_data.get("mastered_quizzes", []) or []
    if not isinstance(db_mastered, list):
        db_mastered = []

    # Gatekeeper: already mastered
    if subject_uid in db_mastered:
        st.subheader(f"🏆 {selected_subject} Mastered!")
        st.success("✨ Great job! You have already earned a perfect score and completed this module.")
        char_stats = row_data.get("character_stats", {"level": 1, "xp": 0, "gold": 0}) or {}
        if not isinstance(char_stats, dict):
            char_stats = {"level": 1, "xp": 0, "gold": 0}
        st.info(f"🎯 Quest Objective: Complete. Current Account Standing: Level {char_stats.get('level')} | 🪙 {char_stats.get('gold')} Gold.")
        st.stop()

    subject_data = day_data.get(selected_subject, {}) if day_data else {}
    quiz_data = subject_data.get("quiz", []) or []

    # Persistent session keys
    quiz_active_key = f"active_{subject_uid}"
    submitted_key = f"submitted_{subject_uid}"
    score_key = f"score_{subject_uid}"
    feedback_key = f"feedback_{subject_uid}"
    saved_answers_key = f"saved_answers_{subject_uid}"
    attempt_count_key = f"attempts_{subject_uid}"

    # Initialize session state defaults
    if quiz_active_key not in st.session_state:
        st.session_state[quiz_active_key] = False
    if submitted_key not in st.session_state:
        st.session_state[submitted_key] = False
        st.session_state[score_key] = 0
        st.session_state[feedback_key] = []
        st.session_state[saved_answers_key] = {}
        st.session_state[attempt_count_key] = 0

    # Read Remaining Database Fields Safely
    char_stats = row_data.get("character_stats", {"level": 1, "xp": 0, "gold": 0}) or {}
    if not isinstance(char_stats, dict):
        char_stats = {"level": 1, "xp": 0, "gold": 0}

    db_attempts = row_data.get("quiz_attempts", {}) or {}
    if not isinstance(db_attempts, dict):
        db_attempts = {}

    # Sync attempts DB -> session memory
    if st.session_state[attempt_count_key] == 0:
        st.session_state[attempt_count_key] = db_attempts.get(subject_uid, 0)

    # Sidebar Character Sheet
    st.sidebar.markdown("### 🛡️ Character Sheet")
    col_lvl, col_xp, col_gld = st.sidebar.columns(3)
    col_lvl.metric("Level", f"Lvl {char_stats.get('level', 1)}")
    col_xp.metric("XP", f"{char_stats.get('xp', 0)} / 1000")
    col_gld.metric("Gold", f"🪙 {char_stats.get('gold', 0)}")
    st.sidebar.progress(min(char_stats.get("xp", 0) / 1000, 1.0))
    st.sidebar.markdown(f"🔢 Attempts Made for this subject: **{st.session_state[attempt_count_key]}**")
    st.sidebar.markdown("---")

    # Sidebar Quiz Controls
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

    # SCREEN ROUTING: Reading Mode
    if not st.session_state[quiz_active_key] and not st.session_state[submitted_key]:
        st.subheader(f"📖 Reviewing: {selected_subject}")
        st.info("💡 Read through these core concepts and examples carefully. When you are ready to earn rewards, hit the sidebar button to lock the notes and start your quest!")
        clean_markdown = subject_data.get("summary_markdown", "") or ""
        # Ensure markdown content is shown correctly
        st.markdown(clean_markdown.replace("\\n", "\n"))
    else:
        # Active Testing / Feedback Mode
        st.subheader(f"⚔️ Active Quest: {selected_subject} Challenge")
        if not quiz_data:
            st.info("No quiz items found for this specific subject segment.")
        else:
            with st.container():
                user_answers: Dict[int, Any] = {}

                # Render Quiz Questions
                for i, q in enumerate(quiz_data):
                    q_options = q.get("options", []) or []
                    st.write(f"**Q{i+1}: {q.get('question', '')}**")

                    # If previously submitted, attempt to load saved choice
                    default_idx = None
                    if st.session_state[submitted_key]:
                        saved_val = st.session_state[saved_answers_key].get(i)
                        if saved_val in q_options:
                            default_idx = q_options.index(saved_val)

                    radio_key = f"q_{selected_day}_{selected_subject}_{i}"
                    # Use index only when we have a valid default index. Otherwise omit index so streamlit chooses default (first option).
                    if default_idx is not None:
                        user_answers[i] = st.radio(
                            "Select the best option:",
                            options=q_options,
                            key=radio_key,
                            index=default_idx,
                            disabled=st.session_state[submitted_key],
                        )
                    else:
                        user_answers[i] = st.radio(
                            "Select the best option:",
                            options=q_options,
                            key=radio_key,
                            disabled=st.session_state[submitted_key],
                        )
                    st.write("---")

                # Submission controls
                submit_button = False
                if not st.session_state[submitted_key]:
                    submit_button = st.button("🚀 Submit Final Answers")

                # Evaluation
                if submit_button:
                    # General safety check: ensure each question has a selection
                    unanswered = any(ans in (None, "") for ans in user_answers.values())
                    if unanswered:
                        st.warning(f"⚠️ Please select an answer for all {len(quiz_data)} questions before submitting.")
                    else:
                        score = 0
                        wrong_items = []
                        for i, q in enumerate(quiz_data):
                            if user_answers[i] == q.get("correct_answer"):
                                score += 1
                            else:
                                wrong_items.append(
                                    {
                                        "num": i + 1,
                                        "question": q.get("question", ""),
                                        "your_ans": user_answers[i],
                                        "correct_ans": q.get("correct_answer"),
                                    }
                                )

                        # Update attempts
                        st.session_state[attempt_count_key] += 1
                        db_attempts[subject_uid] = st.session_state[attempt_count_key]

                        level_up_occurred = False
                        xp_earned = 0
                        gold_earned = 0

                        # Only full mastery grants rewards and marking as mastered
                        if score == len(quiz_data):
                            xp_earned = 200
                            gold_earned = 50

                            # First and second try bonuses
                            if st.session_state[attempt_count_key] == 1:
                                xp_earned += 100
                                gold_earned += 25
                            elif st.session_state[attempt_count_key] == 2:
                                xp_earned += 50

                            new_xp = char_stats.get("xp", 0) + xp_earned
                            new_gold = char_stats.get("gold", 0) + gold_earned
                            current_level = char_stats.get("level", 1)

                            # Level up when XP crosses 1000
                            if new_xp >= 1000:
                                current_level += 1
                                new_xp -= 1000
                                level_up_occurred = True

                            char_stats["xp"] = new_xp
                            char_stats["gold"] = new_gold
                            char_stats["level"] = current_level

                            if subject_uid not in db_mastered:
                                db_mastered.append(subject_uid)

                            st.session_state[f"levelup_{subject_uid}"] = level_up_occurred
                            st.session_state[f"loot_xp_{subject_uid}"] = xp_earned
                            st.session_state[f"loot_gold_{subject_uid}"] = gold_earned

                        # Attempt to persist updated tracking to Supabase (best-effort)
                        try:
                            supabase.table("weekly_packages").update(
                                {
                                    "quiz_attempts": db_attempts,
                                    "character_stats": char_stats,
                                    "mastered_quizzes": db_mastered,
                                }
                            ).eq("week_starting_date", str(current_sunday)).execute()
                        except Exception as upload_err:
                            logger.exception("Failed to synchronize rewards to cloud database.")
                            st.sidebar.error("⚠️ Failed to synchronize rewards to cloud database.")

                        # Seal session parameters
                        st.session_state[score_key] = score
                        st.session_state[feedback_key] = wrong_items
                        st.session_state[saved_answers_key] = user_answers
                        st.session_state[submitted_key] = True

                        # Re-render with updated state
                        st.rerun()

            # Feedback screen after submission
            if st.session_state[submitted_key]:
                final_score = st.session_state[score_key]
                total_q = len(quiz_data)
                missed_list = st.session_state[feedback_key] or []

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
                elif final_score >= max(1, total_q // 2):
                    st.success(f"👍 Good effort! You scored {final_score}/{total_q}. Review your mistakes below, open the notes, and try again to unlock the gold reward!")
                else:
                    st.warning(f"📚 You scored {final_score}/{total_q}. Let's re-read the study material closely before your next challenge attempt.")

                # Missed questions
                if missed_list:
                    st.markdown("#### 🔍 Quest Logs: Missed Targets")
                    for item in missed_list:
                        with st.expander(f"❌ Question {item['num']}: {item['question']}"):
                            st.write(f"**Your Answer:** `{item['your_ans']}`")
                            st.write(f"**Correct Answer:** `{item['correct_ans']}`")
