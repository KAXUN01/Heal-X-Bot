#!/bin/bash
#
# Complete Critical Errors Test Script
# This script crashes services, generates critical errors, and verifies
# they appear in the "Critical Errors Only" section of the dashboard
#

set -e

echo "============================================================"
echo "🔴 CRITICAL ERRORS TEST SCRIPT"
echo "============================================================"
echo ""
echo "This script will:"
echo "  1. Crash/stop various services to generate critical errors"
echo "  2. Write CRITICAL priority logs directly to journalctl"
echo "  3. Wait for the monitor to collect logs (10-15 seconds)"
echo "  4. Verify errors appear in the Critical Errors Only section"
echo ""
echo "⚠️  WARNING: This will stop services (they can be restarted)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_URL="http://localhost:5001/api/critical-services/issues"
WAIT_TIME=15  # Wait 15 seconds for monitor to collect logs
TIMESTAMP=$(date -Is)

# Track which services we stop (so we can restart them)
STOPPED_SERVICES=()

# Function to test if API is accessible
check_api() {
    if ! curl -s "$API_URL" > /dev/null 2>&1; then
        echo -e "${RED}❌ Error: Cannot connect to API at $API_URL${NC}"
        echo "   Make sure the dashboard server is running on port 5001"
        exit 1
    fi
    echo -e "${GREEN}✅ API is accessible${NC}"
}

# Function to stop a service and generate critical error
crash_service() {
    local service_name=$1
    local test_message=$2
    
    echo ""
    echo -e "${BLUE}📝 Testing: $service_name${NC}"
    echo "   Generating critical errors..."
    
    # Try to stop the service (if it exists and is running)
    if systemctl list-units --full -a | grep -q "$service_name.service"; then
        if systemctl is-active --quiet "$service_name" 2>/dev/null; then
            echo "   → Stopping $service_name service..."
            sudo systemctl stop "$service_name" 2>/dev/null || true
            STOPPED_SERVICES+=("$service_name")
            sleep 1
            
            # Generate CRITICAL logs for this service
            logger -p 2 -t "$service_name" "CRITICAL: $service_name service has been stopped/crashed at $TIMESTAMP"
            logger -p 2 -t "$service_name" "CRITICAL: $service_name service failure - $test_message"
            
            # Also use systemd-cat
            if command -v systemd-cat &> /dev/null; then
                echo "CRITICAL: $service_name crash detected - $test_message" | systemd-cat -t "$service_name" -p "crit"
            fi
            
            echo -e "   ${GREEN}✓${NC} Stopped $service_name and generated CRITICAL logs"
        else
            echo "   → $service_name is not running, generating logs anyway..."
            logger -p 2 -t "$service_name" "CRITICAL: $service_name service failure test at $TIMESTAMP - $test_message"
            if command -v systemd-cat &> /dev/null; then
                echo "CRITICAL: $service_name failure test - $test_message" | systemd-cat -t "$service_name" -p "crit"
            fi
        fi
    else
        echo "   → $service_name service not found, generating generic logs..."
        logger -p 2 -t "$service_name" "CRITICAL: Test error for $service_name - $test_message"
        if command -v systemd-cat &> /dev/null; then
            echo "CRITICAL: Test error for $service_name - $test_message" | systemd-cat -t "$service_name" -p "crit"
        fi
    fi
}

# Function to verify errors appear in API
verify_errors() {
    local service_name=$1
    
    echo ""
    echo -e "${BLUE}🔍 Verifying errors for: $service_name${NC}"
    
    # Wait a bit for logs to be collected
    sleep 2
    
    # Check API response
    local response=$(curl -s "$API_URL")
    local service_count=$(echo "$response" | grep -o "$service_name" | wc -l || echo "0")
    local total_issues=$(echo "$response" | grep -o '"count":[0-9]*' | grep -o '[0-9]*' | head -1 || echo "0")
    
    if [ "$service_count" -gt 0 ]; then
        echo -e "   ${GREEN}✅ Found $service_count $service_name error(s) in API response${NC}"
        echo "   → Total issues in response: $total_issues"
        return 0
    else
        echo -e "   ${YELLOW}⚠️  No $service_name errors found yet (may need more time)${NC}"
        echo "   → Total issues in response: $total_issues"
        return 1
    fi
}

# Function to show API response summary
show_api_summary() {
    echo ""
    echo -e "${BLUE}📊 API Response Summary:${NC}"
    
    local response=$(curl -s "$API_URL")
    
    # Extract and display key information
    local status=$(echo "$response" | grep -o '"status":"[^"]*"' | head -1 | cut -d'"' -f4)
    local count=$(echo "$response" | grep -o '"count":[0-9]*' | grep -o '[0-9]*' | head -1)
    
    echo "   Status: $status"
    echo "   Total Issues: $count"
    
    # Show first 5 issues
    echo ""
    echo "   First 5 issues:"
    echo "$response" | grep -o '"service":"[^"]*"' | head -5 | while read -r line; do
        service=$(echo "$line" | cut -d'"' -f4)
        echo "     - $service"
    done
    
    # Check for CRITICAL severity
    local critical_count=$(echo "$response" | grep -o '"severity":"CRITICAL"' | wc -l || echo "0")
    echo ""
    echo "   CRITICAL severity issues: $critical_count"
}

