# Generated by Django 3.2 on 2023-01-17 17:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0002_auto_20230117_1735'),
    ]

    operations = [
        migrations.AlterField(
            model_name='titlegenre',
            name='title',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='reviews.title'),
            preserve_default=False,
        ),
    ]
