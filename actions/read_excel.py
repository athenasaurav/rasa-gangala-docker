""" 
File created for extraction of Excel File and transfer it to a JSON and send the requriements for the bot
"""

import pandas as pd
import copy
import json
import re
from typing import Optional, Dict, List



""" 
Commented part is the code to extract the data from the Excel and convert it to JSON.
Do not uncomment it. 
"""
# data = pd.read_excel(io = "data.xlsx")
# data = data.to_json(orient = 'records')

# with open("data.json", "w") as json_file:
#     json_file.write(data)

with open("data.json") as json_file:
    data = json.load(json_file)


class BasicInputAndOutputsMethods():
    """Basic methods for the bot responses from the JSON file"""
    @classmethod
    def convertTextToList(cls, Text: str) -> List:
        """
        Convert the given text to list that is extracted from the TextResponse or UserSays in the JSON file

        Parameters:
        Text: str : A string of response with - or \n or ,

        Returns:
        A list of Splitted values from the given text

        """
        converted = re.split(r" - |\n|,| or ", Text)
        for index, values in enumerate(converted, 0):
            if values == "" or values == " " or values is None:
                converted.pop(index)
        return converted



    @classmethod
    def giveEntity(cls, intent: str) -> List:
        """ 
        Provides the Entity from the intent

        Parameters:
        intent: The intent that needs to be matched with the JSON file

        Returns:
        List of buttons as a list that needs to be returned for RASA 
        """
        intent_list = intent.split("_") # Spltting the intent
        intent = " ".join([i.strip() for i in intent_list if i != "" or i != " " ]) # Splitting and Joining them as a spaced
        buttons = []
        entities = []
        for i in data:
            if i['INTENT'] == intent:
                if i['ENTITY'] not in entities:
                    buttons.append(i['ENTITY'])
                    entities.append(i['ENTITY'])
        return buttons

    @classmethod
    def giveResponse(cls, intent: str, entity: str, response_number: str, channel: str = "rest") -> List:
        """
        Gives the response other than the Entity like TextResponse and returns the UserSays as next response.

        Parameters:
        intent: str : The intent that should be matched in the JSON file in lower to avoid case issues
        entity: str : The entity to match in JSON file in lower case
        response_number: str : The index of the JSON file
        channel: str : Either be rest or sellerchannel

        Returns:
        List of current response and the next response
        """
        # Lowering to avoid case sesitive
        intent = intent.lower() 
        entity = entity.lower().strip()
        intent_list = intent.split("_") # The intent will be a_b_c format so we need to split 
        intent = " ".join([i.strip() for i in intent_list ]) #and update that to a b c as in JSON fu
        for i in data:
            if channel is None or channel == "rest":
                # If there is no channle of rest channel display the default channel JSON 
                condition = (i['INTENT'].lower() == intent and i['ENTITY'].lower() == entity)
            elif channel is not None and channel != "rest":
                try:
                    # In try may cause crash due to all sets does not contain channel name 
                    condition = i['INTENT'].lower() == intent and i['ENTITY'].lower() == entity and i['channel'] == channel
                except:
                    # Any error due to Channel name returns False to continue the session
                    condition  = False
                else:
                    # If no erroe match the data with the JSON set
                    condition = (i['INTENT'].lower() == intent and i['ENTITY'].lower() == entity and i['channel'] == channel)
            if condition:
                #If the response is not False or True
                if response_number == "0":
                    # If the response number is 0 that means the response is like TextResponse or UserResponse it 
                    # Checks for the correspondings
                    response  = i[f'TextResponse']
                    if i[f'UserSays'] is not None:
                        nextResponse = cls.convertTextToList(i[f'UserSays']) # It is in a string format and needs to be converted 
                        return response, nextResponse #Return if there is a nextresponse
                    return response, "" # Else return "" as nextresponse
                else:
                    # If reponse_number > 0 then check for UserResponse.1 or TextResponse.1
                    response  = i[f'TextResponse.{response_number}']
                    try:
                       i[f'UserSays.{response_number}']
                    except:
                        return response, ""
                    else: 
                        if i[f'UserSays.{response_number}'] is not None:
                            nextResponse = cls.convertTextToList(i[f'UserSays.{response_number}'])
                            return response, nextResponse #Return if there is a nextresponse
                        return response, ""  # Else return "" as nextresponse
            else:
                # Any false condition due to KeyError will continue the bot
                continue