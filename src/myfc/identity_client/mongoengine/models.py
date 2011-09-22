# -*- coding: utf-8 -*-
from datetime import datetime as dt

from mongoengine import *
from mongoengine.queryset import Q

from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.models import SiteProfileNotAvailable

class Identity(Document):
    """
    Myfc ID Users within the Django authentication system are represented by
    this model.

    email is required. Other fields are optional.
    """
    first_name = StringField(max_length=50)
    last_name = StringField(max_length=100)
    email = StringField()
    uuid = StringField(max_length=36, unique=True)
    id_token = StringField(max_length=48, default=None)
    is_active = BooleanField(default=False)

    def __unicode__(self):
        return self.email

    def is_anonymous(self):
        """
        Always returns False. This is a way of comparing User objects to
        anonymous users.
        """
        return False

    def is_authenticated(self):
        """
        Always return True. This is a way to tell if the user has been
        authenticated in templates.
        """
        return True

    def is_staff(self):
        """
        Always returns False.
        """
        return False

    def get_full_name(self):
        "Returns the first_name plus the last_name, with a space in between."
        full_name = u'%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def set_password(self, raw_password):
        raise NotImplementedError

    def check_password(self, raw_password):
        raise NotImplementedError

    def set_unusable_password(self):
        raise NotImplementedError

    def has_usable_password(self):
        return False

    def get_and_delete_messages(self):
        messages = []
        for m in self.message_set.all():
            messages.append(m.message)
            m.delete()
        return messages

    def email_user(self, subject, message, from_email=None):
        "Sends an e-mail to this User."
        from django.core.mail import send_mail
        send_mail(subject, message, from_email, [self.email])

    def get_profile(self):
        """
        Returns site-specific profile for this user. Raises
        SiteProfileNotAvailable if this site does not allow profiles.
        """
        if not hasattr(self, '_profile_cache'):
            from django.conf import settings
            if not getattr(settings, 'AUTH_PROFILE_MODULE', False):
                raise SiteProfileNotAvailable
            try:
                app_label, model_name = settings.AUTH_PROFILE_MODULE.split('.')
                model = models.get_model(app_label, model_name)
                self._profile_cache = model._default_manager.using(self._state.db).get(user__id__exact=self.id)
                self._profile_cache.user = self
            except (ImportError, ImproperlyConfigured):
                raise SiteProfileNotAvailable
        return self._profile_cache

    def _get_message_set(self):
        import warnings
        warnings.warn('The user messaging API is deprecated. Please update'
                      ' your code to use the new messages framework.',
                      category=PendingDeprecationWarning)
        return self._message_set
    message_set = property(_get_message_set)


class AccountMember(EmbeddedDocument):
    identity = ReferenceField(Identity, required=True)
    roles = ListField(StringField(max_length=36))

    def set_roles(self, roles):
        roles = set(roles)
        self.roles = list(roles)
        

class ServiceAccount(Document):
    name = StringField(max_length=256, required=True)
    uuid = StringField(max_length=36, required=True)
    members = ListField(EmbeddedDocumentField(AccountMember))
    expiration = DateTimeField(required=False)


    def __unicode__(self):
        return self.name


    @queryset_manager
    def active(cls, qset):
        return qset.filter(Q(expiration=None)|Q(expiration__gte=dt.now()))


    @classmethod
    def for_identity(cls, identity, include_expired=False):
        if include_expired:
            qset = ServiceAccount.objects
        else:
            qset = ServiceAccount.active

        return qset.filter(members__identity=identity)


    @property
    def is_active(self):
        return (self.expiration is None) or (self.expiration >= dt.now())


    @property
    def members_count(self):
        return len(self.members)


    def add_member(self, identity, roles):
        new_member = self.get_member(identity)
        if new_member is None:
            new_member = AccountMember(identity=identity)
            self.members.append(new_member)

        new_member.set_roles(roles)
        self.save()

        return new_member


    def remove_member(self, identity):
        member = self.get_member(identity)
        if member is None:
            return self

        self.members.remove(member)
        self.save()

        return self


    def get_member(self, identity):
        for item in self.members:
            if item.identity == identity:
                return item

        return None
