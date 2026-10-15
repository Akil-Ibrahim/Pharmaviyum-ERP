import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

const baseUrl = (__ENV.BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
const token = __ENV.AUTH_TOKEN || '';
const superuserToken = __ENV.SUPERUSER_TOKEN || '';
const pharmacyId = Number(__ENV.PHARMACY_ID || 0);
const patientId = Number(__ENV.PATIENT_ID || 0);
const productId = Number(__ENV.PRODUCT_ID || 0);
const orderId = Number(__ENV.ORDER_ID || 0);
const aiEnabled = __ENV.ENABLE_AI === 'true';
const aiVus = Number(__ENV.AI_VUS || 2);
const peakVus = Number(__ENV.PEAK_VUS || 20);
const duration = __ENV.TEST_DURATION || '6m';

if (!token) {
  throw new Error('AUTH_TOKEN is required: use a dedicated synthetic test account.');
}
if (!Number.isInteger(pharmacyId) || pharmacyId < 1) {
  throw new Error('Set PHARMACY_ID to a real, authorized synthetic/staging pharmacy ID.');
}
if (!Number.isInteger(peakVus) || peakVus < 1 || peakVus > 400) {
  throw new Error('PEAK_VUS must be an integer from 1 to 400.');
}
if (aiEnabled && (!Number.isInteger(aiVus) || aiVus < 1 || aiVus > 20)) {
  throw new Error('AI_VUS must be an integer from 1 to 20.');
}

const dashboardLatency = new Trend('dashboard_summary_latency', true);
const drugCatalogLatency = new Trend('drug_catalog_search_latency', true);
const aiLatency = new Trend('mortarium_query_latency', true);
const failedChecks = new Counter('pharmaviyum_failed_checks');

const scenarios = {
  pharmacy_erp_workload: {
    executor: 'ramping-vus',
    exec: 'pharmacyErpWorkload',
    startVUs: Math.min(2, peakVus),
    stages: [
      { duration: '1m', target: Math.max(1, Math.ceil(peakVus * 0.25)) },
      { duration: '1m', target: Math.max(1, Math.ceil(peakVus * 0.5)) },
      { duration: '2m', target: peakVus },
      { duration: '1m', target: Math.max(1, Math.ceil(peakVus * 0.5)) },
      { duration: '1m', target: 0 },
    ],
    gracefulRampDown: '30s',
  },
};

if (superuserToken) {
  scenarios.pharmacy_admin_workload = {
    executor: 'constant-vus',
    exec: 'pharmacyAdminWorkload',
    vus: Number(__ENV.ADMIN_VUS || 2),
    duration,
    startTime: '30s',
    gracefulStop: '30s',
  };
}

if (aiEnabled) {
  scenarios.mortarium_ai_workload = {
    executor: 'constant-vus',
    exec: 'mortariumAiWorkload',
    vus: aiVus,
    duration: __ENV.AI_DURATION || '3m',
    startTime: '1m',
    gracefulStop: '30s',
  };
}

export const options = {
  scenarios,
  thresholds: {
    http_req_failed: ['rate<0.02'],
    http_req_duration: ['p(95)<1500', 'p(99)<3000'],
    dashboard_summary_latency: ['p(95)<1500'],
    drug_catalog_search_latency: ['p(95)<1000'],
    ...(aiEnabled ? { mortarium_query_latency: ['p(95)<20000'] } : {}),
  },
};

function headers(useSuperuser = false) {
  const activeToken = useSuperuser ? superuserToken : token;
  return {
    Authorization: `Bearer ${activeToken}`,
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };
}

function read(path, endpoint, options = {}) {
  const response = http.get(`${baseUrl}${path}`, {
    headers: headers(options.superuser === true),
    tags: { endpoint, workload: options.workload || 'pharmacy_erp' },
    timeout: options.timeout || '30s',
  });
  const passed = check(response, {
    [`${endpoint} returns HTTP 200`]: (r) => r.status === 200,
  });
  if (!passed) failedChecks.add(1, { endpoint });
  if (options.trend) options.trend.add(response.timings.duration);
  return response;
}

export function setup() {
  const health = http.get(`${baseUrl}/health`, { tags: { endpoint: 'health' } });
  if (health.status !== 200) {
    throw new Error(`Health preflight failed with HTTP ${health.status}; target=${baseUrl}`);
  }
  return { startedAt: new Date().toISOString() };
}

function pharmacistJourney() {
  // POS support today is represented by real product/catalog lookup APIs.
  // There is no dedicated checkout transaction API in the current API router,
  // so this test deliberately does not invent or simulate a checkout endpoint.
  const roll = Math.random() * 100;

  if (roll < 24) {
    read('/products/?limit=50', 'pos_product_listing');
  } else if (roll < 44) {
    const term = encodeURIComponent(__ENV.PRODUCT_SEARCH_TERM || 'paracetamol');
    read(`/products/search?q=${term}&limit=20`, 'pos_product_search');
  } else if (roll < 60) {
    const term = encodeURIComponent(__ENV.DRUG_CATALOG_TERM || 'amoxicillin');
    read(
      `/drug-catalog/search?q=${term}&limit=20`,
      'drug_reference_search',
      { trend: drugCatalogLatency },
    );
  } else if (roll < 73) {
    read(`/api/v1/inventory?pharmacy_id=${pharmacyId}`, 'inventory_by_pharmacy');
  } else if (roll < 85) {
    read(
      `/api/v1/patients/?page=1&page_size=50&pharmacy_id=${pharmacyId}`,
      'patient_list',
    );
  } else if (roll < 94) {
    read(
      `/api/v1/dashboard/summary?pharmacy_id=${pharmacyId}`,
      'dashboard_summary',
      { trend: dashboardLatency },
    );
  } else if (patientId > 0) {
    read(
      `/api/v1/patients/${patientId}?pharmacy_id=${pharmacyId}`,
      'patient_profile',
    );
  } else {
    read(
      `/api/v1/patients/statistics?pharmacy_id=${pharmacyId}`,
      'patient_statistics',
    );
  }
}

function managerJourney() {
  const roll = Math.random() * 100;
  if (roll < 30) {
    read(`/api/v1/inventory?pharmacy_id=${pharmacyId}&low_stock=true`, 'low_stock_monitor');
  } else if (roll < 55) {
    read(`/api/v1/dashboard/summary?pharmacy_id=${pharmacyId}`, 'dashboard_summary', {
      trend: dashboardLatency,
    });
  } else if (roll < 75) {
    read('/products/?limit=100', 'product_catalog');
  } else if (roll < 90) {
    read(`/api/v1/patients/?page=1&page_size=50&pharmacy_id=${pharmacyId}`, 'patient_list');
  } else {
    read('/api/v1/pharmacies', 'pharmacy_list');
  }
}

export function pharmacyErpWorkload() {
  const roleRoll = Math.random() * 100;
  if (roleRoll < 78) {
    pharmacistJourney();
  } else {
    managerJourney();
  }
  // Model human think time instead of issuing requests continuously.
  sleep(1 + Math.random() * 2.5);
}

export function pharmacyAdminWorkload() {
  // These endpoints are restricted to privileged users in the current API.
  const paths = [
    ['/api/v1/batches', 'batch_list'],
    ['/api/v1/prescriptions', 'prescription_list'],
    ['/api/v1/suppliers', 'supplier_list'],
    ['/api/v1/erp/integrations', 'erp_integrations'],
    ['/api/v1/sync-events', 'erp_sync_events'],
    ['/patient-purchases/?limit=50', 'dispensing_sales_ledger'],
  ];
  const [path, endpoint] = paths[Math.floor(Math.random() * paths.length)];
  read(path, endpoint, { superuser: true, workload: 'pharmacy_admin' });
  sleep(1 + Math.random() * 3);
}

export function mortariumAiWorkload() {
  const payload = JSON.stringify({
    query:
      __ENV.AI_QUERY ||
      'Summarize low-stock and near-expiry risks for this pharmacy. If live data is unavailable, say so rather than guessing.',
    pharmacy_id: pharmacyId,
    country: __ENV.COUNTRY || 'VN',
    language: __ENV.LANGUAGE || 'en',
    session_id: `load-test-${__VU}-${__ITER}`,
  });

  const response = http.post(`${baseUrl}/api/v1/ai/query`, payload, {
    headers: headers(),
    tags: { endpoint: 'mortarium_ai_query', workload: 'mortarium_ai' },
    timeout: __ENV.AI_TIMEOUT || '60s',
  });
  aiLatency.add(response.timings.duration);
  const passed = check(response, {
    'Mortarium AI returns HTTP 200': (r) => r.status === 200,
  });
  if (!passed) failedChecks.add(1, { endpoint: 'mortarium_ai_query' });
  sleep(5 + Math.random() * 5);
}
