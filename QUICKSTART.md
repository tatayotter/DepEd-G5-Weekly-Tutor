# Grade 5 Learning Dashboard - Quick Start Guide

## 🚀 Getting Started with the Refactored Code

### Prerequisites
```bash
pip install streamlit supabase python-dotenv
```

### Running the Application

**New (Refactored - Recommended):**
```bash
streamlit run app.py
```

**Old (Original - Deprecated):**
```bash
streamlit run G5_Student_Dashboard.py
```

---

## 📁 File Organization

| File | Lines | Purpose | Key Content |
|------|-------|---------|-------------|
| `app.py` | ~300 | Main orchestrator | Tab rendering, callbacks, main flow |
| `config.py` | ~350 | Configuration | Settings, constants, achievement defs |
| `utils.py` | ~450 | Pure utilities | Calculations, helpers, pure functions |
| `business_logic.py` | ~400 | Event handlers | Business rules, data processing |
| `ui_components.py` | ~700 | UI rendering | Streamlit components, forms, displays |

---

## 🎮 Features Overview

### 1. **Quest Board** 🏰
- Browse daily quests by subject
- Study materials for each topic
- Complete quizzes and earn rewards
- Track mastery and attempts

**Key Functions:**
- `render_quest_board_tab()` - Main quest display
- `render_quest_module()` - Quiz interface
- `handle_quiz_submission()` - Score processing

### 2. **Rewards Vault** 🏪
- Purchase items with earned gold
- View purchase history
- Track item status (pending/fulfilled)

**Key Functions:**
- `render_vault_catalog()` - Item display
- `handle_item_purchase()` - Purchase logic
- `can_purchase_item()` - Availability check

### 3. **Achievements** 🏆
- 30 unlockable trophies
- Automatic unlock on condition met
- Dual rewards (XP + Gold)
- Progress tracking

**Achievement Types:**
- Level progression (6 achievements)
- Quest completion (6 achievements)
- Journal entries (6 achievements)
- Gold accumulation (6 achievements)
- Vault purchases (3 achievements)
- Tatay bounties (3 achievements)

### 4. **Admin Panel** 🔑
- Quest reset & unlock
- Reward fulfillment
- Bounty grants
- Character stats editing

**Admin PIN:** `735819` (change in `config.py`)

### 5. **Journal** 📝
- Daily reflection entries
- Auto-save to database
- First entry bonus (50 XP + 50 Gold)
- Track daily activities

---

## 🔧 Common Modifications

### Change Admin PIN
```python
# config.py
ADMIN_PIN = "YOUR_NEW_PIN"
```

### Adjust XP Progression
```python
# config.py
LEVEL_CONFIG = {
    "base_xp_threshold": 600,    # Changed from 500
    "xp_per_level": 120,          # Changed from 100
}
```

### Add Vault Item
```python
# config.py - VAULT_CATALOG
"new_item": {
    "name": "🎮 New Item Name",
    "cost": 150,
    "desc": "Item description here",
},
```

### Create New Achievement
```python
# config.py - ACHIEVEMENT_DEFINITIONS (add to list)
{
    "id": "special_award",
    "title": "🌟 Special Award",
    "desc": "Achievement description",
    "points": 100,
    "gold": 50,
    "condition_type": "custom_condition",
    "condition_value": 1,
}
```

### Change Game Rewards
```python
# config.py - REWARD_SETTINGS
"journal_entry": {"xp": 75, "gold": 60},      # Journal bonus
"quest_perfect": {"xp": 250, "gold": 75},     # Perfect quiz
"quest_first_attempt_bonus": {"xp": 150, "gold": 35},  # First try bonus
```

---

## 📊 Data Flow Example: Quiz Submission

```
User clicks "Submit Quiz Answers"
    ↓
render_quest_module() captures answers
    ↓
on_quiz_submit() callback triggered
    ↓
handle_quiz_submission() processes:
  1. calculate_quiz_score() → score & wrong items
  2. apply_reward() → XP + Gold
  3. process_level_up() → check for level up
  4. Update database
    ↓
Results displayed:
  - Perfect score → Show success
  - Partial score → Show feedback with corrections
    ↓
Achievements checked & rewards applied
    ↓
UI refreshes with new stats
```

---

## 🧪 Testing Individual Components

### Test Character Progression
```python
from utils import apply_reward, process_level_up

# Create test character
char_stats = {"level": 1, "xp": 0, "gold": 0}

# Award 500 XP (should level up)
char_stats, levels = apply_reward(char_stats, 500, 50)

print(f"Level: {char_stats['level']}")      # Should be 2
print(f"XP: {char_stats['xp']}")            # Overflow XP
print(f"Levels gained: {levels}")           # Should be 1
```

### Test Quiz Scoring
```python
from utils import calculate_quiz_score

quiz_data = [
    {"question": "Q1", "options": ["A", "B", "C"], "correct_answer": "A"},
    {"question": "Q2", "options": ["X", "Y", "Z"], "correct_answer": "Y"},
]

answers = {0: "A", 1: "Y"}  # Perfect score

score, wrong = calculate_quiz_score(answers, quiz_data)
print(f"Score: {score}/2")   # Should be 2
print(f"Wrong items: {wrong}")  # Should be []
```

