# Generated by Django 3.2.5 on 2021-08-04 19:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kafka_example', '0003_alter_examplevalue_value'),
    ]

    operations = [
        migrations.AddField(
            model_name='examplevalue',
            name='data_provenance',
            field=models.JSONField(default=list),
        ),
    ]