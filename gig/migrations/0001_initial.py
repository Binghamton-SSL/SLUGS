# Generated by Django 3.0.6 on 2020-06-16 05:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0002_auto_20200616_0154'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('phone_number', phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, null=True, region=None)),
                ('email', models.EmailField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('department', models.CharField(choices=[('L', 'Lighting'), ('S', 'Sound'), ('M', 'Manager'), ('O', 'Other')], max_length=1)),
                ('not_associated_with_event', models.BooleanField(default=False)),
                ('employee_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='auth.Group')),
                ('linked_employee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Hired Employee',
                'verbose_name_plural': 'Hired Employees',
            },
        ),
        migrations.CreateModel(
            name='Gig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('notes', models.TextField(blank=True)),
                ('load_in_lighting', models.DateTimeField()),
                ('load_in_sound', models.DateTimeField()),
                ('start', models.DateTimeField(verbose_name='Gig start time')),
                ('end', models.DateTimeField()),
                ('load_out_lighting', models.DateTimeField()),
                ('load_out_sound', models.DateTimeField()),
                ('day_of_show_notes', models.TextField(blank=True)),
                ('archived', models.BooleanField(default=False)),
                ('contact', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='gig.Contact')),
            ],
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('SA_account_num', models.BigIntegerField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Signup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_open', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Sign Up Status',
                'verbose_name_plural': 'Sign Up Status',
            },
        ),
        migrations.CreateModel(
            name='System',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('is_addon', models.BooleanField(default=False)),
                ('department', models.CharField(choices=[('L', 'Lighting'), ('S', 'Sound'), ('M', 'Manager'), ('O', 'Other')], max_length=1)),
                ('base_price', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
                ('price_per_hour', models.DecimalField(blank=True, decimal_places=2, max_digits=8, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='SystemInstance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hours_rented', models.DecimalField(decimal_places=2, max_digits=6)),
                ('linked_gig', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gig.Gig')),
                ('system', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gig.System')),
            ],
            options={
                'verbose_name': 'Hired System',
                'verbose_name_plural': 'Hired Systems',
            },
        ),
        migrations.CreateModel(
            name='Shift',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time_in', models.DateTimeField()),
                ('time_out', models.DateTimeField()),
                ('total_hours', models.DecimalField(decimal_places=2, max_digits=4)),
                ('processed', models.BooleanField(default=False)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='InterestedEmployee',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('interested_at', models.DateTimeField(auto_now=True)),
                ('job', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gig.Employee')),
                ('linked_employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='gig',
            name='location',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='gig.Location'),
        ),
        migrations.AddField(
            model_name='gig',
            name='org',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='gig.Organization'),
        ),
        migrations.AddField(
            model_name='employee',
            name='linked_gig',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='gig.Gig'),
        ),
        migrations.AddField(
            model_name='employee',
            name='linked_system',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='gig.System'),
        ),
        migrations.AddField(
            model_name='contact',
            name='linked_org',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='gig.Organization'),
        ),
        migrations.CreateModel(
            name='BrokenEquipmentReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_filed', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField()),
                ('investigation', models.TextField(blank=True, null=True)),
                ('status', models.CharField(choices=[('U', 'Unread'), ('A', 'Acknowledged'), ('W', 'WIP'), ('B', 'Blocked'), ('C', 'Closed')], max_length=1, null=True)),
                ('broken_system', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gig.System')),
                ('reported_broken_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
