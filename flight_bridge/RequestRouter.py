import json
import os
import Message
import process_pilots_update
from ValidateToken import ValidateToken
from action_enum import action_enum

import wyvern_logins
import cglogging as cgl

logger_Class = cgl.cglogging()
logger = logger_Class.setup_logging()


class RequestRouter:
    dashboard_ids = os.environ.get("CAG_DASHBOARD_IDS")

    @classmethod
    def router(cls, action, request):
        message = Message.Message()

        if "securityToken" not in request["context"]:
            return message.get_fatal_standard_message(1)

        # return bad token if error
        errNum, return_type, errMsg = ValidateToken.validate_jwt(request["context"]["securityToken"])
        if errNum != 0:
            return message.get_response(errNum, "")

        message = Message.Message()
        # these on environment variables that will be pulled on deployment
        logger.debug("inside router")

        if action.upper() == action_enum.SubmitLogin.name.upper():
            logger.debug("submit login")
            response = wyvern_logins.submit_login_handler_request(request)
            logger.debug(json.dumps(response))
        elif action.upper() == action_enum.DeleteLogin.name.upper():
            logger.debug("delete login")
            response = wyvern_logins.delete_login(request)
        # else:
        #     return_code, key = wyvern_logins.logon(request)
        #     if return_code != 0:
        #         return message.get_fatal_standard_message(return_code)

        # temp hard coded link, this will be pulled by the user in the future
        if action.upper() == action_enum.UpdatePilots.name.upper():
            logger.debug("getting airaft and child details")
            response = process_pilots_update.update_hours(request)

        return response
