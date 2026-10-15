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
const writesEnabled = __ENV.ENABLE_WRITES === 'true';
const aiVus = Number(__ENV.AI_VUS || 2);
const writeVus = Number(__ENV.WRITE_VUS || 2);
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
if (writesEnabled) {
  if (__ENV.CONFIRM_SYNTHETIC_WRITES !== 'YES') {
    throw new Error('Writes are opt-in. Set CONFIRM_SYNTHETIC_WRITES=YES after verifying disposable staging data.');
  }
  if (!superuserToken) {
    throw new Error('ENABLE_WRITES=true requires a dedicated staging SUPERUSER_TOKEN.');
  }
  if (!Number.isInteger(productId) || productId < 1) {
    throw new Error('ENABLE_WRITES=true requires PRODUCT_ID for an existing synthetic product.');
  }
  if (!Number.isInteger(patientId) || patientId < 1) {
    throw new Error('ENABLE_WRITES=true requires PATIENT_ID for an existing synthetic patient.');
  }
  if (!Number.isInteger(writeVus) || writeVus < 1 || writeVus > 20) {
    throw new Error('WRITE_VUS must be an integer from 1 to 20.');
  }
}

const dashboardLatency = new Trend('dashboard_summary_latency', true);
const drugCatalogLatency = new Trend('drug_catalog_search_latency', true);
const aiLatency = new Trend('mortarium_query_latency', true);
const transactionLatency = new Trend('synthetic_transaction_lifecycle_latency', true);
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

