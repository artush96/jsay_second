from django.urls import path, include

urlpatterns = [
    path('accounts/', include('apps.account.rest.v1.urls')),
    # path('billing/', include('apps.billing.rest.v1.urls')),
    path('core/', include('apps.core.rest.v1.urls')),
    # path('notification/', include('apps.notification.rest.v1.urls')),
    # path('feedback/', include('apps.feedback.rest.v1.urls')),
    # path('history/', include('apps.history.rest.v1.urls')),
]
