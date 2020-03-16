import persistencemanager.mysql as mysql
from Instagram.user_info import UserInfo
import requests
from http_request_randomizer.requests.proxy.requestProxy import RequestProxy
import time
import laikeo.generator as generator

class Compare:

    def __init__(self, mysql_instance, instragram_api, share):
        self.share = share #type: generator.Share
        self.instagram_api = instragram_api  # type: instagram_pi.InstagramAPI
        self.mysql_instance = mysql_instance # type: mysql.Connector
        self.proxy_request = RequestProxy()
        self.request = requests
        self.is_running_follower = False
        self.is_running_following = False
        self.is_running_followings_bd_update = False
        self.is_running_followers_bd_update = False

    def compare(self):
        self.followers_comparator()
        self.followings_comparator()
        self.get_followings_bd()
        self.get_followers_bd()
    # actualiza el listado de followings para la clase Share en Generator, y asi las estrategias pueden usar los datos sin tener que consultar mysql
    def get_followings_bd(self):
        if not self.is_running_followings_bd_update:
            self.is_running_followings_bd_update = True
        try:
            list = self.mysql_instance.get_followings()
            for e in list:
                object = {"user_id": e[0],"unfollow_date":e[1]}
                self.share.following_bd[e[0]] = object
            print "followings_bd updated"
        except Exception as ex:
            print str(ex)
        finally:
            self.is_running_followings_bd_update= False
    # actualiza el listado de followings para la clase Share en Generator, y asi las estrategias pueden usar los datos sin tener que consultar mysql
    def get_followers_bd(self):
        if not self.is_running_followers_bd_update:
            self.is_running_followers_bd_update = True
        try:
            list = self.mysql_instance.get_followers()
            for e in list:
                object = {"user_id": e[0],"unfollow_date":e[1]}
                self.share.followers_bd[e[0]] = object
            print "followers_bd updated"
        except Exception as ex:
            print str(ex)
        finally:
            self.is_running_followers_bd_update= False


    def followers_comparator(self):
        if not self.is_running_follower:
            self.is_running_follower = True
            try:
                print ("running follower comparator")
                self.follow_comparator(self.mysql_instance.get_followers,
                                       self.instagram_api.getTotalSelfFollowers,
                                       self.mysql_instance.save_followers,
                                       self.mysql_instance.active_followers)
                self.is_running_follower = False
            except Exception as ex:
                print ("----##$$ error followers comparator ", str(ex))
                self.mysql_instance.reconnect()
                self.is_running_follower = False


    def followings_comparator(self):
        if not self.is_running_following:
            self.is_running_following = True
            try:
                print ("running follower comparator")
                self.follow_comparator(self.mysql_instance.get_followings,
                                       self.instagram_api.getTotalSelfFollowings,
                                       self.mysql_instance.save_followings,
                                       self.mysql_instance.active_followings)
                self.is_running_following = False
            except Exception as ex:
                print ("----##$$ error folowings comparator", str(ex))
                self.mysql_instance.reconnect()
                self.is_running_following = False


    def follow_comparator(self,get_follow, get_instagram_follows, save_follow, active_update_follow):
        #print "get follow"
        list = get_follow()
        #print "get dic follow"
        follows = self.get_dict_follow(list)
        #print "get instagram follow"
        instagram_follows = get_instagram_follows()
        #print "persistence_follows"
        self.persistence_follows(instagram_follows,follows,save_follow,active_update_follow)
        #print "inactive follows"
        self.inactive_follows(follows,active_update_follow)

    def persistence_follows(self,instagram_follows, follows,save_follow,active_update_follow):
        follows_mysql = []
        for inst_follow in instagram_follows:
            id = inst_follow["pk"]
            if str(id) in follows:
                follows[str(id)]["exist"] = True
                if follows[str(id)]["date"]:
                    print "Esta en follows pero se registro un unfollow"
                    update = active_update_follow([follows[str(id)]], True)
                    print "users activated: " + str(update)
                if False:
                    inst_follow["following_count"], inst_follow["follower_count"], inst_follow[
                        "post_count"] = self.get_info_user_by_id(id)
                    time.sleep(20)
                    if inst_follow["following_count"] > 0 or inst_follow["follower_count"] > 0:
                        follows_mysql.append(inst_follow)
                    if len(follows_mysql) > 10:
                        save_follow(follows_mysql)
                        follows_mysql = []
            else:
                inst_follow["following_count"], inst_follow["follower_count"], inst_follow[
                    "post_count"] = self.get_info_user_by_id(id)
                print(str(id), "#", str(inst_follow["following_count"]), "#", str(inst_follow["follower_count"]), "#",
                      str(inst_follow["post_count"]))
                if inst_follow["following_count"] > 0 or inst_follow["follower_count"] > 0:
                    follows_mysql.append(inst_follow)
                if len(follows_mysql) > 10:
                    save_follow(follows_mysql)
                    follows_mysql = []
        save_follow(follows_mysql)

    def inactive_follows(self,follows, active_update_follow):
        update_batch = []
        for follow in follows:
            if "exist" not in follows[follow] and not follows[follow]["date"]:
                update_batch.append(follows[follow])
            if len(update_batch) > 10:
                update = active_update_follow(update_batch,False)
                print "users inactivated: " +str(update)
                update_batch = []
        update = active_update_follow(update_batch,False)
        print "users inactivated: " + str(update)
        update_batch = []

    def get_dict_follow(self,list):
        follows = {}
        try:
            for f in list:
                id = f[0]
                date = f[1]
                follows[str(id)] = {"user_instagram_id": id, "date": date}
        except Exception as ex:
            print str(ex)
        finally:
            return follows

    def persistence_followings(self, followings):
        followings_mysql = []
        for following in followings:
            id = following["pk"]
            following["following_count"], following["follower_count"], following[
                "post_count"] = self.get_info_user_by_id(id)
            print(str(id), "#", str(following["following_count"]), "#", str(following["follower_count"]), "#",
                  str(following["post_count"]))
            if following["following_count"] > 0 and following["follower_count"] > 0:
                followings_mysql.append(following)
            if len(followings_mysql) > 10:
                self.mysql_instance.save_followings(followings_mysql)
                followings_mysql = []
        self.mysql_instance.save_followings(followings_mysql)

    def persistence_followers(self, followers):
        followers_mysql = []
        for follower in followers:
            id = follower["pk"]
            follower["following_count"], follower["follower_count"], follower[
                "post_count"] = self.get_info_user_by_id(id)
            print(str(id), "#", str(follower["following_count"]), "#", str(follower["follower_count"]), "#",
                  str(follower["post_count"]))
            followers_mysql.append(follower)
            if len(followers_mysql) > 10:
                self.mysql_instance.save_followers(followers_mysql)
                followers_mysql = []
        self.mysql_instance.save_followers(followers_mysql)

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


