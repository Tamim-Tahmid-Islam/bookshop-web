"""
Populate Realistic Order History for Popular Books
Ensures 'order_items' and 'orders' have genuine sales history for top books,
enabling the 'Most Popular Available Books' feature to reflect rich database history.
"""
import sqlite3
import random
import datetime

DB_PATH = 'D:/Projects/University Project/pagevault.db'

POPULAR_BOOK_WEIGHTS = [
    (47, 52),  # Atomic Habits
    (14, 45),  # Clean Code
    (15, 38),  # The Pragmatic Programmer
    (91, 35),  # Sapiens
    (1,  30),  # Database System Concepts
    (75, 27),  # The Alchemist
    (2,  24),  # Designing Data-Intensive Applications
    (27, 22),  # Harry Potter and the Sorcerer's Stone
    (37, 20),  # Dune
    (20, 18),  # Deep Learning
    (49, 16),  # Deep Work
    (9,  15),  # Clean Architecture
    (10, 13),  # Introduction to Algorithms (CLRS)
    (50, 12),  # Can't Hurt Me
    (48, 11),  # The Subtle Art of Not Giving a F*ck
    (52, 10),  # How to Win Friends and Influence People
    (12, 9),   # Design Patterns
    (13, 8),   # Patterns of Enterprise Application Architecture
    (22, 8),   # Hands-On Machine Learning
    (5,  7),   # Database Internals
    (6,  6),   # Streaming Systems
    (16, 6),   # Refactoring
]

CUSTOMER_NAMES = [
    ('Sadia Rahman', '01711987654', 'House 24, Road 11, Banani', 'Dhaka'),
    ('Tanvir Ahmed', '01819234567', 'Flat 4B, Dhanmondi 9/A', 'Dhaka'),
    ('Farhana Kabir', '01912345678', 'Chashara, Narayanganj', 'Narayanganj'),
    ('Mehedi Hasan', '01678123456', 'Agrabad C/A, Chittagong', 'Chittagong'),
    ('Nusrat Jahan', '01755667788', 'Zindabazar, Sylhet', 'Sylhet'),
    ('Mahmudul Haque', '01844332211', 'Uttara Sector 7', 'Dhaka'),
    ('Anika Tabassum', '01988776655', 'GEC Circle, Chittagong', 'Chittagong'),
    ('Shakil Chowdhury', '01722334455', 'Mirpur DOHS', 'Dhaka'),
    ('Rashedul Islam', '01511223344', 'Shaheb Bazar, Rajshahi', 'Rajshahi'),
    ('Samira Khan', '01799887766', 'Gulshan 2, Dhaka', 'Dhaka')
]

PAYMENT_METHODS = ['bKash', 'Nagad', 'Card', 'Cash on Delivery']

def run():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get book prices
    cursor.execute("SELECT book_id, price, discount_pct FROM books;")
    book_meta = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

    base_date = datetime.datetime(2026, 9, 15)
    order_idx = 100

    print("Generating orders for popular books...")

    for book_id, target_qty in POPULAR_BOOK_WEIGHTS:
        if book_id not in book_meta:
            continue
        price, discount = book_meta[book_id]
        unit_price = round(price * (1.0 - (discount / 100.0)), 2)

        # Distribute target_qty across multiple orders
        remaining = target_qty
        while remaining > 0:
            qty = min(remaining, random.randint(1, 3))
            remaining -= qty
            order_idx += 1

            cust_name, cust_phone, address, district = random.choice(CUSTOMER_NAMES)
            pay_method = random.choice(PAYMENT_METHODS)
            delivery_fee = 60.0 if district == 'Dhaka' else 120.0
            subtotal = round(unit_price * qty, 2)
            total_amount = round(subtotal + delivery_fee, 2)
            order_code = f"PV-{random.randint(100000, 999999)}-{order_idx}"
            trx_id = f"TRX{random.randint(10000000, 99999999)}" if pay_method != 'Cash on Delivery' else ''
            
            day_offset = random.randint(1, 60)
            order_date = (base_date + datetime.timedelta(days=day_offset, hours=random.randint(8, 20))).strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute("""
                INSERT INTO orders (
                    order_code, user_id, customer_name, customer_phone, delivery_address,
                    district, payment_method, payment_status, order_status, subtotal,
                    delivery_fee, total_amount, created_at, transaction_id
                ) VALUES (?, NULL, ?, ?, ?, ?, ?, 'Completed', 'Confirmed', ?, ?, ?, ?, ?)
            """, (
                order_code, cust_name, cust_phone, address, district,
                pay_method, subtotal, delivery_fee, total_amount, order_date, trx_id
            ))
            order_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO order_items (order_id, book_id, quantity, unit_price, total_price)
                VALUES (?, ?, ?, ?, ?)
            """, (order_id, book_id, qty, unit_price, subtotal))

    conn.commit()

    # Verify top sold books
    cursor.execute("""
        SELECT b.book_id, b.title, b.stock_qty, SUM(oi.quantity) as total_sold
        FROM books b
        JOIN order_items oi ON b.book_id = oi.book_id
        GROUP BY b.book_id
        ORDER BY total_sold DESC
        LIMIT 15;
    """)
    print("\nVerified Top 15 Sold Books in Database:")
    for r in cursor.fetchall():
        print(f"ID: {r[0]:2d} | Sold: {r[3]:2d} | Stock: {r[2]:3d} | Title: {r[1]}")

    conn.close()
    print("\nOrder history populated successfully!")

if __name__ == '__main__':
    run()
