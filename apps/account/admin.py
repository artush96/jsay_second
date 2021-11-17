from django.contrib import admin
# from social_django.models import Association, Nonce, UserSocialAuth
from .models import CUser
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group as StockGroup
from django.utils.translation import ugettext_lazy as _
from .forms import UserChangeForm, UserCreationForm


@admin.register(CUser)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'email_send_time', 'check_email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'middle_name',
                                         'gender', 'water', 'water_norm', 'd_rate', 'd_active',
                                         'expiry_date', 'auth_attempt',
                                         'is_blocked', 'newsletters')}),
        (_('Permissions'), {'fields': ('is_staff', 'is_superuser')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ('id', 'email', 'first_name')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('email',)
    ordering = ('id',)


admin.site.unregister(StockGroup)


# @admin.register(Group)
# class GroupAdmin(BaseGroupAdmin):
#     pass


# admin.site.unregister(Association)
# admin.site.unregister(Nonce)
# admin.site.unregister(UserSocialAuth)
#
#
# @admin.register(ChangeEmail)
# class ChangeEmailAdmin(admin.ModelAdmin):
#     list_display = ('id', 'owner')
#
#
# @admin.register(DailyWater)
# class DailyWaterAdmin(admin.ModelAdmin):
#     list_display = ('id', 'owner')
#
#
# @admin.register(UserAwardWaterDrink)
# class UserAwardWaterDrinkAdmin(admin.ModelAdmin):
#     list_display = ('id', 'owner')
#
#
# @admin.register(UserAwardDailyRate)
# class UserAwardDailyRateAdmin(admin.ModelAdmin):
#     list_display = ('id', 'owner')
#
#
# @admin.register(UserAwardDailyActive)
# class UserAwardDailyActiveAdmin(admin.ModelAdmin):
#     list_display = ('id', 'owner')
#
#
# @admin.register(UserAwardSingle)
# class UserAwardSingleAdmin(admin.ModelAdmin):
#     list_display = ('id', 'owner')
