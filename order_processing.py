DEFAULT_CURRENCY = "USD"

TAX_RATE = 0.21

COUPON_SAVE10 = "SAVE10"
COUPON_SAVE20 = "SAVE20"
COUPON_VIP = "VIP"

SAVE10_RATE = 0.10
SAVE20_RATE = 0.20
SAVE20_FALLBACK_RATE = 0.05

SAVE20_THRESHOLD = 200

VIP_DISCOUNT_DEFAULT = 50
VIP_DISCOUNT_LOW_SUBTOTAL = 10
VIP_LOW_SUBTOTAL_THRESHOLD = 100

ORDER_ID_SUFFIX = "X"



def parse_request(request: dict):
    user_id = request.get("user_id")
    items = request.get("items")
    coupon = request.get("coupon")
    currency = request.get("currency")
    return user_id, items, coupon, currency

def validate_request(user_id, items) -> None:
    if user_id is None:
        raise ValueError("user_id is required")
    if items is None:
        raise ValueError("items is required")

    if type(items) is not list:  # оставляем как в исходнике!
        raise ValueError("items must be a list")
    if len(items) == 0:
        raise ValueError("items must not be empty")

    validate_items(items)


def validate_items(items) -> None:
    for it in items:
        if "price" not in it or "qty" not in it:
            raise ValueError("item must have price and qty")
        if it["price"] <= 0:
            raise ValueError("price must be positive")
        if it["qty"] <= 0:
            raise ValueError("qty must be positive")


def process_checkout(request: dict) -> dict:
    user_id, items, coupon, currency = parse_request(request)

    if currency is None:
        currency = DEFAULT_CURRENCY

    validate_request(user_id, items)

    subtotal = 0
    for it in items:
        subtotal = subtotal + it["price"] * it["qty"]

    discount = 0
    if coupon is None or coupon == "":
        discount = 0
    elif coupon == COUPON_SAVE10:
        discount = int(subtotal * SAVE10_RATE)
    elif coupon == COUPON_SAVE20:
        if subtotal >= SAVE20_THRESHOLD:
            discount = int(subtotal * SAVE20_RATE)
        else:
            discount = int(subtotal * SAVE20_FALLBACK_RATE)
    elif coupon == COUPON_VIP:
        discount = VIP_DISCOUNT_DEFAULT
        if subtotal < VIP_LOW_SUBTOTAL_THRESHOLD:
            discount = VIP_DISCOUNT_LOW_SUBTOTAL
    else:
        raise ValueError("unknown coupon")

    total_after_discount = subtotal - discount
    if total_after_discount < 0:
        total_after_discount = 0

    tax = int(total_after_discount * TAX_RATE)
    total = total_after_discount + tax

    order_id = str(user_id) + "-" + str(len(items)) + "-" + ORDER_ID_SUFFIX

    return {
        "order_id": order_id,
        "user_id": user_id,
        "currency": currency,
        "subtotal": subtotal,
        "discount": discount,
        "tax": tax,
        "total": total,
        "items_count": len(items),
    }