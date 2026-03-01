# 📖 SoftFactory Platform — User Manual

> **Purpose**: **Version:** 1.0
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 SoftFactory Platform — User Manual 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

**Version:** 1.0
**Date:** 2026-02-25
**Last Updated:** 2026-02-25

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Login & Authentication](#login--authentication)
3. [Main Dashboard](#main-dashboard)
4. [CooCook - Chef Booking Service](#coocook---chef-booking-service)
5. [SNS Auto - Social Media Automation](#sns-auto---social-media-automation)
6. [Review Campaign - Customer Reviews](#review-campaign---customer-reviews)
7. [AI Automation - Workflow Automation](#ai-automation---workflow-automation)
8. [WebApp Builder - No-Code Platform](#webapp-builder---no-code-platform)
9. [Account & Settings](#account--settings)
10. [Troubleshooting](#troubleshooting)
11. [FAQ](#faq)

---

## Getting Started

### System Requirements

- **Web Browser:** Chrome, Firefox, Safari, Edge (latest version)
- **Internet Connection:** Broadband (5 Mbps minimum)
- **Device:** Desktop, laptop, or tablet
- **Optional:** Mobile app (iOS/Android - coming soon)

### First Time Login

1. **Visit the platform:** `http://localhost:8000/web/platform/login.html`
2. **Enter passkey:** `demo2026`
3. **Click "Enter"**
4. **Explore demo features** with pre-loaded sample data

### Demo Accounts

| Role | Email | Password | Access |
|------|-------|----------|--------|
| Admin | admin@softfactory.com | admin123 | All features |
| Demo User | demo@softfactory.com | demo123 | Limited features |

---

## Login & Authentication

### Using Passkey (Demo)

**Quickest way to explore:**

1. Go to login page
2. Enter passkey: `demo2026`
3. Click "Enter" (no username/password needed)
4. Full access to all demo features

### Using Email & Password

**For registered users:**

1. Go to login page
2. Click "Sign up" to create account OR enter existing email/password
3. Verify email (check inbox)
4. Set password (8+ characters, mix of letters/numbers)
5. Login with credentials

### Password Requirements

- ✅ Minimum 8 characters
- ✅ At least 1 uppercase letter (A-Z)
- ✅ At least 1 number (0-9)
- ✅ At least 1 special character (!@#$%^&*)

**Example:** `MyPassword@2026`

### Session Security

- Sessions expire after 24 hours
- Click "Logout" to end session immediately
- Clear browser cookies for full logout
- Never share your password with anyone

---

## Main Dashboard

### Dashboard Overview

Your personal command center showing:
- **Quick Stats:** Total bookings, campaigns, posts, workflows
- **Upcoming Events:** Scheduled activities this week
- **Recent Activity:** Last 10 actions performed
- **Notifications:** New messages and updates

### Dashboard Navigation

| Section | Purpose | Access |
|---------|---------|--------|
| CooCook | Book chefs for events | Main menu |
| SNS Auto | Schedule social posts | Main menu |
| Review | Manage review campaigns | Main menu |
| AI Auto | Create workflows | Main menu |
| WebApp | Build websites | Main menu |
| Settings | Account management | Top right menu |

### Quick Actions

- **+ New Booking** — Book a chef
- **+ New Campaign** — Create review campaign
- **+ New Post** — Schedule social media post
- **+ New Workflow** — Create automation
- **+ New Website** — Start website project

---

## CooCook - Chef Booking Service

### What is CooCook?

Connect with professional chefs for:
- Corporate catering
- Private dinners
- Cooking classes
- Menu consultation
- Special event preparation

### How to Book a Chef

#### Step 1: Browse Chefs

1. Click **"CooCook"** from main menu
2. See list of available chefs with photos, ratings, specialties
3. Filter by:
   - **Cuisine:** Italian, Japanese, Korean, French, etc.
   - **Price:** Budget, Standard, Premium
   - **Rating:** 4.5★+, 4.0★+, All
   - **Availability:** This week, Next week, Custom date

#### Step 2: View Chef Profile

1. Click on chef card
2. See full profile:
   - Professional photo
   - Bio & experience
   - Specialties (cuisines, dietary accommodations)
   - Rating & reviews (from previous clients)
   - Pricing & availability
   - Portfolio (photos of past events)

#### Step 3: Send Booking Request

1. Click **"Request Booking"**
2. Fill in details:
   - **Date & Time:** When you need the chef
   - **Duration:** How many hours
   - **Guest Count:** Number of people
   - **Location:** Full address
   - **Menu:** What you want prepared
   - **Special Requests:** Dietary needs, allergies, preferences
   - **Budget:** How much you want to spend

3. Review total price
4. Click **"Send Request"**
5. Chef receives notification and responds

#### Step 4: Confirm & Pay

1. Chef accepts and sends final details
2. Review confirmation
3. Click **"Pay Now"** to process payment
4. Choose payment method:
   - Credit/Debit card
   - Apple Pay
   - Google Pay
   - Bank transfer

5. Print or download invoice for records

#### Step 5: Chef Arrives

1. Chef arrives 30 minutes before scheduled time
2. Check-in and discussion of menu
3. Enjoy your event!
4. Leave rating & review after event

### Managing Bookings

**View Upcoming Bookings:**
- Go to **"My Bookings"**
- See all scheduled events
- Filter by: Upcoming, Completed, Cancelled

**Modify Booking:**
- Click on booking
- Click **"Edit"**
- Change date, time, menu, guest count
- Click **"Update"**
- Notify chef of changes

**Cancel Booking:**
- Click on booking
- Click **"Cancel"**
- Enter cancellation reason
- Refund processed (see policy below)

### Cancellation & Refund Policy

| Timing | Refund |
|--------|--------|
| 30+ days before | 100% refund |
| 14-29 days before | 80% refund |
| 7-13 days before | 60% refund |
| Less than 7 days | No refund |
| After event | No refund |

---

## SNS Auto - Social Media Automation

### What is SNS Auto?

Schedule and automate your social media posts across:
- Facebook
- Instagram
- Twitter/X
- LinkedIn
- TikTok

### How to Connect Your Accounts

#### Step 1: Add Social Media Account

1. Click **"SNS Auto"** from menu
2. Click **"+ Connect Account"**
3. Choose platform (Facebook, Instagram, etc.)
4. Click **"Authorize"**
5. Login to your social media account
6. Click **"Allow"** to grant access
7. Account connected!

### How to Schedule Posts

#### Step 1: Create Post

1. Go to **"Compose"**
2. Write your content (up to 280 characters for Twitter, 2200 for Instagram)
3. Add media:
   - Upload image/video from computer
   - Or paste URL to existing image
   - Preview how it looks
4. Add hashtags and @mentions

#### Step 2: Choose Platforms

1. Check which platforms to post to
2. Platforms auto-adjust format (e.g., vertical for TikTok, square for Instagram)
3. See preview on each platform

#### Step 3: Schedule

1. Click **"Schedule"**
2. Choose:
   - **Date:** Which day
   - **Time:** What time of day
   - **Timezone:** Your timezone
3. Click **"Schedule Post"**

#### Step 4: Manage Scheduled Posts

**View All:**
- Go to **"Scheduled Posts"**
- See all posts queued for publishing

**Edit:**
- Click on post
- Click **"Edit"**
- Change content, time, platforms
- Click **"Update"**

**Delete:**
- Click on post
- Click **"Delete"**
- Post removed from schedule

### Best Practices

- **Optimal times:**
  - Morning: 8-10 AM (reach commuters)
  - Lunch: 12-1 PM (lunch break scrollers)
  - Evening: 5-7 PM (after work)
  - Night: 8-11 PM (before bed)

- **Post frequency:**
  - 1-2 posts per day (optimal engagement)
  - Don't spam (more than 5/day reduces reach)

- **Content mix:**
  - 70% valuable content
  - 20% promotional
  - 10% personal/entertainment

---

## Review Campaign - Customer Reviews

### What is Review Campaign?

Collect and showcase customer reviews:
- Build social proof
- Increase credibility
- Attract new customers
- Track satisfaction

### How to Create a Campaign

#### Step 1: Set Up Campaign

1. Click **"Review"** from menu
2. Click **"+ New Campaign"**
3. Enter:
   - **Campaign Name:** "Product X Reviews", "2026 Spring Feedback", etc.
   - **Description:** What are you collecting reviews for?
   - **Duration:** How long to run campaign (e.g., 30 days)
   - **Target:** How many reviews do you want (e.g., 50)

4. Click **"Create"**

#### Step 2: Invite Customers

1. Click **"Invite Participants"**
2. Choose how to invite:
   - **Email list:** Upload CSV of customer emails
   - **Social media:** Create shareable link for Facebook/Instagram
   - **SMS:** Send link via text message
   - **QR code:** Print for offline distribution

3. Customize invitation message
4. Click **"Send Invitations"**

#### Step 3: Monitor Responses

1. View **"Campaign Dashboard"**
2. See real-time stats:
   - **Invitations sent:** How many
   - **Responses:** How many people reviewed
   - **Response rate:** Percentage
   - **Average rating:** Star rating
   - **Recent reviews:** Latest feedback

3. Filter by:
   - **Rating:** 5★, 4★, 3★, 2★, 1★
   - **Status:** New, Responded, Declined

#### Step 4: Manage Reviews

**Read individual reviews:**
- Click on review
- Read full text
- See customer name & rating
- See timestamp

**Approve for display:**
- Check **"Publish"** checkbox
- Review appears on public profile

**Hide negative reviews:**
- Uncheck publish checkbox
- Review hidden from public
- Still counted in statistics

**Respond to reviews:**
- Click **"Reply"**
- Write response (e.g., "Thank you! We appreciate your feedback")
- Click **"Post Reply"**
- Customer sees your response

### Using Reviews

**Display on website:**
- Copy embed code
- Paste into your website HTML
- Reviews show in real-time

**Share on social media:**
- Click **"Share"**
- Choose platform
- Post best reviews with link to campaign

**Export data:**
- Click **"Export"**
- Get CSV of all reviews
- Analyze in Excel/Google Sheets

---

## AI Automation - Workflow Automation

### What is AI Automation?

Create automated workflows without coding:
- Trigger actions automatically
- Save time on repetitive tasks
- Integrate multiple services
- Create complex logic

### Example Workflows

**Workflow 1: Welcome New Customers**
1. Trigger: New customer signs up
2. Action 1: Send welcome email
3. Action 2: Add to mailing list
4. Action 3: Create task to contact customer

**Workflow 2: Auto-Post to Social Media**
1. Trigger: Schedule (every Monday 9 AM)
2. Action: Post pre-written content to Facebook, Instagram, Twitter

**Workflow 3: Lead Management**
1. Trigger: New form submission
2. Action 1: Save to CRM
3. Action 2: Assign to sales team
4. Action 3: Send follow-up email

### How to Create Workflow

#### Step 1: Choose Template or Start Blank

1. Click **"AI Automation"** from menu
2. Browse templates or click **"+ New Workflow"**
3. Select template or "Blank Workflow"

#### Step 2: Add Trigger

1. Click **"+ Add Trigger"**
2. Choose:
   - **On Schedule:** Daily, Weekly, Monthly
   - **On Event:** New order, Form submission, Email received
   - **Manual:** Click button to run
3. Configure trigger details
4. Click **"Save"**

#### Step 3: Add Actions

1. Click **"+ Add Action"**
2. Choose action:
   - **Send Email:** To specific addresses
   - **Create Task:** Assign to team member
   - **Post to Social:** Publish to social media
   - **Update CRM:** Save/update customer data
   - **Webhook:** Call external API
3. Configure action details
4. Click **"Save"**

#### Step 4: Test & Activate

1. Click **"Test"** to run workflow once
2. Review results
3. Click **"Activate"** to start automation
4. Workflow runs on schedule or trigger

### Monitoring Workflows

**View execution history:**
- Go to **"My Workflows"**
- Click workflow name
- See all past executions
- Check logs for any errors

**Edit workflow:**
- Click workflow
- Click **"Edit"**
- Modify triggers and actions
- Click **"Update"**

**Pause/Resume:**
- Click workflow
- Toggle **"Status"** to pause
- Toggle again to resume

---

## WebApp Builder - No-Code Platform

### What is WebApp Builder?

Create websites without coding:
- Drag-and-drop builder
- Professional templates
- Mobile-responsive
- Free hosting included

### How to Create Website

#### Step 1: Choose Template

1. Click **"WebApp Builder"** from menu
2. See website templates:
   - Business
   - Portfolio
   - E-commerce
   - Blog
   - Restaurant/Cafe
   - Blank

3. Click **"Use Template"**

#### Step 2: Customize Content

1. **Add your information:**
   - Business name
   - Logo
   - Description
   - Contact info
   - Social media links

2. **Edit pages:**
   - Homepage
   - About page
   - Services/Products
   - Contact page
   - Blog (optional)

3. **Add images:**
   - Drag images from desktop
   - Choose from stock image library
   - Add from URL

#### Step 3: Design

1. **Change colors:**
   - Click element
   - Click color button
   - Choose from palette

2. **Change fonts:**
   - Select text
   - Choose font from dropdown
   - Adjust size, bold, italic

3. **Add sections:**
   - Click **"+ Section"**
   - Choose layout: 1 column, 2 column, 3 column
   - Add content

#### Step 4: Publish

1. Click **"Preview"** to see how it looks
2. Click **"Publish"**
3. Choose domain:
   - Free: `yourname.softfactory.site`
   - Custom: Use your own domain
4. Click **"Go Live"**
5. Website is now public at your URL

### Managing Website

**Edit after publishing:**
- Click **"Edit"**
- Make changes
- Click **"Update"**
- Changes live immediately

**View analytics:**
- Click **"Analytics"**
- See:
   - Visitors per day
   - Popular pages
   - Visitor location
   - Device types

**Custom domain:**
- Click **"Settings"**
- Click **"Domain"**
- Enter your domain name
- Follow DNS instructions
- Domain active in 24 hours

---

## Account & Settings

### User Profile

**Edit profile:**
1. Click profile icon (top right)
2. Click **"My Profile"**
3. Edit:
   - Name
   - Email
   - Phone
   - Profile photo
   - Bio
4. Click **"Save"**

### Change Password

1. Click profile icon
2. Click **"Settings"**
3. Click **"Security"**
4. Click **"Change Password"**
5. Enter:
   - Current password
   - New password (8+ chars)
   - Confirm new password
6. Click **"Update"**

### Notifications

**Configure notifications:**
1. Click **"Settings"**
2. Click **"Notifications"**
3. Toggle email alerts:
   - Booking confirmations
   - Campaign responses
   - Scheduled post confirmations
   - Workflow executions
4. Click **"Save"**

### Billing & Subscription

**View subscription:**
1. Click **"Settings"**
2. Click **"Billing"**
3. See:
   - Current plan
   - Renewal date
   - Features included
   - Usage (bookings, campaigns, etc.)

**Upgrade plan:**
1. Click **"Upgrade"**
2. Compare plans
3. Click **"Select Plan"**
4. Enter billing information
5. Click **"Subscribe"**

**Cancel subscription:**
1. Click **"Settings"**
2. Click **"Billing"**
3. Click **"Cancel Subscription"**
4. Confirm cancellation
5. No charges after current billing period

---

## Troubleshooting

### Can't Login

**Problem:** "Invalid passkey" or "Incorrect password"
- ✅ Double-check passkey is exactly: `demo2026`
- ✅ For email login, verify caps lock is off
- ✅ Try clearing browser cookies and trying again
- ✅ If still stuck, click "Forgot Password" to reset

### Page Not Loading

**Problem:** Blank page or "404 Not Found"
- ✅ Refresh page (F5 or Cmd+R)
- ✅ Clear browser cache (Settings → Clear browsing data)
- ✅ Try different browser (Chrome vs Firefox)
- ✅ Check internet connection
- ✅ Restart browser

### Feature Not Working

**Problem:** Button not responding, form won't submit, etc.
- ✅ Wait 10 seconds for page to fully load
- ✅ Check internet speed (tests.softfactory.com/speedtest)
- ✅ Close other browser tabs (free up memory)
- ✅ Try private/incognito window (disables extensions)
- ✅ Contact support with error message visible

### Payment Failed

**Problem:** "Payment declined" or "Transaction failed"
- ✅ Check card is not expired
- ✅ Verify card number, expiry, CVV
- ✅ Contact your bank (might have fraud protection)
- ✅ Try different payment method
- ✅ Try again in 5 minutes

### Chef Didn't Show Up

**Problem:** Booked chef didn't arrive
- ✅ Check booking confirmation email for correct date/time
- ✅ Call chef phone number in confirmation
- ✅ Contact support immediately
- ✅ Full refund processed
- ✅ Escalated to management

---

## FAQ

### General Questions

**Q: Is this free to use?**
A: Basic features are free. Premium features require paid subscription ($9-29/month).

**Q: Can I cancel anytime?**
A: Yes, cancel subscription anytime. No refund for current month, but no charges after that.

**Q: Is my data secure?**
A: Yes. We use 256-bit encryption, daily backups, and comply with GDPR/CCPA.

**Q: Can I export my data?**
A: Yes. Go to Settings → Data → Export. Get all your data as CSV.

### CooCook Questions

**Q: What if chef cancels?**
A: You get 100% refund and priority rebooking with another chef.

**Q: Can I request specific menu items?**
A: Yes. Describe what you want in "Menu" field, and chef confirms they can prepare it.

**Q: How far in advance should I book?**
A: Ideal: 2-4 weeks. Minimum: 48 hours. Some chefs available same-day.

**Q: What if I need to reschedule?**
A: Click "Edit" on booking, change date/time. If within 24 hours, may incur rescheduling fee.

### SNS Auto Questions

**Q: Can I schedule posts for times I'm sleeping?**
A: Yes, that's the whole point! Posts go out automatically at scheduled time.

**Q: What if I want to edit post before it publishes?**
A: Go to "Scheduled Posts", click post, click "Edit", make changes, click "Update".

**Q: Can I reuse posts?**
A: Yes. Click "Duplicate" to create identical post with new schedule.

**Q: What happens if social platform changes API?**
A: We maintain compatibility. Rarely causes issues, and we notify you immediately.

### Review Campaign Questions

**Q: How long can I run a campaign?**
A: 1 day to indefinitely. Most run 30 days.

**Q: Can people leave reviews without being invited?**
A: Only invited customers can leave reviews (keeps spam out).

**Q: Can I edit reviews customers wrote?**
A: No. You can only respond to reviews or hide them (not publish).

**Q: Can I make reviews anonymous?**
A: Yes. In campaign settings, toggle "Anonymous reviews". Ratings still count.

### AI Automation Questions

**Q: Do I need technical skills to create workflows?**
A: No. Drag-and-drop builder with no coding required.

**Q: Can workflows make mistakes?**
A: Rarely. All actions are logged. You can review execution history.

**Q: Can I run workflow manually?**
A: Yes. Create workflow with "Manual" trigger, then click "Run Now".

**Q: What if something goes wrong?**
A: Click "Pause" to stop workflow. Review logs to see what failed.

### WebApp Builder Questions

**Q: Can I use my own domain?**
A: Yes. Go to Settings → Domain, enter your domain, follow DNS instructions.

**Q: How many pages can I create?**
A: Unlimited. No page limits on any plan.

**Q: Can I add email signup form?**
A: Yes. Drag "Email Form" section onto page. Visitors get added to your mailing list.

**Q: Can I delete website after publishing?**
A: Yes. Click "Delete" in website settings. Domain becomes available again.

---

## Contact & Support

### Need Help?

**Email Support:** support@softfactory.com
**Response Time:** Within 24 hours

**Live Chat:** Available Mon-Fri, 9 AM - 6 PM (KST)
**Phone:** +82-2-XXXX-XXXX

### Report a Bug

1. Note exact steps to reproduce
2. Screenshot error message
3. Email to: bugs@softfactory.com
4. Include browser/device info
5. We'll fix ASAP

### Request a Feature

1. Email: features@softfactory.com
2. Describe what you need
3. We review all requests monthly
4. Popular features added in updates

### Report Security Issue

⚠️ **Do NOT post publicly!**

1. Email: security@softfactory.com
2. Include: Issue details, affected areas, how to reproduce
3. Include: Your name and contact info
4. We respond within 24 hours
5. Do not disclose until we issue patch

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-25 | Initial release |
| 0.9 | 2026-02-20 | Beta release |

---

## Legal

- **Terms of Service:** softfactory.com/terms
- **Privacy Policy:** softfactory.com/privacy
- **Cookie Policy:** softfactory.com/cookies
- **Refund Policy:** See individual sections above

---

**Thank you for using SoftFactory Platform!**

For the most up-to-date documentation, visit: **softfactory.com/docs**

---

*Last Updated: 2026-02-25*
*User Manual v1.0*