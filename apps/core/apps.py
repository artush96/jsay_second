from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ApiConfig(AppConfig):
    name = 'apps.core'
    verbose_name = _('Основные настройки')
