from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ApiConfig(AppConfig):
    name = 'apps.account'
    verbose_name = _('Пользователи')

    def ready(self):
        import apps.account.signals
