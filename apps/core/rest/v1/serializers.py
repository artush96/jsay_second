from rest_framework import serializers
from apps.core.models import Questions, LegalDocs, Benefit, Advices, Tariffs


class QuestionsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Questions
        fields = ("id", "question")


class LegalDocsSerializer(serializers.ModelSerializer):

    class Meta:
        model = LegalDocs
        fields = ("policy", "terms")


class BenefitSerializer(serializers.ModelSerializer):

    class Meta:
        model = Benefit
        fields = ("title", "text", "link", "short_link")


class AdvicesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Advices
        fields = ("title", "text", "link", "short_link")


class TariffsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tariffs
        fields = ("id", "title", "cost", "price_per_month",
                  "month", "unlimited", "discount")
