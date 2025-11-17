import json
import random
from textblob import TextBlob 
import os 
import time
import sqlite3 # مكتبة قاعدة البيانات
import datetime # عشان نسجل وقت المقابلة

# --- 1. الدوال المساعدة ---

def load_responses(file_path='responses.json'):
    """يقرأ الردود من ملف JSON."""
    full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"خطأ في تحميل الردود: {e}")
        return None

def get_sentiment_score(text):
    """تحليل النص للحصول على درجة القطبية (Polarity)."""
    analysis = TextBlob(text)
    return analysis.sentiment.polarity

def get_empathetic_reply_and_key(user_text, question_config):
    """
    بيدور في إجابة المستخدم عن كلمة مفتاحية ويرجع الرد التفاعلي + المفتاح الموحد (للتخزين).
    """
    user_text_lower = user_text.lower()
    replies_config = question_config.get("answer_replies", {})
    
    # [تعديل بسيط] البحث عن الكلمات المفتاحية
    for std_key, data in replies_config.items():
        # لو المفتاح مش "Other"
        if std_key != "Other":
            for keyword in data.get("keywords", []):
                if keyword in user_text_lower:
                    reply = random.choice(data.get("bot_reply", ["تمام."]))
                    return reply, std_key 
    
    # [تعديل بسيط] لو ملقاش ولا كلمة، شوف لو فيه رد افتراضي زي "Other"
    if "Other" in replies_config:
         reply = random.choice(replies_config["Other"].get("bot_reply", ["تمام، سجلت ده."]))
         # لو الـ field هو Country، هنخزن الإجابة زي ما هي
         if question_config.get("field") == "Country":
             return reply, user_text # <-- هيخزن "مصر" زي ما هي
         return reply, "Other"
         
    return None, user_text # بيرجع "مفيش رد" + الإجابة الأصلية زي ما هي

def check_mood_keywords(user_text):
    """بيدور الأول على الكلمات المفتاحية للمشاعر في الـ JSON."""
    if "mood_keywords" not in RESPONSES:
        return None 
    
    user_text_lower = user_text.lower()
    
    for mood in ["مبضون", "وحش", "تعبان"]:
        if mood in RESPONSES["mood_keywords"]:
            for keyword in RESPONSES["mood_keywords"][mood]:
                if keyword in user_text_lower:
                    return mood 
    
    for mood in ["ممتاز", "كويس"]:
         if mood in RESPONSES["mood_keywords"]:
            for keyword in RESPONSES["mood_keywords"][mood]:
                if keyword in user_text_lower:
                    return mood 
    
    return None 

# --- 1.6. دوال قاعدة البيانات (هنا التعديل الكبير) ---

def setup_database():
    """
    [تم التعديل] الدالة دي بتنشئ الجدول بالأعمدة الـ 13 الجداد.
    """
    conn = sqlite3.connect('moodmate.db') 
    c = conn.cursor()
    
    # [تعديل] إضافة الأعمدة الجديدة
    c.execute('''
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            
            Gender TEXT, 
            Country TEXT,
            
            Occupation TEXT,
            Growing_Stress TEXT,
            Changes_Habits TEXT,
            Days_Indoors TEXT,
            Mood_Swings TEXT,
            Coping_Struggles TEXT,
            Work_Interest TEXT,
            Social_Weakness TEXT,
            Mental_Health_History TEXT,
            family_history TEXT,
            
            care_options TEXT,
            mental_health_interview TEXT
        )
    ''')
    
    # [جديد] التأكد من إضافة الأعمدة الجديدة لو الجدول القديم موجود
    # ده كود أمان بيضمن إن الأعمدة الجديدة تتضاف حتى لو قاعدة البيانات القديمة موجودة
    existing_columns = [col[1] for col in c.execute("PRAGMA table_info(interviews)")]
    new_columns = {
        "Gender": "TEXT",
        "Country": "TEXT",
        "care_options": "TEXT",
        "mental_health_interview": "TEXT"
    }
    
    for col_name, col_type in new_columns.items():
        if col_name not in existing_columns:
            try:
                c.execute(f"ALTER TABLE interviews ADD COLUMN {col_name} {col_type}")
                print(f"--- (للمطور) تم إضافة عمود {col_name} لقاعدة البيانات ---")
            except Exception as e:
                print(f"--- (للمطور) خطأ في إضافة عمود {col_name}: {e} ---")

    conn.commit() 
    conn.close()  

def save_interview(data):
    """
    [تم التعديل] الدالة دي دلوقتي بتقدر تحفظ الأعمدة الجديدة.
    """
    conn = sqlite3.connect('moodmate.db')
    c = conn.cursor()
    
    # الكود ده ذكي (Dynamic)، هو بيحفظ أي أعمدة تتبعتله
    # فمش محتاجين نغير فيه حاجة، هو هيشتغل لوحده
    columns = ', '.join(data.keys()) 
    placeholders = ', '.join(['?'] * len(data)) 
    values = list(data.values())
    
    columns += ', timestamp'
    placeholders += ', ?'
    values.append(datetime.datetime.now())
    
    try:
        query = f"INSERT INTO interviews ({columns}) VALUES ({placeholders})"
        c.execute(query, values)
        conn.commit()
        print("\n--- (للمطور) تم حفظ البيانات بنجاح في moodmate.db ---")
    except Exception as e:
        print(f"\n--- (للمطور) !!! خطأ في حفظ البيانات: {e} ---")
    finally:
        conn.close()

