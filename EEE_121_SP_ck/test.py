import npyscreen
class Form1(npyscreen.Form):
    def create(self):
        self.name = "I'm the first form! I am so happy!"

    def afterEditing(self):
        self.parentApp.setNextForm("second")

class Form2(npyscreen.Form):
    def create(self):
        self.name = "Im the second form!"

    def afterEditing(self):
        self.parentApp.setNextForm("MAIN")

class App(npyscreen.NPSAppManaged):
    def onStart(self):
        self.registerForm("MAIN", Form1())
        self.registerForm("second", Form2())

App().run()