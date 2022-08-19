# Generated by Django 4.0.6 on 2022-08-19 22:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('posts', '0003_delete_consumption'),
        ('foods', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Consumption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField(default=0)),
                ('meal_type', models.CharField(choices=[('breakfast', '아침'), ('lunch', '점심'), ('dinner', '저녁'), ('snack', '간식')], default=' ', max_length=12)),
                ('img1', models.ImageField(blank=True, upload_to='post/images/%Y/%m/%d')),
                ('img2', models.ImageField(blank=True, upload_to='post/images/%Y/%m/%d')),
                ('img3', models.ImageField(blank=True, upload_to='post/images/%Y/%m/%d')),
                ('food', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='foods.food')),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='posts.post')),
            ],
        ),
    ]
