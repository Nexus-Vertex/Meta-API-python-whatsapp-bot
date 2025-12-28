from flask import Flask, request, request, jsonify, send_from_directory
from datetime import datetime
import sqlite3
import os
import requests
import json
from dotenv import load_dotenv
import logging
from utils import (
    init_db, add_order, get_order_by_phone,
    export_orders_to_excel, generate_order_id,
    auto_progress_statuses
)

# ------------------ تحميل .env ------------------
load_dotenv()

app = Flask(__name__)
DB_PATH = "database.db"

# --- Config WhatsApp API ---
ACCESS_TOKEN = "your_access_token_here"
APP_SECRET =  "your_app_secret_here"
API_URL = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
VERIFY_TOKEN = "your_verify_token_here"

# ------------------ إعداد logging ------------------
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logging.info("Server démarré avec succès")

# ------------------ إنشاء الجداول ------------------
def create_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS numbers (
            phone_number TEXT PRIMARY KEY
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT,
            body TEXT,
            direction TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    logging.info("Tables vérifiées/créées")

create_tables()

# ------------------ حفظ الرقم ------------------
def save_number(phone_number):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO numbers (phone_number) VALUES (?)", (phone_number,))
    conn.commit()
    conn.close()
    logging.info(f"Numéro enregistré: {phone_number}")

# ------------------ حفظ الرسائل ------------------
def save_message(phone_number, body, direction):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (phone_number, body, direction) VALUES (?, ?, ?)",
        (phone_number, body, direction)
    )
    conn.commit()
    conn.close()
    logging.info(f"Message sauvegardé | {direction} | {phone_number}: {body}")

# ------------------ إرسال رسالة عبر Cloud API ------------------
def send_whatsapp_message(to, body):
    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": body}
    }
    try:
        res = requests.post(url, json=payload, headers=headers)
        logging.info(f"Message envoyé à {to}: {body} | Response: {res.text}")
        return res.json()
    except Exception as e:
        logging.error(f"Erreur sending message to {to}: {e}")
        return {"sent": False}

# ------------------ Endpoint لعرض الأرقام ------------------
@app.route("/numbers", methods=["GET"])
def get_numbers():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT phone_number FROM numbers")
        numbers = [row[0] for row in cursor.fetchall()]
        conn.close()
        logging.info(f"Fetched numbers: {numbers}")
        return jsonify(numbers)
    except Exception as e:
        logging.error(f"Error fetching numbers: {e}")
        return jsonify([]), 500

# ------------------ Endpoint لإرسال رسالة ------------------
@app.route("/send-message", methods=["POST"])
def send_message():
    try:
        data = request.get_json()
        to = data.get("to")
        body = data.get("body")
        logging.info(f"Sending message to {to}: {body}")
        res = send_whatsapp_message(to, body)
        if "messages" in res:
            save_message(to, body, "out")
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error"}), 500
    except Exception as e:
        logging.error(f"Error sending message: {e}")
        return jsonify({"status": "error"}), 500

# ------------------ Endpoint لعرض آخر 10 رسائل ------------------
@app.route("/last-messages", methods=["GET"])
def last_messages():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT phone_number, body, direction, timestamp 
            FROM messages
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        messages = cursor.fetchall()
        conn.close()
        result = [{"phone": row[0], "body": row[1], "direction": row[2], "time": row[3]} for row in messages]
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error fetching last messages: {e}")
        return jsonify([]), 500

# ------------------ Endpoint لواجهة التحكم ------------------
@app.route("/control")
def control_page():
    stor_path = os.path.abspath("../VELO.STOR")  # عدّل حسب المسار ديالك
    return send_from_directory(stor_path, "control.html")

# --- Sessions & Products ---
SESSIONS = {}
USER_PRODUCTS = {}

PRICES = {
    "TANK M41": 7990,
    "DUALTRON TOGO": 5290,
    "SHINE S": 7200,
    "CICLISTA": 1449,
    "SPORT BIKE": 1399,
}

