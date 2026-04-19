# Prompt Testing Suite

This file contains test cases for validating the requirement atomization, smell detection, and ISO 29148 formatting capabilities of the RE Tool.

---

## Group A: Real-Time Splitting (Tests "Atomizer" Prompt)

These inputs contain multiple requirements joined by "and", "plus", "but", or commas. The atomizer prompt should split them into separate ISO 29148 requirements.

### A1: Dashboard with Multiple Features
```
"I need a dashboard where managers can see sales reports, and I also want them to be able to download these reports as PDFs, plus there should be an email notification sent to the admin whenever a report is generated."
```
**Expected:** 3 separate requirements (view reports, download PDF, email notification)

### A2: Phone Authentication Flow
```
"The system should allow users to sign up using their phone number and it must automatically send a 6-digit verification code via SMS, plus it should log the user in immediately after they verify."
```
**Expected:** 3 separate requirements (phone signup, SMS verification, auto-login)

### A3: Payment Integration
```
"I want to integrate the checkout process with Stripe and PayPal so people can pay however they want, and it should also calculate the shipping costs automatically based on their location."
```
**Expected:** 3 separate requirements (Stripe integration, PayPal integration, shipping calculation)

### A4: Book Search with Membership
```
"Users should be able to search for books by title or author, but only if they have an active membership, and they should be able to reserve them for up to 48 hours."
```
**Expected:** 3 separate requirements (search by title, search by author, reservation with time limit)

### A5: Health Tracking App
```
"The app needs to track steps, calculate calories burned based on height and weight, and sync all this data to the cloud every ten minutes."
```
**Expected:** 3 separate requirements (step tracking, calorie calculation, cloud sync)

---

## Group B: High-Ambiguity (Tests Smell Detector & HITL)

These inputs contain subjective, vague, or immeasurable terms that should trigger the smell detector and potentially request human clarification.

### B1: Performance + Usability Vagueness
```
"The system needs to be really fast during peak hours, and the user interface should be very modern and easy to use so that people don't get confused."
```
**Expected:** Smell detection for "really fast", "very modern", "easy to use", "don't get confused" — trigger clarification questions

### B2: Search Performance Claim
```
"I want the search results to load super fast even when there are thousands of items in the database so that the user doesn't have to wait around."
```
**Expected:** Smell detection for "super fast", "thousands of items", "wait around" — trigger clarification

### B3: Mobile UI Accessibility Conflict
```
"The mobile app needs to look very modern and the buttons should be easy to click for elderly people, and it should feel very responsive when navigating."
```
**Expected:** Smell detection for "very modern", "easy to click", "very responsive" — trigger clarification

### B4: Global Compliance Vagueness
```
"We need to make sure all user data is kept totally secure and private, and the system should comply with all the latest data protection laws globally."
```
**Expected:** Smell detection for "totally secure", "totally private", "all the latest", "globally" — trigger clarification

### B5: Scalability Claim
```
"The software should be highly scalable and handle a huge amount of traffic during the holiday season without any downtime."
```
**Expected:** Smell detection for "highly scalable", "huge amount", "without any downtime" — trigger clarification

---

## Group C: Logic Gaps & Permissions (Tests Role Analysis)

These inputs contain role-based permissions, conditional logic, or timing requirements that may have gaps.

### C1: Role-Based Access Control
```
"Admins should have a special dashboard to delete user accounts, but regular users should only be able to deactivate their own accounts and not see the admin panel."
```
**Expected:** 2+ requirements with clear role separation (admin vs regular user)

### C2: Scheduled Report Generation
```
"The software should generate a monthly financial report and send it to the management team every first Monday of the month."
```
**Expected:** Requirements for report generation and email delivery with scheduling logic

### C3: Librarian + Performance Concern
```
"The librarian needs to be able to add new books to the catalog, but we have to make sure the system handles a lot of data without crashing."
```
**Expected:** Requirements for book addition and performance/scalability

### D4: Tiered Access
```
"Only premium members can access the video library, while free users can only see the trailers and read the descriptions."
```
**Expected:** 2 requirements with clear permission tiers (premium vs free)

### C5: Order Cancellation Workflow
```
"When a customer cancels an order, the system must notify the warehouse immediately and process a refund to the original payment method."
```
**Expected:** 2 requirements (warehouse notification, refund processing)

---

## Group D: Constraints & Edge Cases (Tests ISO Formatting)

These inputs contain specific constraints, edge cases, or technical requirements that test ISO 29148 formatting.

### D1: File Upload Restrictions
```
"Users should not be allowed to upload files that are too large, and the system must reject any file types that aren't images or PDFs."
```
**Expected:** Requirements for file size limit and file type validation

### D2: Cross-Platform + Offline
```
"The tool has to work perfectly on old Android phones and the latest iPhones, plus it should have an offline mode for people with bad internet."
```
**Expected:** 3 requirements (Android compatibility, iOS compatibility, offline mode)

### D3: Password Policy
```
"All passwords must be very strong and the system should force users to change them every few months to keep things safe."
```
**Expected:** Requirements for password strength and rotation policy

### D4: UI Branding Requirements
```
"The system shall display the company logo on every page in the top left corner, and the background color must be consistent with our brand guidelines."
```
**Expected:** Requirements for logo placement and color consistency

### D5: Error Handling + Monitoring
```
"If the database goes down, the system should show a friendly error message to the user and alert the IT team via Slack immediately."
```
**Expected:** 2 requirements (user-facing error message, IT team Slack notification)

---