### Test Vault Purchase
```python
from utils import can_purchase_item
from config import VAULT_CATALOG

char_stats = {"level": 5, "xp": 100, "gold": 200}
db_claims = []

can_buy = can_purchase_item(
    char_stats, 
    VAULT_CATALOG["voucher_30m"]["cost"],
    "voucher_30m",
    db_claims
)
print(f"Can purchase: {can_buy}")  # Should be True
```

---

## 🐛 Debugging Tips

### Enable Streamlit Debug Mode
```bash
streamlit run app.py --logger.level=debug
```

### Add Debug Output
```python
# Add to any function:
st.write("DEBUG:", variable_name)  # Inline debug output
print(f"Debug: {variable_name}")    # Console output
```

### Check Database Directly
1. Go to Supabase dashboard
2. Navigate to `weekly_packages` table
3. View raw row data
4. Verify fields are being saved correctly

### Common Issues

**Issue:** Database sync fails
- Check Supabase credentials in secrets
- Verify internet connection
- Check database row exists for this week

**Issue:** Quiz submission does nothing
- Check browser console for errors
- Verify quiz_data has all required fields
- Ensure session state keys are initialized

**Issue:** Admin panel locked
- Verify admin PIN in `config.py`
- Check you typed PIN correctly
- Make sure PIN changed if you modified config

---

## 📈 Database Schema

### weekly_packages Table
```json
{
  "week_starting_date": "2024-01-07",
  "package_data": {...},
  "character_stats": {
    "level": 5,
    "xp": 250,
    "gold": 500
  },
  "quiz_attempts": {
    "Monday_Math": 2,
    "Tuesday_Science": 1
  },
  "mastered_quizzes": ["Monday_Math", "Tuesday_Science"],
  "journal_logs": {
    "2024-01-08": {
      "done_today": "Completed math lessons",
      "tomorrow_plan": "Study science",
      "hardest_challenge": "Fractions",
      "gratitude": "Mom helped me"
    }
  },
  "claimed_rewards": [
    {
      "claim_id": "claim_1234567890",
      "item_id": "voucher_30m",
      "item_name": "🎮 30-Min Gaming Voucher",
      "claimed_at": "2024-01-08 15:30:45",
      "status": "Pending"
    }
  ],
  "unlocked_achievements": ["lvl_2", "qst_1", "jrn_1"]
}
```

---

## 🚀 Deployment

### Option 1: Streamlit Community Cloud
```bash
# Push to GitHub
git push origin main

# In Streamlit Community Cloud:
# 1. Connect your GitHub repo
# 2. Select "app.py" as main file
# 3. Add secrets:
#    - SUPABASE_URL
#    - SUPABASE_KEY
# 4. Deploy!
```

### Option 2: Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

```bash
docker build -t g5-dashboard .
docker run -p 8501:8501 g5-dashboard
```

---

## 📚 Additional Resources

### Module Documentation
- Read `README_REFACTORING.md` for detailed architecture
- Check docstrings in each module for function details
- Type hints provide IDE autocomplete support

### Code Examples
```python
# Import examples
from config import ACHIEVEMENT_DEFINITIONS, VAULT_CATALOG
from utils import apply_reward, calculate_quiz_score
from business_logic import handle_journal_save
import ui_components

# Usage examples
import ui_components
ui_components.render_hero_profile(char_stats, "Monday")
```

---

## 🎯 Quick Reference: Adding Features

### Add New Vault Item
1. Add to `config.py` → `VAULT_CATALOG`
2. Run - UI updates automatically ✓

### Add New Achievement
1. Add to `config.py` → `ACHIEVEMENT_DEFINITIONS`
2. Update condition in `utils.py` → `evaluate_achievement_conditions()`
3. Run - UI updates automatically ✓

### Add New Admin Function
1. Create handler in `business_logic.py`
2. Create UI in `ui_components.py`
3. Wire up callback in `app.py` → `render_admin_tab()`

### Add New Reward Type
1. Add to `config.py` → `REWARD_SETTINGS`
2. Use `apply_reward()` in relevant handler
3. Process level ups with `process_level_up()`

---

## ✅ Verification Checklist

Before going live:
- [ ] Supabase credentials configured
- [ ] Admin PIN changed from default
- [ ] Test quiz submission works
- [ ] Test vault purchase works
- [ ] Test journal save works
- [ ] Verify achievements unlock correctly
- [ ] Test admin panel functions
- [ ] Database backed up

---

## 🆘 Getting Help

1. **Find a function:** Search in relevant module (see File Organization)
2. **Understand flow:** Read docstrings and type hints
3. **Debug:** Add st.write() statements or use print()
4. **Check database:** View rows in Supabase dashboard
5. **Review README_REFACTORING.md:** Detailed architecture guide

---

## 📝 License & Credits

Created for DepEd Grade 5 Learning Program
Original author: @tatayotter
Refactored for modularity and maintainability

---

**Happy Coding! 🎓**
