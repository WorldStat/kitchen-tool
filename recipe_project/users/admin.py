from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser  # Make sure this matches your model name

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_paid_customer', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_paid_customer')
    
    # Add your custom fields to the "Edit User" page
    fieldsets = UserAdmin.fieldsets + (
        ('Premium Status', {'fields': ('is_paid_customer',)}),
    )