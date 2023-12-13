from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager as BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password


class UserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not email:
            raise ValueError('The given username must be set')
        email = self.normalize_email(email)
        # Lookup the real model class from the global app registry so this
        # manager method can be used in migrations. This is fine because
        # managers are by definition working on the real model.
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class AbstractCreatedUpdated(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractUser):
    username = None
    email = models.EmailField(_("email address"), unique=True, error_messages={
        "unique": _("A user with that email already exists."),
    }, )

    USERNAME_FIELD = "email"
    friends = models.ManyToManyField("self")
    REQUIRED_FIELDS = []

    objects = UserManager()


class UserRequest(AbstractCreatedUpdated):
    """
    requestor is one you send the request
    requestee is one who receive request

    """
    class UserRequestStatus(models.TextChoices):
        pending = "pending"
        rejected = "rejected"
        accepted = "accepted"

    status = models.CharField(max_length=20, choices=UserRequestStatus.choices, default=UserRequestStatus.pending)
    requestor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="request_recived")
    requestee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="request_send")

    def accept_request(self):
        self.status = UserRequest.UserRequestStatus.accepted.value
        self.save(update_fields=['status'])
        self.requestee.friends.add(self.requestor)
        self.requestor.friends.add(self.requestee)

    def reject_request(self):
        self.status = UserRequest.UserRequestStatus.rejected.value
        self.save(update_fields=['status'])
