---
title: From messy sources to answers you can trust
label: "dag: how_i_work"
steps:
  - {stage: sources, name: Extract, items: [BMEcat XML, PIM exports, CSV, XLSX, SAP OData, GA4]}
  - {stage: ingest, name: Load, items: [Python, Airflow, Azure Data Factory, Pydantic contracts]}
  - {stage: model, name: Transform, items: [dbt, PySpark, Databricks, Snowflake, Great Expectations]}
  - {stage: serve, name: Store, items: [PostgreSQL, Qdrant (vector database), Neo4j (graph database), GraphQL]}
  - {stage: answer, name: AI & analytics, items: [RAG, Agno agents, LangSmith evals, Power BI, Tableau]}
---

How I work, as a pipeline: every tool in each step comes from my roles and skills.
