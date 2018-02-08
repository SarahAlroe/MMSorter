# import the necessary packages
import numpy as np
import cv2
import serial
import time
from enum import Enum


class AppState(Enum):
    IDLE = 1
    MOVE = 2
    ACTIVE = 3
    COLORSET = 4
    CALIBRATE = 5


#
# Global consts
#

testMode = False
if not testMode:
    from picamera.array import PiRGBArray
    from picamera import PiCamera
    camera = PiCamera()

serialTimeout = 1
baudrate = 9600

sleep_time = 100

#screenWidth = 1920
#screenHeight = 1080
screenWidth = 1280
screenHeight = 1024
screenImageProportion = 0.8
font = cv2.FONT_HERSHEY_SIMPLEX

idletext = "Mid: Sort \nUp: Home \nDown: Move \nLeft: Set color \nRight: Calibrate"
runningText = "Currently running! \nPress middle button to stop"
moveText = "Move mode. \nUse buttons to move head. \nMiddle button to confirm position"
calibrateText = "Starting clibration"

# Clean button colors
pRed = (0, 0, 255)
pGreen = (0, 255, 0)
pBlue = (255, 0, 0)
pYellow = (0, 255, 255)
pOrange = (0, 165, 255)
pBrown = (42, 42, 165)
pColors = [pRed, pGreen, pBlue, pYellow, pOrange, pBrown]

# Experimentally chosen values
iRed = (62, 46, 105)
iGreen = (52, 87, 47)
iBlue = (53, 36, 21)
iYellow = (70, 146, 155)
iOrange = (70, 102, 151)
iBrown = (25, 30, 39)
iColors = [iRed, iGreen, iBlue, iYellow, iOrange, iBrown]
nColors = ["Red", "Green", "Blue", "Yellow", "Orange", "Brown"]

#
# Global vars
#
sorterStatus = "Awaiting connection"
currentState = AppState.IDLE
isOk = False
cPos = [0, 0]
buttonClicked = [False, False, False, False, False]
colorListPos = 0


#
# Function defs
#

def handleSerial():
    global sorterStatus
    global isOk
    while ser.in_waiting != 0:
        line = ser.readline()
        print line

        if line.startswith("OK"):
            isOk = True
        elif line.startswith("BP"):
            buttonNumber = int(line[2])
            buttonClicked[buttonNumber] = True
        elif line.startswith("BR"):
            buttonNumber = int(line[2])
            buttonClicked[buttonNumber] = False
        elif line.startswith("CP"):
            cPos[0] = int(line[2:6])
            cPos[1] = int(line[6:10])
        elif line.startswith("PS"):
            sorterStatus = line[2:]


def findPoints(image):
    # Make gray slightly blurred image for optimal circle detection
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)

    # Detect circles in the image
    detectedcircles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1.2, 50, param1=50, param2=25, minRadius=80,
                                       maxRadius=140)

    # Round xy coordinates to int
    detectedcircles = np.round(detectedcircles[0, :]).astype("int")

    return detectedcircles


def getNewImage():
    if testMode:
        return cv2.imread("testimg.jpg")
    else:
        rawCapture = PiRGBArray(camera)
        time.sleep(0.1)
        camera.capture(rawCapture, format="bgr")
        return rawCapture.array


def drawWindowContent(outputScaled, outputMenu):
    cv2.imshow("MMSorter", np.concatenate((outputScaled, outputMenu), axis=0))


def drawCirclesOnimage(image, circles):
    # For each circle as their xypos and radius
    for circle in circles:
        x = circle[0]
        y = circle[1]
        r = circle[2]
        bestFit = get_circle_color(circle, image)

        # cv2.circle(output, (x, y), r, (abs(pColors[bestFit][0]-meanVal[0]),abs(pColors[bestFit][1]-meanVal[1]),abs(pColors[bestFit][2]-meanVal[2])), -1)
        # Draw inner circle of found color
        cv2.circle(image, (x, y), r, pColors[bestFit], -1)
        # Draw outer perimeter
        cv2.circle(image, (x, y), r, (0, 255, 0), 4)
        # Draw rectangle in middle of circle
        cv2.rectangle(image, (x - 5, y - 5), (x + 5, y + 5), (0, 128, 255), -1)

    return image


def get_circle_color(circle, image):
    x = circle[0]
    y = circle[1]
    r = circle[2]
    # Calculate mean color of circle
    circleImg = np.zeros((image.shape[0], image.shape[1]), dtype=image.dtype)
    cv2.circle(circleImg, (x, y), r, 1, -1)
    meanVal = cv2.mean(image, mask=circleImg)
    # Find the best fitting color
    minDistance = 3 * 255
    bestFit = 0
    for i in range(0, len(iColors)):
        distance = abs(meanVal[0] - iColors[i][0]) + abs(meanVal[1] - iColors[i][1]) + abs(
            meanVal[2] - iColors[i][2])
        if distance < minDistance:
            minDistance = distance
            bestFit = i
    return bestFit


