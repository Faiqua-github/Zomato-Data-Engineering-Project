# import os
# import numpy as np
# import pandas as pd
# import streamlit as st
# import snowflake.connector
# from openai import OpenAI
# from dotenv import load_dotenv

# load_dotenv()

# EMBEDDING_MODEL = "text-embedding-3-small"
# CHAT_MODEL = "gpt-4o-mini"
# NEW_REVIEWS = 500
# TOK_K = 5
# CACHE_FILE = "review_embeddings.parquet"

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# def read_reviews_from_snowflake():
#     conn = snowflake.connector.connect(
#         account=os.getenv("SNOWFLAKE_ACCOUNT"),
#         user=os.getenv("SNOWFLAKE_USER"),
#         password=os.getenv("SNOWFLAKE_PASSWORD"),
#         warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
#         database=os.getenv("SNOWFLAKE_DATABASE"),
#         schema=os.getenv("SNOWFLAKE_SCHEMA"),
#     )

#     query = f"""
#         SELECT REVIEW_ID, CITY, RATING, COMMENT
#         FROM ZOMATO.STAGING.STG_REVIEWS
#         SAMPLE ({NEW_REVIEWS} ROWS)
#     """
#     df = conn.cursor().execute(query).fetch_pandas_all()
#     conn.close()

#     df.columns = [col.lower() for col in df.columns]
#     return df

# def embed(texts):
#     response = client.embeddings.create(
#         model=EMBEDDING_MODEL,
#         input=texts)

#     return [item.embedding for item in response.data]
    
# @st.cache_data()
# def load_reviews():
#     if os.path.exists(CACHE_FILE):
#         return pd.read_parquet(CACHE_FILE)

#     df = read_reviews_from_snowflake()
#     df['embedding'] = embed(df['comment'].tolist())
#     df.to_parquet(CACHE_FILE)
#     return df

# st.title("Chat with your Zomato Reviews")
# st.caption(f"Searching {NEW_REVIEWS} review, answering with {CHAT_MODEL} model")

# def consine_simiarity(vec_a, vec_b):
#     return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))

# def find_similar_reviews(question, df):
#     question_vector = embed([question])[0]

#     scores = []
#     for review_vector in df['embedding']:
#         scores.append(consine_simiarity(question_vector, review_vector))

#     df = df.copy()
#     df['score'] = scores
#     return df.nlargest(TOK_K, 'score')

# def ask_llm(question, top_reviews):
#     conext = ""

#     for _, row in top_reviews.iterrows():
#         conext += f" ({row['city']}, {row['rating']} stars) {row['comment']}\n"

#     system_prompt = (
#         "Answer ONLY using the customer reviews provided. "
#         "Be concise. If the reviews don't covert it, say so"
#     )

#     user_prompt = f"Questions: {question}\n\nReviews:\n{conext}"

#     response = client.chat.completions.create(
#         model=CHAT_MODEL,
#         temperature=0.2,
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": user_prompt}
#         ]
#     )
#     return response.choices[0].message.content
    
# review_df = load_reviews()

# question = st.text_input("Ask a question about your reviews:",
#                          placeholder="e.g. What are the most common complaints about delivery?")

# if question:
#     top_reviews = find_similar_reviews(question, review_df)
#     answer = ask_llm(question, top_reviews)

#     st.markdown(f"**Answer:**")
#     st.write(answer)

#     with st.expander("Reviews used to build this answer"):
#         st.dataframe(top_reviews[['city', 'rating', 'comment']], hide_index=True)


# ____________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________________

import os
import re
import numpy as np
import pandas as pd
import streamlit as st
import snowflake.connector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

MOCK_AI = os.getenv("MOCK_AI", "true").lower() == "true"

CHAT_MODEL = "gpt-4o-mini"

NEW_REVIEWS = 500

TOP_K = 5

CACHE_FILE = "review_embeddings.parquet"


# ============================================================
# OPENAI CLIENT
# ============================================================

# Only import/use OpenAI when MOCK_AI is false
if not MOCK_AI:
    from openai import OpenAI

    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )


# ============================================================
# READ REVIEWS FROM SNOWFLAKE
# ============================================================

def read_reviews_from_snowflake():

    conn = snowflake.connector.connect(

        account=os.getenv("SNOWFLAKE_ACCOUNT"),

        user=os.getenv("SNOWFLAKE_USER"),

        password=os.getenv("SNOWFLAKE_PASSWORD"),

        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),

        database=os.getenv("SNOWFLAKE_DATABASE"),

        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )


    query = f"""
        SELECT
            REVIEW_ID,
            CITY,
            RATING,
            COMMENT
        FROM ZOMATO.STAGING.STG_REVIEWS
        SAMPLE ({NEW_REVIEWS} ROWS)
    """


    cursor = conn.cursor()

    cursor.execute(query)

    df = cursor.fetch_pandas_all()

    cursor.close()

    conn.close()


    # Convert column names to lowercase

    df.columns = [
        col.lower()
        for col in df.columns
    ]


    # Remove NULL comments

    df = df[
        df["comment"].notna()
    ].copy()


    # Convert comments to string

    df["comment"] = df["comment"].astype(str)


    return df


