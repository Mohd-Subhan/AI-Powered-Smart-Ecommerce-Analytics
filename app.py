import os
import math
import streamlit as st
import pandas as pd
import plotly.express as px

from pymongo import MongoClient, ASCENDING
from pymongo.errors import PyMongoError

from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Smart E-Commerce Analytics",
    page_icon="🛒",
    layout="wide"
)

load_dotenv()


# =========================================================
# 2. CONSTANTS
# =========================================================

DATABASE_NAME = "ecommerce_db"
COLLECTION_NAME = "products"

VALID_CATEGORIES = [
    "Electronics",
    "Fashion",
    "Home",
    "Books",
    "Sports"
]


# =========================================================
# 3. HELPER FUNCTIONS
# =========================================================

def get_products_dataframe(collection):
    """
    Read products from MongoDB and return a DataFrame.
    """

    products = list(
        collection.find(
            {},
            {"_id": 0}
        )
    )

    return pd.DataFrame(products)


def validate_product(product):
    """
    Validate product data before insertion or update.
    """

    title = product.get("title")

    if not isinstance(title, str) or not title.strip():
        return False, "Product title cannot be empty."

    category = product.get("category")

    if category not in VALID_CATEGORIES:
        return False, "Please select a valid category."

    price = product.get("price")

    if (
        isinstance(price, bool)
        or not isinstance(price, (int, float))
        or not math.isfinite(price)
        or price <= 0
    ):
        return False, "Price must be a positive number."

    stock = product.get("stock")

    if (
        isinstance(stock, bool)
        or not isinstance(stock, int)
        or stock < 0
    ):
        return False, "Stock must be a non-negative integer."

    description = product.get("description")

    if not isinstance(description, str) or not description.strip():
        return False, "Description cannot be empty."

    rating = product.get("rating")

    if (
        isinstance(rating, bool)
        or not isinstance(rating, (int, float))
        or not math.isfinite(rating)
        or not 0 <= rating <= 5
    ):
        return False, "Rating must be between 0 and 5."

    return True, "Product data is valid."


def get_product_label(product):
    """
    Create a readable label for product selection.
    """

    return (
        f'{product.get("product_id", "Unknown")} - '
        f'{product.get("title", "Untitled")}'
    )


def get_collection_stats(collection, query):
    """
    Return MongoDB execution statistics for a query.
    """

    return collection.find(query).explain("executionStats")


# =========================================================
# 4. APPLICATION HEADER
# =========================================================

st.title("🛒 AI-Powered Smart E-Commerce Analytics")
st.caption(
    "Product Analytics | Inventory Management | "
    "Recommendations | Query Optimization"
)

st.divider()


# =========================================================
# 5. SIDEBAR: DATABASE CONNECTION
# =========================================================

st.sidebar.title("⚙️ Application Settings")

st.sidebar.subheader("MongoDB Atlas Connection")

# The existing URI comes from the .env file.
# The password-masked field allows an optional override.

# Read MongoDB URI from local environment first.
default_uri = os.getenv("MONGO_URI", "")

# If not available, read it from Streamlit Cloud secrets.
if not default_uri:
    try:
        default_uri = st.secrets["MONGO_URI"]
    except Exception:
        default_uri = ""

mongo_uri = st.sidebar.text_input(
    "MongoDB Connection String",
    value=default_uri,
    type="password",
    help=(
        "Loaded from .env by default. "
        "You may override it here for this session."
    )
)

connect_button = st.sidebar.button(
    "Connect to MongoDB",
    use_container_width=True
)


# =========================================================
# 6. DATABASE CONNECTION
# =========================================================

if "mongo_client" not in st.session_state:
    st.session_state.mongo_client = None

if "mongo_uri" not in st.session_state:
    st.session_state.mongo_uri = None

