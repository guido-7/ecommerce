from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # We could add extra fields here, e.g.:
    # phone_number = models.CharField(max_length=15, blank=True)
    # address = models.TextField(blank=True)
    pass # For now, we'll just use the default fields.

def __str__(self):
    return self.username