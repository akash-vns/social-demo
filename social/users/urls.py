from django.urls import path
from .views import (SignUpView, LoginView, SendRequestView, UserPendingRequest, UsersView,
                    RejectUserRequestView, AccessUserRequestView, UnFriendUserView)

urlpatterns = [
    path('register/', SignUpView.as_view()),
    path('login/', LoginView.as_view()),
    path('send-request/', SendRequestView.as_view()),
    path('users/', UsersView.as_view({'get': 'list'})),
    path("pending-requests/", UserPendingRequest.as_view()),
    path("reject-request/<int:request_id>", RejectUserRequestView.as_view()),
    path("accept-request/<int:request_id>", AccessUserRequestView.as_view()),
    path("unfriend-user/<int:friend_id>", UnFriendUserView.as_view())
]
