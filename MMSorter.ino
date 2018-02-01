#include <EEPROM.h>

#include <Stepper.h>
#include "Helpers.h"

const PROGMEM String STATUS_SETUP_START = "Starting system";
const PROGMEM String STATUS_SETUP_CAL_READ = "Read calibration data";
const PROGMEM String STATUS_CAL_MISSING = "Missing Calibration Data";
const PROGMEM String STATUS_SETUP_STEPPER = "Steppers initialized";
const PROGMEM String STATUS_MOVING = "Moving grab head";
const PROGMEM String STATUS_GRAB = "Grabbing M&M";
const PROGMEM String STATUS_RELEASE = "Releasing M&M";
const PROGMEM String STATUS_IDLE = "Awaiting instructions";

const PROGMEM String CODE_RESET = "RS";
const PROGMEM String CODE_MOVE = "MV";
const PROGMEM String CODE_HOME = "HM";
const PROGMEM String CODE_CALIBRATE = "CA";
const PROGMEM String CODE_GRAB = "GB";
const PROGMEM String CODE_SET_COLOR = "SC";

const PROGMEM String CODE_OK = "OK";
const PROGMEM String CODE_BUTTON_PUSH = "BP";
const PROGMEM String CODE_BUTTON_RELEASE = "BR";
const PROGMEM String CODE_CURRENT_POS = "CP";
const PROGMEM String CODE_PUSH_STATUS = "PS";

const PROGMEM int STEPS_PER_REV = 200;
const PROGMEM int STEPPER_SPEED = 40;

int BUTTON_PINS[] = {A1, A2, A3, A4, A5};
const PROGMEM int NUM_BUTTONS = 5;
int SPINS_X[] = {7, 6, 5, 8};
int SPINS_Y[] = {11, 10, 9, 12};
int END_PIN_X = A0;
int END_PIN_Y = 13;
int RELAY_PIN_ARM = 2;
int RELAY_PIN_SUCC = 3;
int AUX_PIN = 4;

const PROGMEM int ARM_MOVE_DELAY = 1 * 1000;

//EEPROM storage structure: CalP1, CalP2, ColP1, CamP1, CamP2, ColP2 ColP3 ColP4 ColP5 ColP6 (8 points)
const PROGMEM int EEPROMIntervals[] {0, sizeof(Point) * 1,
        sizeof(Point) * 2, sizeof(Point) * 3,
        sizeof(Point) * 4, sizeof(Point) * 5, sizeof(Point) * 6,
        sizeof(Point) * 7, sizeof(Point) * 8, sizeof(Point) * 9
};

const PROGMEM int calStorageShift = 0;
const PROGMEM int camStorageShift = calStorageShift + 2;
const PROGMEM int colorStorageShift = camStorageShift + 2;

Point calibrationPoints[2];
Point calibrationCamPoints[2];
Point colorBoxPoints[6];

float camToRealXMultiplier = 0.0f;
float camToRealYMultiplier = 0.0f;
Point camToRealOffset = Point();

bool buttonState[] = {false, false, false, false, false};

Stepper stepperX(STEPS_PER_REV, SPINS_X[0], SPINS_X[1], SPINS_X[2], SPINS_X[3]);
Stepper stepperY(STEPS_PER_REV, SPINS_Y[0], SPINS_Y[1], SPINS_Y[2], SPINS_Y[3]);

Point cPos;

void setup() {
  Serial.begin(9600);
  pushStatus(STATUS_SETUP_START);

  //Read and check calibration status
  readCalibrationData();
  if (hasCalibrationData()) {
    calculateCalibrationVars();
    pushStatus(STATUS_SETUP_CAL_READ);
  } else {
    pushStatus(STATUS_CAL_MISSING);
  }

  readColorPosData();

  stepperX.setSpeed(STEPPER_SPEED);
  stepperY.setSpeed(STEPPER_SPEED);

  //Configure all buttons as pullup
  for (int i = 0; i < NUM_BUTTONS; i++) {
    pinMode(BUTTON_PINS[i], INPUT_PULLUP);
  }
  pinMode(END_PIN_X, INPUT_PULLUP);
  pinMode(END_PIN_Y, INPUT_PULLUP);

}

void loop() {
  serialRead();
  handleButtons();
}

void serialRead() {
  //Check for new serial input - act accordingly
  if (Serial.available()) {
    //If serial data i available, read it into buffer
    String input = Serial.readString();
    //Figure out what to do
    String command = input.substring(0, 2);
    if (command == CODE_HOME) {
      homeSteppers();
    } else if (command == CODE_MOVE) {
      Point moveOffset = Point(input.substring(2, 4).toInt(), input.substring(6, 4).toInt());
      goToPos(cPos + moveOffset);
    } else if (command == CODE_CALIBRATE) {
      int caliPointNumber = input.substring(2, 1).toInt();
      Point caliPointCam = Point(input.substring(3, 4).toInt(), input.substring(7, 4).toInt());
      Point caliPointReal = cPos;
      storeCalibrationData(caliPointNumber, caliPointCam, caliPointReal);

      if (hasCalibrationData()) {
        calculateCalibrationVars();
      } else {
        pushStatus(STATUS_CAL_MISSING);
      }

    } else if (command == CODE_SET_COLOR) {
      int colorNum = input.substring(2, 1).toInt();
      storeColorPosition(colorNum, cPos);

    } else if (command == CODE_GRAB) {
      int colorNum = input.substring(2, 1).toInt();
      Point mmCamPos = Point(input.substring(3, 4).toInt(), input.substring(7, 4).toInt());
      grabMMAndSort(colorNum, mmCamPos);
    }
    Serial.println(CODE_OK);
  }
}

