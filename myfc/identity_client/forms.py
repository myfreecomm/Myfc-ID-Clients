# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django import forms
from backend import MyfcidAPIBackend


class RegistrationForm(forms.Form):
    """
    Form for registering a new user account.

    Validates that the email is not already registered, and
    requires the password to be entered twice to catch typos.

    Subclasses should feel free to add any additional validation they
    need, but should avoid defining a ``save()`` method -- the actual
    saving of collected user data is delegated to the active
    registration backend.

    """
    email = forms.EmailField(label=_("Email"), max_length=75, required=True)
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput, 
        min_length=6, max_length=50
    )
    password2 = forms.CharField(
        label=_("Password (again)"),
        widget=forms.PasswordInput, 
        min_length=6, max_length=50
    )

    def clean(self):
        """
        Verifiy that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.

        """
        if 'password' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_("The two password fields didn't match."))
        return self.cleaned_data


class IdentityAuthenticationForm(forms.Form):
    """
    Base class for authenticating users. Extend this to get a form that accepts
    email/password logins.
    """
    email = forms.EmailField(label=_("Email"), max_length=75, required=True)
    password = forms.CharField(label=_("Password"), widget=forms.PasswordInput)

    def __init__(self, request=None, *args, **kwargs):
        """
        If request is passed in, the form will validate that cookies are
        enabled. Note that the request (a HttpRequest object) must have set a
        cookie with the key TEST_COOKIE_NAME and value TEST_COOKIE_VALUE before
        running this validation.
        """
        self.request = request
        self.user_cache = None
        super(IdentityAuthenticationForm, self).__init__(*args, **kwargs)

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        if email and password:
            self.user_cache = MyfcidAPIBackend().authenticate(email=email,
                                                             password=password)
            if self.user_cache is None:
                raise forms.ValidationError(_("Please enter a correct email and password. Note that both fields are case-sensitive."))
            elif not self.user_cache.is_active:
                raise forms.ValidationError(_("This account is inactive."))

        # TODO: determine whether this should move to its own method.
        if self.request:
            if not self.request.session.test_cookie_worked():
                raise forms.ValidationError(_("Your Web browser doesn't appear to have cookies enabled. Cookies are required for logging in."))

        return self.cleaned_data

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache


class LoginOrRegisterForm(IdentityAuthenticationForm):

    email = forms.EmailField(label=_("Email"), max_length=75, required=True)
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput, 
        min_length=6, max_length=50
    )
    password2 = forms.CharField(
        label=_("Password (again)"),
        widget=forms.PasswordInput, 
        min_length=6, max_length=50,
        required=False
    )
    new_user = forms.BooleanField(label=_(u'New User?'), required=False)

    def clean(self):
        """
        Verifiy that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.
        """
        if self.cleaned_data['new_user']:
            if self.cleaned_data['password'] != self.cleaned_data['password2']:
                raise forms.ValidationError(
                    _("The two password fields didn't match.")
                )
        else:
            self.cleaned_data = super(LoginOrRegisterForm, self).clean()

        del(self.cleaned_data['new_user'])

        return self.cleaned_data

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache
