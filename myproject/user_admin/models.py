from django.db import models

class CustomUserAdmin(models.Model):
    # Admin username
    username = models.CharField(max_length=100)

    # Admin email
    email = models.EmailField()

    password = models.CharField(max_length=255, null=True)  # Temporarily allow null


    def __str__(self):
        return self.username
