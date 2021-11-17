from django.contrib import admin
from apps.core.models import Tariffs, Questions, LegalDocs, AppVersion, Benefit, Advices


@admin.register(Tariffs)
class TariffsAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')


@admin.register(Questions)
class QuestionsAdmin(admin.ModelAdmin):
    list_display = ('id', 'question')


@admin.register(LegalDocs)
class LegalDocsAdmin(admin.ModelAdmin):
    list_display = ('id',)


@admin.register(AppVersion)
class AppVersionAdmin(admin.ModelAdmin):
    list_display = ('id', 'version')


@admin.register(Benefit)
class BenefitAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')


@admin.register(Advices)
class AdvicesAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')
