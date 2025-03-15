#!/usr/bin/env python3
"""
Enhanced test runner for Gmail MCP Server tests.
This script runs all the test files and provides detailed information about test execution and results.
"""

import unittest
import sys
import os
import time
import inspect
import json
from datetime import datetime
from io import StringIO
from contextlib import redirect_stdout

# Custom test result class to capture detailed information
class DetailedTestResult(unittest.TextTestResult):
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.test_details = {}
        self.current_test = None
        self.current_output = None
        self.current_start_time = None
    
    def startTest(self, test):
        self.current_test = test
        self.current_output = StringIO()
        self.current_start_time = time.time()
        
        # Get test docstring and source code
        test_method = getattr(test, test._testMethodName)
        docstring = test_method.__doc__ or "No description available"
        
        # Try to get the source code
        try:
            source_code = inspect.getsource(test_method)
        except Exception:
            source_code = "Source code not available"
        
        # Store test details
        test_id = self.getDescription(test)
        self.test_details[test_id] = {
            'description': docstring.strip(),
            'source_code': source_code.strip(),
            'output': '',
            'result': 'RUNNING',
            'start_time': self.current_start_time,
            'end_time': None,
            'duration': None
        }
        
        # Print test header
        header = f"\n{'='*80}\nTEST: {test_id}\n{'-'*80}\n{docstring.strip()}\n{'-'*80}"
        print(header)
        
        super().startTest(test)
    
    def stopTest(self, test):
        end_time = time.time()
        test_id = self.getDescription(test)
        
        if test_id in self.test_details:
            self.test_details[test_id]['end_time'] = end_time
            self.test_details[test_id]['duration'] = end_time - self.test_details[test_id]['start_time']
            
            # Get the captured output
            if self.current_output:
                output = self.current_output.getvalue()
                self.test_details[test_id]['output'] = output
                print(f"Test Output:\n{output}")
        
        # Print test footer
        if test_id in self.test_details:
            duration = self.test_details[test_id]['duration']
            result = self.test_details[test_id]['result']
            footer = f"{'-'*80}\nRESULT: {result} (Duration: {duration:.2f} seconds)\n{'='*80}"
            print(footer)
        
        self.current_test = None
        self.current_output = None
        super().stopTest(test)
    
    def addSuccess(self, test):
        test_id = self.getDescription(test)
        if test_id in self.test_details:
            self.test_details[test_id]['result'] = 'PASS'
        super().addSuccess(test)
    
    def addFailure(self, test, err):
        test_id = self.getDescription(test)
        if test_id in self.test_details:
            self.test_details[test_id]['result'] = 'FAIL'
            self.test_details[test_id]['error'] = self._exc_info_to_string(err, test)
        super().addFailure(test, err)
    
    def addError(self, test, err):
        test_id = self.getDescription(test)
        if test_id in self.test_details:
            self.test_details[test_id]['result'] = 'ERROR'
            self.test_details[test_id]['error'] = self._exc_info_to_string(err, test)
        super().addError(test, err)
    
    def addSkip(self, test, reason):
        test_id = self.getDescription(test)
        if test_id in self.test_details:
            self.test_details[test_id]['result'] = 'SKIP'
            self.test_details[test_id]['skip_reason'] = reason
        super().addSkip(test, reason)

# Custom test runner that uses our detailed test result
class DetailedTestRunner(unittest.TextTestRunner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.resultclass = DetailedTestResult
    
    def run(self, test):
        result = super().run(test)
        return result

def run_tests():
    """Run all test files and return the test results with detailed information"""
    # Print test header
    print("\n" + "="*80)
    print(f"GMAIL MCP SERVER TESTS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Discover and run all tests
    start_time = time.time()
    
    # Create a test loader
    loader = unittest.TestLoader()
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add test files to the suite
    for test_file in ['test_gmail_server.py', 'test_gmail_mcp.py']:
        if os.path.exists(test_file):
            module_name = os.path.splitext(test_file)[0]
            try:
                tests = loader.loadTestsFromName(module_name)
                suite.addTest(tests)
                print(f"Added tests from {test_file}")
                
                # Print test methods in this file
                test_count = 0
                for test_case in tests:
                    for test in test_case:
                        test_count += 1
                        test_method = getattr(test, test._testMethodName)
                        docstring = test_method.__doc__ or "No description available"
                        print(f"  - {test._testMethodName}: {docstring.strip()}")
                
                print(f"  Total: {test_count} tests\n")
                
            except Exception as e:
                print(f"Error loading tests from {test_file}: {str(e)}")
    
    # Run the tests with our detailed runner
    runner = DetailedTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Calculate execution time
    execution_time = time.time() - start_time
    
    # Print test summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print(f"Execution time: {execution_time:.2f} seconds")
    print("="*80)
    
    # Print failures and errors if any
    if result.failures or result.errors:
        print("\nFAILURES AND ERRORS:")
        print("-"*80)
        
        for test, traceback in result.failures:
            print(f"\nFAILURE: {test}")
            print(f"{traceback}")
        
        for test, traceback in result.errors:
            print(f"\nERROR: {test}")
            print(f"{traceback}")
    
    # Generate a detailed report
    report_file = "test_report.json"
    with open(report_file, 'w') as f:
        json.dump(result.test_details, f, indent=2)
    
    print(f"\nDetailed test report saved to {report_file}")
    
    return result

if __name__ == "__main__":
    # Run the tests
    result = run_tests()
    
    # Exit with appropriate status code
    sys.exit(len(result.failures) + len(result.errors))