if connect_button:

    if not mongo_uri.strip():

        st.sidebar.error(
            "Please provide your MongoDB connection string."
        )

    else:

        new_client = None

        try:

            new_client = MongoClient(
                mongo_uri.strip(),
                serverSelectionTimeoutMS=10000
            )

            # Verify the connection before saving the client.
            new_client.admin.command("ping")

            # Close an earlier client if the user reconnects.
            old_client = st.session_state.mongo_client

            if old_client is not None:
                old_client.close()

            st.session_state.mongo_client = new_client
            st.session_state.mongo_uri = mongo_uri.strip()

            st.sidebar.success(
                "Connected to MongoDB Atlas!"
            )

        except PyMongoError as error:

            if new_client is not None:
                new_client.close()

            st.sidebar.error(
                f"MongoDB connection failed: {error}"
            )


# If the user changes the connection string, ask them to reconnect.

if (
    st.session_state.mongo_client is not None
    and st.session_state.mongo_uri != mongo_uri.strip()
):
    st.warning(
        "The connection string has changed. "
        "Click 'Connect to MongoDB' to reconnect."
    )


client = st.session_state.mongo_client

if client is None:

    st.info(
        "👈 Enter your MongoDB connection string if needed, "
        "then click **Connect to MongoDB** to begin."
    )

    st.stop()


db = client[DATABASE_NAME]
products_collection = db[COLLECTION_NAME]


# =========================================================
# 7. SIDEBAR NAVIGATION
# =========================================================

st.sidebar.divider()

selected_page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard & Analytics",
        "Manage Inventory",
        "Recommendation Engine",
        "Query Optimization & Index Inspector"
    ]
)


# =========================================================
# TAB 1: DASHBOARD & ANALYTICS
# =========================================================

if selected_page == "Dashboard & Analytics":

    st.header("📊 Dashboard & Analytics")

    try:

        # -------------------------------------------------
        # A. TOTAL PRODUCTS
        # -------------------------------------------------

        total_products = products_collection.count_documents({})


        # -------------------------------------------------
        # B. TOTAL INVENTORY VALUE
        # -------------------------------------------------
        # Inventory value = sum of price * stock

        inventory_pipeline = [
            {
                "$group": {
                    "_id": None,
                    "total_inventory_value": {
                        "$sum": {
                            "$multiply": [
                                "$price",
                                "$stock"
                            ]
                        }
                    }
                }
            }
        ]

        inventory_result = list(
            products_collection.aggregate(
                inventory_pipeline
            )
        )

        total_inventory_value = (
            inventory_result[0]["total_inventory_value"]
            if inventory_result
            else 0
        )


        # -------------------------------------------------
        # C. AVERAGE PRODUCT PRICE
        # -------------------------------------------------

        average_pipeline = [
            {
                "$group": {
                    "_id": None,
                    "average_price": {
                        "$avg": "$price"
                    }
                }
            }
        ]

        average_result = list(
            products_collection.aggregate(
                average_pipeline
            )
        )

        average_price = (
            average_result[0]["average_price"]
            if average_result
            else 0
        )


        # -------------------------------------------------
        # D. METRIC CARDS
        # -------------------------------------------------

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total Products",
            f"{total_products:,}"
        )

        col2.metric(
            "Total Inventory Value",
            f"₹{total_inventory_value:,.2f}"
        )

        col3.metric(
            "Average Product Price",
            f"₹{average_price:,.2f}"
        )


        st.divider()


        # -------------------------------------------------
        # E. PRODUCTS PER CATEGORY
        # -------------------------------------------------

        category_pipeline = [
            {
                "$group": {
                    "_id": "$category",
                    "total_products": {
                        "$sum": 1
                    }
                }
            },
            {
                "$sort": {
                    "total_products": -1
                }
            }
        ]

        category_results = list(
            products_collection.aggregate(
                category_pipeline
            )
        )

        if category_results:

            category_df = pd.DataFrame(
                [
                    {
                        "Category": item["_id"],
                        "Total Products": item["total_products"]
                    }
                    for item in category_results
                ]
            )

            fig1 = px.bar(
                category_df,
                x="Category",
                y="Total Products",
                color="Category",
                title="Total Products per Category",
                text="Total Products"
            )

            st.plotly_chart(
                fig1,
                use_container_width=True
            )

        else:

            st.info("No products available for category analysis.")


        # -------------------------------------------------
        # F. AVERAGE PRICE PER CATEGORY
        # -------------------------------------------------

        price_pipeline = [
            {
                "$group": {
                    "_id": "$category",
                    "average_price": {
                        "$avg": "$price"
                    }
                }
            },
            {
                "$sort": {
                    "average_price": -1
                }
            }
        ]

        price_results = list(
            products_collection.aggregate(
                price_pipeline
            )
        )

        if price_results:

            price_df = pd.DataFrame(
                [
                    {
                        "Category": item["_id"],
                        "Average Price": round(
                            item["average_price"],
                            2
                        )
                    }
                    for item in price_results
                ]
            )

            fig2 = px.bar(
                price_df,
                x="Category",
                y="Average Price",
                color="Category",
                title="Average Price per Category",
                text="Average Price"
            )

            st.plotly_chart(
                fig2,
                use_container_width=True
            )

        else:

            st.info("No price data available.")


    except PyMongoError as error:

        st.error(f"Dashboard database error: {error}")


