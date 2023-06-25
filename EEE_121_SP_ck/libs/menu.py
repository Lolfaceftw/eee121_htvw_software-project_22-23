import npyscreen
import curses
from libs.chatform import ChatForm
from libs.chatform import ChatInput

class Menu(npyscreen.FormWithMenus):
    def create(self):
        self.x, self.y = self.useable_space()
        self.menu = self.add_menu("Main Menu")
        self.menu.addItemsFromList([
            ("Chat Now!", self.startchat),
            ("Set Nickname", self.setnick),
            ("Exit :(", self.exitNow)
        ])

    def startchat(self):
        self.parentApp.change_form("CHAT")


    def setnick(self):
        curses.beep()

    def exitNow(self):
        curses.beep()
        self.parentApp.setNextForm(None)
        self.editing = False
        self.parentApp.switchFormNow()
