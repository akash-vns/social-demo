from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.throttling import UserRateThrottle
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import filters as in_rest_filter
from django_filters.rest_framework import DjangoFilterBackend
from users.helpers import unfriend_user
from users.models import UserRequest, User
from users.serializers import SignUpSerializer, LoginSerializer, UserRequestSerializer, UserSerializer


# Create your views here.

class SignUpView(APIView):
    permission_classes = []
    authentication_classes = []
    serializer_class = SignUpSerializer

    def post(self, request, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.save()
        return Response({
            "token": token
        })


class LoginView(APIView):
    permission_classes = []
    authentication_classes = []
    serializer_class = LoginSerializer

    def post(self, request, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={"request": request})
        serializer.is_valid(raise_exception=True)
        token = serializer.save()
        return Response({
            "token": token
        })


class SendRequestView(APIView):
    serializer_class = UserRequestSerializer
    throttle_classes = [UserRateThrottle]

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request,
                                                                       "user": request.user})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "request sent successfully"})


class UserPendingRequest(APIView):
    serializer_class = UserRequestSerializer

    def get_queryset(self):
        return UserRequest.objects.filter(status=UserRequest.UserRequestStatus.pending.value,
                                          requestee=self.request.user)

    def get(self, request, **kwargs):
        qs = self.get_queryset()
        return Response(
            self.serializer_class(instance=qs, many=True).data
        )


class UsersView(ModelViewSet):
    """
    In this API
    if we pass query param friend=1 in query param it will return user current friends
    else it will return user suggested friends
    """
    serializer_class = UserSerializer
    pagination_class = LimitOffsetPagination
    filter_backends = [in_rest_filter.SearchFilter, DjangoFilterBackend]
    search_fields = ['=email', 'first_name']

    def get_queryset(self):
        user = self.request.user
        if self.request.query_params.get("friends"):
            return user.friends.all()
        exclude_users = list(user.friends.values_list("pk", flat=True))
        exclude_users.append(user.pk)
        qs = User.objects.exclude(pk__in=exclude_users)
        return qs


class BaseUserRequestHandler(APIView):
    success_message = None
    handler_method_name = None

    def get(self, request, **kwargs):
        request_id = kwargs.get("request_id")
        try:
            user_request = UserRequest.objects.filter(pk=request_id, status=UserRequest.UserRequestStatus.pending).get()
        except ObjectDoesNotExist:
            return Response({
                "request_id": "Object Not found."
            }, status=400)

        getattr(user_request, self.handler_method_name)()
        return Response({
            "message": self.success_message
        })


class RejectUserRequestView(BaseUserRequestHandler):
    success_message = "Request rejected successfully."
    handler_method_name = "reject_request"


class AccessUserRequestView(BaseUserRequestHandler):
    success_message = "Request accepted successfully."
    handler_method_name = "accept_request"


class UnFriendUserView(APIView):

    def get(self, request, **kwargs):
        user = self.request.user
        friend_id = kwargs.get("friend_id")
        if not user.friends.filter(pk=friend_id).exists():
            return Response({
                "message": "friend is not found."
            })
        if user.id == friend_id:
            return Response({
                "message": "self user ID passed."
            })
        try:
            friend = User.objects.filter(pk=friend_id).get()
        except ObjectDoesNotExist:
            return Response(
                {
                    "message": "friend ID dose not found."
                }
            )

        unfriend_user(user, friend)
        return Response(
            {"message": "operation successfully."}
        )
