from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("mtg_profiles", "0004_playermatch_created_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="userdeck",
            name="last_played",
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
