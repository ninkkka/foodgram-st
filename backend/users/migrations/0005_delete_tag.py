# Generated by Django 3.2.18 on 2025-06-08 14:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_ingredient_tag'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Tag',
        ),
    ]