# =========================================================
# TAB 2: MANAGE INVENTORY
# =========================================================

elif selected_page == "Manage Inventory":

    st.header("📦 Manage Inventory")

    create_tab, read_tab, update_tab, delete_tab = st.tabs(
        [
            "Create Product",
            "View & Search",
            "Update Product",
            "Delete Product"
        ]
    )


    # -----------------------------------------------------
    # A. CREATE
    # -----------------------------------------------------

    with create_tab:

        st.subheader("Add a New Product")

        with st.form("create_product_form"):

            product_id = st.text_input(
                "Product ID",
                placeholder="Example: P1021"
            ).strip()

            title = st.text_input(
                "Product Title"
            ).strip()

            category = st.selectbox(
                "Category",
                VALID_CATEGORIES
            )

            price = st.number_input(
                "Price (₹)",
                min_value=0.0,
                value=100.0,
                step=50.0
            )

            stock = st.number_input(
                "Stock Quantity",
                min_value=0,
                value=10,
                step=1
            )

            description = st.text_area(
                "Description"
            ).strip()

            rating = st.number_input(
                "Rating",
                min_value=0.0,
                max_value=5.0,
                value=4.0,
                step=0.1
            )

            create_submitted = st.form_submit_button(
                "Add Product"
            )

        if create_submitted:

            new_product = {
                "product_id": product_id,
                "title": title,
                "category": category,
                "price": price,
                "stock": stock,
                "description": description,
                "rating": rating
            }

            if not product_id:

                st.error("Product ID cannot be empty.")

            else:

                is_valid, message = validate_product(
                    new_product
                )

                if not is_valid:

                    st.error(message)

                else:

                    try:

                        # Prevent duplicate product IDs.
                        existing_product = (
                            products_collection.find_one(
                                {
                                    "product_id": product_id
                                }
                            )
                        )

                        if existing_product:

                            st.error(
                                "A product with this ID already exists."
                            )

                        else:

                            products_collection.insert_one(
                                new_product
                            )

                            st.success(
                                f"Product '{title}' added successfully!"
                            )

                            st.rerun()

                    except PyMongoError as error:

                        st.error(
                            f"Could not insert product: {error}"
                        )


    # -----------------------------------------------------
    # B. READ AND SEARCH
    # -----------------------------------------------------

    with read_tab:

        st.subheader("View and Search Products")

        try:

            products_df = get_products_dataframe(
                products_collection
            )

            if products_df.empty:

                st.info("No products are available.")

            else:

                search_text = st.text_input(
                    "Search by product title or description"
                )

                category_options = [
                    "All"
                ] + sorted(
                    products_df["category"].dropna().unique().tolist()
                )

                selected_category = st.selectbox(
                    "Filter by Category",
                    category_options
                )

                min_price = float(
                    products_df["price"].min()
                )

                max_price = float(
                    products_df["price"].max()
                )

                price_range = st.slider(
                    "Price Range (₹)",
                    min_value=min_price,
                    max_value=max_price,
                    value=(min_price, max_price)
                )

                filtered_df = products_df.copy()

                if search_text.strip():

                    search_mask = (
                        filtered_df["title"]
                        .fillna("")
                        .str.contains(
                            search_text,
                            case=False,
                            regex=False
                        )
                        |
                        filtered_df["description"]
                        .fillna("")
                        .str.contains(
                            search_text,
                            case=False,
                            regex=False
                        )
                    )

                    filtered_df = filtered_df[
                        search_mask
                    ]

                if selected_category != "All":

                    filtered_df = filtered_df[
                        filtered_df["category"]
                        == selected_category
                    ]

                filtered_df = filtered_df[
                    (filtered_df["price"] >= price_range[0])
                    &
                    (filtered_df["price"] <= price_range[1])
                ]

                st.write(
                    f"Matching products: {len(filtered_df)}"
                )

                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    hide_index=True
                )

        except PyMongoError as error:

            st.error(
                f"Could not read products: {error}"
            )


    # -----------------------------------------------------
    # C. UPDATE
    # -----------------------------------------------------

    with update_tab:

        st.subheader("Update Product Price or Stock")

        try:

            available_products = list(
                products_collection.find(
                    {},
                    {
                        "_id": 0,
                        "product_id": 1,
                        "title": 1,
                        "price": 1,
                        "stock": 1
                    }
                ).sort(
                    "product_id",
                    ASCENDING
                )
            )

            if not available_products:

                st.info("No products are available to update.")

            else:

                selected_product = st.selectbox(
                    "Select Product",
                    available_products,
                    format_func=get_product_label,
                    key="update_product_select"
                )

                st.write(
                    f"Product ID: {selected_product['product_id']}"
                )

                with st.form("update_product_form"):

                    new_price = st.number_input(
                        "New Price (₹)",
                        min_value=0.0,
                        value=float(
                            selected_product["price"]
                        ),
                        step=50.0
                    )

                    new_stock = st.number_input(
                        "New Stock",
                        min_value=0,
                        value=int(
                            selected_product["stock"]
                        ),
                        step=1
                    )

                    update_submitted = st.form_submit_button(
                        "Update Product"
                    )

                if update_submitted:

                    update_data = {
                        "price": new_price,
                        "stock": new_stock
                    }

                    if (
                        new_price <= 0
                        or not math.isfinite(new_price)
                    ):

                        st.error(
                            "Price must be greater than zero."
                        )

                    elif new_stock < 0:

                        st.error(
                            "Stock cannot be negative."
                        )

                    else:

                        try:

                            result = (
                                products_collection.update_one(
                                    {
                                        "product_id":
                                        selected_product["product_id"]
                                    },
                                    {
                                        "$set": update_data
                                    }
                                )
                            )

                            if result.matched_count:

                                st.success(
                                    "Product updated successfully!"
                                )

                                st.rerun()

                            else:

                                st.warning(
                                    "Product was not found."
                                )

                        except PyMongoError as error:

                            st.error(
                                f"Update failed: {error}"
                            )

        except PyMongoError as error:

            st.error(
                f"Could not load products: {error}"
            )


    # -----------------------------------------------------
    # D. DELETE
    # -----------------------------------------------------

    with delete_tab:

        st.subheader("Delete a Product")

        try:

            available_products = list(
                products_collection.find(
                    {},
                    {
                        "_id": 0,
                        "product_id": 1,
                        "title": 1
                    }
                ).sort(
                    "product_id",
                    ASCENDING
                )
            )

            if not available_products:

                st.info("No products are available to delete.")

            else:

                product_to_delete = st.selectbox(
                    "Select Product to Delete",
                    available_products,
                    format_func=get_product_label,
                    key="delete_product_select"
                )

                st.warning(
                    "Deleting a product permanently removes "
                    "its document from MongoDB."
                )

                confirm_delete = st.checkbox(
                    "I confirm that I want to delete this product."
                )

                if st.button(
                    "Delete Product",
                    type="primary"
                ):

                    if not confirm_delete:

                        st.error(
                            "Please confirm the deletion first."
                        )

                    else:

                        result = (
                            products_collection.delete_one(
                                {
                                    "product_id":
                                    product_to_delete["product_id"]
                                }
                            )
                        )

                        if result.deleted_count:

                            st.success(
                                "Product deleted successfully!"
                            )

                            st.rerun()

                        else:

                            st.warning(
                                "Product was not found."
                            )

        except PyMongoError as error:

            st.error(
                f"Could not delete product: {error}"
            )


