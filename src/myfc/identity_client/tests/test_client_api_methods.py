# -*- coding: utf-8 -*-
import json
from datetime import datetime as dt, timedelta

mocked_accounts_json = """[
    {
        "service_data": {
            "name": "John App", "slug": "johnapp"
        },
        "account_data": {
            "name": "Pessoal",
            "uuid": "e823f8e7-962c-414f-b63f-6cf439686159"
        },
        "plan_slug": "plus",
        "roles": ["owner"],
        "membership_details_url": "http://192.168.1.48:8000/organizations/api/accounts/e823f8e7-962c-414f-b63f-6cf439686159/",
        "expiration": "%s",
        "external_id": null
    },
    {
        "service_data": {
            "name": "John App", "slug": "johnapp"
        },
        "account_data": {
            "name": "Myfreecomm",
            "uuid": "b39bad59-94af-4880-995a-04967b454c7a"
        },
        "plan_slug": "max",
        "roles": ["owner"],
        "membership_details_url": "http://192.168.1.48:8000/organizations/api/accounts/b39bad59-94af-4880-995a-04967b454c7a/",
        "expiration": "%s",
        "external_id": null
    }
]""" % (
    (dt.today() + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
    (dt.today() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S'),
)

mocked_accounts_list = json.loads(mocked_accounts_json)
