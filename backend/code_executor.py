"""
Code Execution Engine for AI Automation
Provides safe sandboxed JavaScript execution for custom code nodes
"""
import subprocess
import json
import os
import tempfile
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Execution status codes"""
    SUCCESS = "success"
    TIMEOUT = "timeout"
    ERROR = "error"
    VALIDATION_ERROR = "validation_error"
    MEMORY_LIMIT = "memory_limit"


@dataclass
class ExecutionResult:
    """Result of code execution"""
    status: ExecutionStatus
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0
    console_logs: List[str] = None
    return_value: Any = None

    def __post_init__(self):
        if self.console_logs is None:
            self.console_logs = []

    def to_dict(self) -> Dict:
        return {
            'status': self.status.value,
            'output': self.output,
            'error': self.error,
            'execution_time': round(self.execution_time, 3),
            'console_logs': self.console_logs,
            'return_value': self.return_value
        }


class CodeValidator:
    """Validates JavaScript code before execution"""

    # Dangerous patterns that could bypass sandbox
    DANGEROUS_PATTERNS = [
        r'require\s*\(',  # Node require
        r'eval\s*\(',  # Eval
        r'Function\s*\(',  # Dynamic function creation
        r'process\s*\.',  # Process access
        r'child_process',  # Child process
        r'fs\s*\.',  # File system
        r'__dirname',  # Directory access
        r'__filename',  # File access
    ]

    @staticmethod
    def validate(code: str) -> Tuple[bool, Optional[str]]:
        """
        Validate code safety

        Args:
            code: JavaScript code to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        import re

        # Basic syntax check
        if not code or not code.strip():
            return False, "Code cannot be empty"

        # Check code length (prevent DoS)
        if len(code) > 10000:  # 10KB limit
            return False, "Code exceeds maximum length (10KB)"

        # Check for dangerous patterns
        for pattern in CodeValidator.DANGEROUS_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                return False, f"Dangerous pattern detected: {pattern}"

        # Check bracket matching
        if code.count('{') != code.count('}'):
            return False, "Unmatched curly braces"
        if code.count('[') != code.count(']'):
            return False, "Unmatched square brackets"
        if code.count('(') != code.count(')'):
            return False, "Unmatched parentheses"

        return True, None


class SandboxEnvironment:
    """Creates isolated sandbox environment for code execution"""

    @staticmethod
    def create_sandbox_script(user_code: str, api_client_token: str = None) -> str:
        """
        Wrap user code in sandbox with limited API access

        Args:
            user_code: User's JavaScript code
            api_client_token: Optional API token for fetch requests

        Returns:
            Complete sandbox script
        """
        auth_header = f"'Authorization': 'Bearer {api_client_token}'" if api_client_token else ""

        sandbox_script = f"""
(async () => {{
    const EXECUTION_START = Date.now();
    const consoleLogs = [];
    const results = {{}};
    let executionOutput = '';

    // Sandbox console
    const sandboxConsole = {{
        log: (...args) => {{
            const message = args.map(arg =>
                typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
            ).join(' ');
            consoleLogs.push(message);
            process.stdout.write(message + '\\n');
        }},
        error: (...args) => {{
            const message = args.map(arg =>
                typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
            ).join(' ');
            consoleLogs.push('[ERROR] ' + message);
            process.stderr.write('[ERROR] ' + message + '\\n');
        }},
        warn: (...args) => {{
            const message = args.map(arg =>
                typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
            ).join(' ');
            consoleLogs.push('[WARN] ' + message);
            process.stdout.write('[WARN] ' + message + '\\n');
        }},
        info: (...args) => {{
            const message = args.map(arg =>
                typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
            ).join(' ');
            consoleLogs.push('[INFO] ' + message);
            process.stdout.write('[INFO] ' + message + '\\n');
        }}
    }};

    // Sandbox fetch with restricted access
    const sandboxFetch = async (url, options = {{}}) => {{
        // Only allow specific safe URLs
        const allowedHosts = ['localhost', '127.0.0.1', 'api.example.com', 'jsonplaceholder.typicode.com'];
        try {{
            const urlObj = new URL(url);
            const isAllowed = allowedHosts.some(host => urlObj.hostname.includes(host));

            if (!isAllowed) {{
                throw new Error('URL not allowed in sandbox: ' + url);
            }}

            const headers = options.headers || {{}};
            if ('{auth_header}') {{
                headers['Authorization'] = 'Bearer [REDACTED]';
            }}

            return fetch(url, {{ ...options, headers }});
        }} catch (err) {{
            throw new Error('Fetch error: ' + err.message);
        }}
    }};

    // Sandbox environment
    const sandbox = {{
        console: sandboxConsole,
        fetch: sandboxFetch,
        setTimeout: setTimeout,
        setInterval: setInterval,
        Math: Math,
        Date: Date,
        JSON: JSON,
        Array: Array,
        Object: Object,
        String: String,
        Number: Number,
        Boolean: Boolean,
        Error: Error,
        RegExp: RegExp,
        Promise: Promise,
        Symbol: Symbol,
        Map: Map,
        Set: Set,
        WeakMap: WeakMap,
        WeakSet: WeakSet,
        results: results,
        process: {{
            env: {{
                NODE_ENV: 'sandbox'
            }}
        }},
        // Safe APIs
        btoa: btoa,
        atob: atob,
        encodeURIComponent: encodeURIComponent,
        decodeURIComponent: decodeURIComponent
    }};

    try {{
        // User code execution
        (async function(console, fetch, results) {{
            {user_code}
        }})(sandboxConsole, sandboxFetch, results);

        const executionTime = Date.now() - EXECUTION_START;
        process.stdout.write(JSON.stringify({{
            status: 'success',
            execution_time: executionTime,
            console_logs: consoleLogs,
            results: results
        }}));
    }} catch (error) {{
        const executionTime = Date.now() - EXECUTION_START;
        process.stderr.write(JSON.stringify({{
            status: 'error',
            error: error.message,
            stack: error.stack,
            execution_time: executionTime,
            console_logs: consoleLogs
        }}));
    }}
}})();
"""
        return sandbox_script


