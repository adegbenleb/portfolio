---
title: "ShopFlow: E-commerce Analytics Platform"
type: personal learning project
start: 2026-10
end: present
github: github.com/adegbenleb
tags: [Python, SQL, dbt, Airflow, PostgreSQL, Neo4j, LangGraph, Ollama, FastAPI, Docker, GitHub Actions]
---

A learning project that builds a complete analytics platform on the public Olist dataset, almost 100,000 orders from a Brazilian marketplace.

An Airflow pipeline loads raw CSV files into PostgreSQL with lineage columns, then runs dbt to build staging models and a gold star schema: order and order-item facts, customer, seller and date dimensions, and a marketing funnel mart. Around 40 dbt tests check the models, and personal data is masked in the gold layer.

Order data is also modelled as a Neo4j graph to analyse buying patterns.

A LangGraph agent running on a local LLM through Ollama answers questions about sales, delivery times and customer regions. It uses curated read-only queries, a read-only database role, allow-listed parameters, a guardrail against invented tools, and an evaluation set used to compare local models.

A FastAPI backend serves a simple web interface.
