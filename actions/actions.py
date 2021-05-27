# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"
from copy import copy
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import EventType, SlotSet, AllSlotsReset, FollowupAction
from read_excel import BasicInputAndOutputsMethods as basics
from auction import Auction
from gpt import GPT


class Utilities():

    @classmethod
    def checkButtons(cls, buttonsList :List, type_: str = "payload") -> bool:
        """
        Checks whether the buttons is a Valid button or not
        If the buttons is with payload: then the buttons must be with len > 1
        else: len >= 1

        returns: True or False
        """
        return len(buttonsList) > 1 if type_ == "payload" else len(buttonsList) >= 1

    @classmethod
    def getSlots(cls,formname: str , tracker, domain) -> List:
        """Returns the slots in the domain dictionary"""
        slots = domain["forms"][formname]
        list_of_values = []
        for i in slots:
            list_of_values.append(Tracker.get_slot(f"{i}"))
        return list_of_values
    
    @classmethod
    def getLenofSlots(cls, form_name: str, tracker, domain) -> int:
        """Gets the length of slots in the domain file"""
        return len(domain["forms"][form_name])

    @classmethod
    def checkEntities(cls, entity: str, removals: list) -> str:
        returning_entity = ""
        for i in entity:
            if i not in removals:
                returning_entity += i
            else:
                returning_entity += " "
        return returning_entity.strip()


    @classmethod
    def createButtons(cls, intent: str, entity: str, slot_values: list) -> List:
        """ 
        Parameters:

        intent: str : The intent that needs to be mapped
        entity: str : The entity or slot name that needs to be kept as a key
        slot_values: list : A list of values as values for entity

        Returns:
        A list of buttons in the format that RASA needs
        Example: /intent{entity:value}
        """
        buttons = []
        for i in slot_values:
            dict_ = {}
            dict_['title'] = cls.checkEntities(entity = i, removals = ["_"])  #i.strip() if not i.endswith("_") else i.strip()[:-1]  #Removing the _ from the last position if exists
            intent_ = intent if not i.endswith("_") else intent + "_" + i.strip()[:-1] 
            intent_ = cls.checkEntities(entity = intent_, removals = [""])
            dict_['payload'] = "/" + intent_.strip() + "{\"" + entity.strip() + "\":\" "+i.strip()+" \"}"
            buttons.append(dict_)
        return buttons

    @classmethod
    def createButtonsWithoutpayload(cls, slot_values: list) -> List:
        """Creates the buttons without payload for forms"""
        buttons = []
        for i in slot_values:
            dict_ = {}
            dict_['title'] = i
            dict_['payload'] = i
            buttons.append(dict_)
        return buttons

    @classmethod
    def createButtonsWithDiff(cls, intent: str, entity: str, slot_values: list) -> List:
        """Creates buttons with a /restart button as the last option"""
        buttons = []
        for i in slot_values:
            dict_ = {}
            dict_['title'] = i
            dict_['payload'] = "/" + intent.strip() + "{\"" + entity.strip() + "\":\" "+i.strip()+" \"}"
            buttons.append(dict_)
        buttons.append({"title": "No", "payload":"/restart"})
        return buttons
    
    @classmethod
    def convertListToRequiredFormat(cls, data: List) -> Text:
        """For the API to convert to required format for the API"""
        string = f" | ".join(data)
        return string
    
    @classmethod
    def BeautigyString(cls, data: List) -> Text:
        return ", ".join([i.strip() for i in data])
    
    @classmethod
    def createButtonIntens(cls, intents: str, no: str = True) -> List:
        buttons = []
        buttons.append({"title" : f"{intents}", "payload": f"/{intents}"})

        if no is True:
            buttons.append({"title" : "No", "payload": "/restart"})
        return buttons 

