from django.db import migrations
from pgvector.django import VectorExtension

class Migration(Migration):

    dependencies = [
        ('core', '0001_initial'), # Eğer sizde ilk migration adı farklıysa onu yazın
    ]

    operations = [
        VectorExtension(),
    ]