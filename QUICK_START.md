# Quick Start: Country-wise Admin Time Tracking

## What's New?

Your CTF platform now automatically tracks how many hours users from each country spend in the Django admin interface.

## How to Use

### 1️⃣ View Country Statistics
```
1. Go to Django Admin (http://localhost:8000/admin/)
2. Click "Country Admin Stats" in the left sidebar
3. See total hours spent by each country
```

### 2️⃣ View Individual Sessions
```
1. Go to Django Admin (http://localhost:8000/admin/)
2. Click "Admin Time Logs" in the left sidebar
3. See detailed information about each user's admin access
```

### 3️⃣ Update Statistics
After significant admin usage, recalculate the statistics:

```bash
cd backend
python3 manage.py recalculate_country_stats
```

## Example: India's Admin Time

When you go to **Country Admin Stats**, you'll see results like:

```
Country: India
├─ Total Hours Spent: 450.25 hrs
├─ Total Sessions: 1,200
└─ Unique Users: 85
```

This means users from India collectively spent **450.25 hours** in the admin interface across **1,200 sessions** from **85 different users**.

## Admin Interface Features

### Country Admin Stats Page
- 📊 **Summary at top**: Total countries, users, hours, and averages
- 🌍 **Country list**: Sorted by hours (highest first)
- 🎨 **Color coding**:
  - 🔴 Red: > 100 hours (heavy usage)
  - 🟠 Orange: > 50 hours (moderate usage)
  - 🟢 Green: < 50 hours (light usage)
- 🔍 **Search**: Find countries quickly
- 📅 **Last Updated**: See when stats were last calculated

### Admin Time Logs Page
- 👤 Show which user accessed admin
- 🌐 Show their country
- ⏱️ Show login/logout times
- ⏲️ Show duration of session
- 🔴 Show if session is still active
- 🔍 Filter by user, country, or date

## Example Commands

```bash
# View current statistics (no changes to data)
python3 manage.py recalculate_country_stats

# Clear old stats and recalculate fresh from logs
python3 manage.py recalculate_country_stats --clear

# View the database (if you have access)
python3 manage.py shell
>>> from users.models import CountryAdminStats
>>> CountryAdminStats.objects.all().order_by('-total_hours')[:5]
```

## How It Works (Behind the Scenes)

1. **Automatic Tracking**: Whenever a user visits `/admin/`, the system automatically creates a log entry
2. **Session Duration**: When they leave admin, the session is closed and duration calculated
3. **Time Calculation**: Hours are calculated automatically (no manual entry needed)
4. **Aggregation**: All sessions are summed up by country
5. **Updates**: Use the management command to refresh statistics

## Typical Workflow

```
User creates account with "India" as country
               ↓
User visits Django Admin
               ↓
AdminTrackingMiddleware creates AdminTimeLog
               ↓
User browses admin for 30 minutes
               ↓
User leaves admin area
               ↓
AdminTrackingMiddleware closes the session
               ↓
Run: python manage.py recalculate_country_stats
               ↓
CountryAdminStats updated:
   India: 0.5 hours added
```

## FAQ

**Q: Do I need to start/stop tracking manually?**
A: No! It's completely automatic via middleware.

**Q: How often should I run the recalculate command?**
A: Periodically (daily/weekly). You can also run it manually whenever needed.

**Q: Where does the country information come from?**
A: From the user's profile (the `country` field on their CTFUser account).

**Q: What if a user leaves without logging out?**
A: Their session will close on the next non-admin page they visit, or you can manually update it in the database.

**Q: Can I see a user's activity breakdown?**
A: Yes! Go to Users → Admin Time Logs and filter by user name.

**Q: Are historical logs kept?**
A: Yes! All admin sessions are logged indefinitely in AdminTimeLog table.

## Files Changed

- ✅ Backend models updated with new tracking models
- ✅ Admin interface enhanced with new views
- ✅ Middleware added for automatic tracking
- ✅ Management command created for statistics
- ✅ Migrations created and applied
- ✅ Database updated with new tables

## Support

Need more details? Check:
- `/Users/kunalkalawant/Desktop/CTF2.0/COUNTRY_ADMIN_TRACKING.md` - Complete documentation
- `/Users/kunalkalawant/Desktop/CTF2.0/IMPLEMENTATION_SUMMARY.md` - Technical details
