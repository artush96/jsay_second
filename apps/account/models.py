from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import (
    BaseUserManager, PermissionsMixin, AbstractBaseUser
)
from django.contrib.auth.models import Group as BaseGroup
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import cached_property
from django.utils import timezone
from django.utils.dateparse import parse_date
from datetime import datetime, timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from apps.core.mailer import Mailer


def bottles_variants_default():
    return [100, 200, 300, 500]


class CUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_('Адрес электронной почты обязателен'))
        email = self.normalize_email(email)
        user = self.model(email=email.lower(), **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class AbstractCUser(AbstractBaseUser, PermissionsMixin):
    gender_type = (
        ('0', '--'),
        ('1', _('М')),
        ('2', _('Ж')),
    )
    auth_by = (
        ('0', _('Соц. сети')),
        ('1', _('Эл. почта')),
    )
    email = models.EmailField(unique=True, verbose_name=_('адрес электронной почты'))
    email_send_time = models.DateTimeField(verbose_name=_('время отправки письма активации'), null=True, blank=True)
    check_email = models.BooleanField(verbose_name=_('необходимо проверить эл. почту'), default=True)
    first_name = models.CharField(verbose_name=_('имя'), max_length=30)
    last_name = models.CharField(verbose_name=_('фамилия'), max_length=150, null=True, blank=True)
    middle_name = models.CharField(_('отчество'), max_length=30, null=True, blank=True)
    gender = models.CharField(max_length=25, choices=gender_type, default=0, verbose_name=_('пол'))
    water = models.IntegerField(verbose_name=_('норма воды'), default=1500)
    bottles = ArrayField(
        models.IntegerField(),
        default=bottles_variants_default,
        verbose_name=_('варианты бутылок')
    )
    # The field is for check water overrun
    water_norm = ArrayField(models.DateField(), verbose_name=_('дни превышения нормы'), default=list, blank=True)
    # The field is for check daily rate series
    d_rate = ArrayField(models.DateField(), verbose_name=_('даты дневной нормы'), default=list, blank=True)
    # The field is for check daily active series
    d_active = ArrayField(models.DateField(), verbose_name=_('даты посещений'), default=list, blank=True)
    expiry_date = models.DateTimeField(verbose_name=_('срок действия подписки'), null=True, blank=True)
    auth_attempt = models.IntegerField(verbose_name=_('попытки авторизации'), default=0)
    is_blocked = models.DateTimeField(verbose_name=_('заблокирован до'), null=True, blank=True)
    newsletters = models.BooleanField(verbose_name=_('подписка на новости'), default=True)
    is_staff = models.BooleanField(verbose_name=_('статус персонала'), default=False)
    is_active = models.BooleanField(verbose_name=_('активный'), default=True)
    date_joined = models.DateTimeField(verbose_name=_('дата регистрации'), default=timezone.now)
    last_seen = models.DateTimeField(auto_now_add=True)
    authorized = models.CharField(max_length=25, choices=auth_by, default=0, verbose_name=_('авторизован по'))

    objects = CUserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = _('учетная запись')
        verbose_name_plural = _('Учетные записи')
        abstract = True

    def __str__(self):
        return str(self.email)

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def daily_rate_count(self, date):
        if isinstance(date, str):
            date = parse_date(date)
        if (date - timedelta(1)) in self.d_rate:
            self.d_rate.append(date)
            count = len(self.d_rate)
            self.save(update_fields=['d_rate'])
            return count
        else:
            self.d_rate.clear()
            self.d_rate.append(date)
            self.save(update_fields=['d_rate'])
            return len(self.d_rate)

    def daily_active(self, date):
        today = parse_date(date)
        yesterday = today - timedelta(1)
        if yesterday and today in self.d_active:
            return len(self.d_active) - 1
        elif yesterday in self.d_active and today not in self.d_active:
            self.d_active.append(today)
            self.save(update_fields=['d_active'])
            return len(self.d_active) - 1
        else:
            self.d_active.clear()
            self.d_active.append(today)
            self.save(update_fields=['d_active'])
            return len(self.d_active) - 1

    def reset_d_rate(self):
        self.d_rate.clear()
        self.save(update_fields=['d_rate'])

    def reset_d_active(self):
        self.d_active.clear()
        self.save(update_fields=['d_active'])

    @cached_property
    def token(self):
        refresh = RefreshToken.for_user(self)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    @cached_property
    def auth_provider(self):
        if self.authorized == '0':
            now = datetime.now()
            social = self.social_auth.filter(modified__lte=now).order_by('-modified').first()
            return {"social": True, "provider": social.provider}
        return {"social": False}


# Base Group model
# class Group(BaseGroup):
#     class Meta:
#         verbose_name = _('группа')
#         verbose_name_plural = _('Группы')
#         proxy = True


class CUser(AbstractCUser):

    def __init__(self, *args, **kwargs):
        self.mail = Mailer()
        super().__init__(*args, **kwargs)

    def send_email_verification(self, url, uid, token):
        self.mail.send_messages(
            subject=_('Активациия'),
            template='notifications/acc_active_email.html',
            context={'user': self, 'url': url, 'uid': uid, 'token': token},
            to_emails=[self.email]
        )

    def password_reset_email(self, password):
        self.mail.send_messages(
            subject=_('Сброс пароля'),
            template='notifications/password_reset.html',
            context={'email': self.email, 'password': password},
            to_emails=[self.email]
        )

    def send_change_email_code(self, email, code):
        self.mail.send_messages(
            subject=_('Проверочный код'),
            template='notifications/change_email.html',
            context={'code': code},
            to_emails=[email]
        )

    class Meta(AbstractCUser.Meta):
        swappable = 'AUTH_USER_MODEL'


# class ChangeEmail(models.Model):
#     id = models.AutoField(primary_key=True)
#     owner = models.ForeignKey(CUser, related_name="change_email",
#                               verbose_name=_('владелец'), on_delete=models.CASCADE)
#     email = models.EmailField(verbose_name=_('новый адрес электронной почты'), null=True, blank=True)
#     old_email = models.EmailField(verbose_name=_('старый адрес электронной почты'), null=True, blank=True)
#     code = models.CharField(max_length=4, verbose_name=_('проверочный код'))
#     ip_address = models.GenericIPAddressField(_("IP адрес отправителя"), default="127.0.0.1")
#     attempts = models.IntegerField(_("неудачные попытки"), default=0)
#     is_confirm = models.BooleanField(verbose_name=_('статус проверки старого адреса'), default=False)
#     is_change = models.BooleanField(verbose_name=_('статус проверки нового адреса'), default=False)
#     blocked_time = models.DateTimeField(verbose_name=_('время блокировки'), null=True, blank=True)
#     created = models.DateTimeField(verbose_name=_('создан'), auto_now_add=True)
#
#     def __str__(self):
#         return str(self.id)
#
#     class Meta:
#         verbose_name = _("изменение эл. почты")
#         verbose_name_plural = _("Изменение эл. почт")
#
#     def reset_attempts(self, confirm=False, change=False):
#         self.attempts = 0
#         self.is_confirm = confirm
#         self.is_change = change
#         self.save(update_fields=['attempts', 'is_confirm', 'is_change', 'email', 'old_email'])
#
#     def inc_attempts(self):
#         self.attempts += 1
#         self.save(update_fields=['attempts', 'blocked_time'])

#
# class DailyWater(models.Model):
#     id = models.AutoField(primary_key=True)
#     owner = models.ForeignKey(CUser, related_name="daily_water",
#                               verbose_name=_('владелец'), on_delete=models.CASCADE)
#     water = models.IntegerField(verbose_name=_('дневная норма воды'), default=0)
#     milliliter = models.IntegerField(verbose_name=_('миллилитр'), default=0)
#     percent = models.IntegerField(verbose_name=_('процент выполнения'), default=0)
#     overrun = models.BooleanField(verbose_name=_('условие перерасхода'), default=False)
#     done = models.BooleanField(verbose_name=_('достигнуто'), default=False)
#     count = models.IntegerField(verbose_name=_('счетчик пополнений после достижения'), default=0)
#     date = models.DateField(verbose_name=_('дата'))
#
#     def __str__(self):
#         return str(self.id)
#
#     class Meta:
#         verbose_name = _("выпитая вода")
#         verbose_name_plural = _("Выпитая вода")
#
#     def drink_water(self, milliliter):
#         self.milliliter += milliliter
#         if self.milliliter >= self.water:
#             self.count += 1
#             self.done = True
#         elif self.done:
#             self.count += 1
#         self.save()
#         # drunk_water.send(sender=DailyWater, instance=self)
#         daily_rate = UserAwardDailyRate.load(
#             self.owner,
#             self.owner.daily_rate_count(self.date),
#             self.date
#         ) if self.count == 1 else None
#         first_drink = UserAwardSingle.first_drink(self.owner, 's1', self.date)
#         drink_award = self.owner.drink_awards.all().\
#             filter(open=True).first().update_award(milliliter, self.date, datetime.now())
#         return {
#             "daily_norm": self,
#             "drink_award": drink_award,
#             "rate_award": daily_rate,
#             "first_drink": first_drink
#         }
#
#     @cached_property
#     def exec_percent_per_day(self):
#         return round((self.milliliter * 100) / self.water)
#
#     @classmethod
#     def load(cls, owner, date):
#         instance, created = cls.objects.get_or_create(owner=owner, date=date, defaults={"water": owner.water})
#         if created:
#             instance.save()
#         return instance


# class UserAwardWaterDrink(models.Model):
#     id = models.AutoField(primary_key=True)
#     owner = models.ForeignKey(
#         CUser,
#         related_name='drink_awards',
#         verbose_name=_('владелец'),
#         on_delete=models.CASCADE
#     )
    # award = models.ForeignKey(
    #     AwardWaterDrink,
    #     verbose_name=_('тип достижения'),
    #     on_delete=models.CASCADE
    # )
    # counter = models.IntegerField(verbose_name=_('повторения'), default=0)
    # milliliter = models.IntegerField(verbose_name=_('миллилитр'), default=0)
    # open = models.BooleanField(verbose_name=_('открыт'), default=True)
    # received = models.BooleanField(verbose_name=_('получено'), default=False)
    # users_percent = models.IntegerField(verbose_name=_('процент выполнивших'), default=0)
    # received_date = models.DateField(verbose_name=_('дата получения'), null=True, blank=True)
    # created = models.DateTimeField(verbose_name=_('время получения'), default=datetime.now)
    #
    # def __str__(self):
    #     return str(self.id)
    #
    # class Meta:
    #     verbose_name = _("достижение выпитой воды")
    #     verbose_name_plural = _("Достижения выпитой воды")
    #     ordering = ['id']
    #
    # def update_award(self, milliliter, date, now):
    #     self.milliliter += milliliter
    #     self.received_date = date
    #     self.created = now
    #     self.save()
    #     return self
    #
    # @classmethod
    # def done_users_percent(cls, award):
    #     return round(
    #         cls.objects.filter(award=award, received=True).count() / CUser.objects.filter(
    #             check_email=False).count() * 100
    #     )


# class UserAwardDailyRate(models.Model):
#     id = models.AutoField(primary_key=True)
#     owner = models.ForeignKey(
#         CUser,
#         related_name='rate_awards',
#         verbose_name=_('владелец'),
#         on_delete=models.CASCADE
#     )
    # award = models.ForeignKey(
    #     AwardDailyRate,
    #     verbose_name=_('тип достижения'),
    #     on_delete=models.CASCADE
    # )
    # counter = models.IntegerField(verbose_name=_('повторения'), default=0)
    # users_percent = models.IntegerField(verbose_name=_('процент выполнивших'), default=0)
    # received_date = models.DateField(verbose_name=_('дата получения'), null=True, blank=True)
    # created = models.DateTimeField(verbose_name=_('время получения'), default=datetime.now)
    #
    # def __str__(self):
    #     return str(self.id)
    #
    # class Meta:
    #     verbose_name = _("достижение нормы воды")
    #     verbose_name_plural = _("Достижения нормы воды")
    #     ordering = ['id']
    #
    # @classmethod
    # def done_users_percent(cls, award):
    #     return round(
    #         cls.objects.filter(award=award).count() / CUser.objects.filter(
    #             check_email=False).count() * 100
    #     )
    #
    # @classmethod
    # def get_non_repeat_count(cls, owner):
    #     count = cls.objects.filter(owner=owner, award__repeat=False).count()
    #     return count

    # @classmethod
    # def load(cls, owner, day, date):
    #     if cls.get_non_repeat_count(owner) == AwardDailyRate.get_non_repeat_count():
    #         try:
    #             award = AwardDailyRate.objects.filter(repeat=True).get(day=day)
    #         except AwardDailyRate.DoesNotExist:
    #             return None
    #         instance, created = cls.objects.get_or_create(
    #             owner=owner,
    #             award=award,
    #             defaults={"received_date": date}
    #         )
    #         instance.owner.reset_d_rate()
    #         if created:
    #             instance.save()
    #             return instance
    #         instance.counter += 1
    #         instance.save()
    #         return instance
    #     try:
    #         award = AwardDailyRate.objects.filter(repeat=False).get(day=day)
    #     except AwardDailyRate.DoesNotExist:
    #         return None
    #     instance, created = cls.objects.get_or_create(
    #         owner=owner,
    #         award=award,
    #         defaults={"received_date": date}
    #     )
    #     if created:
    #         return instance
    #     return None


# class UserAwardDailyActive(models.Model):
#     id = models.AutoField(primary_key=True)
#     owner = models.ForeignKey(
#         CUser,
#         related_name='active_awards',
#         verbose_name=_('владелец'),
#         on_delete=models.CASCADE
#     )
    # award = models.ForeignKey(
    #     AwardDailyActive,
    #     verbose_name=_('тип достижения'),
    #     on_delete=models.CASCADE
    # )
    # counter = models.IntegerField(verbose_name=_('повторения'), default=0)
    # users_percent = models.IntegerField(verbose_name=_('процент выполнивших'), default=0)
    # date = models.DateField(verbose_name=_('дата получения'), null=True, blank=True)
    # created = models.DateTimeField(verbose_name=_('время получения'), default=datetime.now)

    # def __str__(self):
    #     return str(self.id)
    #
    # class Meta:
    #     verbose_name = _("достижение дневной активности")
    #     verbose_name_plural = _("Достижения активности")
    #     ordering = ['id']
    #
    # @classmethod
    # def done_users_percent(cls, award):
    #     return round(
    #         cls.objects.filter(award=award).count() / CUser.objects.filter(
    #             check_email=False).count() * 100
    #     )
    #
    # @classmethod
    # def get_non_repeat_count(cls, owner):
    #     count = cls.objects.filter(owner=owner, award__repeat=False).count()
    #     return count
    #
    # @classmethod
    # def load(cls, owner, day, date):
    #     if (cls.get_non_repeat_count(owner) + 1) == AwardDailyActive.get_non_repeat_count():
    #         try:
    #             award = AwardDailyActive.objects.filter(repeat=True).get(day=day)
    #         except AwardDailyActive.DoesNotExist:
    #             return None
    #         instance, created = cls.objects.get_or_create(owner=owner, award=award)
    #         instance.owner.reset_d_active()
    #         if created:
    #             instance.date = date
    #             instance.save()
    #             return instance
    #         instance.counter += 1
    #         instance.save()
    #         return instance
    #     try:
    #         award = AwardDailyActive.objects.filter(repeat=False).get(day=day)
    #     except AwardDailyActive.DoesNotExist:
    #         return None
    #     instance, created = cls.objects.get_or_create(owner=owner, award=award)
    #     if created:
    #         instance.date = date
    #         instance.save()
    #         return instance
    #     return None


# class UserAwardSingle(models.Model):
#     id = models.AutoField(primary_key=True)
#     owner = models.ForeignKey(
#         CUser,
#         related_name='single_awards',
#         verbose_name=_('владелец'),
#         on_delete=models.CASCADE
#     )
#     award = models.ForeignKey(
#         AwardSingle,
#         verbose_name=_('тип достижения'),
#         on_delete=models.CASCADE
#     )
#     counter = models.IntegerField(verbose_name=_('повторения'), default=0)
#     users_percent = models.IntegerField(verbose_name=_('процент выполнивших'), default=0)
#     date = models.DateField(verbose_name=_('дата получения'), null=True, blank=True)
#     created = models.DateTimeField(verbose_name=_('время получения'), default=datetime.now)
#
#     def __str__(self):
#         return str(self.id)
#
#     class Meta:
#         verbose_name = _("одиночное достижение")
#         verbose_name_plural = _("Одиночные достижения")
#         ordering = ['id']
#
#     @classmethod
#     def done_users_percent(cls, award):
#         return round(
#             cls.objects.filter(award=award).count() / CUser.objects.filter(
#                 check_email=False).count() * 100
#         )
#
#     @classmethod
#     def load(cls, owner, award):
#         instance, created = cls.objects.update_or_create(
#             owner=owner, award=award, defaults={"date": datetime.now()}
#         )
#         if created:
#             instance.users_percent = instance.done_users_percent(instance.award)
#             instance.save()
#         return instance
#
#     @classmethod
#     def first_drink(cls, owner, code, date):
#         try:
#             award = AwardSingle.objects.get(photo_code=code)
#         except AwardSingle.DoesNotExist:
#             return None
#         instance, created = cls.objects.get_or_create(owner=owner, award=award)
#         if created:
#             instance.date = date
#             instance.save()
#             return instance
#         return None
