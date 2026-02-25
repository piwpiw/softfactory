# AI Automation: Create Your First Workflow (5-Minute Setup)

> **Goal:** Go from zero to creating your first AI automation workflow in 5 minutes
> **Skill Level:** Beginner
> **Time Required:** 5 minutes
> **Last Updated:** 2026-02-25

---

## ⚡ Step 1: Log In (30 seconds)

Navigate to **SoftFactory Dashboard**:
```
http://localhost:8000/web/platform/dashboard.html
```

**Demo Credentials:**
```
Email:    admin@softfactory.com
Password: admin123
```

Click **Login** → You'll see your dashboard.

---

## ✅ Step 2: Subscribe to AI Automation (30 seconds)

1. Find **AI Automation** card on your dashboard
2. Click **Subscribe** (or "View Details" if already subscribed)
3. You'll be redirected to AI Automation home page

**What you get:**
- Visual workflow builder (no code required)
- 50+ pre-built workflow templates
- Connect to any app (Slack, Email, Webhooks, etc.)
- AI-powered automation (uses GPT-4)
- Workflow versioning & rollback
- Team collaboration
- Execution history & logs
- Error handling & retries

---

## 🔨 Step 3: Understand Workflow Basics (60 seconds)

Every automation follows this pattern:

```
TRIGGER → CONDITION → ACTION → RESULT

Example:
"When email arrives with 'invoice' →
 Check if amount > $1000 →
 Send Slack alert →
 Save to database"
```

### **Key Components:**

| Component | Purpose | Example |
|-----------|---------|---------|
| **Trigger** | What starts the workflow | Email received, Time interval |
| **Condition** | When should it run | Amount > $1000, Author = "Boss" |
| **Action** | What to do | Send message, Create record |
| **Filter** | Skip unnecessary runs | Ignore test emails |

### **Pre-Built Templates:**

The platform includes templates for:

| Category | Examples |
|----------|----------|
| **Email** | Forward important emails to Slack, Auto-reply, Extract data from email |
| **Slack** | Post updates to channel, Create tasks from Slack messages, Send alerts |
| **Social Media** | Post to Twitter when blog publishes, Repost top Slack threads |
| **Data** | Save form submissions to database, Sync databases, Backup files |
| **Admin** | Send weekly reports, Auto-assign tickets, Clean up old data |

---

## 📝 Step 4: Create Your First Workflow (120 seconds)

### **Step 4A: Click "Create Workflow"**

You'll see the **Workflow Builder**:

```
┌──────────────────────────────────────┐
│ WORKFLOW BUILDER                     │
│                                      │
│ Workflow Name: [____________]        │
│                                      │
│ 🔴 Trigger                           │
│ └─ [Select a trigger ▼]              │
│                                      │
│ 🔵 Conditions (optional)             │
│ ├─ [Add condition]                   │
│ └─ [And / Or logic ▼]               │
│                                      │
│ 🟢 Actions                           │
│ ├─ [Add action 1]                    │
│ ├─ [Add action 2]                    │
│ └─ [Add more]                        │
│                                      │
│ [Save Draft] [Test] [Publish]       │
└──────────────────────────────────────┘
```

### **Step 4B: Pick a Trigger**

Let's create a simple workflow: **"Alert me in Slack when sales email arrives"**

1. Click **"Select a trigger"**
2. Choose **"Email Received"**
3. Configure:
   - From: Any address
   - Subject contains: (optional)
   - Body contains: (optional)

```
Trigger Configuration:
├─ Email from: [Any ▼]
├─ Subject contains: "sales" OR "quote" OR "order"
├─ Body contains: (leave blank)
└─ Only trigger if: Unread = Yes
```

### **Step 4C: Add Condition (Optional)**

Before running the action, check something:

Click **"Add Condition"** →

```
Condition: Subject contains "sales"
├─ Operator: [contains ▼]
├─ Value: "sales"
└─ [Add AND] [Add OR]
```

This means: "Only trigger if subject has 'sales' in it"

### **Step 4D: Add Action**

Click **"Add Action"** →

**Action #1: Send Slack Message**

```
Action Type: [Select... ▼] → Choose "Slack"
└─ Channel: [#sales ▼]
└─ Message: "New sales email from {{ email.from }}
              Subject: {{ email.subject }}
              Preview: {{ email.body | first 100 chars }}"
```

The `{{ }}` brackets are **variables** - they pull real data from your email.

**Action #2 (Optional): Create Database Entry**