# --- 2. المنطق الرئيسي ---

# تحميل الردود مرة واحدة
RESPONSES = load_responses()

if __name__ == "__main__":
    
    setup_database() # [مهم!] بنتأكد إن قاعدة البيانات جاهزة بالأعمدة الجديدة
    
    if not RESPONSES:
        print("خطأ فادح: لا يمكن تحميل ملف responses.json. البرنامج سيتوقف.")
    elif "mood_keywords" not in RESPONSES:
         print("خطأ فادح: ملف responses.json ناقص! لازم تضيف قسم 'mood_keywords' عشان أفهم عربي.")
    else:
        print("🤖 MoodMate (الوضع المحلي - المقابلة الكاملة): نورت! عامل إيه؟")
        
        conversation_state = {
            "mode": "greeting", 
            "current_question_index": 0,
            "collected_data": {}
        }

        while True:
            try:
                user_text = input("أنت: ").strip()
                bot_response = "" 

                # --- 1. فحص الوداع ---
                if any(keyword in user_text.lower() for keyword in RESPONSES.get("farewell_keywords", [])):
                    print(f"🤖 MoodMate: {random.choice(RESPONSES.get('farewells'))}")
                    break 

                # --- 2. فحص حالة الحوار ---
                
                # (الحالة أ: لو مستني موافقة المستخدم)
                if conversation_state["mode"] == "awaiting_confirmation":
                    if any(keyword in user_text.lower() for keyword in RESPONSES["interview_intro"]["confirmation_keywords"]):
                        conversation_state["mode"] = "in_interview"
                        first_question = RESPONSES["interview_questions"][0] # هيبدأ من Gender?
                        conversation_state["current_question_index"] = 0
                        bot_response = first_question["question"]
                    else:
                        conversation_state["mode"] = "greeting" 
                        bot_response = "تمام، براحتك جدًا. لو حبيت نبدأ في أي وقت، قولي بس إنك متضايق أو زهقان."
                
                # (الحالة ب: لو جوه المقابلة - القسم الثاني)
                elif conversation_state["mode"] == "in_interview":
                    last_q_index = conversation_state["current_question_index"]
                    last_q_config = RESPONSES["interview_questions"][last_q_index]
                    last_q_field = last_q_config["field"]

                    empathetic_reply, stored_key = get_empathetic_reply_and_key(user_text, last_q_config)
                    
                    conversation_state["collected_data"][last_q_field] = stored_key
                    
                    if empathetic_reply:
                        print(f"🤖 MoodMate: {empathetic_reply}")
                        time.sleep(1.2) 

                    next_q_index = last_q_index + 1
                    if next_q_index < len(RESPONSES["interview_questions"]):
                        next_question = RESPONSES["interview_questions"][next_q_index]
                        conversation_state["current_question_index"] = next_q_index
                        bot_response = next_question["question"] 
                    else:
                        # [مهم] المقابلة الكاملة (13 سؤال) خلصت
                        bot_response = RESPONSES["interview_end"] 
                        
                        print("--- (للمطور) البيانات اللي اتجمعت (قبل الحفظ) ---")
                        print(conversation_state["collected_data"])
                        
                        # [مهم] هنا بنحفظ النوتة الكاملة (أبو 13 عمود)
                        save_interview(conversation_state["collected_data"])
                        
                        # Reset
                        conversation_state = {"mode": "greeting", "current_question_index": 0, "collected_data": {}}
                
                # (الحالة ج: الوضع العادي/الترحيب)
                elif conversation_state["mode"] == "greeting":
                    if any(keyword in user_text.lower() for keyword in RESPONSES["greetings_keywords"]["عام"]) and len(user_text.split()) < 4:
                        bot_response = f"{random.choice(RESPONSES['greetings']['عام'])} عامل إيه النهارده؟"
                    else:
                        mood_key = check_mood_keywords(user_text) 

                        if mood_key in ["وحش", "تعبان", "مبضون"]:
                            bot_response = RESPONSES["interview_intro"]["speech"]
                            conversation_state["mode"] = "awaiting_confirmation"
                        
                        elif mood_key in ["ممتاز", "كويس"]:
                            bot_response = random.choice(RESPONSES["mood_responses"][mood_key]["responses"])
                        
                        else:
                            sentiment_score = get_sentiment_score(user_text)
                            if sentiment_score < -0.2: 
                                bot_response = RESPONSES["interview_intro"]["speech"]
                                conversation_state["mode"] = "awaiting_confirmation" 
                            elif sentiment_score > 0.3: 
                                bot_response = random.choice(RESPONSES["mood_responses"]["ممتاز"]["responses"])
                            else:
                                bot_response = random.choice(RESPONSES.get("unclear_responses"))

                # طباعة رد البوت النهائي
                print(f"🤖 MoodMate: {bot_response}")

            except EOFError:
                break
            except Exception as e:
                print(f"حدث خطأ فادح: {e}")
                break