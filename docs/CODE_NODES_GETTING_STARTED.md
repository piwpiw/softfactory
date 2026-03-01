# 📝 Getting Started with Custom Code Nodes

> **Purpose**: Welcome to Custom Code Nodes for AI Automation! This guide will help you get started in just a few minutes.
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 Getting Started with Custom Code Nodes 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

Welcome to Custom Code Nodes for AI Automation! This guide will help you get started in just a few minutes.

## What Are Custom Code Nodes?

Custom Code Nodes allow you to write and execute custom JavaScript code in a secure sandbox environment. Perfect for:
- Complex data processing
- Custom validation rules
- API integration
- Data transformation
- Automation workflows

## Access the Feature

1. **Log in** to SoftFactory (http://localhost:8000)
2. Navigate to **AI Automation → Custom Code**
3. You'll see the code editor with built-in templates

## Your First Program

### Step 1: Simple Output

Copy this code into the editor:

```javascript
console.log('Hello, Code Nodes!');
```

Click **Run** → You'll see the output in the console below.

### Step 2: Do Math

```javascript
const x = 10;
const y = 5;
const sum = x + y;
console.log('Result:', sum);
results.answer = sum;
```

Click **Run** → The result is stored in `results.answer`

### Step 3: Use a Template

1. Look at the **Templates** panel on the right
2. Click **"Process Array Data"**
3. Click **Run** to execute
4. See the results in the console

## Common Tasks

### Process a List

```javascript
const items = [10, 20, 30, 40, 50];
const doubled = items.map(x => x * 2);
const sum = doubled.reduce((a, b) => a + b, 0);

console.log('Doubled:', doubled);
console.log('Sum:', sum);
results.doubled = doubled;
results.sum = sum;
```

### Validate Email

```javascript
const validateEmail = (email) => {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
};

const emails = ['user@example.com', 'invalid', 'test@domain.co.uk'];
results.valid = emails.filter(e => validateEmail(e));
console.log('Valid:', results.valid);
```

### Check Conditions

```javascript
const score = 85;

if (score >= 90) {
    results.grade = 'A';
} else if (score >= 80) {
    results.grade = 'B';
} else {
    results.grade = 'C';
}

console.log('Grade:', results.grade);
```

### Fetch Data (Async)

```javascript
async function demo() {
    try {
        // Fetch from API
        const response = await fetch('/api/ai-automation/employees');
        const data = await response.json();

        console.log('Data received:', data);
        results.data = data;
    } catch (error) {
        console.error('Error:', error.message);
    }
}

await demo();
```

## Tips

### 1. Save Your Code
Click **Save** to store code locally (in your browser)

### 2. Check Syntax
The editor validates syntax automatically. Errors will show before you run.

### 3. Use Console
```javascript
console.log('Info message');     // Light gray
console.error('Error message');  // Red
console.warn('Warning');         // Yellow
```

### 4. Store Results
```javascript
results.myValue = 42;
results.myArray = [1, 2, 3];
results.myObject = {name: 'John'};
```

### 5. Use Built-in Objects
```javascript
Math.sqrt(16)           // = 4
Date.now()              // Current timestamp
JSON.parse('{...}')     // Parse JSON
JSON.stringify(obj)     // Convert to JSON
```

## Debugging

### See What's Happening
```javascript
const data = [1, 2, 3];
console.log('Data:', data);

const processed = data.map(x => x * 2);
console.log('Processed:', processed);
```

### Catch Errors
```javascript
try {
    // Your code
    const result = risky();
} catch (error) {
    console.error('Failed:', error.message);
}
```

### Check Variables
```javascript
const myVar = 'test';
console.log('Variable value:', myVar);
console.log('Variable type:', typeof myVar);
console.log('Is null?', myVar === null);
```

## Common Errors & Solutions

| Error | Cause | Fix |
|-------|-------|-----|
| "undefined is not defined" | Typo in variable name | Check spelling |
| "Cannot read property" | Using null/undefined | Add safety check |
| "Unexpected token" | Syntax error | Check parentheses/brackets |
| "Execution timeout" | Code takes too long | Optimize algorithm |

## Templates Available

Click any template in the right panel:

1. **Hello World** - Start here
2. **Fetch Data** - Call APIs
3. **Process Array** - Transform data
4. **Loop Examples** - Iterate data
5. **Error Handling** - Try-catch patterns
6. **Conditional Logic** - If/else statements
7. **Data Validation** - Validate input
8. **Data Aggregation** - Summarize data
9. **Async/Await** - Async operations
10. **Object Manipulation** - Work with objects
11. **String Operations** - Text manipulation
12. **Math Operations** - Calculations

## What's Available

### Built-in Objects
```javascript
Math           // sqrt, round, min, max, random
Date           // now, getTime, getFullYear
JSON           // parse, stringify
Array          // methods like map, filter, reduce
Object         // keys, values, entries
String         // methods like split, trim, includes
RegExp         // regular expressions
Map, Set       // collections
Promise        // async operations
```

### Functions
```javascript
console.log()          // Output
fetch()                // HTTP requests
setTimeout()           // Delay execution
Math.sqrt()            // Square root
Array.map()            // Transform array
Array.filter()         // Filter array
Array.reduce()         // Aggregate
String.split()         // Split string
JSON.parse()           // Parse JSON
JSON.stringify()       // Convert to JSON
```

## Limitations

- **Code size:** Maximum 10 KB
- **Execution time:** Default 5 seconds (configurable)
- **Memory:** 128 MB per execution
- **Network:** Limited to safe domains (no unrestricted internet)
- **No file system access:** Cannot read/write files
- **No dangerous functions:** require(), eval() blocked

## More Help

- **Complete Guide:** See [CODE_NODES_GUIDE.md](./CODE_NODES_GUIDE.md)
- **API Reference:** See [CODE_NODES_API.md](./CODE_NODES_API.md)
- **Quick Tips:** See [CODE_NODES_QUICK_START.md](./CODE_NODES_QUICK_START.md)

## Next Steps

1. **Try the examples above** - Copy and run them
2. **Explore templates** - Click templates to see working code
3. **Modify code** - Change values and see results
4. **Build your own** - Start with a template and customize
5. **Check documentation** - Read guides for advanced usage

## Example Workflow

### Create an Automation

1. **Open Custom Code** in AI Automation
2. **Load a template** (e.g., "Process Array")
3. **Modify for your data** - Change variables
4. **Test** - Click Run to verify
5. **Save** - Store the code
6. **Use in workflow** - Reference from other nodes

### Build Custom Logic

```javascript
// 1. Load some data
const data = [
    { name: 'Alice', score: 85 },
    { name: 'Bob', score: 92 },
    { name: 'Charlie', score: 78 }
];

// 2. Process it
const results_data = data
    .filter(person => person.score >= 80)
    .map(person => ({
        name: person.name.toUpperCase(),
        passed: person.score >= 80
    }))
    .sort((a, b) => a.name.localeCompare(b.name));

// 3. Output
console.log('Results:', results_data);
results.passing = results_data;
```

## Best Practices

1. **Start Simple** - Write small pieces first
2. **Test Each Step** - Verify intermediate results
3. **Use Console** - Log to understand flow
4. **Handle Errors** - Use try-catch
5. **Check Null** - Prevent undefined errors
6. **Comment Code** - Explain complex logic
7. **Reuse Templates** - Start with examples

## Support

Need help?

1. **Check templates** - Click any template for examples
2. **Read guides** - See documentation files
3. **Debug code** - Use console.log to trace
4. **Simplify** - Break complex code into steps

---

**Ready to code? Open Custom Code and start building!**

Questions? Check the [Complete Guide](./CODE_NODES_GUIDE.md) or [API Reference](./CODE_NODES_API.md).