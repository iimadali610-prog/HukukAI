from django.db import migrations
from pgvector.django import VectorExtension


class Migration(migrations.Migration):  # <--- 'migrations.Migration' olarak düzeltildi

    dependencies = [
        ('core', '0001_initial'),  # İlk migration adın neyse o kalmalı
    ]

    operations = [
        VectorExtension(),
    ]
