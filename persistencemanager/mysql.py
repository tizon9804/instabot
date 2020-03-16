import pymysql

class Connector:
    def __init__(self, config):
        self.host = config['hostname']
        self.user = config['username']
        self.password = config['password']
        self.db = config['database']
        self.connection = None

    def reconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None
        self.connect()

    def connect(self):
        i = 1
        while not self.connection:
            try:
                print("Connect Mysql " + str(i))
                self.connection = pymysql.connect(host=self.host, user=self.user, passwd=self.password, db=self.db)
                print("Connected!")
                cursor = self.connection.cursor()
                cursor.execute('SET autocommit = 0;')
            except Exception as e:
                print("Error mysql connection " + str(e))
                i += 1
            if i > 10:
                break

    def close(self):
        self.connection.close()
        self.connection = None

    def execute_query(self, command):
        self.connect()
        cursor = self.connection.cursor()
        cursor.execute(command)
        self.connection.commit()

    def execute_query_fetchall(self, command):
        self.connect()
        cursor = self.connection.cursor()
        cursor.execute(command)
        return cursor.fetchall()

    def execute_query_insert(self, command):
        self.connect()
        cursor = self.connection.cursor()
        cursor.execute(command)
        self.connection.commit()
        return cursor.lastrowid

    def execute_query_update(self, command):
        self.connect()
        cursor = self.connection.cursor()
        cursor.execute(command)
        self.connection.commit()
        return cursor.rowcount

    def get_followers(self):
        sql_command = """
        SELECT user_instagram_id,unfollow_us_date
        FROM follower
        """
        return self.execute_query_fetchall(sql_command)

    def get_followings(self):
        sql_command = """
        SELECT user_instagram_id, unfollow_date
        FROM following
        """
        return self.execute_query_fetchall(sql_command)

    def active_followers(self,followers,active):
        if (len(followers) == 0):
            return 0
        date = "now()"
        if active:
            date = "null"
        temporal = """ CREATE TEMPORARY TABLE IF NOT EXISTS update_table (
                            user_instagram_id BIGINT(20) not null
                          ); """

        drop_temporal = """ drop table update_table; """
        insert = """ INSERT INTO update_table (user_instagram_id) VALUES """
        inputs = ""
        for follower in followers:
            values = """({user_instagram_id}),
                 """
            inputs += values.format(user_instagram_id=follower['user_instagram_id'])

        update = """
                    UPDATE follower
                    INNER JOIN update_table
                    ON follower.user_instagram_id = update_table.user_instagram_id
                    SET follower.unfollow_us_date =
                """
        update += date + ";"
        inputs = str(inputs).strip()[:-1]
        inserts = insert + inputs + ";"
        print("creating temporal table")
        self.execute_query(temporal)
        print("inserting data in temporal")
        self.execute_query(inserts)
        print("updating follower from temporal")
        updated_count = self.execute_query_update(update)
        print("drop temporal table")
        self.execute_query(drop_temporal)
        return updated_count

    def active_followings(self,followings,active):
        if (len(followings) == 0):
            return 0
        date = "now()"
        if active:
            date = "null"
        temporal = """ CREATE TEMPORARY TABLE IF NOT EXISTS update_table (
                            user_instagram_id BIGINT(20) not null
                          ); """

        drop_temporal = """ drop table update_table; """
        insert = """ INSERT INTO update_table (user_instagram_id) VALUES """
        inputs = ""
        for following in followings:
            values = """({user_instagram_id}),
                 """
            inputs += values.format(user_instagram_id=following['user_instagram_id'])

        update = """
                    UPDATE following
                    INNER JOIN update_table
                    ON following.user_instagram_id = update_table.user_instagram_id
                    SET following.unfollow_date =
                """
        update += date + ";"
        inputs = str(inputs).strip()[:-1]
        inserts = insert + inputs + ";"
        print("creating temporal table")
        self.execute_query(temporal)
        print("inserting data in temporal")
        self.execute_query(inserts)
        print("updating following from temporal")
        updated_count = self.execute_query_update(update)
        print("drop temporal table")
        self.execute_query(drop_temporal)
        return updated_count

    def save_followings(self, followings):
        if (len(followings) == 0):
            return 0
        print("inserting followings")
        insert = """INSERT INTO following
                (user_instagram_id,user_name,user_count_followers,user_count_following,user_count_posts,creation_date,unfollow_date)
                VALUES """
        inputs = ""
        for user in followings:
            values = """("{user_instagram_id}","{user_name}","{user_count_followers}",
                   "{user_count_following}","{user_count_posts}",now(),null),
                   """
            inputs += values.format(user_instagram_id=user["pk"],
                                    user_name=user["username"],
                                    user_count_followers=user["follower_count"],
                                    user_count_following=user["following_count"],
                                    user_count_posts=user["post_count"])

        update = """ ON DUPLICATE KEY UPDATE user_count_followers = VALUES(user_count_followers),
                                             user_count_following = VALUES(user_count_following),
                                             user_count_posts = VALUES(user_count_posts)
                 """
        inputs = str(inputs).strip()[:-1]
        sql_command = insert + inputs + update + ";"
        self.execute_query_insert(sql_command)

    def save_followers(self,followers):
        if(len(followers)== 0):
            return 0
        print("inserting follower")
        insert = """INSERT INTO follower
                        (user_instagram_id,user_name,user_count_followers,
                        user_count_following,user_count_posts,creation_date,unfollow_us_date)
                        VALUES """
        inputs = ""
        for user in followers:
            values = """("{user_instagram_id}","{user_name}","{user_count_followers}",
                           "{user_count_following}","{user_count_posts}",now(),null),
                           """
            inputs += values.format(user_instagram_id=user["pk"],
                                    user_name=user["username"],
                                    user_count_followers=user["follower_count"],
                                    user_count_following=user["following_count"],
                                    user_count_posts=user["post_count"])
        update = """ ON DUPLICATE KEY UPDATE user_count_followers = VALUES(user_count_followers),
                                                     user_count_following = VALUES(user_count_following),
                                                     user_count_posts = VALUES(user_count_posts)
                         """
        inputs = str(inputs).strip()[:-1]
        sql_command = insert + inputs + update + ";"
        self.execute_query_insert(sql_command)