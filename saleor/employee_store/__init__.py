from django.utils.translation import pgettext_lazy

class AuthTypes:
    """The different authentication types."""

    STANDARD = "standard"
    OKTA = "okta"

    CHOICES = [
        (STANDARD, pgettext_lazy("Auth type", "Standard")),
        (OKTA, pgettext_lazy("Auth type", "Okta")),
    ]