class JavaScriptExecutor:
    """Execute JavaScript code safely"""

    # Execution limits
    MAX_EXECUTION_TIME = 5000  # 5 seconds in milliseconds
    MAX_MEMORY_MB = 128  # 128 MB limit
    MAX_OUTPUT_SIZE = 1024 * 1024  # 1 MB output limit

    @staticmethod
    def execute(
        code: str,
        timeout_ms: int = None,
        api_token: str = None
    ) -> ExecutionResult:
        """
        Execute JavaScript code safely in sandbox

        Args:
            code: JavaScript code to execute
            timeout_ms: Execution timeout in milliseconds
            api_token: Optional API token for fetch requests

        Returns:
            ExecutionResult with output, status, and execution time
        """
        start_time = time.time()
        timeout_ms = timeout_ms or JavaScriptExecutor.MAX_EXECUTION_TIME

        # Validate code
        is_valid, error_msg = CodeValidator.validate(code)
        if not is_valid:
            return ExecutionResult(
                status=ExecutionStatus.VALIDATION_ERROR,
                output="",
                error=error_msg,
                execution_time=0
            )

        # Create sandbox script
        sandbox_script = SandboxEnvironment.create_sandbox_script(code, api_token)

        # Execute in Node.js
        try:
            # Create temporary file for script
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.js',
                delete=False,
                encoding='utf-8'
            ) as tmp_file:
                tmp_file.write(sandbox_script)
                tmp_file_path = tmp_file.name

            try:
                # Run with timeout
                result = subprocess.run(
                    ['node', tmp_file_path],
                    capture_output=True,
                    timeout=timeout_ms / 1000.0,  # Convert to seconds
                    text=True
                )

                execution_time = time.time() - start_time

                # Parse output
                if result.returncode == 0 and result.stdout:
                    try:
                        # Try to extract JSON from the last line
                        lines = result.stdout.strip().split('\n')
                        # Find the JSON object (usually the last thing printed)
                        json_str = None
                        for line in reversed(lines):
                            if line.startswith('{'):
                                json_str = line
                                break

                        if json_str:
                            output_data = json.loads(json_str)
                            return ExecutionResult(
                                status=ExecutionStatus.SUCCESS,
                                output=result.stdout,
                                console_logs=output_data.get('console_logs', []),
                                return_value=output_data.get('results'),
                                execution_time=execution_time
                            )
                        else:
                            return ExecutionResult(
                                status=ExecutionStatus.SUCCESS,
                                output=result.stdout,
                                console_logs=[result.stdout],
                                execution_time=execution_time
                            )
                    except json.JSONDecodeError:
                        return ExecutionResult(
                            status=ExecutionStatus.SUCCESS,
                            output=result.stdout,
                            console_logs=[result.stdout],
                            execution_time=execution_time
                        )
                elif result.stderr:
                    try:
                        error_data = json.loads(result.stderr)
                        return ExecutionResult(
                            status=ExecutionStatus.ERROR,
                            output=result.stderr,
                            error=error_data.get('error', 'Unknown error'),
                            console_logs=error_data.get('console_logs', []),
                            execution_time=execution_time
                        )
                    except json.JSONDecodeError:
                        return ExecutionResult(
                            status=ExecutionStatus.ERROR,
                            output=result.stderr,
                            error=result.stderr,
                            execution_time=execution_time
                        )
                else:
                    return ExecutionResult(
                        status=ExecutionStatus.SUCCESS,
                        output="Code executed successfully (no output)",
                        execution_time=execution_time
                    )

            except subprocess.TimeoutExpired:
                execution_time = time.time() - start_time
                return ExecutionResult(
                    status=ExecutionStatus.TIMEOUT,
                    output="",
                    error=f"Execution timeout (>{timeout_ms}ms)",
                    execution_time=execution_time
                )

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Code execution error: {str(e)}")
            return ExecutionResult(
                status=ExecutionStatus.ERROR,
                output="",
                error=str(e),
                execution_time=execution_time
            )

        finally:
            # Cleanup temporary file
            try:
                if 'tmp_file_path' in locals():
                    os.unlink(tmp_file_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file: {str(e)}")


# Code template library
CODE_TEMPLATES = {
    "hello_world": {
        "name": "Hello World",
        "description": "Simple console output",
        "code": """console.log('Hello, World!');"""
    },
    "fetch_data": {
        "name": "Fetch Data",
        "description": "Fetch data from an API endpoint",
        "code": """// Fetch data from API
const response = await fetch('/api/data');
const data = await response.json();
console.log('Fetched items:', data.length);
results.data = data;"""
    },
    "process_array": {
        "name": "Process Array",
        "description": "Transform array data",
        "code": """// Process array data
const items = [
    { id: 1, name: 'Item 1', value: 100 },
    { id: 2, name: 'Item 2', value: 200 },
    { id: 3, name: 'Item 3', value: 150 }
];

const processed = items
    .filter(item => item.value > 100)
    .map(item => ({
        id: item.id,
        name: item.name.toUpperCase(),
        doubled_value: item.value * 2
    }));

console.log('Processed items:', JSON.stringify(processed, null, 2));
results.processed = processed;"""
    },
    "loop_example": {
        "name": "Loop Example",
        "description": "Iterate over data with control flow",
        "code": """// Loop example
const numbers = [1, 2, 3, 4, 5];
let sum = 0;

for (const num of numbers) {
    sum += num;
    if (num % 2 === 0) {
        console.log(`${num} is even`);
    }
}

console.log('Sum:', sum);
results.sum = sum;"""
    },
    "error_handling": {
        "name": "Error Handling",
        "description": "Handle errors gracefully",
        "code": """// Error handling example
try {
    const data = JSON.parse('{"invalid json"');
} catch (error) {
    console.error('JSON parse error:', error.message);
    results.error = error.message;
}

try {
    const response = await fetch('https://api.example.com/data');
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    console.log('Success:', data);
} catch (error) {
    console.error('Fetch failed:', error.message);
}"""
    },
    "conditional_logic": {
        "name": "Conditional Logic",
        "description": "Use if/else conditions",
        "code": """// Conditional logic
const score = 85;

if (score >= 90) {
    console.log('Grade: A');
    results.grade = 'A';
} else if (score >= 80) {
    console.log('Grade: B');
    results.grade = 'B';
} else if (score >= 70) {
    console.log('Grade: C');
    results.grade = 'C';
} else {
    console.log('Grade: F');
    results.grade = 'F';
}"""
    },
    "data_validation": {
        "name": "Data Validation",
        "description": "Validate and sanitize input",
        "code": """// Data validation
const validateEmail = (email) => {
    const regex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
    return regex.test(email);
};

const validatePhoneNumber = (phone) => {
    const regex = /^[0-9\\-+\\s()]{7,}$/;
    return regex.test(phone);
};

const testEmails = ['user@example.com', 'invalid.email', 'test@domain.co.uk'];
const testPhones = ['123-456-7890', '(123) 456 7890', 'invalid'];

results.emailValidation = testEmails.map(email => ({
    email,
    valid: validateEmail(email)
}));

results.phoneValidation = testPhones.map(phone => ({
    phone,
    valid: validatePhoneNumber(phone)
}));

console.log('Validation complete');"""
    },
    "data_aggregation": {
        "name": "Data Aggregation",
        "description": "Aggregate and summarize data",
        "code": """// Data aggregation
const sales = [
    { product: 'A', amount: 100, date: '2024-01-01' },
    { product: 'B', amount: 150, date: '2024-01-01' },
    { product: 'A', amount: 200, date: '2024-01-02' },
    { product: 'C', amount: 75, date: '2024-01-02' }
];

const byProduct = sales.reduce((acc, sale) => {
    if (!acc[sale.product]) {
        acc[sale.product] = { total: 0, count: 0 };
    }
    acc[sale.product].total += sale.amount;
    acc[sale.product].count += 1;
    return acc;
}, {});

const summary = Object.entries(byProduct).map(([product, data]) => ({
    product,
    total_sales: data.total,
    average_sale: (data.total / data.count).toFixed(2),
    transaction_count: data.count
}));

console.log('Sales Summary:', JSON.stringify(summary, null, 2));
results.summary = summary;"""
    }
}
