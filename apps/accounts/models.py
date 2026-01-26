from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedUUIDModel

from .managers import UserManager


class User(TimeStampedUUIDModel, AbstractBaseUser, PermissionsMixin):
	email = models.EmailField(unique=True)
	is_active = models.BooleanField(default=True)
	is_staff = models.BooleanField(default=False)
	date_joined = models.DateTimeField(default=timezone.now)
	
	tag_items = GenericRelation("activity.TaggedItem", content_type_field="content_type", object_id_field="object_id")
	note_items = GenericRelation("activity.Note", content_type_field="content_type", object_id_field="object_id")
	activity_events = GenericRelation("activity.ActivityEvent", content_type_field="content_type", object_id_field="object_id")
	
	contact = models.OneToOneField(
		"contacts.Contact",
		null=True, blank=True,
		on_delete=models.SET_NULL,
		related_name="user",
	)
	
	objects = UserManager()
	
	USERNAME_FIELD = "email"
	
	def __str__(self) -> str:
		return self.email