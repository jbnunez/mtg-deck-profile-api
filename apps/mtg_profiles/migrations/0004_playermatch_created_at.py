from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("mtg_profiles", "0003_alter_profilefield_field_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="playermatch",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
