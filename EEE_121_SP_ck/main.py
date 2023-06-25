import npyscreen
from libs.menu import Menu as menu
from libs.chatform import ChatForm
from libs.chatform import ChatInput

class ChatApp(npyscreen.NPSAppManaged):
    # Method called at start by npyscreen
    def onStart(self):
        self.menu = self.addForm('MAIN', menu, name='Peer-2-Peer Chat by CK | Menu')
        self.chatform = self.addForm("CHAT", ChatForm, name = 'Peer-2-Peer Chat by CK | Chat')

    def change_form(self, name):
        self.switchForm(name)
        self.resetHistory()
if __name__ == '__main__':
    ChatApp().run()