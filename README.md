![Demo](https://img.shields.io/badge/Demo-Safe-green) ![NDA](https://img.shields.io/badge/NDA-Yes-blue) ![DB](https://img.shields.io/badge/DB-PostgreSQL-blue) ![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-lightgrey) ![Coverage](https://img.shields.io/badge/Coverage-95%25-brightgreen)

# Pharmavium-CRM → /ˌfɑːr.məˈviː.əm/

**Pharmavium** is a CRM platform for pharmacies, integrated with ERP systems, helping pharmacists efficiently engage with clients, manage orders, and analyze data to improve service quality.

**Core Purpose:** Centralize client management, streamline pharmacy operations, and provide actionable insights for better customer experience.

---

## 📌 Table of Contents
- [Project Versions](#project-versions)
- [MVP Demo Highlights](#mvp-demo-highlights)
- [Repository Structure](#repository-structure-demo-overview)
- [Tech Stack](#-tech-stack-2026--light--modern)
- [Architecture Diagram](#architecture-diagram)
- [Screenshots](#screenshots)
- [Contact](#contact)

---

# Project Versions

This repository contains **two branches**:

1. **Production (`main` / `production`)** 🛠️  
   - Full codebase with all features, real integrations, and proprietary business logic  
   - Uses **PostgreSQL production database** with real client and order data  
   - **Private access only**  

2. **Demo (`demo`)** ✅  
   - Safe demonstration version for evaluation or employer review  
   - Uses **PostgreSQL demo database** with fake/test data  
   - Abstracts proprietary business logic and **protected under NDA** 🔒  
   - Maintained in private access; can be shared **with author’s permission**  
   - Periodically synchronized from production to reflect current system architecture  

---

## MVP Demo Highlights

- 💻 Core CRM interface and workflow  
- 🏗️ High-level system architecture  
- 🔧 Abstract examples of code patterns and structure  
- 🤖 RAG module functionality with demo documents  

> ⚠️ **Note:** No real client data or proprietary business logic is included.

---

## Repository Structure (Demo Overview)

📁 backend/ 📄 manage.py 📄 requirements.txt 📁 pharmavium/ 📁 settings/ 📄 base.py       # Shared settings 📄 prod.py       # Production PostgreSQL, real integrations 📄 demo.py       # Demo PostgreSQL, fake data, NDA compliance 📁 frontend/            # React 18 + Tailwind CSS 3 + Lucide Icons 0.268 📁 apps/rag_fastapi/    # FastAPI RAG module (demo documents only) 📁 tests/               # Unit and integration tests 📁 docs/                # Documentation and demo guides 💾 demo_db/             # PostgreSQL demo database with fake data 💾 prod_db/             # PostgreSQL production database
---


---

## 🚀 Tech Stack (2026 — Light & Modern)

![Python 3.12](https://img.shields.io/badge/Python-3.12-yellow) 
![Django 5.2 LTS](https://img.shields.io/badge/Django-5.2%20LTS-blue) 
![DRF 3.20](https://img.shields.io/badge/DRF-3.20-lightgrey) 
![FastAPI 0.124](https://img.shields.io/badge/FastAPI-0.124-green) 
![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-blue) 
![Celery 5.6](https://img.shields.io/badge/Celery-5.6-orange) 
![Redis 7](https://img.shields.io/badge/Redis-7-red) 
![React 18](https://img.shields.io/badge/React-18-blue) 
![Tailwind CSS 3](https://img.shields.io/badge/Tailwind-3-lightblue) 
![Lucide Icons 0.268](https://img.shields.io/badge/Lucide%20Icons-0.268-pink) 
![Docker 24](https://img.shields.io/badge/Docker-24-blue) 
![Docker Compose 2.20](https://img.shields.io/badge/Docker%20Compose-2.20-lightblue) 
![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Yes-black) 
![Pytest 8](https://img.shields.io/badge/Pytest-8-purple) 
![Jest 29](https://img.shields.io/badge/Jest-29-red) 
![React Testing Library 14](https://img.shields.io/badge/RTL-14-green) 
![LangChain 1.2](https://img.shields.io/badge/LangChain-1.2-orange)

---


## Architecture Diagram

[Frontend React/Tailwind/Lucide Icons] │ ▼ [Django Backend / DRF] │ ▼ [FastAPI RAG Module] │ ▼ [PostgreSQL Database] │ ▼ [Celery / Redis for tasks]


---

## Screenshots

![MVP Interface Placeholder](https://via.placeholder.com/800x400?text=Pharmavium+CRM+MVP+Demo)

> Screenshots are placeholders. Actual UI in demo branch only.

---

© 2026 Pharmavium. All rights reserved.  
Unauthorized use, copying, or distribution is strictly prohibited.

---

## Contact

For a technical walkthrough or demo access, contact **[Your Name]** at your.email@example.com


