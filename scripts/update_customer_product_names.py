"""Update existing customers and products rows with meaningful column values."""

import time

import psycopg2

CUSTOMERS_UPDATE_SQL = """
UPDATE ecommerce.customers AS c
SET
    first_name = v.first_name,
    last_name = v.last_name,
    email = LOWER(v.first_name) || '.' || LOWER(v.last_name) || c.customer_id::text || '@shopsphere.com',
    country = v.country,
    city = v.city
FROM (
    SELECT
        customer_id,
        (ARRAY[
            'James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda',
            'William', 'Elizabeth', 'David', 'Barbara', 'Richard', 'Susan', 'Joseph',
            'Jessica', 'Thomas', 'Sarah', 'Charles', 'Karen', 'Daniel', 'Nancy',
            'Matthew', 'Lisa', 'Anthony', 'Betty', 'Mark', 'Margaret', 'Donald', 'Sandra'
        ])[1 + (customer_id % 30)] AS first_name,
        (ARRAY[
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
            'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson',
            'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez',
            'Thompson', 'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson'
        ])[1 + ((customer_id / 7)::bigint % 30)] AS last_name,
        (ARRAY[
            'United States', 'United States', 'United States', 'United Kingdom',
            'Canada', 'Australia', 'Germany', 'France', 'Netherlands', 'Spain',
            'Italy', 'Ireland', 'United States', 'Canada', 'United Kingdom'
        ])[1 + (customer_id % 15)] AS country,
        (ARRAY[
            'New York', 'Los Angeles', 'Chicago', 'London', 'Toronto', 'Sydney',
            'Berlin', 'Paris', 'Amsterdam', 'Madrid', 'Rome', 'Dublin',
            'Houston', 'Vancouver', 'Manchester'
        ])[1 + (customer_id % 15)] AS city
    FROM ecommerce.customers
) AS v
WHERE c.customer_id = v.customer_id
"""

