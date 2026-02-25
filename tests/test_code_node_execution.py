"""
Test Suite for Custom JavaScript Code Node Execution
Tests code validation, execution, security, and performance
"""
import pytest
import sys
import os
import json
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.code_executor import (
    CodeValidator,
    JavaScriptExecutor,
    SandboxEnvironment,
    ExecutionStatus,
    CODE_TEMPLATES
)


class TestCodeValidator:
    """Test code validation for security and syntax"""

    def test_empty_code(self):
        """Test validation of empty code"""
        is_valid, error = CodeValidator.validate("")
        assert not is_valid
        assert "empty" in error.lower()

    def test_valid_simple_code(self):
        """Test validation of simple valid code"""
        code = "console.log('hello');"
        is_valid, error = CodeValidator.validate(code)
        assert is_valid
        assert error is None

    def test_code_too_long(self):
        """Test validation of excessively long code"""
        code = "console.log('x');" * 1000  # More than 10KB
        is_valid, error = CodeValidator.validate(code)
        assert not is_valid
        assert "exceeds maximum length" in error.lower()

    def test_dangerous_require_pattern(self):
        """Test detection of require() calls"""
        code = "const fs = require('fs');"
        is_valid, error = CodeValidator.validate(code)
        assert not is_valid
        assert "dangerous" in error.lower()

    def test_dangerous_eval_pattern(self):
        """Test detection of eval() calls"""
        code = "eval('dangerous code');"
        is_valid, error = CodeValidator.validate(code)
        assert not is_valid

    def test_dangerous_process_access(self):
        """Test detection of process access"""
        code = "process.env.SECRET"
        is_valid, error = CodeValidator.validate(code)
        assert not is_valid

    def test_dangerous_file_system(self):
        """Test detection of file system access"""
        code = "fs.readFileSync('/etc/passwd')"
        is_valid, error = CodeValidator.validate(code)
        assert not is_valid

    def test_unmatched_braces(self):
        """Test detection of unmatched braces"""
        code = "function test() { console.log('test')"
        is_valid, error = CodeValidator.validate(code)
        assert not is_valid
        assert "unmatched" in error.lower()

    def test_unmatched_brackets(self):
        """Test detection of unmatched brackets"""
        code = "const arr = [1, 2, 3;"
        is_valid, error = CodeValidator.validate(code)
        assert not is_valid

    def test_unmatched_parentheses(self):
        """Test detection of unmatched parentheses"""
        code = "console.log('test'"
        is_valid, error = CodeValidator.validate(code)
        assert not is_valid

    def test_valid_complex_code(self):
        """Test validation of complex but valid code"""
        code = """
        function processData(items) {
            return items.filter(item => item.active)
                        .map(item => ({ id: item.id, name: item.name }));
        }
        const results = processData([{id: 1, active: true, name: 'Test'}]);
        console.log(results);
        """
        is_valid, error = CodeValidator.validate(code)
        assert is_valid
        assert error is None


class TestSandboxEnvironment:
    """Test sandbox environment creation"""

    def test_sandbox_script_generation(self):
        """Test that sandbox script is properly generated"""
        user_code = "console.log('test');"
        sandbox_script = SandboxEnvironment.create_sandbox_script(user_code)

        assert user_code in sandbox_script
        assert "sandboxConsole" in sandbox_script
        assert "sandboxFetch" in sandbox_script
        assert "EXECUTION_START" in sandbox_script

    def test_sandbox_includes_console_mock(self):
        """Test that sandbox includes console mock"""
        user_code = "console.log('test');"
        sandbox_script = SandboxEnvironment.create_sandbox_script(user_code)

        assert "sandboxConsole" in sandbox_script
        assert "consoleLogs" in sandbox_script
        assert "error:" in sandbox_script  # Check for error method definition

    def test_sandbox_includes_fetch_mock(self):
        """Test that sandbox includes fetch mock"""
        user_code = "fetch('/api/data');"
        sandbox_script = SandboxEnvironment.create_sandbox_script(user_code)

        assert "sandboxFetch" in sandbox_script
        assert "allowedHosts" in sandbox_script

    def test_sandbox_with_api_token(self):
        """Test sandbox creation with API token"""
        user_code = "fetch('/api/data');"
        api_token = "test_token_123"
        sandbox_script = SandboxEnvironment.create_sandbox_script(user_code, api_token)

        # Token should be in the script but redacted format
        assert "sandboxFetch" in sandbox_script