def draw_menu_button(image, pos, state):
    r = 20
    if state:
        cv2.circle(image, pos, r, (255, 255, 255), -1)
    else:
        cv2.circle(image, pos, r, (255, 255, 255), 3)


def generate_menu_image_from_shape(shape):
    width = int(screenHeight * (1 - screenImageProportion))
    height = int(screenHeight * screenImageProportion / shape[0] * shape[1])

    menu = np.zeros((width, height, 3), np.uint8)
    cv2.putText(menu, sorterStatus, (5, width - 10), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(menu, str(cPos), (height - 150, width - 10), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

    butttonCenterX = height - 200
    buttonCenterY = 80
    buttonOffset = 45

    draw_menu_button(menu, (butttonCenterX, buttonCenterY), buttonClicked[0])
    draw_menu_button(menu, (butttonCenterX, buttonCenterY - buttonOffset), buttonClicked[1])
    draw_menu_button(menu, (butttonCenterX, buttonCenterY + buttonOffset), buttonClicked[2])
    draw_menu_button(menu, (butttonCenterX - buttonOffset, buttonCenterY), buttonClicked[3])
    draw_menu_button(menu, (butttonCenterX + buttonOffset, buttonCenterY), buttonClicked[4])

    y0 = 30
    dy = 25
    if currentState == AppState.IDLE:
        for i, line in enumerate(idletext.split('\n')):
            y = y0 + i * dy
            cv2.putText(menu, line, (5, y), font, 0.75, (255, 255, 255), 1, cv2.LINE_AA)
    elif currentState == AppState.MOVE:
        for i, line in enumerate(moveText.split('\n')):
            y = y0 + i * dy
            cv2.putText(menu, line, (5, y), font, 0.75, (255, 255, 255), 1, cv2.LINE_AA)
    elif currentState == AppState.ACTIVE:
        for i, line in enumerate(runningText.split('\n')):
            y = y0 + i * dy
            cv2.putText(menu, line, (5, y), font, 0.75, (255, 255, 255), 1, cv2.LINE_AA)
    elif currentState == AppState.CALIBRATE:
        for i, line in enumerate(calibrateText.split('\n')):
            y = y0 + i * dy
            cv2.putText(menu, line, (5, y), font, 0.75, (255, 255, 255), 1, cv2.LINE_AA)
    elif currentState == AppState.COLORSET:
        for i in range(0, 6):
            y = y0 + i * dy
            if i == colorListPos:
                cv2.putText(menu, "> " + nColors[i], (5, y), font, 0.75, (255, 255, 255), 1, cv2.LINE_AA)
            else:
                cv2.putText(menu, nColors[i], (5, y), font, 0.75, (255, 255, 255), 1, cv2.LINE_AA)

    return menu


def resize_img_for_screen(originalImage):
    return cv2.resize(originalImage,
                      (int(screenHeight * screenImageProportion / originalImage.shape[0] * originalImage.shape[1]),
                       int(screenHeight * screenImageProportion)))


def home_machine():
    global isOk
    isOk = False
    ser.write("HM\n")
    wait_for_ok()


def wait_for_ok():
    global isOk
    while not isOk:
        handleSerial()
        cv2.waitKey(sleep_time)


def start_guided_calibration():
    global calibrateText
    for i in range(0, 2):
        home_machine()
        image = getNewImage()
        outputScaled = resize_img_for_screen(image)
        if i == 0:
            calibrateText = "Please place a blue M&M 5 cm from corner nearest home \nand press middle button"
        else:
            calibrateText = "Please place a blue M&M 5 cm from corner furthest home \nand press middle button"
        outputMenu = generate_menu_image_from_shape(outputScaled.shape)
        drawWindowContent(outputScaled, outputMenu)
        while not buttonClicked[0]:
            handleSerial()
            cv2.waitKey(sleep_time)
        while buttonClicked[0]:
            handleSerial()
            cv2.waitKey(sleep_time)
        image = getNewImage()
        circles = findPoints(image)
        output = drawCirclesOnimage(image, circles)
        cv2.rectangle(output, (circles[0][0] - circles[0][2], circles[0][1] - circles[0][2]),
                      (circles[0][0] + circles[0][2], circles[0][1] + circles[0][2]), (255, 255, 255), 5)
        outputScaled = resize_img_for_screen(output)
        caliPoint = circles[0]
        calibrateText = "Please move head to M&M \nand press middle button"
        outputMenu = generate_menu_image_from_shape(outputScaled.shape)
        drawWindowContent(outputScaled, outputMenu)
        while not buttonClicked[0]:
            handleSerial()
            isMoving = False
            global isOk
            isOk = False
            if buttonClicked[1]:
                ser.write("MV+0000-0010\n")
                isMoving = True
            if buttonClicked[2]:
                ser.write("MV+0000+0010\n")
                isMoving = True
            if buttonClicked[3]:
                ser.write("MV-0010+0000\n")
                isMoving = True
            if buttonClicked[4]:
                ser.write("MV+0010+0000\n")
                isMoving = True
            if isMoving:
                wait_for_ok()
            outputMenu = generate_menu_image_from_shape(outputScaled.shape)
            drawWindowContent(outputScaled, outputMenu)
            cv2.waitKey(sleep_time)
        while buttonClicked[0]:
            handleSerial()
            cv2.waitKey(sleep_time)
        x_pos_padded = pad_to_string(caliPoint[0], 4)
        y_pos_padded = pad_to_string(caliPoint[1], 4)
        ser.write("CA" + str(i) + x_pos_padded + y_pos_padded)
        wait_for_ok()


def pad_to_string(number, length):
    numstring = str(number)
    while len(numstring) < length:
        numstring = "0" + numstring
    return numstring


def sort_mms():
    global isOk
    home_machine()
    image = getNewImage()
    output = image.copy()
    circles = findPoints(image)

    # Only do circle stuff if any are actually found
    if circles is not None:
        output = drawCirclesOnimage(output, circles)
        willBreak = False
        for circle in circles:
            marked_output = output.copy()
            cv2.rectangle(marked_output, (circle[0] - circle[2], circle[1] - circle[2]),
                          (circle[0] + circle[2], circle[1] + circle[2]), (255, 255, 255), 5)
            outputScaled = resize_img_for_screen(marked_output)
            colorString = str(get_circle_color(circle, image))
            x_padded = pad_to_string(circle[0], 4)
            y_padded = pad_to_string(circle[0], 4)
            isOk = False
            ser.write("GB" + colorString + x_padded + y_padded + "\n")
            while (not isOk) and (not willBreak):
                handleSerial()
                outputMenu = generate_menu_image_from_shape(output.shape)
                drawWindowContent(outputScaled, outputMenu)
                cv2.waitKey(sleep_time)
                if buttonClicked[0]:
                    willBreak = True
            if willBreak:
                break


#
# Main
#
# Setup serial
# ser = serial.Serial('/dev/ttyUSB0', baudrate, timeout=serialTimeout)
ser = serial.Serial('/dev/ttyACM0', baudrate, timeout=serialTimeout)

# Setup window
cv2.namedWindow("MMSorter", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("MMSorter", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# Get image
image = getNewImage()
outputScaled = resize_img_for_screen(image)
while True:
    handleSerial()
    if currentState == AppState.IDLE:
        if buttonClicked[0]:
            currentState = AppState.ACTIVE
        elif buttonClicked[1]:
            home_machine()
        elif buttonClicked[2]:
            currentState = AppState.MOVE
        elif buttonClicked[3]:
            currentState = AppState.COLORSET
        elif buttonClicked[4]:
            currentState = AppState.CALIBRATE
    elif currentState == AppState.ACTIVE:
        sort_mms()
        currentState = AppState.IDLE
    elif currentState == AppState.MOVE:
        if buttonClicked[0]:
            currentState = AppState.IDLE
        isOk = False
        if buttonClicked[1]:
            ser.write("MV+0000-0010\n")
            wait_for_ok()
        if buttonClicked[2]:
            ser.write("MV+0000+0010\n")
            wait_for_ok()
        if buttonClicked[3]:
            ser.write("MV-0010+0000\n")
            wait_for_ok()
        if buttonClicked[4]:
            ser.write("MV+0010+0000\n")
            wait_for_ok()
    elif currentState == AppState.COLORSET:
        if buttonClicked[0]:
            ser.write("SC" + str(colorListPos))
            currentState = AppState.IDLE
        elif buttonClicked[1]:
            colorListPos -= 1
            if colorListPos == -1:
                colorListPos = 5
        elif buttonClicked[2]:
            colorListPos += 1
            if colorListPos == 6:
                colorListPos = 0
        elif buttonClicked[3]:
            currentState = AppState.IDLE
        elif buttonClicked[4]:
            currentState = AppState.MOVE
    elif currentState == AppState.CALIBRATE:
        start_guided_calibration()
        currentState = AppState.IDLE
    outputMenu = generate_menu_image_from_shape(image.shape)
    drawWindowContent(outputScaled, outputMenu)
    cv2.waitKey(sleep_time)
