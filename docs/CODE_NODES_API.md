# 🔌 Custom Code Nodes - API Reference

> **Purpose**: Validate JavaScript code before execution.
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Custom Code Nodes - API Reference 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

## Endpoints

### POST /api/ai-automation/code/validate

Validate JavaScript code before execution.

**Authentication:** Required (Bearer token)

**Request:**
```json
{
  "code": "console.log('Hello, World!');"
}
```

**Response (Valid):**
```json
{
  "valid": true,
  "error": null
}
```

**Response (Invalid):**
```json
{
  "valid": false,
  "error": "Unmatched curly braces"
}
```

**Status Codes:**
- `200` - Validation result returned
- `401` - Unauthorized
- `403` - Forbidden (insufficient subscription)

**Example cURL:**
```bash
curl -X POST http://localhost:8000/api/ai-automation/code/validate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code": "console.log(\"test\");"}'
```

---

### POST /api/ai-automation/code/execute

Execute JavaScript code in a secure sandbox.

**Authentication:** Required (Bearer token)

**Request:**
```json
{
  "code": "const x = 5 + 3; results.sum = x; console.log('Sum:', x);",
  "timeout_ms": 5000
}
```

**Response (Success):**
```json
{
  "status": "success",
  "output": "...",
  "error": null,
  "execution_time": 0.234,
  "console_logs": ["Sum: 8"],
  "return_value": {
    "sum": 8
  }
}
```

**Response (Error):**
```json
{
  "status": "error",
  "output": "...",
  "error": "ReferenceError: undefined variable",
  "execution_time": 0.045,
  "console_logs": [],
  "return_value": null
}
```

**Status Codes:**
- `200` - Code executed (check status field)
- `400` - Validation error or bad request
- `401` - Unauthorized
- `403` - Forbidden (insufficient subscription)

**Execution Statuses:**
- `success` - Code executed successfully
- `error` - Runtime error occurred
- `timeout` - Execution exceeded timeout
- `validation_error` - Code failed validation
- `memory_limit` - Memory limit exceeded

**Timeout Parameters:**
- `timeout_ms`: Execution timeout in milliseconds (optional, default: 5000)
- Allowed range: 1000 - 30000 ms
- Code is terminated if execution exceeds timeout

**Example cURL:**
```bash
curl -X POST http://localhost:8000/api/ai-automation/code/execute \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "const result = 10 * 5; results.answer = result; console.log(result);",
    "timeout_ms": 5000
  }'
```

**Example JavaScript:**
```javascript
async function executeCode(code, token) {
  const response = await fetch('/api/ai-automation/code/execute', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ code, timeout_ms: 5000 })
  });

  const result = await response.json();

  if (result.status === 'success') {
    console.log('Execution successful');
    console.log('Output:', result.console_logs);
    console.log('Results:', result.return_value);
  } else {
    console.error('Execution failed:', result.error);
  }

  return result;
}
```

---

### GET /api/ai-automation/code/templates

Get list of available code templates.

**Authentication:** Required (Bearer token)

**Response:**
```json
{
  "templates": [
    {
      "id": "hello_world",
      "name": "Hello World",
      "description": "Simple console output - perfect for testing"
    },
    {
      "id": "fetch_data",
      "name": "Fetch Data from API",
      "description": "Fetch data from an API endpoint and process it"
    },
    {
      "id": "process_array",
      "name": "Process Array Data",
      "description": "Transform and filter array data"
    }
  ]
}
```

**Status Codes:**
- `200` - Templates returned
- `401` - Unauthorized
- `403` - Forbidden (insufficient subscription)

