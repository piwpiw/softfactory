# Custom JavaScript Code Nodes Guide

## Overview

Custom Code Nodes are a powerful feature of AI Automation that allows advanced users to write and execute custom JavaScript code in a secure sandbox environment. This unlocks unlimited customization possibilities for automation workflows.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Core Concepts](#core-concepts)
3. [API Reference](#api-reference)
4. [Code Examples](#code-examples)
5. [Safety & Security](#safety--security)
6. [Performance](#performance)
7. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Accessing the Code Editor

1. Navigate to **AI Automation → Custom Code** in SoftFactory
2. You'll see the code editor with syntax highlighting
3. Start writing JavaScript or select a template

### Basic Hello World

```javascript
console.log('Hello, World!');
```

Click **Run** to execute. You'll see the output in the console panel below.

### Using Templates

The template library provides ready-made code for common tasks:

- **Hello World** - Simple output
- **Fetch Data** - API calls
- **Process Array** - Data transformation
- **Loop Examples** - Iteration patterns
- **Error Handling** - Try-catch patterns
- **Conditional Logic** - If/else statements
- **Data Validation** - Input validation
- **Data Aggregation** - Summarization

Click any template to load it into the editor.

---

## Core Concepts

### Console Object

Log messages to see execution output:

```javascript
console.log('Info message');      // General output
console.error('Error message');   // Error logs (red)
console.warn('Warning message');  // Warnings (yellow)
console.info('Info message');     // Information (cyan)
```

### Results Object

Store execution results:

```javascript
results.myValue = 42;
results.myArray = [1, 2, 3];
results.myObject = { name: 'John', age: 30 };
```

The results object is returned after execution and can be used by subsequent nodes.

### Async/Await

Execute asynchronous operations:

```javascript
async function fetchUserData() {
    const response = await fetch('/api/users');
    const data = await response.json();
    return data;
}

const users = await fetchUserData();
console.log('Users:', users);
```

### Fetch API

Make HTTP requests (limited to safe domains):

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

**Allowed hosts:** `localhost`, `127.0.0.1`, `api.example.com`, `jsonplaceholder.typicode.com`

---

## API Reference

### Backend Routes

#### Validate Code
```
POST /api/ai-automation/code/validate
Headers:
  Authorization: Bearer <token>
  Content-Type: application/json

Body:
  {
    "code": "console.log('test');"
  }

Response:
  {
    "valid": true,
    "error": null
  }
```

#### Execute Code
```
POST /api/ai-automation/code/execute
Headers:
  Authorization: Bearer <token>
  Content-Type: application/json

Body:
  {
    "code": "console.log('test');",
    "timeout_ms": 5000
  }

Response:
  {
    "status": "success|error|timeout|validation_error",
    "output": "...",
    "error": null,
    "execution_time": 0.234,
    "console_logs": ["log1", "log2"],
    "return_value": { "key": "value" }
  }
```

#### Get Templates
```
GET /api/ai-automation/code/templates
Headers:
  Authorization: Bearer <token>

Response:
  {
    "templates": [
      {
        "id": "hello_world",
        "name": "Hello World",
        "description": "Simple console output"
      },
      ...
    ]
  }
```

#### Get Specific Template
```
GET /api/ai-automation/code/templates/{template_id}
Headers:
  Authorization: Bearer <token>

Response:
  {
    "id": "hello_world",
    "name": "Hello World",
    "description": "Simple console output",
    "code": "console.log('Hello, World!');"
  }
```

### Global Objects Available

```javascript
console       // Console object (log, error, warn, info)
fetch         // HTTP request function
results       // Object to store results
Math          // Math object
Date          // Date constructor
JSON          // JSON parser
Array         // Array constructor
Object        // Object constructor
String        // String constructor
Number        // Number constructor
Boolean       // Boolean constructor
Error         // Error constructor
RegExp        // RegExp constructor
Promise       // Promise constructor
Map           // Map constructor
Set           // Set constructor
Symbol        // Symbol constructor
```

---

## Code Examples

### Example 1: Process Customer Data

```javascript
const customers = [
    { id: 1, name: 'Alice', spent: 150 },
    { id: 2, name: 'Bob', spent: 200 },
    { id: 3, name: 'Charlie', spent: 100 }
];

// Filter high-value customers
const vip = customers.filter(c => c.spent > 120);

// Calculate total spent
const totalSpent = customers.reduce((sum, c) => sum + c.spent, 0);
const avgSpent = totalSpent / customers.length;

console.log(`Total spent: $${totalSpent}`);
console.log(`Average spent: $${avgSpent.toFixed(2)}`);
console.log(`VIP customers: ${vip.map(c => c.name).join(', ')}`);

results.vip = vip;
results.totalSpent = totalSpent;
results.avgSpent = avgSpent;
```

### Example 2: Validate Email List

```javascript
const validateEmail = (email) => {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
};

const emails = [
    'user@example.com',
    'invalid.email',
    'test@domain.co.uk'
];

const validation = emails.map(email => ({
    email,
    valid: validateEmail(email),
    domain: email.split('@')[1]
}));

console.log('Email Validation Results:');
validation.forEach(v => {
    const status = v.valid ? '✓' : '✗';
    console.log(`${status} ${v.email}`);
});

results.validation = validation;
```

### Example 3: Fetch and Process API Data

```javascript
async function fetchAndProcess() {
    try {
        // Fetch data from API
        const response = await fetch('/api/data');

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        // Process the data
        const processed = data
            .filter(item => item.active)
            .map(item => ({
                id: item.id,
                name: item.name.toUpperCase(),
                timestamp: new Date().toISOString()
            }));

        console.log(`Processed ${processed.length} items`);
        results.processed = processed;

        return processed;
    } catch (error) {
        console.error('Error:', error.message);
        results.error = error.message;
    }
}

await fetchAndProcess();
```

### Example 4: Generate Statistics

```javascript
const data = [
    { category: 'A', value: 100 },
    { category: 'B', value: 150 },
    { category: 'A', value: 200 },
    { category: 'C', value: 75 },
    { category: 'B', value: 125 }
];

// Group by category
const grouped = data.reduce((acc, item) => {
    if (!acc[item.category]) {
        acc[item.category] = [];
    }
    acc[item.category].push(item.value);
    return acc;
}, {});

// Calculate statistics
const stats = Object.entries(grouped).map(([category, values]) => ({
    category,
    count: values.length,
    sum: values.reduce((a, b) => a + b, 0),
    average: values.reduce((a, b) => a + b, 0) / values.length,
    min: Math.min(...values),
    max: Math.max(...values)
}));

console.log('Statistics by Category:');
stats.forEach(s => {
    console.log(`${s.category}: avg=${s.average.toFixed(2)}, min=${s.min}, max=${s.max}`);
});

results.statistics = stats;
```

### Example 5: Conditional Logic

```javascript
const score = 85;
let grade = '';

if (score >= 90) {
    grade = 'A';
} else if (score >= 80) {
    grade = 'B';
} else if (score >= 70) {
    grade = 'C';
} else {
    grade = 'F';
}

const feedback = score >= 80
    ? 'Great job!'
    : 'Keep trying!';

console.log(`Score: ${score} → Grade: ${grade}`);
console.log(`Feedback: ${feedback}`);

results.grade = grade;
results.feedback = feedback;
```

---

## Safety & Security

### What's NOT Allowed

Dangerous patterns are automatically blocked:

- **File System Access** - `fs`, `readFile`, `writeFile`
- **Process Access** - `process.env`, `process.exit`
- **Dynamic Code Execution** - `eval()`, `Function()`
- **Module Loading** - `require()`, `import`

### Validation Rules

Code is checked for:
- **Maximum Length:** 10 KB limit
- **Bracket Matching:** All braces must be balanced
- **Security Patterns:** No dangerous functions

### Sandbox Limitations

- Cannot access system files
- Cannot spawn processes
- Cannot modify Node.js internals
- Fetch requests limited to safe domains
- Environment variables not accessible

### Best Practices

1. **Validate Input** - Check data before processing
2. **Handle Errors** - Use try-catch for risky operations
3. **Log Progress** - Use console for debugging
4. **Timeout Awareness** - Code runs for max 5 seconds
5. **Memory Efficient** - Avoid infinite loops

---

## Performance

### Execution Time Limits

- **Default Timeout:** 5 seconds
- **Custom Timeout:** Specify `timeout_ms` in request
- **Maximum:** 30 seconds

### Performance Tips

1. **Avoid Nested Loops** - Use array methods instead
   ```javascript
   // ✓ Good: O(n)
   const names = people.map(p => p.name);

   // ✗ Slow: O(n²)
   for (const p of people) {
       for (const person of people) { /* ... */ }
   }
   ```

2. **Use Efficient Algorithms**
   ```javascript
   // ✓ Good: Filter once
   const active = items.filter(i => i.status === 'active');

   // ✗ Slow: Filter multiple times
   const active = items.filter(i => i.status === 'active').filter(i => i.value > 100);
   ```

3. **Reduce Array Operations**
   ```javascript
   // ✓ Good: Single pass with reduce
   const result = data.reduce((acc, item) => {
       acc.total += item.amount;
       acc.count += 1;
       return acc;
   }, { total: 0, count: 0 });
   ```

### Benchmark Results

| Operation | Time |
|-----------|------|
| Simple console.log | < 1ms |
| Fetch API call | 50-200ms |
| Process 1000 items | 10-50ms |
| Data aggregation | 20-100ms |

---

## Troubleshooting

### Code Validation Errors

**Error:** "Dangerous pattern detected"
- **Cause:** Code contains blocked functions
- **Solution:** Use sandbox-approved APIs only

**Error:** "Unmatched curly braces"
- **Cause:** Missing closing `}`
- **Solution:** Check brace balance in code

**Error:** "Code exceeds maximum length"
- **Cause:** Code is over 10 KB
- **Solution:** Split code into multiple nodes

### Execution Errors

**Error:** "Execution timeout"
- **Cause:** Code takes longer than 5 seconds
- **Solution:** Optimize algorithm or reduce data size

**Error:** "ReferenceError: undefined variable"
- **Cause:** Variable not declared
- **Solution:** Check variable spelling and scope

**Error:** "TypeError: Cannot read property"
- **Cause:** Accessing property on null/undefined
- **Solution:** Add null checks

### Common Issues

**Issue:** Results are empty
```javascript
// ✗ Wrong: Missing assignment to results
const value = 42;

// ✓ Correct: Assign to results object
results.value = 42;
```

**Issue:** Async code doesn't execute
```javascript
// ✗ Wrong: Forgetting await
const data = fetch('/api/data');

// ✓ Correct: Use await
const response = await fetch('/api/data');
const data = await response.json();
```

**Issue:** Console shows no output
```javascript
// ✗ Wrong: No logging
const result = data.filter(x => x.active);

// ✓ Correct: Log for visibility
const result = data.filter(x => x.active);
console.log('Filtered items:', result.length);
```

---

## Advanced Topics

### Using Promise.all for Parallel Requests

```javascript
async function fetchMultiple() {
    try {
        const [users, posts, comments] = await Promise.all([
            fetch('/api/users').then(r => r.json()),
            fetch('/api/posts').then(r => r.json()),
            fetch('/api/comments').then(r => r.json())
        ]);

        console.log(`Users: ${users.length}`);
        console.log(`Posts: ${posts.length}`);
        console.log(`Comments: ${comments.length}`);

        results.all = { users, posts, comments };
    } catch (error) {
        console.error('Failed to fetch:', error);
    }
}

await fetchMultiple();
```

### Complex Data Transformations

```javascript
const transactions = [
    { date: '2024-01-01', amount: 100, category: 'food' },
    { date: '2024-01-01', amount: 50, category: 'transport' },
    { date: '2024-01-02', amount: 200, category: 'food' }
];

// Group by date and category
const grouped = transactions.reduce((acc, tx) => {
    const key = `${tx.date}|${tx.category}`;
    if (!acc[key]) {
        acc[key] = { date: tx.date, category: tx.category, total: 0 };
    }
    acc[key].total += tx.amount;
    return acc;
}, {});

const summary = Object.values(grouped)
    .sort((a, b) => a.date.localeCompare(b.date));

console.log(JSON.stringify(summary, null, 2));
results.summary = summary;
```

### Error Recovery Patterns

```javascript
async function robustFetch(url, retries = 3) {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.warn(`Attempt ${i + 1} failed: ${error.message}`);
            if (i === retries - 1) {
                throw error;
            }
            // Wait before retry
            await new Promise(r => setTimeout(r, 1000 * (i + 1)));
        }
    }
}

try {
    const data = await robustFetch('/api/data');
    results.data = data;
} catch (error) {
    console.error('Failed after retries:', error.message);
    results.error = error.message;
}
```

---

## API Rate Limits

No specific rate limits for code execution, but:
- Maximum 5 concurrent executions per user
- Maximum 100 executions per hour
- Maximum 1000 executions per day

---

## Support

For issues or questions:
1. Check the **Troubleshooting** section
2. Review **Code Examples**
3. Try **Templates** for reference
4. Contact support with error message

---

**Last Updated:** 2026-02-25
**Version:** 1.0.0
