from django.db import models

class ZoomMeeting(models.Model):
    client_name = models.CharField(max_length=255, blank=True, null=True)
    client_gmail = models.CharField(max_length=255, blank=True, null=True)  # Name of the client, nullable
    duration = models.PositiveIntegerField(help_text="Duration in minutes", blank=True, null=True)  # Duration in minutes, nullable
    topic = models.CharField(max_length=255, blank=True, null=True)  # Meeting topic, nullable
    meeting_id = models.CharField(max_length=255, unique=True, blank=True, null=True)  # Unique Zoom meeting ID, nullable
    join_url = models.URLField(max_length=500, blank=True, null=True)  # Zoom meeting join URL, nullable
    meeting_passed = models.BooleanField(default=False)
    admin_meeting_time = models.DateTimeField(blank=True, null=True)  # Admin's time zone date and time (combined)
    utc_time = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.client_name} - {self.admin_meeting_time.strftime('%Y-%m-%d %H:%M:%S')}"

    

    def mark_as_passed(self):
        self.meeting_passed = True
        self.save()

    # Method to delete the meeting
    def delete_meeting(self):
        self.delete()

    class Meta:
        ordering = ['-admin_meeting_time']  # Order by date and time