class ActionAllInOne(Action):
    def name(self):
        return "action_AllInOne"
    
    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        """
        One run method for all standalone responses
        To preserver the slot values, the slot "data" is used to store them in a list format
        To preserver the primary entity a slot "dummy" is used to store the current value and then transfer to data slot
        """
        channel = tracker.get_latest_input_channel().strip() #Tracking the Current channel name
        channel = "rest"  # Making the channel rest for now
        intent = tracker.get_intent_of_latest_message().strip() # Tracking the Intent
        intent_org = copy(intent)
        if intent in ["location", "contact"] and tracker.get_slot("form_intent") is None:
            return []
        intent = intent if intent not in ["location", "contact"] else tracker.get_slot("form_intent")
        slot_value = tracker.get_slot(intent) # Getting the slot value
        response_number = tracker.get_slot(f"{intent}_count") # Getting the Index number
        if slot_value is None:
            """
            If the Slot values are None. That is if the user is intitating a specific intent for the 1st time.
            Since there are no slots are filled. The bot prompts the Entities that are extracted from the JSON file.
            """
            slot_values = basics.giveEntity(intent = intent) # Getting the entities based on the intent
            buttons = Utilities.createButtons(intent = intent, entity = intent, slot_values = slot_values) # Creating the buttons from the list of slot values
            dispatcher.utter_message(text = "Select one", buttons = buttons) # Dispatching the text and buttons
            return [SlotSet("form_intent", intent)]
        else:
            """
            If the user is already in the conversation with the same intent.
            The bot looks for the responses
            """
            slot_value = slot_value.lower().strip() # Converting the slot value to lower inorder to maintain equaity  for matching
            if response_number is not None:
                response_number = response_number.strip()
            else:
                """If the user is in his 1st conversation, setting the response number to str(0)"""
                response_number = "0"
            response, next_response  = basics.giveResponse(intent = intent, entity = slot_value, response_number = response_number, channel = channel) # Getting the Current and next response from the JSON file
            str_next_response = " ".join(next_response)
            if next_response == "":
                """
                If the next_response is None that is the current message is End of the conversation.
                Dispatching the message, Setting the final slot values.
                """
                current_slots = tracker.get_slot("data")
                if current_slots is None:
                    current_slots = []
                    current_slots.append(tracker.get_slot(intent_org))
                if "location" not in str_next_response.lower() and "contact" not in str_next_response.lower() and "location" not in response.lower() and "contact" not in response.lower():
                    dispatcher.utter_message(text = response)

                dummy_slot_value = tracker.get_slot("dummy")
                if dummy_slot_value is not None: current_slots.append(dummy_slot_value)
                current_slots.insert(0, tracker.get_slot(intent))

                if "location" in str_next_response.lower() or "contact" in str_next_response.lower() or "location" in response.lower() or "contact" in response.lower():
                    current_slots = [i for i in current_slots if i is not None]
                    for index, values in enumerate(current_slots[:-1], 0):
                        if values == current_slots[index+1]:
                            current_slots.pop(index)
                    string = Utilities.BeautigyString(current_slots)
                    dispatcher.utter_message(text = f"Please confirm that {string}", buttons = Utilities.createButtonsWithDiff(intent = "general_form", entity = "dummy", slot_values = ["Yes"]) )
                    return [SlotSet("data", current_slots)]
                else:
                    for index, values in enumerate(current_slots[:-1], 0):
                        if values == current_slots[index+1]:
                            current_slots.pop(index)
                    # print("The Final slot values that are needed to send to the server are: ", current_slots)
                    string = Utilities.convertListToRequiredFormat(data = current_slots)
                    auction_response = Auction.writeScipt(description = string)
                    dispatcher.utter_message(text = auction_response)
                return [SlotSet("data", current_slots), AllSlotsReset()]
                
            else:
                """
                If there is still a next response.
                The entity is changed to dummy inorder to preserve the entity name.
                """
                current_slots = tracker.get_slot("data")
                if current_slots is None:
                        current_slots = []
                dummy_slot_value = tracker.get_slot("dummy")
                if dummy_slot_value is not None:
                    current_slots.append(tracker.get_slot("dummy"))
                for i in ["location", "contact"]:
                    temp = tracker.get_slot(i)
                    if temp is not None:
                        current_slots.append(temp)
                str_next_response = " ".join(next_response)
                if not "location" or "contact" in str_next_response.lower():
                    entity = "dummy"
                    buttons = Utilities.createButtons(intent = intent, entity = entity, slot_values = next_response[1:])               
                elif "location" in str_next_response.lower() or "contact" in str_next_response.lower() or "location" in response or "contact" in response:
                    if current_slots[0] != tracker.get_slot(intent_org):  current_slots.append(tracker.get_slot(intent_org))
                    current_slots.append(tracker.get_slot("dummy"))
                    current_slots = [i for i in current_slots if i is not None]
                    for index, values in enumerate(current_slots[:-1], 0):
                        if values == current_slots[index+1]:
                            current_slots.pop(index)
                    string = Utilities.BeautigyString(current_slots)
                    dispatcher.utter_message(text = f"Please confirm that {string}", buttons = Utilities.createButtonsWithDiff(intent = "general_form", entity = "dummy", slot_values = ["Yes"]) )
                else:
                    entity = "dummy"
                    if "select" in next_response[0].lower():
                        next_response = next_response[1:]
                    buttons = Utilities.createButtons(intent = intent_org, entity = entity, slot_values = next_response)
                    buttons = buttons if Utilities.checkButtons(buttons) else None
                    dispatcher.utter_message(text = response, buttons = buttons)
                return [SlotSet(f"{intent}_count", str(int(response_number)+1)), SlotSet("data", current_slots)]



