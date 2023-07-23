import asyncio
import json
import datetime
import threading
from time import timezone
from kademlia.network import Server
import sync as sync
from itertools import groupby

class KServer:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.main_loop = None
        self.timeline_posts = []
        self.timestamp_id = sync.generate_timestamp_id(self.port)
        self.logged_user=None
        

    def init_server(self):

        self.main_loop = asyncio.new_event_loop()

        self.server = Server()
        self.main_loop.run_until_complete(self.server.listen(self.port))
        self.main_loop.run_until_complete(self.server.bootstrap([("127.0.0.1", 7001), ("127.0.0.1", 7002), ("127.0.0.1", 7003)]))
        if self.port == 7003: 
            self.main_loop.run_until_complete(self.server.set("user_list", json.dumps({"user_list" : []})))
        
        try:
            self.main_loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.server.stop()

    def shutdown_hook(self):
        self.user_info["is_online"] = False
        future = asyncio.run_coroutine_threadsafe(self.server.set(self.logged_user, json.dumps(self.user_info)), self.main_loop)
        var = future.result()

    async def bootpeer_check_online_peers(self):
        user_list = await self.server.get("user_list")
        user_list = json.loads(user_list)["user_list"]
        for peer in user_list:
            user_info = await self.server.get(peer)
            user_info = json.loads(user_info)
            await self.check_online_status(peer, user_info)
        return True

    def run_listener(self):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.init_listener())

    async def init_listener(self):
        self.listener_server = await asyncio.start_server(self.process_listen, self.ip, self.port)
        await self.listener_server.serve_forever()    

    async def process_listen(self, readsocket, writesocket):
        raw_data = await readsocket.readline()
        message = json.loads(raw_data.decode())
        
        if message["type"] == "post":
            timeline_dic = {"message": message["message"], "timestamp": message["timestamp"], "user": message["user"]}
            self.timeline_posts.append(timeline_dic)
        elif message["type"] == "follow":
            value = await self.server.get(self.logged_user)
            self.user_info = json.loads(value)
        writesocket.close()
        await writesocket.wait_closed()

    async def register(self):
        username = input("Username: ")
        while "@" in username:
            username = input("Can't have '@' in username. Enter username: ")
        value = await self.server.get(username)
        if value != None:
            print("Username already taken.")
            return 1
        else:
            value_aux = { "followers": [], "following": [], "is_online" : True, "ip": self.ip, "port": self.port} 
            await self.server.set(username+"@gc_dict", json.dumps({"timestamps": [], "seen" : []}))
            user_list = await self.server.get("user_list")
            user_list = json.loads(user_list)["user_list"]
            user_list.append(username)
            await self.server.set("user_list", json.dumps({"user_list" : user_list}))
            await self.server.set(username + "@posts", json.dumps({"posts" : []}))
            self.logged_user = username
            self.user_info = value_aux
            await self.server.set(username, json.dumps(value_aux))
            print("\n - Registered Successfully - Welcome "+ username )
            threading.Thread(target=self.run_listener, daemon=True).start()
            #input("Press Enter to continue...")
            return 0
    
    async def login(self):
        username = input("Username: ")
        value = await self.server.get(username)
        if value is None:
            print("This user was not found. Check your credentials or register a new user.")
            return 1
        else: 
            value_dic = json.loads(value)
            value_dic["is_online"] = True
            self.logged_user = username
            self.user_info = value_dic
            await self.server.set(username, json.dumps(value_dic))
            await self.get_feed()
            print("\n - Logged In Successfully - Welcome back "+ username )
            threading.Thread(target=self.run_listener, daemon=True).start()
            #input("Press Enter to continue...")
            return 0
    
    async def logout(self):
        print("\n - Logged Out Successfully - Bye " + self.logged_user)
        #input("Press Enter to continue...")
        return 0
    
    async def follow(self):
        user_to_follow = input("\n - Enter the username you want to follow: ")
        value_aux = await self.server.get(user_to_follow)
        if user_to_follow != self.logged_user:
            if value_aux is None:
                print("\n - User doesn't exist.")
                #input("Press Enter to continue...")
                return 1
            else:
                if user_to_follow in self.user_info["following"]:
                    print("\n - This user is already being followed!")
                    #input("Press Enter to continue...")
                    return 1
                self.user_info["following"].append(user_to_follow)
                value = json.loads(value_aux)
                value["followers"].append(self.logged_user)
                message_dict = {"type": "follow", "user": self.logged_user}
                await self.server.set(self.logged_user, json.dumps(self.user_info))
                await self.server.set(user_to_follow, json.dumps(value))
                threading.Thread(target=await self.write_if_online(user_to_follow, value, json.dumps(message_dict).encode()), daemon=True).start()
                user_to_follow_posts = await self.server.get(user_to_follow+"@posts")
                user_to_follow_posts = json.loads(user_to_follow_posts)
                #print(user_to_follow_posts["posts"])
                for post in user_to_follow_posts["posts"]:
                    post["user"] = user_to_follow
                    self.timeline_posts.append(post)
                print("\n - "+self.logged_user + " is now following " + user_to_follow+".")
                #input("Press Enter to continue...")
                return 0
        else:
            print("\n - You can't follow yourself.")
            #input("Press Enter to continue...")
            return 1
        
    async def unfollow(self):
        user_to_unfollow = input("\n - Enter the username you want to unfollow: ")
        value_aux = await self.server.get(user_to_unfollow)

        if user_to_unfollow != self.logged_user:
            if value_aux is None:
                print("\n - This username doesn't exist.")
                #input("Press Enter to continue...")
                return 1
            else:
                if user_to_unfollow not in self.user_info["following"]:
                    print("\n - This user is not being followed.")
                    #input("Press Enter to continue...")
                    return 1
                self.user_info["following"].remove(user_to_unfollow)
                value = json.loads(value_aux)
                value["followers"].remove(self.logged_user)
                message_dict = {"type" : "follow", "user" : self.logged_user}
                await self.server.set(self.logged_user, json.dumps(self.user_info))
                await self.server.set(user_to_unfollow, json.dumps(value))
                threading.Thread(target=await self.write_if_online(user_to_unfollow, value, json.dumps(message_dict).encode()), daemon=True).start()

                print("\n - "+ self.logged_user + " unfollowed " + user_to_unfollow)
                return 0
        else:
            print("\n - You Can't follow yourself.")
            #input("Press Enter to continue...")
            return 1

    def add_user_to_post(self, user, dic):
        dic["user"] = user
        return dic

    async def get_feed(self):
        for user in self.user_info["following"]:
            posts = await self.server.get(user+"@posts")
            posts = json.loads(posts)
            self.timeline_posts += [self.add_user_to_post(user, x) for x in posts["posts"]]
    
    def key_func(self, k):
        return k["user"]
    
    async def update_seen(self):
        for user, posts in groupby(self.timeline_posts, key=self.key_func):
            user_gc_dict = await self.server.get(user+"@gc_dict")
            user_gc_dict = json.loads(user_gc_dict)
            for post in list(posts):
                if post["timestamp"] in user_gc_dict["timestamps"]: 
                    msg_index = user_gc_dict["timestamps"].index(post["timestamp"])
                    seen_list = user_gc_dict["seen"][msg_index]
                    if self.logged_user not in seen_list: 
                        seen_list.append(self.logged_user)
                        user_gc_dict["seen"][msg_index] = seen_list
            await self.server.set(user+"@gc_dict", json.dumps(user_gc_dict))
            

    async def show_feed(self):
        print("\n Your feed: \n")
        if(len(self.timeline_posts) == 0):
            print("No new posts found!")
            #input("Press Enter to continue...")
        else:
            await self.update_seen()
            sorted_timeline = sorted(self.timeline_posts, key=lambda x: x["timestamp"], reverse=True)
            self.timeline_posts = []
            for timeline_dic in sorted_timeline:
                timestamp=sync.generate_datetime(timeline_dic["timestamp"])
                print(" - Received message: \n'" + timeline_dic["message"] + "'\nTimestamp: " + timestamp.strftime("%A, %B %d, %Y %H:%M:%S") + "\nFrom user: " + timeline_dic["user"] + "\n")
            #input("Press Enter to continue...")
            

    async def garbage_collect(self):
        userlist = await self.server.get("user_list")
        userlist = json.loads(userlist)["user_list"]
        for user in userlist:
            timestamps_to_delete = []
            ordered_for_deletion = []
            seen_info = await self.server.get(user+"@gc_dict")
            seen_info = json.loads(seen_info)
            user_info = await self.server.get(user)
            user_info = json.loads(user_info)
            for i in range(len(seen_info["seen"])):
                follower_set = set(user_info["followers"])
                seen_set = set(seen_info["seen"][i])
                if follower_set.issubset(seen_set):
                    timestamps_to_delete.append(seen_info["timestamps"][i])
                else:
                    ordered_for_deletion.append({"timestamp": seen_info["timestamps"][i], "seen_by": len(follower_set.intersection(seen_set))/len(follower_set)})
            post_num = len(seen_info["timestamps"]) - len(timestamps_to_delete)
            if post_num > 10:
                number_to_del = (post_num - 10) + 4
                ordered_for_deletion.sort(key = lambda x : (-1*x["seen_by"], sync.generate_datetime(x["timestamp"])))
                for dic in ordered_for_deletion[:number_to_del]:
                    timestamps_to_delete.append(dic["timestamp"])
            if len(timestamps_to_delete) > 0:
                user_posts = await self.server.get(user+"@posts")
                user_posts = json.loads(user_posts)
                user_posts = user_posts["posts"]
                #print(timestamps_to_delete)
                #print(user_posts)
                new_user_posts = list(filter((lambda x : x["timestamp"] not in timestamps_to_delete), user_posts))
                #print("New posts for user " + user)
                #print(new_user_posts)
                for timestamp in timestamps_to_delete:
                    index_to_del = seen_info["timestamps"].index(timestamp)
                    del seen_info["timestamps"][index_to_del]
                    del seen_info["seen"][index_to_del]
                    #print("New seen info for user " + user)
                    #print(seen_info)
                await self.server.set(user+"@posts", json.dumps({"posts": new_user_posts}))
                await self.server.set(user+"@gc_dict", json.dumps(seen_info))


    async def see_follows(self):
        if(len(self.user_info["following"])==0):
            print("Not following anyone")
        else:
            print("\n - Following: \n")
            for u in self.user_info["following"]:
                print(u)
        if(len(self.user_info["followers"])==0):
            print("No followers yet")
        else:
            print("\n - Followers: \n")
            for u in self.user_info["followers"]:
                print(u)
        #input("Press Enter to continue...")

    async def create_new_post(self):
        post = input("\n - Insert new post: ")
        
        while(len(post) > 100):
            post = input("Max characters exceeded. Insert new post: ")
        
        timestamp_id = self.timestamp_id.__next__()

        post_dict = {"message" : post, "timestamp" : timestamp_id}
        user_posts = await self.server.get(self.logged_user+"@posts")
        user_posts = json.loads(user_posts)
        user_posts["posts"].append(post_dict)
        user_gc_dict = await self.server.get(self.logged_user+"@gc_dict")
        user_gc_dict = json.loads(user_gc_dict)
        user_gc_dict["timestamps"].append(timestamp_id)
        user_gc_dict["seen"].append([])
        await self.server.set(self.logged_user+"@gc_dict", json.dumps(user_gc_dict))
        await self.server.set(self.logged_user+"@posts", json.dumps(user_posts))

        post_dict.update({"type": "post", "user": self.logged_user})
        threading.Thread(target=await self.send_post(post_dict), daemon=True).start()
        #input("Press Enter to continue...")


    async def send_post(self, post_dict):
        for user in self.user_info["followers"]:
            follower_info = await self.server.get(user)
            follower_info = json.loads(follower_info)
            if follower_info["is_online"]:
                threading.Thread(target=await self.write_if_online(user, follower_info, json.dumps(post_dict).encode()), daemon=True).start()


    async def write_if_online(self, username, userinfo, msgbytes):
        if userinfo["is_online"]:
            socket = await self.check_online_status(username, userinfo)
            if socket != None:
                await self.socket_write_message(socket[1], msgbytes)


    async def check_online_status(self, username, userinfo):
        socket = await self.check_connection(userinfo["ip"], userinfo["port"])
        if socket == None: is_online = False
        else: is_online = True
        retval = await self.change_online_status(userinfo, is_online)
        if retval: 
            await self.server.set(username, json.dumps(userinfo))
            print(username + " changed status")
        return socket


    async def check_connection(self, ip, port):
        try:
            socket = await asyncio.open_connection(ip, port)
            return socket
        except ConnectionRefusedError:
            return None


    async def change_online_status(self, userinfo, is_online):
        if userinfo["is_online"] != is_online:
            userinfo["is_online"] = is_online
            return True
        return False

    async def socket_write_message(self, writesocket, msgbytes):
        writesocket.write(msgbytes)
        await writesocket.drain()
        await self.close_write_socket(writesocket)


    async def close_write_socket(self, writesocket):
        writesocket.close()
        await writesocket.wait_closed()
        