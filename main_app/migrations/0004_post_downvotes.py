# path: main_app/migrations/0003_post_downvotes.py
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ("main_app", "0003_remove_profile_linkedin_link_alter_commentlike_id"),  # update if your last migration differs
    ]

    operations = [
        migrations.CreateModel(
            name="Downvote",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("post", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="main_app.post")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="main_app.customuser")),
            ],
            options={"unique_together": {("user", "post")}},
        ),
    ]
