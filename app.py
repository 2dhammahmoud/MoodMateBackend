# # ============================================
# # 🚀 MoodMate - Backend Flask Full Logic
# # ============================================

# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import json, random, os, sqlite3, datetime, pandas as pd, joblib, warnings, time
# from catboost import Pool
# from textblob import TextBlob

# warnings.filterwarnings('ignore', category=UserWarning)
# warnings.filterwarnings('ignore', category=FutureWarning)

# # --- 1. دوال مساعدة ---
# def load_json_file(file_path):
#     full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
#     try:
#         with open(full_path, 'r', encoding='utf-8') as f:
#             return json.load(f)
#     except Exception as e:
#         print(f"!!! خطأ فادح: لا يمكن تحميل {file_path}. {e}")
#         return None

# def load_model_file(file_path):
#     full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), file_path)
#     try:
#         model = joblib.load(full_path)
#         print(f"--- (للمطور) تم تحميل 'الموديل' ({file_path}) بنجاح ---")
#         return model
#     except FileNotFoundError:
#         print(f">>> خطأ: ملف '{file_path}' مش موجود!")
#         return None

# def get_sentiment_score(text):
#     return TextBlob(text).sentiment.polarity

# def check_mood_keywords(user_text):
#     if not RESPONSES or "mood_keywords" not in RESPONSES: return None
#     user_text_lower = user_text.lower()
#     for mood, keywords in RESPONSES["mood_keywords"].items():
#         if any(keyword in user_text_lower for keyword in keywords):
#             return mood
#     return None

# def get_empathetic_reply_and_key(user_text, question_config):
#     user_text_lower = user_text.lower()
#     replies_config = question_config.get("answer_replies", {})
#     for std_key, data in replies_config.items():
#         if std_key != "Other":
#             for keyword in data.get("keywords", []):
#                 if keyword in user_text_lower:
#                     reply = random.choice(data.get("bot_reply", ["تمام."]))
#                     return reply, std_key 
#     if "Other" in replies_config:
#         reply = random.choice(replies_config["Other"].get("bot_reply", ["تمام، سجلت ده."]))
#         if question_config.get("field") == "Country":
#             return reply, user_text 
#         return reply, "Other"
#     return None, user_text

# # --- 2. إعداد الملفات والموديل ---
# RESPONSES = load_json_file('responses.json')
# SOLUTIONS = load_json_file('solutions.json')
# MODEL = load_model_file('catboost_raw_model.joblib')
# DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'moodmate.db')

# # --- 3. إعداد قاعدة البيانات ---
# def setup_database():
#     conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#     c = conn.cursor()
#     c.execute('''
#         CREATE TABLE IF NOT EXISTS interviews (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             timestamp DATETIME,
#             Gender TEXT, Country TEXT, Occupation TEXT, Growing_Stress TEXT,
#             Changes_Habits TEXT, Days_Indoors TEXT, Mood_Swings TEXT,
#             Coping_Struggles TEXT, Work_Interest TEXT, Social_Weakness TEXT,
#             Mental_Health_History TEXT, family_history TEXT,
#             care_options TEXT, mental_health_interview TEXT,
#             prediction_score TEXT
#         )
#     ''')
#     conn.commit()
#     conn.close()

# def save_interview(data):
#     conn = sqlite3.connect(DB_PATH, check_same_thread=False)
#     c = conn.cursor()
#     known_columns = [
#         "Gender", "Country", "Occupation", "Growing_Stress", "Changes_Habits",
#         "Days_Indoors", "Mood_Swings", "Coping_Struggles", "Work_Interest",
#         "Social_Weakness", "Mental_Health_History", "family_history",
#         "care_options", "mental_health_interview", "prediction_score"
#     ]
#     filtered_data = {k: v for k, v in data.items() if k in known_columns}
#     if not filtered_data: return
#     columns = ', '.join(filtered_data.keys())
#     placeholders = ', '.join(['?']*len(filtered_data))
#     values = list(filtered_data.values())
#     columns += ', timestamp'
#     placeholders += ', ?'
#     values.append(datetime.datetime.now())
#     try:
#         query = f"INSERT INTO interviews ({columns}) VALUES ({placeholders})"
#         c.execute(query, values)
#         conn.commit()
#         print(f"--- تم حفظ البيانات بنجاح في {DB_PATH} ---")
#     except Exception as e:
#         print(f"--- خطأ في حفظ البيانات: {e} ---")
#     finally:
#         conn.close()

