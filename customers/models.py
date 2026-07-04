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


class Gift(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Gift'
        verbose_name_plural = 'Gifts'

    def __str__(self):
        return self.name


class Customer(models.Model):
    RESULT_PENDING = 'pending'
    RESULT_WIN = 'win'
    RESULT_LOSS = 'loss'
    RESULT_CHOICES = [
        (RESULT_PENDING, 'Pending'),
        (RESULT_WIN, 'Win'),
        (RESULT_LOSS, 'Loss'),
    ]

    CONSOLATION_GIFT = 'Pay ₹1000 & Get Services Worth ₹1500 Gift Voucher'

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
    game_result = models.CharField(
        max_length=10,
        choices=RESULT_CHOICES,
        default=RESULT_PENDING,
    )
    won_gift = models.ForeignKey(
        Gift,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='winners',
    )

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

    @property
    def gift_display(self):
        if self.game_result == self.RESULT_WIN:
            return self.won_gift.name if self.won_gift else ''
        if self.game_result == self.RESULT_LOSS:
            return self.CONSOLATION_GIFT
        return ''
