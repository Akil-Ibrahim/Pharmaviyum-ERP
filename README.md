![Demo](https://img.shields.io/badge/Demo-Safe-green) 
![NDA](https://img.shields.io/badge/NDA-Yes-blue) 
![DB](https://img.shields.io/badge/DB-PostgreSQL-blue) 
![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-lightgrey) 
![Coverage](https://img.shields.io/badge/Coverage-95%25-brightgreen)

# Pharmavium-CRM → /ˌfɑːr.məˈviː.əm/

**Pharmavium** is a CRM platform for pharmacies, integrated with ERP systems, helping pharmacists efficiently engage with clients, manage orders, and analyze data.

**Core Purpose:** Centralize client management, streamline pharmacy operations, and provide actionable insights for better customer experience.

---

## Table of Contents
1. [Project Versions](#project-versions)
2. [MVP Demo Highlights](#mvp-demo-highlights)
3. [Tech Stack](#tech-stack-2026-light--modern)
4. [Contact](#contact)

---

## Project Versions

This repository contains two branches:

**Production (`main` / `production`)**
- Full codebase with all features, real integrations, and proprietary business logic  
- Uses **PostgreSQL production database** with real client and order data  
- Private access only  

**Demo (`demo`)**
- Safe demonstration version for evaluation or employer review  
- Uses **PostgreSQL demo database** with fake/test data  
- Abstracts proprietary business logic and protected under NDA  
- Maintained in private access; can be shared **with author’s permission**  
- Periodically synchronized from production to reflect current system architecture  

---

## MVP Demo Highlights

- Core CRM interface and workflow  
- High-level system architecture  
- Abstract examples of code patterns and structure  
- RAG module functionality with demo documents  

> Note: No real client data or proprietary business logic is included.

---

## Tech Stack (2026 — Light & Modern)

**Backend:** Python 3.12, Django 5.2 LTS, Django REST Framework 3.20  
**API / RAG:** FastAPI 0.124, OpenAPI / Swagger  
**Database:** PostgreSQL 16  
**Async Tasks:** Celery 5.6, Redis 7  
**Frontend:** React 18, Tailwind CSS 3, Lucide Icons 0.268  
**DevOps:** Docker 24, Docker Compose 2.20, GitHub Actions  
**Testing:** Pytest 8, Jest 29 + React Testing Library 14  
**AI/RAG:** LangChain 1.2

---

## Contact

For a technical walkthrough or demo access, contact **[Your Name]** at your.email@example.com

---

© 2026 Pharmavium. All rights reserved.  
Unauthorized use, copying, or distribution is strictly prohibited.  
The demo version is protected under NDA and may only be shared with the author’s permission.
