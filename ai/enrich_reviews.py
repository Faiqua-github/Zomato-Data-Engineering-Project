# import os
# import json
# from xmlrpc import client
# import snowflake.connector
# from openai import OpenAI
# from dotenv import load_dotenv

# load_dotenv()

# MODEL = "gpt-4o-mini"
# SAMPLE_N = 5
# # sample size of 5 requests to avoid hitting the rate limit of OpenAI API

# TOPICS = ["Food Quality", "Delivery", "Pricing", "Services", "Packaging", "Other"]

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# SYSTEM_PROMPT = f""" 

# You classify customer reviews for a food delivery app.

# For the review you are given, return:
# - sentiment_label: positive, negative, or neutral
# - sentiment_score: a number between -1.0 and 1.0
# - topic: one of {TOPICS}
# - key_issue: a short phrase of 6 words or less that describes the main issue in the review, if any. If there is no issue, return null

# Reply as JSON in this exact format:
# {{
#     "sentiment_label": "<sentiment_label>",
#     "sentiment_score": <sentiment_score>,
#     "topic": "<topic>",
#     "key_issue": "<key_issue>"}}

#  """

# def get_snowflake_connection():
#     return snowflake.connector.connect(
#         user=os.getenv("SNOWFLAKE_USER"),
#         password=os.getenv("SNOWFLAKE_PASSWORD"),
#         account=os.getenv("SNOWFLAKE_ACCOUNT"),
#         warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
#         database=os.getenv("SNOWFLAKE_DATABASE"),
#         schema=os.getenv("SNOWFLAKE_SCHEMA")
#     )

# def create_output_table(cursor):
#     cursor.execute("CREATE SCHEMA IF NOT EXISTS ZOMATO.AI")
#     cursor.execute("""
#         CREATE TABLE IF NOT EXISTS ZOMATO.AI.REVIEW_ENRICHED (
#             REVIEW_ID STRING,
#             SENTIMENT_LABEL STRING,
#             SENTIMENT_SCORE FLOAT,
#             TOPIC STRING,
#             KEY_ISSUE STRING,
#             MODEL STRING,
#             ENRICHED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
#         )
#     """)

# def get_reviews_to_enrich(cursor):
#     cursor.execute(f"""
#         SELECT REVIEW_ID, COMMENT
#         FROM ZOMATO.RAW.REVIEWS
#         WHERE REVIEW_ID NOT IN (SELECT REVIEW_ID FROM ZOMATO.AI.REVIEW_ENRICHED)            
#         LIMIT {SAMPLE_N}
#         """)
#     return cursor.fetchall()

# def classify_review(comment):
#     response = client.chat.completions.create(
#         model=MODEL,
#         temperature=0,
#         response_format={"type": "json_object"},
#         messages=[
#             {"role": "system", "content": SYSTEM_PROMPT},
#             {"role": "user", "content": comment}
#         ]
#     )
#     answer = response.choices[0].message.content
#     return json.loads(answer)

# def save_results(cursor, results):
#     """Insert all the enriched rows into Snowflake in one go."""
#     print(f"Saving {len(results)} enriched reviews to Snowflake...")
#     cursor.executemany(
#         """
#         INSERT INTO ZOMATO.AI.REVIEW_ENRICHED
#             (review_id, sentiment_label, sentiment_score, topic, key_issue, model)
#         VALUES (%s, %s, %s, %s, %s, %s)
#         """,
#         results,
#     )
 

# def main():
#     conn = get_snowflake_connection()
#     cursor = conn.cursor()
#     create_output_table(cursor)
#     reviews = get_reviews_to_enrich(cursor)

#     if len(reviews) == 0:
#         print("No new reviews to enrich.")
#         return

#     print(f"Enriching {len(reviews)} reviews...")

#     results = []
#     for review_id, comment in reviews:
#         print(f"Classifying review {review_id}: {comment}")
#         try:
#             labels = classify_review(comment)
#             print(f"Labels for review {review_id}: {labels}")
#             results.append((
#                 review_id,
#                 labels["sentiment_label"],
#                 labels["sentiment_score"],
#                 labels["topic"],
#                 labels["key_issue"],
#                 MODEL
#             ))
#         except Exception as e:
#             print(f"Error occurred while classifying review {review_id}: {e}")

#     save_results(cursor, results)
#     print(f"Saved {len(results)} enriched reviews to Snowflake.")
#     conn.commit()
#     cursor.close()
#     conn.close()

# if __name__ == "__main__":
#     main()

# -----------------------------------------------------------------------------------------------------------------------------------







# ********************make your enrich_reviews.py work with mock AI classifications so you can continue testing the Snowflake → AI → dbt → Power BI pipeline without calling the OpenAI API.**************************

    

import os
import json
import random

import snowflake.connector
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

# Load .env file
load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

# MOCK_AI=true  -> Do NOT call OpenAI
# MOCK_AI=false -> Use OpenAI API

MOCK_AI = os.getenv("MOCK_AI", "true").lower() == "true"


