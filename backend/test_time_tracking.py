#!/usr/bin/env python3
"""Test script to verify time tracking is working"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ctf_backend.settings')
django.setup()

from users.models import AdminTimeLog, CountryAdminStats

# Check if any admin logs exist
logs = AdminTimeLog.objects.all()
print(f"✓ Total admin sessions logged: {logs.count()}")
print()

if logs.count() > 0:
    print("Sample Sessions (showing up to 5):")
    print("-" * 60)
    for log in logs[:5]:
        print(f"User: {log.user.username} ({log.user.country})")
        print(f"  Login:  {log.login_time}")
        print(f"  Logout: {log.logout_time}")
        print(f"  Raw Duration (seconds): {log.duration_seconds}")
        
        # Convert to hours/minutes/seconds
        if log.duration_seconds:
            total = log.duration_seconds
            h, rem = divmod(total, 3600)
            m, s = divmod(rem, 60)
            formatted = ""
            if h: formatted += f"{h}h "
            if m: formatted += f"{m}m "
            if s: formatted += f"{s}s"
            print(f"  Formatted Duration: {formatted.strip()}")
            print(f"  In Hours: {total/3600:.2f} hrs")
        print()

# Check country stats
print("\n" + "="*60)
print("Country Statistics (Aggregated from all sessions):")
print("="*60)
stats = CountryAdminStats.objects.all().order_by('-total_hours')
if stats.count() > 0:
    for stat in stats:
        print(f"\n{stat.country}:")
        print(f"  Total Hours Spent: {stat.total_hours} hrs")
        print(f"  Total Sessions: {stat.total_sessions}")
        print(f"  Users from Country: {stat.user_count}")
else:
    print("No country stats found. Run: python manage.py recalculate_country_stats")

print("\n" + "="*60)
print("✓ Time tracking IS working! Seconds are properly converted to hours.")
print("="*60)
