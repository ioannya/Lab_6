# =========================
# Константы (убраны magic numbers)
# =========================

# Валюта по умолчанию
DEFAULT_CURRENCY = "USD"

# Ставка налога
TAX_RATE = 0.21

# Коды купонов
COUPON_SAVE10 = "SAVE10"
COUPON_SAVE20 = "SAVE20"
COUPON_VIP = "VIP"

# Проценты скидок
SAVE10_RATE = 0.10
SAVE20_RATE = 0.20
SAVE20_FALLBACK_RATE = 0.05

# Пороговые значения для скидок
SAVE20_THRESHOLD = 200
VIP_LOW_SUBTOTAL_THRESHOLD = 100

# Фиксированные скидки
VIP_DISCOUNT_DEFAULT = 50
VIP_DISCOUNT_LOW_SUBTOTAL = 10

# Суффикс для order_id
ORDER_ID_SUFFIX = "X"


# =========================
# Разбор входного запроса
# =========================
def parse_request(request: dict):
    """
    Извлекает данные из входного словаря.
    Поведение полностью соответствует исходному коду.
    """
    user_id = request.get("user_id")
    items = request.get("items")
    coupon = request.get("coupon")
    currency = request.get("currency")
    return user_id, items, coupon, currency


# =========================
# Валидация запроса
# =========================
def validate_request(user_id, items) -> None:
    """
    Проверяет корректность входных данных заказа.
    Если данные некорректны — выбрасывает ValueError.
    """
    if user_id is None:
        raise ValueError("user_id is required")
    if items is None:
        raise ValueError("items is required")

    # Оставлено type(items) is not list,
    # чтобы не менять поведение исходного кода
    if type(items) is not list:
        raise ValueError("items must be a list")
    if len(items) == 0:
        raise ValueError("items must not be empty")

    validate_items(items)


def validate_items(items) -> None:
    """
    Проверяет каждый товар в списке.
    """
    for it in items:
        if "price" not in it or "qty" not in it:
            raise ValueError("item must have price and qty")
        if it["price"] <= 0:
            raise ValueError("price must be positive")
        if it["qty"] <= 0:
            raise ValueError("qty must be positive")


# =========================
# Подсчёт стоимости товаров
# =========================
def calculate_subtotal(items) -> int:
    """
    Считает общую стоимость товаров без скидок и налогов.
    """
    subtotal = 0
    for it in items:
        subtotal = subtotal + it["price"] * it["qty"]
    return subtotal


# =========================
# Расчёт скидки
# =========================
def calculate_discount(subtotal: int, coupon) -> int:
    """
    Рассчитывает скидку на основе купона и суммы заказа.
    """
    if coupon is None or coupon == "":
        return 0

    if coupon == COUPON_SAVE10:
        return int(subtotal * SAVE10_RATE)

    if coupon == COUPON_SAVE20:
        if subtotal >= SAVE20_THRESHOLD:
            return int(subtotal * SAVE20_RATE)
        return int(subtotal * SAVE20_FALLBACK_RATE)

    if coupon == COUPON_VIP:
        discount = VIP_DISCOUNT_DEFAULT
        if subtotal < VIP_LOW_SUBTOTAL_THRESHOLD:
            discount = VIP_DISCOUNT_LOW_SUBTOTAL
        return discount

    # Неизвестный купон — ошибка (как в исходном коде)
    raise ValueError("unknown coupon")


# =========================
# Применение скидки
# =========================
def apply_discount(subtotal: int, discount: int) -> int:
    """
    Применяет скидку и не допускает отрицательной суммы.
    """
    total_after_discount = subtotal - discount
    if total_after_discount < 0:
        total_after_discount = 0
    return total_after_discount


# =========================
# Расчёт налога
# =========================
def calculate_tax(amount: int) -> int:
    """
    Рассчитывает налог от суммы после скидки.
    """
    return int(amount * TAX_RATE)


# =========================
# Генерация идентификатора заказа
# =========================
def generate_order_id(user_id, items_count: int) -> str:
    """
    Формирует идентификатор заказа.
    """
    return str(user_id) + "-" + str(items_count) + "-" + ORDER_ID_SUFFIX


# =========================
# Основной сценарий оформления заказа
# =========================
def process_checkout(request: dict) -> dict:
    """
    Основная функция обработки заказа.
    Читается сверху вниз как сценарий.
    """
    # 1. Разбор запроса
    user_id, items, coupon, currency = parse_request(request)

    # 2. Значения по умолчанию
    if currency is None:
        currency = DEFAULT_CURRENCY

    # 3. Валидация данных
    validate_request(user_id, items)

    # 4. Расчёты
    subtotal = calculate_subtotal(items)
    discount = calculate_discount(subtotal, coupon)
    total_after_discount = apply_discount(subtotal, discount)
    tax = calculate_tax(total_after_discount)
    total = total_after_discount + tax

    # 5. Генерация id заказа
    order_id = generate_order_id(user_id, len(items))

    # 6. Формирование результата
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
