from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    street_address = models.CharField("Street address", max_length=255, blank=True, null=True)
    city = models.CharField("City", max_length=100, blank=True, null=True)
    postal_code = models.CharField("ZIP code", max_length=20, blank=True, null=True)
    country = models.CharField("Country", max_length=100, blank=True, null=True)

    def __str__(self):
        return self.username

    @property
    def full_address(self):
        return f"{self.street_address}, {self.city}, {self.postal_code}, {self.country}"