# --- دالة إرسال رسالة نصية ---
def send_message(to, text):
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    res = requests.post(API_URL, headers=headers, json=payload)
    logging.debug(f"send_message to {to} response: {res.status_code} {res.text}")

# --- دالة إرسال أزرار ---
def send_buttons(to, text, buttons):
    if len(buttons) > 3:
        buttons = buttons[:3]  # WhatsApp يقدر فقط 3 أزرار
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": text},
            "action": {
                "buttons": [{"type": "reply", "reply": {"id": b["id"], "title": b["title"]}} for b in buttons]
            }
        }
    }
    res = requests.post(API_URL, headers=headers, json=payload)
    logging.debug(f"send_buttons to {to} response: {res.status_code} {res.text}")

# --- Webhook verification ---
@app.route("/webhook", methods=["GET"])
def webhook_verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    # التحقق بالطريقة الأولى (mode + token)
    if mode == "subscribe" and token == VERIFY_TOKEN:
        logging.info("Webhook verified successfully (mode + token).")
        return challenge, 200

    # التحقق بالطريقة الثانية (token فقط)
    if token == VERIFY_TOKEN:
        logging.info("Webhook verified successfully (simple token).")
        return challenge, 200

    # إذا ما تحقق حتى شرط
    logging.warning("Webhook verification failed.")
    return "Forbidden", 403


