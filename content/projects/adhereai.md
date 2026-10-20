---
title: "AdhereAI: Health App for Patients with Non-Communicable Diseases"
type: competition project
category: Professional
start: 2026-04
end: present
status: in development
tags: [Python, PostgreSQL, Pydantic, FastAPI, GDPR, data modeling]
---

AdhereAI is a health app that helps people with non-communicable diseases manage their
treatment and recovery, connecting them with doctors, pharmacists, drug stores and
ambulance services. I worked on the data engineering for data collection.

- Built Python pipelines that collect patient onboarding data, medication schedules, adherence check-ins, symptom reports and health readings into PostgreSQL.
- Designed the data model linking patients, conditions, prescriptions, adherence events, providers and referrals, with standardised drug names, dosages and units.
- Defined validation rules with Pydantic for health data, including plausible ranges for vital signs, required fields and duplicate checks.
- Applied privacy by design for health data under the GDPR, with consent tracking, pseudonymised patient IDs and role-based access.
- Built adherence metrics and prepared features for predicting which patients are likely to miss doses.
- Designed FastAPI endpoints for exchanging data with doctors, pharmacies, drug stores and ambulance services.
