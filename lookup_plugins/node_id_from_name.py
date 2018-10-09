from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
from ansible.plugins.lookup import LookupBase
import requests
import json



DOCUMENTATION = """
lookup: node_id_from_name
version_added: "0.1"
short_description: return ACI node id from node name
description:
    - Returns the node id of a fabricNode given it's name of the URL requested to be used as data in play.
options:
  verify:
    description: Flag to control SSL certificate validation
    type: boolean
    default: False

"""

EXAMPLES = """
- name: return fabric node id
  set_fact:
    node_id: "{{ lookup('node_id_from_name', 'LEAF123', provider={'url': 'https://apic', 'username': 'admin', 'password': 'admin', 'verify': 'false'}) }}"

"""

RETURN = """
  _list:
    description: list of list of lines or content of url(s)
"""


try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


def _headers(url, username, password, verify=False):
    payload = {
        "aaaUser": {
            "attributes": {
                "name": username,
                "pwd": password
            }
        }
    }

    headers = {'content-type': 'application/json'}
    url = "{}/api/aaaLogin.json".format(url)

    response = requests.post(url,
                             data=json.dumps(payload),
                             headers=headers,
                             verify=verify)


    token = response.json()['imdata'][0]['aaaLogin']['attributes']['token']
    headers['Cookie'] = response.headers['Set-Cookie']
    return headers


class LookupModule(LookupBase):

    def run(self, node_name, variables=None, **kwargs):

        self.set_options(direct=kwargs)
        node_name = node_name[0]

        provider = kwargs.pop('provider', {})
        url = provider['url']
        username = provider['username']
        password = provider['password']
        ret = []
        # Disable InsecureRequestWarning
        import urllib3
        urllib3.disable_warnings()

        headers = _headers(url,
                           username,
                           password,
                           verify=False)
        base_url = "{}/api/node/class/fabricNode.json".format(url)
        query_parm = '?query-target-filter=' \
                     'and(eq(fabricNode.name,"{}"))'.format(node_name)
        url = base_url + query_parm
        resp = requests.get(url,
                            headers=headers,
                            verify=False).json()
        if int(resp['totalCount']) == 1:
            ret.append(resp['imdata'][0]['fabricNode']['attributes']['id'])
        return ret