# --- Check status endpoint ---
@app.route("/check_status", methods=["GET"])
def check_status():
    # call auto_progress_statuses() كما هي (تحديث DB فقط)
    updated_orders, stats = auto_progress_statuses()  

    # نرجعو فقط البيانات البسيطة
    return {
        "updated_orders": updated_orders,  # كل طلب تبدلات حالته (id, status)
        "status_statistics": stats         # إحصائيات الحالة
    }, 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        logging.debug(f"Incoming webhook data: {json.dumps(data, indent=2, ensure_ascii=False)}")

        if data.get("object") == "whatsapp_business_account":
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messages = value.get("messages")
                    if messages:
                        msg = messages[0]
                        phone = msg.get("from")
                        if not phone:
                            logging.warning("Message without phone number.")
                            continue

                        text = ""
                        if "interactive" in msg:
                            inter_type = msg["interactive"].get("type")
                            if inter_type == "button_reply":
                                text = msg["interactive"]["button_reply"]["id"]
                            elif inter_type == "list_reply":
                                text = msg["interactive"]["list_reply"]["id"]
                        elif "text" in msg:
                            text = msg["text"].get("body", "").strip()

                        logging.debug(f"From: {phone} | Text/Button ID: {text}")

                        text_lower = text.lower().strip()

                        # --- التحقق من اسم المنتج ---
                        PRODUCT_NAMES = {
                            "tank m41": "TANK M41",
                            "dualtron togo": "DUALTRON TOGO",
                            "shine s": "SHINE S",
                            "ciclista": "CICLISTA",
                            "sport bike": "SPORT BIKE"
                        }

                        product_detected = None
                        for key in PRODUCT_NAMES:
                            if key in text_lower:
                                product_detected = PRODUCT_NAMES[key]
                                break

                        if product_detected:
                            SESSIONS[phone] = f"desc:{product_detected}"  # وضع الجلسة في وصف المنتج

                            # ✅ إرسال رسالة info + أزرار المنتج
                            send_buttons(
                                phone,
                                f"وعليكم السلام! 😊\n"
                                f"بالنسبة لـ *{product_detected}*، الثمن ديالو هو **{PRICES.get(product_detected, 'غير معروف')} DH** 💸\n"
                                f"\n📦 هاد الموديل متوفر حالياً فالمخزون ✅\n"
                                "\n👉 إلا بغيتي تعرف كيفاش كنديرو التوصيل ولا طريقة الأداء، غير سول ومرحبا نعاونك 🚴‍♂🚚💰\n"
                                "\n✨ وإذا عندك شي سؤال آخر، أنا هنا نعاونك بكل سرور 😉\n\n",
                                [
                                    {"id": "o1", "title": "🛒 بغيت نطلب"},
                                    {"id": "o3", "title": "🚚 التوصيل"},
                                    {"id": "0", "title": "🏠 الرئيسية"},
                                ]
                            )
                            return "OK", 200

                        # --- باقي الحالات مثل السلام والـ main menu ---
                        session = SESSIONS.get(phone, "main")
                        if text_lower in ["سلام", "slm", "salut", "السلام عليكم", "hello", "0", "🏠 الرئيسية"]:
                            SESSIONS[phone] = "main"
                            send_buttons(
                                phone,
                                "وعليكم السلام ورحمة الله وبركاته! 😊\n"
                                "مرحبا بك فـ VELO.STOR، المتجر ديال أحسن التروتينيطات والدراجات الكهربائية فالمغرب! 🚴‍♂⚡\n"
                                "أنا هنا باش نعاونك ونقدم لك أفضل تجربة تسوق.\n\n"
                                "دابا، اختار من هاد الفئات باش نبدأ:\n\n",
                                [
                                    {"id": "1", "title": "📦 المنتجات ديالنا"},
                                    {"id": "2", "title": "🛠 الخدمات ديالنا"},
                                    {"id": "plus_more", "title": "➕ المزيد"},
                                ]
                            )
                            return "OK", 200


                        
                        if text == "plus_more" or text == "➕ المزيد":
                            SESSIONS[phone] = "more"
                            send_buttons(phone,
                                "➕ هادو بعض الاختيارات الزايدة لي وجدّينا ليك، باش تكتاشف خدمات أخرى وتسهّل عليك الطور ديالك فالمنصة.",
                                [
                                    {"id": "status_order", "title": "📋 حالة الطلب ديالي"},
                                    {"id": "order_method", "title": "🛒 طريقة الطلب"},
                                    {"id": "contact_admin", "title": "📞 تواصل مع المسؤول"},
                                ])
                            return "OK", 200

                        if session == "more":
                            if text == "status_order" or text == "📋 حالة الطلب ديالي":
                                order = get_order_by_phone(phone)
                                if order:
                                    order_id, status, client_name, product_name, price, ville, address, last_updated = order
            
                                    # رسائل مفصلة حسب الحالة + اسم المنتج
                                    if status == "EN ATTENTE":
                                        message = (
                                            f"📦 الطلب {order_id}\n"
                                            f"المنتج: {product_name}\n"
                                            f"الحالة: في الانتظار ⏳\n"
                                            f"حنا توصلنا بطلبك وراه غادي يتم تأكيده قريبا."
                                        )
                                    elif status == "CONFIRMÉ":
                                        message = (
                                            f"📦 الطلب {order_id}\n"
                                            f"المنتج: {product_name}\n"
                                            f"الحالة: مؤكد ✅\n"
                                            f"طلبك تأكد رسمياً وغادي نحضروه للتوصيل.\n"
                                            f"إذا عندك أي سؤال على الطلب، تقدر تجاوب هاد الرسالة."
                                        )
                                    elif status == "EN LIVRAISON":
                                        message = (
                                            f"🚚 الطلب {order_id}\n"
                                            f"المنتج: {product_name}\n"
                                            f"الحالة: في الطريق\n"
                                            f"طلبك راه حاليا في التوصيل وغادي يوصل للعنوان اللي عطيتنا.\n"
                                            f"قريبًا إن شاء الله غادي يوصل عندك! ⏱️"
                                        )
                                    elif status == "LIVRÉ":
                                        message = (
                                            f"🎉 الطلب {order_id}\n"
                                            f"المنتج: {product_name}\n"
                                            f"الحالة: تم التوصيل ✅\n"
                                            f"شكراً لك! طلبك وصل للعنوان ديالك.\n"
                                            f"نتمنى يعجبك المنتج 😊"
                                        )
                                    elif status == "TERMINÉ":
                                        message = (
                                            f"✅ الطلب {order_id}\n"
                                            f"المنتج: {product_name}\n"
                                            f"الحالة: منتهية\n"
                                            f"جميع الإجراءات ديال الطلب تمّت بنجاح.\n"
                                            f"شكراً على ثقتك بنا، ومرحبا بك في أي وقت!"
                                            )
                                    else:
                                        message = (
                                            f"📋 الطلب {order_id}\n"
                                            f"المنتج: {product_name}\n"
                                            f"الحالة: {status}"
                                        )

                                else:
                                    message = "مع الأسف، ما لقيتش حتى طلب مسجل برقم الهاتف ديالك."

                                # إرسال الرسالة مع زر العودة للرئيسية
                                send_buttons(phone, message, [
                                    {"id": "0", "title": "🏠 الرئيسية"},
                                                        ])
                                return "OK", 200

                            elif text == "order_method" or text == "🛒 طريقة الطلب":
                                send_buttons(phone,
                                    "🛒 طريقة الطلب سهلة:\n"
                                    "1️⃣ اختار المنتج اللي بغيتي\n"
                                    "2️⃣ عطي الاسم، المدينة والعنوان\n"
                                    "3️⃣ استنى الاتصال والتوصيل\n\n"
                                    "لمزيد من المساعدة، تواصل مع المسؤولين.",
                                    [
                                        {"id": "contact_admin", "title": "📞 تواصل مع المسؤول"},
                                        {"id": "0", "title": "🏠 الرئيسية"},
                                    ])
                                return "OK", 200

                            elif text == "contact_admin" or text == "📞 تواصل مع المسؤول":
                                send_buttons(phone,
                                    "📞 تقدر تتواصل معانا عبر:\n"
                                    "- 📱 رقم الهاتف: 0716142438\n"
                                    "- 📧 البريد الإلكتروني: support@velo.stor\n"
                                    "- 🕒 أوقات العمل: 9 صباحاً - 6 مساءً",
                                    [
                                        {"id": "order_method", "title": "🛒 طريقة الطلب"},
                                        {"id": "0", "title": "🏠 الرئيسية"},
                                    ])
                                return "OK", 200

                            elif text == "0":
                                SESSIONS[phone] = "main"
                                send_buttons(phone,
                                    "✅ رجعنا للقائمة الرئيسية.",
                                    [
                                        {"id": "1", "title": "📦 المنتجات ديالنا"},
                                        {"id": "2", "title": "🛠 الخدمات ديالنا"},
                                        {"id": "plus_more", "title": "➕ المزيد"},
                                    ])
                                return "OK", 200

                      
                        if text == "1":
                            SESSIONS[phone] = "products"
                            send_buttons(phone,
                                "📂 عندنا بزاف ديال الأقسام فالمتجر، قول ليا شنو هي الفئة لي عجباك أكثر،باش نقدر نوريك المنتجات ديالها بالتفصيل وبطريقة واضحة.",
                                [
                                    {"id": "t1", "title": "🛴 Trottinette"},
                                    {"id": "t2", "title": "🚲 Vélo électrique"},
                                    {"id": "t3", "title": "🚵‍♂ Vélo VTT"},
                                ])
                            return "OK", 200

                        
                        if session == "products" and text in ["t1", "t2", "t3"]:
                            if text == "t1":
                                SESSIONS[phone] = "trot"
                                send_buttons(phone,
                                    "⚡ التروتينيت ديالنا قوية وعصرية، مع بطاريات كتخليك تسافر مسافات طويلة بلا توقف.\n"
                                    "سواقة سلسة وتصميم أنيق يناسب المدينة والرياضة.\n"
                                    "\n———\n"
                                    "اختار من بين جوج موديلات مشهورين باش نعطيك تفاصيل أكثر:\n\n",
                                    [
                                        {"id": "m1", "title": "🔥 M14"},
                                        {"id": "m2", "title": "🚀 DUALTRON TOGO"},
                                        {"id": "0", "title": "🏠 الرئيسية"},
                                    ])
                            elif text == "t2":
                                SESSIONS[phone] = "electrique"
                                send_buttons(phone,
                                    "⚡ عندنا موديلات كهربائية ممتازة، سهلة فالسياقة، وكتوفر استقلالية كبيرة.\n"
                                    "مثالية للمدينة وللسفر اليومي براحة وبدون تعب.\n"
                                    "\n———\n"
                                    "عندنا موديل مشهور بزاف، اختاره باش نعطيك التفاصيل:\n\n",
                                    [
                                        {"id": "m3", "title": "⚡ SHINE S"},
                                        {"id": "0", "title": "🏠 الرئيسية"},
                                    ])
                            elif text == "t3":
                                SESSIONS[phone] = "vtt"
                                send_buttons(phone,
                                    "🚵 عندنا VTT قوية ومتينة مناسبة لجميع التضاريس.\n"
                                    "مريحة وبتقنيات حديثة لركوب آمن.\n"
                                    "\n———\n"
                                    "اختار من بين الموديلات:\n\n",
                                    [
                                        {"id": "m4", "title": "🏔 CICLISTA"},
                                        {"id": "m5", "title": "🔥 SPORT BIKE"},
                                        {"id": "0", "title": "🏠 الرئيسية"},
                                    ])
                            return "OK", 200

                        
                        if session in ["trot", "electrique", "vtt"]:
                            produits = {
                                "m1": ("M14", "✅OFFRE SPÉCIALE M41 TANK🔥\n➡TROTTINETTE Tank M41 double moteur \n➡MARQUE Ecoxtrem tank\n➡Charge max 150 kg\n➡Freinage: disque Avant et arrière +E-ABS\n➡Autonomie 50km min - 65km max\n➡Vitesse 75km mini - 99km max \n➡Matériel Alliage d'aluminium\n➡Batterie lithium \n➡écran Lcd \n➡Charge 54.8V 5A\n➡Sac de Trottinette cadeau 🎁 🎁 \n➡Promo  7990 DH"),
                                "m2": ("DUALTRON TOGO", "➡TROTTINETTE DUALTRON TOGO 48V\n➡Moteur 1300W  max\n➡Batterie 36 V 12AH\n➡Frein de sécurité\n➡Suspension avant et arrière \n➡Charge max 110 kg\n➡Freinage: Avant et arrière +E-ABS\n➡Autonomie 30km min - 40km max\n➡9 pouces Chambre à air\n➡Charge 48V \n➡Promo  5290 DH"),
                                "m3": ("SHINE S", "🛴علامة تجارية أصلية LIKEBIKE \n🛴دراجة قابلة للطي \n🛴محرك 500 واط ماكس \n🛴بطاريات 48V 13AH \n🛴الحد الأقصى للشحن 120 كجم \n🛴مكابح: أمامي وخلفي\n🛴السرعة الذاتي 40 كم - 50 كم كحد أقصى\n🛴فيتيس ماكس 38 كم \n🛴بطارية ليثيوم \n🛴لوحة رقمية \n🛴السرعة 5فيتاس\n🛴مقعد جلد\n🛴بورت باكاج الأمتعة الخلفي \n🛴إطار 20 بوصة \n🛴شحن 54 فولت \n🛴منبه \n🛴قطع غيار شيمانو اصلي\n🛴التمن: 7200 درهم"),
                                "m4": ("CICLISTA", "💫 OFFRE SPÉCIALE\n💫VÉLO VTT CICLISTA 2025\n💫26 POUCES \n💫ROUE DE VÉLO ALUMINIUM\n💫CHANGEMENT SIMLICHT\n💫VITESSE 3×7=21\n💫PLATEAU SIMLICHT\n💫AMORTISSEUR AVANT\n💫SIÈGE SPORT CUIR\n💫FREINS À DISQUE AVANT ET ARRIÈRE* \n🔥Promo 1449 DH"),
                                "m5": ("SPORT BIKE", "💫 OFFRE SPÉCIALE VÉLO VTT SPORT BIKE \n💫VÉLO VTT SPORT BIKE 27,5P 💯\n💫27,5 POUCES \n💫LES GARDES-BOUES AV ET AR \n💫SPORT BIKE 1E QUALITÉ 💯 \n💫ROUE DE VÉLO ALUMINIUM\n💫CHANGEMENT SHIMANO\n💫VITESSE 3×7=21\n💫PLATEAU  SHIMANO \n💫AMORTISSEUR AVANT\n💫SIÈGE SPORT CUIR \n💫FREIN À DISQUE AVANT ET ARRIÈRE\n✅COLOR 🟠🩶🔴🔵\n✅Prix: 1399 درهم")
                            }
                            if text in produits:
                                name, desc = produits[text]
                                SESSIONS[phone] = f"desc:{name}"
                                USER_PRODUCTS[phone] = name

                                send_buttons(phone,
                                    f"{desc}\n\nشنو بغيت دابا؟",
                                    [
                                        {"id": "o1", "title": "🛒 بغيت نطلب"},
                                        {"id": "o3", "title": "🚚 التوصيل"},
                                        {"id": "0", "title": "🏠 الرئيسية"},
                                    ])
                                return "OK", 200

                        
                        if session.startswith("desc:"):
                            prod = session.split(":", 1)[1]
                            if text == "o1":
                                SESSIONS[phone] = f"ask_name:{prod}"
                                send_buttons(phone,
                                    f"📥 عفاك عطيني الاسم ديالك باش نكملو طلب {prod}.",
                                    [
                                        {"id": "0", "title": "🏠 الرئيسية"},
                                    ])
                                return "OK", 200
                            elif text == "o3":
                                send_buttons(phone,
                                    "🚚 التوصيل مجاني فكل المدن. الوقت المتوقع 2 حتى 5 أيام.",
                                    [
                                        {"id": "o1", "title": "🛒 بغيت نطلب"},
                                        {"id": "0", "title": "🏠 الرئيسية"},
                                    ])
                                return "OK", 200
                            elif text == "0":
                                SESSIONS[phone] = "main"
                                send_buttons(phone,
                                    "✅ رجعنا للقائمة الرئيسية.",
                                    [
                                        {"id": "1", "title": "📦 المنتجات ديالنا"},
                                        {"id": "2", "title": "🛠 الخدمات ديالنا"},
                                        {"id": "plus_more", "title": "➕ المزيد"},
                                    ])
                                return "OK", 200

                        # جمع المعلومات خطوة بخطوة
                        if session.startswith("ask_name:"):
                            prod = session.split(":", 1)[1]
                            client_name = text.strip()
                            SESSIONS[phone] = f"ask_ville:{prod}:{client_name}"
                            send_buttons(phone,
                                f"🏙️ شكراً {client_name}، دابا عفاك عطينا المدينة ديالك.",
                                [{"id": "0", "title": "🏠 الرئيسية"}])
                            return "OK", 200

                        if session.startswith("ask_ville:"):
                            _, prod, client_name = session.split(":", 2)
                            ville = text.strip()
                            SESSIONS[phone] = f"ask_address:{prod}:{client_name}:{ville}"
                            send_buttons(phone,
                                f"🏠 شكراً، دابا عطينا العنوان ديالك باش نكملو الطلب.",
                                [{"id": "0", "title": "🏠 الرئيسية"}])
                            return "OK", 200

                        if session.startswith("ask_address:"):
                            try:
                                _, prod, client_name, ville = session.split(":", 3)
                                address = text.strip()

                                order_number = generate_order_id()
                                product_name = prod
                                price = PRICES.get(product_name, 0)

                                # Debug print
                                logging.info(f"Debug before adding order: phone={phone}, client_name={client_name}, order_number={order_number}, product_name={product_name}, price={price}, ville={ville}, address={address}")

                                # إضافة الطلب
                                add_order(phone, client_name, order_number, "📦 طلب جديد", product_name, price , ville, address)
                                export_orders_to_excel("orders.xlsx")
                                logging.info(f"Order added successfully: {order_number} for {phone} - {product_name} at {ville}")

                                send_buttons(phone,
                                    f"✅ شكراً {client_name}! الطلب ديالك تسجل وغادي نتاصلوا بيك قريباً.\nرقم الطلب ديالك هو: {order_number}",
                                    [
                                        {"id": "1", "title": "📦 المنتجات ديالنا"},
                                        {"id": "2", "title": "🛠 الخدمات ديالنا"},
                                        {"id": "plus_more", "title": "➕ المزيد"},
                                    ])
                                SESSIONS[phone] = "main"
                                return "OK", 200

                            except Exception as e:
                                logging.error(f"Failed to add order: {e}", exc_info=True)
                                (phone,
                                    "❌ وقع مشكل أثناء تسجيل الطلب. عاود المحاولة من فضلك.",
                                    [{"id": "0", "title": "🏠 الرئيسية"}])
                                return "OK", 200
                        
                        if text == "2":
                            SESSIONS[phone] = "services"
                            send_buttons(phone,
                                "🧰 هادو بعض الخدمات لي كنوفروها ليك، وغادي تعاونك تستافد مزيان وتلقى كلشي بلا ما تضيع وقت:",
                                [
                                    {"id": "s1", "title": "🚚 التوصيل"},
                                    {"id": "s2", "title": "💰 الدفع"},
                                    {"id": "0", "title": "🏠 الرئيسية"},
                                ])
                            return "OK", 200

                        if session == "services":
                            if text == "s1":
                                send_buttons(phone,
                                    "🚚 التوصيل مجاني والمدة بين 2 حتى 5 أيام حسب المدينة.",
                                    [
                                        {"id": "s2", "title": "💰 الدفع"},
                                        {"id": "0", "title": "🏠 الرئيسية"},
                                    ])
                                return "OK", 200
                            elif text == "s2":
                                send_buttons(phone,
                                    "💰 الدفع كاين نقداً عند التوصيل، أو عن طريق التحويل البنكي.",
                                    [
                                        {"id": "s1", "title": "🚚 التوصيل"},
                                        {"id": "0", "title": "🏠 الرئيسية"},
                                    ])
                                return "OK", 200
                            elif text == "0":
                                SESSIONS[phone] = "main"
                                send_buttons(phone,
                                    "✅ رجعنا للقائمة الرئيسية.",
                                    [
                                        {"id": "1", "title": "📦 المنتجات ديالنا"},
                                        {"id": "2", "title": "🛠 الخدمات ديالنا"},
                                        {"id": "plus_more", "title": "➕ المزيد"},
                                    ])
                                return "OK", 200

                       
                        SESSIONS[phone] = "main"
                        send_buttons(phone,
                            "❓ معليش ما فهمتش، عاود اختار من القائمة:",
                            [
                                {"id": "1", "title": "📦 المنتجات ديالنا"},
                                {"id": "2", "title": "🛠 الخدمات ديالنا"},
                                {"id": "plus_more", "title": "➕ المزيد"},
                            ])
                        return "OK", 200

    except Exception as e:
        logging.error(f"Exception in webhook: {e}", exc_info=True)
        return "Error", 200

    return "OK", 200


if __name__ == "__main__":
    init_db()
    logging.info("Starting Flask app for WhatsApp bot.")
    app.run(port=5000, debug=True)
