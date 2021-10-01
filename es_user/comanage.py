#!/usr/bin/env python3
import requests
from typing import Tuple, Any, List
from requests.auth import HTTPBasicAuth
import re

# Some bad python code to show how to use COmanage REST API

# update here
CO_REGISTRY_URL = "https://registry-test.cilogon.org/registry/"
# you can register a user for accessing REST API. Username password go here (get them from COmanage UI)
COAPI_USER = "co_28.adam-test"
COAPI_KEY = "nxvh-awri-mmsf-7z6m"
# your CO ID (number) should go here
COID = "28"
# a special COI for 'active users'
CO_ACTIVE_USERS_COU = "1306"


def comanage_lookup_sub(sub: str) -> Tuple[int, str or None]:
    """
    Look up a user sub (ie. cilogon identifier) in COmanage
    """
    pass


def comanage_get_person_name(co_person_id) -> Tuple[int, str or None]:
    """
    Sometimes CILogon doesn't give us a person name initially, but
    it should be there after enrollment in COmanage.
    We provide co_person_id externally as it may or may not
    be already stored on the person.
    :return: tuple of comanage return code and name if any
    """
    assert co_person_id is not None
    params = {'copersonid': co_person_id}
    response = requests.get(
        url=CO_REGISTRY_URL + 'names.json',
        params=params,
        auth=HTTPBasicAuth(COAPI_USER, COAPI_KEY),
    )
    if response.status_code == 204:
        # we got nothing back, just say so
        return 200, None
    if response.status_code != 200:
        return response.status_code, None
    response_obj = response.json()
    names_list = response_obj.get('Names', None)
    if names_list is None or len(names_list) == 0:
        return 200, None
    # use the first name entry
    names = names_list[0]
    name = "".join(
        [
            names['Given'],
            ' ',
            names['Middle'],
            ' ',
            names['Family'],
            ' ',
            names['Suffix'],
        ]
    )
    name = re.sub(' +', ' ', name)
    return 200, name[:-1]


def comanage_list_people_matches(
    given: str = None, family: str = None, email: str = None
) -> Tuple[int, List]:
    """
    Try to get a brief list of people matching one or more of these fields.
    Returns a tuple of status code and a list of matching CoPeople entries (if any)
    """
    params = {'coid': str(COID)}
    if given is not None:
        params['given'] = given
    if family is not None:
        params['family'] = family
    if email is not None:
        params['mail'] = email
    # don't allow to ask stupid questions
    if len(params.keys()) == 1:
        return 500, []
    response = requests.get(
        url=CO_REGISTRY_URL + 'co_people.json',
        params=params,
        auth=HTTPBasicAuth(COAPI_USER, COAPI_KEY),
    )
    if response.status_code != 200:
        return response.status_code, []
    response_obj = response.json()
    return response.status_code, response_obj['CoPeople']


def comanage_check_person_couid(person_id, couid) -> Tuple[int, bool]:
    """
    Check if a given person is a member of couid. Return tuple of API status code
    and True or False. Strings or integers accepted as parameters
    """
    assert person_id is not None
    assert couid is not None
    params = {'coid': str(COID), 'copersonid': str(person_id)}
    response = requests.get(
        url=CO_REGISTRY_URL + 'co_person_roles.json',
        params=params,
        auth=HTTPBasicAuth(COAPI_USER, COAPI_KEY),
    )

    if response.status_code == 204:
        # we got nothing back - user with that ID has been deleted
        return 200, False
    if response.status_code != 200:
        return response.status_code, False
    response_obj = response.json()
    if response_obj.get('CoPersonRoles', None) is None:
        return 500, False
    for role in response_obj['CoPersonRoles']:
        if role.get('CouId', None) is not None and role['CouId'] == str(couid):
            return response.status_code, True
    return response.status_code, False


def comanage_check_active_person(person) -> Tuple[int, bool]:
    """
    Try to figure out person's co_person_id from different attributes.
    Returns COmanage status code and string id (if found)
    """
    # if person_id is present, skip the line
    if person.co_person_id is not None:
        print(f'Checking person {person.oidc_claim_sub} active status by co_person_id')
        code, active_flag = comanage_check_person_couid(
            person.co_person_id, CO_ACTIVE_USERS_COU
        )
        return code, active_flag, None
    # if email is present, try that first
    people_list = []
    person_id = None
    email = person.email if person.email is not None else person.eppn
    print(f'Checking person {person.oidc_claim_sub} active status by searching {email}')
    if email is not None:
        # easiest if there is email
        code, people_list = comanage_list_people_matches(email=email)
        if code != 200:
            return code, False, None
    else:
        if person.name is not None:
            name_split = person.name.split(' ')
            fname = name_split[0]
            if len(name_split) == 2:
                lname = name_split[1]
            else:
                lname = name_split[2]
            # try to find by fname, lname
            print(
                f'Checking person {person.oidc_claim_sub} active status by searching fname, lname'
            )
            code, people_list = comanage_list_people_matches(given=fname, family=lname)
            if code != 200:
                return code, False, None
    print(f'Found {len(people_list)} people')
    for people in people_list:
        if (
            people.get('ActorIdentifier', None) is not None
            and people['ActorIdentifier'] == person.oidc_claim_sub
        ):
            person_id = people.get('Id', None)
    if person_id is None:
        # person id not available
        return 200, False, None
    code, active_flag = comanage_check_person_couid(person_id, CO_ACTIVE_USERS_COU)
    return code, active_flag, person_id


class Person:
    def __init__(self, eppn, email, name, oidc_claim_sub, co_person_id):
        self.eppn = eppn
        self.email = email
        # self.name = name.split(' ')[0]
        # self.given = name.split(' ')[1]
        self.oidc_claim_sub = oidc_claim_sub
        self.co_person_id = co_person_id


SAMPLE_JWT = {
    "sub": "http://cilogon.org/serverA/users/21201616",
    "aud": "cilogon:/client_id/7b1d69bc506572a4f7153fbc5103e213",
    "idp_name": "Google",
    "idp": "http://google.com/accounts/o8/id",
    "token_id": "https://cilogon.org/oauth2/idToken/1cdfd053009f139430698655a7c2f86e/1628010788025",
    "cert_subject_dn": "/DC=org/DC=cilogon/C=US/O=Google/CN=Adam Clark A21201616",
    "name": "Adam Clark",
    "iss": "https://cilogon.org",
    "given_name": "Adam",
    "family_name": "Clark",
    "oidc": "100294778781914277982",
    "email": "adam.clark@iris.edu",
}


def jwt_to_person(jwt_data):
    return Person(
        jwt_data.get('email'),
        jwt_data.get('email'),
        jwt_data.get('name'),
        jwt_data.get('sub'),
        None,
    )


if __name__ == "__main__":
    person = jwt_to_person(SAMPLE_JWT)
    print(comanage_list_people_matches())
    print(comanage_check_active_person(person))
    print(comanage_check_person_couid("1597", CO_ACTIVE_USERS_COU))
    print("calling for name")
    print(comanage_get_person_name("1597"))
