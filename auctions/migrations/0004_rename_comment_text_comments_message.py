# Generated by Django 5.0.6 on 2024-09-04 08:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auctions', '0003_alter_auctionlisting_seller'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comments',
            old_name='comment_text',
            new_name='message',
        ),
    ]