# ============================================================
# MOCK EMBEDDING
# ============================================================

def mock_embedding(text):

    """
    Creates a simple local vector based on words.

    This is NOT a real AI embedding.

    It is only used so the RAG pipeline can be tested
    without OpenAI API calls.
    """

    text = text.lower()


    keywords = [

        "delivery",
        "food",
        "taste",
        "quality",
        "packaging",
        "service",
        "staff",
        "price",
        "expensive",
        "cheap",
        "late",
        "fast",
        "slow",
        "cold",
        "fresh",
        "restaurant",
        "order",
        "refund",
        "portion",
        "clean",
        "dirty",
        "friendly",
        "rude",
        "delay",
        "missing",
        "wrong",
        "good",
        "great",
        "excellent",
        "bad",
        "terrible",
        "amazing",
        "disappointed",
    ]


    vector = []

    for word in keywords:

        if word in text:

            vector.append(1.0)

        else:

            vector.append(0.0)


    return vector


# ============================================================
# REAL OPENAI EMBEDDING
# ============================================================

def openai_embed(texts):

    response = client.embeddings.create(

        model="text-embedding-3-small",

        input=texts
    )


    return [
        item.embedding
        for item in response.data
    ]


# ============================================================
# EMBEDDING FUNCTION
# ============================================================

def embed(texts):

    if MOCK_AI:

        return [
            mock_embedding(text)
            for text in texts
        ]

    else:

        return openai_embed(texts)


# ============================================================
# LOAD REVIEWS
# ============================================================

@st.cache_data
def load_reviews():

    # --------------------------------------------------------
    # USE CACHE IF AVAILABLE
    # --------------------------------------------------------

    if os.path.exists(CACHE_FILE):

        try:

            df = pd.read_parquet(
                CACHE_FILE
            )

            return df

        except Exception:

            pass


    # --------------------------------------------------------
    # READ FROM SNOWFLAKE
    # --------------------------------------------------------

    df = read_reviews_from_snowflake()


    # --------------------------------------------------------
    # CREATE EMBEDDINGS
    # --------------------------------------------------------

    df["embedding"] = embed(
        df["comment"].tolist()
    )


    # --------------------------------------------------------
    # SAVE CACHE
    # --------------------------------------------------------

    try:

        df.to_parquet(
            CACHE_FILE,
            index=False
        )

    except Exception as e:

        print(
            f"Could not save cache: {e}"
        )


    return df


# ============================================================
# COSINE SIMILARITY
# ============================================================

def cosine_similarity(
    vec_a,
    vec_b
):

    vec_a = np.array(
        vec_a,
        dtype=float
    )

    vec_b = np.array(
        vec_b,
        dtype=float
    )


    denominator = (

        np.linalg.norm(vec_a)
        *
        np.linalg.norm(vec_b)

    )


    if denominator == 0:

        return 0


    return np.dot(
        vec_a,
        vec_b
    ) / denominator


# ============================================================
# FIND SIMILAR REVIEWS
# ============================================================

def find_similar_reviews(
    question,
    df
):

    question_vector = embed(
        [question]
    )[0]


    scores = []


    for review_vector in df[
        "embedding"
    ]:

        score = cosine_similarity(

            question_vector,

            review_vector
        )

        scores.append(score)


    result = df.copy()

    result["score"] = scores


    return result.nlargest(
        TOP_K,
        "score"
    )


# ============================================================
# MOCK ANSWER GENERATION
# ============================================================

