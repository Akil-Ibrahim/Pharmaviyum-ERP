#!/bin/bash
# Test authentication endpoints

BASE_URL="${BASE_URL:-http://localhost:8000}"

echo "🧪 Testing authentication endpoints..."
echo ""

# Test 1: Public signup
echo "1️⃣  Testing public signup..."
curl -s -X POST "$BASE_URL/api/v1/users/signup" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }' | head -c 200
echo ""
echo ""

# Test 2: Login
echo "2️⃣  Testing login..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/login/access-token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=test@example.com&password=testpassword123")
echo "$LOGIN_RESPONSE" | head -c 200
echo ""

# Extract token
TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# Test 3: Get current user
echo ""
echo "3️⃣  Testing /users/me..."
curl -s -X GET "$BASE_URL/api/v1/users/me" \
    -H "Authorization: Bearer $TOKEN" | head -c 200
echo ""

# Test 4: Test token
echo ""
echo "4️⃣  Testing /login/test-token..."
curl -s -X POST "$BASE_URL/api/v1/login/test-token" \
    -H "Authorization: Bearer $TOKEN" | head -c 200
echo ""

# Test 5: Password recovery (enumeration protection)
echo ""
echo "5️⃣  Testing password recovery (should return same message)..."
curl -s -X POST "$BASE_URL/api/v1/password-recovery/nonexistent@example.com" | head -c 200
echo ""
echo ""

echo "✅ Tests complete!"
