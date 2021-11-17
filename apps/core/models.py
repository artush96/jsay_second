from django.db import models
from django.utils.translation import ugettext_lazy as _
import math


class Tariffs(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(verbose_name=_('название'), max_length=30)
    cost = models.IntegerField(verbose_name=_('стоимость'))
    price_per_month = models.IntegerField(verbose_name=_('цена за месяц'), default=0)
    month = models.IntegerField(verbose_name=_('количество месяцев'), default=0)
    unlimited = models.BooleanField(verbose_name=_('безлимитный'), default=False)
    discount = models.IntegerField(verbose_name=_('процент скидки'), default=0)
    created = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.unlimited:
            self.discount = math.ceil((1-self.cost/(self.price_per_month*self.month))*100)
        super(Tariffs, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = _("тариф")
        verbose_name_plural = _("Тарифы")


class Questions(models.Model):
    id = models.AutoField(primary_key=True)
    question = models.CharField(
        verbose_name=_('вопрос'),
        help_text=_('будут видны как варианты при отправке негативного отзыва'),
        max_length=30
    )
    created = models.DateField(auto_now_add=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = _("вопрос")
        verbose_name_plural = _("Вопросы")


class LegalDocs(models.Model):
    id = models.AutoField(primary_key=True)
    policy = models.TextField(verbose_name=_('политика конфиденциальности'), max_length=30000)
    terms = models.TextField(verbose_name=_('условия использования'), max_length=30000)
    created = models.DateField(auto_now_add=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = _("правовой документ")
        verbose_name_plural = _("Правовые документы")


class Benefit(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(verbose_name=_('заголовок'), max_length=100)
    text = models.TextField(verbose_name=_('текст'), max_length=300)
    link = models.URLField(_('ссылка на источник'))
    short_link = models.CharField(_('краткая ссылка'), max_length=100)
    created = models.DateField(auto_now_add=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = _("о пользе воды")
        verbose_name_plural = _("О пользе воды")


class Advices(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(verbose_name=_('заголовок'), max_length=100)
    text = models.TextField(verbose_name=_('текст'), max_length=300)
    link = models.URLField(_('ссылка на источник'))
    short_link = models.CharField(_('краткая ссылка'), max_length=100)
    created = models.DateField(auto_now_add=True)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = _("совет")
        verbose_name_plural = _("Советы")


class AppVersion(models.Model):
    id = models.AutoField(primary_key=True)
    version = models.CharField(verbose_name=_('версия приложения'), max_length=10)

    def __str__(self):
        return str(self.id)

    class Meta:
        verbose_name = _("версия приложения")
        verbose_name_plural = _("Версия приложения")
