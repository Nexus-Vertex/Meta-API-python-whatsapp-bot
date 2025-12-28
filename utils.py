import sqlite3
import logging
import datetime
import random
import os

DB_PATH = "database.db"

# --- إعداد تدفق الحالات ---
STATUS_FLOW = ["EN ATTENTE", "CONFIRMÉ", "EN LIVRAISON", "LIVRÉ", "TERMINÉ"]
STEP_SECONDS = 20
INITIAL_BOT_STATUS = "📦 طلب جديد"

# بعض المرادفات لتصحيح الإدخالات القديمة
STATUS_ALIASES = {
    "EN ATTEND": "EN ATTENTE",
    "CONFIRER": "CONFIRMÉ",
    "CONFIRME": "CONFIRMÉ",
    "LIVRISON": "EN LIVRAISON",
    "LIVRE": "LIVRÉ",
    "TERMINE": "TERMINÉ",
}

STATUS_LOG_FILE = "status_log.txt"

# -----------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            client_name TEXT NOT NULL,
            order_id TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL,
            product_name TEXT NOT NULL,
            price REAL NOT NULL,
            ville TEXT NOT NULL,
            address TEXT NOT NULL,
            last_updated TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def _normalize_status(status: str) -> str:
    s = (status or "").strip().upper()
    if s == INITIAL_BOT_STATUS.upper():
        return "EN ATTENTE"
    return STATUS_ALIASES.get(s, s)

def generate_order_id():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    while True:
        rand = random.randint(0, 999)
        order_id = f"CMD{rand:03d}"
        cursor.execute("SELECT 1 FROM orders WHERE order_id = ?", (order_id,))
        if not cursor.fetchone():
            break
    conn.close()
    return order_id

def add_order(phone, client_name, order_id, status, product_name, price, ville, address):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO orders (phone, client_name, order_id, status, product_name, price, ville, address, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        phone,
        client_name,
        order_id,
        status,
        product_name,
        price,
        ville,
        address,
        now
    ))
    conn.commit()
    conn.close()

