from rest_framework import serializers
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth import get_user_model
from django.core import exceptions
import django.contrib.auth.password_validation as validators
UserModel = get_user_model()


gender_type = (
        ('1', _('М')),
        ('2', _('Ж')),
    )


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        password = data.get('password')
        errors = dict()
        try:
            validators.validate_password(password=password, user=UserModel)
        except exceptions.ValidationError as e:
            errors['error_message'] = e.messages
        if errors:
            raise serializers.ValidationError(errors)
        return super(PasswordSerializer, self).validate(data)


class SocialSerializer(serializers.Serializer):
    access_token = serializers.CharField(required=True)
    email = serializers.EmailField(allow_null=True, required=False)
    water = serializers.IntegerField(allow_null=True, required=False)
    gender = serializers.ChoiceField(choices=gender_type, allow_null=True, required=False)
    first_name = serializers.CharField(allow_null=True, required=False)
    newsletters = serializers.BooleanField()


class RegisterSerializer(PasswordSerializer, serializers.Serializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True)
    water = serializers.IntegerField(allow_null=True, required=False)
    gender = serializers.ChoiceField(choices=gender_type, allow_null=True, required=False)
    newsletters = serializers.BooleanField()


class LoginSerializer(PasswordSerializer, serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordResetSerializer(EmailSerializer):
    pass


class AccountSerializer(serializers.ModelSerializer):
    auth_status = serializers.CharField(default={})

    class Meta:
        model = UserModel
        fields = ("id", "first_name", "email", "water", "gender", "newsletters", "bottles", "auth_status")

    def to_representation(self, instance):
        representation = super(AccountSerializer, self).to_representation(instance)
        representation['auth_status'] = instance.auth_provider
        return representation


class AccountUPSerializer(serializers.ModelSerializer):
    gender = serializers.ChoiceField(choices=gender_type)

    class Meta:
        model = UserModel
        fields = ("first_name", "water", "gender", "bottles", "newsletters")


class EmailChangeSerializer(EmailSerializer, serializers.Serializer):
    code = serializers.CharField(required=True, max_length=4)


class AddNewEmailSerializer(EmailSerializer):
    pass