SNOWFLAKE_CONFIG = {
    "account": os.getenv("SNOWFLAKE_ACCOUNT"),
    "user": os.getenv("SNOWFLAKE_USER"),
    "password": os.getenv("SNOWFLAKE_PASSWORD"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "ZOMATO_WH"),
    "database": os.getenv("SNOWFLAKE_DATABASE", "ZOMATO"),
    "schema": os.getenv("SNOWFLAKE_SCHEMA", "RAW"),
}


# ============================================================
# VALIDATE CONFIGURATION
# ============================================================

def validate_config():

    required_variables = [
        "SNOWFLAKE_ACCOUNT",
        "SNOWFLAKE_USER",
        "SNOWFLAKE_PASSWORD",
    ]

    missing_variables = []

    for variable in required_variables:
        if not os.getenv(variable):
            missing_variables.append(variable)

    if missing_variables:

        raise ValueError(
            "Missing Snowflake environment variables: "
            + ", ".join(missing_variables)
        )


# ============================================================
# MOCK AI CLASSIFICATION
# ============================================================

def mock_classify_review(review):

    """
    Mock AI classifier.

    This function replaces OpenAI while testing the pipeline.

    It analyzes keywords in the review and generates:
        - sentiment
        - category
        - confidence
    """

    text = review.lower()

    # --------------------------------------------------------
    # SENTIMENT
    # --------------------------------------------------------

    positive_words = [
        "great",
        "good",
        "excellent",
        "amazing",
        "love",
        "perfect",
        "fast",
        "fresh",
        "delicious",
        "friendly",
        "quick",
        "nice",
        "happy",
        "awesome",
        "on time",
        "tasty",
        "wonderful",
    ]

    negative_words = [
        "bad",
        "poor",
        "terrible",
        "late",
        "slow",
        "cold",
        "wrong",
        "awful",
        "horrible",
        "dirty",
        "rude",
        "missing",
        "disappointed",
        "delay",
        "worst",
        "unhappy",
    ]

    positive_score = sum(
        word in text for word in positive_words
    )

    negative_score = sum(
        word in text for word in negative_words
    )

    if positive_score > negative_score:

        sentiment = "positive"

    elif negative_score > positive_score:

        sentiment = "negative"

    else:

        sentiment = "neutral"


    # --------------------------------------------------------
    # CATEGORY
    # --------------------------------------------------------

    if any(
        word in text
        for word in [
            "delivery",
            "delivered",
            "late",
            "fast",
            "slow",
            "on time",
            "delay",
        ]
    ):

        category = "delivery"

    elif any(
        word in text
        for word in [
            "food",
            "taste",
            "delicious",
            "fresh",
            "cold",
            "tasty",
            "flavor",
        ]
    ):

        category = "food_quality"

    elif any(
        word in text
        for word in [
            "packaging",
            "package",
            "packed",
            "eco-friendly",
        ]
    ):

        category = "packaging"

    elif any(
        word in text
        for word in [
            "service",
            "staff",
            "rude",
            "friendly",
            "waiter",
        ]
    ):

        category = "service"

    elif any(
        word in text
        for word in [
            "price",
            "expensive",
            "cheap",
            "cost",
            "value",
        ]
    ):

        category = "price"

    else:

        category = "other"


    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------

    confidence = round(
        random.uniform(0.80, 0.98),
        2
    )


    return {
        "sentiment": sentiment,
        "category": category,
        "confidence": confidence,
    }


# ============================================================
# OPENAI CLASSIFICATION
# ============================================================

def classify_with_openai(review):

    """
    Real OpenAI classifier.

    This function is ONLY called when:

        MOCK_AI=false
    """

    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:

        raise ValueError(
            "OPENAI_API_KEY is not set."
        )

    client = OpenAI(
        api_key=api_key
    )


    prompt = f"""
Classify the following restaurant review.

Review:
{review}

Return ONLY valid JSON using exactly this format:

{{
    "sentiment": "positive/negative/neutral",
    "category": "delivery/food_quality/packaging/service/price/other",
    "confidence": 0.0
}}
"""


    response = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )


    result = response.output_text

    return json.loads(result)


# ============================================================
# CLASSIFICATION CONTROLLER
# ============================================================

def classify_review(review):

    if MOCK_AI:

        print("  Using MOCK AI classification...")

        return mock_classify_review(review)

    else:

        print("  Using OpenAI classification...")

        return classify_with_openai(review)


# ============================================================
# SNOWFLAKE CONNECTION
# ============================================================

def get_snowflake_connection():

    validate_config()

    print("Connecting to Snowflake...")

    conn = snowflake.connector.connect(

        account=SNOWFLAKE_CONFIG["account"],

        user=SNOWFLAKE_CONFIG["user"],

        password=SNOWFLAKE_CONFIG["password"],

        warehouse=SNOWFLAKE_CONFIG["warehouse"],

        database=SNOWFLAKE_CONFIG["database"],

        schema=SNOWFLAKE_CONFIG["schema"],
    )

    print("Snowflake connection successful.")

    return conn


# ============================================================
# GET REVIEWS FROM SNOWFLAKE
# ============================================================

