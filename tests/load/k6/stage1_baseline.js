import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

const baseUrl = (__ENV.BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

// Keep the safety checks inside the k6 script too, so direct `k6 run` calls
// cannot silently bypass the guarded shell runner.
const normalizedBaseUrl = baseUrl.toLowerCase();
if (/prod|production|live|pharmaviyum\.onrender\.com|pharmaviyum-api\.onrender\.com/.test(normalizedBaseUrl)) {
  throw new Error(`Refusing to run load tests against a production-like target: ${baseUrl}`);
}
const isLocalTarget = /^https?:\/\/(localhost|127\.0\.0\.1|0\.0\.0\.0)(:[0-9]+)?(\/|$)/i.test(baseUrl);
if (!isLocalTarget && (__ENV.ALLOW_REMOTE_TARGET !== 'true' || __ENV.LOAD_TEST_ENV !== 'staging')) {
  throw new Error('Remote targets require ALLOW_REMOTE_TARGET=true and LOAD_TEST_ENV=staging.');
}
const token = __ENV.AUTH_TOKEN || '';
const superuserToken = __ENV.SUPERUSER_TOKEN || '';
const pharmacyId = Number(__ENV.PHARMACY_ID || 0);
const patientId = Number(__ENV.PATIENT_ID || 0);
const productId = Number(__ENV.PRODUCT_ID || 0);
const orderId = Number(__ENV.ORDER_ID || 0);
const writesEnabled = __ENV.ENABLE_WRITES === 'true';
const aiEnabled = __ENV.ENABLE_AI === 'true';

const aiLatency = new Trend('ai_query_latency', true);
const transactionLatency = new Trend('synthetic_transaction_lifecycle_latency', true);
const peakVus = Number(__ENV.PEAK_VUS || 20);
const loadProfile = __ENV.LOAD_PROFILE || 'health';
const customerVisits = Number(__ENV.CUSTOMER_VISITS || 200);
const staffVus = Number(__ENV.STAFF_VUS || 6);
if (!Number.isInteger(customerVisits) || customerVisits < 1 || customerVisits > 10000) throw new Error('CUSTOMER_VISITS must be an integer from 1 to 10000.');
if (!Number.isInteger(staffVus) || staffVus < 1 || staffVus > 20) throw new Error('STAFF_VUS must be an integer from 1 to 20.');
if (!['health', 'baseline', 'pharmacy_day'].includes(loadProfile)) throw new Error('LOAD_PROFILE must be health, baseline, or pharmacy_day.');
if (loadProfile === 'health' && (writesEnabled || aiEnabled)) throw new Error('The health profile cannot enable writes or Mortarium AI.');

if (loadProfile !== 'health') {
  if (!token) throw new Error('AUTH_TOKEN is required.');
  if (!Number.isInteger(pharmacyId) || pharmacyId < 1) throw new Error('PHARMACY_ID must be a positive integer.');
}
if (writesEnabled) {
  if (__ENV.CONFIRM_SYNTHETIC_WRITES !== 'YES') throw new Error('Writes require CONFIRM_SYNTHETIC_WRITES=YES.');
  if (!superuserToken) throw new Error('Writes require a dedicated staging SUPERUSER_TOKEN.');
  if (!Number.isInteger(productId) || productId < 1) throw new Error('Writes require a valid synthetic PRODUCT_ID.');
  if (!Number.isInteger(patientId) || patientId < 1) throw new Error('Writes require a valid synthetic PATIENT_ID.');
}

const scenarios = loadProfile === 'health'
  ? {
      health_only: {
        executor: 'ramping-vus',
        exec: 'healthCheck',
        startVUs: Math.min(5, peakVus),
        stages: [
          { duration: '30s', target: Math.max(1, Math.ceil(peakVus * 0.25)) },
          { duration: '1m', target: Math.max(1, Math.ceil(peakVus * 0.5)) },
          { duration: '1m', target: peakVus },
          { duration: '30s', target: 0 },
        ],
        gracefulRampDown: '10s',
      },
    }
  : loadProfile === 'pharmacy_day'
  ? {
      pharmacy_day_customers: {
        executor: 'shared-iterations',
        exec: 'pharmacyDay',
        vus: staffVus,
        iterations: customerVisits,
        maxDuration: __ENV.PHARMACY_DAY_MAX_DURATION || '30m',
        gracefulStop: '30s',
      },
    }
  : {
      pharmacy_workload: {
        executor: 'ramping-vus',
        exec: 'pharmacyWorkload',
        startVUs: Math.min(5, peakVus),
        stages: [
          { duration: '1m', target: Math.max(1, Math.ceil(peakVus * 0.25)) },
          { duration: '2m', target: Math.max(1, Math.ceil(peakVus * 0.5)) },
          { duration: '2m', target: peakVus },
          { duration: '1m', target: 0 },
        ],
        gracefulRampDown: '30s',
      },
    };

if (aiEnabled) {
  scenarios.ai_query = {
    executor: 'constant-vus',
    exec: 'aiQuery',
    vus: Number(__ENV.AI_VUS || 1),
    duration: __ENV.AI_DURATION || '1m',
    startTime: '1m',
    gracefulStop: '30s',
  };
}

if (writesEnabled) {
  scenarios.synthetic_writes = {
    executor: 'constant-vus',
    exec: 'syntheticWrites',
    vus: Number(__ENV.WRITE_VUS || 1),
    duration: __ENV.WRITE_DURATION || '30s',
    startTime: __ENV.WRITE_START_TIME || '1m',
    gracefulStop: '30s',
  };
}

export const options = {
  scenarios,
  thresholds: {
    http_req_failed: ['rate<0.02'],
    http_req_duration: ['p(95)<1500', 'p(99)<3000'],
    ...(writesEnabled ? { synthetic_transaction_lifecycle_latency: ['p(95)<2000'] } : {}),
    ...(aiEnabled ? { ai_query_latency: ['p(95)<20000'] } : {}),
  },
};

export function healthCheck() {
  const response = http.get(`${baseUrl}/health`, { tags: { endpoint: 'health' } });
  check(response, {
    'health endpoint returns 200': (r) => r.status === 200,
    'health response is valid JSON': (r) => {
      try { return typeof r.json() === 'object' && r.json() !== null; } catch (_) { return false; }
    },
  });
  sleep(0.5);
}

function headers(useSuperuser = false) {
  const bearer = useSuperuser ? superuserToken : token;
  return { Authorization: `Bearer ${bearer}`, 'Content-Type': 'application/json' };
}

function get(path, endpoint, useSuperuser = false) {
  const response = http.get(`${baseUrl}${path}`, {
    headers: headers(useSuperuser),
    tags: { endpoint },
  });
  check(response, { [`${endpoint} returns 200`]: (r) => r.status === 200 });
  return response;
}

function post(path, payload, endpoint, useSuperuser = false, expectedStatus = 201) {
  const response = http.post(`${baseUrl}${path}`, JSON.stringify(payload), {
    headers: headers(useSuperuser),
    tags: { endpoint },
  });
  check(response, { [`${endpoint} returns ${expectedStatus}`]: (r) => r.status === expectedStatus });
  return response;
}

function del(path, endpoint) {
  const response = http.del(`${baseUrl}${path}`, null, {
    headers: headers(true),
    tags: { endpoint },
  });
  check(response, { [`${endpoint} returns 204`]: (r) => r.status === 204 });
  return response;
}

function pharmacistJourney() {
  const roll = Math.random() * 100;
  if (roll < 25) {
    get('/products/?limit=50', 'pos_product_listing');
  } else if (roll < 45) {
    get('/products/search?q=par&limit=20', 'pos_product_search');
  } else if (roll < 60) {
    get('/drug-catalog/search?q=para&limit=8', 'drug_reference_search');
  } else if (roll < 75) {
    get(`/api/v1/patients/?page=1&page_size=50&pharmacy_id=${pharmacyId}`, 'patient_list');
  } else if (roll < 85 && patientId > 0) {
    get(`/api/v1/patients/${patientId}?pharmacy_id=${pharmacyId}`, 'patient_detail');
  } else if (orderId > 0) {
    get(`/orders/${orderId}?pharmacy_id=${pharmacyId}`, 'order_detail');
  } else {
    get(`/api/v1/patients/statistics?pharmacy_id=${pharmacyId}`, 'patient_statistics');
  }
}

function managerJourney() {
  const roll = Math.random() * 100;
  if (roll < 40) {
    get(`/api/v1/inventory?pharmacy_id=${pharmacyId}`, 'inventory_list');
  } else if (roll < 55) {
    get('/api/v1/dashboard/summary', 'dashboard_summary');
  } else if (roll < 70) {
    get('/api/v1/pharmacies', 'pharmacy_list');
  } else if (roll < 80) {
    get('/api/v1/inventory?low_stock=true', 'inventory_low_stock');
  } else {
    get('/products/?limit=50', 'product_catalog');
  }
}

function privilegedJourney() {
  const endpoints = [
    ['/api/v1/batches', 'batch_list'],
    ['/api/v1/prescriptions', 'prescription_list'],
    ['/api/v1/suppliers', 'supplier_list'],
    ['/api/v1/erp/integrations', 'erp_integrations'],
    ['/api/v1/sync-events', 'erp_sync_events'],
    ['/patient-purchases/', 'patient_purchase_ledger'],
  ];
  const item = endpoints[Math.floor(Math.random() * endpoints.length)];
  get(item[0], item[1], true);
}

export function pharmacyWorkload() {
  const roleRoll = Math.random() * 100;
  if (roleRoll < 70) pharmacistJourney();
  else if (roleRoll < 90) managerJourney();
  else if (superuserToken) privilegedJourney();
  else get('/api/v1/dashboard/summary', 'dashboard_summary');
  sleep(1 + Math.random() * 3);
}

// One iteration represents one synthetic customer visit. This profile models
// supported search/lookup and manager activity only; it does not fake POS,
// payment, dispensing, FEFO, procurement or receiving transactions.
export function pharmacyDay() {
  const roleRoll = Math.random() * 100;
  if (roleRoll < 85) {
    pharmacistJourney();
  } else if (roleRoll < 98) {
    managerJourney();
  } else if (superuserToken) {
    privilegedJourney();
  } else {
    get('/api/v1/dashboard/summary', 'dashboard_summary');
  }
  sleep(1 + Math.random() * 3);
}

export function aiQuery() {
  const response = http.post(`${baseUrl}/api/v1/ai/query`, JSON.stringify({
    query: __ENV.AI_QUERY,
    pharmacy_id: pharmacyId,
    country: __ENV.COUNTRY || 'VN',
    language: __ENV.LANGUAGE || 'en',
    session_id: `load-test-${__VU}-${__ITER}`,
  }), { headers: headers(), tags: { endpoint: 'ai_query' } });
  aiLatency.add(response.timings.duration);
  check(response, { 'AI query returns 200': (r) => r.status === 200 });
  sleep(5 + Math.random() * 5);
}

export function syntheticWrites() {
  const startedAt = Date.now();
  const unique = `${Date.now()}-${__VU}-${__ITER}`.replace(/\D/g, '').slice(-16);
  let inventoryId = 0;
  let createdOrderId = 0;
  let lifecycleOk = true;

  const inventory = post('/api/v1/inventory', {
    product_id: productId,
    pharmacy_id: pharmacyId,
    quantity: 10,
    reserved_quantity: 0,
    reorder_level: 2,
    lot_number: `LOAD-${unique}`,
    expires_at: '2030-12-31T00:00:00',
  }, 'write_inventory_create', true);

  if (inventory.status === 201) {
    inventoryId = Number(inventory.json('id'));
    if (!inventoryId) lifecycleOk = false;
    else {
      const cleanup = del(`/api/v1/inventory/${inventoryId}`, 'write_inventory_cleanup');
      if (cleanup.status !== 204) lifecycleOk = false;
    }
  } else {
    lifecycleOk = false;
  }

  const order = post(`/orders/?pharmacy_id=${pharmacyId}`, {
    patient_id: patientId,
    total_amount: 1,
  }, 'write_order_create', true);

  if (order.status === 201) {
    createdOrderId = Number(order.json('id'));
    if (!createdOrderId) lifecycleOk = false;
    else {
      const cancel = http.patch(
        `${baseUrl}/orders/${createdOrderId}/status?pharmacy_id=${pharmacyId}`,
        JSON.stringify({ status: 'cancelled' }),
        { headers: headers(true), tags: { endpoint: 'write_order_cancel' } },
      );
      check(cancel, { 'synthetic order cancellation returns 200': (r) => r.status === 200 });
      if (cancel.status !== 200) lifecycleOk = false;
    }
  } else {
    lifecycleOk = false;
  }

  transactionLatency.add(Date.now() - startedAt);
  check({ lifecycleOk }, { 'synthetic transaction lifecycle completed': (v) => v.lifecycleOk });
  // Avoid an uncontrolled write loop; write intensity is deliberately lower than read VU intensity.
  sleep(1 + Math.random() * 2);
}
