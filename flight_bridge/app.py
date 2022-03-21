import json
import cglogging as cgl
import Message
from RequestRouter import RequestRouter

logger_Class = cgl.cglogging()
logger = logger_Class.setup_logging()


def lambda_handler(event, context):
    logger.debug(event)
    message = Message.Message()
    logger.debug("Received event: ")
    try:
        if "body" not in event:
            if "commonParms" not in event \
                    and "domainName" not in event["context"] \
                    and "action" not in event["commonParms"]:
                logger.error('Invalid message from cloudwatch: {} , error : {}'.format(event, 1))
                return message.get_fatal_standard_message(1)
            request_action = event["commonParms"]["action"]
            response = RequestRouter.router(request_action, event)
        else:
            logger.debug("body is in request")
            request = json.loads(json.dumps(event))
            logger.debug(request)
            body = json.loads(request["body"])
            logger.debug(body)

            if 'context' not in event["body"] \
                    and 'commonParms' not in request["body"] \
                    and 'domainName' not in request["body"]['context'] \
                    and 'action' not in request["body"]['commonParms']:
                logger.error('Invalid message from cloudwatch: {} , error : {}'.format(event, 1))
                return message.get_fatal_standard_message(1)

            request_action = body["commonParms"]["action"]
            logger.debug(request_action)
            response = RequestRouter.router(request_action, body)

        if response["standardResponse"]["returnCode"] == 0:
            transactionResponse = {'statusCode': '200', 'headers': {}}
            transactionResponse['headers']['Content - Type'] = 'applicationjson'
            transactionResponse['headers']['Access-Control-Allow-Methods'] = 'OPTIONS,POST,PUT,PATCH'
            transactionResponse['headers']['Access-Control-Allow-Headers'] = 'Content-Type'
            transactionResponse['headers']['Access-Control-Allow-Origin'] = '*'
            transactionResponse['headers']['Access-Control-Allow-Credentials'] = True
            transactionResponse['body'] = json.dumps(response)
        else:
            transactionResponse = {'statusCode': '400', 'headers': {}}
            transactionResponse['headers']['Content - Type'] = 'applicationjson'
            transactionResponse['headers']['Access-Control-Allow-Methods'] = 'OPTIONS,POST,PUT,PATCH'
            transactionResponse['headers']['Access-Control-Allow-Headers'] = 'Content-Type'
            transactionResponse['headers']['Access-Control-Allow-Origin'] = '*'
            transactionResponse['headers']['Access-Control-Allow-Credentials'] = True
            transactionResponse['body'] = json.dumps(response)
        logger.debug("Transaction Response: {}".format(transactionResponse))
        return transactionResponse

    except Exception as details:
        logger.error('Exception, Unexpected error: {} , {}'.format(19002, details))
        transactionResponse = {'statusCode': '400', 'headers': {}}
        transactionResponse['headers']['Content - Type'] = 'applicationjson'
        transactionResponse['headers']['Access-Control-Allow-Methods'] = 'OPTIONS,POST,PUT,PATCH'
        transactionResponse['headers']['Access-Control-Allow-Headers'] = 'Content-Type'
        transactionResponse['headers']['Access-Control-Allow-Origin'] = '*'
        transactionResponse['headers']['Access-Control-Allow-Credentials'] = True
        transactionResponse['body'] = json.dumps(message.get_fatal_standard_message(19002))
        return transactionResponse
