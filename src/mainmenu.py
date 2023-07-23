import asyncio
import os

class LoggedOut(Exception): pass

class Menu:
    def __init__(self, server):
        self.first_menu = True
        self.server = server

    def print_menu_ini(self):
        print("\n________________ Twitter @ FEUP ________________ ")
        print("\n")
        print("                 [0] Register")
        print("                 [1] Login")
        print("________________________________________________ \n")

    def print_menu_autenticado(self):
        print("\n________________ Twitter @ FEUP ________________ ")
        print("\nLogged In: "+ self.server.logged_user +"\n")
        print("                [0] Feed")
        print("                [1] Follow user")
        print("                [2] Unfollow user")
        print("                [3] Create new post")
        print("                [4] See Following and Followers")
        print("                [5] Logout")
        print("________________________________________________ \n")

# https://www.pythonpool.com/python-check-if-string-is-integer/
    def read_menu_option(self):
        aux = input("Option -> ")
        try:
            if (self.first_menu and (int(aux) not in range(0,3))) or (not self.first_menu and (int(aux) not in range(0,6))):
                print("Option not available.")
            else:
                self.option = int(aux)
                self.handle_option()
        except ValueError:
            print("Option must be an integer!")

    def handle_option(self):
        if self.first_menu == True: #login_menu
            if self.option == 0:
                self.execute_option(self.server.register(), self.server.main_loop)
            elif self.option == 1:
                self.execute_option(self.server.login(), self.server.main_loop)
            input("Press Enter to continue...")
        else:   #authenticated user menu
            if self.option == 0:
                self.execute_option(self.server.show_feed(), self.server.main_loop)
            elif self.option == 1:
                self.execute_option(self.server.follow(), self.server.main_loop)
            elif self.option == 2:
                self.execute_option(self.server.unfollow(), self.server.main_loop)
            elif self.option == 3:
                self.execute_option(self.server.create_new_post(), self.server.main_loop)
            elif self.option == 4:
                self.execute_option(self.server.see_follows(), self.server.main_loop)
            elif self.option == 5:
                #self.execute_option(self.server.logout(), self.server.main_loop)
                raise LoggedOut
            input("Press Enter to continue...")
    

    def execute_option(self, function, loop):
        future = asyncio.run_coroutine_threadsafe(function, loop)
        retval = future.result()
        if (retval == 0) and self.first_menu:
            self.first_menu = False
  

    def run_menu(self):
        try:
            while(True):
                if self.first_menu == True:
                    os.system('cls' if os.name == 'nt' else 'clear')
                    self.print_menu_ini()
                    self.read_menu_option()
                else:
                    os.system('cls' if os.name == 'nt' else 'clear')
                    self.print_menu_autenticado()
                    self.read_menu_option()
        except KeyboardInterrupt:
            raise LoggedOut
            