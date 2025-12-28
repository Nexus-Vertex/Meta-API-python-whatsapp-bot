from utils import (
    init_db,
    generate_order_id,
    add_order,
    export_orders_to_excel
)

init_db()


order_id = generate_order_id()


add_order(
    phone="+212714150342",
    client_name=" Sendibad ",
    order_id=order_id,
    status="📦 طلب جديد",
    product_name="BIKE ",
    price=7500.00,
    ville="meknes",
    address="Bd Zerktouni, Maarif"
)

export_orders_to_excel("orders.xlsx")

print("✅ Test terminé avec succès.")
