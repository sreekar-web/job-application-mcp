# Dashboard Quick Start Guide

## Starting the Dashboard

### Option 1: Direct Python Execution
```bash
cd c:\Users\rsree\Documents\job-application-mcp

# Activate virtual environment
venv\Scripts\activate

# Start the Flask server
python dashboard/app.py
```

### Option 2: Using PowerShell
```powershell
cd 'c:\Users\rsree\Documents\job-application-mcp'
& '.\venv\Scripts\python.exe' dashboard/app.py
```

**Expected Output**:
```
 * Running on http://127.0.0.1:5000
 * Press CTRL+C to quit
 * Restarting with reloader
```

### Step 2: Open in Browser
Navigate to: **`http://localhost:5000`**

---

## Dashboard Pages

### 1. Dashboard (Main Page) — `/`

**What You See**:
- 6 statistics cards (Total, Submitted, Interviews, Offers, Pending, Success Rate)
- Status distribution pie chart
- Top 10 companies bar chart
- Overdue follow-ups widget (red badges)
- Recent 5 applications

**Key Interactions**:
- Click "Update" button on follow-ups to change status
- Hover over charts to see details
- Click "View All" to go to applications page

**Auto-Refresh**: Charts update every 30 seconds

---

### 2. Applications List — `/applications`

**What You See**:
- Search box (filter by company or role)
- Status filter dropdown
- Full table of all applications
- Summary statistics at bottom

**Key Interactions**:

**Search Box**:
- Type company name or role (e.g., "Google", "Backend")
- Results filter in real-time (no page reload)

**Status Filter**:
- Select a status (Submitted, Interview, Offer, etc.)
- Only shows applications with that status
- Works with search (filters are combined)

**Reset Button**:
- Clears both search and status filter
- Shows all applications

**Quick Actions** (per application):
- ✏️ **Edit Button**: Update status with notes
- 📅 **Timeline Button**: View full application history

---

## Status Update Workflow

### From Dashboard
1. Find application in follow-ups widget
2. Click "Update" button
3. Modal opens with:
   - Company name and role
   - Current status badge
   - Status dropdown (only shows valid transitions)
   - Optional notes field
4. Select new status
5. Optionally add notes
6. Click "Update Status"
7. ✅ Status updated, dashboard refreshes

### From Applications List
1. Find application in table
2. Click ✏️ **Edit button**
3. Same modal as above
4. Update and submit

**Valid Status Transitions**:
```
SUBMITTED  → VIEWED, REJECTED, SAVED
VIEWED     → INTERVIEW, REJECTED
INTERVIEW  → OFFER, REJECTED
OFFER      → ACCEPTED, REJECTED
ACCEPTED   → (no transitions)
REJECTED   → (no transitions)
SAVED      → SUBMITTED, DELETED
```

---

## Keyboard Shortcuts

- **Ctrl+K**: Focus on search box (quick search)
- **Escape**: Close any open modals

---

## Filtering & Searching

### Search Box
- **Case-insensitive**: "google" finds "Google"
- **Partial matches**: "back" finds "Backend Engineer"
- **Multiple fields**: Searches both company AND role
- **Real-time**: Results update as you type
- **Debounced**: Waits 300ms after last keystroke (prevents excessive queries)

### Status Filter
- **All Statuses**: Shows all applications (default)
- **Specific Status**: Shows only that status
- **Combines with Search**: Both filters applied together

**Example**:
- Search: "Amazon"
- Status: "INTERVIEW"
- Result: Only Amazon applications with INTERVIEW status

---

## Understanding the Statistics

### Statistics Cards (Dashboard)
- **Total Applications**: Count of all applications
- **Submitted**: Count with SUBMITTED status
- **Interviews**: Count with INTERVIEW status
- **Offers**: Count with OFFER status
- **Pending Follow-ups**: Count that need follow-up (overdue)
- **Success Rate %**: (Offers + Accepted) / Total * 100

### Summary Statistics (Applications Page)
- **Total Applications**: Count of visible applications
- **Overdue Follow-ups**: Applications with next_followup_at < now
- **Pending Interviews**: Count with INTERVIEW status
- **Offers / Accepted**: Count with OFFER or ACCEPTED status

---

## Timeline View

**What It Shows**:
- Complete status history for one application
- Each status change with timestamp
- User notes (if any)
- Visual timeline with color-coded markers

**How to Access**:
1. Go to Applications page
2. Find the application
3. Click 📅 **Timeline button**
4. Modal opens with full history

**Understanding Timeline**:
- **Oldest at top**, newest at bottom
- **Colored circles**: Status markers (color matches badge color)
- **Lines**: Connect each status change
- **Dates**: Show exactly when status changed

**Example Timeline**:
```
✓ SUBMITTED  — Jan 20, 2026 at 10:30 AM
             "Applied via Greenhouse"

✓ VIEWED     — Jan 22, 2026 at 08:15 AM

✓ INTERVIEW  — Jan 25, 2026 at 03:00 PM
             "Phone screen with hiring manager"
```

---

## Charts Explained

### Status Distribution (Pie Chart)
- **What**: Percentage of applications in each status
- **Colors**: 
  - Blue = Submitted
  - Teal = Viewed
  - Light Blue = Interview
  - Green = Offer
  - Dark Green = Accepted
  - Red = Rejected
  - Gray = Saved
- **Hover**: Shows exact count for each status
- **Purpose**: Understand application pipeline health

