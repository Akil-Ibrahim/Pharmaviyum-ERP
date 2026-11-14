#!/bin/bash
# =============================================================================
# PharmaViyum CRM - OWASP ZAP Penetration Testing Script
# =============================================================================
# This script runs OWASP ZAP (Zed Attack Proxy) against the PharmaViyum API
# to identify security vulnerabilities.
#
# Prerequisites:
#   - Docker installed
#   - Backend running on http://localhost:8000
#
# Usage:
#   chmod +x tests/security/zap_scan.sh
#   ./tests/security/zap_scan.sh
#
# Output:
#   - HTML report: tests/security/reports/zap_report.html
#   - JSON report: tests/security/reports/zap_report.json
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
TARGET_URL="http://backend:8000"
REPORT_DIR="tests/security/reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo -e "${GREEN}🔒 Starting OWASP ZAP Security Scan${NC}"
echo "Target: $TARGET_URL"
echo "Timestamp: $TIMESTAMP"
echo ""

# Create reports directory
mkdir -p "$REPORT_DIR"

# Check if backend is running
echo -e "${YELLOW}Checking if backend is accessible...${NC}"
if curl -f -s "$TARGET_URL/health" > /dev/null; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${RED}✗ Backend is not accessible at $TARGET_URL${NC}"
    echo "Please ensure the backend is running before starting the scan."
    exit 1
fi

# Run ZAP baseline scan
echo -e "${YELLOW}Running ZAP baseline scan...${NC}"
docker run -t \
    --network=pharmaviyum-network \
    -v "$(pwd)/$REPORT_DIR:/zap/wrk/" \
    ghcr.io/zaproxy/zaproxy:stable \
    zap-baseline.py \
    -t "$TARGET_URL" \
    -r "zap_report_${TIMESTAMP}.html" \
    -J "zap_report_${TIMESTAMP}.json" \
    -l "WARN" \
    -I

# Check exit code
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Scan completed successfully${NC}"
elif [ $EXIT_CODE -eq 1 ]; then
    echo -e "${YELLOW}⚠ Scan completed with warnings${NC}"
elif [ $EXIT_CODE -eq 2 ]; then
    echo -e "${RED}✗ Scan completed with failures${NC}"
else
    echo -e "${RED}✗ Scan failed with exit code $EXIT_CODE${NC}"
fi

echo ""
echo "Reports generated:"
echo "  - HTML: $REPORT_DIR/zap_report_${TIMESTAMP}.html"
echo "  - JSON: $REPORT_DIR/zap_report_${TIMESTAMP}.json"
echo ""

# Open HTML report if on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${YELLOW}Opening HTML report...${NC}"
    open "$REPORT_DIR/zap_report_${TIMESTAMP}.html"
fi

exit $EXIT_CODE
