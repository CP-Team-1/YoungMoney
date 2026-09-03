import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)

    # Opaque identifier for anything user-facing (API responses, URLs), so
    # the sequential integer pk is never exposed and can't be enumerated.
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    is_verified = models.BooleanField(default=False)

    # Account-level lockout, independent of the per-IP login throttle.
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email