PRODUCTS_UPDATE_SQL = """
UPDATE ecommerce.products AS p
SET product_name = v.product_name
FROM (
    SELECT
        product_id,
        TRIM(
            (ARRAY[
                'Premium', 'Essential', 'Classic', 'Ultra', 'Compact',
                'Deluxe', 'Everyday', 'Professional'
            ])[1 + (product_id % 8)] || ' ' ||
            CASE category_id
                WHEN 1 THEN (ARRAY[
                    'Wireless Bluetooth Headphones', 'Smart Watch', 'Portable Power Bank',
                    'USB-C Hub Adapter', '4K Webcam', 'Mechanical Keyboard'
                ])[1 + (product_id % 6)]
                WHEN 2 THEN (ARRAY[
                    'Stainless Steel Cookware Set', 'Ceramic Nonstick Frying Pan',
                    'Glass Food Storage Containers', 'Electric Kettle', 'Chef Knife Set'
                ])[1 + (product_id % 5)]
                WHEN 3 THEN (ARRAY[
                    'Cotton Crew Neck T-Shirt', 'Slim Fit Denim Jeans',
                    'Fleece Zip Hoodie', 'Linen Button-Down Shirt', 'Wool Winter Scarf'
                ])[1 + (product_id % 5)]
                WHEN 4 THEN (ARRAY[
                    'Running Sneakers', 'Leather Ankle Boots', 'Canvas Slip-On Shoes',
                    'Hiking Trail Shoes', 'Casual Loafers'
                ])[1 + (product_id % 5)]
                WHEN 5 THEN (ARRAY[
                    'Yoga Mat', 'Adjustable Dumbbell Set', 'Resistance Bands Kit',
                    'Camping Sleeping Bag', 'Insulated Water Bottle'
                ])[1 + (product_id % 5)]
                WHEN 6 THEN (ARRAY[
                    'Moisturizing Face Cream', 'Hydrating Shampoo', 'SPF 50 Sunscreen',
                    'Vitamin C Serum', 'Charcoal Face Mask'
                ])[1 + (product_id % 5)]
                WHEN 7 THEN (ARRAY[
                    'Building Blocks Set', 'Board Game Family Pack', 'Remote Control Car',
                    'Plush Teddy Bear', 'Puzzle 1000 Pieces'
                ])[1 + (product_id % 5)]
                WHEN 8 THEN (ARRAY[
                    'Mystery Novel Paperback', 'Cookbook Mediterranean Recipes',
                    'Children Storybook Collection', 'Business Leadership Guide',
                    'Travel Photography Journal'
                ])[1 + (product_id % 5)]
                WHEN 9 THEN (ARRAY[
                    'Ballpoint Pen Pack', 'Spiral Notebook Set', 'Desk Organizer Tray',
                    'Sticky Notes Assorted', 'Document File Folders'
                ])[1 + (product_id % 5)]
                WHEN 10 THEN (ARRAY[
                    'Expandable Garden Hose', 'Pruning Shears', 'Raised Bed Planter',
                    'LED Solar Path Lights', 'Organic Potting Soil'
                ])[1 + (product_id % 5)]
                WHEN 11 THEN (ARRAY[
                    'Car Phone Mount', 'Microfiber Wash Mitt', 'Tire Pressure Gauge',
                    'Emergency Roadside Kit', 'Seat Cover Set'
                ])[1 + (product_id % 5)]
                WHEN 12 THEN (ARRAY[
                    'Vitamin D Supplement', 'Protein Powder Vanilla', 'Fish Oil Capsules',
                    'Electrolyte Drink Mix', 'Daily Multivitamin'
                ])[1 + (product_id % 5)]
                WHEN 13 THEN (ARRAY[
                    'Sterling Silver Necklace', 'Gold Hoop Earrings', 'Leather Bracelet',
                    'Pearl Stud Earrings', 'Charm Pendant'
                ])[1 + (product_id % 5)]
                WHEN 14 THEN (ARRAY[
                    'Organic Cotton Onesie', 'Baby Monitor', 'Soft Plush Blanket',
                    'BPA-Free Sippy Cup', 'Diaper Bag Backpack'
                ])[1 + (product_id % 5)]
                WHEN 15 THEN (ARRAY[
                    'Stainless Dog Food Bowl', 'Cat Scratching Post', 'Pet Grooming Brush',
                    'Reflective Dog Leash', 'Automatic Pet Feeder'
                ])[1 + (product_id % 5)]
                WHEN 16 THEN (ARRAY[
                    'Ergonomic Office Desk Chair', 'Standing Desk Converter',
                    'Bookshelf 5-Tier', 'Queen Memory Foam Mattress', 'Nightstand with Drawer'
                ])[1 + (product_id % 5)]
                WHEN 17 THEN (ARRAY[
                    'Extra Virgin Olive Oil', 'Whole Bean Coffee', 'Granola Breakfast Cereal',
                    'Organic Green Tea', 'Dark Chocolate Bar'
                ])[1 + (product_id % 5)]
                WHEN 18 THEN (ARRAY[
                    'Cordless Drill Kit', 'Socket Wrench Set', 'Measuring Tape',
                    'Safety Goggles', 'Workbench Clamps'
                ])[1 + (product_id % 5)]
                WHEN 19 THEN (ARRAY[
                    'Acoustic Guitar Strings', 'Digital Piano Bench', 'Studio Microphone',
                    'DJ Headphones', 'Sheet Music Stand'
                ])[1 + (product_id % 5)]
                ELSE (ARRAY[
                    'Watercolor Paint Set', 'Sketchbook Hardcover', 'Acrylic Paint Tubes',
                    'Calligraphy Pen Set', 'Craft Glue Gun'
                ])[1 + (product_id % 5)]
            END
        ) AS product_name
    FROM ecommerce.products
) AS v
WHERE p.product_id = v.product_id
"""


def main() -> None:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="shopsphere",
        user="postgres",
        password="admin99",
    )
    cur = conn.cursor()

    for label, sql in [
        ("customers", CUSTOMERS_UPDATE_SQL),
        ("products", PRODUCTS_UPDATE_SQL),
    ]:
        t0 = time.time()
        cur.execute(sql)
        print(f"{label}: updated {cur.rowcount:,} rows in {time.time() - t0:.1f}s")

    conn.commit()

    cur.execute(
        """
        SELECT customer_id, first_name, last_name, email, country, city
        FROM ecommerce.customers
        ORDER BY customer_id
        LIMIT 5
        """
    )
    print("sample customers:", cur.fetchall())

    cur.execute(
        """
        SELECT product_id, product_name, category_id
        FROM ecommerce.products
        ORDER BY product_id
        LIMIT 8
        """
    )
    print("sample products:", cur.fetchall())

    cur.close()
    conn.close()
    print("done")


if __name__ == "__main__":
    main()
