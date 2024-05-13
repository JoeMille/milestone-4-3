# Generated by Django 4.2.7 on 2024-04-15 14:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0022_basketitem_book_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="basketitem",
            name="price",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=6),
        ),
    ]