def configuredForActionAskSlots(response_number: str):
    def deco(klass):
        def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict) -> List[EventType]:
            form_name = tracker.active_loop['name']
            if response_number == "0":
                intent = tracker.get_slot("form_intent")
                entity = tracker.get_slot(intent)
                response, nextresponse = basics.giveResponse(intent = intent, entity = entity, response_number = response_number)
                buttons = Utilities.createButtonsWithoutpayload(slot_values = nextresponse[1:])
                if Utilities.checkButtons(buttonsList = buttons, type_ = "withput"):
                    dispatcher.utter_message(text = response, buttons = buttons)
                else:
                    dispatcher.utter_message(text = f"{response}\n{nextresponse}")
                return [SlotSet("form_intent", intent)]
            else:
                intent_org = "form_intent"
                intent = tracker.get_slot(intent_org)
                entity = tracker.get_slot(intent)
                response, nextresponse = basics.giveResponse(intent = intent, entity = entity, response_number = response_number)
                buttons = Utilities.createButtonsWithoutpayload(slot_values = nextresponse[1:])
                dispatcher.utter_message(text = response, buttons = buttons if Utilities.checkButtons(buttonsList = buttons, type_ = "without") else None)
        klass.run = run
        return klass
    return deco



@configuredForActionAskSlots(response_number = "0")
class ActionSlotAsk(Action):
    
    def name(self) -> Text:
        return "action_ask_slot0"



@configuredForActionAskSlots(response_number = "1")
class ActionSlotAsk1(Action):
    
    def name(self) -> Text:
        return "action_ask_slot1"

@configuredForActionAskSlots(response_number = "2")
class ActionSlotAsk2(Action):
    
    def name(self) -> Text:
        return "action_ask_slot2"

@configuredForActionAskSlots(response_number = "3")
class ActionSlotAsk3(Action):
    
    def name(self) -> Text:
        return "action_ask_slot3"


@configuredForActionAskSlots(response_number = "4")
class ActionSlotAsk4(Action):
    
    def name(self) -> Text:
        return "action_ask_slot4"

@configuredForActionAskSlots(response_number = "5")
class ActionSlotAsk5(Action):
    
    def name(self) -> Text:
        return "action_ask_slot5"






class ActionSumbit(Action):

    def name(self) -> Text:
        return "action_submit"
    
    def run(self, dispatcher: "CollectingDispatcher", tracker: Tracker, domain: "DomainDict") -> List[Dict[Text, Any]]:
        intent = tracker.get_slot("form_intent").strip()
        entity = tracker.get_slot(intent).strip()[:-1]
        try:
            slots = domain["forms"][f"{intent}_{entity}"]
        except:
            slots = domain["forms"]["general_form"]
        list_of_values = []
        for i in slots:
            list_of_values.append(tracker.get_slot(f"{i}"))
        currnt_slots = tracker.get_slot("data")
        if currnt_slots is None:
            currnt_slots = []
        string = Utilities.convertListToRequiredFormat(data = currnt_slots + list_of_values)
        server_response = Auction.writeScipt(description = string)
        dispatcher.utter_message(text = server_response)
        return [AllSlotsReset()]


class ActionNLUFallback(Action):

    def name(self) -> Text:
        return "action_nlu_fallback"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: "DomainDict") -> List[Dict[Text, Any]]:
        intent = tracker.get_intent_of_latest_message()
        intent = tracker.get_slot("form_intent")
        print(intent)
        latest_message = tracker.latest_message['text']
        try:
            instance = GPT(question = latest_message)
        except:
            dispatcher.utter_message(text = "Something went wrong", buttons = Utilities.createButtonIntens(intents = intent, no = True))
            return []
        else:
            dispatcher.utter_message(text = instance + "\nYou are out of the conversation, do you like to go back to the conversation", buttons = Utilities.createButtonIntens(intents = intent, no = True))
            return []