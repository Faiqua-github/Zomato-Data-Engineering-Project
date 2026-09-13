# import os
# import numpy as np
# import pandas as pd
# import streamlit as st
# import snowflake.connector
# from openai import OpenAI
# import json
# from dotenv import load_dotenv

# load_dotenv()

# MODEL = "gpt-4o-mini"

# FORBIDDEN_WORDS = ['drop', 'delete', 'truncate', 'alter', 'update', 'insert', 'create', 'replace', 'grant', 'revoke']

# EXAMPLE_QUESTIONS = [
#     "Top 10 cities by GMV",
#     "Which cuisin has the most orders?",
#     "Average delivery time by city, worst first",
#     "Cancel rate by payment method"
# ]

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# SCHEMA = """
# Tables available (Snowflake). Use bare table names, no database or schema prefix.
 
# FCT_ORDERS(order_id, order_date, customer_id, restaurant_id, city, cuisine,
#            payment_method, order_status, is_delivered, sales_amount, discount,
#            delivery_fee, gst, customer_rating, delivery_time_min)
# DIM_RESTAURANT(restaurant_id, restaurant_name, city, cuisine, rating, cost_for_two)
# DIM_CUSTOMER(customer_id, customer_name, age, age_segment, gender, city)
# MART_DAILY_CITY_REVENUNE(order_date, city, orders, cancel_rate, gmv, aov)
# MART_RESTAURANT_PERFORMANCE(restaurant_id, restaurant_name, city, cuisine,
#                             orders, revenue, avg_customer_rating, cancel_rate)
# MART_DELIVERY_SLA(city, order_hour, delivered_orders, p50_delivery_min, late_rate)

 
# Note: gmv means delivered revenue. Prefer the MART_ tables when they fit the question.
# """
 
# SYSTEM_PROMPT = f"""
# You are a Snowflake SQL expert. Write ONE SELECT query that answers the question.
 
# Rules:
# - SELECT queries only, never modify data.
# - Use bare table names (FCT_ORDERS, not ZOMATO.MARTS.FCT_ORDERS).
# - Add a LIMIT of 100 or less, unless the question asks for a single total.
# - Reply as JSON in this exact format: {{"sql": "your query here"}}
 
# {SCHEMA}
# """
 


# @st.cache_resource
# def get_connection():
#     return snowflake.connector.connect(
#         account=os.getenv("SNOWFLAKE_ACCOUNT"),
#         user=os.getenv("SNOWFLAKE_USER"),
#         password=os.getenv("SNOWFLAKE_PASSWORD"),
#         warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
#         database=os.getenv("SNOWFLAKE_DATABASE"),
#         schema="MARTS",
#         role = "DBT_ROLE"
#     )


# def generate_sql(question):
#     response = client.chat.completions.create(
#         model=MODEL,
#         temperature=0,
#         response_format={"type": "json_object"},
#         messages=[
#             {"role": "system", "content": SYSTEM_PROMPT},
#             {"role": "user", "content": question}
#         ]
#     )
#     answer = response.choices[0].message.content
#     sql = json.loads(answer)["sql"]

#     sql = sql.replace("ZOMATO.MARTS.", "").replace("ZOMATO.", "")
#     return sql.strip().rstrip(";")


# def is_safe(sql):
#     lowered = sql.lower()

#     if not lowered.startswith("select") and not lowered.startswith("with"):
#         return False

#     for word in FORBIDDEN_WORDS:
#         if word in lowered:
#             return False

#     return True

# def run_query(sql):
#     conn = get_connection()
#     cursor = conn.cursor()
#     return cursor.execute(sql).fetch_pandas_all()


# st.title("Chat with your Zomato Data")
# st.caption(f"Ask in English, {MODEL} writes the SQL, Snowflake runs it")

# with st.sidebar:
#     st.header("Example Questions")
#     for q in EXAMPLE_QUESTIONS:
#         st.markdown(f" - {q}")

# question = st.text_input("Enter your question here", 
#                          placeholder="e.g. Top 10 restaurants by revenune in Banglore")


# if question:
#     sql = generate_sql(question)
#     st.code(sql, language="sql")

#     if not is_safe(sql):
#         st.error("The generated SQL is not safe to run. Please modify your question.")

#     else:
#         try:
#             df = run_query(sql)
#             st.success(f"{len(df)} rows returned")
#             st.dataframe(df, hide_index=True)

