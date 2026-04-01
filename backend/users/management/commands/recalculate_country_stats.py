"""
Management command to recalculate country-wise admin time statistics
Usage: python manage.py recalculate_country_stats
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import CountryAdminStats


class Command(BaseCommand):
    help = 'Recalculate country-wise admin time statistics from AdminTimeLog'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing stats before recalculating',
        )

    def handle(self, *args, **options):
        if options['clear']:
            count = CountryAdminStats.objects.count()
            CountryAdminStats.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f'Deleted {count} existing country stats records')
            )
        
        self.stdout.write('Recalculating country statistics...')
        
        try:
            CountryAdminStats.recalculate_all()
            
            stats = CountryAdminStats.objects.all()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully recalculated stats for {stats.count()} countries')
            )
            
            # Print summary
            from django.db.models import Sum
            total_hours = stats.aggregate(Sum('total_hours'))['total_hours__sum'] or 0
            total_users = stats.aggregate(Sum('user_count'))['user_count__sum'] or 0
            
            self.stdout.write(self.style.SUCCESS(f'\nSummary:'))
            self.stdout.write(f'  Total Countries: {stats.count()}')
            self.stdout.write(f'  Total Users: {total_users}')
            self.stdout.write(f'  Total Hours: {total_hours}')
            self.stdout.write(f'  Last Updated: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error recalculating stats: {str(e)}'))
            raise
