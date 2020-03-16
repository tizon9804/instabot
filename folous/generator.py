import Instagram.InstagramAPI as instagram_pi
import threading
import time
import laikeo.comparator as comparator
import persistencemanager.mysql as mysql
import requests
from http_request_randomizer.requests.proxy.requestProxy import RequestProxy
import copy
from Instagram.user_info import UserInfo

class Shared:
    def __init__(self):
        self.following_bd = {}
        self.followers_bd = {}

class Controller:

    def __init__(self, instragram_api, mysql_instance):
        self.instagram_api = instragram_api # type: instagram_pi.InstagramAPI
        self.max_follow_per_user = 20000
        self.interval = None
        self.is_running_strategy = False
        self.is_running_unfollow_strategy = False
        self.break_follow_seconds = 10
        self.followings = {}
        self.mysql_instance = mysql_instance # type:  mysql.Connector
        self.request = requests
        self.proxy_request = RequestProxy()
        self.share = Shared()
        self.comparator = comparator.Compare(self.mysql_instance,self.instagram_api,self.share)

    def run(self, seconds):
        # start the flow data each seconds
        if not self.interval:
            self.interval = self.set_interval(self.unfollow_strategy, seconds)
            self.interval = self.set_interval(self.follow_strategy, seconds)
            self.interval_followers_comparator = self.set_interval(self.comparator.compare,10)
        else:
            # restart the interval to change the interval timer
            print ("restarting...")
            self.interval.cancel()
            self.interval = None
            self.run(seconds)

    def unfollow_strategy(self):
        if not self.is_running_unfollow_strategy:
            self.is_running_unfollow_strategy = True
            try:
                following_bd = copy.copy(self.share.following_bd)
                sum_followers_in_followings = 0
                for i,id in enumerate(following_bd):
                    try:
                        user = following_bd[id]
                        if not user["unfollow_date"]:
                            total_following, total_followers, posts = self.get_info_user_by_id(id)
                            if total_following == 0 and total_followers == 0 and posts == 0:
                                count_followers_in_followings = 0
                                print "Regla influencer"
                                if total_followers/float(total_following) > 0.9:
                                    print "UNFOLLOW--- " + str(total_followers/float(total_following)) + " ## " + str(id)
                                    self.instagram_api.unfollow(id)
                                print "Regla ExFollower"
                                if id in self.share.followers_bd:
                                    if self.share.followers_bd[id]["unfollow_date"]:
                                        print "UNFOLLOW ex follower"
                                        self.instagram_api.unfollow(id)
                                followers = self.instagram_api.getTotalFollowers(id)
                                print (str(id), " cantidad de followers: ", str(len(followers)))
                                for follower in followers:
                                    fw_id = follower["pk"]
                                    fw_username = follower["username"]
                                    if fw_id in following_bd:
                                        print "El following: " + str(id) + " tiene un follower: " + str(
                                            fw_username) + " que ya esta o estuvo en followings candylero"
                                        count_followers_in_followings += 1
                                print "Regla del 50% unfollow: " + str(
                                    count_followers_in_followings / float(total_followers))
                                if count_followers_in_followings / float(total_followers) >= 0.5:
                                    print "UNFOLLOW---## " + str(id)
                                    self.instagram_api.unfollow(id)
                    except Exception as ex:
                        if str(ex) == "users":
                            print "pause for 1 minute"
                            time.sleep(60)
                        print str(ex)
                if following_bd:
                    promedio = sum_followers_in_followings / len(following_bd)
                    print "el promedio de porcentaje extraido de los followings es: " + str(promedio)
            except Exception as ex:
                print str(ex)
            finally:
                self.is_running_unfollow_strategy = False

    def validate_follow_strategy(self):
        validation = self.total_followers/float(self.total_following) > 0.9
        print "continue following: " + str(validation)
        return validation

    def follow_strategy(self):
        if not self.is_running_strategy:
            self.is_running_strategy = True
            try:
                print ("running strategy")
                self.total_following, self.total_followers, posts = self.get_info_user_by_id(self.instagram_api.username_id)
                print "my rate followers/followings: " + str(self.total_followers/float(self.total_following))
                if self.validate_follow_strategy() :
                    self.own_following_strategy()
                    #self.own_followers_strategy()
                else:
                    print "hay mas followings que followers ############################## Pausado following strategy"
            except Exception as ex:
                print ("----##$$ error folous ", str(ex))
                self.instagram_api.logout()
                self.instagram_api.login()
                time.sleep(60)
                self.is_running_strategy = False
            finally:
                time.sleep(60)
                self.is_running_strategy = False

    def own_following_strategy(self):
        if not self.followings:
            self.followings = self.instagram_api.getTotalSelfFollowings()
        print ("mis followings: ", len(self.followings))
        for following in self.followings:
            fw_id = following["pk"]
            fw_username = following["username"]
            print (fw_username, " user_following follow his friends")
            self.follow_friends_followers_strategy(fw_id,fw_username)
            if not self.validate_follow_strategy():
                break

    def own_followers_strategy(self):
        followers = self.instagram_api.getTotalSelfFollowers()
        print ("mis followers: ", str(len(followers)))
        for follower in followers:
            fw_id = follower["pk"]
            fw_username = follower["username"]
            is_following = self.am_i_following(fw_id)
            print ("$$$$$", fw_username, "following ", is_following)
            if follower["is_private"] and not is_following:
                print("La cuenta es privada y no lo estoy siguiendo")
                print ("###### Follow private")
                print (self.instagram_api.follow(fw_id))
                time.sleep(self.break_follow_seconds)
            if not follower['is_private']:
                print ("puedo buscar sus amigos")
                self.follow_friends_followers_strategy(fw_id, fw_username)

    def mercadoni_strategy(self):
        self.instagram_api.searchUsername("mercadoni_co")
        user = self.instagram_api.LastJson
        mercadoni_id = user["user"]["pk"]
        mercadoni_username = user["user"]["username"]
        print("amigos de mercadoni")
        self.follow_friends_followers_strategy(mercadoni_id, mercadoni_username)

    def follow_friends_followers_strategy(self, user_id, name):
        followers = self.instagram_api.getTotalFollowers(user_id)
        count_follows = 0
        print (name," cantidad de followers: ", str(len(followers)))
        for follower in followers:
            try:
                fw_id = follower["pk"]
                fw_username = follower["username"]
                is_following_me = self.is_following_me(fw_id)
                is_pending_request = self.is_in_pending_request(fw_id)
                am_i_following = self.am_i_following(fw_id)
                if not is_following_me and not is_pending_request and not am_i_following:

                    print ("no me esta siguiendo, no tiene un pending request mio y no lo estoy siguiendo")
                    print ("###### Follow friend of friend ", fw_username)
                    print (self.instagram_api.follow(fw_id))
                    self.total_following += 1
                    count_follows +=1
                    time.sleep(self.break_follow_seconds)
                    if not self.validate_follow_strategy():
                        break
                else:
                    print ("no es apto para follow: ", fw_username)
                    print ("is_following_me: ", is_following_me)
                    print ("is_pending_request: ", is_pending_request)
                    print ("am_i_following: ", am_i_following)
                if count_follows >= self.max_follow_per_user:
                    print ("----------------------------------------------------", name," max follows ", count_follows)
                    break
            except Exception as ex:
                print "error in a follower of a friend: " + str(ex)

    def am_i_following(self, user_id):
        if self.share.following_bd:
            if user_id in self.share.following_bd:
                return True
        else:
            followings = self.instagram_api.getTotalSelfFollowings()
            for following in followings:
                fw_id = following["pk"]
                if fw_id == user_id:
                    return True
        return False

    def is_following_me(self, user_id):
        followers = self.instagram_api.getTotalSelfFollowers()
        for follower in followers:
            fw_id = follower["pk"]
            if fw_id == user_id:
                return True
        return False

    def get_info_user_by_id(self, user_id, level=1):
        try:
            self.ui = UserInfo(self.request, self.proxy_request)
            user = self.ui.get_info_user_by_id(user_id)
            if user:
                following_count = user["following_count"]
                follower_count = user["follower_count"]
                media_count = user["media_count"]
                time.sleep(5)
                return [following_count, follower_count, media_count]
            else:
                time.sleep(60)
                return [0, 0, 0]
        except Exception as ex:
            print("error", str(ex))
            if level <= 5:
                print ("Trying again")
                return self.get_info_user_by_id(user_id, level + 1)
        return [0, 0, 0]

    def is_in_pending_request(self, user_id):
        return False
        #pendings = self.instagram_api.getPendingFollowRequests()
        #for penders in pendings:
        #    p_id = penders["pk"]
        #    if p_id == user_id:
        #        return True
        #return False

    def set_interval(self, func, sec):
        # each interval run in a different thread
        def func_wrapper():
            self.set_interval(func, sec)
            func()

        t = threading.Timer(sec, func_wrapper)
        t.start()
        return t







