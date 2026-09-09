import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0004_daily_task_completion_article_read'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Drop the old CharField-based DailyTaskCompletion
        migrations.DeleteModel(name='DailyTaskCompletion'),
        # Create the user-owned DailyTask definition model
        migrations.CreateModel(
            name='DailyTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='daily_tasks',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['order', 'created_at'],
            },
        ),
        # Create the FK-based completion tracker
        migrations.CreateModel(
            name='DailyTaskCompletion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('task', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='completions',
                    to='wallet.dailytask',
                )),
            ],
            options={
                'constraints': [
                    models.UniqueConstraint(fields=('task', 'date'), name='unique_task_completion_per_day'),
                ],
            },
        ),
    ]
