# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django import forms
from django.contrib.localflavor.br import forms as br_forms
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
    first_name = forms.CharField(
        label=_('First Name'), max_length=50, required=False
    )
    last_name = forms.CharField(
        label=_('Last Name'), max_length=100, required=False
    )
    email = forms.EmailField(
        label=_("Email Address"), max_length=75, required=True
    )

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

    cpf = br_forms.BRCPFField(
        required=False,
        label=_("CPF")
    )
    tos = forms.BooleanField(
        label=_(u'I have read and agree to the Terms of Service'),
        required=True,
        error_messages={
            'required': _(u"Você precisa ler e concordar com os termos de serviço")
        }
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
                raise forms.ValidationError(_(u"As senhas informadas são diferentes."))
        return self.cleaned_data

class IdentityAuthenticationForm(forms.Form):
    """
    Base class for authenticating users. Extend this to get a form that accepts
    email/password logins.
    """
    email = forms.EmailField(label=_(u"Email"), max_length=75, required=True)
    password = forms.CharField(label=_(u"Password"), widget=forms.PasswordInput)

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
            self.user_cache = MyfcidAPIBackend().authenticate(
                email=email, password=password
            )
            if self.user_cache is None:
                raise forms.ValidationError(_(u"Por favor digite seu e-mail e senha. O sistema diferencia minúsculas de maiúsculas."))
            elif not self.user_cache.is_active:
                raise forms.ValidationError(_(u"Esta conta está inativa."))

        # TODO: determine whether this should move to its own method.
        if self.request:
            if not self.request.session.test_cookie_worked():
                raise forms.ValidationError(_(u"Parece que seu navegador não aceita cookies. Por favor habilite os cookies."))

        return self.cleaned_data

    def get_user_id(self):
        if self.user_cache:
            return self.user_cache.id
        return None

    def get_user(self):
        return self.user_cache