# def run_prediction(collected_data):
#     if not MODEL: return "Model not loaded"
#     cat_features_list = [
#         'Gender', 'Country', 'Occupation', 'self_employed', 'family_history', 
#         'Days_Indoors', 'Growing_Stress', 'Changes_Habits', 
#         'Mental_Health_History', 'Mood_Swings', 'Coping_Struggles', 
#         'Work_Interest', 'Social_Weakness', 'mental_health_interview', 'care_options',
#         'ts_hour', 'ts_dayofweek', 'ts_month'
#     ]
#     prediction_data = collected_data.copy()
#     now = datetime.datetime.now()
#     prediction_data['ts_hour'] = now.hour
#     prediction_data['ts_dayofweek'] = now.weekday()
#     prediction_data['ts_month'] = now.month
#     occupation = prediction_data.get("Occupation", "Other")
#     prediction_data["self_employed"] = "Yes" if occupation=="Business" else "No"
#     prediction_df = pd.DataFrame([prediction_data])
#     for col in cat_features_list:
#         if col not in prediction_df.columns:
#             prediction_df[col] = "Missing"
#     prediction_df = prediction_df[cat_features_list]
#     prediction_pool = Pool(prediction_df, cat_features=cat_features_list)
#     try:
#         proba = MODEL.predict_proba(prediction_pool)[0][1]
#         return f"{proba*100:.2f}%"
#     except Exception as e:
#         print(f"--- خطأ في التنبؤ: {e} ---")
#         return "Prediction failed"

# def build_solutions_menu(collected_data):
#     problem_list = []
#     if not SOLUTIONS: return []
#     for problem_key, problem_data in SOLUTIONS.items():
#         if problem_key=="final_summary": continue
#         user_answer = collected_data.get(problem_key, "")
#         if user_answer in problem_data.get("trigger_answer", []):
#             problem_list.append(problem_key)
#     return problem_list

# def format_solution(problem_key):
#     if not SOLUTIONS or problem_key not in SOLUTIONS:
#         return ["آسف، مش لاقي حلول للمشكلة دي."] 
#     data = SOLUTIONS[problem_key]
#     responses = []
#     if data.get("problem_intro"): responses.append(data["problem_intro"])
#     else: responses.append(f"تمام، خلينا نتكلم عن **{data.get('problem_name', problem_key)}**.")
#     if data.get("descriptions"): responses.append(f"**إيه هي المشكلة دي؟**\n*{random.choice(data['descriptions'])}*")
#     if data.get("symptoms"): responses.append(f"**إزاي ممكن تكون بتأثر عليك؟**\n*{random.choice(data['symptoms'])}*")
#     if data.get("solutions"):
#         k = 3 if problem_key=="Coping_Struggles" else 2
#         k = min(len(data["solutions"]), k)
#         chosen = random.sample(data["solutions"], k)
#         sol_text = "**طيب، إيه الحلول المقترحة؟**\n" + "\n".join([f"**{i+1}.** {s}" for i,s in enumerate(chosen)])
#         responses.append(sol_text)
#     if data.get("videos"): responses.append(f"\n{data.get('video_intro','')} \n- {random.choice(data['videos'])}")
#     if data.get("podcasts"): responses.append(f"\n{data.get('podcast_intro','')} \n- {random.choice(data['podcasts'])}")
#     return responses

# # --- 5. إعداد Flask ---
# app = Flask(__name__)
# CORS(app)
# setup_database()

# default_state = {"mode":"greeting","current_question_index":0,"collected_data":{},"problem_list":[]}

# # --- 6. API endpoint كامل ---
# @app.route('/chat', methods=['POST'])
# def chat():
#     try:
#         data = request.get_json() or {}               # نضمن إن فيه dictionary
#         user_text = data.get('message', '').strip()  # جلب رسالة المستخدم
#         state = data.get('state') or default_state.copy()  # لو state None أو فاضية، خد نسخة افتراضية
#         bot_responses = []

 


#         # --- تحليل سريع ---
#         is_farewell = any(k in user_text.lower() for k in RESPONSES.get("farewell_keywords",[]))
#         mood_key_check = check_mood_keywords(user_text)
#         is_negative_trigger = mood_key_check in ["وحش","تعبان","مبضون","زعلان"]
#         is_greeting = any(k in user_text.lower() for k in RESPONSES.get("greetings_keywords",{}).get("عام",[])) and len(user_text.split())<4

