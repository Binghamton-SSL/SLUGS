from array import array
from django.utils.translation import ugettext as _
from oidc_provider.lib.claims import ScopeClaims


def userinfo(claims, user):
    # Populate claims dict.
    claims['name'] = f'{user.preferred_name if user.preferred_name else user.first_name} {user.last_name}'
    claims['given_name'] = user.preferred_name if user.preferred_name else user.first_name
    claims['family_name'] = user.last_name
    claims['preferred_username'] = user.preferred_name
    claims['email'] = user.email
    claims['phone_number'] = user.phone_number
    
    return claims


class CustomScopeClaims(ScopeClaims):

    info_groups = (
        _(u'Groups'),
        _(u'A users groups.'),
    )

    def scope_groups(self):
        # self.user - Django user instance.
        # self.userinfo - Dict returned by OIDC_USERINFO function.
        # self.scopes - List of scopes requested.
        # self.client - Client requesting this claims.
        dic = {
            'groups': [group.name for group in self.user.groups.all()]
        }

        return dic

    # If you want to change the description of the profile scope, you can redefine it.
    info_profile = (
        _(u'Profile'),
        _(u'Another description.'),
    )