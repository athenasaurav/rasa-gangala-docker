"""For sending and recieving Auction ID"""


from typing import Text, List, Dict, Optional, Any
import requests
from datetime import datetime, time, timedelta

class Auction:

    access_token_url = 'http://172.105.36.229:8069/api/auth/get_tokens?username=admin&password=admin&access_lifetime=0'
    send_data_url = "http://172.105.36.229:8069/api/wk.reverse.auction"
    send_data_headers = {
        'Content-Type': 'text/html; charset=utf-8',
        'Access-Token': "access_token"
    }

    @classmethod
    def getAccessToken(cls) -> Text:
        """To get the access token from the server to send the auction data"""
        response = requests.get(url = cls.access_token_url)
        access_token = response.json()['access_token']
        return access_token

    @classmethod
    def getScript(cls, description: Text, time: int = 24) -> List:
        """Send the required format of the JSON"""
        row_data_list = [
        {
            "name" : 'Test Reverse Auction 3',
            "intial_price" : 1000.0,
            "reserve_price" : 50.0,
            "start_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "end_date": (datetime.now() + timedelta(hours = time)).strftime('%Y-%m-%d %H:%M:%S') ,
        "reverse_auction_line_ids" : [
            {
            'name' : 'Test Product1 for Reverse Auction 2',
                    'product_id' : 48,
                    'product_qty' : 4.0,
                    'price_unit' : 30.0,
                },
            {
            'name' : 'Test Product2 for Reverse Auction 2',
            'product_id' : 36,
                    'product_qty' : 2.0,
                    'price_unit' : 10.0,
            },
        ],
            "bid_decrement_rule_ids" : [
                {
                "id":1,
                },
                {
                "id":2,
                },
                {
                "id":3,
                },
                {
                "id":4,
                }
            ],
            "notify_before_expire" : True,
            "notify_before" : 15,
            "expire_note_send" : False,
            "notify_s_auction_running" : True,
            "notify_s_auction_extended" : True,
            "notify_s_auction_closed" : True,
            "notify_s_new_bid" : True,
            "notify_s_auction_completed" : True,
            "notify_w_auction_completed" : True,
            "notify_l_auction_completed" : True,
            "description" : description
        }
    ]
        return row_data_list

    @classmethod
    def writeScipt(cls, description: Text, time_stamp: int = 24) -> Text:
        """Called by the """
        access_token = cls.getAccessToken()
        row_data_list = cls.getScript(time = time_stamp, description = description)
        response = cls.sendData(data = row_data_list, access_token = access_token)
        string = "The details of your action are \n"
        for i in response:
            string = string + str(i).title() + ": " + str(response[i]).title() + "\n"
        return string

    @classmethod
    def sendData(cls, data: List, access_token: Text) -> List:
        headers = cls.send_data_headers
        headers['Access-Token'] = access_token
        response = requests.post(url = cls.send_data_url, headers = cls.send_data_headers, json = data)
        return response.json()[0]
