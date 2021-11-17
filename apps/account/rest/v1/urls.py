from django.urls import path
from ..v1 import api as acc_api
from rest_framework_simplejwt.views import TokenRefreshView

"""
@apiDefine User User access rights needed.
Permission is granted to modify user objects.
"""
"""
@api {post} accounts/token/refresh/ Продление токена
@apiSuccessExample {json} Success-Response:
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhw"
}
}
@apiErrorExample {json} Error-Response:
{
    "detail": "Токен недействителен или просрочен",
    "code": "token_not_valid"
}
@apiVersion 1.0.0
@apiName token_refresh
@apiGroup Аутентификация
@apiParam {String} refresh Refresh Token пользователя
@apiSuccess (Response) {String} access Новый токен пользователя
"""
account = acc_api.AccountViewSet.as_view({'get': 'list'})
account_change_pass = acc_api.AccountViewSet.as_view({'post': 'change_password'})
account_update = acc_api.AccountViewSet.as_view({'patch': 'update_info'})

urlpatterns = [
    path('social_auth/<backend>/', acc_api.social_auth),
    path('auth/', acc_api.auth),
    path('exists/', acc_api.user_exists),
    path('registration/', acc_api.registration),
    path('resend_activate/', acc_api.resend_activate_token),
    path('activate/<uidb64>/<token>/', acc_api.activate, name='activate'),
    path('token/refresh/', TokenRefreshView.as_view()),
    path('reset_password/', acc_api.reset_password),
    path('account/', account),
    path('account/change_password/', account_change_pass),
    # path('account/update/', account_update),
    # path('email/change/', acc_api.ChangeEmailView.as_view()),
    # path('email/confirm/', acc_api.change_email_confirm),
    # path('new_email/add/', acc_api.AddNewEmailView.as_view()),
    # path('new_email/confirm/', acc_api.new_email_confirm),
    # path('drink_water/', acc_api.drink_water),
    # path('status_active/', acc_api.status_active),
    # path('account/achievements/', acc_api.user_awards),
    # path('account/single_award/create/', acc_api.create_single_award),
]
