# Zomato End-to-End Data Engineering Pipeline

An end-to-end **Data Engineering and Analytics platform** built using **AWS, Snowflake, dbt, Apache Airflow, Python, SQL, AI/LLM technologies, and Power BI**.

The project demonstrates how raw Zomato-style restaurant, customer, order, delivery, and review data can be transformed into reliable analytical datasets through a production-style **ELT pipeline**, followed by AI-powered review analysis and business intelligence.

---

## 🚀 Project Overview

This project implements a complete modern data pipeline:

**Data Sources → AWS S3 → Snowflake RAW → dbt STAGING → dbt MART → AI/LLM → Power BI**

The pipeline is designed around the principles of:

* Cloud-based data warehousing
* ELT architecture
* Medallion-style data transformation
* Modular dbt models
* Automated workflow orchestration
* Incremental data processing
* Data quality testing
* AI-powered text enrichment
* Business intelligence and analytics

---

## 🏗️ Architecture

```text
                    ┌─────────────────────┐
                    │   Zomato Dataset    │
                    │ CSV / Source Data   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      AWS S3         │
                    │   Data Lake Layer   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      Snowflake      │
                    │                     │
                    │       RAW           │
                    │        │            │
                    │        ▼            │
                    │     STAGING         │
                    │        │            │
                    │        ▼            │
                    │       MART          │
                    └──────────┬──────────┘
                               │
                         dbt Transformations
                               │
                               ▼
                    ┌─────────────────────┐
                    │   AI / LLM Layer    │
                    │                     │
                    │ • Review Enrichment │
                    │ • Embeddings        │
                    │ • RAG               │
                    │ • Text-to-SQL       │
                    └──────────┬──────────┘
                               │
                               ▼
                         Apache Airflow
                               │
                  ┌────────────┴────────────┐
                  │ Orchestrates Pipeline   │
                  │ & dbt Transformations   │
                  └─────────────────────────┘
```

---

## 🛠️ Technology Stack

| Technology         | Purpose                                          |
| ------------------ | ------------------------------------------------ |
| **AWS S3**         | Cloud object storage / data lake                 |
| **Snowflake**      | Cloud data warehouse                             |
| **SQL**            | Data transformation and analytics                |
| **dbt**            | Data transformation, modeling and testing        |
| **Apache Airflow** | Pipeline orchestration                           |
| **Python**         | Data processing and AI integration               |
| **Docker**         | Containerized Airflow environment                |
| **LLM / AI**       | Review analysis and natural-language interaction |
| **RAG**            | Retrieval-augmented analytics                    |

---

# 📂 Project Structure

```text
Zomato-Data-Engineering-Project/
│
├── ai/
│   ├── enrich_reviews.py
│   ├── rag_chat.py
│   └── text_to_sql.py
│
├── airflow/
│   ├── Dockerfile
│   ├── docker-compose.yaml
│   └── dags/
│       └── zomato_batch.py
│
├── analyses/
│
├── macros/
│   └── generate_schema_name.sql
│
├── models/
│   ├── staging/
│   │   ├── _sources.yml
│   │   ├── _staging.yml
│   │   ├── _ai_sources.yml
│   │   ├── stg_food.sql
│   │   ├── stg_menu.sql
│   │   ├── stg_order_items.sql
│   │   ├── stg_orders.sql
│   │   ├── stg_restaurants.sql
│   │   ├── stg_reviews.sql
│   │   └── stg_users.sql
│   │
│   └── marts/
│       ├── _marts.yml
│       ├── dim_customers.sql
│       ├── dim_date.sql
│       ├── dim_food.sql
│       ├── dim_restaurants.sql
│       ├── fct_order_items.sql
│       ├── fct_orders.sql
│       ├── mart_daily_city_revenue.sql
│       ├── mart_delivery_sla.sql
│       ├── mart_restaurant_performance.sql
│       └── mart_review_insights.sql
│
├── seeds/
├── snapshots/
├── tests/
│
├── dbt_project.yml
├── README.md
└── .gitignore
```

---

# ☁️ 1. Data Ingestion — AWS S3

The pipeline begins with source datasets that are stored in **Amazon S3**.

S3 acts as the cloud-based landing/data lake layer before the data is loaded into Snowflake.

### Key concepts demonstrated

* Cloud object storage
* Data lake architecture
* File-based ingestion
* Separation of storage and compute
* Secure cloud-to-warehouse data movement

---

# ❄️ 2. Snowflake Data Warehouse

Snowflake is used as the central analytical data warehouse.

The data is organized into separate layers:

```text
RAW
 │
 ▼
STAGING
 │
 ▼
MART
```

### RAW

The RAW layer contains source data with minimal transformation.

Its purpose is to preserve the original source structure and provide a reliable ingestion layer.

### STAGING

The STAGING layer contains cleaned and standardized datasets.

Typical transformations include:

* Data type standardization
* Column renaming
* NULL handling
* Data cleaning
* Source normalization
* Basic business logic

### MART

The MART layer contains analytics-ready datasets.

The models are organized into:

**Dimensions**

* Customers
* Restaurants
* Food
* Date

**Facts**

* Orders
* Order Items

**Business Marts**

