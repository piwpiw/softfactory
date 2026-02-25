# Custom Code Nodes - Quick Start Guide

Get started with Custom Code Nodes in AI Automation in just 5 minutes.

## 1. Access the Code Editor

1. Log in to SoftFactory
2. Go to **AI Automation**
3. Click **Custom Code**

You'll see the code editor with syntax highlighting and a template library.

## 2. Write Your First Code

**Option A: Use a Template**

Click any template in the right panel to load it:
- **Hello World** - Simple starting point
- **Fetch Data** - Call an API
- **Process Array** - Transform data

**Option B: Write Code Manually**

```javascript
// Log a message
console.log('Hello, World!');

// Create a variable
const message = 'AI Automation is awesome!';
console.log(message);

// Return a result
results.greeting = message;
```

## 3. Click Run

- Click the **Run** button (▶)
- Watch the console output in the bottom panel
- See execution time and results

## 4. Common Patterns

### Print Output

```javascript
console.log('Your message');
```

### Store Results

```javascript
results.myValue = 42;
results.myArray = [1, 2, 3];
results.myObject = { name: 'John' };
```

### Process Arrays

```javascript
const items = [1, 2, 3, 4, 5];
const doubled = items.map(x => x * 2);
const evens = items.filter(x => x % 2 === 0);
console.log('Doubled:', doubled);
results.doubled = doubled;
```

### Fetch Data

```javascript
const response = await fetch('/api/data');
const data = await response.json();
results.data = data;
```

### Error Handling

```javascript
try {
  // Your code
  const result = risky();
} catch (error) {
  console.error('Error:', error.message);
  results.error = error.message;
}
```

### Conditional Logic

```javascript
if (value > 100) {
  console.log('High value');
  results.level = 'high';
} else {
  console.log('Low value');
  results.level = 'low';
}
```

## 5. Available Functions

| Function | What It Does | Example |
|----------|-------------|---------|
| `console.log()` | Print message | `console.log('Hello')` |
| `console.error()` | Print error | `console.error('Failed')` |
| `fetch()` | Call API | `await fetch('/api/data')` |
| `JSON.parse()` | Parse JSON | `JSON.parse('{"x":1}')` |
| `Math.sqrt()` | Math function | `Math.sqrt(16)` |
| `Date.now()` | Current timestamp | `Date.now()` |

## 6. Tips & Tricks

### Save Your Code

Click **Save** to store code in your browser (localStorage):
```javascript
// Your code is automatically saved here
```

### Test Before Running

The editor validates syntax before execution:
- Checks for matching brackets `{}`, `[]`, `()`
- Blocks dangerous functions (require, eval, fs, etc.)
- Limits code to 10 KB

### Use Async/Await

```javascript
async function fetchData() {
  const res = await fetch('/api/data');
  return await res.json();
}

const data = await fetchData();
results.data = data;
```

### Debug with console.log

```javascript
const steps = ['start', 'process', 'finish'];
steps.forEach((step, i) => {
  console.log(`Step ${i}: ${step}`);
});
```

## 7. Common Errors & Solutions

| Error | Fix |
|-------|-----|
| "Unmatched braces" | Count `{` and `}` |
| "Undefined variable" | Check spelling |
| "Cannot read property" | Add null check |
| "Execution timeout" | Simplify code |
| "Dangerous pattern" | Avoid require(), eval() |

## 8. Performance

- **Execution time:** <500ms for typical code
- **Timeout:** 5 seconds default
- **Code limit:** 10 KB maximum
- **Memory:** 128 MB per execution

## 9. Full Documentation

For more details, see:
- [Complete Guide](./CODE_NODES_GUIDE.md)
- [API Reference](./CODE_NODES_API.md)

## 10. Example Code

### Customer Data Analysis

```javascript
const customers = [
  { name: 'Alice', purchases: 5 },
  { name: 'Bob', purchases: 12 },
  { name: 'Charlie', purchases: 3 }
];

// Find top customers
const topCustomers = customers.filter(c => c.purchases > 4);

// Count total
const totalPurchases = customers.reduce(
  (sum, c) => sum + c.purchases, 0
);

console.log('Top customers:', topCustomers.map(c => c.name));
console.log('Total purchases:', totalPurchases);

results.topCustomers = topCustomers;
results.totalPurchases = totalPurchases;
```

### Email Validation

```javascript
const validateEmail = (email) => {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
};

const emails = ['user@example.com', 'invalid', 'test@domain.co.uk'];
const valid = emails.filter(e => validateEmail(e));

console.log('Valid emails:', valid);
results.validEmails = valid;
```

### Data Processing

```javascript
const sales = [
  { product: 'A', amount: 100 },
  { product: 'B', amount: 150 },
  { product: 'A', amount: 200 }
];

// Group by product
const byProduct = sales.reduce((acc, sale) => {
  acc[sale.product] = (acc[sale.product] || 0) + sale.amount;
  return acc;
}, {});

console.log('Total by product:', byProduct);
results.salesByProduct = byProduct;
```

## Getting Help

1. **Check templates** - Click any template to see working examples
2. **Read the guide** - See [CODE_NODES_GUIDE.md](./CODE_NODES_GUIDE.md)
3. **View API docs** - See [CODE_NODES_API.md](./CODE_NODES_API.md)
4. **Contact support** - Reach out with your questions

---

**That's it!** You're ready to build custom automations with code.

Happy coding! 🚀
