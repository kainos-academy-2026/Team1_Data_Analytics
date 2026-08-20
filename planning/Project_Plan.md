%md
# NYC Taxi Data & AI Engineering Project — Simplified Project Plan

## 1. Overview
This project builds a full end-to-end Lakehouse solution using the NYC Yellow Taxi dataset.  
It covers Bronze → Silver → Gold → ML → RAG over five days, completed by a team of **3 members**.

---

## 2. Project Objectives
- Ingest raw taxi data into a Bronze table.
- Clean and refine data into a reliable Silver table.
- Produce simple analytics and KPIs using a Gold table.
- Train a small ML model and log results with MLflow.
- Implement a minimal RAG workflow using a small corpus.

---

# 3. Day-by-Day Plan (with Roles)

---

# Day 1 — Planning (All Members)
### Tasks
- Define scope and responsibilities.
- Agree dataset subset (e.g., 1 month).
- Create project plan notebook.
- Create blank notebooks for project stages.

### Deliverable
- **Project Plan Notebook** (this document)

---

# Day 2 — Ingestion & Silver Cleaning

## Person B — Bronze Ingestion Lead
### Tasks
- Load raw NYC taxi data.
- Explore schema.
- Write Bronze Delta table.
- Define ingestion assumptions.

### Deliverables
- **01_bronze_ingestion** notebook  
- Bronze Delta table  

---

## Person A — Silver Cleaning Lead
### Tasks
- Apply schema, fix datatypes.
- Handle missing and invalid values.
- Standardise timestamps.
- Produce clean Silver table.

### Deliverables
- **02_silver_cleaning** notebook  
- Silver Delta table  
- Small **Data Quality Notes** (markdown cell)

---

## Person C — Exploration & Data Dictionary
### Tasks
- Run initial data exploration.
- Validate Bronze and Silver outputs.
- Create a simple data dictionary.

### Deliverables
- **00_data_exploration** notebook  
- **Data Dictionary** (small markdown table)

---

# Day 3 — Analytics & Gold Table

## Person B — Analytics Lead
### Tasks
- Build Gold analytical table.
- Compute 1–2 KPIs (e.g., trip duration, revenue/day).
- Create a small dashboard tile or chart.

### Deliverables
- **03_gold_analytics** notebook  
- Gold table  
- KPI chart  

---

## Person C — KPI Explanation
### Tasks
- Validate KPIs.
- Write short business explanation (“Why this matters”).

### Deliverables
- KPI explanation (markdown cell in analytics notebook)

---

## Person A — Support
### Tasks
- Add derived fields to Silver if needed.
- Help validate Gold outputs.

---

# Day 4 — Machine Learning

## Person C — ML Lead
### Tasks
- Define prediction target (e.g., trip duration or tip amount).
- Train baseline and improved model.
- Log runs with MLflow.
- Register best model.

### Deliverables
- **05_ml_model** notebook  
- MLflow runs  
- Registered model  

---

## Person A — Feature Preparation
### Tasks
- Prepare ML features.
- Create clean train/test split.

### Deliverables
- **04_ml_features** notebook  

---

## Person B — Model Evaluation
### Tasks
- Compare baseline vs improved model.
- Add short interpretation.

### Deliverables
- **Short ML Summary** (markdown cell)

---

# Day 5 — RAG Workflow

## Person A — Corpus Preparation
### Tasks
- Create small text dataset (FAQs, taxi rules).
- Write corpus as Delta.

### Deliverables
- **06_rag_corpus** notebook  

---

## Person B — Embeddings Lead
### Tasks
- Generate embeddings.
- Create vector store.
- Test basic vector search.

### Deliverables
- Vector store table  

---

## Person C — RAG Demo Lead
### Tasks
- Build simple RAG notebook (retrieve + answer).
- Connect embedding → retrieval → LLM.
- Add final summary.

### Deliverables
- **07_rag_demo** notebook  

---

# 4. Essential Documentation (Only What Is Needed)

1. **Project Plan** (this notebook)  
2. **Data Dictionary** (simple table in a notebook)  
3. **Data Quality Notes** (markdown in Silver notebook)  
4. **KPI Explanation** (markdown in analytics notebook)  
5. **Short ML Summary** (markdown in ML notebook)  

These can all live *inside the relevant notebooks*, not as separate files.

---

# 5. Final Deliverables Checklist

### Required Tables
- Bronze table  
- Silver table  
- Gold table  
- Corpus table  
- Vector store table  

### Required Notebooks
- 00 Exploration  
- 01 Bronze  
- 02 Silver  
- 03 Gold  
- 04 ML Features  
- 05 ML Model  
- 06 Corpus  
- 07 RAG Demo  

### Required Documentation
- Project plan  
- Data dictionary  
- Data quality notes  
- KPI explanation  
- ML summary  