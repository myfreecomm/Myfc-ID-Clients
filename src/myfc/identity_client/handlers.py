# -*- coding: utf-8 -*-
import logging
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
            account.plan_slug = item['plan_slug']
            account.url = item['url']

            expiration = item.get('expiration', None)
            if expiration:
                new_expiration = dt.strptime(expiration, '%Y-%m-%d %H:%M:%S')
                account.update_expiration(new_expiration)
            else:
                account.update_expiration(None)

            try:
                account.add_member(identity, item['roles'])
                account.save()
            except Exception, e:
                message = 'Error updating accounts for identity %s (%s): %s <%s>'
                logging.error(message, identity.email, identity.uuid, e, type(e))

            message = 'Identity %s (%s) at account %s (%s) members list'
            logging.info(message, identity.email, identity.uuid, account.name, account.uuid)

    return


def dissociate_old_identity_accounts(sender, identity, user_data, **kwargs):

    current_associations = user_data.get('accounts', [])
    current_uuids = [item['uuid'] for item in current_associations]

    serviceAccount = get_account_module()
    cached_associations = serviceAccount.for_identity(identity, include_expired=True)

    stale_accounts = [account for account in cached_associations if account.uuid not in current_uuids]

    for account in stale_accounts:
        account.remove_member(identity)
        account.save()
        message = 'Identity %s (%s) was removed from account %s (%s) members list.'
        logging.info(message, identity.email, identity.uuid, account.name, account.uuid)

    return


pre_identity_authentication.connect(
    update_identity_accounts, dispatch_uid="update_identity_accounts"
)
pre_identity_authentication.connect(
    dissociate_old_identity_accounts, dispatch_uid="dissociate_old_identity_accounts"
)
