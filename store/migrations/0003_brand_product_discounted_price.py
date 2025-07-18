# Generated by Django 5.2.3 on 2025-07-03 09:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0002_remove_product_image_productimage'),
    ]

    operations = [
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('slug', models.SlugField(max_length=255, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='discounted_price',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Price after discount, if applicable.', max_digits=10, null=True, verbose_name='Discounted Price'),
        ),
    ]
