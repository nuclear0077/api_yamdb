# Generated by Django 3.2 on 2023-01-24 13:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('YamUsers', '0001_initial'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='yamuser',
            name='unique_email',
        ),
    ]