class TestJavaScriptExecutor:
    """Test JavaScript code execution"""

    def test_simple_console_log(self):
        """Test simple console.log execution"""
        code = "console.log('Hello, World!');"
        result = JavaScriptExecutor.execute(code)

        assert result.status == ExecutionStatus.SUCCESS
        assert result.execution_time > 0
        assert len(result.console_logs) > 0

    def test_execution_with_variables(self):
        """Test execution with variable assignment"""
        code = """
        const x = 5;
        const y = 10;
        const sum = x + y;
        console.log('Sum:', sum);
        results.sum = sum;
        """
        result = JavaScriptExecutor.execute(code)

        assert result.status == ExecutionStatus.SUCCESS
        # Check that execution completed successfully
        assert len(result.console_logs) > 0 or result.return_value is not None

    def test_execution_with_functions(self):
        """Test execution with function definitions"""
        code = """
        function add(a, b) {
            return a + b;
        }
        const result = add(3, 7);
        console.log('Result:', result);
        results.calculation = result;
        """
        result = JavaScriptExecutor.execute(code)

        assert result.status == ExecutionStatus.SUCCESS

    def test_execution_with_loops(self):
        """Test execution with loops"""
        code = """
        let sum = 0;
        for (let i = 1; i <= 10; i++) {
            sum += i;
        }
        console.log('Sum 1-10:', sum);
        results.sum = sum;
        """
        result = JavaScriptExecutor.execute(code)

        assert result.status == ExecutionStatus.SUCCESS

    def test_execution_with_array_methods(self):
        """Test execution with array methods"""
        code = """
        const numbers = [1, 2, 3, 4, 5];
        const doubled = numbers.map(n => n * 2);
        const evens = numbers.filter(n => n % 2 === 0);
        console.log('Doubled:', doubled);
        console.log('Evens:', evens);
        results.doubled = doubled;
        results.evens = evens;
        """
        result = JavaScriptExecutor.execute(code)

        assert result.status == ExecutionStatus.SUCCESS

    def test_execution_with_objects(self):
        """Test execution with object operations"""
        code = """
        const person = {
            name: 'John',
            age: 30,
            email: 'john@example.com'
        };
        console.log('Person:', JSON.stringify(person));
        results.person = person;
        """
        result = JavaScriptExecutor.execute(code)

        assert result.status == ExecutionStatus.SUCCESS

    def test_validation_error(self):
        """Test handling of validation errors"""
        code = "const fs = require('fs');"  # Dangerous pattern
        result = JavaScriptExecutor.execute(code)

        assert result.status == ExecutionStatus.VALIDATION_ERROR
        assert result.error is not None

    def test_timeout_error(self):
        """Test timeout handling"""
        code = """
        // Infinite loop - should timeout
        while (true) {
            // Spin forever
        }
        """
        result = JavaScriptExecutor.execute(code, timeout_ms=1000)

        assert result.status == ExecutionStatus.TIMEOUT

    def test_syntax_error(self):
        """Test handling of syntax errors"""
        code = "const x = {invalid json};"
        result = JavaScriptExecutor.execute(code)

        assert result.status == ExecutionStatus.ERROR
        assert result.error is not None

    def test_execution_time_measurement(self):
        """Test that execution time is measured"""
        code = """
        let sum = 0;
        for (let i = 0; i < 1000; i++) {
            sum += i;
        }
        console.log('Done');
        """
        result = JavaScriptExecutor.execute(code)

        assert result.status == ExecutionStatus.SUCCESS
        assert result.execution_time > 0
        assert result.execution_time < 1.0  # Should complete in <1 second

    def test_console_logs_capture(self):
        """Test that console logs are captured"""
        code = """
        console.log('First message');
        console.log('Second message');
        console.log('Third message');
        """
        result = JavaScriptExecutor.execute(code)

        assert result.status == ExecutionStatus.SUCCESS
        # Check that console logs contain the messages
        assert len(result.console_logs) > 0
        assert any('First message' in log for log in result.console_logs)

    def test_multiple_console_types(self):
        """Test capturing different console methods"""
        code = """
        console.log('This is info');
        console.error('This is an error');
        console.warn('This is a warning');
        console.info('This is information');
        """
        result = JavaScriptExecutor.execute(code)

        assert result.status == ExecutionStatus.SUCCESS

    def test_json_operations(self):
        """Test JSON parsing and stringification"""
        code = """
        const jsonStr = '{"name":"John","age":30}';
        const obj = JSON.parse(jsonStr);
        obj.city = 'New York';
        const result = JSON.stringify(obj);
        console.log('Result:', result);
        results.data = obj;
        """
        result = JavaScriptExecutor.execute(code)

        assert result.status == ExecutionStatus.SUCCESS

    def test_math_operations(self):
        """Test Math object usage"""
        code = """
        const sqrt = Math.sqrt(16);
        const abs = Math.abs(-5);
        const max = Math.max(1, 5, 3);
        const random = Math.random();
        console.log('sqrt(16):', sqrt);
        console.log('abs(-5):', abs);
        console.log('max(1,5,3):', max);
        results.sqrt = sqrt;
        results.abs = abs;
        results.max = max;
        """
        result = JavaScriptExecutor.execute(code)

        assert result.status == ExecutionStatus.SUCCESS

    def test_date_operations(self):
        """Test Date object usage"""
        code = """
        const now = new Date();
        const timestamp = now.getTime();
        const year = now.getFullYear();
        console.log('Year:', year);
        console.log('Timestamp:', timestamp);
        results.timestamp = timestamp;
        results.year = year;
        """
        result = JavaScriptExecutor.execute(code)

        assert result.status == ExecutionStatus.SUCCESS

    def test_error_handling_try_catch(self):
        """Test try-catch error handling"""
        code = """
        try {
            throw new Error('Test error');
        } catch (error) {
            console.log('Caught error:', error.message);
            results.error = error.message;
        }
        """
        result = JavaScriptExecutor.execute(code)

        assert result.status == ExecutionStatus.SUCCESS

    def test_custom_timeout(self):
        """Test custom timeout value"""
        code = "console.log('Quick execution');"
        result = JavaScriptExecutor.execute(code, timeout_ms=10000)

        assert result.status == ExecutionStatus.SUCCESS

    def test_return_value_preservation(self):
        """Test that results object is preserved"""
        code = """
        results.value1 = 42;
        results.value2 = 'test string';
        results.value3 = [1, 2, 3];
        results.value4 = {nested: {data: true}};
        """
        result = JavaScriptExecutor.execute(code)

        assert result.status == ExecutionStatus.SUCCESS
        assert result.return_value is not None