**Example cURL:**
```bash
curl -X GET http://localhost:8000/api/ai-automation/code/templates \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### GET /api/ai-automation/code/templates/{template_id}

Get specific code template with full code.

**Authentication:** Required (Bearer token)

**URL Parameters:**
- `template_id` - Template identifier (e.g., `hello_world`, `fetch_data`)

**Response:**
```json
{
  "id": "hello_world",
  "name": "Hello World",
  "description": "Simple console output - perfect for testing",
  "code": "console.log('Hello, World!');"
}
```

**Status Codes:**
- `200` - Template returned
- `401` - Unauthorized
- `403` - Forbidden (insufficient subscription)
- `404` - Template not found

**Example cURL:**
```bash
curl -X GET http://localhost:8000/api/ai-automation/code/templates/hello_world \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Template IDs:**
- `hello_world` - Hello World
- `fetch_data` - Fetch Data from API
- `process_array` - Process Array Data
- `loop_example` - Loop Examples
- `error_handling` - Error Handling
- `conditional_logic` - Conditional Logic
- `data_validation` - Data Validation
- `data_aggregation` - Data Aggregation
- `async_await` - Async/Await Pattern
- `object_manipulation` - Object Manipulation
- `string_operations` - String Operations
- `mathematical_operations` - Mathematical Operations

---

## Global Objects

### console

Logging interface for debugging.

```javascript
console.log(...args)      // Log info message
console.error(...args)    // Log error message
console.warn(...args)     // Log warning message
console.info(...args)     // Log info message
```

**Example:**
```javascript
console.log('Value:', 42);
console.error('Something went wrong');
```

### results

Object to store execution results returned to caller.

```javascript
results.myValue = 42;
results.myArray = [1, 2, 3];
results.myObject = { key: 'value' };
```

### fetch

HTTP request function for API calls.

```javascript
// GET request
const response = await fetch('/api/data');
const data = await response.json();

// POST request
const response = await fetch('/api/data', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name: 'John' })
});
```

**Allowed Hosts:**
- `localhost`
- `127.0.0.1`
- `api.example.com`
- `jsonplaceholder.typicode.com`

### Standard Objects

Available from JavaScript standard library:

```javascript
Math           // Math operations (sqrt, random, etc.)
Date           // Date/time (new Date(), getTime(), etc.)
JSON           // JSON parsing (parse, stringify)
Array          // Array constructor
Object         // Object constructor
String         // String constructor
Number         // Number constructor
Boolean        // Boolean constructor
Error          // Error constructor
RegExp         // Regular expressions
Promise        // Promises
Map            // Map collection
Set            // Set collection
Symbol         // Symbol primitive
```

---

## Error Handling

### Validation Errors

Code is validated before execution. Common validation errors:

| Error | Cause | Solution |
|-------|-------|----------|
| "Code cannot be empty" | No code provided | Enter some code |
| "Code exceeds maximum length" | Code > 10 KB | Split code into smaller parts |
| "Unmatched curly braces" | Missing `}` | Check brace balance |
| "Unmatched square brackets" | Missing `]` | Check bracket balance |
| "Unmatched parentheses" | Missing `)` | Check parenthesis balance |
| "Dangerous pattern detected" | Uses banned functions | Avoid require, eval, etc. |

### Runtime Errors

Errors that occur during execution:

```javascript
// ReferenceError - variable not defined
console.log(undefinedVar);  // Error: undefinedVar is not defined

// TypeError - wrong type
null.someProperty;  // Error: Cannot read property

// SyntaxError - invalid syntax
const x = {invalid};  // Error: Unexpected token
```

### Timeout Errors

Code execution exceeds timeout (default 5 seconds):

```json
{
  "status": "timeout",
  "error": "Execution timeout (>5000ms)",
  "execution_time": 5.001,
  "console_logs": []
}
```

---

## Rate Limits

### Per-User Limits

- **Concurrent executions:** 5 maximum
- **Hourly executions:** 100 maximum
- **Daily executions:** 1000 maximum

### Per-Execution Limits

- **Time limit:** 5 seconds default, 30 seconds max
- **Code size:** 10 KB maximum
- **Memory:** 128 MB per execution
- **Output size:** 1 MB maximum

