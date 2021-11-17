from social_core.pipeline.user import USER_FIELDS
from datetime import timedelta, datetime
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
import random
import string
from django.contrib.auth import get_user_model
UserModel = get_user_model()


# Create or Authenticate user by social
def create_user(strategy, details, backend, user=None, *args, **kwargs):
    now = datetime.now()

    if user:
        if user.expiry_date is None:
            user.expiry_date = now + timedelta(7)
        user.authorized = '0'
        user.check_email = False
        user.save()
        return {'is_new': False}

    fields = dict((name, kwargs.get(name, details.get(name)))
                  for name in backend.setting('USER_FIELDS', USER_FIELDS))
    if not fields:
        return

    fields['check_email'] = False
    fields['authorized'] = '0'
    fields['water'] = kwargs['data']['water']
    fields['gender'] = kwargs['data']['gender']
    fields['newsletters'] = kwargs['data']['newsletters']
    email = kwargs['data']['email']

    if backend.name == 'vk-oauth2':
        try:
            vk_user = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            fields['email'] = email
            pass
        else:
            if vk_user.expiry_date is None:
                vk_user.expiry_date = now + timedelta(7)
            vk_user.authorized = '0'
            vk_user.check_email = False
            vk_user.save()
            return {
                'is_new': False,
                'user': vk_user
            }
    elif backend.name == 'apple-id':
        fields['first_name'] = kwargs['data']['first_name']

    return {
        'is_new': True,
        'user': strategy.create_user(**fields)
    }


# Check user authentication attempt
def check_user_auth(now, user):
    user.auth_attempt += 1
    user.save()
    if user.auth_attempt == 3:
        user.is_blocked = now + timedelta(minutes=1)
        user.save()
        time = user.is_blocked - now
        response_data = {"error_code": 2, "error_message": str(time.seconds)}
        return response_data
    elif user.auth_attempt == 4:
        user.is_blocked = now + timedelta(minutes=30)
        user.save()
        time = user.is_blocked - now
        response_data = {"error_code": 2, "error_message": str(time.seconds)}
        return response_data
    elif user.auth_attempt > 4:
        user.auth_attempt = 1
        user.save()
    response_data = {"error_code": 1, "error_message": _("Неверный логин или пароль")}
    return response_data


def pass_generator(length=settings.PASSWORD_LENGTH):
    digits = string.digits
    upper = string.ascii_uppercase
    lower = string.ascii_lowercase
    password = ''
    var = [digits, upper, lower]
    password += random.choice(digits)
    password += random.choice(upper)
    password += random.choice(lower)
    while len(password) < length:
        password += random.choice(var[random.randint(0, 2)])
    return password