#         if state["mode"]!="greeting" and (is_farewell or is_negative_trigger or is_greeting):
#             state = default_state.copy()

#         # --- الحالات ---
#         if is_farewell:
#             bot_responses.append(random.choice(RESPONSES.get('farewells',["باي!"])))
#             state = default_state.copy()

#         elif state["mode"]=="greeting":
#             if is_greeting:
#                 bot_responses.append(f"{random.choice(RESPONSES.get('greetings',{}).get('عام', ['هاي']))} عامل إيه النهارده؟")
#             elif is_negative_trigger:
#                 bot_responses.append(RESPONSES.get("interview_intro",{}).get("speech","تمام، حابب نبدأ مقابلة قصيرة؟"))
#                 state["mode"]="awaiting_confirmation"
#             else:
#                 sentiment_score = get_sentiment_score(user_text)
#                 if sentiment_score<-0.2:
#                     bot_responses.append(RESPONSES.get("interview_intro",{}).get("speech","تمام، حابب نبدأ مقابلة قصيرة؟"))
#                     state["mode"]="awaiting_confirmation"
#                 elif sentiment_score>0.3:
#                     bot_responses.append(random.choice(RESPONSES.get("mood_responses",{}).get("ممتاز",{}).get("responses",["تمام."])))
#                 else:
#                     bot_responses.append(random.choice(RESPONSES.get("unclear_responses",["تمام."])))

#         # --- باقي الحالات (awaiting_confirmation, in_interview, solutions_menu, final_summary) ---
#         # ممكن نضيفها بنفس طريقة Streamlit لاحقًا بنفس المنطق، 
#         # الحاضر هو Skeleton كامل وجاهز للتوسيع

#         return jsonify({"responses":bot_responses,"newState":state})

#     except Exception as e:
#         print(f"--- خطأ في /chat: {e}")
#         import traceback; traceback.print_exc()
#         return jsonify({"responses":["آسف جدًا، حصل خطأ كبير في السيرفر."]}),500

# # --- 7. تشغيل السيرفر ---
# if __name__=="__main__":
#     print("--- سيرفر MoodMate بيبدأ ---")
#     app.run(host='0.0.0.0', port=5000, debug=False)
from fastapi import FastAPI
from pydantic import BaseModel
import json, random, os, joblib
from textblob import TextBlob

# --- 1. مسار الملفات ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESPONSES_PATH = os.path.join(BASE_DIR, 'responses.json')
SOLUTIONS_PATH = os.path.join(BASE_DIR, 'solutions.json')
MODEL_PATH = os.path.join(BASE_DIR, 'catboost_raw_model.joblib')  # عدل حسب اسم الموديل عندك

# --- 2. تحميل الملفات والموديل ---
def load_json_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

RESPONSES = load_json_file(RESPONSES_PATH)
SOLUTIONS = load_json_file(SOLUTIONS_PATH)

try:
    MODEL = joblib.load(MODEL_PATH)
    print("--- موديل البوت تم تحميله بنجاح ---")
except:
    MODEL = None
    print("!!! موديل البوت لم يتم تحميله")

# --- 3. كلاس البوت الأساسي ---
class ChatBot:
    def __init__(self):
        self.model = MODEL
        self.responses = RESPONSES

    def get_response(self, user_text):
        # تحليل بسيط
        sentiment = TextBlob(user_text).sentiment.polarity
        if "هاي" in user_text.lower() or "hello" in user_text.lower():
            return "أهلا! عامل إيه النهاردة؟"
        elif sentiment < -0.2:
            return "ملاحظ عليك طاقة سلبية. تحب نبدأ مقابلة قصيرة؟"
        elif sentiment > 0.3:
            return "تمام! واضح إن مزاجك ممتاز 😊"
        else:
            return "تمام، سجلت رسالتك."

bot = ChatBot()

# --- 4. FastAPI setup ---
app = FastAPI()

class RequestModel(BaseModel):
    message: str
    state: dict = {}

@app.post("/chat")
def chat(request: RequestModel):
    user_text = request.message
    state = request.state or {"mode":"greeting","current_question_index":0,"collected_data":{}}
    reply = bot.get_response(user_text)
    return {"responses": [reply], "newState": state}

# --- 5. Run locally ---
if __name__=="__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
