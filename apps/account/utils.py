# from django.contrib.auth import get_user_model
# UserModel = get_user_model()
#
#
# class DrinkAwardsAdapter:
#     USER_COUNT = UserModel.objects.filter(check_email=False)
#     DAILY_NORM = DailyWater.objects.all()
#     DAILY_RATE = UserAwardDailyRate.objects.all()
#     DRINK_AWARD = UserAwardWaterDrink.objects.all()
#     SINGLE_AWARD = UserAwardSingle.objects.all()
#
#     @classmethod
#     def do_notify_daily_norm(cls, obj):
#         if obj.count == 1:
#             total_per_day = cls.DAILY_NORM.filter(date__exact=obj.date, count__gt=0).count()
#             return {
#                 "notify": True,
#                 "milliliter": obj.milliliter,
#                 "percent": round(total_per_day / cls.USER_COUNT.count() * 100),
#                 "date": obj.date
#             }
#         return {"notify": False}
#
#     @classmethod
#     def do_notify_first_drink(cls, obj):
#         if obj:
#             total_per_day = cls.SINGLE_AWARD.filter(award=obj.award).count()
#             users_percent = round(total_per_day / cls.USER_COUNT.count() * 100)
#             obj.users_percent = users_percent
#             obj.save(update_fields=['users_percent'])
#             return {
#                 "notify": True,
#                 "percent": users_percent,
#                 "award": AwardSingleSerializer(obj.award).data,
#                 "date": obj.date
#             }
#         return {"notify": False}
#
#     @classmethod
#     def do_notify_drink_award(cls, obj):
#         if obj.received:
#             if not obj.award.repeat:
#                 total_received = cls.DRINK_AWARD.filter(award=obj.award, received=True).count()
#                 users_percent = round(total_received / cls.USER_COUNT.count() * 100)
#                 obj.users_percent = users_percent
#                 obj.save(update_fields=['users_percent'])
#                 return {
#                     "notify": True,
#                     "percent": users_percent,
#                     "date": obj.received_date,
#                     "award": AwardWaterDrinkSerializer(obj.award).data
#                 }
#             elif obj.milliliter == 0:
#                 total_received = cls.DRINK_AWARD.filter(award=obj.award, counter=obj.counter, received=True).count()
#                 users_percent = round(total_received / cls.USER_COUNT.count() * 100)
#                 obj.users_percent = users_percent
#                 obj.save(update_fields=['users_percent'])
#                 return {
#                     "notify": True,
#                     "percent": users_percent,
#                     "date": obj.received_date,
#                     "award": AwardWaterDrinkSerializer(obj.award).data
#                 }
#         return {"notify": False}
#
#     @classmethod
#     def do_notify_daily_rate(cls, obj):
#         if obj:
#             if not obj.award.repeat:
#                 total_received = cls.DAILY_RATE.filter(award=obj.award).count()
#                 users_percent = round(total_received / cls.USER_COUNT.count() * 100)
#                 obj.users_percent = users_percent
#                 obj.save(update_fields=['users_percent'])
#                 return {
#                     "notify": True,
#                     "percent": users_percent,
#                     "date": obj.received_date,
#                     "award": AwardDailyRateSerializer(obj.award).data
#                 }
#             total_received = cls.DAILY_RATE.filter(award=obj.award, counter=obj.counter).count()
#             users_percent = round(total_received / cls.USER_COUNT.count() * 100)
#             obj.users_percent = users_percent
#             obj.save(update_fields=['users_percent'])
#             return {
#                 "notify": True,
#                 "percent": users_percent,
#                 "date": obj.received_date,
#                 "award": AwardDailyRateSerializer(obj.award).data
#             }
#         return {"notify": False}
#
#
# class DailyActiveAdapter:
#     USER_COUNT = UserModel.objects.filter(check_email=False)
#     DAIL_ACTIVE = UserAwardDailyActive.objects.all()
#
#     @classmethod
#     def do_notify_daily_active(cls, obj):
#         if obj:
#             if obj.counter == 0:
#                 total_received = cls.DAIL_ACTIVE.filter(award=obj.award).count()
#                 users_percent = round(total_received / cls.USER_COUNT.count() * 100)
#                 obj.users_percent = users_percent
#                 obj.save(update_fields=['users_percent'])
#                 return {
#                     "notify": True,
#                     "percent": users_percent,
#                     "date": obj.date,
#                     "award": AwardDailyActiveSerializer(obj.award).data
#                 }
#             total_received = cls.DAIL_ACTIVE.filter(award=obj.award, counter=obj.counter).count()
#             users_percent = round(total_received / cls.USER_COUNT.count() * 100)
#             obj.users_percent = users_percent
#             obj.save(update_fields=['users_percent'])
#             return {
#                 "notify": True,
#                 "percent": users_percent,
#                 "date": obj.date,
#                 "award": AwardDailyActiveSerializer(obj.award).data
#             }
#         return {"notify": False}