def get_reviews(conn):

    cursor = conn.cursor()

    query = """
        SELECT
            REVIEW_ID,
            ORDER_ID,
            USER_ID,
            RESTAURANT_ID,
            RATING,
            COMMENT,
            REVIEW_DATE

        FROM ZOMATO.RAW.REVIEWS

        WHERE COMMENT IS NOT NULL

        ORDER BY REVIEW_DATE

        LIMIT 5
    """


    cursor.execute(query)

    reviews = cursor.fetchall()

    cursor.close()

    return reviews


# ============================================================
# CHECK EXISTING REVIEW
# ============================================================

def review_already_enriched(conn, review_id):

    cursor = conn.cursor()

    query = """
        SELECT COUNT(*)

        FROM ZOMATO.RAW.REVIEW_AI_ENRICHED

        WHERE REVIEW_ID = %s
    """


    cursor.execute(
        query,
        (review_id,)
    )


    count = cursor.fetchone()[0]

    cursor.close()

    return count > 0


# ============================================================
# SAVE AI CLASSIFICATION
# ============================================================

def save_classification(
    conn,
    review_id,
    order_id,
    user_id,
    restaurant_id,
    rating,
    comment,
    review_date,
    result,
):

    cursor = conn.cursor()

    query = """
        INSERT INTO ZOMATO.RAW.REVIEW_AI_ENRICHED
        (
            REVIEW_ID,
            ORDER_ID,
            USER_ID,
            RESTAURANT_ID,
            RATING,
            COMMENT,
            REVIEW_DATE,
            SENTIMENT,
            CATEGORY,
            CONFIDENCE
        )

        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
    """


    cursor.execute(

        query,

        (
            review_id,
            order_id,
            user_id,
            restaurant_id,
            rating,
            comment,
            review_date,
            result["sentiment"],
            result["category"],
            result["confidence"],
        )
    )


    cursor.close()


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)

    print("ZOMATO REVIEW AI ENRICHMENT")

    print("=" * 60)


    # --------------------------------------------------------
    # DISPLAY MODE
    # --------------------------------------------------------

    if MOCK_AI:

        print("MODE: MOCK AI")

        print("OpenAI API will NOT be called.")

    else:

        print("MODE: REAL OPENAI")

        print("OpenAI API will be called.")


    print()


    # --------------------------------------------------------
    # CONNECT TO SNOWFLAKE
    # --------------------------------------------------------

    conn = get_snowflake_connection()


    try:

        # ----------------------------------------------------
        # GET REVIEWS
        # ----------------------------------------------------

        reviews = get_reviews(conn)


        print(
            f"Found {len(reviews)} reviews to process."
        )

        print()


        if len(reviews) == 0:

            print(
                "No reviews found in ZOMATO.RAW.REVIEWS."
            )

            return


        # ----------------------------------------------------
        # PROCESS EACH REVIEW
        # ----------------------------------------------------

        processed = 0

        skipped = 0


        for i, review in enumerate(
            reviews,
            start=1
        ):


            (
                review_id,
                order_id,
                user_id,
                restaurant_id,
                rating,
                comment,
                review_date,
            ) = review


            print("-" * 60)

            print(
                f"Review {i}/{len(reviews)}"
            )

            print(
                f"Review ID: {review_id}"
            )

            print(
                f"Comment: {comment}"
            )


            # ------------------------------------------------
            # DUPLICATE CHECK
            # ------------------------------------------------

            if review_already_enriched(
                conn,
                review_id
            ):

                print(
                    "  Already enriched. Skipping."
                )

                skipped += 1

                continue


            # ------------------------------------------------
            # AI CLASSIFICATION
            # ------------------------------------------------

            try:

                result = classify_review(
                    comment
                )


                print(
                    f"  Sentiment: "
                    f"{result['sentiment']}"
                )

                print(
                    f"  Category: "
                    f"{result['category']}"
                )

                print(
                    f"  Confidence: "
                    f"{result['confidence']}"
                )


                # --------------------------------------------
                # SAVE TO SNOWFLAKE
                # --------------------------------------------

                save_classification(

                    conn,

                    review_id,

                    order_id,

                    user_id,

                    restaurant_id,

                    rating,

                    comment,

                    review_date,

                    result,
                )


                conn.commit()


                print(
                    "  Saved to "
                    "ZOMATO.RAW.REVIEW_AI_ENRICHED."
                )


                processed += 1


            except Exception as e:

                print(
                    f"  Error processing "
                    f"review {review_id}: {e}"
                )

                conn.rollback()


        # ----------------------------------------------------
        # SUMMARY
        # ----------------------------------------------------

        print()

        print("=" * 60)

        print("ENRICHMENT COMPLETE")

        print("=" * 60)

        print(
            f"Processed: {processed}"
        )

        print(
            f"Skipped:   {skipped}"
        )

        print(
            f"Total:     {len(reviews)}"
        )

        print("=" * 60)


    finally:

        conn.close()

        print(
            "Snowflake connection closed."
        )


# ============================================================
# RUN SCRIPT
# ============================================================

if __name__ == "__main__":

    main()