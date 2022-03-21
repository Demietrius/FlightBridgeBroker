import datetime
import json
import os

import fore_flight_accessor
from Message import Message
from lambda_accessor import lambda_accessor
from secret_manager import secret_manager


def submit_login(request):
    message = Message()
    return_code = 0
    error_message = None

    # getting api key from secret manager
    return_code, return_type, secret_token = secret_manager.get_secrets(os.getenv("CAG_FORE_FLIGHT_API"))
    if return_code != 0:
        return message.get_fatal_standard_message(return_code)

    # extracting api key from secret
    extracted_secret = json.loads(secret_token['SecretString'])
    request["request"]["account"]["vendorId"] = extracted_secret["vendorId"]
    request["request"]["account"]["token"] = [{"apiKey": request["request"]["account"]["apiKey"]}]

    # calling foreFlight
    return_code, foreflight_crew_response = fore_flight_accessor.get_crew(request)
    if return_code != 0:
        return message.get_fatal_standard_message(return_code)

    # add to account  plugin manager
    return_code, error_message, account_response = lambda_accessor.call_AccountPluginManger(
        build_account_plugin_submit_request(request))
    if return_code != 0 or ("accounts" in account_response["responseMessage"]
                            and account_response["responseMessage"]["accounts"] > 0):
        message.add_warnings({"number": return_code, "message": account_response["errorMessage"]})
        return message.get_fatal_standard_message(39002)

    # getting business profile
    return_code, error_message, read_business_profile = lambda_accessor.call_businessProfile(
        build_read_business_profile(request))
    if return_code != 0:
        return message.get_fatal_standard_message(return_code)
    for profile in read_business_profile["responseMessage"]:
        if profile["businessProfileId"] == 0 and "profileType" in profile and profile["profileType"].upper() == "SP":
            business_profile = profile
            break

    # building account for business profile
    business_account = {
        "name": "FOREFLIGHT",
        "type": "FLIGHTTOOL",
        "config": {},
        "status": "ACTIVE"
    }
    services = {
        "type": "SERVICES",
        "services": [business_account]
    }

    business_profile.pop("profileType")
    for cag_profile in business_profile["cagProfile"]:
        if cag_profile["type"] == "SERVICES":
            for service in cag_profile["services"]:
                if service["name"] == "FOREFLIGHT":
                    service["status"] = "ACTIVE"
                    break
            else:
                cag_profile["services"].append(business_account)
                break
    else:
        business_profile["cagProfile"].append(services)

    # update businessProfile
    return_code, error_message, business_profile = lambda_accessor.call_businessProfile(
        build_business_submit_login_request(request, business_profile))
    if return_code != 0:
        return message.get_fatal_standard_message(return_code)

    # reading user profiles
    return_code, error_message, read_user_profile = lambda_accessor.call_userprofile(
        build_user_profile(request))
    if return_code != 0:
        return message.get_fatal_standard_message(return_code)

    for user in read_user_profile["responseMessage"]:
        # building user profiles
        user_account = {
            "name": "FOREFLIGHT",
            "type": "FLIGHTTOOL",
            "config": {"name": "",
                       "address": "",
                       },
            "status": "ACTIVE"
        }
        cag_configuration = [{
            "type": "SERVICES",
            "services": [
                user_account
            ]
        }]

        if user["profileStatus"] != "ACT" \
                or len(user["userProfile"][0]["positions"]) < 1 \
                or "position" not in user["userProfile"][0]["positions"][0] \
                or user["userProfile"][0]["positions"][0]["type"] != "PILOT":
            continue
        # fixing object and array issues
        if "cagConfiguration" not in user or isinstance(user["cagConfiguration"], dict):
            user["cagConfiguration"] = cag_configuration

        name = None
        email = None

        # getting email from user
        for media in user["userProfile"][0]["socialMedias"]:
            if media["status"] == "PRIMARY" \
                    and media["mediaType"] == "EMAIL" \
                    and media["usage"] == "WORK":
                email = media["address"]

        # getting username
        name = user["userProfile"][0]["names"][0]["firstName"] + \
               " " + user["userProfile"][0]["names"][0]["lastName"]

        for config in user["cagConfiguration"]:
            if config["type"] == "SERVICES":
                for service in config["services"]:
                    # checking if ForeFlight exists
                    if service["name"].upper() == "FOREFLIGHT" \
                            and service["type"].upper() == "FLIGHTTOOL":
                        # if ForeFlight already exists inside user profile
                        for fore_flight_crew in foreflight_crew_response:
                            # if data has not changed then reactivate
                            if (service["config"]["name"] == fore_flight_crew["fullname"] \
                                    or service["config"]["address"] == fore_flight_crew["username"]):
                                service["status"] = "ACTIVE"
                                break
                            # if data has changed look for a match
                            if name.replace(" ", "") == fore_flight_crew["fullname"].replace(" ", "") \
                                    and email == fore_flight_crew["username"]:
                                service["config"] = {
                                    "name": name,
                                    "address": email,
                                }
                                service["status"] = "ACTIVE"
                                break
                        # this should break out of the loop if match is found
                        else:
                            pass
                        break
                else:
                    continue
                break

        # this logic will Link user to ForeFlight is email or name matches
        else:
            # getting name from user linking ForeFlight is first and last names match
            for fore_flight_crew in foreflight_crew_response:
                if name.replace(" ", "") != fore_flight_crew["fullname"].replace(" ", "") \
                        and email != fore_flight_crew["username"]:
                    continue

                else:
                    user_account["config"] = {
                        "name": name,
                        "address": email,
                    }
                    for config in user["cagConfiguration"]:
                        if config["type"] == "SERVICES":
                            config["services"].append(user_account)
                            break
                    # add array if there are no accounts
                    else:
                        user["cagConfiguration"] = cag_configuration
                        break
                    break
            else:
                continue
        #  update user Profile
        return_code, error_message, account_response = lambda_accessor.call_userprofile(
            build_update_user_profile(user, request))
        if return_code != 0:
            continue

    return message.get_response(return_code, account_response["responseMessage"])