def get_order_by_phone(phone):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT order_id, status, client_name, product_name, price, ville, address, last_updated
        FROM orders
        WHERE phone = ?
        ORDER BY id DESC
        LIMIT 1
    """, (phone,))
    order = cursor.fetchone()
    conn.close()
    return order

def _progress_one_status(current_status: str, last_updated_str: str, now: datetime.datetime):
    try:
        last_updated = datetime.datetime.strptime(last_updated_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return current_status, False

    current_status = _normalize_status(current_status)
    if current_status not in STATUS_FLOW:
        return current_status, False
    if current_status == STATUS_FLOW[-1]:
        return current_status, False

    elapsed_seconds = (now - last_updated).total_seconds()
    if elapsed_seconds < STEP_SECONDS:
        return current_status, False

    idx = STATUS_FLOW.index(current_status)
    new_idx = min(idx + 1, len(STATUS_FLOW) - 1)
    new_status = STATUS_FLOW[new_idx]
    if new_status != current_status:
        return new_status, True
    return current_status, False

def auto_progress_statuses():
    import collections
    from webhook import send_message  # تأكد أن send_message موجودة فـ webhook.py
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.datetime.now()

    logging.debug("=== /check_status CALLED ===")

    cursor.execute("SELECT id, phone, order_id, status, last_updated FROM orders")
    rows = cursor.fetchall()
    logging.debug(f"DEBUG all rows from orders table: {rows}")

    to_update = []
    updated_orders = []
    status_counter = collections.Counter()

    # --- تحديد الطلبات اللي خاصها تتبدل
    for row in rows:
        _id, phone, order_id, status, last_updated = row
        logging.debug(f"DEBUG row: id={_id}, phone={phone}, order_id={order_id}, status={status}, last_updated={last_updated}")

        new_status, should_update = _progress_one_status(status, last_updated, now)
        logging.debug(f"DEBUG _progress_one_status -> new_status={new_status}, should_update={should_update}")

        status_counter[status] += 1

        if should_update:
            norm_status = _normalize_status(new_status)
            to_update.append((norm_status, now.strftime("%Y-%m-%d %H:%M:%S"), _id))
            logging.debug(f"DEBUG will update: id={_id}, new_status={norm_status}")

    # --- تحديث DB وإرسال الرسائل
    if to_update:
        cursor.executemany(
            "UPDATE orders SET status = ?, last_updated = ? WHERE id = ?",
            to_update
        )
        conn.commit()
        logging.debug(f"DEBUG updated rows committed: {to_update}")

        for status, last_updated_str, _id in to_update:
            cursor.execute("SELECT phone, order_id, product_name FROM orders WHERE id = ?", (_id,))
            row = cursor.fetchone()
            if row:
                phone, order_id, product_name = row
                updated_orders.append((phone, order_id, status))

                # --- الرسائل حسب الحالة
                if status == "EN ATTENTE":
                    message = f"📦 حالة طلبك رقم {order_id} تبدلات دابا: في الانتظار ⏳\nالمنتج: {product_name}\nحنا توصلنا بطلبك وراه غادي يتم تأكيده قريبا."
                elif status == "CONFIRMÉ":
                    message = f"📦 حالة طلبك رقم {order_id} تبدلات دابا: مؤكد ✅\nالمنتج: {product_name}\nطلبك تأكد رسمياً وغادي نحضروه للتوصيل."
                elif status == "EN LIVRAISON":
                    message = f"📦 حالة طلبك رقم {order_id} تبدلات دابا: في الطريق 🚚\nالمنتج: {product_name}\nطلبك راه حاليا في التوصيل وغادي يوصل للعنوان اللي عطيتنا."
                elif status == "LIVRÉ":
                    message = f"📦 حالة طلبك رقم {order_id} تبدلات دابا: تم التوصيل 🎉\nالمنتج: {product_name}\nشكراً لك! طلبك وصل للعنوان ديالك."
                elif status == "TERMINÉ":
                    message = f"📦 حالة طلبك رقم {order_id} تبدلات دابا: منتهية ✅\nالمنتج: {product_name}\nجميع الإجراءات ديال الطلب تمّت بنجاح. شكراً على ثقتك بنا."
                else:
                    message = f"📦 حالة طلبك رقم {order_id} تبدلات دابا: {status}\nالمنتج: {product_name}\nغادي يتم تحديث الحالة تلقائياً في أقرب وقت."

                try:
                    send_message(phone, message)
                    logging.debug(f"✅ Message sent to {phone} for order {order_id}: {status}")
                except Exception as e:
                    logging.error(f"❌ Failed to send message to {phone} for order {order_id}: {e}")

    conn.close()
    logging.debug(f"DEBUG final updated_orders: {updated_orders}")
    logging.debug(f"DEBUG status statistics: {dict(status_counter)}")

    return updated_orders, dict(status_counter)


def export_orders_to_excel(filename):
    auto_progress_statuses()
    import pandas as pd
    from openpyxl.styles import Alignment, Font
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM orders", conn)
    conn.close()

    df.insert(0, "الترتيب", range(1, len(df) + 1))
    df = df[[
        "الترتيب", "order_id", "client_name", "phone", "product_name",
        "price", "ville", "address", "status", "last_updated"
    ]]
    df.columns = [
        "🔢 الترتيب", "📦 رقم الطلب", "👤 الاسم الكامل", "📱 رقم الهاتف",
        "🚲 المنتج", "💰 الثمن (درهم)", "🏙️ المدينة", "📍 العنوان",
        "📌 الحالة", "🕒 آخر تعديل"
    ]
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="الطلبات")
        sheet = writer.sheets["الطلبات"]
        for col in sheet.columns:
            max_length = 0
            col_letter = col[0].column_letter
            for cell in col:
                cell.alignment = Alignment(horizontal='center')
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except Exception:
                    pass
            sheet.column_dimensions[col_letter].width = max_length + 4
        for cell in sheet[1]:
            cell.font = Font(bold=True)

def status_statistics():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.datetime.now()
    cursor.execute("SELECT id, order_id, status, last_updated FROM orders")
    rows = cursor.fetchall()
    conn.close()
    stats = {"updated": [], "not_updated": []}
    for _id, order_id, status, last_updated in rows:
        new_status, should_update = _progress_one_status(status, last_updated, now)
        if should_update:
            stats["updated"].append({
                "order_id": order_id,
                "old_status": status,
                "new_status": new_status
            })
        else:
            elapsed_seconds = (now - datetime.datetime.strptime(last_updated, "%Y-%m-%d %H:%M:%S")).total_seconds()
            reason = ""
            if status not in STATUS_FLOW:
                reason = "Status غير معروف أو خارجي عن التدفق"
            elif status == STATUS_FLOW[-1]:
                reason = "الوصول لآخر حالة TERMINÉ"
            elif elapsed_seconds < STEP_SECONDS:
                reason = f"مازال ما دازت {STEP_SECONDS} ثواني من آخر تحديث"
            stats["not_updated"].append({
                "order_id": order_id,
                "status": status,
                "reason": reason
            })
    return stats

def log_status_change(stats):
    with open(STATUS_LOG_FILE, "a", encoding="utf-8") as f:
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"\n=== Log at {now_str} ===\n")
        if stats["updated"]:
            f.write("✅ الطلبات لي تبدلت حالاتهم:\n")
            for s in stats["updated"]:
                f.write(f"Order {s['order_id']}: {s['old_status']} → {s['new_status']}\n")
        else:
            f.write("✅ ماكاين حتى تغيير في الطلبات\n")
        if stats["not_updated"]:
            f.write("❌ الطلبات لي ما تبدلوش و السبب:\n")
            for s in stats["not_updated"]:
                f.write(f"Order {s['order_id']}: {s['status']} - {s['reason']}\n")
