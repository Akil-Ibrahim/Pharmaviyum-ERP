![Demo](https://img.shields.io/badge/Demo-Safe-green) ![NDA](https://img.shields.io/badge/NDA-Yes-blue) ![DB](https://img.shields.io/badge/DB-PostgreSQL-blue)

# Pharmavium-CRM → /ˌfɑːr.məˈviː.əm/

**Pharmavium** is a CRM platform for pharmacies, integrated with ERP systems, helping pharmacists efficiently engage with clients, manage orders, and analyze data to improve service quality.

**Core Purpose:** Centralize client management, streamline pharmacy operations, and provide actionable insights for better customer experience.

---

# Project Versions

This repository contains **two branches**:

1. **Production (`main` or `production` branch)**  
   - Full codebase with all features, real integrations, and proprietary business logic.  
   - Uses **PostgreSQL production database** with real data.  
   - **Private and not publicly accessible**.  

2. **Demo (`demo` branch)** ✅  
   - Safe demonstration version **for evaluation or employer review**.  
   - Uses **PostgreSQL demo database** with fake/test data, abstracts proprietary business logic, and is **protected under NDA**.  
   - Maintained in **private access**; can be shared **only with the author’s permission**.  
   - Periodically synchronized from production to reflect current system architecture while maintaining NDA compliance.

---

## MVP Demo Highlights

The demo version allows you to:

- Explore the core CRM interface and workflow  
- See high-level system architecture  
- Review abstract code patterns and structure  
- Interact with RAG/assistant functionality using **fake documents**  

> ⚠️ **Note:** No real client data or proprietary business logic is included.

---

## Repository Structure (Demo Overview)
/backend ├─ manage.py ├─ requirements.txt └─ /pharmavium ├─ settings/ │   ├─ base.py        # shared settings for all environments │   ├─ prod.py        # production PostgreSQL database, real integrations │   └─ demo.py        # demo PostgreSQL database with fake data, NDA compliance /frontend            # React + Tailwind frontend /apps/rag_fastapi    # FastAPI RAG module (demo documents only) /tests               # Unit and integration tests /docs                # Documentation and demo guides


> Production branch includes all apps, real data, and integrations not included in demo.

---

© 2026 Pharmavium. All rights reserved.  
Unauthorized use, copying, or distribution is strictly prohibited.

---

## Contact

For a **technical walkthrough or demo access**, contact **[Your Name]** at your.email@example.com
