# Country-wise Admin Time Tracking Feature

## Overview
This feature tracks how many hours users from each country spend in the Django admin interface and displays country-wise statistics.

## What Was Added

### 1. New Models (users/models.py)

#### `AdminTimeLog`
- Tracks individual admin access sessions
- Records login_time (automatic), logout_time, and duration_seconds
- Automatically calculates duration when session ends
- Linked to CTFUser via ForeignKey

#### `CountryAdminStats`
- Aggregates admin time statistics by country
- Stores: total_hours, total_sessions, user_count
- Automatically updated via the `recalculate_all()` method
- Ordered by total hours spent (descending)

### 2. Middleware (ctf_backend/admin_tracking_middleware.py)

`AdminTrackingMiddleware` automatically:
- Creates a new `AdminTimeLog` entry when a user first accesses `/admin/`
- Closes the session when the user leaves the admin interface
- Tracks time spent in the admin panel

### 3. Admin Interface (users/admin.py)

#### `AdminTimeLogAdmin`
View all individual admin access sessions with:
- User, login time, logout time, duration
- Filter by user, date, or country
- Visual status indicator (Active/Closed)

#### `CountryAdminStatsAdmin`
View country-wise statistics with:
- Country name
- Total hours (color-coded: red > 100h, orange > 50h, green < 50h)
- Total sessions
- Number of unique users
- Summary statistics at the top (total countries, users, hours, average)

### 4. Management Command

Use this command to recalculate statistics:

```bash
python manage.py recalculate_country_stats
```

Options:
- `--clear` : Delete existing stats before recalculating

Example:
```bash
python manage.py recalculate_country_stats --clear
```

### 5. Migrations
- Migration file: `users/migrations/0003_countryadminstats_admintimelog.py`
- Already applied to the database

## How It Works

1. **Tracking**: When a user with a country field accesses the admin, a session starts
2. **Duration**: Time is calculated in seconds and converted to hours
3. **Aggregation**: `CountryAdminStats.recalculate_all()` aggregates all AdminTimeLog entries by country
4. **Display**: View statistics in Django admin under "Country Admin Stats"

## Usage

### View in Django Admin

1. Go to Django Admin
2. Click on "Country Admin Stats" (under Users)
3. See complete statistics with color-coded hours

### Access Individual Sessions

1. Go to "Admin Time Logs" in Django Admin
2. Filter by country, user, or date
3. See detailed session information

### Recalculate Statistics

```bash
# From the backend directory
python3 manage.py recalculate_country_stats

# With clear option to reset stats first
python3 manage.py recalculate_country_stats --clear
```

## Data Fields

### AdminTimeLog
- `user` - ForeignKey to CTFUser
- `login_time` - DateTime (auto-recorded)
- `logout_time` - DateTime (recorded when leaving admin)
- `duration_seconds` - Integer (auto-calculated)

### CountryAdminStats
- `country` - CharField (unique, indexed)
- `total_hours` - DecimalField
- `total_sessions` - IntegerField (count of sessions)
- `user_count` - IntegerField (count of unique users)
- `last_updated` - DateTimeField (auto-updated)

## Features

✓ Automatic session tracking via middleware
✓ Color-coded statistics for easy visualization
✓ Summary statistics at the top of the list
✓ Filterable by country, user, or date
✓ Aggregated data by country
✓ Management command for manual recalculation
✓ Custom admin templates with better UX

## Example Data Display

When viewing Country Admin Stats, you'll see:

```
Country Admin Time Statistics Summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Countries: 15
Total Users: 250
Total Hours Spent: 1,250.50 hrs
Avg Hours per Country: 83.37 hrs

Country  | Total Hours | Sessions | Users
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
India    | 450.25 hrs  | 1,200    | 85
USA      | 320.50 hrs  | 890      | 65
...
```

## Technical Notes

- Sessions are created when `process_request` detects admin access
- Sessions are closed when `process_response` detects non-admin request
- Duration is calculated when logout_time is set
- `CountryAdminStats.recalculate_all()` should be run periodically or after significant data changes
- Uses Django ORM aggregation with `Sum()` and `Count()`

## Integration Points

- Middleware: Automatically integrated in settings.py
- Models: Registered in users admin
- Migrations: Already applied
- Templates: Custom template for CountryAdminStats view
- Commands: Management command available

## Future Enhancements

- Real-time session detection (currently session ends on next non-admin request)
- Session duration threshold alerts (e.g., alert if user>X hours)
- Export statistics to CSV/PDF
- Analytics dashboard with charts
- Logs retention policy
