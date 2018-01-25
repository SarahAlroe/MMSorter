#include <Stepper.h>
#include "Helpers.h"

const String STATUS_SETUP_START = "Starting system";
const String STATUS_SETUP_CAL_READ = "Read calibration data";
const String STATUS_CAL_MISSING = "Missing Calibration Data";
const String STATUS_SETUP_STEPPER = "Steppers initialized";
const String STATUS_MOVING = "Moving grab head";
const String STATUS_GRAB = "Grabbing M&M";
const String STATUS_RELEASE = "Releasing M&M";
const String STATUS_IDLE = "Awaiting instructions";

const String CODE_RESET = "RS";
const String CODE_HOME = "HM";
const String CODE_CALIBRATE = "CA";
const String CODE_GRAB = "GB";
const String CODE_SET_COLOR = "SC";

const String CODE_OK = "OK";
const String CODE_BUTTON_PUSH = "BP";
const String CODE_BUTTON_RELEASE = "BR";
const String CODE_CURRENT_POS = "CP";
const String CODE_PUSH_STATUS = "PS";

const int STEPS_PER_REV = 200;
const int STEPPER_SPEED = 40;

const int BUTTON_PINS[] = {A1, A2, A3, A4, A5};
const int NUM_BUTTONS = 5;
const int SPINS_X[] = {7, 6, 5, 8};
const int SPINS_Y[] = {11, 10, 9, 12};
const int END_PIN_X = A0;
const int END_PIN_Y = 13;
const int RELAY_PIN_A = 2;
const int RELAY_PIN_B = 3;
const int AUX_PIN = 4;

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

void storeColorPosition(int colorNum, Point cPos) {
  //TODO store
}

void readCalibrationData() {
  //TODO
}

void storeCalibrationData(int caliPointNumber, Point caliPointCam, Point caliPointReal) {
  //TODO Store calibration data saftely
}

bool isCalibrated() {
  return hasCalibrationData[0] && hasCalibrationData[1];
}

void grabMMAndSort(int colorNum, Point mmCamPos) {
  //TODOGrab M&M at camera position and move to matching container.
  Point stepPos = calculateStepPosFromCamPos(mmCamPos);
  //Calculate real pos
  //Goto pos - pick up
  //Lookup colorpos, goto drop.
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
