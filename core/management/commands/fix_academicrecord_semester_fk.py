from django.core.management.base import BaseCommand
from core.models import AcademicRecord, Semester
from django.db import transaction

class Command(BaseCommand):
    help = 'Fix AcademicRecord rows with invalid semester foreign keys by deleting them.'

    def handle(self, *args, **options):
        with transaction.atomic():
            valid_semester_ids = set(Semester.objects.values_list('id', flat=True))
            to_delete = AcademicRecord.objects.exclude(semester_id__in=valid_semester_ids)
            count = to_delete.count()
            to_delete.delete()
            self.stdout.write(self.style.SUCCESS(f'Deleted {count} AcademicRecord(s) with invalid semester foreign keys.'))
