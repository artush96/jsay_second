from rest_framework import permissions
from datetime import datetime, timezone
from django.http import Http404
from rest_framework.exceptions import APIException
from rest_framework import status
from rest_framework.utils.serializer_helpers import ReturnDict, ReturnList
from django.utils.encoding import force_text
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
UserModel = get_user_model()


def _get_error_details(data, default_code=None):
    """
    Descend into a nested data structure, forcing any
    lazy translation strings or strings into `ErrorDetail`.

    Keeps None, True, False and integers.
    """
    if isinstance(data, list):
        ret = [
            _get_error_details(item, default_code) for item in data
        ]
        if isinstance(data, ReturnList):
            return ReturnList(ret, serializer=data.serializer)
        return ret
    elif isinstance(data, dict):
        ret = {
            key: _get_error_details(value, default_code)
            for key, value in data.items()
        }
        if isinstance(data, ReturnDict):
            return ReturnDict(ret, serializer=data.serializer)
        return ret

    if data is None or data is True or data is False or isinstance(data, int):
        return data
    return force_text(data)


class BlockedAPIException(APIException):
    """
    raises API exceptions with custom messages and custom status codes
    """
    status_code = status.HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS
    default_code = 'error'
    default_detail = {"error_code": 1, "error_message": _("Смена емейла заблокирована на 24 часа")}

    def __init__(self, detail=None, code=None):
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code

        if not isinstance(detail, dict) and not isinstance(detail, list):
            detail = [detail]

        self.detail = _get_error_details(detail, code)

    def get_codes(self):
        return self.default_code

    def get_full_details(self):
        raise NotImplementedError


class IsChangeEmailAccess(permissions.BasePermission):

    def has_permission(self, request, view):
        now = datetime.now(timezone.utc)
        try:
            if request.user.change_email.filter(blocked_time__gte=now).exists():
                raise BlockedAPIException()
            return True
        except AttributeError:
            return True


class IsEmailAccount(permissions.BasePermission):

    def has_permission(self, request, view):
        try:
            if request.user.authorized == "0":
                return False
            return True
        except AttributeError:
            raise Http404
