from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('artist', 'Artist'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='artist')

    def __str__(self):
        return self.username
