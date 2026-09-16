import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

const baseUrl = __ENV.BASE_URL || 'http://localhost:8000';
const token = __ENV.AUTH_TOKEN || '';
const pharmacyId = Number(__ENV.PHARMACY_ID || 1);
const patientId = Number(__ENV.PATIENT_ID || 1);
const productId = Number(__ENV.PRODUCT_ID || 1);
const orderId = Number(__ENV.ORDER_ID || 1);
const inventoryId = Number(__ENV.INVENTORY_ID || 1);

const aiLatency = new Trend('ai_query_latency', true);

// Stage 1 business model:
// 100 pharmacies, ~120 customer visits/day/pharmacy, with ~2-4 staff active
// per pharmacy during busy periods. The default peak is 200 active CRM users;
// increase PEAK_VUS to 400 for the upper-bound scenario.
const peakVus = Number(__ENV.PEAK_VUS || 200);

export const options = {
  scenarios: {
    pharmacy_workload: {
      executor: 'ramping-vus',
      exec: 'pharmacyWorkload',
      startVUs: 5,
      stages: [
        { duration: '1m', target: Math.ceil(peakVus * 0.25) },
        { duration: '2m', target: Math.ceil(peakVus * 0.5) },
        { duration: '3m', target: peakVus },
        { duration: '2m', target: Math.ceil(peakVus * 0.5) },
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '30s',
    },
    ai_query: {
      executor: 'constant-vus',
      exec: 'aiQuery',
      vus: Number(__ENV.AI_VUS || 10),
      duration: __ENV.AI_DURATION || '7m',
      startTime: '2m',
      gracefulStop: '30s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<1000', 'p(99)<2000'],
    ai_query_latency: ['p(95)<15000'],
  },
};

function headers() {
  return token
    ? { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
    : { 'Content-Type': 'application/json' };
}

function get(path, endpoint) {
  const response = http.get(`${baseUrl}${path}`, {
    headers: headers(),
    tags: { endpoint },
  });
  check(response, { [`${endpoint} is successful`]: (r) => r.status === 200 });
  return response;
}

export function pharmacyWorkload() {
  // Weighted approximation of real pharmacy staff activity.
  // Writes are intentionally excluded from the baseline: the test must not
  // create unbounded patients/orders/ERP events in the target database.
  const roll = Math.random() * 100;

  if (roll < 30) {
    get('/api/v1/products/?limit=50', 'products_list');
  } else if (roll < 55) {
    get('/api/v1/patients/?page=1&page_size=50', 'patients_list');
  } else if (roll < 70) {
    get(`/api/v1/products/${productId}`, 'product_detail');
  } else if (roll < 82) {
    get(`/api/v1/patients/${patientId}`, 'patient_detail');
  } else if (roll < 90) {
    get(`/api/v1/inventory?pharmacy_id=${pharmacyId}`, 'inventory_list');
  } else if (roll < 95) {
    get(`/api/v1/orders/${orderId}`, 'order_detail');
  } else {
    get('/api/v1/pharmacies', 'pharmacies_list');
  }

  // Human think time: the CRM is not hammered continuously by every user.
  sleep(1 + Math.random() * 3);
}

export function aiQuery() {
  const payload = JSON.stringify({
    query:
      __ENV.AI_QUERY ||
      'What are the main safety considerations for common pharmacy medicines?',
    pharmacy_id: pharmacyId,
    country: __ENV.COUNTRY || 'VN',
    language: __ENV.LANGUAGE || 'vi',
    session_id: `load-test-${__VU}-${__ITER}`,
  });

  const response = http.post(`${baseUrl}/api/v1/ai/query`, payload, {
    headers: headers(),
    tags: { endpoint: 'ai_query' },
  });
  aiLatency.add(response.timings.duration);
  check(response, {
    'ai response is successful': (r) => r.status === 200,
  });
  sleep(5 + Math.random() * 5);
}