```
Action Type: [Select... ▼] → Choose "Create Database Record"
└─ Table: "Sales_Leads"
└─ Fields:
    ├─ sender: {{ email.from }}
    ├─ subject: {{ email.subject }}
    ├─ date_received: {{ now() }}
    └─ status: "new"
```

### **Step 4E: Save & Publish**

Click **"Save Draft"** →

```
✅ WORKFLOW SAVED

Workflow: "Sales Email Alert"
Status: DRAFT
Trigger: Email received
Actions: 2 (Slack message + Database save)

Next: Click "Test" or "Publish"
```

Click **"Publish"** → Workflow goes live!

```
🚀 WORKFLOW PUBLISHED

Status: ACTIVE
├─ Listening for: Emails with "sales" in subject
├─ On trigger: Send Slack to #sales + save to database
├─ Last run: Never (waiting for first email)
├─ Executions: 0

Actions:
├─ [View Runs] (see execution history)
├─ [Edit] (modify workflow)
├─ [Disable] (pause workflow)
└─ [Delete] (remove workflow)
```

---

## ✨ Step 5: Test Your Workflow (90 seconds)

### **Option A: Automatic Test**

1. Click **"Test"** button
2. System shows: "Send test data?"
3. Click **"Send Test Data"**
4. Workflow runs with sample data
5. You see results immediately

```
✅ TEST RUN SUCCESSFUL

Trigger: Email received (sample data)
├─ From: test@example.com
├─ Subject: "sales inquiry"

Actions executed:
├─ ✅ Slack message sent (verified)
├─ ✅ Database record created (ID: 12345)
├─ Total execution time: 1.2 seconds

Results:
├─ Slack thread: https://slack.com/...
└─ DB record: [View]
```

### **Option B: Real Test**

1. Send yourself an email with "sales" in subject
2. Workflow triggers automatically
3. Check Slack channel for message
4. Check database for new record

Both confirm your workflow is working!

---

## 📊 Step 6: Monitor Workflow Execution (30 seconds)

Click **"View Runs"** on your workflow:

```
EXECUTION HISTORY: Sales Email Alert

Run #3 ✅ 2min ago
├─ Triggered by: Email from john@bigclient.com
├─ Subject: "sales inquiry - large order"
├─ Status: Success (all actions completed)
├─ Duration: 1.3 seconds
├─ Actions: Slack ✅, Database ✅

Run #2 ✅ 15min ago
├─ Triggered by: Email from sarah@company.com
├─ Subject: "sales meeting confirm"
├─ Status: Success
├─ Duration: 1.1 seconds

Run #1 ✅ 1hour ago
├─ Triggered by: Email from bob@client.com
├─ Subject: "sales questions"
├─ Status: Success
├─ Duration: 1.4 seconds

Summary:
├─ Total runs: 3
├─ Success rate: 100%
├─ Avg execution time: 1.3 seconds
├─ Last error: None
```

---

## 🎯 Your First Workflow Checklist

- [ ] Logged into SoftFactory dashboard
- [ ] Subscribed to AI Automation service
- [ ] Understood trigger → condition → action pattern
- [ ] Created workflow with email trigger
- [ ] Added Slack action
- [ ] Added database save action (optional)
- [ ] Published workflow
- [ ] Ran test to confirm it works
- [ ] Saw it execute on real data
- [ ] Checked execution history

---

## 💡 Pro Tips for Effective Workflows

### **Tip 1: Start Simple**
- First workflow: 1 trigger + 1 action
- After 1 week: Add conditions
- After 2 weeks: Add multiple actions
- Progress: Gradually increase complexity

### **Tip 2: Use Variables for Dynamic Data**
```
DON'T: "New email received"
DO: "New email from {{ email.from }} with subject '{{ email.subject }}'"

Variables available:
├─ {{ email.from }}          - Sender address
├─ {{ email.subject }}       - Email subject
├─ {{ email.body }}          - Email content
├─ {{ now() }}               - Current date/time
├─ {{ user.name }}           - Current user
└─ {{ trigger.timestamp }}   - When triggered
```

### **Tip 3: Error Handling**
Add what to do if action fails:

```
Action: Send Slack message
├─ If successful: Mark as done
├─ If fails:
│  ├─ Retry 3 times
│  ├─ Then: Send email to admin
│  └─ Log error for review
```

### **Tip 4: Schedule Workflows**
Not everything needs real-time triggers. Examples:

```
Weekly: Send Monday morning recap
├─ Trigger: Every Monday at 9am
├─ Action: Send Slack summary
└─ Data: Count activities from last week

Monthly: Cleanup old data
├─ Trigger: 1st of month at 2am
├─ Action: Delete records older than 90 days
└─ Notify: Send confirmation email

Daily: Backup important files
├─ Trigger: Every day at 3am
├─ Action: Archive files to S3
└─ Notify: Log backup completion
```

