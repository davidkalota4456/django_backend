from django.db import models



class ClientMessage(models.Model):
    PREFERRED_WAYS = [
        ('EMAIL', 'Email'),
        ('WHATSAPP', 'WhatsApp'),
    ]

    name = models.CharField(max_length=255)
    preferred_way_to_connect = models.CharField(
        max_length=50,
        choices=PREFERRED_WAYS,
        default='EMAIL',
    )
    gmail = models.EmailField(blank=True, null=True)
    whatsapp_number = models.CharField(max_length=15, blank=True, null=True)
    msg_info = models.TextField()
    is_client = models.BooleanField(default=False)
    admin_response = models.TextField(blank=True, null=True)  # New field for admin responses


    def __str__(self):
        return f"{self.name} - {'Client' if self.is_client else 'Interest'}"

