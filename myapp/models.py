from django.db import models
from django.core.validators import FileExtensionValidator


class Document(models.Model):
    docfile = models.FileField(upload_to='documents//%Y/%m/%d/%H')