#             if len(df.columns) == 2 and pd.api.types.is_numeric_dtype(df.iloc[:, 1]):
#                 st.bar_chart(df, x=df.columns[0], y=df.columns[1])

#         except Exception as e:
#             st.error(f"Error running query: {e}")




import os
import json
import re

import numpy as np
import pandas as pd
import streamlit as st
import snowflake.connector

from dotenv import load_dotenv

load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

# true  = no OpenAI API calls
# false = use OpenAI API

MOCK_AI = os.getenv("MOCK_AI", "true").lower() == "true"

MODEL = "gpt-4o-mini"


# ============================================================
# SECURITY
# ============================================================

FORBIDDEN_WORDS = [
    "drop",
    "delete",
    "truncate",
    "alter",
    "update",
    "insert",
    "create",
    "replace",
    "grant",
    "revoke"
]


# ============================================================
# EXAMPLE QUESTIONS
# ============================================================

EXAMPLE_QUESTIONS = [

    "Top 10 cities by GMV",

    "Which cuisine has the most orders?",

    "Average delivery time by city, worst first",

    "Cancel rate by payment method",

    "Top 10 restaurants by revenue",

    "What is the average order value?",

    "Which city has the highest cancellation rate?",

    "Show the number of orders by payment method",

    "What is the average delivery time?",

    "Top 10 cuisines by revenue"

]


# ============================================================
# OPENAI CLIENT
# ============================================================

if not MOCK_AI:

    from openai import OpenAI

    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )


# ============================================================
# DATABASE SCHEMA
# ============================================================

SCHEMA = """

Tables available in Snowflake.

Use bare table names without database or schema prefix.

FCT_ORDERS(
    order_id,
    order_date,
    customer_id,
    restaurant_id,
    city,
    cuisine,
    payment_method,
    order_status,
    is_delivered,
    sales_amount,
    discount,
    delivery_fee,
    gst,
    customer_rating,
    delivery_time_min
)

DIM_RESTAURANT(
    restaurant_id,
    restaurant_name,
    city,
    cuisine,
    rating,
    cost_for_two
)

DIM_CUSTOMER(
    customer_id,
    customer_name,
    age,
    age_segment,
    gender,
    city
)

MART_DAILY_CITY_REVENUNE(
    order_date,
    city,
    orders,
    cancel_rate,
    gmv,
    aov
)

MART_RESTAURANT_PERFORMANCE(
    restaurant_id,
    restaurant_name,
    city,
    cuisine,
    orders,
    revenue,
    avg_customer_rating,
    cancel_rate
)

MART_DELIVERY_SLA(
    city,
    order_hour,
    delivered_orders,
    p50_delivery_min,
    late_rate
)

Note:

gmv means delivered revenue.

Prefer MART_ tables when they fit the question.

"""


# ============================================================
# OPENAI SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = f"""

You are a Snowflake SQL expert.

Write ONE SELECT query that answers the question.

Rules:

- SELECT queries only.
- Never modify data.
- Use bare table names.
- Do not use database or schema prefixes.
- Add LIMIT 100 or less unless the question asks for a single total.
- Return JSON in this format:

{{"sql": "your query here"}}

{SCHEMA}

"""


# ============================================================
# SNOWFLAKE CONNECTION
# ============================================================

@st.cache_resource
def get_connection():

    return snowflake.connector.connect(

        account=os.getenv(
            "SNOWFLAKE_ACCOUNT"
        ),

        user=os.getenv(
            "SNOWFLAKE_USER"
        ),

        password=os.getenv(
            "SNOWFLAKE_PASSWORD"
        ),

        warehouse=os.getenv(
            "SNOWFLAKE_WAREHOUSE"
        ),

        database=os.getenv(
            "SNOWFLAKE_DATABASE"
        ),

        schema="MARTS",

        role="DBT_ROLE"

    )


# ============================================================
# MOCK TEXT-TO-SQL
# ============================================================

def mock_generate_sql(question):

    """
    Generates SQL locally without using OpenAI.

    This is designed for testing the Streamlit →
    SQL → Snowflake portion of the application.
    """

    q = question.lower().strip()


    # ========================================================
    # TOP CITIES BY GMV
    # ========================================================

    if (
        "city" in q
        and "gmv" in q
    ):

        return """

SELECT
    city,
    SUM(gmv) AS gmv
FROM MART_DAILY_CITY_REVENUNE
GROUP BY city
ORDER BY gmv DESC
LIMIT 10

