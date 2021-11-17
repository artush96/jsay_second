from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import datetime
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from apps.core.tokens import account_activation_token
from django.conf import settings
from django.contrib.auth import get_user_model
UserModel = get_user_model()
# from .models import ChangeEmail, DailyWater, UserAwardWaterDrink, \
#     UserAwardDailyActive, UserAwardDailyRate
# from apps.achievement.models import AwardWaterDrink, AwardDailyRate, AwardDailyActive
# from .tasks import _check_account_water_overrun, _open_next_water_drink_achievement
# from apps.notification.models import Notifications


# @receiver(post_save, sender=UserModel)
# def create_user(sender, instance, created, **kwargs):
#     if created:
#         award = AwardWaterDrink.first_award()
#         UserAwardWaterDrink.objects.create(owner=instance, award=award)
#         Notifications.objects.create(owner=instance)
#         now = datetime.datetime.now()
#         if not instance.check_email:
#             instance.expiry_date = now + datetime.timedelta(7)
#             instance.save()
#         else:
#             instance.send_email_verification(
#                 settings.SITE_URL,
#                 urlsafe_base64_encode(force_bytes(instance.id)),
#                 account_activation_token.make_token(instance)
#             )
#             instance.email_send_time = now + datetime.timedelta(minutes=1)
#             instance.save()
#
#
# @receiver(pre_save, sender=ChangeEmail)
# def check_change_email_attempts(sender, instance, **kwargs):
#     if instance.attempts > 2:
#         now = datetime.datetime.now()
#         instance.blocked_time = now + datetime.timedelta(1)
#     elif instance.is_confirm and instance.is_change:
#         instance.old_email = instance.owner.email
#         instance.owner.email = instance.email
#         instance.owner.save()
#         instance.email = ''
#         instance.is_change = False
#         instance.is_confirm = False
#
#
# @receiver(pre_save, sender=DailyWater)
# def pre_check_daily_water(sender, instance, **kwargs):
#     instance.percent = instance.exec_percent_per_day
#     if instance.milliliter > instance.water and not instance.overrun:
#         _check_account_water_overrun.apply_async(args=(instance.id,), countdown=2)
#
#
# @receiver(pre_save, sender=UserAwardWaterDrink)
# def update_user_award_water_drink(sender, instance, **kwargs):
#     if not instance.award.repeat and not instance.received and instance.milliliter >= instance.award.milliliter:
#         instance.open = False
#         instance.received = True
#         instance.milliliter = instance.award.milliliter
#         _open_next_water_drink_achievement.apply_async(args=(instance.id,))
#     elif instance.award.repeat and not instance.received and instance.milliliter >= instance.award.rep_milli:
#         instance.received = True
#         instance.milliliter = 0
#     elif instance.received and instance.milliliter >= instance.award.rep_milli:
#         instance.counter += 1
#         instance.milliliter = 0
#
#
# @receiver(post_save, sender=UserAwardDailyActive)
# def reset_user_daily_active(sender, instance, **kwargs):
#     if (instance.owner.active_awards.filter(
#             award__repeat=False).count() + 1) \
#             == AwardDailyActive.get_non_repeat_count():
#         instance.owner.reset_d_active()
#
#
# @receiver(post_save, sender=UserAwardDailyRate)
# def reset_user_daily_rate(sender, instance, **kwargs):
#     if instance.owner.rate_awards.filter(
#             award__repeat=False).count() \
#             == AwardDailyRate.get_non_repeat_count():
#         instance.owner.reset_d_rate()
