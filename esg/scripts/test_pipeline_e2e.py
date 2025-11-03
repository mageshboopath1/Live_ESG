#!/usr/bin/env python3
"""
End-to-End Pipeline Test Execution Script

This script provides a comprehensive testing framework for the ESG pipeline.
It uses the pipeline orchestrator to execute all stages and generates detailed
test reports with timing and success metrics.

Features:
- Test with limited number of companies (e.g., 3-5)
- Option to skip cleanup for incremental testing
- Detailed logging of each stage
- Generate test report with timing and success metrics
- Support for different test scenarios
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Import pipeline orchestrator functions
from pipeline_orchestrator import (
    run_full_pipeline,
    get_queue_message_count,
    RABBITMQ_CONFIG,
    PIPELINE_CONFIG
)

# Import configuration
try:
    from pipeline_config import get_config
    USE_CENTRALIZED_CONFIG = True
except ImportError:
    USE_CENTRALIZED_CONFIG = False


# ============================================================================
# Configuration
# ============================================================================

# Test scenarios
TEST_SCENARIOS = {
    'quick': {
        'name': 'Quick Test',
        'description': 'Test with 3 companies for rapid validation',
        'limit': 3,
        'embedding_timeout': 1800,  # 30 minutes
        'extraction_timeout': 3600,  # 1 hour
    },
    'standard': {
        'name': 'Standard Test',
        'description': 'Test with 5 companies for balanced coverage',
        'limit': 5,
        'embedding_timeout': 3600,  # 1 hour
        'extraction_timeout': 7200,  # 2 hours
    },
    'comprehensive': {
        'name': 'Comprehensive Test',
        'description': 'Test with 10 companies for thorough validation',
        'limit': 10,
        'embedding_timeout': 7200,  # 2 hours
        'extraction_timeout': 14400,  # 4 hours
    },
    'full': {
        'name': 'Full Pipeline Test',
        'description': 'Test with all available companies',
        'limit': None,
        'embedding_timeout': 14400,  # 4 hours
        'extraction_timeout': 28800,  # 8 hours
    }
}

# Default test companies (known to have good data)
DEFAULT_TEST_COMPANIES = [
    'RELIANCE',
    'TCS',
    'INFY',
    'HDFCBANK',
    'ICICIBANK'
]


# ============================================================================
# Logging Setup
# ============================================================================

def setup_logging(log_level: str = 'INFO', log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
    
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger('pipeline_e2e_test')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers = []
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)  # Always log everything to file
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# ============================================================================
# Test Report Generation
# ============================================================================

class TestReport:
    """Test report generator for pipeline execution."""
    
    def __init__(self, test_name: str, scenario: str):
        """
        Initialize test report.
        
        Args:
            test_name: Name of the test
            scenario: Test scenario name
        """
        self.test_name = test_name
        self.scenario = scenario
        self.start_time = datetime.now()
        self.end_time = None
        self.pipeline_result = None
        self.pre_test_state = {}
        self.post_test_state = {}
        self.errors = []
        self.warnings = []
    
    def set_pre_test_state(self, state: Dict):
        """Record pre-test system state."""
        self.pre_test_state = state
    
    def set_post_test_state(self, state: Dict):
        """Record post-test system state."""
        self.post_test_state = state
    
    def set_pipeline_result(self, result: Dict):
        """Record pipeline execution result."""
        self.pipeline_result = result
        self.end_time = datetime.now()
    
    def add_error(self, error: str):
        """Add error message to report."""
        self.errors.append(error)
    
    def add_warning(self, warning: str):
        """Add warning message to report."""
        self.warnings.append(warning)
    
    def get_duration(self) -> float:
        """Get total test duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    def format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"
    
    def generate_summary(self) -> str:
        """Generate test summary as formatted string."""
        lines = []
        lines.append("=" * 80)
        lines.append(f"  END-TO-END PIPELINE TEST REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Test information
        lines.append(f"Test Name: {self.test_name}")
        lines.append(f"Scenario: {self.scenario}")
        lines.append(f"Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if self.end_time:
            lines.append(f"End Time: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append(f"Total Duration: {self.format_duration(self.get_duration())}")
        lines.append("")
        
        # Overall result
        if self.pipeline_result:
            success = self.pipeline_result.get('success', False)
            status_symbol = "✓" if success else "✗"
            status_text = "PASSED" if success else "FAILED"
            lines.append(f"Overall Result: {status_symbol} {status_text}")
            lines.append("")
        
        # Stage results
        if self.pipeline_result and 'stages' in self.pipeline_result:
            lines.append("Stage Results:")
            lines.append("-" * 80)
            
            stages = self.pipeline_result['stages']
            
            for stage_name, stage_result in stages.items():
                success = stage_result.get('success', False)
                symbol = "✓" if success else "✗"
                duration = stage_result.get('duration_seconds', 0)
                
                stage_line = f"  {symbol} {stage_name.capitalize()}: "
                
                if stage_name == 'cleanup':
                    minio = stage_result.get('minio', 0)
                    db_total = sum(stage_result.get('database', {}).values())
                    rabbitmq_total = sum(stage_result.get('rabbitmq', {}).values())
                    stage_line += f"{minio + db_total + rabbitmq_total} items cleaned"
                
                elif stage_name == 'ingestion':
                    stage_line += f"{self.format_duration(duration)}"
                
                elif stage_name in ['embedding', 'extraction']:
                    messages = stage_result.get('messages_processed', 0)
                    stage_line += f"{messages} messages in {self.format_duration(duration)}"
                
                elif stage_name == 'validation':
                    passed = stage_result.get('passed', 0)
                    total = stage_result.get('total', 0)
                    stage_line += f"{passed}/{total} checks passed"
                
                lines.append(stage_line)
            
            lines.append("")
        
        # Data statistics
        if self.pipeline_result and 'stages' in self.pipeline_result:
            validation = self.pipeline_result['stages'].get('validation', {})
            if validation and 'checks' in validation:
                lines.append("Data Statistics:")
                lines.append("-" * 80)
                
                checks = validation['checks']
                
                if 'embeddings_count' in checks:
                    count = checks['embeddings_count'].get('count', 0)
                    lines.append(f"  • Embeddings Created: {count:,}")
                
                if 'embedding_dimensions' in checks:
                    total = checks['embedding_dimensions'].get('total_embeddings', 0)
                    invalid = checks['embedding_dimensions'].get('invalid_dimensions', 0)
                    lines.append(f"  • Embedding Dimensions: {total:,} total, {invalid} invalid")
                
                if 'indicators_count' in checks:
                    count = checks['indicators_count'].get('count', 0)
                    reports = checks['indicators_count'].get('unique_reports', 0)
                    lines.append(f"  • Indicators Extracted: {count:,} (across {reports} reports)")
                
                if 'scores_count' in checks:
                    count = checks['scores_count'].get('count', 0)
                    lines.append(f"  • ESG Scores Calculated: {count:,}")
                
                if 'referential_integrity' in checks:
                    issues = checks['referential_integrity'].get('issues', [])
                    if issues:
                        lines.append(f"  • Referential Integrity Issues: {len(issues)}")
                        for issue in issues:
                            lines.append(f"      - {issue}")
                    else:
                        lines.append(f"  • Referential Integrity: ✓ No issues")
                
                lines.append("")
        
        # Performance metrics
        if self.pipeline_result and 'stages' in self.pipeline_result:
            lines.append("Performance Metrics:")
            lines.append("-" * 80)
            
            stages = self.pipeline_result['stages']
            
            # Embedding throughput
            if 'embedding' in stages:
                embedding = stages['embedding']
                messages = embedding.get('messages_processed', 0)
                duration = embedding.get('duration_seconds', 0)
                if duration > 0:
                    rate = messages / duration
                    lines.append(f"  • Embedding Throughput: {rate:.2f} messages/second")
            
            # Extraction throughput
            if 'extraction' in stages:
                extraction = stages['extraction']
                messages = extraction.get('messages_processed', 0)
                duration = extraction.get('duration_seconds', 0)
                if duration > 0:
                    rate = messages / duration
                    lines.append(f"  • Extraction Throughput: {rate:.2f} messages/second")
            
            # Overall throughput
            total_duration = self.pipeline_result.get('total_duration', 0)
            if total_duration > 0 and 'validation' in stages:
                validation = stages['validation']
                if 'checks' in validation and 'indicators_count' in validation['checks']:
                    reports = validation['checks']['indicators_count'].get('unique_reports', 0)
                    if reports > 0:
                        rate = reports / total_duration
                        lines.append(f"  • Overall Throughput: {rate:.4f} reports/second")
            
            lines.append("")
        
        # Errors and warnings
        if self.errors:
            lines.append("Errors:")
            lines.append("-" * 80)
            for error in self.errors:
                lines.append(f"  ✗ {error}")
            lines.append("")
        
        if self.warnings:
            lines.append("Warnings:")
            lines.append("-" * 80)
            for warning in self.warnings:
                lines.append(f"  ⚠️  {warning}")
            lines.append("")
        
        # Recommendations
        if self.pipeline_result and not self.pipeline_result.get('success', False):
            lines.append("Recommendations:")
            lines.append("-" * 80)
            
            stages = self.pipeline_result.get('stages', {})
            
            if 'embedding' in stages and not stages['embedding'].get('success', False):
                lines.append("  • Check embedding service logs for errors")
                lines.append("  • Verify Google AI API key is valid and has quota")
                lines.append("  • Consider increasing embedding timeout")
            
            if 'extraction' in stages and not stages['extraction'].get('success', False):
                lines.append("  • Check extraction service logs for errors")
                lines.append("  • Verify embeddings were created successfully")
                lines.append("  • Consider increasing extraction timeout")
            
            if 'validation' in stages and not stages['validation'].get('success', False):
                checks = stages['validation'].get('checks', {})
                if 'embedding_dimensions' in checks and not checks['embedding_dimensions'].get('success', False):
                    lines.append("  • Verify embedding service is using 3072-dimensional model")
                if 'referential_integrity' in checks and not checks['referential_integrity'].get('success', False):
                    lines.append("  • Check for data consistency issues in database")
            
            lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def save_to_file(self, filepath: str):
        """Save report to file."""
        with open(filepath, 'w') as f:
            f.write(self.generate_summary())
    
    def save_to_json(self, filepath: str):
        """Save report data as JSON."""
        data = {
            'test_name': self.test_name,
            'scenario': self.scenario,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': self.get_duration(),
            'pipeline_result': self.pipeline_result,
            'pre_test_state': self.pre_test_state,
            'post_test_state': self.post_test_state,
            'errors': self.errors,
            'warnings': self.warnings
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)


# ============================================================================
# Test Execution Functions
# ============================================================================

def get_system_state() -> Dict:
    """
    Get current system state for comparison.
    
    Returns:
        dict: System state information
    """
    state = {
        'timestamp': datetime.now().isoformat(),
        'queues': {}
    }
    
    # Get queue depths
    try:
        embedding_queue = RABBITMQ_CONFIG['embedding_queue']
        state['queues'][embedding_queue] = get_queue_message_count(embedding_queue)
    except Exception as e:
        state['queues']['embedding_error'] = str(e)
    
    try:
        extraction_queue = RABBITMQ_CONFIG['extraction_queue']
        state['queues'][extraction_queue] = get_queue_message_count(extraction_queue)
    except Exception as e:
        state['queues']['extraction_error'] = str(e)
    
    return state


def run_test(
    scenario: str = 'standard',
    companies: Optional[List[str]] = None,
    skip_cleanup: bool = False,
    force_cleanup: bool = False,
    log_level: str = 'INFO',
    output_dir: Optional[str] = None
) -> TestReport:
    """
    Run end-to-end pipeline test.
    
    Args:
        scenario: Test scenario name (quick, standard, comprehensive, full)
        companies: List of company symbols to test (overrides scenario limit)
        skip_cleanup: Skip cleanup stage
        force_cleanup: Force cleanup without confirmation
        log_level: Logging level
        output_dir: Directory for test reports
    
    Returns:
        TestReport: Test report object
    """
    # Get scenario configuration
    if scenario not in TEST_SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario}. Choose from: {', '.join(TEST_SCENARIOS.keys())}")
    
    scenario_config = TEST_SCENARIOS[scenario]
    
    # Setup logging
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        log_file = os.path.join(output_dir, f"test_{scenario}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    else:
        log_file = None
    
    logger = setup_logging(log_level, log_file)
    
    # Create test report
    test_name = f"E2E Pipeline Test - {scenario_config['name']}"
    report = TestReport(test_name, scenario)
    
    logger.info("=" * 80)
    logger.info(f"Starting {test_name}")
    logger.info(f"Description: {scenario_config['description']}")
    logger.info("=" * 80)
    
    # Record pre-test state
    logger.info("Recording pre-test system state...")
    report.set_pre_test_state(get_system_state())
    
    # Determine companies to test
    if companies:
        test_companies = companies
        limit = None
    elif scenario_config['limit']:
        test_companies = None
        limit = scenario_config['limit']
    else:
        test_companies = None
        limit = None
    
    # Log test parameters
    logger.info(f"Test Parameters:")
    if test_companies:
        logger.info(f"  Companies: {', '.join(test_companies)}")
    elif limit:
        logger.info(f"  Limit: {limit} companies")
    else:
        logger.info(f"  Limit: All companies")
    logger.info(f"  Skip Cleanup: {skip_cleanup}")
    logger.info(f"  Embedding Timeout: {scenario_config['embedding_timeout']}s")
    logger.info(f"  Extraction Timeout: {scenario_config['extraction_timeout']}s")
    logger.info("")
    
    try:
        # Run pipeline
        logger.info("Executing pipeline...")
        result = run_full_pipeline(
            companies=test_companies,
            limit=limit,
            skip_cleanup=skip_cleanup,
            force_cleanup=force_cleanup,
            embedding_timeout=scenario_config['embedding_timeout'],
            extraction_timeout=scenario_config['extraction_timeout']
        )
        
        # Record result
        report.set_pipeline_result(result)
        
        # Record post-test state
        logger.info("Recording post-test system state...")
        report.set_post_test_state(get_system_state())
        
        # Check for issues
        if not result['success']:
            report.add_error(f"Pipeline failed: {result.get('summary', 'Unknown error')}")
        
        # Check for warnings
        if 'stages' in result:
            for stage_name, stage_result in result['stages'].items():
                if not stage_result.get('success', False):
                    report.add_warning(f"{stage_name.capitalize()} stage did not complete successfully")
        
        logger.info("")
        logger.info("Test execution completed")
        
    except KeyboardInterrupt:
        logger.warning("Test interrupted by user")
        report.add_error("Test interrupted by user")
        report.end_time = datetime.now()
    
    except Exception as e:
        logger.error(f"Test failed with exception: {e}", exc_info=True)
        report.add_error(f"Test failed with exception: {e}")
        report.end_time = datetime.now()
    
    return report


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description='ESG Pipeline End-to-End Test Execution Script',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Test Scenarios:
{chr(10).join(f"  {name}: {config['description']}" for name, config in TEST_SCENARIOS.items())}

Examples:
  # Run quick test (3 companies)
  python test_pipeline_e2e.py --scenario quick
  
  # Run standard test (5 companies)
  python test_pipeline_e2e.py --scenario standard
  
  # Run with specific companies
  python test_pipeline_e2e.py --companies RELIANCE TCS INFY
  
  # Skip cleanup for incremental testing
  python test_pipeline_e2e.py --scenario quick --skip-cleanup
  
  # Force cleanup without confirmation
  python test_pipeline_e2e.py --scenario standard --force-cleanup
  
  # Save reports to specific directory
  python test_pipeline_e2e.py --scenario comprehensive --output-dir ./test_reports
  
  # Enable debug logging
  python test_pipeline_e2e.py --scenario quick --log-level DEBUG

Environment Variables:
  All environment variables from pipeline_orchestrator.py are supported.
        """
    )
    
    parser.add_argument(
        '--scenario',
        choices=list(TEST_SCENARIOS.keys()),
        default='standard',
        help='Test scenario to run (default: standard)'
    )
    
    parser.add_argument(
        '--companies',
        nargs='+',
        help='List of company symbols to test (overrides scenario limit)'
    )
    
    parser.add_argument(
        '--skip-cleanup',
        action='store_true',
        help='Skip cleanup stage (for incremental testing)'
    )
    
    parser.add_argument(
        '--force-cleanup',
        action='store_true',
        help='Force cleanup without confirmation'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--output-dir',
        help='Directory for test reports (default: ./test_reports)'
    )
    
    parser.add_argument(
        '--no-report',
        action='store_true',
        help='Do not generate test report files'
    )
    
    args = parser.parse_args()
    
    # Set default output directory
    if args.output_dir is None and not args.no_report:
        args.output_dir = './test_reports'
    
    # Run test
    report = run_test(
        scenario=args.scenario,
        companies=args.companies,
        skip_cleanup=args.skip_cleanup,
        force_cleanup=args.force_cleanup,
        log_level=args.log_level,
        output_dir=args.output_dir
    )
    
    # Print summary
    print("\n")
    print(report.generate_summary())
    
    # Save reports
    if not args.no_report and args.output_dir:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save text report
        text_report_path = os.path.join(
            args.output_dir,
            f"test_report_{args.scenario}_{timestamp}.txt"
        )
        report.save_to_file(text_report_path)
        print(f"\n📄 Text report saved to: {text_report_path}")
        
        # Save JSON report
        json_report_path = os.path.join(
            args.output_dir,
            f"test_report_{args.scenario}_{timestamp}.json"
        )
        report.save_to_json(json_report_path)
        print(f"📄 JSON report saved to: {json_report_path}")
    
    # Exit with appropriate code
    success = report.pipeline_result and report.pipeline_result.get('success', False)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
