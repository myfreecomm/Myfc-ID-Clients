# -*- coding: utf-8 -*-
import datetime

from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Identity(models.Model):
    """
    Myfc ID Users within the Django authentication system are represented by
    this model.

    email is required. Other fields are optional.
    """
    first_name = models.CharField(_('first name'), max_length=50, null=True)
    last_name = models.CharField(_('last name'), max_length=100, null=True)
    email = models.EmailField(_('e-mail address'), unique=True)
    uuid = models.CharField(_('universally unique id'), max_length=36, unique=True)
    is_active = models.BooleanField(_('active'), default=True,
        help_text=_("Designates whether this user should be treated as active. Unselect this instead of deleting accounts.")
    )
    last_login = models.DateTimeField(_('last login'), default=datetime.datetime.now)

    class Meta:
        verbose_name = _('identity')
        verbose_name_plural = _('identities')
        app_label = 'identity_client'

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