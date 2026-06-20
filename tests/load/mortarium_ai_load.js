/**
 * =============================================================================
 * PharmaViyum CRM - Mortarium AI Load Testing with k6
 * =============================================================================
 * This script performs load testing specifically for the Mortarium AI service.
 * 
 * Prerequisites:
 *   - k6 installed (https://k6.io/docs/getting-started/installation/)
 *   - Backend running on http://localhost:8000
 * 
 * Usage:
 *   # Basic load test
 *   k6 run tests/load/mortarium_ai_load.js
 *   
 *   # With environment variables
 *   k6 run -e BASE_URL=http://localhost:8000 -e VUS=50 -e DURATION=5m tests/load/mortarium_ai_load.js
 *   
 *   # With output to InfluxDB
 *   k6 run --out influxdb=http://localhost:8086/k6 tests/load/mortarium_ai_load.js
 * =============================================================================
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend } from 'k6/metrics';
import { randomItem } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Custom metrics
const aiResponseTime = new Trend('ai_response_time');
const aiErrorRate = new Rate('ai_error_rate');

// Configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const VUS = parseInt(__ENV.VUS || '10');
const DURATION = __ENV.DURATION || '2m';

// Test options
export const options = {
    stages: [
        { duration: '30s', target: VUS / 2 },  // Ramp up to 50% VUs
        { duration: '1m', target: VUS },        // Stay at 100% VUs
        { duration: '30s', target: VUS * 1.5 }, // Spike to 150% VUs
        { duration: '1m', target: VUS },        // Back to 100% VUs
        { duration: '30s', target: 0 },         // Ramp down
    ],
    thresholds: {
        http_req_duration: ['p(95)<5000'], // 95% of requests < 5s (AI can be slow)
        ai_response_time: ['p(95)<8000'],  // AI response time < 8s
        ai_error_rate: ['rate<0.1'],       // Error rate < 10%        http_req_failed: ['rate<0.05'],    // HTTP errors < 5%
    },
};

// Sample questions for AI
const QUESTIONS = [
    'What are the top selling products this month?',
    'Show me sales statistics for last week',
    'Which clients made the most purchases?',
    'What is the total revenue for today?',
    'Show me low stock products',
    'What are the most prescribed medications?',
    'Show me customer retention metrics',
    'What is the average transaction value?',
    'Which products are expiring soon?',
    'Show me daily sales trends',
];

// Setup function - runs once before the test
export function setup() {
    console.log(`Starting Mortarium AI Load Test`);
    console.log(`Target: ${BASE_URL}`);
    console.log(`VUs: ${VUS}`);
    console.log(`Duration: ${DURATION}`);
    
    // Authenticate and get token
    const loginRes = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify({
        username: 'load_test_user',
        password: 'load_test_password',
    }), {
        headers: { 'Content-Type': 'application/json' },
    });
    
    if (loginRes.status === 200) {
        const token = loginRes.json('access_token');
        return { token };
    } else {
        console.warn('Authentication failed, running without token');
        return { token: null };
    }
}

// Default function - runs for each VU iteration
export default function (data) {
    group('Mortarium AI Queries', function () {
        const question = randomItem(QUESTIONS);
        
        const payload = JSON.stringify({
            question: question,
            context: 'pharmacy_sales',            max_tokens: 500,
        });
        
        const headers = {
            'Content-Type': 'application/json',
        };
        
        if (data.token) {
            headers['Authorization'] = `Bearer ${data.token}`;
        }
        
        const startTime = new Date();
        const res = http.post(`${BASE_URL}/api/v1/ai/query`, payload, {
            headers: headers,
            timeout: '30s', // AI can take longer
        });
        const endTime = new Date();
        
        // Record custom metrics
        aiResponseTime.add(endTime - startTime);
        aiErrorRate.add(res.status >= 400);
        
        // Checks
        check(res, {
            'AI query status is 200': (r) => r.status === 200,
            'AI response has answer': (r) => {
                try {
                    const body = r.json();
                    return body.answer !== undefined && body.answer !== null;
                } catch (e) {
                    return false;
                }
            },
            'AI response time < 10s': (r) => r.timings.duration < 10000,
        });
        
        // Think time between queries
        sleep(Math.random() * 3 + 2); // 2-5 seconds
    });
}

// Teardown function - runs once after the test
export function teardown(data) {
    console.log('Mortarium AI Load Test completed');
}
