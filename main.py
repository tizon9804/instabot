import folous.generator as folous
import Instagram.InstagramAPI as instargramApi
import persistencemanager.mysql as mysql

config = {
        "username": "",
        "password": ""
    }

mysql_config = {
    "hostname": "candylero.com",
    "username": "candyrem",
    "password": "",
    "database": "laikeo",
};

class Instabot:

    def __init__(self):
        print("Init Instabot")
        self.instagram_pi = instargramApi.InstagramAPI(config['username'],config['password'])
        print("Init mysql")
        self.mysql_instance = mysql.Connector(mysql_config)
        print("Init flous")
        self.folous = folous.Controller(self.instagram_pi, self.mysql_instance)
        #self.account = login.Login(self.request, self.user_agent, config)
        #self.account.get_info_user_by_id(self.account.user_id)

    def login_api(self):
        self.instagram_pi.login()
        time_interval_procces = 5
        self.folous.run(time_interval_procces)

instabot = Instabot()
instabot.login_api()
