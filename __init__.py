import display
import buttons
import mch22
import wifi
import time
import math
import nvs
import urequests as requests

# production server
# uba_url = "http://192.168.0.1:8080"

# debug / testing server
uba_url = "http://192.168.0.108:8000"

def reboot(pressed):
    if pressed:
        mch22.exit_python()

def connectUbaWifi():
    wifi.connect("ubabot", "ubabot1337")
    while True:
        if wifi.wait(60):
            break

def drawWifiStatus():
    status = "Disconnected"
    if wifi.status:
        status = "Connected"
    text = "WiFi Status: " + status
    h = display.getTextHeight(text)
    display.drawText(0, display.height() - h, text , 0xFFFFFF)

    text = status_string
    w = 42#display.getTextWidth(text)
    h = 12#display.getTextHeight(text)
    display.drawText(0, 0, status_string, 0xFFFFFF)

def drawSplash():
    # show some nice splash graphics
    display.drawFill(0x000000)
    display.drawText(5, 0, "UbaBot Cocktail Machine", 0xFF0000, "permanentmarker22")
    display.drawText(10, 30, "@ FruBar Island", 0x00FF00, "press_start_2p18")

def drawHelpText():
    display.drawText(0, 60, "Attempting to connect to WiFi of UbaBot.")
    display.drawText(0, 80, "Make sure you are near the machine.")
    display.drawText(0, 100, "It is located in FruBar Island village.")
    display.drawText(0, 160, "Press HOME button to exit this app.")

def drawErrorText():
    display.drawText(0, 60, "ERROR!", 0xFF0000)
    display.drawText(0, 80, "WiFi Connection could not be established!")
    display.drawText(0, 100, "Please restart app to try again.")
    display.drawText(0, 160, "Press HOME button to exit this app.")

def drawErrorTextUbabot():
    display.drawText(0, 60, "ERROR!", 0xFF0000)
    display.drawText(0, 80, "Connection to UbaBot could not be established!")
    display.drawText(0, 100, "Please restart app to try again.")
    display.drawText(0, 160, "Press HOME button to exit this app.")

def scrollMenuDown(pressed):
    if pressed and should_draw_menu:
        menu_index = nvs.nvs_getint("owner", "ubb_i")
        menu_index -= 1
        if menu_index < 0:
            menu_index = 0
        nvs.nvs_setint("owner", "ubb_i", menu_index)
        drawEverything()

def scrollMenuUp(pressed):
    if pressed and should_draw_menu:
        menu_index = nvs.nvs_getint("owner", "ubb_i")
        menu_index += 1
        if menu_index >= len(menu_items):
            menu_index = len(menu_items) - 1
        nvs.nvs_setint("owner", "ubb_i", menu_index)
        drawEverything()

def drawMenuList(items, index):
    display.drawText(0, 50, "Cocktail Menu:", 0x0044FF, "exo2_bold22")

    off = index - math.floor(max_items / 2)
    if off < 0:
        off = 0

    if off > (len(items) - max_items):
        off = len(items) - max_items

    for i in range(0, max_items):
        if ((off + i) > len(items)):
            break

        color = 0xFFFFFF
        if (off + i) == index:
            color = 0xFF0000

        display.drawText(0, 80 + (i * 20), items[off + i], color, "ocra16")

def drawLoginButton():
    display.drawText(60, 70, "Please Log In Now", 0x0044FF, "roboto_black22")
    display.drawText(0, 130, "Press A to login to UbaBot.")
    display.drawText(0, 160, "Press HOME button to exit this app.")

def drawEverything():
    drawSplash()
    drawWifiStatus()

    if should_draw_menu:
        if len(menu_items) <= 0:
            display.drawText(0, 130, "UbaBot can not produce drinks at the moment.")
            display.drawText(0, 160, "Press HOME button to exit this app.")
        else:
            menu_index = nvs.nvs_getint("owner", "ubb_i")
            drawMenuList(menu_items, menu_index)
    else:
        drawLoginButton()

    display.flush()

def actionButton(pressed):
    print("actionButton")
    if pressed:
        if should_draw_menu:
            status_string = "Ordering..."
            status_color = 0x0044FF
            status_clear = time.time() + 3
            drawEverything()

            pass # TODO dispense / order drink
        else:
            status_string = "Logging in..."
            status_color = 0x0044FF
            status_clear = time.time() + 60
            drawEverything()

            attemptLogin()

def queryMenuItems():
    print("queryMenuItems")
    menu_res = requests.get(uba_url + "/menu")
    menu = menu_res.text
    menu = menu.strip().split(",")
    menu_items = []
    for m in menu:
        if len(m) > 2:
            print("Menu Item: " + m)
            menu_items.append(m)
    nvs.nvs_setint("owner", "ubb_i", 0)

def attemptLogin():
    print("attemptLogin")
    try:
        nickname = nvs.nvs_getstr("owner", "nickname")
        login_res = requests.post(uba_url + "/badge", data = b"name=nickname")
        login = login_res.text
        print(login)

        # TODO check if login was successful

        status_string = "Login Successful"
        status_color = 0x00FF00
        status_clear = time.time() + 3
        drawEverything()

        loginEstablished()
    except OSError:
        print("Error logging into Ubabot")
        drawSplash()
        drawErrorTextUbabot()
        display.flush()
        while True:
            pass

def loginEstablished():
    print("loginEstablished")
    try:
        queryMenuItems()
        if len(menu_items) <= 0:
            print("No menu available")
        should_draw_menu = True
    except OSError:
        print("Error getting menu items from Ubabot")
        drawSplash()
        drawErrorTextUbabot()
        display.flush()
        while True:
            pass

# -----------------------------------------------------------------------------

max_items = 6
menu_items = []
should_draw_menu = False

status_string = ""
status_color = 0xFFFFFF
status_clear = 0

# -----------------------------------------------------------------------------

drawSplash()
drawHelpText()
display.flush()

# make sure user can leave while connecting
buttons.attach(buttons.BTN_HOME, reboot)

# Establish WiFi connection
connectUbaWifi()

buttons.attach(buttons.BTN_A, actionButton)
buttons.attach(buttons.BTN_DOWN, scrollMenuUp)
buttons.attach(buttons.BTN_UP, scrollMenuDown)

while True:
    #if time.time() >= status_clear:
    #    status_string = ""
    #    status_color = 0xFFFFFF

    drawEverything()

    time.sleep(0.3)