### Subscription Tiers

| Feature | Starter | Ambassador | Enterprise |
|---------|---------|-----------|------------|
| Code nodes | Included | Included | Included |
| Monthly executions | 100 | 500 | Unlimited |
| Max timeout | 5s | 10s | 30s |
| Concurrent executions | 1 | 3 | 5 |

---

## Authentication

All endpoints require Bearer token authentication.

**Header Format:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**How to get a token:**
1. Log in to SoftFactory
2. Navigate to Settings → API Keys
3. Generate new API key or use session token

---

## Examples

### Example 1: Simple Calculation

**Request:**
```bash
curl -X POST http://localhost:8000/api/ai-automation/code/execute \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "const result = 10 * 5; results.answer = result; console.log(\"10 * 5 =\", result);"
  }'
```

**Response:**
```json
{
  "status": "success",
  "output": "10 * 5 = 50",
  "error": null,
  "execution_time": 0.042,
  "console_logs": ["10 * 5 = 50"],
  "return_value": {
    "answer": 50
  }
}
```

### Example 2: Array Processing

**Request:**
```bash
curl -X POST http://localhost:8000/api/ai-automation/code/execute \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "const nums = [1,2,3,4,5]; const evens = nums.filter(n => n % 2 === 0); results.evens = evens; console.log(\"Evens:\", evens);"
  }'
```

**Response:**
```json
{
  "status": "success",
  "execution_time": 0.051,
  "console_logs": ["Evens: 2,4"],
  "return_value": {
    "evens": [2, 4]
  }
}
```

### Example 3: Error Handling

**Request:**
```bash
curl -X POST http://localhost:8000/api/ai-automation/code/execute \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "try { const x = JSON.parse(\"invalid\"); } catch(e) { console.error(\"JSON error:\", e.message); results.error = e.message; }"
  }'
```

**Response:**
```json
{
  "status": "success",
  "execution_time": 0.038,
  "console_logs": ["JSON error: Unexpected token i"],
  "return_value": {
    "error": "Unexpected token i"
  }
}
```

### Example 4: API Integration

**Request:**
```bash
curl -X POST http://localhost:8000/api/ai-automation/code/execute \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "async function demo() { const res = await fetch(\"https://jsonplaceholder.typicode.com/posts/1\"); const data = await res.json(); results.post = data; console.log(\"Post title:\", data.title); } await demo();"
  }'
```

**Response:**
```json
{
  "status": "success",
  "execution_time": 0.234,
  "console_logs": ["Post title: ..."],
  "return_value": {
    "post": {
      "userId": 1,
      "id": 1,
      "title": "...",
      "body": "..."
    }
  }
}
```

---

## Status Codes

### 2xx Success

| Code | Meaning |
|------|---------|
| 200 | Request successful, code executed or validated |
| 201 | Resource created |

### 4xx Client Error

| Code | Meaning |
|------|---------|
| 400 | Bad request, invalid input, or validation error |
| 401 | Missing or invalid authentication token |
| 403 | Insufficient permissions or subscription |
| 404 | Resource not found (template doesn't exist) |

### 5xx Server Error

| Code | Meaning |
|------|---------|
| 500 | Internal server error |

---

## Changelog

### v1.0.0 (2026-02-25)

- Initial release
- Code validation with security checks
- Sandboxed JavaScript execution
- 12 code templates
- Full console capture
- Error handling and reporting
- Performance monitoring
- 45+ test cases

---

## Support

For issues or questions:

1. Check the [Code Nodes Guide](./CODE_NODES_GUIDE.md)
2. Review [Code Examples](./CODE_NODES_GUIDE.md#code-examples)
3. Try [Templates](https://localhost:8000/api/ai-automation/code/templates)
4. Contact support with error details

---

**Last Updated:** 2026-02-25
**API Version:** 1.0.0