if (writesEnabled) {
  scenarios.pharmacy_transaction_workload = {
    executor: 'constant-vus',
    exec: 'pharmacyTransactionWorkload',
    vus: writeVus,
    duration: __ENV.WRITE_DURATION || '2m',
    startTime: '1m',
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
    // Keep AI provider latency separate from the interactive ERP API SLO.
    'http_req_duration{workload:pharmacy_erp}': ['p(95)<1500', 'p(99)<3000'],
    'http_req_duration{workload:pharmacy_admin}': ['p(95)<2000', 'p(99)<4000'],
    ...(writesEnabled
      ? { 'http_req_duration{workload:pharmacy_transaction}': ['p(95)<2000', 'p(99)<4000'] }
      : {}),
    dashboard_summary_latency: ['p(95)<1500'],
    drug_catalog_search_latency: ['p(95)<1000'],
    ...(writesEnabled ? { synthetic_transaction_lifecycle_latency: ['p(95)<2000'] } : {}),
    ...(aiEnabled
      ? {
          'http_req_duration{workload:mortarium_ai}': ['p(95)<20000'],
          mortarium_query_latency: ['p(95)<20000'],
        }
      : {}),
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
  const target = baseUrl.toLowerCase();
  const knownProductionTarget =
    target.includes('pharmaviyum.onrender.com') ||
    target.includes('pharmaviyum-api.onrender.com') ||
    target.includes('production') ||
    target.includes('prod.') ||
    target.includes('live.');
  if (knownProductionTarget) {
    throw new Error(`Refusing load test against production-like target: ${baseUrl}`);
  }
  const isLocal =
    target.startsWith('http://localhost') ||
    target.startsWith('http://127.0.0.1') ||
    target.startsWith('http://0.0.0.0');
  if (!isLocal && (__ENV.ALLOW_REMOTE_TARGET !== 'true' || __ENV.LOAD_TEST_ENV !== 'staging')) {
    throw new Error('Remote load tests require ALLOW_REMOTE_TARGET=true and LOAD_TEST_ENV=staging.');
  }

  const health = http.get(`${baseUrl}/health`, { tags: { endpoint: 'health' } });
  if (health.status !== 200) {
    throw new Error(`Health preflight failed with HTTP ${health.status}; target=${baseUrl}`);
  }
  return { startedAt: new Date().toISOString() };
}

function pharmacistJourney() {
  // POS support today is represented by real product/catalog lookup APIs.
  // No verified checkout/dispense API exists in the current router.
  const roll = Math.random() * 100;

  if (roll < 24) {
    read('/products/?limit=50', 'pos_product_listing');
  } else if (roll < 44) {
    const term = encodeURIComponent(__ENV.PRODUCT_SEARCH_TERM || 'paracetamol');
    read(`/products/search?q=${term}&limit=20`, 'pos_product_search');
  } else if (roll < 60) {
    const term = encodeURIComponent(__ENV.DRUG_CATALOG_TERM || 'amoxicillin');
    read(`/drug-catalog/search?q=${term}&limit=20`, 'drug_reference_search', {
      trend: drugCatalogLatency,
    });
  } else if (roll < 73) {
    const inventoryPath =
      productId > 0
        ? `/api/v1/inventory?pharmacy_id=${pharmacyId}&product_id=${productId}`
        : `/api/v1/inventory?pharmacy_id=${pharmacyId}`;
    read(inventoryPath, 'inventory_by_pharmacy');
  } else if (roll < 85) {
    read(`/api/v1/patients/?page=1&page_size=50&pharmacy_id=${pharmacyId}`, 'patient_list');
  } else if (roll < 94) {
    read(`/api/v1/dashboard/summary?pharmacy_id=${pharmacyId}`, 'dashboard_summary', {
      trend: dashboardLatency,
    });
  } else if (orderId > 0) {
    read(`/api/v1/orders/${orderId}`, 'order_detail');
  } else if (patientId > 0) {
    read(`/api/v1/patients/${patientId}?pharmacy_id=${pharmacyId}`, 'patient_profile');
  } else {
    read(`/api/v1/patients/statistics?pharmacy_id=${pharmacyId}`, 'patient_statistics');
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
  if (Math.random() * 100 < 78) pharmacistJourney();
  else managerJourney();
  sleep(1 + Math.random() * 2.5);
}

export function pharmacyAdminWorkload() {
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

export function pharmacyTransactionWorkload() {
  // Verified write API: create a uniquely named inventory lot, then delete only
  // the record returned by that successful create. Requires disposable test data.
  const lotPrefix = (__ENV.TEST_LOT_PREFIX || 'k6-synthetic').replace(/[^a-zA-Z0-9_-]/g, '').slice(0, 40);
  const lotNumber = `${lotPrefix}-${__VU}-${__ITER}-${Date.now()}`;
  const expiresAt = new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString();
  const payload = JSON.stringify({
    product_id: productId,
    pharmacy_id: pharmacyId,
    quantity: 1,
    reserved_quantity: 0,
    reorder_level: 0,
    lot_number: lotNumber,
    expires_at: expiresAt,
  });
  const started = Date.now();
  const createResponse = http.post(`${baseUrl}/api/v1/inventory`, payload, {
    headers: headers(true),
    tags: { endpoint: 'synthetic_inventory_create', workload: 'pharmacy_transaction' },
    timeout: '30s',
  });
  const createdOk = check(createResponse, {
    'synthetic inventory create returns HTTP 201': (r) => r.status === 201,
  });
  if (!createdOk) {
    failedChecks.add(1, { endpoint: 'synthetic_inventory_create' });
    transactionLatency.add(Date.now() - started);
    sleep(1 + Math.random() * 2);
    return;
  }

  let created;
  try {
    created = createResponse.json();
  } catch (_) {
    created = null;
  }
  const inventoryId = Number(created && created.id);
  if (!Number.isInteger(inventoryId) || inventoryId < 1) {
    failedChecks.add(1, { endpoint: 'synthetic_inventory_create_missing_id' });
    transactionLatency.add(Date.now() - started);
    throw new Error('Inventory create returned 201 without a usable record ID; manual staging cleanup may be required.');
  }

  const deleteResponse = http.del(`${baseUrl}/api/v1/inventory/${inventoryId}`, null, {
    headers: headers(true),
    tags: { endpoint: 'synthetic_inventory_cleanup', workload: 'pharmacy_transaction' },
    timeout: '30s',
  });
  const deletedOk = check(deleteResponse, {
    'synthetic inventory cleanup returns HTTP 204': (r) => r.status === 204,
  });
  if (!deletedOk) failedChecks.add(1, { endpoint: 'synthetic_inventory_cleanup' });
  // Also exercise the real order create -> cancel lifecycle. Canceled orders
  // remain in the database, so this workload requires a disposable staging DB.
  const orderResponse = http.post(
    `${baseUrl}/api/v1/orders/?pharmacy_id=${pharmacyId}`,
    JSON.stringify({ patient_id: patientId, total_amount: 12.34 }),
    {
      headers: headers(true),
      tags: { endpoint: 'synthetic_order_create', workload: 'pharmacy_transaction' },
      timeout: '30s',
    },
  );
  const orderCreatedOk = check(orderResponse, {
    'synthetic order create returns HTTP 201': (r) => r.status === 201,
  });
  if (!orderCreatedOk) {
    failedChecks.add(1, { endpoint: 'synthetic_order_create' });
    transactionLatency.add(Date.now() - started);
    sleep(1 + Math.random() * 2);
    return;
  }

  let order;
  try {
    order = orderResponse.json();
  } catch (_) {
    order = null;
  }
  const createdOrderId = Number(order && order.id);
  if (!Number.isInteger(createdOrderId) || createdOrderId < 1) {
    failedChecks.add(1, { endpoint: 'synthetic_order_create_missing_id' });
    transactionLatency.add(Date.now() - started);
    throw new Error('Order create returned 201 without a usable ID; manual staging cleanup may be required.');
  }

  const cancelResponse = http.patch(
    `${baseUrl}/api/v1/orders/${createdOrderId}/status?pharmacy_id=${pharmacyId}`,
    JSON.stringify({ status: 'cancelled' }),
    {
      headers: headers(true),
      tags: { endpoint: 'synthetic_order_cancel', workload: 'pharmacy_transaction' },
      timeout: '30s',
    },
  );
  const cancelledOk = check(cancelResponse, {
    'synthetic order cancellation returns HTTP 200': (r) => r.status === 200,
  });
  if (!cancelledOk) failedChecks.add(1, { endpoint: 'synthetic_order_cancel' });

  transactionLatency.add(Date.now() - started);
  sleep(1 + Math.random() * 2);
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
