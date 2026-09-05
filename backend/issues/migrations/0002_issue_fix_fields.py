from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('issues', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='issue',
            name='ai_suggested_value',
            field=models.TextField(
                blank=True,
                null=True,
                help_text="AI-suggested replacement value for the affected cell. "
                           "Empty for DUPLICATE issues, whose fix is to remove the row."
            ),
        ),
        migrations.AddField(
            model_name='issue',
            name='is_resolved',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='issue',
            name='resolved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
