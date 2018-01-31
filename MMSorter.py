# import the necessary packages
import numpy as np
import argparse
import cv2

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
    return cv2.imread("testimg.jpg")

def drawWindowContent(outputScaled, outputMenu):
    cv2.imshow("MMSorter", np.concatenate((outputScaled, outputMenu), axis=0))

def drawCirclesOnimage(image, circles):
    # For each circle as their xypos and radius
    for (x, y, r) in circles:
        # Calculate mean color of circle
        circleImg = np.zeros((height, width), dtype=image.dtype)
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

screenWidth = 1920
screenHeight = 1080
screenImageProportion = 0.8

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
# iRed = (90, 46, 105) #Artificial
iGreen = (52, 87, 47)
iBlue = (53, 36, 21)
iYellow = (70, 146, 155)
iOrange = (70, 102, 151)
iBrown = (25, 30, 39)
# iBrown = (15, 25, 26)#Artificially lowered
iColors = [iRed, iGreen, iBlue, iYellow, iOrange, iBrown]

# construct the argument parser and parse the arguments
# ap = argparse.ArgumentParser()
# ap.add_argument("-i", "--image", required=True, help="Path to the image")
# args = vars(ap.parse_args())

#Setup window
cv2.namedWindow("MMSorter", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("MMSorter", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# load the image, clone it for output, and then convert it to grayscale
# image = cv2.imread(args["image"])
image = getNewImage()
output = image.copy()
# Get image dimensions
height, width, depth = image.shape

circles = findPoints(image)

# Only do circle stuff if any are actually found
if circles is not None:
    output = drawCirclesOnimage(output, circles)
    cv2.imwrite("output2.jpg", output)

    # Show the output image
    outputScaled = cv2.resize(output, (int(screenHeight * screenImageProportion / output.shape[0] * output.shape[1]),
                                       int(screenHeight * screenImageProportion)))
    outputMenu = np.zeros((int(screenHeight * (1 - screenImageProportion)),
                           int(screenHeight * screenImageProportion / output.shape[0] * output.shape[1]), 3), np.uint8)
    drawWindowContent(outputScaled, outputMenu)
    #  Wait for a few clicks
    cv2.waitKey(0)
    cv2.waitKey(0)
    cv2.waitKey(0)