**Healthy Distribution**:
- High "Submitted" → many applications
- Increasing "Interview" → good pipeline
- Some "Offer" → conversion happening

### Top 10 Companies (Bar Chart)
- **What**: Companies with most applications
- **Bar Height**: Number of applications per company
- **Colors**: Different color per company
- **Purpose**: See which companies you're focused on
- **Example**: Google (3 apps), Amazon (2 apps), etc.

---

## Tips & Tricks

### 1. Quick Follow-up
1. Go to Dashboard
2. Scroll to "Follow-ups Needed" widget
3. Click "Update" on overdue applications
4. Change status (e.g., SUBMITTED → VIEWED)
5. Dashboard updates immediately

### 2. Bulk Filter
1. Go to Applications page
2. Use search to find company: "Google"
3. See all Google applications
4. Update status for each one

### 3. Monitor Pipeline
1. Return to Dashboard
2. Check charts for trends
3. Are interview counts increasing? ✅ Good sign
4. Are offers coming? ✅ Pipeline working

### 4. View Application History
1. Applications page
2. Click 📅 button on any application
3. See complete journey from submit to current status
4. Useful for remembering interview details

---

## Troubleshooting

### Dashboard Won't Load
**Problem**: "Cannot connect to localhost:5000"

**Solution**:
1. Make sure Flask server is running
2. Check terminal for errors
3. Try refreshing page (Ctrl+R)
4. Restart server:
   ```bash
   # Press Ctrl+C to stop
   # Then run again:
   python dashboard/app.py
   ```

### No Applications Showing
**Problem**: "No applications found" message

**Solution**:
1. Check `applications.csv` exists in current directory
2. Make sure `applications.csv` has data
3. Verify status is correct (not filtered)
4. Try resetting filters (click Reset button)

### Chart Not Displaying
**Problem**: Empty chart or "Chart.js error"

**Solution**:
1. Check browser console (F12)
2. Make sure Chart.js CDN is accessible
3. Refresh page
4. Try a different browser

### Search Not Working
**Problem**: Search box not filtering results

**Solution**:
1. Wait 300ms after typing (debounce)
2. Make sure text matches company or role
3. Search is case-insensitive (try "google" not "GOOGLE")
4. Clear filters and try again

---

## Performance Tips

### For Large Data Sets (100+ applications)
1. Use status filter to narrow results
2. Use search to find specific companies
3. Avoid loading all applications at once
4. Use timeline view only when needed

### For Slow Networks
1. Dashboard loads stats first, then charts
2. Wait 2-3 seconds for complete load
3. Check browser Network tab (F12) to see requests
4. Try disabling browser extensions

---

## Data Privacy

**Important**: 
- Dashboard data comes from local `applications.csv`
- No data sent to external servers
- No cloud storage
- Completely private and local

---

## Keyboard Navigation

**Tab through**:
- Search box
- Status filter
- Reset button
- Edit buttons (per row)
- Timeline buttons (per row)

**Enter**:
- Submit search
- Open modal
- Submit form

**Escape**:
- Close modal
- Exit search focus

---

## Browser Developer Tools (F12)

**Useful for Debugging**:

**Console Tab**:
- See JavaScript errors
- Check API responses
- View warnings

**Network Tab**:
- See API requests (/api/stats, /api/applications)
- Check response times
- Verify data format

**Elements Tab**:
- Inspect HTML structure
- Check CSS classes
- Debug styling issues

---

## Integration with Rest of System

**Dashboard Gets Data From**:
- Stage 6: `applications/application_tracker.py` → reads `applications.csv`
- Stage 6: `applications/followup_manager.py` → calculates follow-up dates
- Stage 5: Application submission history → status_history in CSV

**Dashboard Flows Back To**:
- Status updates → CSV via ApplicationTracker
- Next follow-up dates → calculated and displayed

---

## Common Workflows

### Workflow 1: Daily Check-in
1. Open Dashboard (`/`)
2. Check statistics (how many submitted, how many interviews?)
3. Check follow-ups (any overdue?)
4. Update overdue applications with "VIEWED" or "INTERVIEW"
5. Check charts for pipeline health

### Workflow 2: After Interview
1. Go to Applications page
2. Search for the company
3. Click Edit button
4. Change status to "INTERVIEW"
5. Add note: "Phone screen with hiring manager"
6. Check follow-up date (should be 7 days out)

### Workflow 3: Got an Offer
1. Go to Applications page
2. Search for company
3. Click Edit
4. Change status to "OFFER"
5. Add note: "Verbal offer received, formal offer coming"
6. Check follow-up date (should be 30 days out)

### Workflow 4: Analyze Trends
1. Go to Dashboard
2. Look at pie chart (which statuses have most apps?)
3. Look at bar chart (which companies getting most attention?)
4. Go to Applications page
5. Filter by "INTERVIEW" status
6. See which companies are moving to interviews

---

## Next Steps

After you're comfortable with the Dashboard:

1. **Stage 8: Interview Prep**
   - Email follow-up automation
   - Interview scheduling
   - Interview preparation materials

2. **Stage 9: Optimization**
   - Advanced analytics
   - Success rate tracking
   - Keyword heatmaps

---

**Have Questions?** Check the detailed documentation in `STAGE_8_DASHBOARD.md`

**Need Help?** Refer to `STAGE_8_TEST_RESULTS.md` for technical details

**Happy job hunting! 🎯**
