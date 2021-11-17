import json

from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils.translation import ugettext_lazy as _
from .serializers import SocialSerializer, RegisterSerializer, \
    LoginSerializer, PasswordResetSerializer, AccountSerializer, \
    PasswordSerializer, AccountUPSerializer, EmailChangeSerializer, \
    AddNewEmailSerializer, EmailSerializer
import random
from social_django.utils import psa
from datetime import datetime, timezone, timedelta
from rest_framework.views import APIView
from rest_framework.exceptions import Throttled
from apps.account.auth import check_user_auth, pass_generator
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
UserModel = get_user_model()
from apps.account.permissions import IsEmailAccount, IsChangeEmailAccess
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_text, force_bytes
from apps.core.tokens import account_activation_token
from apps.core.mailer import Mailer
from django.conf import settings
from django.shortcuts import render, HttpResponsePermanentRedirect
from urllib import parse


# Create or Authenticate user by social account
@csrf_exempt
@api_view(['POST'])
@permission_classes((AllowAny,))
@psa('social:complete')
def social_auth(request, backend):
    """
    @api {post} accounts/social_auth/:backend/ Авторизация через соц. сети
    @apiSuccessExample {json} Success-Response:
    {
        "token": {
            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6M",
            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNT"
    }
    }
    @apiErrorExample {json} Error-Response:
    {
        "error_code": 1,
        "error_message": [
            "400 Client Error: Bad Request for url: https://graph.facebook.com/v8.0/me?fields=id%2C+name%2C+email"
        ]
    }
    @apiVersion 1.0.0
    @apiName social_auth
    @apiGroup Аутентификация
    @apiDescription Возможные варианты backend - <code>facebook, google-oauth2, yandex-oauth2, vk-oauth2, apple-id</code>

    @apiParam {String} access_token Токен полученный от соц. сети
    @apiParam {String} [email] Валидный e-mail, обязательное поле если backend <code>vk-oauth2</code>
    @apiParam {String} [first_name] Имя пользователя, обязательное поле если backend <code>apple-id</code>
    @apiParam {Number} [water] Норма воды
    @apiParam {String=1,2} [gender] Пол пользователя, <code>1</code> - Муж. <code>2</code> - Жен.
    @apiParam {Boolean} [newsletters=True] Подписка на новости

    @apiSuccess (Response) {Object} token Информация о токене пользователя
    @apiSuccess (Response) {String} token.refresh Refresh токен для продления основного токена
    @apiSuccess (Response) {String} token.access Токен пользователя

    @apiError (Error Code) 1 Невалидный токен или пользователь не дал необходимые разрешения
    """
    serializer = SocialSerializer(data=request.data)
    if serializer.is_valid():
        access_token = request.data.get('access_token')
        email = request.data.get('email')
        water = request.data.get('water')
        gender = request.data.get('gender')
        newsletters = request.data.get('newsletters', True)
        first_name = request.data.get('first_name')
        try:
            user = request.backend.do_auth(
                access_token,
                data={'water': water if water else 1500,
                      'gender': gender if gender else "0",
                      'email': email, 'newsletters': newsletters,
                      'first_name': first_name
                      }
            )
        except Exception as e:
            response_data = {"error_code": 1, "error_message": e.args}
            return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)
        return Response({'token': user.token}, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Custom schema for apple redirect
class AppleSchemeRedirect(HttpResponsePermanentRedirect):
    allowed_schemes = ['intent']


# Apple redirect
@csrf_exempt
@api_view(['POST'])
@permission_classes((AllowAny,))
def apple_redirect(request):
    data = parse.urlencode(request.data)
    return AppleSchemeRedirect(
        f'intent://callback?{data}#Intent;package=it.jsay.love;scheme=signinwithapple;end'
    )


# Create or Authenticate user by email (login form)
@csrf_exempt
@api_view(['POST'])
@permission_classes((AllowAny,))
def auth(request):
    """
    @api {post} accounts/auth/ Авторизация через почту
    @apiSuccessExample {json} Success-Response:
    {
        "token": {
            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6M",
            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNT"
    }
    }
    @apiErrorExample {json} 1.Error-Response:
    {
        "error_code": 1,
        "error_message": "Неверный емейл или пароль"
    }
    @apiErrorExample {json} 2.Error-Response:
    {
        "error_code": 2,
        "error_message": "30"
    }
    @apiVersion 1.0.0
    @apiName auth
    @apiGroup Аутентификация
    @apiDescription Авторизация через почту (форма логина)
    @apiParam {String} email Валидный e-mail - адрес почты
    @apiParam {String} password Пароль пользователя, минимум <code>6</code> символов (минимум <code>1</code>
     цифра и <code>1</code> буква)

    @apiSuccess (Response) {Object} token Информация о токене пользователя
    @apiSuccess (Response) {String} token.refresh Refresh токен для продления основного токена
    @apiSuccess (Response) {String} token.access Токен пользователя

    @apiError (Error Code) 1 Неверный емейл или пароль
    @apiError (Error Code) 2 Время блокировки в секундах
    """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        email = request.data['email'].lower()
        password = request.data['password']
        try:
            user = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            new_user = UserModel.objects.create(
                email=email
            )
            new_user.authorized = '1'
            new_user.set_password(password)
            new_user.save()
            return Response({'token': new_user.token}, status=status.HTTP_200_OK)
        now = datetime.now(timezone.utc)
        # if user.is_blocked is not None:
        #     if user.is_blocked > now:
        #         time = user.is_blocked - now
        #         response_data = {"error_code": 2, "error_message": str(time.seconds)}
        #         return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        _user = authenticate(username=email, password=password)
        print(_user)
        if _user is not None:
            user.auth_attempt = 0
            user.authorized = '1'
            user.save()
            return Response({'token': user.token}, status=status.HTTP_200_OK)
        else:
            response_data = check_user_auth(now, user)
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Check User exists
@csrf_exempt
@api_view(['POST'])
@permission_classes((AllowAny,))
def user_exists(request):
    """
    @api {post} accounts/exists/ Проверка емайла в БД
    @apiSuccessExample {json} Success-Response:
    {
        "status": true
    }
    @apiVersion 1.0.0
    @apiName exists
    @apiGroup Аутентификация
    @apiParam {String} email Валидный e-mail - адрес почты
    @apiSuccess (Response) {Boolean} status <code>True</code> - существует, <code>False</code> - не существует
    """
    serializer = EmailSerializer(data=request.data)
    if serializer.is_valid():
        if UserModel.objects.filter(email=request.data['email'].lower()).exists():
            return Response({"status": True}, status=status.HTTP_200_OK)
        return Response({"status": False}, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Create or Authenticate user by email (register form)
@csrf_exempt
@api_view(['POST'])
@permission_classes((AllowAny,))
def registration(request):
    """
    @api {post} accounts/registration/ Регистрация через почту
    @apiSuccessExample {json} Success-Response:
    {
        "token": {
            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6M",
            "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNT"
        }
    }
    @apiVersion 1.0.0
    @apiName registration
    @apiGroup Аутентификация
    @apiDescription Регистрация через почту (форма регистрации)
    @apiParam {String} email Валидный e-mail - адрес почты
    @apiParam {String} password Пароль пользователя, минимум <code>6</code> символов (минимум <code>1</code>
     цифра и <code>1</code> буква)
    @apiParam {String} first_name Имя пользователя
    @apiParam {Number} [water=1500] Норма воды
    @apiParam {String=1,2} [gender] Пол пользователя, <code>1</code> - Муж. <code>2</code> - Жен.
    @apiParam {Boolean} [newsletters=True] Подписка на новости
    @apiSuccess (Response) {Object} token Информация о токене пользователя
    @apiSuccess (Response) {String} token.refresh Refresh токен для продления основного токена
    @apiSuccess (Response) {String} token.access Токен пользователя
    """
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        email = request.data['email'].lower()
        password = request.data['password']
        water = request.data.get('water')
        gender = request.data.get('gender')
        try:
            UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            new_user = UserModel.objects.create(
                email=email,
                first_name=request.data['first_name'],
                water=water if water else 1500,
                gender=gender if gender else "0",
                newsletters=request.data.get('newsletters', True),
                authorized='1'
            )
            new_user.set_password(password)
            new_user.save()
            return Response({'token': new_user.token}, status=status.HTTP_200_OK)
        return Response(
            {"error_code": 1, "error_message": "Пользователь уже существует"},
            status=status.HTTP_400_BAD_REQUEST
        )
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Activate user email
def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = UserModel.objects.get(id=uid)
    except(TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.check_email = False
        now = datetime.now()
        user.expiry_date = now + timedelta(7)
        user.save()
        return render(request, 'notifications/activated_status.html', {"active": True})
        # return HttpResponse('Ваш профиль был успешно активирован.')
    else:
        # return HttpResponse('Ой! Что то пошло не так.')
        return render(request, 'notifications/activated_status.html', {"active": False})


# Resend user email activation link
@csrf_exempt
@api_view(['POST'])
@permission_classes((IsAuthenticated,))
def resend_activate_token(request):
    """
    @api {post} accounts/resend_activate/ Письмо активации
    @apiSuccessExample {json} Success-Response:
    {
        "message": "Мы отправили вам письмо на user@example.com"
    }
    @apiErrorExample {json} Error-Response:
    {
        "error_code": 1,
        "error_message": "30"
    }
    @apiVersion 1.0.0
    @apiHeader {String} Authorization User Bearer Token.
    @apiPermission User
    @apiName resend_activate
    @apiGroup Аутентификация
    @apiDescription Переотправка письма активации

    @apiSuccess (Response) {String} message Письмо отправлено

    @apiError (Error Code) 1 Время блокировки в секундах
    """
    user = request.user
    if not user.check_email:
        response_data = {"error_message": _("Профиль уже активирован.")}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    if user.email_send_time is not None:
        now = datetime.now(timezone.utc)
        if user.email_send_time > now:
            time = user.email_send_time - now
            response_data = {"error_code": 1, "error_message": str(time.seconds)}
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        else:
            user.send_email_verification(
                settings.SITE_URL,
                urlsafe_base64_encode(force_bytes(user.id)),
                account_activation_token.make_token(user)
            )
            user.email_send_time = now + timedelta(minutes=1)
            user.save()
            response_data = {"message": _(f"Мы отправили вам письмо на {user.email}")}
            return Response(response_data, status=status.HTTP_200_OK)
    return Response(status=status.HTTP_409_CONFLICT)


# Password reset
@csrf_exempt
@api_view(['POST'])
@permission_classes((AllowAny,))
def reset_password(request):
    """
    @api {post} accounts/reset_password/ Сброс пароля
    @apiSuccessExample {json} Success-Response:
    {
        "message": "Новый пароль отправлен на user@example.com"
    }
    @apiVersion 1.0.0
    @apiName reset_password
    @apiGroup Аутентификация
    @apiParam {String} email Эл. почта пользователя
    @apiDescription Если пользователь есть в системе отправляем новый пароль, если нет отправляем приглашение
    @apiSuccess (Response) {String} message Новый пароль отправлен на почту
    """
    serializer = PasswordResetSerializer(data=request.data)
    if serializer.is_valid():
        email = request.data['email']
        try:
            user = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            mail = Mailer()
            mail.send_messages(subject=_('Приглашение'),
                               template='notifications/invite.html',
                               context={'email': email},
                               to_emails=[email])
            return Response({"message": _(f"Приглашение отправлено")},
                            status=status.HTTP_200_OK)
        password = pass_generator()
        user.set_password(password)
        user.save(update_fields=['password'])
        user.password_reset_email(password)
        return Response({"message": _(f"Новый пароль отправлен на {email}")},
                        status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Get and Update account info
class AccountViewSet(viewsets.ModelViewSet):
    """
    @api {get} accounts/account/ Просмотр данных
    @apiSuccessExample {json} Success-Response:
    {
        "id": 1,
        "first_name": "Егор",
        "email": "egor@example.com",
        "water": 1500,
        "gender": "1",
        "newsletters": true,
        "bottles": [100, 200, 300, 500],
        "auth_status": {
            "social": true,
            "provider": "facebook"
        }
    }
    @apiVersion 1.0.0
    @apiHeader {String} Authorization User Bearer Token.
    @apiPermission User
    @apiName account_info
    @apiGroup Пользователь
    @apiSuccess (Response) {Object} auth_status Статус авторизации
    @apiSuccess (Response) {Boolean} auth_status.social Статус соц. сети, <code>True</code> - через соц. сеть,
    <code>False</code> - через email
    @apiSuccess (Response) {String} auth_status.provider Название соц. сети
    @apiSuccess (Response) {Number} id ID пользователя
    @apiSuccess (Response) {String} first_name Имя пользователя
    @apiSuccess (Response) {String} email Эл. почта пользователя
    @apiSuccess (Response) {Number} water Норма воды
    @apiSuccess (Response) {String} gender Пол пользователя, <code>1</code> - Муж. <code>2</code> - Жен.
    @apiSuccess (Response) {Boolean} newsletters Подписка на новости
    @apiSuccess (Response) {Object[]} bottles Варианты бутылок, JSON Array пример: [<code>100, 300, 500, 1000</code>]
    """
    """
    @api {post} accounts/account/change_password/ Изменение пароля
    @apiSuccessExample {json} Success-Response:
    {
        "message": "Пароль успешно изменен"
    }
    @apiVersion 1.0.0
    @apiHeader {String} Authorization User Bearer Token.
    @apiPermission User
    @apiName change_password
    @apiGroup Пользователь
    @apiDescription Пользователь должен быть авторизован с помощью ввода емейла и пароля, 
    в противном случае ответ будет <code>403</code>
    @apiParam {String} password Новый пароль, минимум <code>6</code> символов (минимум <code>1</code>
     цифра и <code>1</code> буква)
    @apiSuccess (Response) {String} message Пароль успешно изменен
    """
    """
    @api {patch} accounts/account/update/ Редактирование данных
    @apiSuccessExample {json} Success-Response:
    {
        "first_name": "Егор",
        "water": 1500,
        "gender": "1",
        "bottles": [100, 300, 500, 1000],
        "newsletters": true
    }
    @apiVersion 1.0.0
    @apiHeader {String} Authorization User Bearer Token.
    @apiPermission User
    @apiName account_update
    @apiGroup Пользователь
    @apiParam {String} [first_name] Имя пользователя
    @apiParam {Number} [water] Норма воды
    @apiParam {Object[]} [bottles] Варианты бутылок, JSON Array пример: [<code>100, 300, 500, 1000</code>]
    @apiParam {String=1,2} [gender] Пол пользователя, <code>1</code> - Муж. <code>2</code> - Жен.
    @apiParam {Boolean} [newsletters=True] Подписка на новости
    """
    queryset = UserModel.objects.all()
    serializer_class = AccountSerializer

    def get_permissions(self):
        if self.action == 'change_password':
            permission_classes = [IsAuthenticated, IsEmailAccount]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()
        data = serializer(request.user).data
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.request.user
        serializer = PasswordSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.validated_data['password'])
            user.save()
            return Response({'message': _('Пароль успешно изменен')},
                            status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['patch'])
    def update_info(self, request, pk=None):
        serializer = AccountUPSerializer(self.request.user,
                                         data=request.data,
                                         partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


# User email change 1'st step
# class ChangeEmailView(APIView):
#     """
#     @api {post} accounts/email/change/ Смена почты
#     @apiSuccessExample {json} Success-Response:
#     {
#         "message": "Код отправлен на user@example.com",
#         "email": "user@example.com"
#     }
#     @apiErrorExample {json} 1.Error-Response:
#     {
#         "error_code": 1,
#         "error_message": "Смена емейла заблокирована на 24 часа"
#     }
#     @apiErrorExample {json} 2.Error-Response:
#     {
#         "error_code": 2,
#         "error_message": "30"
#     }
#     @apiVersion 1.0.0
#     @apiHeader {String} Authorization User Bearer Token.
#     @apiPermission User
#     @apiName email_change
#     @apiGroup Пользователь
#     @apiSuccess (Response) {String} message Код успешно отправлен
#     @apiError (Error Code) 1 Смена емейла заблокирована на 24 часа
#     @apiError (Error Code) 2 Время блокировки в секундах
#     """
#     permission_classes = (IsAuthenticated, IsChangeEmailAccess)
#     throttle_scope = 'old_email'
#
#     def throttled(self, request, wait):
#         raise Throttled(detail={
#             "error_code": 2,
#             "error_message": str(round(wait))
#         })
#
#     def post(self, request, *args, **kwargs):
#         random_code = random.sample(range(10), 4)
#         code = ''.join(map(str, random_code))
#         obj, created = ChangeEmail.objects.update_or_create(
#             owner=self.request.user,
#             defaults={
#                 "code": code,
#                 "ip_address": request.META.get('REMOTE_ADDR')
#             }
#         )
#         obj.reset_attempts()
#         obj.owner.send_change_email_code(self.request.user.email, code)
#         email = obj.owner.email
#         return Response(
#             {
#                 "message": _(f"Код отправлен на {email}"),
#                 "email": email
#             },
#             status=status.HTTP_200_OK
#         )


# User email change 1'st step confirmation
# @csrf_exempt
# @api_view(['POST'])
# @permission_classes((IsAuthenticated, IsChangeEmailAccess))
# def change_email_confirm(request):
#     """
#     @api {post} accounts/email/confirm/ Подтверждение смены почты
#     @apiSuccessExample {json} Success-Response:
#     {
#         "message": "Валидация прошла успешно"
#     }
#     @apiErrorExample {json} 1.Error-Response:
#     {
#         "error_code": 1,
#         "error_message": "Смена емейла заблокирована на 24 часа"
#     }
#     @apiErrorExample {json} 2.Error-Response:
#     {
#         "error_code": 2,
#         "error_message": "Неправильный код подтверждения"
#     }
#     @apiVersion 1.0.0
#     @apiHeader {String} Authorization User Bearer Token.
#     @apiPermission User
#     @apiName email_change_confirm
#     @apiGroup Пользователь
#     @apiDescription Если Пользователь ввел 3 раза неверно проверочный код,
#     смена емейла блокируется на <code>24</code> часа.
#     @apiParam {String} email Актуальная эл. почта пользователя
#     @apiParam {Number{4}} code Код подтверждения полученный на емейл
#     @apiSuccess (Response) {String} message Валидация прошла успешно
#     @apiError (Error Code) 1 Смена емейла заблокирована на 24 часа
#     @apiError (Error Code) 2 Неправильный код подтверждения
#     """
#     serializer = EmailChangeSerializer(data=request.data)
#     if serializer.is_valid():
#         try:
#             obj = ChangeEmail.objects.get(owner__email=request.data['email'])
#         except ChangeEmail.DoesNotExist:
#             response_data = {"error_code": 10, "error_message": _('Нарушен порядок действий')}
#             return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
#         if obj.code == str(request.data['code']):
#             obj.reset_attempts(confirm=True)
#             response_data = {"message": _('Валидация прошла успешно')}
#             return Response(response_data, status=status.HTTP_200_OK)
#         else:
#             obj.inc_attempts()
#             response_data = {"error_code": 2, "error_message": _('Неправильный код подтверждения')}
#             return Response(response_data, status=status.HTTP_417_EXPECTATION_FAILED)
#     else:
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# User email change 2'st step
# class AddNewEmailView(APIView):
#     """
#     @api {post} accounts/new_email/add/ Добавление новой почты
#     @apiSuccessExample {json} Success-Response:
#     {
#         "message": "Код отправлен на user@example.com",
#         "email": "user@example.com"
#     }
#     @apiErrorExample {json} 1.Error-Response:
#     {
#         "error_code": 1,
#         "error_message": "Смена емейла заблокирована на 24 часа"
#     }
#     @apiErrorExample {json} 2.Error-Response:
#     {
#         "error_code": 2,
#         "error_message": "30"
#     }
#     @apiErrorExample {json} 3.Error-Response:
#     {
#         "error_code": 3,
#         "error_message": "Изменение невозможно, обратитесь в техподдержку"
#     }
#     @apiVersion 1.0.0
#     @apiHeader {String} Authorization User Bearer Token.
#     @apiPermission User
#     @apiName new_email
#     @apiGroup Пользователь
#     @apiParam {String} email Новая эл. почта пользователя
#     @apiSuccess (Response) {String} message Код успешно отправлен
#     @apiError (Error Code) 1 Смена емейла заблокирована на 24 часа
#     @apiError (Error Code) 2 Время блокировки в секундах
#     @apiError (Error Code) 3 Эл. почта уже занята
#     """
#     permission_classes = (IsAuthenticated, IsChangeEmailAccess)
#     throttle_scope = 'new_email'
#
#     def throttled(self, request, wait):
#         raise Throttled(detail={
#             "error_code": 2,
#             "error_message": str(round(wait))
#         })
#
#     def post(self, request):
#         serializer = AddNewEmailSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         email = serializer.data['email']
#         if UserModel.objects.filter(email=email).exists():
#             response_data = {"error_code": 3, "error_message": _("Изменение невозможно, обратитесь в техподдержку")}
#             return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
#         try:
#             obj = ChangeEmail.objects.get(owner=self.request.user, is_confirm=True)
#         except ChangeEmail.DoesNotExist:
#             response_data = {"error_code": 10, "error_message": _('Нарушен порядок действий')}
#             return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
#
#         random_code = random.sample(range(10), 4)
#         code = ''.join(map(str, random_code))
#         obj.email = email
#         obj.code = code
#         obj.ip_address = request.META.get('REMOTE_ADDR')
#         obj.save()
#         obj.owner.send_change_email_code(email, code)
#         return Response(
#             {
#                 "message": _(f"Код отправлен на {email}"),
#                 "email": email
#             },
#             status=status.HTTP_200_OK
#         )


# User email change 2'st step confirmation
# @csrf_exempt
# @api_view(['POST'])
# @permission_classes((IsAuthenticated, IsChangeEmailAccess))
# def new_email_confirm(request):
#     """
#     @api {post} accounts/new_email/confirm/ Подтверждение новой почты
#     @apiSuccessExample {json} Success-Response:
#     {
#         "message": "Вы изменили адрес электронной почты"
#     }
#     @apiErrorExample {json} 1.Error-Response:
#     {
#         "error_code": 1,
#         "error_message": "Смена емейла заблокирована на 24 часа"
#     }
#     @apiErrorExample {json} 2.Error-Response:
#     {
#         "error_code": 2,
#         "error_message": "Неправильный код подтверждения"
#     }
#     @apiVersion 1.0.0
#     @apiHeader {String} Authorization User Bearer Token.
#     @apiPermission User
#     @apiName new_email_confirm
#     @apiGroup Пользователь
#     @apiDescription Если Пользователь ввел 3 раза неверно проверочный код,
#     смена емейла блокируется на <code>24</code> часа.
#     @apiParam {String} email Новая эл. почта пользователя
#     @apiParam {Number{4}} code Код подтверждения полученный на емейл
#     @apiSuccess (Response) {String} message Адрес электронной почты изменен
#     @apiError (Error Code) 1 Смена емейла заблокирована на 24 часа
#     @apiError (Error Code) 2 Неправильный код подтверждения
#     """
#     serializer = EmailChangeSerializer(data=request.data)
#     if serializer.is_valid():
#         try:
#             obj = ChangeEmail.objects.get(owner=request.user, is_confirm=True)
#         except ChangeEmail.DoesNotExist:
#             response_data = {"error_code": 10, "error_message": _('Нарушен порядок действий')}
#             return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
#         if obj.code == str(request.data['code']) and obj.email == request.data['email']:
#             obj.reset_attempts(confirm=True, change=True)
#             response_data = {"message": _('Вы изменили адрес электронной почты')}
#             return Response(response_data, status=status.HTTP_200_OK)
#         else:
#             obj.inc_attempts()
#             response_data = {"error_code": 2, "error_message": _('Неправильный код')}
#             return Response(response_data, status=status.HTTP_417_EXPECTATION_FAILED)
#     else:
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Drink water
# @csrf_exempt
# @api_view(['POST'])
# @permission_classes((IsAuthenticated,))
# def drink_water(request):
#     """
#     @api {post} accounts/drink_water/ Выпить воды
#     @apiSuccessExample {json} 1.Success-Response:
#     {
#         "daily_norm": {
#             "notify": true,
#             "milliliter": 500,
#             "percent": 100.0,
#             "date": "2021-09-06"
#         },
#         "first_drink": {
#             "notify": true,
#             "percent": 100.0,
#             "date": "2021-09-06",
#             "award": {
#                 "text": "Первый пошёл: вы записали свой первый стакан воды. Продолжайте!",
#                 "photo_code": "s1"
#             }
#         },
#         "drink_award": {
#             "notify": true,
#             "percent": 100.0,
#             "date": "2021-09-06",
#             "award": {
#                 "title": "Ваши первые 2 л!",
#                 "text": "Продолжайте в том же духе и почувствуете себя лучше уже очень скоро.",
#                 "photo_code": "wd1"
#             }
#         },
#         "daily_rate": {
#             "notify": true,
#             "percent": 100.0,
#             "date": "2021-09-06",
#             "award": {
#                 "title": "Вы 1 день пьете свою норму воды",
#                 "text": "Сегодня вы выпили свою нормы воды. Увидимся завтра!",
#                 "photo_code": "dr1"
#             }
#         }
#     }
#     @apiSuccessExample {json} 2.Success-Response:
#     {
#         "daily_norm": {
#             "notify": false
#         },
#         "first_drink": {
#             "notify": false
#         },
#         "drink_award": {
#             "notify": false
#         },
#         "daily_rate": {
#             "notify": false
#         }
#     }
#     @apiVersion 1.0.0
#     @apiHeader {String} Authorization User Bearer Token.
#     @apiPermission User
#     @apiName drink_water
#     @apiGroup Вода и достижения
#     @apiParam {String=YYYY-MM-DD} date Текущая дата
#     @apiParam {Number} milliliter Количество воды в миллилитрах
#     @apiDescription Если Пользователь отменяет пополнение, можно отправить отрицательное значение <code>-150</code>
#     @apiSuccess (Response) {Object} daily_norm Дневная цель
#     @apiSuccess (Response) {Boolean} daily_norm.notify Поздравить <code>True</code> - да, <code>False</code> - нет
#     @apiSuccess (Response) {Number} daily_norm.milliliter Количество выпитой воды в миллилитрах
#     @apiSuccess (Response) {Number} daily_norm.percent Процент пользователей, которые достигли дневной цели
#     @apiSuccess (Response) {String} daily_norm.date День выполнения
#     @apiSuccess (Response) {Object} first_drink Пользователь выпивает воду впервые в приложении
#     @apiSuccess (Response) {Boolean} first_drink.notify Поздравить <code>True</code> - да, <code>False</code> - нет
#     @apiSuccess (Response) {Number} first_drink.percent Процент пользователей, которые достигли дневной цели
#     @apiSuccess (Response) {String} first_drink.date День выполнения
#     @apiSuccess (Response) {Object} first_drink.award Достижение
#     @apiSuccess (Response) {String} first_drink.award.text Текст поздравления
#     @apiSuccess (Response) {String} first_drink.award.photo_code Код миниатюры
#     @apiSuccess (Response) {Object} drink_award Достижение выпитой воды
#     @apiSuccess (Response) {Boolean} drink_award.notify Поздравить <code>True</code> - да, <code>False</code> - нет
#     @apiSuccess (Response) {Number} drink_award.percent Процент пользователей получивших достижение
#     @apiSuccess (Response) {String} drink_award.date День достижения
#     @apiSuccess (Response) {Object} drink_award.award Достижение
#     @apiSuccess (Response) {String} drink_award.award.title Название достижения
#     @apiSuccess (Response) {String} drink_award.award.text Текст поздравления
#     @apiSuccess (Response) {String} drink_award.award.photo_code Код миниатюры
#     @apiSuccess (Response) {Object} daily_rate Достижение дневной нормы
#     @apiSuccess (Response) {Boolean} daily_rate.notify Поздравить <code>True</code> - да, <code>False</code> - нет
#     @apiSuccess (Response) {Number} daily_rate.percent Процент пользователей получивших достижение
#     @apiSuccess (Response) {String} daily_rate.date День достижения
#     @apiSuccess (Response) {Object} daily_rate.award Достижение
#     @apiSuccess (Response) {String} daily_rate.award.title Название достижения
#     @apiSuccess (Response) {String} daily_rate.award.text Текст поздравления
#     @apiSuccess (Response) {String} daily_rate.award.photo_code Код миниатюры
#     """
#     serializer = DrinkWaterSerializer(data=request.data)
#     serializer.is_valid(raise_exception=True)
#     obj = DailyWater.load(
#         request.user,
#         serializer.data['date'])\
#         .drink_water(serializer.data['milliliter'])
#     response = DrinkWaterSerializer.get_possible_awards(obj)
#     return Response(response, status=status.HTTP_200_OK)


# Int layer method
# @csrf_exempt
# @api_view(['POST'])
# @permission_classes((IsAuthenticated,))
# def status_active(request):
#     """
#     @api {post} accounts/status_active/ Статус и активность пользователя
#     @apiSuccessExample {json} 1.Success-Response:
#     {
#         "check_email": false,
#         "check_full_info": false,
#         "daily_active": {
#             "notify": true,
#             "counter": 0,
#             "percent": 100.0,
#             "date": "2021-09-08",
#             "award": {
#                 "title": "Вы пользуетесь приложением 1 дней",
#                 "text": "Поздравляем и увидимся завтра!",
#                 "photo_code": "da1"
#             }
#         },
#         "bottles": [
#             100,
#             200,
#             300,
#             500
#         ],
#         "daily_water": {
#             "water_norm": 1500,
#             "drunk": 1500,
#             "percent": 100
#         }
#     }
#     @apiSuccessExample {json} 2.Success-Response:
#     {
#         "check_email": false,
#         "check_full_info": false,
#         "daily_active": {
#             "notify": false
#         },
#         "bottles": [
#             100,
#             200,
#             300,
#             500
#         ],
#         "daily_water": {
#             "water_norm": 1500,
#             "drunk": 1500,
#             "percent": 100
#         }
#     }
#     @apiVersion 1.0.0
#     @apiHeader {String} Authorization User Bearer Token.
#     @apiPermission User
#     @apiName status_active
#     @apiGroup Активность и статус
#     @apiParam {String=YYYY-MM-DD} date Текущая дата
#     @apiSuccess (Response) {Object} daily_water Информация о выпитой воде
#     @apiSuccess (Response) {Number} daily_water.water_norm Норма воды за день
#     @apiSuccess (Response) {Number} daily_water.drunk Выпитая вода за день
#     @apiSuccess (Response) {Number} daily_water.percent Процент выпитой воды за день
#     @apiSuccess (Response) {Object} daily_active Достижение активности
#     @apiSuccess (Response) {Boolean} daily_active.notify Поздравить <code>True</code> - да, <code>False</code> - нет
#     @apiSuccess (Response) {Number} daily_active.counter Счетчик повторений
#     @apiSuccess (Response) {Number} daily_active.percent Процент пользователей получивших достижение
#     @apiSuccess (Response) {String} daily_active.date День достижения
#     @apiSuccess (Response) {Object} daily_active.award Достижение
#     @apiSuccess (Response) {String} daily_active.award.title Название достижения
#     @apiSuccess (Response) {String} daily_active.award.text Текст поздравления
#     @apiSuccess (Response) {String} daily_active.award.photo_code Код миниатюры
#     @apiSuccess (Response) {Boolean} check_email Статус почты <code>True</code> - необходима проверка,
#     <code>False</code> - проверка не требуется
#     @apiSuccess (Response) {Boolean} check_full_info Статус данных пользователя
#     <code>True</code> - необходима проверка, <code>False</code> - проверка не требуется
#     @apiSuccess (Response) {Object[]} bottles Бутылки пользователя
#     """
#     serializer = DailyActiveSerializer(data=request.data)
#     serializer.is_valid(raise_exception=True)
#     date = serializer.data['date']
#     user = request.user
#     obj = UserAwardDailyActive.load(
#         user,
#         user.daily_active(date),
#         date)
#     daily_active = DailyActiveSerializer.get_active_awards(obj)
#     daily_water = DailyWater.load(user, date)
#     return Response({
#         "check_email": user.check_email,
#         "check_full_info": True if user.gender == "0" and len(user.first_name) > 0 else False,
#         "daily_active": daily_active,
#         "bottles": user.bottles,
#         "daily_water": {
#             "water_norm": daily_water.water,
#             "drunk": daily_water.milliliter,
#             "percent": daily_water.percent
#         }
#     }, status=status.HTTP_200_OK)


# Get user awards
# @csrf_exempt
# @api_view(['GET'])
# @permission_classes((IsAuthenticated,))
# def user_awards(request):
#     """
#     @api {get} accounts/account/achievements/ Достижения пользователя
#     @apiSuccessExample {json} Success-Response:
#     {
#         "d_rate": 7,
#         "d_active": 125,
#         "drink_awards": [
#             {
#                 "counter": 0,
#                 "percent": 62,
#                 "date": "2021-09-03",
#                 "users_percent": 100,
#                 "created": 1630698909,
#                 "award": {
#                     "title": "Выпьём для здоровья!",
#                     "text": "Продолжайте в том же духе и почувствуете себя лучше уже очень скоро."
#                     "photo_code": "wd2",
#                     "users_percent": 50,
#                     "description": "Вы выпили 2л воды!",
#                     "condition": "Пользователь выпивает 40 литров воды",
#                     "name": "Заголовок для рассказать друзьям",
#                     "milliliter": 2000,
#                     "repeat": false
#                 }
#             },
#             {
#                 "counter": 0,
#                 "percent": 100,
#                 "date": "2021-09-03",
#                 "users_percent": 70,
#                 "created": 1630698910,
#                 "award": {
#                     "title": "Вода — друг человека",
#                     "text": "Продолжайте в том же духе и почувствуете себя лучше уже очень скоро."
#                     "photo_code": "wd2",
#                     "users_percent": 50,
#                     "description": "Вы выпили 100л воды!",
#                     "condition": "Пользователь выпивает 40 литров воды",
#                     "name": "Заголовок для рассказать друзьям",
#                     "milliliter": 40000,
#                     "repeat": false
#                 }
#             },
#             {
#                 "award": {
#                     "title": "Оазис здоровья",
#                     "text": "Продолжайте в том же духе и почувствуете себя лучше уже очень скоро."
#                     "photo_code": "wd2",
#                     "users_percent": 50,
#                     "description": "Вы выпили 40л воды!",
#                     "condition": "Пользователь выпивает 40 литров воды",
#                     "name": "Заголовок для рассказать друзьям",
#                     "milliliter": 100000,
#                     "repeat": false
#                 }
#             }
#         ],
#         "active_awards": [
#             {
#                 "counter": 0,
#                 "date": "2021-09-03",
#                 "users_percent": 80,
#                 "created": 1730698909,
#                 "award": {
#                     "title": "7 — магическое число",
#                     "text": "Вы пользуетесь приложением 7 дней. Отличный результат!",
#                     "photo_code": "da2",
#                     "users_percent": 50,
#                     "description": "Я впервые зашёл в JSay Water",
#                     "condition": "Пользователь использует приложение количество дней : 7",
#                     "name": "Заголовок для рассказать друзьям",
#                     "day": 120,
#                     "repeat": false
#                 }
#             },
#             {
#                 "counter": 0,
#                 "date": "2021-09-03",
#                 "users_percent": 100,
#                 "created": 1830698909,
#                 "award": {
#                     "title": "Всё бывает в первый раз",
#                     "text": "Поздравляем и увидимся завтра!",
#                     "photo_code": "da1",
#                     "users_percent": 70,
#                     "description": "Я впервые зашёл в JSay Water",
#                     "condition": "Я 7-й день с JSay Water",
#                     "name": "Заголовок для рассказать друзьям",
#                     "day": 150,
#                     "repeat": false
#                 }
#             }
#         ],
#         "rate_awards": [
#             {
#                 "counter": 0,
#                 "date": "2021-09-03",
#                 "users_percent": 80,
#                 "created": 1530698909,
#                 "award": {
#                     "title": "Новобранец Армии Здоровья",
#                     "text": "Сегодня вы выпили свою нормы воды. Увидимся завтра!",
#                     "photo_code": "dr1",
#                     "users_percent": 50,
#                     "description": "Ваша норма воды на 1 день выпита",
#                     "condition": "Пользователь пьет свою норму воды 1 день",
#                     "name": "Заголовок для рассказать друзьям",
#                     "day": 8,
#                     "repeat": false
#                 }
#             },
#             {
#                 "counter": 1,
#                 "date": "2021-09-03",
#                 "users_percent": 100,
#                 "created": 1650698909,
#                 "award": {
#                     "title": "Солдат Армии Здоровья",
#                     "text": "Второй день с водой — вы отлично идете!",
#                     "photo_code": "dr2",
#                     "users_percent": 70,
#                     "description": "Ваша норма воды на 2 день выпита",
#                     "condition": "Пользователь пьет свою норму воды 2 дня",
#                     "name": "Заголовок для рассказать друзьям",
#                     "day": 7,
#                     "repeat": true
#                 }
#             }
#         ],
#         "single_awards": [
#             {
#                 "date": "2021-09-03",
#                 "users_percent": 90,
#                 "created": 1770698909,
#                 "award": {
#                     "title": Вода — просто улёт,
#                     "text": "Первый пошёл: вы записали свой первый стакан воды. Продолжайте!",
#                     "photo_code": "s1",
#                     "users_percent": 50,
#                     "description": "Я впервые выпил воды в JSay!",
#                     "condition": "Пользователь выпивает воду впервые в приложении",
#                     "name": "Заголовок для рассказать друзьям",
#                     "repeat": false
#                 }
#             }
#         ]
#     }
#     @apiVersion 1.0.0
#     @apiHeader {String} Authorization User Bearer Token.
#     @apiPermission User
#     @apiName user_achievements
#     @apiGroup Вода и достижения
#
#     @apiSuccess (Response) {Object} drink_awards Достижения выпитой воды
#     @apiSuccess (Response) {Number} drink_awards.counter Счетчик повторений
#     @apiSuccess (Response) {Number} drink_awards.percent Процент выполнения
#     @apiSuccess (Response) {String} drink_awards.date День достижения
#     @apiSuccess (Response) {Number} drink_awards.users_percent Процент пользователей
#     @apiSuccess (Response) {String} drink_awards.created День получения в timestamp, для выборки последнего
#     @apiSuccess (Response) {Object} drink_awards.award Достижение
#     @apiSuccess (Response) {String} drink_awards.award.title Название достижения
#     @apiSuccess (Response) {String} drink_awards.award.text Текст достижения
#     @apiSuccess (Response) {String} drink_awards.award.photo_code Код миниатюры
#     @apiSuccess (Response) {String} drink_awards.award.users_percent Актуальный процент пользователей
#     @apiSuccess (Response) {String} drink_awards.award.description Описание
#     @apiSuccess (Response) {String} drink_awards.award.condition Условия получения
#     @apiSuccess (Response) {String} drink_awards.award.name Заголовок для рассказать друзьям
#     @apiSuccess (Response) {Number} drink_awards.award.milliliter Объем достижения
#     @apiSuccess (Response) {Boolean} drink_awards.award.repeat Повторяемый <code>True</code> - да,
#     <code>False</code> - нет
#
#     @apiSuccess (Response) {Object} active_awards Достижение активности
#     @apiSuccess (Response) {Number} active_awards.counter Счетчик повторений
#     @apiSuccess (Response) {String} active_awards.date День достижения
#     @apiSuccess (Response) {Number} active_awards.users_percent Процент пользователей
#     @apiSuccess (Response) {String} active_awards.created День получения в timestamp, для выборки последнего
#     @apiSuccess (Response) {Object} active_awards.award Достижение
#     @apiSuccess (Response) {String} active_awards.award.title Название достижения
#     @apiSuccess (Response) {String} active_awards.award.text Текст достижения
#     @apiSuccess (Response) {String} active_awards.award.photo_code Код миниатюры
#     @apiSuccess (Response) {String} active_awards.award.users_percent Актуальный процент пользователей
#     @apiSuccess (Response) {String} active_awards.award.description Описание
#     @apiSuccess (Response) {String} active_awards.award.condition Условия получения
#     @apiSuccess (Response) {String} active_awards.award.name Заголовок для рассказать друзьям
#     @apiSuccess (Response) {Number} active_awards.award.day День серии
#     @apiSuccess (Response) {Boolean} active_awards.award.repeat Повторяемый <code>True</code> - да,
#     <code>False</code> - нет
#
#     @apiSuccess (Response) {Object} rate_awards Достижения дневной нормы
#     @apiSuccess (Response) {Number} rate_awards.counter Счетчик повторений
#     @apiSuccess (Response) {String} rate_awards.date День достижения
#     @apiSuccess (Response) {Number} rate_awards.users_percent Процент пользователей
#     @apiSuccess (Response) {String} rate_awards.created День получения в timestamp, для выборки последнего
#     @apiSuccess (Response) {Object} rate_awards.award Достижение
#     @apiSuccess (Response) {String} rate_awards.award.title Название достижения
#     @apiSuccess (Response) {String} rate_awards.award.text Текст достижения
#     @apiSuccess (Response) {String} rate_awards.award.photo_code Код миниатюры
#     @apiSuccess (Response) {String} rate_awards.award.users_percent Актуальный процент пользователей
#     @apiSuccess (Response) {String} rate_awards.award.description Описание
#     @apiSuccess (Response) {String} rate_awards.award.condition Условия получения
#     @apiSuccess (Response) {String} rate_awards.award.name Заголовок для рассказать друзьям
#     @apiSuccess (Response) {Number} rate_awards.award.day День серии
#     @apiSuccess (Response) {Boolean} rate_awards.award.repeat Повторяемый <code>True</code> - да,
#     <code>False</code> - нет
#
#     @apiSuccess (Response) {Object} single_awards Одиночные достижения
#     @apiSuccess (Response) {String} single_awards.date День достижения
#     @apiSuccess (Response) {Number} single_awards.users_percent Процент пользователей
#     @apiSuccess (Response) {String} single_awards.created День получения в timestamp, для выборки последнего
#     @apiSuccess (Response) {Object} single_awards.award Достижение
#     @apiSuccess (Response) {String} single_awards.award.title Название достижения
#     @apiSuccess (Response) {String} single_awards.award.text Текст достижения
#     @apiSuccess (Response) {String} single_awards.award.photo_code Код миниатюры
#     @apiSuccess (Response) {String} single_awards.award.users_percent Актуальный процент пользователей
#     @apiSuccess (Response) {String} single_awards.award.description Описание
#     @apiSuccess (Response) {String} single_awards.award.condition Условия получения
#     @apiSuccess (Response) {String} single_awards.award.name Заголовок для рассказать друзьям
#     @apiSuccess (Response) {Boolean} single_awards.award.repeat Повторяемый <code>True</code> - да,
#     <code>False</code> - нет
#
#     @apiSuccess (Response) {Number} d_rate Непрерывность дней (дневная норма - Daily Rate)
#     @apiSuccess (Response) {Number} d_active Непрерывность дней (активность - Daily Active)
#     """
#     data = UserAwardsSerializer.get_user_awards(request.user)
#     return Response(data, status=status.HTTP_200_OK)
