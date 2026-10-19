import os
from pymongo import MongoClient, ASCENDING, TEXT
from pymongo.errors import PyMongoError
from dotenv import load_dotenv


# --------------------------------------------------
# 1. LOAD ENVIRONMENT VARIABLES
# --------------------------------------------------

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError(
        "MONGO_URI is missing. Add your MongoDB connection "
        "string to the .env file."
    )


# --------------------------------------------------
# 2. CONNECT TO MONGODB ATLAS
# --------------------------------------------------

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=10000
)

try:
    # Verify that the database server is reachable.
    client.admin.command("ping")

    print("Successfully connected to MongoDB Atlas!")

    # Select database and collection.
    db = client["ecommerce_db"]
    products_collection = db["products"]


    # --------------------------------------------------
    # 3. SAMPLE E-COMMERCE PRODUCTS
    # --------------------------------------------------

    products = [
        {
            "product_id": "P1001",
            "title": "Wireless Bluetooth Headphones",
            "category": "Electronics",
            "price": 2499.00,
            "stock": 35,
            "description": "Wireless headphones with clear sound and noise cancellation.",
            "rating": 4.5
        },
        {
            "product_id": "P1002",
            "title": "Smart Fitness Watch",
            "category": "Electronics",
            "price": 3999.00,
            "stock": 20,
            "description": "Fitness watch with heart rate monitoring and activity tracking.",
            "rating": 4.3
        },
        {
            "product_id": "P1003",
            "title": "USB-C Fast Charger",
            "category": "Electronics",
            "price": 799.00,
            "stock": 60,
            "description": "Compact fast charger compatible with USB-C devices.",
            "rating": 4.4
        },
        {
            "product_id": "P1004",
            "title": "Mechanical Gaming Keyboard",
            "category": "Electronics",
            "price": 3299.00,
            "stock": 15,
            "description": "Mechanical keyboard with tactile keys and customizable lighting.",
            "rating": 4.6
        },
        {
            "product_id": "P1005",
            "title": "Portable Bluetooth Speaker",
            "category": "Electronics",
            "price": 1799.00,
            "stock": 28,
            "description": "Portable wireless speaker with powerful sound and long battery life.",
            "rating": 4.2
        },
        {
            "product_id": "P1006",
            "title": "Cotton Casual T-Shirt",
            "category": "Fashion",
            "price": 499.00,
            "stock": 100,
            "description": "Comfortable cotton t-shirt suitable for everyday wear.",
            "rating": 4.1
        },
        {
            "product_id": "P1007",
            "title": "Men's Running Shoes",
            "category": "Fashion",
            "price": 2199.00,
            "stock": 25,
            "description": "Lightweight running shoes designed for comfort and support.",
            "rating": 4.4
        },
        {
            "product_id": "P1008",
            "title": "Women's Shoulder Bag",
            "category": "Fashion",
            "price": 1499.00,
            "stock": 18,
            "description": "Stylish shoulder bag suitable for daily use and travel.",
            "rating": 4.3
        },
        {
            "product_id": "P1009",
            "title": "Classic Wrist Watch",
            "category": "Fashion",
            "price": 1899.00,
            "stock": 22,
            "description": "Classic wrist watch with a minimalist dial and durable strap.",
            "rating": 4.2
        },
        {
            "product_id": "P1010",
            "title": "Polarized Sunglasses",
            "category": "Fashion",
            "price": 999.00,
            "stock": 40,
            "description": "Polarized sunglasses offering stylish everyday eye protection.",
            "rating": 4.0
        },
        {
            "product_id": "P1011",
            "title": "Stainless Steel Water Bottle",
            "category": "Home",
            "price": 599.00,
            "stock": 75,
            "description": "Reusable insulated water bottle for hot and cold beverages.",
            "rating": 4.5
        },
        {
            "product_id": "P1012",
            "title": "LED Desk Lamp",
            "category": "Home",
            "price": 899.00,
            "stock": 32,
            "description": "Energy-efficient LED desk lamp with adjustable brightness.",
            "rating": 4.3
        },
        {
            "product_id": "P1013",
            "title": "Memory Foam Pillow",
            "category": "Home",
            "price": 1199.00,
            "stock": 26,
            "description": "Supportive memory foam pillow designed for comfortable sleep.",
            "rating": 4.4
        },
        {
            "product_id": "P1014",
            "title": "Non-Stick Frying Pan",
            "category": "Home",
            "price": 1299.00,
            "stock": 19,
            "description": "Non-stick frying pan designed for convenient everyday cooking.",
            "rating": 4.1
        },
        {
            "product_id": "P1015",
            "title": "Ceramic Coffee Mug Set",
            "category": "Home",
            "price": 699.00,
            "stock": 45,
            "description": "Set of ceramic coffee mugs suitable for home and office.",
            "rating": 4.2
        },
        {
            "product_id": "P1016",
            "title": "Python Programming Handbook",
            "category": "Books",
            "price": 549.00,
            "stock": 50,
            "description": "Beginner-friendly handbook covering Python programming fundamentals.",
            "rating": 4.7
        },
        {
            "product_id": "P1017",
            "title": "Data Science with Python",
            "category": "Books",
            "price": 799.00,
            "stock": 30,
            "description": "Learn data analysis and machine learning with Python examples.",
            "rating": 4.8
        },
        {
            "product_id": "P1018",
            "title": "Machine Learning Essentials",
            "category": "Books",
            "price": 899.00,
            "stock": 17,
            "description": "Introduction to machine learning algorithms and practical applications.",
            "rating": 4.6
        },
        {
            "product_id": "P1019",
            "title": "Yoga Exercise Mat",
            "category": "Sports",
            "price": 1099.00,
            "stock": 24,
            "description": "Non-slip exercise mat suitable for yoga and home workouts.",
            "rating": 4.3
        },
        {
            "product_id": "P1020",
            "title": "Adjustable Dumbbell Set",
            "category": "Sports",
            "price": 2799.00,
            "stock": 12,
            "description": "Adjustable dumbbell set for strength training at home.",
            "rating": 4.5
        }
    ]


    # --------------------------------------------------
    # 4. VALIDATE PRODUCT DATA
    # --------------------------------------------------

    valid_categories = {
        "Electronics",
        "Fashion",
        "Home",
        "Books",
        "Sports"
    }

    def validate_product(product):
        """
        Check that the product has valid required fields.
        Return True when valid; otherwise, return False.
        """

        # Title must be a non-empty string.
        title = product.get("title")

        if not isinstance(title, str) or not title.strip():
            return False

        # Price must be a positive number.
        # Boolean values are explicitly rejected.
        price = product.get("price")

        if (
            isinstance(price, bool)
            or not isinstance(price, (int, float))
            or price <= 0
        ):
            return False

        # Category must be one of our allowed categories.
        category = product.get("category")

        if category not in valid_categories:
            return False

        # Product ID must be a non-empty string.
        product_id = product.get("product_id")

        if not isinstance(product_id, str) or not product_id.strip():
            return False

        # Description must be a non-empty string.
        description = product.get("description")

        if not isinstance(description, str) or not description.strip():
            return False

        # Stock must be a non-negative integer.
        stock = product.get("stock")

        if (
            isinstance(stock, bool)
            or not isinstance(stock, int)
            or stock < 0
        ):
            return False

        # Rating must be a number between 0 and 5.
        rating = product.get("rating")

        if (
            isinstance(rating, bool)
            or not isinstance(rating, (int, float))
            or not 0 <= rating <= 5
        ):
            return False

        return True


    # --------------------------------------------------
    # 5. FILTER VALID PRODUCTS
    # --------------------------------------------------

    valid_products = []
    invalid_count = 0

    for product in products:
        if validate_product(product):
            valid_products.append(product)
        else:
            invalid_count += 1
            print(
                "Invalid product skipped:",
                product.get("product_id", "Unknown")
            )

    print(f"Valid products: {len(valid_products)}")
    print(f"Invalid products: {invalid_count}")


    # --------------------------------------------------
    # 6. INSERT PRODUCTS WITHOUT DUPLICATING THEM
    # --------------------------------------------------

    inserted_count = 0
    existing_count = 0

    for product in valid_products:

        result = products_collection.update_one(
            {"product_id": product["product_id"]},
            {"$setOnInsert": product},
            upsert=True
        )

        if result.upserted_id is not None:
            inserted_count += 1
        else:
            existing_count += 1

    print(f"New products inserted: {inserted_count}")
    print(f"Products already present: {existing_count}")


    # --------------------------------------------------
    # 7. CREATE COMPOUND INDEX
    # --------------------------------------------------

    products_collection.create_index(
        [
            ("category", ASCENDING),
            ("price", ASCENDING)
        ],
        name="category_price_idx"
    )

    print("Compound index created or already exists.")


    # --------------------------------------------------
    # 8. CREATE TEXT INDEX
    # --------------------------------------------------

    products_collection.create_index(
        [
            ("title", TEXT),
            ("description", TEXT)
        ],
        name="product_text_idx"
    )

    print("Text index created or already exists.")


    # --------------------------------------------------
    # 9. VERIFY FINAL PRODUCT COUNT
    # --------------------------------------------------

    total_products = products_collection.count_documents({})

    print("\n========== DATABASE SETUP COMPLETE ==========")
    print("Database: ecommerce_db")
    print("Collection: products")
    print(f"Total products in collection: {total_products}")
    print("=============================================")


except PyMongoError as error:
    print("MongoDB operation failed:", error)

finally:
    client.close()
    print("MongoDB connection closed.")