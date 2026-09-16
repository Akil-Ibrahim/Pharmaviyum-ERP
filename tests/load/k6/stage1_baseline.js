import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

const baseUrl = __ENV.BASE_URL || 'http://localhost:8000';
const token = __ENV.AUTH_TOKEN || '';
const pharmacyId = Number(__ENV.PHARMACY_ID || 1);
const patientId = Number(__ENV.PATIENT_ID || 1);
const productId = Number(__ENV.PRODUCT_ID || 1);
const orderId = Number(__ENV.ORDER_ID || 1);

const aiLatency = new Trend('ai_query_latency', true);

// Business model for the Stage 1 capacity baseline:
// - 100 pharmacies
// - ~120 customer visits/day/pharmacy on average
// - 1 manager + 4-6 pharmacists per pharmacy
// - ~2-4 staff actively using the system at a busy time
// - 200 active CRM users is the default peak; 400 is the upper-bound scenario
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

function pharmacistJourney() {
  // Customer needs represented in the workload:
  // OTC symptoms, prescription refills, chronic therapy, medical goods,
  // vitamins/supplements and personal-care products.
  const roll = Math.random() * 100;

  if (roll < 35) {
    get('/api/v1/products/?limit=50', 'pharmacist_product_search');
  } else if (roll < 60) {
    get('/api/v1/patients/?page=1&page_size=50', 'pharmacist_patient_search');
  } else if (roll < 75) {
    get(`/api/v1/products/${productId}`, 'pharmacist_product_detail');
  } else if (roll < 90) {
    get(`/api/v1/patients/${patientId}`, 'pharmacist_patient_profile');
  } else {
    get(`/api/v1/orders/${orderId}`, 'pharmacist_order_history');
  }
}

function managerJourney() {
  // Managers monitor stock, pharmacies and customer activity.
  const roll = Math.random() * 100;

  if (roll < 45) {
    get(`/api/v1/inventory?pharmacy_id=${pharmacyId}`, 'manager_inventory');
  } else if (roll < 70) {
    get('/api/v1/pharmacies', 'manager_pharmacies');
  } else if (roll < 85) {
    get('/api/v1/products/?limit=50', 'manager_product_catalog');
  } else {
    get('/api/v1/patients/?page=1&page_size=50', 'manager_customer_list');
  }
}

function prescriptionJourney() {
  // Prescription support is represented by the current read endpoint.
  // Detailed prescription workflows will be enabled once the production
  // prescription contract is implemented instead of using placeholder data.
  get('/api/v1/prescriptions/', 'prescription_list');
}

function erpJourney() {
  // The current ERP adapter exposes a lightweight connectivity/status check.
  // Inventory and order reads above represent the CRM-facing ERP data path.
  get('/api/v1/erp/status', 'erp_status');
}

function pharmacyWorkload() {
  // Role mix for a typical pharmacy peak:
  // ~75% pharmacists, ~15% managers, ~5% prescription-related work,
  // ~5% ERP/integration activity. This is a starting assumption and should
  // be recalibrated against measured production telemetry.
  const roleRoll = Math.random() * 100;

  if (roleRoll < 75) {
    pharmacistJourney();
  } else if (roleRoll < 90) {
    managerJourney();
  } else if (roleRoll < 95) {
    prescriptionJourney();
  } else {
    erpJourney();
  }

  // Human think time: users do not issue requests continuously.
  sleep(1 + Math.random() * 3);
}

export function aiQuery() {
  const payload = JSON.stringify({
    query:
      __ENV.AI_QUERY ||
      'Help a pharmacist compare common OTC options for a customer with mild cold symptoms, including key safety considerations.',
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
