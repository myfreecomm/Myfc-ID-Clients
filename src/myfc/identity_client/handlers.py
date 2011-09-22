# -*- coding: utf-8 -*-
from datetime import datetime as dt

from identity_client.signals import pre_identity_authentication
from identity_client.utils import get_account_module

def update_identity_accounts(sender, identity, user_data, **kwargs):

    serviceAccount = get_account_module()

    if serviceAccount is not None:
        for item in user_data.get('accounts', []):
            try:
                account = serviceAccount.objects.get(uuid=item['uuid'])
            except serviceAccount.DoesNotExist:
                account = serviceAccount(uuid=item['uuid'])

            account.name = item['name']
            account.expiration = dt.strptime(item['expiration'], '%Y-%m-%d %H:%M:%S')
            account.add_member(identity, item['roles'])
            account.save()

    return


pre_identity_authentication.connect(
    update_identity_accounts, dispatch_uid="update_identity_accounts"
)
