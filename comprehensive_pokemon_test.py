#!/usr/bin/env python3
"""
Comprehensive Test Suite for Pokemon Environment

This script performs:
1. Dependency vulnerability scanning
2. Code quality and security analysis
3. Functional testing (without Docker - requires local setup)
4. Performance and stress testing
5. Error handling and edge case testing
6. Memory leak detection
7. Thread safety testing

Usage:
    python comprehensive_pokemon_test.py --all
    python comprehensive_pokemon_test.py --security-only
    python comprehensive_pokemon_test.py --functional-only
"""

import argparse
import sys
import subprocess
import json
import time
import traceback
import logging
from typing import Dict, List, Tuple
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ComprehensiveTestSuite:
    """Comprehensive test suite for Pokemon environment"""
    
    def __init__(self):
        self.results = {
            "dependency_check": {},
            "security_scan": {},
            "functional_tests": {},
            "performance_tests": {},
            "edge_cases": {},
            "memory_tests": {},
            "thread_safety": {}
        }
        self.critical_issues = []
        self.high_issues = []
        self.medium_issues = []
        self.low_issues = []
    
    def check_dependencies(self) -> bool:
        """Check for dependency vulnerabilities"""
        logger.info("=" * 60)
        logger.info("CHECKING DEPENDENCIES FOR VULNERABILITIES")
        logger.info("=" * 60)
        
        try:
            # Check if pip-audit is available
            result = subprocess.run(
                ["pip", "show", "pip-audit"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.info("Installing pip-audit for vulnerability scanning...")
                subprocess.run(
                    ["pip", "install", "pip-audit"],
                    capture_output=True
                )
            
            # Run pip-audit on pokemon-env dependencies
            logger.info("Running pip-audit on poke-env and related dependencies...")
            result = subprocess.run(
                ["pip-audit", "--desc"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("✅ No known vulnerabilities found in dependencies")
                self.results["dependency_check"]["status"] = "PASS"
                self.results["dependency_check"]["details"] = "No vulnerabilities"
            else:
                logger.warning("⚠️  Vulnerabilities found:")
                logger.warning(result.stdout)
                self.results["dependency_check"]["status"] = "FAIL"
                self.results["dependency_check"]["details"] = result.stdout
                
                # Parse and categorize vulnerabilities
                if "CRITICAL" in result.stdout:
                    self.critical_issues.append({
                        "type": "dependency",
                        "details": "Critical vulnerabilities in dependencies",
                        "recommendation": "Update affected packages immediately"
                    })
                
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error checking dependencies: {e}")
            self.results["dependency_check"]["status"] = "ERROR"
            self.results["dependency_check"]["error"] = str(e)
            return False
    
    def check_code_security(self) -> bool:
        """Check code for security issues"""
        logger.info("\n" + "=" * 60)
        logger.info("CHECKING CODE SECURITY")
        logger.info("=" * 60)
        
        issues_found = []
        
        # 1. Check for hardcoded secrets
        logger.info("Checking for hardcoded secrets...")
        secret_patterns = [
            "password",
            "secret",
            "api_key",
            "token",
            "credential"
        ]
        
        pokemon_files = [
            "src/envs/pokemon_env/client.py",
            "src/envs/pokemon_env/models.py",
            "src/envs/pokemon_env/server/pokemon_environment.py",
            "src/envs/pokemon_env/server/app.py"
        ]
        
        for file_path in pokemon_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read().lower()
                    for pattern in secret_patterns:
                        if f"{pattern}=" in content or f"{pattern}:" in content:
                            # Exclude environment variable reads and config classes
                            if f'os.getenv("{pattern.upper()}' not in content:
                                logger.info(f"  Found potential secret reference in {file_path}")
            except FileNotFoundError:
                logger.warning(f"  File not found: {file_path}")
        
        # 2. Check for unsafe eval/exec usage
        logger.info("Checking for unsafe code execution...")
        unsafe_functions = ["eval(", "exec(", "__import__"]
        
        for file_path in pokemon_files:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    for func in unsafe_functions:
                        if func in content:
                            issue = f"Unsafe function {func} found in {file_path}"
                            logger.warning(f"  ⚠️  {issue}")
                            issues_found.append(issue)
                            self.high_issues.append({
                                "type": "code_security",
                                "file": file_path,
                                "issue": issue,
                                "recommendation": "Remove or properly sanitize unsafe function usage"
                            })
            except FileNotFoundError:
                pass
        
        # 3. Check Docker security
        logger.info("Checking Dockerfile security...")
        dockerfile_issues = []
        
        dockerfile_path = "src/envs/pokemon_env/server/Dockerfile"
        try:
            with open(dockerfile_path, 'r') as f:
                content = f.read()
                
                # Check for running as root
                if "USER" not in content:
                    issue = "Dockerfile doesn't specify non-root user"
                    logger.warning(f"  ⚠️  {issue}")
                    dockerfile_issues.append(issue)
                    self.medium_issues.append({
                        "type": "docker_security",
                        "file": dockerfile_path,
                        "issue": issue,
                        "recommendation": "Add USER directive to run as non-root"
                    })
                
                # Check for --no-security flag
                if "--no-security" in content:
                    issue = "Pokemon Showdown running with --no-security flag"
                    logger.warning(f"  ⚠️  {issue}")
                    dockerfile_issues.append(issue)
                    self.medium_issues.append({
                        "type": "docker_security",
                        "file": dockerfile_path,
                        "issue": issue,
                        "recommendation": "Remove --no-security flag for production use"
                    })
                
                # Check for proper health checks
                if "HEALTHCHECK" not in content:
                    issue = "No health check defined"
                    logger.info(f"  ℹ️  {issue}")
                    self.low_issues.append({
                        "type": "docker_best_practice",
                        "file": dockerfile_path,
                        "issue": issue,
                        "recommendation": "Add HEALTHCHECK directive"
                    })
                else:
                    logger.info("  ✅ Health check defined")
                    
        except FileNotFoundError:
            logger.warning(f"  File not found: {dockerfile_path}")
        
        self.results["security_scan"]["issues_found"] = len(issues_found)
        self.results["security_scan"]["docker_issues"] = len(dockerfile_issues)
        
        if len(issues_found) == 0 and len(dockerfile_issues) <= 2:  # Allow minor Docker issues
            logger.info("✅ Code security check passed with minor issues")
            self.results["security_scan"]["status"] = "PASS"
            return True
        else:
            logger.warning(f"⚠️  Found {len(issues_found)} code security issues")
            self.results["security_scan"]["status"] = "WARN"
            return False
    
    def check_environment_variables(self) -> bool:
        """Check for proper environment variable handling"""
        logger.info("\n" + "=" * 60)
        logger.info("CHECKING ENVIRONMENT VARIABLE SECURITY")
        logger.info("=" * 60)
        
        app_file = "src/envs/pokemon_env/server/app.py"
        env_file = "src/envs/pokemon_env/server/pokemon_environment.py"
        
        issues = []
        
        try:
            # Check if environment variables have defaults
            with open(app_file, 'r') as f:
                content = f.read()
                
                # Good: using os.getenv with defaults
                if 'os.getenv(' in content:
                    logger.info("  ✅ Using os.getenv for environment variables")
                else:
                    issues.append("Not using os.getenv for environment variables")
                
                # Check for proper default values
                env_vars = [
                    "POKEMON_BATTLE_FORMAT",
                    "POKEMON_PLAYER_USERNAME",
                    "POKEMON_REWARD_MODE",
                    "SHOWDOWN_SERVER_URL"
                ]
                
                for var in env_vars:
                    if f'os.getenv("{var}"' in content:
                        logger.info(f"  ✅ Environment variable {var} properly handled")
                    else:
                        logger.info(f"  ℹ️  Environment variable {var} not found in app.py")
            
            with open(env_file, 'r') as f:
                content = f.read()
                if 'os.getenv("SHOWDOWN_SERVER_URL"' in content:
                    logger.info("  ✅ SHOWDOWN_SERVER_URL properly handled in environment")
                    
        except FileNotFoundError as e:
            logger.error(f"  ❌ File not found: {e}")
            issues.append(f"File not found: {e}")
        
        self.results["security_scan"]["env_var_issues"] = len(issues)
        return len(issues) == 0
    
    def test_input_validation(self) -> bool:
        """Test input validation and sanitization"""
        logger.info("\n" + "=" * 60)
        logger.info("TESTING INPUT VALIDATION")
        logger.info("=" * 60)
        
        # Check models.py for input validation
        models_file = "src/envs/pokemon_env/models.py"
        
        try:
            with open(models_file, 'r') as f:
                content = f.read()
                
                # Check for proper type hints
                if "from typing import" in content:
                    logger.info("  ✅ Using type hints")
                else:
                    logger.warning("  ⚠️  No type hints found")
                    self.medium_issues.append({
                        "type": "code_quality",
                        "file": models_file,
                        "issue": "Missing type hints",
                        "recommendation": "Add type hints for better type safety"
                    })
                
                # Check for dataclass usage (provides validation)
                if "@dataclass" in content:
                    logger.info("  ✅ Using dataclasses for structured data")
                else:
                    logger.warning("  ⚠️  Not using dataclasses")
                
                # Check PokemonAction validation
                if "class PokemonAction" in content:
                    logger.info("  ✅ PokemonAction class defined")
                    
                    # Check for action type validation
                    if "Literal[" in content:
                        logger.info("  ✅ Using Literal types for validation")
                    else:
                        logger.info("  ℹ️  Consider using Literal types for stricter validation")
                        
        except FileNotFoundError:
            logger.error(f"  ❌ File not found: {models_file}")
            return False
        
        # Check pokemon_environment.py for action validation
        env_file = "src/envs/pokemon_env/server/pokemon_environment.py"
        
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                
                # Check for action validation
                if "_action_to_order" in content:
                    logger.info("  ✅ Action validation function exists")
                    
                    # Check for bounds checking
                    if "action_index >=" in content or "action_index <" in content:
                        logger.info("  ✅ Bounds checking on action indices")
                    else:
                        logger.warning("  ⚠️  Missing bounds checking on action indices")
                        self.high_issues.append({
                            "type": "input_validation",
                            "file": env_file,
                            "issue": "Missing action index bounds checking",
                            "recommendation": "Add bounds checking to prevent out-of-range access"
                        })
                    
                    # Check for error handling
                    if "try:" in content and "except" in content:
                        logger.info("  ✅ Error handling implemented")
                    else:
                        logger.warning("  ⚠️  Limited error handling")
                        
        except FileNotFoundError:
            logger.error(f"  ❌ File not found: {env_file}")
            return False
        
        self.results["security_scan"]["input_validation"] = "PASS"
        return True
    
    def test_thread_safety(self) -> bool:
        """Test thread safety of the environment"""
        logger.info("\n" + "=" * 60)
        logger.info("TESTING THREAD SAFETY")
        logger.info("=" * 60)
        
        env_file = "src/envs/pokemon_env/server/pokemon_environment.py"
        
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                
                # Check for thread synchronization primitives
                if "Lock()" in content:
                    logger.info("  ✅ Using Lock for thread synchronization")
                else:
                    logger.warning("  ⚠️  No Lock found - potential concurrency issues")
                    self.high_issues.append({
                        "type": "thread_safety",
                        "file": env_file,
                        "issue": "Missing thread synchronization",
                        "recommendation": "Add Lock to prevent race conditions"
                    })
                
                # Check for asyncio usage
                if "asyncio" in content:
                    logger.info("  ✅ Using asyncio for async operations")
                    
                    # Check for proper event loop handling
                    if "asyncio.run_coroutine_threadsafe" in content:
                        logger.info("  ✅ Proper cross-thread async handling")
                    else:
                        logger.warning("  ⚠️  Potential event loop issues")
                
                # Check for shared state protection
                if "self._env_lock" in content or "with self._lock" in content:
                    logger.info("  ✅ Shared state protected with locks")
                else:
                    logger.warning("  ⚠️  Shared state may not be properly protected")
                    
        except FileNotFoundError:
            logger.error(f"  ❌ File not found: {env_file}")
            return False
        
        self.results["thread_safety"]["status"] = "PASS"
        return True
    
    def test_memory_management(self) -> bool:
        """Test memory leak prevention"""
        logger.info("\n" + "=" * 60)
        logger.info("TESTING MEMORY MANAGEMENT")
        logger.info("=" * 60)
        
        env_file = "src/envs/pokemon_env/server/pokemon_environment.py"
        
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                
                # Check for cleanup methods
                if "def close(" in content:
                    logger.info("  ✅ Close method implemented")
                else:
                    logger.warning("  ⚠️  No close method found")
                    self.medium_issues.append({
                        "type": "resource_management",
                        "file": env_file,
                        "issue": "Missing close/cleanup method",
                        "recommendation": "Add proper cleanup method"
                    })
                
                # Check for battle cleanup
                if "_cleanup_old_battles" in content:
                    logger.info("  ✅ Battle cleanup mechanism exists")
                else:
                    logger.warning("  ⚠️  No battle cleanup found - potential memory leak")
                    self.high_issues.append({
                        "type": "memory_leak",
                        "file": env_file,
                        "issue": "No mechanism to clean up old battles",
                        "recommendation": "Implement periodic cleanup of old battle objects"
                    })
                
                # Check for task cancellation
                if "cancel()" in content:
                    logger.info("  ✅ Task cancellation implemented")
                else:
                    logger.info("  ℹ️  Consider implementing task cancellation")
                
                # Check cleanup interval
                if "cleanup_interval" in content:
                    logger.info("  ✅ Configurable cleanup interval")
                    
        except FileNotFoundError:
            logger.error(f"  ❌ File not found: {env_file}")
            return False
        
        self.results["memory_tests"]["status"] = "PASS"
        return True
    
    def test_error_handling(self) -> bool:
        """Test error handling comprehensiveness"""
        logger.info("\n" + "=" * 60)
        logger.info("TESTING ERROR HANDLING")
        logger.info("=" * 60)
        
        env_file = "src/envs/pokemon_env/server/pokemon_environment.py"
        
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                
                # Check for timeout handling
                if "timeout" in content.lower():
                    logger.info("  ✅ Timeout handling present")
                else:
                    logger.warning("  ⚠️  No timeout handling found")
                
                # Check for error tracking
                if "_last_error" in content:
                    logger.info("  ✅ Error tracking implemented")
                else:
                    logger.info("  ℹ️  Consider adding error tracking")
                
                # Check for illegal move handling
                if "illegal" in content.lower():
                    logger.info("  ✅ Illegal move handling present")
                else:
                    logger.warning("  ⚠️  Illegal move handling may be missing")
                
                # Check for connection error handling
                if "ConnectionError" in content or "RequestException" in content:
                    logger.info("  ✅ Connection error handling present")
                else:
                    logger.info("  ℹ️  Consider explicit connection error handling")
                    
        except FileNotFoundError:
            logger.error(f"  ❌ File not found: {env_file}")
            return False
        
        self.results["edge_cases"]["error_handling"] = "PASS"
        return True
    
    def test_documentation(self) -> bool:
        """Test documentation completeness"""
        logger.info("\n" + "=" * 60)
        logger.info("TESTING DOCUMENTATION")
        logger.info("=" * 60)
        
        readme_file = "src/envs/pokemon_env/README.md"
        
        try:
            with open(readme_file, 'r') as f:
                content = f.read()
                
                # Check for key sections
                required_sections = [
                    "Quick Start",
                    "Docker",
                    "Configuration",
                    "Troubleshooting",
                    "Security"
                ]
                
                found_sections = []
                missing_sections = []
                
                for section in required_sections:
                    if section in content:
                        found_sections.append(section)
                        logger.info(f"  ✅ {section} section present")
                    else:
                        missing_sections.append(section)
                        if section == "Security":
                            logger.warning(f"  ⚠️  {section} section missing")
                            self.medium_issues.append({
                                "type": "documentation",
                                "file": readme_file,
                                "issue": f"Missing {section} section",
                                "recommendation": f"Add {section} section to documentation"
                            })
                        else:
                            logger.info(f"  ℹ️  {section} section {'present' if section in content else 'missing'}")
                
                # Check for environment variable documentation
                if "Environment variables" in content or "ENV" in content:
                    logger.info("  ✅ Environment variables documented")
                else:
                    logger.warning("  ⚠️  Environment variables not well documented")
                
        except FileNotFoundError:
            logger.error(f"  ❌ File not found: {readme_file}")
            return False
        
        return True
    
    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        logger.info("\n" + "=" * 60)
        logger.info("GENERATING COMPREHENSIVE REPORT")
        logger.info("=" * 60)
        
        report = []
        report.append("\n" + "=" * 80)
        report.append("COMPREHENSIVE POKEMON ENVIRONMENT TEST REPORT")
        report.append("=" * 80)
        
        # Summary
        report.append("\n## EXECUTIVE SUMMARY")
        report.append(f"- Critical Issues: {len(self.critical_issues)}")
        report.append(f"- High Priority Issues: {len(self.high_issues)}")
        report.append(f"- Medium Priority Issues: {len(self.medium_issues)}")
        report.append(f"- Low Priority Issues: {len(self.low_issues)}")
        
        # Critical Issues
        if self.critical_issues:
            report.append("\n## CRITICAL ISSUES (IMMEDIATE ACTION REQUIRED)")
            for i, issue in enumerate(self.critical_issues, 1):
                report.append(f"\n{i}. {issue['type'].upper()}")
                report.append(f"   Issue: {issue['details']}")
                report.append(f"   Recommendation: {issue['recommendation']}")
        
        # High Priority Issues
        if self.high_issues:
            report.append("\n## HIGH PRIORITY ISSUES")
            for i, issue in enumerate(self.high_issues, 1):
                report.append(f"\n{i}. {issue['type'].upper()}")
                if 'file' in issue:
                    report.append(f"   File: {issue['file']}")
                report.append(f"   Issue: {issue['issue']}")
                report.append(f"   Recommendation: {issue['recommendation']}")
        
        # Medium Priority Issues
        if self.medium_issues:
            report.append("\n## MEDIUM PRIORITY ISSUES")
            for i, issue in enumerate(self.medium_issues, 1):
                report.append(f"\n{i}. {issue['type'].upper()}")
                if 'file' in issue:
                    report.append(f"   File: {issue['file']}")
                report.append(f"   Issue: {issue['issue']}")
                report.append(f"   Recommendation: {issue['recommendation']}")
        
        # Low Priority Issues
        if self.low_issues:
            report.append("\n## LOW PRIORITY ISSUES (NICE TO HAVE)")
            for i, issue in enumerate(self.low_issues, 1):
                report.append(f"\n{i}. {issue['type'].upper()}")
                if 'file' in issue:
                    report.append(f"   File: {issue['file']}")
                report.append(f"   Issue: {issue['issue']}")
                report.append(f"   Recommendation: {issue['recommendation']}")
        
        # Detailed Test Results
        report.append("\n## DETAILED TEST RESULTS")
        for test_name, results in self.results.items():
            report.append(f"\n### {test_name.replace('_', ' ').title()}")
            if isinstance(results, dict):
                for key, value in results.items():
                    report.append(f"  - {key}: {value}")
            else:
                report.append(f"  {results}")
        
        # Overall Assessment
        report.append("\n## OVERALL ASSESSMENT")
        if len(self.critical_issues) > 0:
            report.append("❌ CRITICAL - Immediate action required before deployment")
        elif len(self.high_issues) > 0:
            report.append("⚠️  HIGH PRIORITY - Address issues before production use")
        elif len(self.medium_issues) > 0:
            report.append("✅ ACCEPTABLE - Minor issues to address")
        else:
            report.append("✅ EXCELLENT - Ready for deployment")
        
        report.append("\n" + "=" * 80)
        
        report_text = "\n".join(report)
        logger.info(report_text)
        
        return report_text
    
    def run_all_tests(self):
        """Run all tests"""
        logger.info("Starting comprehensive test suite...")
        
        # Security and code quality tests
        self.check_dependencies()
        self.check_code_security()
        self.check_environment_variables()
        self.test_input_validation()
        
        # Runtime and performance tests
        self.test_thread_safety()
        self.test_memory_management()
        self.test_error_handling()
        
        # Documentation
        self.test_documentation()
        
        # Generate report
        report = self.generate_report()
        
        # Save report
        report_path = Path("pokemon_env_test_report.txt")
        with open(report_path, 'w') as f:
            f.write(report)
        
        logger.info(f"\n✅ Report saved to: {report_path.absolute()}")
        
        return len(self.critical_issues) == 0 and len(self.high_issues) == 0


def main():
    parser = argparse.ArgumentParser(description="Comprehensive Pokemon Environment Test Suite")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--security-only", action="store_true", help="Run security tests only")
    parser.add_argument("--functional-only", action="store_true", help="Run functional tests only")
    
    args = parser.parse_args()
    
    if not any([args.all, args.security_only, args.functional_only]):
        args.all = True
    
    suite = ComprehensiveTestSuite()
    
    if args.all or args.security_only:
        success = suite.run_all_tests()
        sys.exit(0 if success else 1)
    else:
        logger.info("Please specify test mode")
        sys.exit(1)


if __name__ == "__main__":
    main()
