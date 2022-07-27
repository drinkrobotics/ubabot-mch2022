import display
import buttons
import mch22
import wifi
import time
import math
import nvs
import urequests as requests

class ButtonInput:
    def __init__(self, a = False, b = False, up = False, down = False):
        self.a = a
        self.b = b
        self.up = up
        self.down = down

class StateWifiConnect:
    connect_timeout = 0
    parent = None

    def __init__(self, parent):
        self.parent = parent

    def enter(self):
        self.parent.drawSplash()
        self.parent.drawWifiStatus()

        display.drawText(0, 60, "Attempting to connect to WiFi of UbaBot.")
        display.drawText(0, 80, "Make sure you are near the machine.")
        display.drawText(0, 100, "It is located in FruBar Island village.")
        display.drawText(0, 160, "Press HOME button to exit this app.")

        display.flush()

        # Start establishing WiFi connection
        wifi.connect("ubabot", "ubabot1337")
        connect_timeout = time.time() + 60

    def act(self, inputs):
        if wifi.status():
            print("WiFi connected")
            return 1 # login state

        if (time.time() >= self.connect_timeout) and (self.connect_timeout > 0):
            print("WiFi timeout")
            self.parent.errorMessage = "WiFi connection timed out!"
            self.parent.errorThrower = 0
            return 3 # error state

        return -1

    def exit(self):
        pass

class StateLogin:
    parent = None
    login_running = False
    login_timeout = 0

    def __init__(self, parent):
        self.parent = parent

    def drawLoginButton(self):
        display.drawText(60, 70, "Please Log In Now", 0x0044FF, "roboto_black22")
        display.drawText(0, 130, "Press A to login to UbaBot.")
        display.drawText(0, 160, "Press HOME button to exit this app.")

    def draw(self):
        self.parent.drawSplash()
        self.parent.drawWifiStatus()

        if self.login_running:
            display.drawText(0, 100, "Logging in to UbaBot.")
            display.drawText(0, 130, "Please wait.")
            display.drawText(0, 160, "Press HOME button to exit this app.")
        else:
            self.drawLoginButton()

        display.flush()

    def enter(self):
        self.login_running = False
        self.login_timeout = 0
        self.draw()

    def performLogin(self):
        try:
            nickname = nvs.nvs_getstr("owner", "nickname")
            if len(nickname) <= 1:
                print("No username set")
                self.parent.errorMessage = "No username set on badge!"
                self.parent.errorThrower = 1
                return 3
            else:
                # TODO nickname should be query-string url-encoded

                login_res = requests.get(self.parent.uba_url + "/badge?name=" + nickname)
                login = login_res.text
                print("got response: \"" + login + "\"")
                if "ok" in login:
                    return 2
                else:
                    print("Other user already logged in")
                    self.parent.errorMessage = login
                    self.parent.errorThrower = 1
                    return 3
        except OSError as e:
            print("Error logging into Ubabot")
            print(e)
            self.parent.errorMessage = "Login Error ({})".format(str(e))
            self.parent.errorThrower = 1
            return 3

        return -1

    def act(self, inputs):
        if inputs.a and not self.login_running:
            self.login_running = True
            self.login_timeout = time.time() + 60
            self.draw()
            return self.performLogin()

        if self.login_running and (time.time() >= self.login_timeout):
            self.login_running = False
            self.draw()

        return -1

    def exit(self):
        pass

