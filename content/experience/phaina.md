---
title: Data Engineer
company: Phaina
location: Bielefeld, Germany
start: 2026-05
end: present
domain: product data for technical products
tags: [Python, PostgreSQL, Qdrant, Neo4j, RAG, Agno, LangSmith, GraphQL, Pydantic]
---

Phaina builds Argus, software for digital product advice on technical products.

- Built Python ingestion pipelines for more than 500,000 products and 5.9 million attribute values from 15 industrial manufacturers, distributors and retailers, mapping BMEcat XML, PIM exports, CSV and XLSX deliveries into one canonical model across PostgreSQL, Qdrant and Neo4j.
- Solved customer-specific data problems across very different product domains, including Excel-corrupted IDs and dates, internal PIM IDs used as SKUs, numeric values without units, separating parent, variant and accessory products, splitting value ranges into min and max features, and refreshing stale vector snapshots.
- Developed RAG pipelines for document ingestion, chunking, embedding refresh and Qdrant index updates, keeping knowledge bases current.
- Built and deployed AI agents and LLM workflows with Agno, with prompt engineering, context design and vector retrieval, traced and evaluated in LangSmith.
- Exposed data to AI agents and applications through GraphQL APIs, and validated incoming data with Pydantic data contracts and automated quality, consistency and freshness checks.
- Worked closely with AI engineers to align data formats, access patterns and requirements for inference and retrieval.

## Case study

- **Problem**: Product data from 15 industrial manufacturers, distributors and retailers arrived as BMEcat XML, PIM exports, CSV and XLSX, with customer-specific problems such as Excel-corrupted IDs and dates, internal PIM IDs used as SKUs and numeric values without units.
- **What I did**: Built Python ingestion pipelines that map every delivery into one canonical model across PostgreSQL, Qdrant and Neo4j, validated incoming data with Pydantic data contracts and automated quality, consistency and freshness checks, and built RAG pipelines and AI agents with Agno on top.
- **Result**: More than 500,000 products and 5.9 million attribute values in one canonical model, with knowledge bases kept current and exposed to AI agents and applications through GraphQL APIs.
