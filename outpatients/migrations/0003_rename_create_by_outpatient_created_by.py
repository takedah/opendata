# Generated by Django 4.2.9 on 2024-02-13 13:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("outpatients", "0002_alter_outpatient_is_pediatrics_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="outpatient",
            old_name="create_by",
            new_name="created_by",
        ),
    ]