* Daily City Revenue
* Delivery SLA
* Restaurant Performance
* Review Insights

---

# 🔄 3. dbt Transformation Layer

dbt is used to transform data inside Snowflake.

The project follows a modular transformation approach:

```text
Source Data
     ↓
Staging Models
     ↓
Dimension / Fact Models
     ↓
Business Marts
```

### dbt features used

* SQL-based transformations
* Model dependencies
* Source definitions
* Schema YAML files
* Data testing
* Reusable macros
* Modular data modeling
* Custom schema generation

---

## 📊 Dimensional Modeling

The MART layer follows a dimensional modeling approach.

### Dimension Tables

```text
dim_customers
dim_date
dim_food
dim_restaurants
```

### Fact Tables

```text
fct_orders
fct_order_items
```

This structure makes the warehouse easier to consume from BI tools and supports analytical queries efficiently.

---

# 🧪 4. Data Quality & Testing

dbt tests are used to validate the transformed datasets.

Examples include:

* Primary key uniqueness
* NOT NULL checks
* Referential integrity
* Source freshness/validity
* Relationship testing

The objective is to ensure that downstream dashboards and analytics are built on trustworthy data.

---

# ⚙️ 5. Apache Airflow Orchestration

Apache Airflow is used to automate and orchestrate the pipeline.

The Airflow DAG coordinates the execution of the data workflow instead of requiring manual execution of individual steps.

High-level workflow:

```text
Start
  │
  ▼
Load / Refresh Data
  │
  ▼
Snowflake RAW
  │
  ▼
dbt STAGING
  │
  ▼
dbt MART
  │
  ▼
AI Enrichment
  │
  ▼
Analytics / BI
```

The Airflow environment is containerized using Docker.

---

# 🤖 6. AI / LLM Layer

The project extends the traditional data pipeline with an AI layer.

The `ai/` directory contains components for:

### Review Enrichment

`enrich_reviews.py`

Used to process restaurant review data and generate additional analytical information from unstructured text.

### RAG

`rag_chat.py`

Provides a foundation for retrieval-augmented interaction with the project data.

The concept is:

```text
User Question
     ↓
Retrieve Relevant Data
     ↓
  Context
     ↓
    LLM
     ↓
Natural Language Answer
```

### Text-to-SQL

`text_to_sql.py`

Provides a natural-language interface for querying analytical data.

For example:

```text
"Which cities generated the highest revenue?"
```

can be translated into an analytical SQL query and used to retrieve the required information.

---

# 🧠 AI Architecture

The AI layer can be represented as:

```text
              User Question
                    │
                    ▼
             Intent / Query
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
      RAG Search          Text-to-SQL
          │                   │
          ▼                   ▼
   Relevant Context       SQL Query
          │                   │
          └─────────┬─────────┘
                    ▼
                   LLM
                    │
                    ▼
            Natural Language
                 Answer
```

This demonstrates how modern AI capabilities can be integrated with a traditional cloud data engineering architecture.

---

# 📈 7. Business Intelligence

The curated MART tables are designed to be consumed by BI tools such as **Power BI**.

Potential dashboard areas include:

### Revenue Analytics

* Daily revenue
* City-wise revenue
* Revenue trends
* Order volume

### Restaurant Performance

* Restaurant ratings
* Order volume
* Revenue
* Delivery performance

### Delivery Analytics

* Delivery SLA
* Delayed orders
* Average delivery time
* City-level delivery performance

### Customer Analytics

* Customer activity
* Order frequency
* Customer segmentation

### Review Analytics

* Review scores
* Review trends
* AI-generated insights
* Restaurant sentiment analysis

---

# 🔁 End-to-End Pipeline

The complete workflow can be summarized as:

```text
                    SOURCE DATA
                         │
                         ▼
                      AWS S3
                         │
                         ▼
                    SNOWFLAKE
                         │
                    ┌────┴────┐
                    ▼         ▼
                   RAW     Metadata
                    │
                    ▼
                 dbt STAGING
                    │
                    ▼
             DIMENSIONS + FACTS
                    │
                    ▼
              BUSINESS MARTS
                    │
            ┌───────┴────────┐
            ▼                ▼
        AI / LLM          Power BI
            │                │
            ▼                ▼
       RAG / NLP         Dashboards
       Text-to-SQL
```

Apache Airflow orchestrates the pipeline execution.

---

# 🔐 Security

Sensitive credentials are intentionally excluded from the repository.

Examples:

```text
.env
profiles.yml
.user.yml
AWS credentials
Snowflake credentials
API keys
```

These should be configured locally or through secure environment/secret management.

---

# 🐳 Running the Project

## Prerequisites

Install/configure:

* Python
* Git
* Docker Desktop
* dbt
* Snowflake account
* AWS account
* Airflow

---

## Run Airflow

From the Airflow directory:

```bash
cd airflow
docker compose up -d
```

Check running containers:

```bash
docker compose ps
```

Airflow can then be accessed through the configured Airflow web interface.

---

## Run dbt

From the dbt project directory:

```bash
dbt debug
```

Then:

```bash
dbt deps
```

Run the transformation pipeline:

```bash
dbt build
```


