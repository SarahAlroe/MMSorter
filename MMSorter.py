# import the necessary packages
import numpy as np
import cv2
import serial
from enum import Enum

class AppState(Enum):
    IDLE = 1
    MOVE = 2
    ACTIVE = 3

#
# Global consts
#
serialTimeout = 1
baudrate = 9600

screenWidth = 1920
screenHeight = 1080
screenImageProportion = 0.8
font = cv2.FONT_HERSHEY_SIMPLEX

idletext = "Mid: Sort \nUp: Home \nDown: Move \nLeft: Set color \nRight: Calibrate"
runningText = "Currently running! \nPress middle button to stop"
moveText = "Move mode. \nUse buttons to move head. \nMiddle button to confirm position"

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

#
# Global vars
#
sorterStatus = "Awaiting connection"
currentState = AppState.IDLE
isOk = False
cPos = [0, 0]
buttonClicked = [False, False, False, False, False]


#
# Function defs
#

def handleSerial():
    while ser.in_waiting!=0:
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
    detectedcircles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1.2, 50, param1=50, param2=25, minRadius=80, maxRadius=140)

    # Round xy coordinates to int
    detectedcircles = np.round(detectedcircles[0, :]).astype("int")

    return detectedcircles

def getNewImage():
    # load the image, clone it for output, and then convert it to grayscale
    # image = cv2.imread(args["image"])
    return cv2.imread("testimg.jpg")

def drawWindowContent(outputScaled, outputMenu):
    cv2.imshow("MMSorter", np.concatenate((outputScaled, outputMenu), axis=0))

def drawCirclesOnimage(image, circles):
    # For each circle as their xypos and radius
    for (x, y, r) in circles:
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

        # cv2.circle(output, (x, y), r, (abs(pColors[bestFit][0]-meanVal[0]),abs(pColors[bestFit][1]-meanVal[1]),abs(pColors[bestFit][2]-meanVal[2])), -1)
        # Draw inner circle of found color
        cv2.circle(image, (x, y), r, pColors[bestFit], -1)
        # Draw outer perimeter
        cv2.circle(image, (x, y), r, (0, 255, 0), 4)
        # Draw rectangle in middle of circle
        cv2.rectangle(image, (x - 5, y - 5), (x + 5, y + 5), (0, 128, 255), -1)

    return image


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
    print width
    cv2.putText(menu, sorterStatus, (5, width-10), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(menu, str(cPos), (height-150, width - 10), font, 1, (255, 255, 255), 2, cv2.LINE_AA)

    butttonCenterX = height-200
    buttonCenterY = 80
    buttonOffset = 45

    draw_menu_button(menu, (butttonCenterX,buttonCenterY), buttonClicked[0])
    draw_menu_button(menu, (butttonCenterX, buttonCenterY-buttonOffset), buttonClicked[1])
    draw_menu_button(menu, (butttonCenterX, buttonCenterY+buttonOffset), buttonClicked[2])
    draw_menu_button(menu, (butttonCenterX-buttonOffset, buttonCenterY), buttonClicked[3])
    draw_menu_button(menu, (butttonCenterX+buttonOffset, buttonCenterY), buttonClicked[4])

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

    return menu


def resize_img_for_screen(originalImage):
    return cv2.resize(originalImage, (int(screenHeight * screenImageProportion / originalImage.shape[0] * originalImage.shape[1]),
                               int(screenHeight * screenImageProportion)))


#
# Main
#
#Setup serial
#ser = serial.Serial('/dev/ttyUSB0', baudrate, timeout=serialTimeout)
ser = serial.Serial('/dev/ttyACM0', baudrate, timeout=serialTimeout)

#Setup window
cv2.namedWindow("MMSorter", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("MMSorter", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

#Get image
image = getNewImage()

output = image.copy()
# Get image dimensions

circles = findPoints(image)

# Only do circle stuff if any are actually found
if circles is not None:
    output = drawCirclesOnimage(output, circles)
    cv2.imwrite("output2.jpg", output)

    # Show the output image
    outputScaled = resize_img_for_screen(output)
    outputMenu = generate_menu_image_from_shape(output.shape)
    drawWindowContent(outputScaled, outputMenu)
    #  Wait for a few clicks
    cv2.waitKey(0)
    handleSerial()
    outputMenu = generate_menu_image_from_shape(output.shape)
    drawWindowContent(outputScaled, outputMenu)
    cv2.waitKey(0)
    handleSerial()
    outputMenu = generate_menu_image_from_shape(output.shape)
    drawWindowContent(outputScaled, outputMenu)
    cv2.waitKey(0)

