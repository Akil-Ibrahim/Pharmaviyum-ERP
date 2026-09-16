import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

const baseUrl = __ENV.BASE_URL || 'http://localhost:8000';
const token = __ENV.AUTH_TOKEN || '';
const pharmacyId = Number(__ENV.PHARMACY_ID || 1);

const aiLatency = new Trend('ai_query_latency', true);

export const options = {
  scenarios: {
    crm_read: {
      executor: 'ramping-vus',
      startVUs: 1,
      stages: [
        { duration: '30s', target: 10 },
        { duration: '1m', target: 25 },
        { duration: '2m', target: 50 },
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '30s',
    },
    ai_query: {
      executor: 'constant-vus',
      vus: Number(__ENV.AI_VUS || 2),
      duration: __ENV.AI_DURATION || '2m',
      startTime: '30s',
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

export default function () {
  const response = http.get(`${baseUrl}/health`);
  check(response, { 'health is 200': (r) => r.status === 200 });
  sleep(1);
}

export function ai_query() {
  const payload = JSON.stringify({
    query: __ENV.AI_QUERY || 'What are the main safety considerations for common pharmacy medicines?',
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
  sleep(3);
}