def mock_llm_answer(
    question,
    top_reviews
):

    question_lower = question.lower()


    # --------------------------------------------------------
    # COLLECT REVIEW TEXT
    # --------------------------------------------------------

    comments = top_reviews[
        "comment"
    ].astype(str).tolist()


    combined_text = " ".join(
        comments
    ).lower()


    # --------------------------------------------------------
    # DELIVERY
    # --------------------------------------------------------

    if any(
        word in question_lower
        for word in [
            "delivery",
            "delivered",
            "late",
            "delay",
        ]
    ):

        delivery_words = [

            "late",
            "slow",
            "delay",
            "delivery",
            "on time",
            "fast",
        ]


        matches = []

        for comment in comments:

            if any(
                word in comment.lower()
                for word in delivery_words
            ):

                matches.append(comment)


        if matches:

            return (
                f"Based on the {len(matches)} "
                f"most relevant reviews, delivery "
                f"is mainly discussed in terms of "
                f"timeliness and speed."
            )


        return (
            "The provided reviews do not contain "
            "enough information about delivery."
        )


    # --------------------------------------------------------
    # FOOD
    # --------------------------------------------------------

    if any(
        word in question_lower
        for word in [
            "food",
            "taste",
            "quality",
            "meal",
        ]
    ):

        return (
            "Based on the most relevant reviews, "
            "customers mainly discuss food taste, "
            "freshness, and overall quality."
        )


    # --------------------------------------------------------
    # PACKAGING
    # --------------------------------------------------------

    if any(
        word in question_lower
        for word in [
            "packaging",
            "package",
        ]
    ):

        return (
            "The relevant reviews mention packaging "
            "quality and how the food was packaged "
            "during delivery."
        )


    # --------------------------------------------------------
    # SERVICE
    # --------------------------------------------------------

    if any(
        word in question_lower
        for word in [
            "service",
            "staff",
            "employee",
        ]
    ):

        return (
            "The relevant reviews discuss customer "
            "service and staff experience."
        )


    # --------------------------------------------------------
    # PRICE
    # --------------------------------------------------------

    if any(
        word in question_lower
        for word in [
            "price",
            "expensive",
            "cheap",
            "cost",
        ]
    ):

        return (
            "The relevant reviews contain comments "
            "about pricing and perceived value."
        )


    # --------------------------------------------------------
    # RATING
    # --------------------------------------------------------

    if any(
        word in question_lower
        for word in [
            "rating",
            "stars",
            "score",
        ]
    ):

        average_rating = round(
            top_reviews["rating"].mean(),
            2
        )


        return (
            f"The average rating among the "
            f"{len(top_reviews)} most relevant "
            f"reviews is {average_rating} stars."
        )


    # --------------------------------------------------------
    # DEFAULT
    # --------------------------------------------------------

    return (
        f"I found {len(top_reviews)} relevant "
        f"reviews, but the mock AI cannot provide "
        f"a detailed answer to this question yet."
    )


# ============================================================
# REAL OPENAI LLM
# ============================================================

def openai_llm_answer(
    question,
    top_reviews
):

    context = ""


    for _, row in top_reviews.iterrows():

        context += (

            f"({row['city']}, "
            f"{row['rating']} stars) "
            f"{row['comment']}\n"

        )


    system_prompt = (

        "Answer ONLY using the customer "
        "reviews provided. "

        "Be concise. "

        "If the reviews don't cover the "
        "question, say so."

    )


    user_prompt = (

        f"Question: {question}\n\n"

        f"Reviews:\n{context}"

    )


    response = client.chat.completions.create(

        model=CHAT_MODEL,

        temperature=0.2,

        messages=[

            {
                "role": "system",
                "content": system_prompt
            },

            {
                "role": "user",
                "content": user_prompt
            }

        ]
    )


    return response.choices[
        0
    ].message.content


# ============================================================
# ANSWER CONTROLLER
# ============================================================

def ask_llm(
    question,
    top_reviews
):

    if MOCK_AI:

        return mock_llm_answer(
            question,
            top_reviews
        )

    else:

        return openai_llm_answer(
            question,
            top_reviews
        )


# ============================================================
# STREAMLIT UI
# ============================================================

st.title(
    "Chat with your Zomato Reviews"
)


if MOCK_AI:

    st.warning(
        "MOCK AI MODE: "
        "No OpenAI API calls are being made."
    )

else:

    st.info(
        f"Using OpenAI model: {CHAT_MODEL}"
    )


st.caption(
    f"Searching {NEW_REVIEWS} reviews"
)


# ============================================================
# LOAD REVIEWS
# ============================================================

try:

    review_df = load_reviews()

except Exception as e:

    st.error(
        f"Unable to load reviews: {e}"
    )

    st.stop()


st.success(
    f"Loaded {len(review_df)} reviews."
)


# ============================================================
# QUESTION INPUT
# ============================================================

question = st.text_input(

    "Ask a question about your reviews:",

    placeholder=(
        "e.g. What are the most common "
        "complaints about delivery?"
    )
)


# ============================================================
# PROCESS QUESTION
# ============================================================

if question:

    with st.spinner(
        "Searching reviews..."
    ):

        top_reviews = find_similar_reviews(

            question,

            review_df
        )


    with st.spinner(
        "Generating answer..."
    ):

        answer = ask_llm(

            question,

            top_reviews
        )


    st.markdown(
        "**Answer:**"
    )

    st.write(answer)


    # --------------------------------------------------------
    # SHOW REVIEWS
    # --------------------------------------------------------

    with st.expander(
        "Reviews used to build this answer"
    ):

        st.dataframe(

            top_reviews[
                [
                    "city",
                    "rating",
                    "comment",
                    "score",
                ]
            ],

            hide_index=True
        )