# Function to restart stopped services
restart_services() {
    if [ ${#STOPPED_SERVICES[@]} -eq 0 ]; then
        return
    fi
    
    echo ""
    echo -e "${BLUE}🔄 Restarting stopped services...${NC}"
    
    for service in "${STOPPED_SERVICES[@]}"; do
        echo "   → Restarting $service..."
        sudo systemctl start "$service" 2>/dev/null || echo "     ⚠️  Could not restart $service (may not be needed)"
    done
    
    echo -e "${GREEN}✅ Services restarted${NC}"
}

# Main execution
main() {
    echo -e "${GREEN}Starting test...${NC}"
    echo ""
    
    # Check API
    check_api
    
    # Get baseline count
    echo ""
    echo -e "${BLUE}📊 Getting baseline issue count...${NC}"
    baseline_response=$(curl -s "$API_URL")
    baseline_count=$(echo "$baseline_response" | grep -o '"count":[0-9]*' | grep -o '[0-9]*' | head -1 || echo "0")
    echo "   Baseline issues: $baseline_count"
    
    # Crash various services
    echo ""
    echo -e "${YELLOW}⚠️  CRASHING SERVICES TO GENERATE CRITICAL ERRORS${NC}"
    echo "============================================================"
    
    crash_service "nginx" "Web server crash test - HTTP service unavailable"
    crash_service "docker" "Container runtime crash test - Docker daemon failure"
    crash_service "dbus" "Message bus crash test - Inter-process communication failure"
    crash_service "systemd-journald" "Logging daemon crash test - System log failure"
    
    # Also generate some generic critical errors
    echo ""
    echo -e "${BLUE}📝 Generating generic CRITICAL errors...${NC}"
    
    for i in {1..3}; do
        logger -p 2 -t "test-critical-service" "CRITICAL: Generic test error #$i at $TIMESTAMP - This MUST appear in Critical Errors Only section"
        sleep 0.2
    done
    
    if command -v systemd-cat &> /dev/null; then
        echo "CRITICAL: System-wide critical error test" | systemd-cat -t "test-system" -p "crit"
    fi
    
    echo -e "${GREEN}✓${NC} Generated additional CRITICAL logs"
    
    # Wait for monitor to collect logs
    echo ""
    echo -e "${BLUE}⏳ Waiting $WAIT_TIME seconds for monitor to collect logs...${NC}"
    echo "   (Monitor runs every 10 seconds)"
    sleep "$WAIT_TIME"
    
    # Verify errors
    echo ""
    echo "============================================================"
    echo -e "${YELLOW}🔍 VERIFICATION${NC}"
    echo "============================================================"
    
    verify_errors "nginx"
    verify_errors "docker"
    verify_errors "dbus"
    verify_errors "test-critical-service"
    
    # Show API summary
    show_api_summary
    
    # Final verification
    echo ""
    echo "============================================================"
    echo -e "${BLUE}📋 FINAL VERIFICATION${NC}"
    echo "============================================================"
    
    final_response=$(curl -s "$API_URL")
    final_count=$(echo "$final_response" | grep -o '"count":[0-9]*' | grep -o '[0-9]*' | head -1 || echo "0")
    final_critical=$(echo "$final_response" | grep -o '"severity":"CRITICAL"' | wc -l || echo "0")
    
    echo ""
    echo "   Baseline issues: $baseline_count"
    echo "   Final issues: $final_count"
    echo "   CRITICAL severity: $final_critical"
    
    if [ "$final_count" -gt "$baseline_count" ]; then
        echo ""
        echo -e "${GREEN}✅ SUCCESS: New critical errors were detected!${NC}"
        echo "   → Issues increased from $baseline_count to $final_count"
        echo ""
        echo -e "${GREEN}✅ The 'Critical Errors Only' section should now show:${NC}"
        echo "   → $final_critical CRITICAL severity issues"
        echo "   → Check your dashboard at http://localhost:5001"
    else
        echo ""
        echo -e "${YELLOW}⚠️  WARNING: No new issues detected${NC}"
        echo "   → This could mean:"
        echo "     1. Monitor hasn't collected logs yet (wait another 10 seconds)"
        echo "     2. Logs are being filtered out"
        echo "     3. Services weren't actually stopped"
        echo ""
        echo "   → Check the dashboard manually and look at server logs"
    fi
    
    # Show how to verify in dashboard
    echo ""
    echo "============================================================"
    echo -e "${BLUE}📖 HOW TO VERIFY IN DASHBOARD${NC}"
    echo "============================================================"
    echo ""
    echo "1. Open the dashboard: http://localhost:5001"
    echo "2. Scroll to 'Critical Errors Only' section"
    echo "3. You should see errors for:"
    echo "   - nginx (if installed)"
    echo "   - docker (if installed)"
    echo "   - dbus (if installed)"
    echo "   - test-critical-service"
    echo "4. All issues should have 'CRITICAL' severity"
    echo ""
    echo "To check the log file:"
    echo "   tail -n 50 ~/critical_monitor.log"
    echo "   (or /var/log/critical_monitor.log if using sudo)"
    echo ""
    
    # Restart services
    read -p "Restart stopped services? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        restart_services
    else
        echo ""
        echo "Services left stopped. You can restart them manually:"
        for service in "${STOPPED_SERVICES[@]}"; do
            echo "   sudo systemctl start $service"
        done
    fi
    
    echo ""
    echo -e "${GREEN}✅ Test complete!${NC}"
    echo ""
}

# Run main function
main