# =========================================================
# TAB 3: RECOMMENDATION ENGINE
# =========================================================

elif selected_page == "Recommendation Engine":

    st.header("🤖 Product Recommendation Engine")

    st.write(
        "Find products similar to your selected product "
        "using TF-IDF and cosine similarity."
    )

    try:

        products = list(
            products_collection.find(
                {},
                {"_id": 0}
            ).sort(
                "product_id",
                ASCENDING
            )
        )

        if len(products) < 2:

            st.warning(
                "At least two products are required "
                "to generate recommendations."
            )

        else:

            products_df = pd.DataFrame(products)

            # Combine the text fields used for recommendations.
            products_df["combined_text"] = (
                products_df["title"].fillna("")
                + " "
                + products_df["category"].fillna("")
                + " "
                + products_df["description"].fillna("")
            )

            selected_product = st.selectbox(
                "Choose a Product",
                products,
                format_func=get_product_label
            )

            if st.button("Generate Recommendations"):

                # -------------------------------------------------
                # A. TF-IDF VECTORIZATION
                # -------------------------------------------------

                vectorizer = TfidfVectorizer(
                    stop_words="english"
                )

                tfidf_matrix = vectorizer.fit_transform(
                    products_df["combined_text"]
                )


                # -------------------------------------------------
                # B. COSINE SIMILARITY
                # -------------------------------------------------

                similarity_matrix = cosine_similarity(
                    tfidf_matrix
                )

                selected_index = products_df.index[
                    products_df["product_id"]
                    == selected_product["product_id"]
                ][0]

                similarity_scores = (
                    similarity_matrix[selected_index]
                )


                # -------------------------------------------------
                # C. TOP 3 RECOMMENDATIONS
                # -------------------------------------------------

                ranked_indices = similarity_scores.argsort()[::-1]

                recommendations = []

                for index in ranked_indices:

                    # Do not recommend the selected product itself.
                    if index == selected_index:
                        continue

                    recommendations.append(
                        {
                            "product": products[index],
                            "score": float(
                                similarity_scores[index]
                            )
                        }
                    )

                    if len(recommendations) == 3:
                        break


                # -------------------------------------------------
                # D. DISPLAY RECOMMENDATIONS
                # -------------------------------------------------

                st.subheader(
                    f"Products similar to: "
                    f"{selected_product['title']}"
                )

                for rank, item in enumerate(
                    recommendations,
                    start=1
                ):

                    product = item["product"]
                    score = item["score"]

                    with st.container(border=True):

                        col1, col2 = st.columns(
                            [3, 1]
                        )

                        with col1:

                            st.markdown(
                                f"### {rank}. {product['title']}"
                            )

                            st.write(
                                f"Category: {product['category']}"
                            )

                            st.write(
                                product["description"]
                            )

                            st.write(
                                f"Price: ₹{product['price']:,.2f}"
                            )

                            st.write(
                                f"Rating: {product['rating']}/5"
                            )

                        with col2:

                            st.metric(
                                "Similarity",
                                f"{score:.1%}"
                            )

                st.caption(
                    "Similarity scores measure textual similarity, "
                    "not predicted purchase probability or product quality."
                )

    except PyMongoError as error:

        st.error(
            f"Recommendation engine database error: {error}"
        )