### **Tip 5: Test Before Publishing**
- Always run test first
- Check all variables replace correctly
- Verify action destinations exist
- Look at execution details for errors

---

## 🔗 10 Workflow Templates for Every Business

### **1. Lead Qualification (Sales)**
```
Trigger: Form submission
Condition: Company size > 100 people
Action: Add to CRM + Send welcome email + Alert sales team
```

### **2. Customer Support Ticketing (Support)**
```
Trigger: Email to support@yourcompany.com
Action: Create ticket + Auto-assign to team + Send confirmation
```

### **3. Social Media Publishing (Marketing)**
```
Trigger: Blog post published
Action: Auto-post to Twitter + Facebook + LinkedIn + Slack notification
```

### **4. Data Synchronization (Operations)**
```
Trigger: Record created in Database A
Condition: Type = "Customer"
Action: Sync to Database B + Update CRM + Send webhook
```

### **5. Slack Notifications (Team)**
```
Trigger: Daily at 9am
Action: Pull metrics from database + Format message + Post to #daily-standup
```

### **6. Email Campaign Trigger (Marketing)**
```
Trigger: User visits pricing page 3 times
Action: Add to email list + Send "Questions?" email + Add tag
```

### **7. Invoice Processing (Finance)**
```
Trigger: Invoice email received
Condition: Amount > $500
Action: Create expense + Alert finance team + Save to file storage
```

### **8. Feedback Collection (Product)**
```
Trigger: Customer clicks "happy" emoji on page
Action: Send feedback form + Add to database + Alert product team
```

### **9. Data Export Schedule (Analytics)**
```
Trigger: Every Friday at 5pm
Action: Export weekly data + Create CSV + Email to stakeholders
```

### **10. Error Monitoring (DevOps)**
```
Trigger: Error log created (from app)
Condition: Severity = "Critical"
Action: Page on-call engineer + Open Slack thread + Create ticket
```

---

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| **"Workflow never triggers"** | Check trigger condition - might be too specific |
| **"Variables not working"** | Use `{{ }}` format, check spelling (case sensitive) |
| **"Action failing silently"** | Click "View Runs" to see error message, check logs |
| **"Too many notifications"** | Add more specific condition, or increase trigger threshold |
| **"Wrong data in action"** | Verify variable names, test with sample data |

---

## 📞 Common Questions

**Q: Can workflows run in parallel or only one at a time?**
> They run in parallel! If 3 emails arrive, 3 workflows execute simultaneously.

**Q: How often can workflows trigger?**
> No limit. Can trigger 100x per minute if needed. You only pay for execution.

**Q: Can I edit a published workflow?**
> Yes! Click "Edit" → Change settings → Click "Update" (versions auto-saved).

**Q: What happens if an action fails?**
> Workflow stops. You'll see error in execution logs. Configure retries for critical workflows.

**Q: Can workflows talk to each other?**
> Yes! Use webhooks. Workflow A can trigger Workflow B when it completes.

---

## 🚀 Next Steps After First Workflow

### **Week 1:**
- [ ] Create 1 simple workflow (email → Slack)
- [ ] Verify it works on real data
- [ ] Monitor execution logs
- [ ] Share with team

### **Week 2:**
- [ ] Create 2nd workflow with conditions
- [ ] Test error handling
- [ ] Document workflow for team
- [ ] Measure time saved

### **Week 3:**
- [ ] Create workflow with multiple actions
- [ ] Use variables extensively
- [ ] Set up failure notifications
- [ ] Schedule recurring workflows

### **Month 2:**
- [ ] Create 5+ workflows across team
- [ ] Calculate total time saved
- [ ] Optimize most-used workflows
- [ ] Plan advanced features (loops, parallel execution)

---

## 📚 Learn More

- **Full AI Automation Guide:** [docs/AI_AUTOMATION_PROTOCOL.md](/docs/)
- **Advanced Workflow Patterns:** [docs/AUTOMATION_PATTERNS.md](/docs/)
- **Integration Library:** [docs/INTEGRATIONS.md](/docs/)
- **Contact Support:** support@softfactory.com

---

## 🎉 Congratulations!

You've successfully created your first AI automation! You're now saving time by letting machines handle repetitive tasks.

**Time to celebrate:** Calculate how many hours this workflow will save. Multiply by your hourly rate. That's your ROI!

---

**Questions?** Hit the support chat in the bottom-right corner. Real humans respond within 2 hours.

