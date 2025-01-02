from django.db import models
from django.core.validators import RegexValidator

class User(models.Model):
    # Username field - This could be a name or any other identifier
    username = models.CharField(max_length=100, unique=True)

    # Gmail field
    gmail = models.EmailField(
        max_length=100,
        unique=True,
        validators=[RegexValidator(regex=r'^[a-zA-Z0-9._%+-]+@gmail\.com$', message='Must be a valid Gmail address')]
    )

    def __str__(self):
        return f"{self.username} ({self.gmail})"