# =========================================================
# TAB 4: QUERY OPTIMIZATION & INDEX INSPECTOR
# =========================================================

elif selected_page == "Query Optimization & Index Inspector":

    st.header("⚡ Query Optimization & Index Inspector")

    st.write(
        "Compare an indexed query against a query "
        "that has no suitable secondary index."
    )

    st.info(
        "The examples below use your existing "
        "'category_price_idx' compound index."
    )


    # -----------------------------------------------------
    # A. INDEXED QUERY
    # -----------------------------------------------------

    st.subheader("1. Indexed Query")

    st.code(
        """
db.products.find({
    category: "Electronics",
    price: { $lt: 3000 }
})
        """,
        language="javascript"
    )

    st.write(
        "This query can use the compound index "
        "on category and price."
    )


    # -----------------------------------------------------
    # B. NON-INDEXED QUERY
    # -----------------------------------------------------

    st.subheader("2. Query Without a Suitable Secondary Index")

    st.code(
        """
db.products.find({
    stock: { $gte: 10 }
})
        """,
        language="javascript"
    )

    st.write(
        "The collection does not have a secondary index "
        "on stock, so MongoDB will generally need a "
        "collection scan for this query."
    )


    # -----------------------------------------------------
    # C. RUN EXPLAIN
    # -----------------------------------------------------

    if st.button("Run Query Performance Analysis"):

        indexed_query = {
            "category": "Electronics",
            "price": {
                "$lt": 3000
            }
        }

        non_indexed_query = {
            "stock": {
                "$gte": 10
            }
        }

        try:

            with st.spinner(
                "Analyzing MongoDB query execution plans..."
            ):

                indexed_stats = get_collection_stats(
                    products_collection,
                    indexed_query
                )

                non_indexed_stats = get_collection_stats(
                    products_collection,
                    non_indexed_query
                )


            # -------------------------------------------------
            # D. DISPLAY SUMMARY METRICS
            # -------------------------------------------------

            def extract_stats(explain_result):

                execution = explain_result.get(
                    "executionStats",
                    {}
                )

                return {
                    "Execution Time (ms)": execution.get(
                        "executionTimeMillis",
                        0
                    ),
                    "Documents Examined": execution.get(
                        "totalDocsExamined",
                        0
                    ),
                    "Documents Returned": execution.get(
                        "nReturned",
                        0
                    ),
                    "Keys Examined": execution.get(
                        "totalKeysExamined",
                        0
                    )
                }


            indexed_summary = extract_stats(
                indexed_stats
            )

            non_indexed_summary = extract_stats(
                non_indexed_stats
            )


            col1, col2 = st.columns(2)

            with col1:

                st.markdown("### Indexed Query")

                st.json(indexed_summary)

                st.write(
                    "Winning execution plan:"
                )

                st.code(
                    str(
                        indexed_stats.get(
                            "queryPlanner",
                            {}
                        ).get(
                            "winningPlan",
                            {}
                        )
                    ),
                    language="json"
                )

            with col2:

                st.markdown("### Query Without Suitable Index")

                st.json(non_indexed_summary)

                st.write(
                    "Winning execution plan:"
                )

                st.code(
                    str(
                        non_indexed_stats.get(
                            "queryPlanner",
                            {}
                        ).get(
                            "winningPlan",
                            {}
                        )
                    ),
                    language="json"
                )


            # -------------------------------------------------
            # E. COMPARISON TABLE
            # -------------------------------------------------

            comparison_df = pd.DataFrame(
                [
                    {
                        "Metric": metric,
                        "Indexed Query": indexed_summary[metric],
                        "Query Without Suitable Index":
                            non_indexed_summary[metric]
                    }
                    for metric in indexed_summary
                ]
            )

            st.subheader(
                "Performance Comparison"
            )

            st.dataframe(
                comparison_df,
                use_container_width=True,
                hide_index=True
            )


            # -------------------------------------------------
            # F. INDEX INFORMATION
            # -------------------------------------------------

            st.subheader("Existing Collection Indexes")

            index_information = list(
                products_collection.list_indexes()
            )

            index_rows = []

            for index in index_information:

                index_rows.append(
                    {
                        "Index Name": index["name"],
                        "Fields": str(
                            list(index["key"].items())
                        ),
                        "Unique": index.get(
                            "unique",
                            False
                        )
                    }
                )

            st.dataframe(
                pd.DataFrame(index_rows),
                use_container_width=True,
                hide_index=True
            )


        except PyMongoError as error:

            st.error(
                f"Query analysis failed: {error}"
            )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "AI-Powered Smart E-Commerce Analytics & "
    "Recommendation Engine | Python + MongoDB + Streamlit"
)