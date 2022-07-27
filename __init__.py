import display
import buttons
import mch22
import wifi
import time
import math
import nvs
import urequests as requests

class UbaBot:
    # production server
    uba_url = "http://192.168.0.1:8080"

    # debug / testing server
    #uba_url = "http://192.168.0.108:8000"

    max_items = 6
    menu_items = []
    menu_index = 0
    should_draw_menu = False
    kill_thread = 0

    status_text = ""
    status_color = 0xFFFFFF
    status_clear = 0

    def reboot(self, pressed):
        if pressed:
            mch22.exit_python()

    def connectUbaWifi(self):
        wifi.connect("ubabot", "ubabot1337")
        while True:
            if wifi.wait(60):
                break

    def drawWifiStatus(self):
        status = "Disconnected"
        if wifi.status:
            status = "Connected"
        text = "WiFi Status: " + status
        h = display.getTextHeight(text)
        display.drawText(0, display.height() - h, text , 0xFFFFFF)

        text = self.status_text
        w = display.getTextWidth(text)
        h = display.getTextHeight(text)
        display.drawText(display.width() - w, display.height() - h, text, self.status_color)

    def drawSplash(self):
        # show some nice splash graphics
        display.drawFill(0x000000)
        display.drawText(5, 0, "UbaBot Cocktail Machine", 0xFF0000, "permanentmarker22")
        display.drawText(10, 30, "@ FruBar Island", 0x00FF00, "press_start_2p18")

    def drawHelpText(self):
        display.drawText(0, 60, "Attempting to connect to WiFi of UbaBot.")
        display.drawText(0, 80, "Make sure you are near the machine.")
        display.drawText(0, 100, "It is located in FruBar Island village.")
        display.drawText(0, 160, "Press HOME button to exit this app.")

    def drawErrorText(self, msg = None):
        display.drawText(0, 60, "ERROR!", 0xFF0000)

        if msg == None:
            display.drawText(0, 80, "Connection to UbaBot could not be established!")
        else:
            display.drawText(0, 80, msg)

        display.drawText(0, 100, "Please restart app to try again.")
        display.drawText(0, 160, "Press HOME button to exit this app.")

    def scrollMenuDown(self, pressed):
        if pressed and self.should_draw_menu:
            self.menu_index -= 1
            if self.menu_index < 0:
                self.menu_index = 0
            self.drawEverything()

    def scrollMenuUp(self, pressed):
        if pressed and self.should_draw_menu:
            self.menu_index += 1
            if self.menu_index >= len(self.menu_items):
                self.menu_index = len(self.menu_items) - 1
            self.drawEverything()

    def drawMenuList(self, items, index):
        display.drawText(0, 50, "Cocktail Menu:", 0x0044FF, "exo2_bold22")

        off = index - math.floor(self.max_items / 2)
        if off > (len(items) - self.max_items):
            off = len(items) - self.max_items

        if off < 0:
            off = 0

        for i in range(0, self.max_items - 1):
            if ((off + i) > len(items)):
                break

            color = 0xFFFFFF
            if (off + i) == index:
                color = 0xFF0000

            display.drawText(0, 80 + (i * 20), items[off + i], color, "ocra16")

    def drawLoginButton(self):
        display.drawText(60, 70, "Please Log In Now", 0x0044FF, "roboto_black22")
        display.drawText(0, 130, "Press A to login to UbaBot.")
        display.drawText(0, 160, "Press HOME button to exit this app.")

    def drawEverything(self):
        self.drawSplash()
        self.drawWifiStatus()

        if self.should_draw_menu:
            #if len(self.menu_items) <= 0:
            #    display.drawText(0, 130, "UbaBot can not produce drinks at the moment.")
            #    display.drawText(0, 160, "Press HOME button to exit this app.")
            #else:
            #    self.drawMenuList(self.menu_items, self.menu_index)

            nickname = nvs.nvs_getstr("owner", "nickname")
            display.drawText(0, 65, "User: " + nickname + "@drinkrobotics.de", 0xFFFFFF, "ocra16")
            display.drawText(0, 90, "Pass: " + nickname + "mch2022", 0xFFFFFF, "ocra16")
            display.drawText(0, 120, "You can order at the machine now!", 0xFFFFFF, "roboto_regular18")

        else:
            self.drawLoginButton()

        display.flush()

    def drawErrorScreenText(self, msg = None):
        self.drawSplash()
        self.drawWifiStatus()
        self.drawErrorText(msg)
        display.flush()

    def drawErrorScreen(self, msg = None):
        self.kill_thread = 1
        self.kill_msg = msg

    def setStatus(self, text, color, sec):
        status_text = text
        status_color = color
        status_clear = time.time() + sec
        self.drawEverything()

    def actionButton(self, pressed):
        print("actionButton")
        if pressed:
            if self.should_draw_menu:
                #self.setStatus("Ordering...", 0x0044FF, 3)
                pass # TODO dispense / order drink
            else:
                self.setStatus("Logging in...", 0x0044FF, 60)
                self.attemptLogin()

    def queryMenuItems(self):
        print("queryMenuItems")
        menu_res = requests.get(self.uba_url + "/menu")
        menu = menu_res.text
        menu = menu.strip().split(",")
        self.menu_items = []
        for m in menu:
            if len(m) > 2:
                print("Menu Item: " + m)
                self.menu_items.append(m)

    def attemptLogin(self):
        print("attemptLogin")
        try:
            nickname = nvs.nvs_getstr("owner", "nickname")
            if len(nickname) <= 1:
                print("No username set")
                self.drawErrorScreen("Badge Username is not set")
            else:
                # TODO nickname should be query-string url-encoded

                login_res = requests.get(self.uba_url + "/badge?name=" + nickname)
                login = login_res.text
                print("got response: \"" + login + "\"")
                if "ok" in login:
                    self.setStatus("Login Successful", 0x00FF00, 3)
                    self.loginEstablished()
                else:
                    print("Other user already logged in")
                    self.drawErrorScreen(login)
        except OSError as e:
            print("Error logging into Ubabot")
            print(e)
            self.drawErrorScreen()

    def loginEstablished(self):
        print("loginEstablished")
        try:
            #self.queryMenuItems()
            #if len(self.menu_items) <= 0:
            #    print("No menu available")
            self.should_draw_menu = True
        except OSError as e:
            print("Error getting menu items from Ubabot")
            print(e)
            self.drawErrorScreen()

    def autoStatusClear(self):
        if time.time() >= self.status_clear:
            self.status_text = ""

    def main(self):
        # initialize non-volatile storage
        self.setStatus("", 0xFFFFFF, 0)

        self.drawSplash()
        self.drawHelpText()
        display.flush()

        # make sure user can leave while connecting
        buttons.attach(buttons.BTN_HOME, self.reboot)

        # Establish WiFi connection
        self.connectUbaWifi()

        buttons.attach(buttons.BTN_A, self.actionButton)
        buttons.attach(buttons.BTN_DOWN, self.scrollMenuUp)
        buttons.attach(buttons.BTN_UP, self.scrollMenuDown)

        while True:
            self.autoStatusClear()

            if self.kill_thread:
                self.drawErrorScreenText(self.kill_msg)
                if buttons.value(buttons.BTN_HOME):
                    self.reboot(True)
                time.sleep(0.1)
            else:
                self.drawEverything()
                time.sleep(1.0)

# -----------------------------------------------------------------------------

uba = UbaBot()
uba.main()
