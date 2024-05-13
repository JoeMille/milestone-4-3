# Generated by Django 4.2.7 on 2024-04-11 12:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0016_item_order_completedorder"),
    ]

    operations = [
        migrations.AddField(
            model_name="completedorder",
            name="total_cost",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
        migrations.AddField(
            model_name="order",
            name="total_cost",
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]