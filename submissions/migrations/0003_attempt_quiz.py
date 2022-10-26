# Generated by Django 3.2.9 on 2022-10-26 09:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('quizzes', '0003_quiz_is_active'),
        ('submissions', '0002_attempt'),
    ]

    operations = [
        migrations.AddField(
            model_name='attempt',
            name='quiz',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, to='quizzes.quiz'),
            preserve_default=False,
        ),
    ]