void pushStatus(String statusMessage) {
  Serial.println(CODE_PUSH_STATUS + statusMessage);
}

void homeSteppers() {
  while (!digitalRead(END_PIN_X)) {
    stepperX.step(-1);
  }
  while (!digitalRead(END_PIN_Y)) {
    stepperY.step(-1);
  }
  cPos = Point();
}

void readColorPosData() {
  for (int i = 0; i < 6; i++) {
    EEPROM.get(EEPROMIntervals[i + colorStorageShift], colorBoxPoints[i]);
  }
}

void storeColorPosition(int colorNum, Point cPos) {
  EEPROM.put(EEPROMIntervals[colorNum + colorStorageShift], cPos);
}

void readCalibrationData() {
  EEPROM.get(EEPROMIntervals[0], calibrationPoints[0]);
  EEPROM.get(EEPROMIntervals[1], calibrationPoints[1]);
  EEPROM.get(EEPROMIntervals[camStorageShift + 0], calibrationCamPoints[0]);
  EEPROM.get(EEPROMIntervals[camStorageShift + 1], calibrationCamPoints[1]);
}

void storeCalibrationData(int caliPointNumber, Point caliPointCam, Point caliPointReal) {
  EEPROM.put(EEPROMIntervals[caliPointNumber], caliPointReal);
  EEPROM.put(EEPROMIntervals[caliPointNumber + camStorageShift], caliPointCam);
  calibrationPoints[caliPointNumber] = caliPointReal;
  calibrationCamPoints[caliPointNumber] = caliPointCam;
}

void calculateCalibrationVars() {
  //Get difference between calibration points
  Point realDiff = calibrationPoints[1] - calibrationPoints[0];
  Point camDiff = calibrationCamPoints[1] - calibrationCamPoints[0];

  //Multiplier for converting a cam to real pos calculated
  camToRealXMultiplier = float(realDiff.x) / float(camDiff.x);
  camToRealYMultiplier = float(realDiff.y) / float(camDiff.y);

  //Offset from 0,0 calculated using multiplier
  int camToRealXOffset = calibrationPoints[1].x - int(calibrationCamPoints[1].x * camToRealXMultiplier);
  int camToRealYOffset = calibrationPoints[1].y - int(calibrationCamPoints[1].y * camToRealYMultiplier);
  camToRealOffset = Point(camToRealXOffset, camToRealYOffset);
}

bool hasCalibrationData() {
  return calibrationPoints[0] != Point(0, 0)
         && calibrationPoints[1] != Point(0, 0)
         && calibrationCamPoints[0] != Point(0, 0)
         && calibrationCamPoints[1] != Point(0, 0);

}

void grabMMAndSort(int colorNum, Point mmCamPos) {
  Point stepPos = calculateStepPosFromCalibration(mmCamPos);
  goToPos(stepPos);
  pickUpAndHoldMM();
  goToPos(colorBoxPoints[colorNum]);
  releaseMM();
}

Point calculateStepPosFromCalibration(Point mmCamPos) {
  float realXPos = float(mmCamPos.x) * camToRealXMultiplier;
  float realYPos = float(mmCamPos.y) * camToRealYMultiplier;
  Point realPos = Point(int(realXPos), int(realYPos));
  realPos = realPos + camToRealOffset;
  return realPos;
}

void goToPos(Point pos) {
  Point toMove = pos - cPos;
  while (toMove != Point(0, 0)) {
    Point nextStep = toMove.sign();
    stepperX.step(nextStep.x);
    stepperY.step(nextStep.y);
    toMove = toMove - nextStep;
  }
  cPos = pos;
}

void pickUpAndHoldMM() {
  digitalWrite(RELAY_PIN_ARM, HIGH);
  digitalWrite(RELAY_PIN_SUCC, HIGH);
  delay(ARM_MOVE_DELAY);
  digitalWrite(RELAY_PIN_ARM, LOW);
}

void releaseMM() {
  digitalWrite(RELAY_PIN_SUCC, LOW);
}

void handleButtons() {
  for (int i = 0; i < NUM_BUTTONS; i++) {
    bool buttonPressed = (digitalRead(BUTTON_PINS[i])==LOW); //Inverse because pullup
    if (buttonPressed != buttonState[i]) {
      if (buttonPressed) {
        sendButtonPressed(i);
      } else {
        sendButtonReleased(i);
      }
      buttonState[i] = buttonPressed;
    }
  }
}

void sendButtonPressed(int button) {
  Serial.println(CODE_BUTTON_PUSH + button);
}

void sendButtonReleased(int button) {
  Serial.println(CODE_BUTTON_RELEASE + button);
}
