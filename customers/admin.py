from django.contrib import admin
from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'mobile_number', 'aadhar_number', 'bill_number', 'has_played', 'registered_at']
    list_filter = ['has_played', 'registered_at']
    search_fields = ['name', 'mobile_number', 'bill_number']
    readonly_fields = ['registered_at']
    ordering = ['-registered_at']