def deactivate_login(request):
    message = Message()
    return_code = 0
    error_message = None

    return_code, error_message, read_business_profile = lambda_accessor.call_businessProfile(
        build_read_business_profile(request))
    if return_code != 0:
        message.add_warnings({"number": return_code, "message": read_business_profile["errorMessage"]})
        return message.get_fatal_standard_message(39002)
    for profile in read_business_profile["responseMessage"]:
        if profile["businessProfileId"] == 0 and "profileType" in profile and profile["profileType"].upper() == "SP":
            business_profile = profile
            break
    else:
        return 3
    business_profile.pop("profileType")
    for cag_profile in business_profile["cagProfile"]:
        if cag_profile["type"] == "SERVICES":
            for service in cag_profile["services"]:
                if service["name"] == "FOREFLIGHT":
                    service["status"] = "INACTIVE"
                    break
            else:
                pass
            break

    # update businessProfile
    return_code, error_message, business_profile = lambda_accessor.call_businessProfile(
        build_business_submit_login_request(request, business_profile))
    if return_code != 0:
        return message.get_fatal_standard_message(return_code)

    # reading user profiles
    return_code, error_message, read_user_profile = lambda_accessor.call_userprofile(
        build_user_profile(request))
    if return_code != 0:
        return message.get_fatal_standard_message(return_code)

    for user in read_user_profile["responseMessage"]:
        # skipping not pilot users
        if user["profileStatus"] != "ACT" \
                or len(user["userProfile"][0]["positions"]) < 1 \
                or "position" not in user["userProfile"][0]["positions"][0] \
                or user["userProfile"][0]["positions"][0]["type"] != "PILOT":
            continue

        for config in user["cagConfiguration"]:
            if config["type"] != "SERVICES":
                continue
            for service in config["services"]:
                # checking if ForeFlight exists
                if service["name"].upper() == "FOREFLIGHT" \
                        and service["type"].upper() == "FLIGHTTOOL":
                    service["status"] = "INACTIVE"
                    break
            else:
                continue
            break
        else:
            continue
        #   updating user profile
        return_code, error_message, account_response = lambda_accessor.call_userprofile(
            build_update_user_profile(user, request))
        if return_code != 0:
            continue

    # add account credentials
    return_code, error_message, account_details = lambda_accessor.call_AccountPluginManger(
        build_delete_account_request(request["request"]["supplierId"],
                                     request["request"]["keyPrefix"],
                                     request["request"]["secretName"],
                                     request["context"]["securityToken"]))
    if return_code != 0:
        return message.get_fatal_standard_message(return_code)

    return message.get_good_standard_message()


def build_update_user_profile(user, request):
    return {
        "context": {
            "securityToken": request["context"]["securityToken"],
            "domainName": "PROFILES",
            "transactionid": "PETERG PROFILES",
            "language": "EN",
            "client": "API"
        },
        "commonParms": {
            "action": "UPDATECAG",
            "view": "DEFAULT",
            "version": "1.0.0"
        },
        "request": {
            "supplierId": user["supplierId"],
            "businessProfileId": user["businessProfileId"],

            "lastChangeTime": user["lastChangeTime"],
            "userId": user["userId"],
            "cagConfiguration": user["cagConfiguration"]
        }
    }


