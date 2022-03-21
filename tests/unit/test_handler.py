import json

import pytest

from flight_bridge import app


@pytest.fixture()
def apigw_event():
    """ Generates API GW Event"""

    return {
        "Trips": [
            {
                "TripNumber": "string",
                "PreIdentifier": 0,
                "IsReceived": True,
                "TripDisplayName": "string",
                "AltTripNumber": "string",
                "IsCancelled": True,
                "IsCompleted": True,
                "ExternalTripNumber": "string",
                "SystemIdentifier": "string",
                "TargetSystemIdentifier": "string",
                "OperatorIdentifier": "string",
                "OperatorCode": "string",
                "OperatorName": "string",
                "ConnectionCode": "string",
                "LastModifiedDate": "2022-03-21T01:47:26.130Z",
                "Legs": [
                    {
                        "LegNumber": "string",
                        "FarPart": "string",
                        "LegGroupName": "string",
                        "AircraftIcaoCode": "string",
                        "AircraftTypeName": "string",
                        "AircraftTail": "string",
                        "AircraftCallsign": "string",
                        "DepartureAirportCode": "string",
                        "DepartureAirportName": "string",
                        "DepartureFboName": "string",
                        "DepartureDate": "string",
                        "DepartureDateLocal": "string",
                        "ArrivalAirportCode": "string",
                        "ArrivalAirportName": "string",
                        "ArrivalFboName": "string",
                        "ArrivalDate": "string",
                        "ArrivalDateLocal": "string",
                        "IsPlaceholder": True,
                        "PlaceholderType": 1,
                        "CrewCount": 0,
                        "PassengerCount": 0,
                        "Travelers": [
                            {
                                "TravelerNumber": "string",
                                "FirstName": "string",
                                "LastName": "string",
                                "TravelerType": 1,
                                "CrewType": 0,
                                "MiddleName": "string",
                                "ContactEmail": "string",
                                "ContactPhone": "string",
                                "DateOfBirth": "2022-03-21T01:47:26.130Z",
                                "Gender": 1,
                                "NationalityIsoCode": "string",
                                "IsTransient": True,
                                "ContactCcEmail": "string",
                                "CellPhone": "string",
                                "CellPhone2": "string",
                                "IsWaitlist": True,
                                "BriefingStatus": 1,
                                "HomeAirportCode": "string",
                                "TsaRedressNumber": "string",
                                "Notes": "string",
                                "IsLeadPassenger": True,
                                "PassengerStatusCode": "string",
                                "PassengerStatusDescription": "string",

                                "TravelerDisplayNumber": "string"
                            }
                        ],

                        "DepartureAirportCodeType": 1,
                        "ArrivalAirportCodeType": 1,
                        "ArrivalDateType": 0,
                        "DepartureDateType": 0,
                        "LegProperties": {},
                        "IsCancelled": True,
                        "DepartureTime": {
                            "Type": 1,
                            "Time": "string"
                        },
                        "ArrivalTime": {
                            "Type": 1,
                            "Time": "string"
                        },
                        "AircraftEngineTypeCode": "string",
                        "CustomerName": "string",
                        "CustomerNumber": "string",
                        "CustomerEmail": "string",
                        "Purpose": "string",
                        "DepartureLocationIdentifier": "string",
                        "ArrivalLocationIdentifier": "string",
                        "ArrivalFboOrderNotes": "string",
                        "DepartureFboOrderNotes": "string",
                        "IsArrivalFuelRequested": True,
                        "IsDepartureFuelRequested": True,
                        "DepartureTimeTentative": True,
                        "ArrivalTimeTentative": True,
                        "IsLocked": True,
                        "IsReleased": True,
                        "RequestorType": 0,
                        "LegBase": "string",
                        "LegType": "string",
                        "IsDeadhead": True,
                        "AircraftFaaType": "string",
                        "AircraftHomeBaseAirportCode": "string",
                        "AircraftVendorIdentifier": "string",
                        "AircraftVendorName": "string",
                        "IsConvectionOven": True,
                        "IsMicrowave": True,
                        "IsSlotOven": True,
                        "IsToaster": True,
                        "IsSkillet": True,
                        "IsFullGalley": True,
                        "IsMiniGalley": True,
                        "IsOven": True,
                        "PlannerIdentifier": "string",
                        "PlannerFirstName": "string",
                        "PlannerLastName": "string",
                        "PlannerPhoneNumber": "string",
                        "PlannerEmailAddress": "string",
                        "NotifyPlannerForFlightFollowing": True,
                        "PlannerCellPhone": "string",
                        "LegNotes": "string",
                        "Priority": 0,
                        "Risk": 0,

                        "TripNotes": "string",
                        "TripEmail": "string",
                        "NotifyTripEmailForFlightFollowing": True
                    }
                ],
                "SystemIdentifier": "string",
                "OriginalSystemIdentifier": "string",
                "TargetSystemIdentifier": "string",
                "OperatorCode": "string",
                "CompanyIdentifier": "string",
                "OperatorName": "string",
                "ConnectionCode": "string",
                "NoWait": True,
                "MessageSequenceNumber": 0
            }
        ]
    }


def test_lambda_handler(apigw_event, mocker):
    ret = app.lambda_handler(apigw_event, "")
    data = json.loads(ret["body"])

    assert ret["statusCode"] == 200
    assert "message" in ret["body"]
    assert data["message"] == "hello world"
    # assert "location" in data.dict_keys()
