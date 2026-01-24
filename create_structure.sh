#!/bin/bash
# Pharmavium-CRM full project structure creation script

# Function to create directories and files
create_file() {
    dir=$1
    file=$2
    mkdir -p "$dir"
    touch "$dir/$file"
}

echo "Creating Pharmavium-CRM project structure..."

# -------------------
# Root files
# -------------------
touch README.md LICENSE CHANGELOG.md CONTRIBUTING.md CODE_OF_CONDUCT.md .env.example pyproject.toml docker-compose.yml Dockerfile.backend Dockerfile.frontend Dockerfile.nginx

# -------------------
# CI/CD
# -------------------
mkdir -p ci-cd
touch ci-cd/build.yml ci-cd/test.yml ci-cd/deploy.yml ci-cd/security_scan.yml

# -------------------
# Backend
# -------------------
mkdir -p backend/app/{api/v1,core,db/seeds,db/migrations/versions,models,schemas,services,events,tasks/tasks,middleware,metrics,utils} backend/tests/{unit,integration,e2e,factories,mock_data}

# Backend root files
touch backend/.env backend/.env.production backend/.env.demo backend/requirements.txt backend/pydantic_settings.py backend/app/main.py backend/healthcheck.py backend/audit_logs.py

# Backend API v1
touch backend/app/api/v1/{auth.py,users.py,clients.py,orders.py,products.py,erp.py,rag.py}

# Backend core
touch backend/app/core/{config.py,security.py,oauth2.py,permissions.py,tenancy.py,logging.py,cors.py,rate_limiter.py,feature_flags.py}

# Backend DB
touch backend/app/db/{base.py,session.py,repository.py,unit_of_work.py}
touch backend/app/db/seeds/{users_seed.py,clients_seed.py,products_seed.py}
touch backend/app/db/migrations/{env.py,script.py.mako}
touch backend/app/db/migrations/versions/{20260101_init.py,20260215_add_orders_table.py,20260320_update_clients.py}

# Backend models
touch backend/app/models/{user.py,client.py,order.py,product.py,audit_log.py}

# Backend schemas
touch backend/app/schemas/{user_schema.py,client_schema.py,order_schema.py}

# Backend services
touch backend/app/services/{erp_service.py,notification_service.py,analytics_service.py,rag_service.py}

# Backend events
touch backend/app/events/{startup.py,shutdown.py}

# Backend tasks
touch backend/app/tasks/{celery_app.py,worker.py}
touch backend/app/tasks/tasks/{notify_new_order.py,sync_inventory.py,analytics_event.py}

# Backend middleware
touch backend/app/middleware/{auth_middleware.py,logging_middleware.py,error_handler.py}

# Backend metrics
touch backend/app/metrics/{prometheus_client.py,routes.py}

# Backend utils
touch backend/app/utils/{exceptions.py,validators.py,pagination.py,swagger_schemas.py}

# Backend tests
touch backend/tests/conftest.py
touch backend/tests/factories/{user_factory.py,order_factory.py,client_factory.py}
touch backend/tests/mock_data/{users.json,orders.json,clients.json}
touch backend/tests/unit/{test_users.py,test_clients.py,test_products.py}
touch backend/tests/integration/{test_orders.py,test_erp_integration.py}
touch backend/tests/e2e/{test_end_to_end.py,test_rag_assistant.py}

# -------------------
# RAG
# -------------------
mkdir -p rag/{common,pipelines,services,configs,pharmacist/demo/{documents,prompts},pharmacist/prod/{documents,prompts},developer/demo/docs,developer/prod/docs,developer/prompts,tests/{unit,integration,e2e},scripts}

# RAG common
touch rag/common/{embeddings.py,llm.py,permissions.py,retrievers.py,vectorstores.py}

# RAG pipelines
touch rag/pipelines/{ingest.py,index.py,query.py,cache_layer.py}

# RAG services
touch rag/services/{rag_orchestrator.py,notification_service.py,analytics_service.py}

# RAG configs
touch rag/configs/{default.yaml,dev.yaml,prod.yaml}

# RAG pharmacist documents & prompts
touch rag/pharmacist/demo/documents/{doc1.pdf,doc2.pdf,faq.md}
touch rag/pharmacist/demo/prompts/{prompt1.txt,prompt2.txt}
touch rag/pharmacist/prod/documents/{doc1.pdf,doc2.pdf,faq.md}
touch rag/pharmacist/prod/prompts/{prompt1.txt,prompt2.txt}

# RAG developer documents & prompts
touch rag/developer/demo/docs/{api_guide.md,example_doc.md}
touch rag/developer/prod/docs/{api_guide.md,example_doc.md}
touch rag/developer/prompts/{dev_prompt1.txt,dev_prompt2.txt}

# RAG scripts
touch rag/scripts/{rebuild_index.py,ingest_docs.py,clear_cache.py}

# RAG tests
touch rag/tests/unit/{test_embeddings.py,test_retrievers.py}
touch rag/tests/integration/test_rag_orchestrator.py
touch rag/tests/e2e/test_rag_flow.py

# -------------------
# Frontend
# -------------------
mkdir -p frontend/src/{router,pages,layouts,components/{ui,table,charts,loaders},features/{auth,clients,orders,products,reports,rag},services,store,hooks,feature_flags,utils,i18n,styles,error-boundaries,assets/{images,icons},icons/{lucide,custom},types} frontend/public

