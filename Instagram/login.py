import time
import random
from .user_info import UserInfo


class Login:
    def __init__(self, request,user_agent, login_post):
        self.request = request
        self.user_agent = user_agent
        self.url = 'https://www.instagram.com/'
        self.url_login = 'https://www.instagram.com/accounts/login/ajax/'
        self.accept_language = 'en-US,en;q=0.5'
        self.user_login = login_post["username"]
        log_string = 'login as %s...\n' % (self.user_login)
        print(log_string)
        self.login_post = login_post
        self.init_request()
        self.request_login()

    def init_request(self):
        self.request.headers.update({
            'Accept': '*/*',
            'Accept-Language': self.accept_language,
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Content-Length': '0',
            'Host': 'www.instagram.com',
            'Origin': 'https://www.instagram.com',
            'Referer': 'https://www.instagram.com/',
            'User-Agent': self.user_agent,
            'X-Instagram-AJAX': '1',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest'
        })

        r = self.request.get(self.url)
        self.request.headers.update({'X-CSRFToken': r.cookies['csrftoken']})
        time.sleep(5 * random.random())

    def request_login(self):
        self.user_id = None
        login = self.request.post(
            self.url_login, data=self.login_post, allow_redirects=True)
        self.request.headers.update({'X-CSRFToken': login.cookies['csrftoken']})
        self.csrftoken = login.cookies['csrftoken']
        # ig_vw=1536; ig_pr=1.25; ig_vh=772;  ig_or=landscape-primary;
        self.request.cookies['ig_vw'] = '1536'
        self.request.cookies['ig_pr'] = '1.25'
        self.request.cookies['ig_vh'] = '772'
        self.request.cookies['ig_or'] = 'landscape-primary'
        time.sleep(5 * random.random())

        if login.status_code == 200:
            r = self.request.get('https://www.instagram.com/')
            finder = r.text.find(self.user_login)
            if finder != -1:
                self.ui = UserInfo(self.request)
                self.user_id = self.ui.get_user_id_by_login(self.user_login)
                print ("user_id",str(self.user_id))
                self.login_status = True
                log_string = '%s login success!' % (self.user_login)
                print(log_string)
            else:
                self.login_status = False
                print('Login error! Check your login data!')
        else:
            print('Login error! Connection error!')


