# path: main_app/migrations/0002_comment_threads_and_likes.py
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ("main_app", "0001_initial"),  # update to your latest existing migration
    ]

    operations = [
        migrations.AddField(
            model_name="comment",
            name="parent",
            field=models.ForeignKey(
                to="main_app.comment",
                on_delete=django.db.models.deletion.CASCADE,
                null=True,
                blank=True,
                related_name="children",
            ),
        ),
        migrations.AddField(
            model_name="comment",
            name="like_count",
            field=models.IntegerField(default=0, blank=True),
        ),
        migrations.AlterUniqueTogether(
            name="like",
            unique_together={("user", "post")},
        ),
        migrations.CreateModel(
            name="CommentLike",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                (
                    "user",
                    models.ForeignKey(
                        to="main_app.customuser",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
                (
                    "comment",
                    models.ForeignKey(
                        to="main_app.comment",
                        on_delete=django.db.models.deletion.CASCADE,
                    ),
                ),
            ],
            options={"unique_together": {("user", "comment")}},
        ),
    ]
