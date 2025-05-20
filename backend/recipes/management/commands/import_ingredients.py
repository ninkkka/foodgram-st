import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Import ingredients from JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', '-f', default='data/ingredients.json',
            help='Path to JSON file with ingredients'
        )

    def handle(self, *args, **options):
        path = options['file']
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        created = 0
        for item in data:
            Ingredient.objects.get_or_create(
                name=item['name'],
                measurement_unit=item['measurement_unit']
            )
            created += 1
        self.stdout.write(self.style.SUCCESS(f'Imported {created} ingredients'))