def build_user_profile(request):
    return {
        "context": {
            "securityToken": request["context"]["securityToken"],
            "domainName": "PROFILES",
            "transactionid": "PETERG PROFILES",
            "language": "EN",
            "client": "API"
        },
        "commonParms": {
            "action": "READ",
            "view": "DEFAULT",
            "version": "1.0.0"
        },
        "request": {
            "supplierId": request["request"]["supplierId"]
        }
    }


def build_read_business_profile(request):
    return {
        "context": {
            "domainName": "BusinessProfile",
            "securityToken": request["context"]["securityToken"],
            "language": "EN"
        },
        "commonParms": {
            "action": "READ",
            "view": "DEFAULT",
            "version": "1.0.0",
            "transactionId": "PETERG ACCOUNTS"
        },
        "request": {
            "supplierId": request["request"]["supplierId"]
        }
    }


def build_business_submit_login_request(request, business_profile):
    return {
        "context": {
            "domainName": "BusinessProfile",
            "securityToken": request["context"]["securityToken"],
            "language": "EN"
        },
        "commonParms": {
            "action": "UPDATECAG",
            "view": "DEFAULT",
            "version": "1.0.0"
        },
        "request": {
            "supplierId": business_profile["supplierId"],
            "businessProfileId": business_profile["businessProfileId"],
            "cagProfile": business_profile["cagProfile"]
        }
    }

    " this is the logic for adding external accounts to aircraft profile"


def build_aircraft_read_request(request):
    return {
        "context": {
            "domainName": "AircraftSpecification",
            "securityToken": request["context"]["securityToken"],
            "language": "EN",
            "transactionid": "PETE CONTEXT"
        },
        "commonParms": {
            "action": "READ",
            "view": "DEFAULT",
            "version": "1.0.0"
        },
        "request": {
            "chartersupplierid": request["request"]["supplierId"]
        }
    }


def build_aircraft_submit_login_request(request, aircraft):
    return {
        "context": {
            "domainName": "AircraftSpecification",
            "securityToken": request["context"]["securityToken"],
            "language": "EN"
        },
        "commonParms": {
            "action": "UPDATEACCOUNTS",
            "view": "DEFAULT",
            "version": "1.0.0",
            "transactionId": "PETERG ACCOUNTS"
        },
        "request": {
            "chartersupplierid": request["request"]["supplierId"],
            "aircrafts": {
                "cagaircraftid": aircraft["cagaircraftid"],
                "activatedate": aircraft["activatedate"],
            },
            "newAccount": {
                "activeDate": format(datetime.date.today().strftime("%Y-%m-%d")),
                "keyPrefix": request["request"]["account"]["keyPrefix"],
                "name": "ForeFlight".upper(),
                "secretName": request["request"]["account"]["secretName"],
                "type": request["request"]["account"]["type"].upper()
            }
        }
    }


" this is the logic for adding external accounts to account plugin manager"


def build_account_plugin_submit_request(request):
    return {
        "context": {
            "domainName": "accountPluginManager",
            "securityToken": request["context"]["securityToken"],
            "language": "EN"
        },
        "commonParms": {
            "action": "SubmitLogin",
            "view": "Accounts",
            "version": "1.0.0",
            "transactionId": "PETERG AIRCRAFT"
        },
        "request": {
            "supplierId": request["request"]["supplierId"],
            "account": {
                "account": "ForeFlight",
                "password": "",
                "type": "FlightTool",
                "token": [{"apiKey": request["request"]["account"]["apiKey"]},
                          ]
            }
        }
    }


def build_delete_account_request(supplier_id, keyPrefix, secretName, token):
    return {
        "context": {
            "domainName": "AccountPluginManager",
            "securityToken": token,
            "language": "EN",
            "transactionid": "culpa nulla elit"
        },
        "commonParms": {
            "action": "DeleteLogin",
            "view": "DEFAULT",
            "version": "1.0.0",
            "client": "CAGPOS",
            "transactionid": "ve"
        },
        "request": {
            "supplierId": supplier_id,
            "secretName": secretName,
            "keyPrefix": keyPrefix
        }
    }


def build_account_request(supplier_id, api_key):
    return {
        "context": {
            "domainName": "AccountPluginManager",
            "securityToken": api_key,
            "language": "EN",
            "transactionid": "cupidatat "
        },
        "commonParms": {
            "action": "GetCredentialsByAccountType",
            "view": "DEFAULT",
            "version": "1.0.0",
            "client": "CAGPOS",
            "transactionid": "elit "
        },
        "request": {
            "supplierId": supplier_id,
            "account": "ForeFlight"
        }
    }
