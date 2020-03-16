#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import requests

class UserInfo:
    '''
    This class try to take some user info (following, followers, etc.)
    '''
    user_agent = ("Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/48.0.2564.103 Safari/537.36")
    url_user_info = "https://www.instagram.com/%s/" #"https://www.instagram.com/%s/?__a=1"


    def __init__(self, request,proxy_request):
        self.api_user_detail = 'https://i.instagram.com/api/v1/users/%s/info/'
        self.request = request
        self.proxy_request = proxy_request

    def get_info_user_by_id(self, user_id):
        """ Get username by user_id """
        try:
            url_info = self.api_user_detail % user_id
            if self.proxy_request:
                r = self.proxy_request.generate_proxied_request(url_info)
            else:
                r = self.request.get(url_info, headers="")
            all_data = json.loads(r.text)
            user = all_data["user"]
            return user
        except:
            print("Except on get_info_user_by_id")
            return False

    def get_user_id_by_login(self, user_name):
        url_info = self.url_user_info % (user_name)
        info = self.request.get(url_info)
        all_data = info.text[info.text.find('javascript">window._sharedData'):]
        id_user = int(all_data[all_data.find('"profilePage_') + 13: all_data.find('"', all_data.find('"profilePage_') + 13)])
        return id_user


