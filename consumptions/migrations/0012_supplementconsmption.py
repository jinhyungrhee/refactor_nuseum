# Generated by Django 4.0.6 on 2022-09-01 16:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0004_alter_post_created_at'),
        ('foods', '0003_supplement'),
        ('consumptions', '0011_foodimage_deprecated'),
    ]

    operations = [
        migrations.CreateModel(
            name='SupplementConsmption',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('manufacturer', models.CharField(max_length=100)),
                ('amount', models.IntegerField(default=0)),
                ('image', models.CharField(blank=True, max_length=250)),
                ('deprecated', models.BooleanField(default=False)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='posts.post')),
                ('supplement', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='foods.supplement')),
            ],
        ),
    ]