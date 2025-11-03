#!/bin/bash
# Example script demonstrating different ways to use test_pipeline_e2e.py

echo "ESG Pipeline E2E Test Examples"
echo "==============================="
echo ""

# Example 1: Quick test for development
echo "Example 1: Quick test (3 companies, 30 min timeout)"
echo "Command: python scripts/test_pipeline_e2e.py --scenario quick --force-cleanup"
echo ""

# Example 2: Standard test with specific companies
echo "Example 2: Test specific companies"
echo "Command: python scripts/test_pipeline_e2e.py --companies RELIANCE TCS INFY"
echo ""

# Example 3: Incremental testing (skip cleanup)
echo "Example 3: Incremental testing without cleanup"
echo "Command: python scripts/test_pipeline_e2e.py --scenario quick --skip-cleanup"
echo ""

# Example 4: Comprehensive test with debug logging
echo "Example 4: Comprehensive test with debug logging"
echo "Command: python scripts/test_pipeline_e2e.py --scenario comprehensive --log-level DEBUG"
echo ""

# Example 5: Full pipeline test
echo "Example 5: Full pipeline test (all companies)"
echo "Command: python scripts/test_pipeline_e2e.py --scenario full --force-cleanup"
echo ""

# Example 6: Custom output directory
echo "Example 6: Save reports to custom directory"
echo "Command: python scripts/test_pipeline_e2e.py --scenario standard --output-dir ./my_reports"
echo ""

# Example 7: CI/CD integration
echo "Example 7: CI/CD integration (no interactive prompts)"
echo "Command: python scripts/test_pipeline_e2e.py --scenario quick --force-cleanup --no-report"
echo ""

echo "To run any example, copy the command and execute it."
echo ""
echo "For more information, see scripts/E2E_TEST_README.md"
