from django.conf import settings
from celery import shared_task
from datetime import timedelta
from apps.account.models import DailyWater, UserAwardWaterDrink
from apps.achievement.models import AwardWaterDrink


# Проверка превышения нормы воды
@shared_task
def _check_account_water_overrun(obj_id):
    obj = DailyWater.objects.get(pk=obj_id)
    if (obj.date - timedelta(1)) in obj.owner.water_norm:
        if (len(obj.owner.water_norm) + 1) == settings.CONTINUITY_EXC_WATER:
            # to do send push notification
            # send new water value {obj.milliliter}
            obj.owner.water_norm.clear()
        else:
            obj.owner.water_norm.append(obj.date)
        obj.overrun = True
        obj.save(update_fields=['overrun'])
        obj.owner.save(update_fields=['water_norm'])
    else:
        obj.owner.water_norm.clear()
        obj.owner.water_norm.append(obj.date)
        obj.owner.save(update_fields=['water_norm'])
        obj.overrun = True
        obj.save(update_fields=['overrun'])


# Открываем следующее достижение
@shared_task
def _open_next_water_drink_achievement(obj_id):
    obj = UserAwardWaterDrink.objects.get(pk=obj_id)
    award = AwardWaterDrink.objects.filter(milliliter__gt=obj.award.milliliter).first()
    UserAwardWaterDrink.objects.create(owner=obj.owner, award=award)