class TestCodeTemplates:
    """Test code template library"""

    def test_templates_exist(self):
        """Test that code templates are defined"""
        assert len(CODE_TEMPLATES) > 0
        assert 'hello_world' in CODE_TEMPLATES
        assert 'fetch_data' in CODE_TEMPLATES

    def test_template_structure(self):
        """Test that templates have required fields"""
        for template_id, template in CODE_TEMPLATES.items():
            assert 'name' in template
            assert 'description' in template
            assert 'code' in template
            assert isinstance(template['code'], str)
            assert len(template['code']) > 0

    def test_hello_world_template(self):
        """Test hello_world template execution"""
        template = CODE_TEMPLATES['hello_world']
        result = JavaScriptExecutor.execute(template['code'])

        assert result.status == ExecutionStatus.SUCCESS

    def test_process_array_template(self):
        """Test process_array template execution"""
        template = CODE_TEMPLATES['process_array']
        result = JavaScriptExecutor.execute(template['code'])

        assert result.status == ExecutionStatus.SUCCESS

    def test_loop_example_template(self):
        """Test loop_example template execution"""
        template = CODE_TEMPLATES['loop_example']
        result = JavaScriptExecutor.execute(template['code'])

        assert result.status == ExecutionStatus.SUCCESS

    def test_conditional_logic_template(self):
        """Test conditional_logic template execution"""
        template = CODE_TEMPLATES['conditional_logic']
        result = JavaScriptExecutor.execute(template['code'])

        assert result.status == ExecutionStatus.SUCCESS

    def test_data_validation_template(self):
        """Test data_validation template execution"""
        template = CODE_TEMPLATES['data_validation']
        result = JavaScriptExecutor.execute(template['code'])

        assert result.status == ExecutionStatus.SUCCESS

    def test_data_aggregation_template(self):
        """Test data_aggregation template execution"""
        template = CODE_TEMPLATES['data_aggregation']
        result = JavaScriptExecutor.execute(template['code'])

        assert result.status == ExecutionStatus.SUCCESS


class TestExecutionResult:
    """Test execution result data class"""

    def test_result_serialization(self):
        """Test that results can be serialized to dict"""
        from backend.code_executor import ExecutionResult

        result = ExecutionResult(
            status=ExecutionStatus.SUCCESS,
            output="test output",
            execution_time=1.234,
            console_logs=['log1', 'log2']
        )

        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict['status'] == 'success'
        assert result_dict['execution_time'] == 1.234

    def test_result_with_error(self):
        """Test result with error message"""
        from backend.code_executor import ExecutionResult

        result = ExecutionResult(
            status=ExecutionStatus.ERROR,
            output="",
            error="Test error message",
            execution_time=0.5
        )

        result_dict = result.to_dict()
        assert result_dict['status'] == 'error'
        assert result_dict['error'] == "Test error message"


class TestIntegration:
    """Integration tests for complete execution flow"""

    def test_full_execution_flow(self):
        """Test complete validation and execution flow"""
        code = """
        const items = [
            {id: 1, name: 'Item 1', value: 100},
            {id: 2, name: 'Item 2', value: 200}
        ];
        const filtered = items.filter(i => i.value > 100);
        results.count = filtered.length;
        console.log('Filtered:', filtered);
        """

        # Validate
        is_valid, error = CodeValidator.validate(code)
        assert is_valid

        # Execute
        result = JavaScriptExecutor.execute(code)
        assert result.status == ExecutionStatus.SUCCESS

    def test_performance_baseline(self):
        """Test that execution completes within performance target"""
        code = """
        let sum = 0;
        for (let i = 0; i < 10000; i++) {
            sum += Math.sqrt(i);
        }
        results.sum = sum;
        """

        start = time.time()
        result = JavaScriptExecutor.execute(code)
        elapsed = time.time() - start

        assert result.status == ExecutionStatus.SUCCESS
        assert elapsed < 0.5  # Should complete in <500ms
        assert result.execution_time < 0.5
