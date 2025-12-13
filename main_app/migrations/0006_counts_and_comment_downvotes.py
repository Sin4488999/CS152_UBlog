from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ("main_app", "0005_alter_downvote_id"),  # adjust to your latest
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="downvote_count",
            field=models.IntegerField(default=0, blank=True),
        ),
        migrations.AddField(
            model_name="comment",
            name="downvote_count",
            field=models.IntegerField(default=0, blank=True),
        ),
        migrations.CreateModel(
            name="CommentDownvote",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("comment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="main_app.comment")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="main_app.customuser")),
            ],
            options={"unique_together": {("user", "comment")}},
        ),
    ]
