from django.contrib import admin
from .models import Customer, Gift


@admin.register(Gift)
class GiftAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    ordering = ['name']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'mobile_number', 'aadhar_number', 'bill_number', 'has_played', 'game_result', 'won_gift', 'registered_at']
    list_filter = ['has_played', 'game_result', 'registered_at']
    search_fields = ['name', 'mobile_number', 'bill_number']
    readonly_fields = ['registered_at']
    ordering = ['-registered_at']