""".strip()


    # ========================================================
    # CUISINE WITH MOST ORDERS
    # ========================================================

    if (
        "cuisine" in q
        and "most orders" in q
    ):

        return """

SELECT
    cuisine,
    COUNT(*) AS orders
FROM FCT_ORDERS
GROUP BY cuisine
ORDER BY orders DESC
LIMIT 10

""".strip()


    # ========================================================
    # AVERAGE DELIVERY TIME BY CITY
    # ========================================================

    if (
        "delivery time" in q
        and "city" in q
    ):

        return """

SELECT
    city,
    ROUND(AVG(delivery_time_min), 2)
        AS avg_delivery_time_min
FROM FCT_ORDERS
WHERE is_delivered = TRUE
GROUP BY city
ORDER BY avg_delivery_time_min DESC
LIMIT 100

""".strip()


    # ========================================================
    # CANCEL RATE BY PAYMENT METHOD
    # ========================================================

    if (
        "cancel" in q
        and "payment" in q
    ):

        return """

SELECT
    payment_method,
    ROUND(
        100.0 * SUM(
            CASE
                WHEN LOWER(order_status) = 'cancelled'
                THEN 1
                ELSE 0
            END
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS cancel_rate
FROM FCT_ORDERS
GROUP BY payment_method
ORDER BY cancel_rate DESC
LIMIT 100

""".strip()


    # ========================================================
    # TOP RESTAURANTS BY REVENUE
    # ========================================================

    if (
        "restaurant" in q
        and "revenue" in q
    ):

        return """

SELECT
    restaurant_name,
    city,
    revenue
FROM MART_RESTAURANT_PERFORMANCE
ORDER BY revenue DESC
LIMIT 10

""".strip()


    # ========================================================
    # AVERAGE ORDER VALUE
    # ========================================================

    if (
        "average order value" in q
        or "average order" in q
        or "aov" in q
    ):

        return """

SELECT
    ROUND(
        SUM(gmv) / NULLIF(SUM(orders), 0),
        2
    ) AS average_order_value
FROM MART_DAILY_CITY_REVENUNE

""".strip()


    # ========================================================
    # HIGHEST CANCELLATION CITY
    # ========================================================

    if (
        "cancellation" in q
        and "city" in q
    ):

        return """

SELECT
    city,
    cancel_rate
FROM MART_DAILY_CITY_REVENUNE
GROUP BY city, cancel_rate
ORDER BY cancel_rate DESC
LIMIT 10

""".strip()


    # ========================================================
    # ORDERS BY PAYMENT METHOD
    # ========================================================

    if (
        "orders" in q
        and "payment method" in q
    ):

        return """

SELECT
    payment_method,
    COUNT(*) AS orders
FROM FCT_ORDERS
GROUP BY payment_method
ORDER BY orders DESC
LIMIT 100

""".strip()


    # ========================================================
    # AVERAGE DELIVERY TIME
    # ========================================================

    if (
        "average delivery" in q
        or "avg delivery" in q
    ):

        return """

SELECT
    ROUND(
        AVG(delivery_time_min),
        2
    ) AS average_delivery_time_min
FROM FCT_ORDERS
WHERE is_delivered = TRUE

""".strip()


    # ========================================================
    # TOP CUISINES BY REVENUE
    # ========================================================

    if (
        "cuisine" in q
        and "revenue" in q
    ):

        return """

SELECT
    cuisine,
    SUM(sales_amount) AS revenue
FROM FCT_ORDERS
GROUP BY cuisine
ORDER BY revenue DESC
LIMIT 10

""".strip()


    # ========================================================
    # ORDERS BY CITY
    # ========================================================

    if (
        "orders" in q
        and "city" in q
    ):

        return """

SELECT
    city,
    COUNT(*) AS orders
FROM FCT_ORDERS
GROUP BY city
ORDER BY orders DESC
LIMIT 100

""".strip()


    # ========================================================
    # TOTAL ORDERS
    # ========================================================

    if (
        "total orders" in q
        or q == "orders"
        or "how many orders" in q
    ):

        return """

SELECT
    COUNT(*) AS total_orders
FROM FCT_ORDERS

""".strip()


    # ========================================================
    # DEFAULT
    # ========================================================

    return None


# ============================================================
# REAL OPENAI TEXT-TO-SQL
# ============================================================

def openai_generate_sql(question):

    response = client.chat.completions.create(

        model=MODEL,

        temperature=0,

        response_format={
            "type": "json_object"
        },

        messages=[

            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },

            {
                "role": "user",
                "content": question
            }

        ]
    )


    answer = (
        response
        .choices[0]
        .message
        .content
    )


    sql = json.loads(
        answer
    )["sql"]


    sql = sql.replace(
        "ZOMATO.MARTS.",
        ""
    )

    sql = sql.replace(
        "ZOMATO.",
        ""
    )


    return (
        sql
        .strip()
        .rstrip(";")
    )


# ============================================================
# GENERATE SQL
# ============================================================

def generate_sql(question):

    if MOCK_AI:

        return mock_generate_sql(
            question
        )

    else:

        return openai_generate_sql(
            question
        )


# ============================================================
# SQL SAFETY CHECK
# ============================================================

def is_safe(sql):

    if not sql:

        return False


    lowered = sql.lower().strip()


    # Must start with SELECT or WITH

    if not (
        lowered.startswith("select")
        or lowered.startswith("with")
    ):

        return False


    # Remove SQL comments

    lowered = re.sub(
        r"--.*",
        "",
        lowered
    )


    # Check forbidden operations

    for word in FORBIDDEN_WORDS:

        pattern = (
            r"\b"
            + re.escape(word)
            + r"\b"
        )


        if re.search(
            pattern,
            lowered
        ):

            return False


    # Prevent multiple statements

    if ";" in lowered:

        return False


    return True


# ============================================================
# RUN QUERY
# ============================================================

def run_query(sql):

    conn = get_connection()

    cursor = conn.cursor()


    try:

        result = (
            cursor
            .execute(sql)
            .fetch_pandas_all()
        )

        return result

    finally:

        cursor.close()


# ============================================================
# STREAMLIT UI
# ============================================================

st.title(
    "Chat with your Zomato Data"
)


# ------------------------------------------------------------
# MODE DISPLAY
# ------------------------------------------------------------

if MOCK_AI:

    st.warning(
        "MOCK AI MODE: "
        "OpenAI API is not being called."
    )

    st.caption(
        "Questions are mapped to predefined "
        "SQL templates for pipeline testing."
    )

else:

    st.caption(
        f"Ask in English, {MODEL} "
        "writes the SQL, Snowflake runs it."
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "Example Questions"
    )


    for q in EXAMPLE_QUESTIONS:

        st.markdown(
            f"- {q}"
        )


# ============================================================
# QUESTION INPUT
# ============================================================

question = st.text_input(

    "Enter your question here",

    placeholder=(
        "e.g. Top 10 restaurants "
        "by revenue in Bangalore"
    )
)


# ============================================================
# PROCESS QUESTION
# ============================================================

if question:

    sql = generate_sql(
        question
    )


    # --------------------------------------------------------
    # SQL NOT FOUND
    # --------------------------------------------------------

    if sql is None:

        st.warning(
            "Mock mode does not have a SQL "
            "template for this question yet."
        )

        st.info(
            "Try one of the example questions "
            "from the sidebar."
        )

        st.stop()


    # --------------------------------------------------------
    # SHOW SQL
    # --------------------------------------------------------

    st.subheader(
        "Generated SQL"
    )

    st.code(
        sql,
        language="sql"
    )


    # --------------------------------------------------------
    # SAFETY CHECK
    # --------------------------------------------------------

    if not is_safe(sql):

        st.error(
            "The generated SQL is not safe "
            "to run."
        )

        st.stop()


    # --------------------------------------------------------
    # EXECUTE SQL
    # --------------------------------------------------------

    try:

        with st.spinner(
            "Running query in Snowflake..."
        ):

            df = run_query(
                sql
            )


        st.success(
            f"{len(df)} rows returned"
        )


        # ----------------------------------------------------
        # DISPLAY RESULTS
        # ----------------------------------------------------

        st.dataframe(
            df,
            hide_index=True
        )


        # ----------------------------------------------------
        # SIMPLE CHART
        # ----------------------------------------------------

        if (
            len(df.columns) == 2
            and pd.api.types.is_numeric_dtype(
                df.iloc[:, 1]
            )
        ):

            st.subheader(
                "Visualization"
            )


            st.bar_chart(
                df,
                x=df.columns[0],
                y=df.columns[1]
            )


    except Exception as e:

        st.error(
            f"Error running query: {e}"
        )