class StateStatus:
    parent = None

    def __init__(self, parent):
        self.parent = parent

    def queryAlcoholLevel(self):
        bac = 0.0
        redraw = 0

        try:
            nickname = nvs.nvs_getstr("owner", "nickname")
            if len(nickname) <= 1:
                print("No username set")
                return -1
            else:
                # TODO nickname should be query-string url-encoded

                bac_res = requests.get(self.parent.uba_url + "/bac?name=" + nickname)
                print("got bac response: \"" + bac_res.text + "\"")
                try:
                    bac = float(bac_res.text)
                except ValueError as e:
                    print("Error interpreting BAC")
                    print(e)
                    return -1
        except OSError as e:
            print("Error getting BAC")
            print(e)
            return -1

        return bac

    def drawHelp(self):
        display.drawText(0, 140, "Querying data from UbaBot.")
        display.drawText(0, 160, "Please wait.")
        display.drawText(0, 180, "Press HOME button to exit this app.")

    def drawData(self):
        nickname = nvs.nvs_getstr("owner", "nickname")
        display.drawText(0, 65, "User: " + nickname + "@drinkrobotics.de", 0xFFFFFF, "roboto_regular12")
        display.drawText(0, 90, "Pass: " + nickname + "mch2022", 0xFFFFFF, "roboto_regular12")
        display.drawText(0, 120, "You can order at the machine now!", 0xFFFFFF, "roboto_regular18")

    def drawAlcohol(self):
        pegel = self.bac
        if (pegel >= 0):
            display.drawText(0, 150, "BAC: {:.2f}% / {:.2f}‰".format(pegel, pegel / 10.0))

    def enter(self):
        self.parent.drawSplash()
        self.parent.drawWifiStatus()
        self.drawData()
        self.drawHelp()
        display.flush()

        self.bac = self.queryAlcoholLevel()
        self.redraw = time.time() + 10

        self.parent.drawSplash()
        self.parent.drawWifiStatus()
        self.drawData()
        self.drawAlcohol()
        display.flush()

    def act(self, inputs):
        if time.time() >= self.redraw:
            self.bac = self.queryAlcoholLevel()
            self.redraw = time.time() + 10

            self.parent.drawSplash()
            self.parent.drawWifiStatus()
            self.drawData()
            self.drawAlcohol()
            display.flush()

        return -1

    def exit(self):
        pass

class StateError:
    parent = None

    def __init__(self, parent):
        self.parent = parent

    def enter(self):
        pass

    def act(self, inputs):
        self.parent.drawSplash()
        self.parent.drawWifiStatus()

        display.drawText(0, 60, "ERROR!", 0xFF0000)

        if (self.parent.errorMessage == None) or (self.parent.errorMessage == ""):
            display.drawText(0, 80, "Connection to UbaBot could not be established!")
        else:
            display.drawText(0, 80, self.parent.errorMessage)

        display.drawText(0, 100, "Please press A or B button to try again.")
        display.drawText(0, 160, "Press HOME button to exit this app.")

        display.flush()

        if inputs.a or inputs.b:
            return self.parent.errorThrower

        return -1

    def exit(self):
        pass

class UbaBot:
    # production server
    uba_url = "http://192.168.0.1:8080"

    # debug / testing server
    #uba_url = "http://192.168.0.108:8000"

    states = []

    current_state = 0
    inputs = ButtonInput()
    errorMessage = ""
    errorThrower = 0

    def reboot(self, pressed):
        if pressed:
            mch22.exit_python()

    def buttonA(self, pressed):
        self.inputs.a = pressed

    def buttonB(self, pressed):
        self.inputs.b = pressed

    def buttonUp(self, pressed):
        self.inputs.up = pressed

    def buttonDown(self, pressed):
        self.inputs.down = pressed

    def main(self):
        self.states = [
            StateWifiConnect(self),
            StateLogin(self),
            StateStatus(self),
            StateError(self)
        ]
        buttons.attach(buttons.BTN_HOME, self.reboot)
        buttons.attach(buttons.BTN_A, self.buttonA)
        buttons.attach(buttons.BTN_B, self.buttonB)
        buttons.attach(buttons.BTN_DOWN, self.buttonDown)
        buttons.attach(buttons.BTN_UP, self.buttonUp)

        while True:
            s = self.states[self.current_state]
            s.enter()

            while True:
                r = s.act(self.inputs)
                self.inputs = ButtonInput()
                if (r >= 0):
                    print("Changing state from " + str(self.current_state) + " to " + str(r))
                    s.exit()
                    self.current_state = r
                    break

    def drawSplash(self):
        display.drawFill(0x000000)
        display.drawText(5, 0, "UbaBot Cocktail Machine", 0xFF0000, "permanentmarker22")
        display.drawText(10, 30, "@ FruBar Island", 0x00FF00, "press_start_2p18")

    def drawWifiStatus(self):
        status = "Disconnected"
        if wifi.status:
            status = "Connected"
        text = "WiFi Status: " + status
        h = display.getTextHeight(text)
        display.drawText(0, display.height() - h, text , 0xFFFFFF)

        #text = self.status_text
        #w = display.getTextWidth(text)
        #h = display.getTextHeight(text)
        #display.drawText(display.width() - w, display.height() - h, text, self.status_color)

uba = UbaBot()
uba.main()
