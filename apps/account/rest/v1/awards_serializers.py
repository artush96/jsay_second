# from rest_framework import serializers
# from apps.account.utils import DrinkAwardsAdapter, DailyActiveAdapter
# from apps.account.models import UserAwardWaterDrink, UserAwardDailyActive, \
#     UserAwardDailyRate, UserAwardSingle
# from apps.achievement.rest.v1.serializers import AwardWaterDrinkSerializer, \
#     AwardDailyRateSerializer, AwardDailyActiveSerializer, AwardSingleSerializer
# from apps.achievement.models import AwardWaterDrink, AwardDailyRate, AwardDailyActive, AwardSingle
#
#
# class DrinkWaterSerializer(serializers.Serializer):
#     date = serializers.DateField(required=True)
#     milliliter = serializers.IntegerField(required=True)
#
#     @staticmethod
#     def get_possible_awards(obj):
#         awards = DrinkAwardsAdapter()
#         daily_norm = obj['daily_norm']
#         drink_award = obj['drink_award']
#         daily_rate = obj['rate_award']
#         first_drink = obj['first_drink']
#         data = {
#             'daily_norm': awards.do_notify_daily_norm(daily_norm),
#             'first_drink': awards.do_notify_first_drink(first_drink),
#             'drink_award': awards.do_notify_drink_award(drink_award),
#             'daily_rate': awards.do_notify_daily_rate(daily_rate)
#         }
#         return data
#
#
# class DailyActiveSerializer(serializers.Serializer):
#     date = serializers.DateField(required=True)
#
#     @staticmethod
#     def get_active_awards(obj):
#         awards = DailyActiveAdapter()
#         data = dict(awards.do_notify_daily_active(obj))
#         return data
#
#
# class UserAwardWaterDrinkSerializer(serializers.ModelSerializer):
#     award = AwardWaterDrinkSerializer()
#     date = serializers.DateField(source='received_date')
#     percent = serializers.SerializerMethodField()
#     users_percent = serializers.SerializerMethodField()
#
#     class Meta:
#         model = UserAwardWaterDrink
#         fields = ("counter", "percent", "date", "users_percent", "created", "award")
#
#     def to_representation(self, instance):
#         representation = super(UserAwardWaterDrinkSerializer, self).to_representation(instance)
#         representation['created'] = round(instance.created.timestamp())
#         return representation
#
#     def get_percent(self, obj):
#         if not obj.award.repeat:
#             return round(obj.milliliter / obj.award.milliliter * 100)
#         return round(obj.milliliter / obj.award.rep_milli * 100)
#
#     def get_users_percent(self, obj):
#         if obj.received:
#             return obj.users_percent
#         return obj.done_users_percent(obj.award)
#
#
# class UserAwardDailyActiveSerializer(serializers.ModelSerializer):
#     award = AwardDailyActiveSerializer()
#
#     class Meta:
#         model = UserAwardDailyActive
#         fields = ("counter", "date", "users_percent", "created", "award")
#
#     def to_representation(self, instance):
#         representation = super(UserAwardDailyActiveSerializer, self).to_representation(instance)
#         representation['created'] = round(instance.created.timestamp())
#         return representation
#
#
# class UserAwardDailyRateSerializer(serializers.ModelSerializer):
#     award = AwardDailyRateSerializer()
#     date = serializers.DateField(source='received_date')
#
#     class Meta:
#         model = UserAwardDailyRate
#         fields = ("counter", "date", "users_percent", "created", "award")
#
#     def to_representation(self, instance):
#         representation = super(UserAwardDailyRateSerializer, self).to_representation(instance)
#         representation['created'] = round(instance.created.timestamp())
#         return representation
#
#
# class UserAwardSingleSerializer(serializers.ModelSerializer):
#     award = AwardSingleSerializer()
#
#     class Meta:
#         model = UserAwardSingle
#         fields = ("date", "users_percent", "created", "award")
#
#     def to_representation(self, instance):
#         representation = super(UserAwardSingleSerializer, self).to_representation(instance)
#         representation['created'] = round(instance.created.timestamp())
#         return representation
#
#
# class UserAwardsSerializer(serializers.Serializer):
#
#     @staticmethod
#     def get_user_awards(user):
#         drink_awards = user.drink_awards.all()
#         active_awards = user.active_awards.all()
#         rate_awards = user.rate_awards.all()
#         single_awards = user.single_awards.all()
#         data = {
#             "d_rate": len(user.d_rate),
#             "d_active": len(user.d_active),
#             "drink_awards": UserAwardWaterDrinkSerializer(drink_awards, many=True).data,
#             "active_awards": UserAwardDailyActiveSerializer(active_awards, many=True).data,
#             "rate_awards": UserAwardDailyRateSerializer(rate_awards, many=True).data,
#             "single_awards": UserAwardSingleSerializer(single_awards, many=True).data
#         }
#         closed_drink = AwardWaterDrink.objects.exclude(id__in=drink_awards.values_list('award_id', flat=True))
#         closed_active = AwardDailyActive.objects.exclude(id__in=active_awards.values_list('award_id', flat=True))
#         closed_rate = AwardDailyRate.objects.exclude(id__in=rate_awards.values_list('award_id', flat=True))
#         closed_single = AwardSingle.objects.exclude(id__in=single_awards.values_list('award_id', flat=True))
#         data["drink_awards"] += [{"award": e} for e in AwardWaterDrinkSerializer(closed_drink, many=True).data]
#         data["active_awards"] += [{"award": e} for e in AwardDailyActiveSerializer(closed_active, many=True).data]
#         data["rate_awards"] += [{"award": e} for e in AwardDailyRateSerializer(closed_rate, many=True).data]
#         data["single_awards"] += [{"award": e} for e in AwardSingleSerializer(closed_single, many=True).data]
#         return data
#
#
# class SingleAwardCreateSerializer(serializers.Serializer):
#     _type = (
#         ('1', 'Подписка'),
#         ('2', 'Чат'),
#         ('3', 'Отзыв'),
#     )
#     award_type = serializers.ChoiceField(choices=_type)
