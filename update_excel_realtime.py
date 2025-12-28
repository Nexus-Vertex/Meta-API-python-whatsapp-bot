import time
from utils import export_orders_to_excel, auto_progress_statuses, status_statistics, log_status_change
import os
import threading

FILENAME = "orders.xlsx"

def update_status_loop():
    """Loop مستقل لتحديث جميع الحالات في DB وكتابة log خارجي"""
    while True:
        try:
            auto_progress_statuses()
            stats = status_statistics()
            log_status_change(stats)
        except Exception as e:
            print(f"❌ خطأ في تحديث الحالات: {e}")
        time.sleep(30)

def update_excel_loop():
    """Loop مستقل لتصدير Excel كل 3 ثواني"""
    while True:
        try:
            if os.path.exists(FILENAME):
                os.remove(FILENAME)
            export_orders_to_excel(FILENAME)
            print(f"✅ Excel تم تحديثه: {FILENAME}")
        except Exception as e:
            print(f"❌ خطأ أثناء تحديث Excel: {e}")
        time.sleep(15)

# تشغيل Loops في Threads مستقلة
threading.Thread(target=update_status_loop, daemon=True).start()
threading.Thread(target=update_excel_loop, daemon=True).start()

print("🚀 التحديث التلقائي للحالات وExcel وLog شغال الآن...")

# منع السكريبت من الإغلاق
while True:
    time.sleep(15)
