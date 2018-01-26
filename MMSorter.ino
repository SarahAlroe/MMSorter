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

const PROGMEM int BUTTON_PINS[] = {A1, A2, A3, A4, A5};
const PROGMEM int NUM_BUTTONS = 5;
const PROGMEM int SPINS_X[] = {7, 6, 5, 8};
const PROGMEM int SPINS_Y[] = {11, 10, 9, 12};
const PROGMEM int END_PIN_X = A0;
const PROGMEM int END_PIN_Y = 13;
const PROGMEM int RELAY_PIN_A = 2;
const PROGMEM int RELAY_PIN_B = 3;
const PROGMEM int AUX_PIN = 4;

//EEPROM storage structure: CalP1, CalP2, ColP1, CamP1, CamP2, ColP2 ColP3 ColP4 ColP5 ColP6 (8 points)
const PROGMEM int EEPROMIntervals[]{0, sizeof(Point)*1, 
sizeof(Point)*2, sizeof(Point)*3, 
sizeof(Point)*4, sizeof(Point)*5, sizeof(Point)*6, 
sizeof(Point)*7, sizeof(Point)*8, sizeof(Point)*9};

const PROGMEM int calStorageShift = 0;
const PROGMEM int camStorageShift = calStorageShift + 2;
const PROGMEM int colorStorageShift = camStorageShift + 2;

Point calibrationPoints[2];
Point calibrationCamPoints[2];
Point colorBoxPoints[6];

bool buttonState[] = {false, false, false, false, false};

Stepper stepperX(STEPS_PER_REV, SPINS_X[0], SPINS_X[1], SPINS_X[2], SPINS_X[3]);
Stepper stepperY(STEPS_PER_REV, SPINS_Y[0], SPINS_Y[1], SPINS_Y[2], SPINS_Y[3]);

Point cPos;

bool hasCalibrationData[] = {false, false};

void setup() {
  Serial.begin(9600);
  pushStatus(STATUS_SETUP_START);

  //Read and check calibration status
  readCalibrationData();
  if (isCalibrated()) {
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
    } else if (command == CODE_CALIBRATE) {
      int caliPointNumber = input.substring(2, 1).toInt();
      Point caliPointCam = Point(input.substring(3, 4).toInt(), input.substring(7, 4).toInt());
      Point caliPointReal = cPos;
      storeCalibrationData(caliPointNumber, caliPointCam, caliPointReal);

      if (! isCalibrated()) {
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

void readColorPosData(){
  for (int i = 0; i<6; i++){
    EEPROM.get(EEPROMIntervals[i+colorStorageShift],colorBoxPoints[i]);
  }
}

void storeColorPosition(int colorNum, Point cPos) {
  EEPROM.put(EEPROMIntervals[colorNum+colorStorageShift], cPos);
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

bool isCalibrated() {
  return calibrationPoints[0]!=Point(0,0) 
    && calibrationPoints[1]!=Point(0,0) 
    && calibrationCamPoints[0]!=Point(0,0) 
    && calibrationCamPoints[1]!=Point(0,0);
}

void grabMMAndSort(int colorNum, Point mmCamPos) {
  //TODOGrab M&M at camera position and move to matching container.
  Point stepPos = calculateStepPosFromCalibration(mmCamPos);
  //Calculate real pos
  //Goto pos - pick up
  //Lookup colorpos, goto drop.
}

Point calculateStepPosFromCalibration(mmCamPos){
  
}

void goToPos(Point pos){
  Point toMove = pos-cPos;
  stepperX.step(toMove.x); //TODO, optimize
  stepperY.step(toMove.y);
  cPos = pos; 
}

void handleButtons() {
  for(int i=0; i<NUM_BUTTONS; i++){
    bool buttonPressed = !digitalRead(BUTTON_PINS[i]); //Inverse because pullup
    if (buttonPressed != buttonState[i]){
      if (buttonPressed){
        sendButtonPressed(i);
      }else{
        sendButtonReleased(i);
      }
      buttonState[i]=buttonPressed;
    }
  }
}

void sendButtonPressed(int button){
  Serial.println(CODE_BUTTON_PUSH + button);
}

void sendButtonReleased(int button){
  Serial.println(CODE_BUTTON_RELEASE + button);
}
