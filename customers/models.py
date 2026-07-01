from django.db import models
from django.core.validators import RegexValidator


mobile_validator = RegexValidator(
    regex=r'^\d{10}$',
    message='Enter a valid 10-digit mobile number.'
)

aadhar_validator = RegexValidator(
    regex=r'^\d{12}$',
    message='Enter a valid 12-digit Aadhar number.'
)


class Customer(models.Model):
    name = models.CharField(max_length=100)
    mobile_number = models.CharField(
        max_length=10,
        unique=True,
        validators=[mobile_validator],
        help_text='10-digit mobile number'
    )
    aadhar_number = models.CharField(
        max_length=12,
        unique=True,
        validators=[aadhar_validator],
        help_text='12-digit Aadhar number'
    )
    bill_number = models.CharField(
        max_length=50,
        unique=True,
        help_text='Bill / Invoice number from purchase'
    )
    registered_at = models.DateTimeField(auto_now_add=True)
    has_played = models.BooleanField(default=False)

    class Meta:
        ordering = ['-registered_at']
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        indexes = [
            # date-range filters on dashboard, report, charts, and default ordering
            models.Index(fields=['-registered_at'], name='customer_registered_at_idx'),
            # played_count filter: Customer.objects.filter(has_played=True)
            models.Index(fields=['has_played'], name='customer_has_played_idx'),
            # combined query: filter(registered_at__date__range, has_played=True)
            models.Index(fields=['registered_at', 'has_played'], name='customer_reg_played_idx'),
        ]

    def __str__(self):
        return f"{self.name} — {self.mobile_number}"

    def mask_aadhar(self):
        """Return Aadhar with only last 4 digits visible."""
        return 'XXXX-XXXX-' + self.aadhar_number[-4:]