# Frontend root files
touch frontend/{index.html,vite.config.ts,tsconfig.json,tsconfig.node.json,package.json,pnpm-lock.yaml,yarn.lock,.env,.env.demo,.env.production,.gitignore,.eslintrc.cjs,.prettierrc,tailwind.config.js,postcss.config.js}
touch frontend/public/{favicon.svg,robots.txt}

# Frontend main
touch frontend/src/{main.tsx,App.tsx}

# Frontend router
touch frontend/src/router/{index.tsx,routes.ts}

# Frontend pages
touch frontend/src/pages/{LoginPage.tsx,DashboardPage.tsx,ClientsPage.tsx,OrdersPage.tsx,ProductsPage.tsx,ReportsPage.tsx,RagAssistantPage.tsx}

# Frontend layouts
touch frontend/src/layouts/{AuthLayout.tsx,MainLayout.tsx}

# Frontend components
touch frontend/src/components/ui/{Button.tsx,Input.tsx,Modal.tsx}
touch frontend/src/components/table/{DataTable.tsx,TableRow.tsx}
touch frontend/src/components/charts/{BarChart.tsx,LineChart.tsx}
touch frontend/src/components/loaders/{Spinner.tsx,Skeleton.tsx}

# Frontend features
touch frontend/src/features/rag/{rag.api.ts,rag.chat.tsx,rag.store.ts,types.ts}

# Frontend services
touch frontend/src/services/{http.ts,auth.service.ts,crm.service.ts,rag.service.ts}

# Frontend store/hooks/flags/utils/types
touch frontend/src/store/index.ts
touch frontend/src/hooks/{useAuth.ts,useFeatureFlag.ts,useDebounce.ts,usePermissions.ts}
touch frontend/src/feature_flags/{flags.ts,types.ts}
touch frontend/src/utils/{constants.ts,formatters.ts,permissions.ts,env.ts}
touch frontend/src/types/{api.ts,user.ts,common.ts}

# Frontend i18n/styles/error-boundaries/assets/icons
touch frontend/src/i18n/{index.ts,en.json,de.json}
touch frontend/src/styles/{index.css,tailwind.css}
touch frontend/src/error-boundaries/ErrorBoundary.tsx
touch frontend/src/assets/images/{logo.png,banner.jpg}
touch frontend/src/assets/icons/{user.svg,order.svg,dashboard.svg}

# Frontend icons
touch frontend/src/icons/lucide/{user.svg,order.svg,dashboard.svg,settings.svg}
touch frontend/src/icons/custom/{CustomUserIcon.tsx,CustomOrderIcon.tsx,CustomDashboardIcon.tsx,CustomSettingsIcon.tsx}
touch frontend/src/icons/index.ts

# -------------------
# Mobile
# -------------------
mkdir -p mobile/react-native/screens
touch mobile/react-native/{App.tsx,package.json,tsconfig.json}
touch mobile/react-native/screens/{LoginScreen.tsx,DashboardScreen.tsx,ClientScreen.tsx}

# -------------------
# Serverless
# -------------------
mkdir -p serverless/functions
touch serverless/functions/{notify_new_order.py,sync_inventory.py,analytics_event.py}
touch serverless/README.md

# -------------------
# Nginx
# -------------------
mkdir -p nginx
touch nginx/nginx.conf

# -------------------
# Render
# -------------------
mkdir -p render
touch render/{backend.yaml,frontend.yaml,serverless.yaml}

# -------------------
# Monitoring
# -------------------
mkdir -p monitoring/{prometheus,grafana,sentry}
touch monitoring/prometheus/prometheus.yml
touch monitoring/grafana/{dashboards.json,datasource.yaml}
touch monitoring/sentry/sentry_config.yaml

# -------------------
# Security
# -------------------
mkdir -p security/penetration-tests
touch security/{threat-model.md,security-checklist.md}
touch security/penetration-tests/{test_report_202601.md,test_report_202602.md}

# -------------------
# QA
# -------------------
mkdir -p qa/{test-cases,test-plans,regression}
touch qa/test-cases/{login_tests.md,orders_tests.md}
touch qa/test-plans/{sprint1_plan.md,sprint2_plan.md}
touch qa/regression/{regression_202601.md,regression_202602.md}

# -------------------
# UX/UI
# -------------------
mkdir -p ux-ui/{wireframes,prototypes,design-system}
touch ux-ui/wireframes/{dashboard.png,clients.png}
touch ux-ui/prototypes/{dashboard.fig,login.fig}
touch ux-ui/design-system/{colors.md,typography.md}

# -------------------
# Architecture
# -------------------
mkdir -p architecture/{decision-records,diagrams}
touch architecture/{system-design.md,scalability-notes.md}
touch architecture/decision-records/{001_auth.md,002_rag.md}
touch architecture/diagrams/{architecture.png,database.png}

# -------------------
# Docs
# -------------------
mkdir -p docs/{api,onboarding,demo}
touch docs/api/endpoints.md docs/onboarding/guide.md docs/demo/demo_steps.md

# -------------------
# Scripts
# -------------------
mkdir -p scripts
touch scripts/{db_reset.py,rag_rebuild.py,serverless_deploy.py,backup.py}

echo "Pharmavium-CRM full project structure created successfully."
