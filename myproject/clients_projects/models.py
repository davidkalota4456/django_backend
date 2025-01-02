from django.db import models
from django.utils.timezone import now


class ClientProject(models.Model):
    client_name = models.CharField(max_length=255)
    project_picture = models.ImageField(upload_to='project_pictures/', blank=True, null=True)
    completed = models.BooleanField(default=False)
    project_info = models.TextField()
    time_to_complete = models.IntegerField()
    creation_date = models.DateTimeField(default=now)
    start_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.client_name} - {self.project_info[:50]}"


# Create your models here.
