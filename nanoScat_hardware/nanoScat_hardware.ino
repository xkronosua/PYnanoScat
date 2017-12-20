bool debugMode = 0;

#include <Servo.h>
Servo fWheel;

#define FWHEEL_PIN 5
#define SM_DIR_PIN  4
#define SM_STEP_PIN 11 //7
#define SM_ENABLE_PIN 2
#define HOME_SENSOR_PIN 7  //2

#define LASER_CONTROL_PIN 13
#define LASER_SET_OFF HIGH
#define LASER_SET_ON  LOW
#define LASER_SIM_PIN 9

#define BUTTON_STOP 3
#define BUTTON_CW   6
#define BUTTON_CCW  8


#define FW_CORRECTION 17
byte fWheelAng[6] = {10 + FW_CORRECTION, 40 + FW_CORRECTION, 70 + FW_CORRECTION, 100 + FW_CORRECTION, 130 + FW_CORRECTION, 160 + FW_CORRECTION};
byte activeFilter = 2;

enum COMMANDS {SM_STOP, SM_OFF, SM_ON, SM_HOME_CW, SM_HOME_CCW, SM_ROT_CCW, SM_ROT_CW, SM_ROT_CCWN, SM_ROT_CWN, FWHEEL_ANG, SM_SET_ANGLE,
               SM_MOVE, SM_STEP_MOVE
              };


#define SM_INVERT_DIR 1
#include <AccelStepper.h>
// Define a stepper and the pins it will use
AccelStepper stepper(AccelStepper::DRIVER, SM_STEP_PIN, SM_DIR_PIN); // Defaults to AccelStepper::FULL4WIRE (4 pins) on 2, 3, 4, 5

unsigned long curMillis;
unsigned long prevStepMillis = 0;
unsigned long millisBetweenSteps = 1000; // milliseconds
unsigned long mouseReinit = 1800000; // milliseconds
unsigned long mouseReinitTimer = 0; // milliseconds

unsigned long serialPrevStepMillis = 0;
unsigned long serialOutputPeriod = 1000; // milliseconds

unsigned long angle_timer = 0;
unsigned long laser_timer = 0;


String inputString = "";         // a string to hold incoming command
String inputValue = "";         // a string to hold incoming value

boolean stringComplete = false;  // whether the string is complete



#include <DirectIO.h>
#include "ps2.h"
//PS2 mouse(data, clock);
PS2 mouse(10, 12);

InputPin optEndstop(HOME_SENSOR_PIN);

InputPin stop_button(BUTTON_STOP);
InputPin cw_button(BUTTON_CW);
InputPin ccw_button(BUTTON_CCW);
OutputPin laserControl(LASER_CONTROL_PIN);

OutputPin laserSimulator(LASER_SIM_PIN);


int rotationMode = 0;
int angleCounter = 0;
float ANGLE_CALIBR = 2;
byte homeState = 0;

int SM_SPEED = 512;
int SM_MAX_SPEED = 10000;
float SM_STEP_CALIBR = -991.37; //-16./1.8*126.4;
//enum SM_MODE {SM_OFF, SM_CONTINUOUS_MOVE, SM_STEP_MOVE};
int SM_MODE = SM_OFF;
int SM_direction = 1;

void setFWheel(int ang) {
  int last_pos = fWheel.read();
  int pos = 0;
  if (last_pos < ang) {
    for (pos = last_pos; pos <= ang; pos += 1) { // goes from 0 degrees to 180 degrees
      // in steps of 1 degree
      fWheel.write(pos);              // tell servo to go to position in variable 'pos'
      delay(15);                       // waits 15ms for the servo to reach the position
    }
  }
  else {
    for (pos = last_pos; pos >= ang; pos -= 1) { // goes from 180 degrees to 0 degrees
      fWheel.write(pos);              // tell servo to go to position in variable 'pos'
      delay(15);                       // waits 15ms for the servo to reach the position
    }
  }
}
int setFilter(byte index) {
  if (index < 6) {
    setFWheel(fWheelAng[index]);
    return 1;
  }
  else {
    return 0;
  }
}



void fWheelTest() {
  int pos = 0;
  for (pos = 0; pos <= 180; pos += 1) // goes from 0 degrees to 180 degrees
  { // in steps of 1 degree
    fWheel.write(pos);              // tell servo to go to position in variable 'pos'
    delay(15);                       // waits 15ms for the servo to reach the position
  }
  for (pos = 180; pos >= 0; pos -= 1) // goes from 180 degrees to 0 degrees
  {
    fWheel.write(pos);              // tell servo to go to position in variable 'pos'
    delay(15);                       // waits 15ms for the servo to reach the position
  }
}

void parseInput() {
  int st, ang;

  if (inputString == "OFF") {
    stepper.disableOutputs();
    Serial.println(">OFF");
    SM_MODE = SM_OFF;
  }
  else if (inputString == "STOP") { /////////////////////////////////////////////////////////////////___+++__________
    stepper.stop();
    Serial.println(">STOP");
    SM_MODE = SM_STOP;
  }
  else if (inputString == "ON") {
    stepper.enableOutputs();
    Serial.println(">ON");
    SM_MODE = SM_ON;
  }
  
  else if (inputString == "CW" ) {
    stepper.enableOutputs();
    SM_MODE = SM_MOVE;
    SM_direction = 1;
    stepper.setSpeed(SM_direction*SM_SPEED);
    Serial.println(">CW");
  }
  else if (inputString == "CCW" ) {
    stepper.enableOutputs();
    SM_MODE = SM_MOVE;
    SM_direction = -1;
    stepper.setSpeed(SM_direction*SM_SPEED);
    Serial.println(">CCW");
  }
  
  else if (inputString == "REL=") {
    st = inputValue.toInt();
    stepper.enableOutputs();
   // stepper.setSpeed(SM_SPEED);
    stepper.move(round(st * SM_STEP_CALIBR));
    SM_MODE = SM_STEP_MOVE;
    Serial.print(">REL:");
    Serial.println(st);
  }
  else if (inputString == "ABS=") {
    st = inputValue.toInt();
    stepper.enableOutputs();
    //stepper.setSpeed(SM_SPEED);
    stepper.moveTo(round(st * SM_STEP_CALIBR));
    SM_MODE = SM_STEP_MOVE;
    Serial.print(">ABS:");
    Serial.println(st);
  }
  

  //^^^^^^^^^^^^^^^^   CCW   ^^^^^^^^^^^^^^^^^^
  else if (inputString == "HOME=" ) {
    stepper.enableOutputs();
    if (inputValue == "CW") {
      SM_MODE = SM_HOME_CW;
      SM_direction = 1;
      stepper.setSpeed(SM_direction*SM_SPEED);
    }
    if (inputValue == "CCW") {
      SM_MODE = SM_HOME_CCW;
      SM_direction = -1;
      stepper.setSpeed(SM_direction*SM_SPEED);
    }
    Serial.print(">HOME:");
    Serial.println(inputValue);
  }
  else if (inputString == "SPEED=" ) {
    int val = inputValue.toInt();
    if (val > 0 && val < SM_MAX_SPEED) {
      SM_SPEED = val;
      Serial.print(">SPEED:");
      Serial.println(SM_SPEED);
    }
  }
  else if (inputString == "ANGLE=" ) {
    int val = inputValue.toInt();
    angleCounter = val*ANGLE_CALIBR;
    stepper.setCurrentPosition(val*SM_STEP_CALIBR);
    Serial.print(">ANGLE:");
    Serial.println(angleCounter/ANGLE_CALIBR);

  }

  else if (inputString == "FW=") {
    st = inputValue.toInt();
    setFilter((byte)st);
    activeFilter = (byte)st;
    Serial.print(">FW:");
    Serial.println(st);
  }
  else if (inputString == "LASER=") {
    if (inputValue == "OFF") laserControl = LASER_SET_OFF;
    if (inputValue == "ON")  laserControl = LASER_SET_ON;

    Serial.print(">LASER:");
    Serial.println(inputValue);
  }

}
//vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv  SETUP  vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
//####################################################################################
void setup() {
  Serial.begin(9600);
  if (debugMode != 1)  {
    Serial.print(">INIT:");
    mouse.init();
    Serial.println("DONE");
  }
  Serial.println(">READY");

  // reserve 5 bytes for the inputString:
  inputString.reserve(100);

  fWheel.attach(FWHEEL_PIN);
  setFilter(activeFilter);


  // put your setup code here, to run once:
  stepper.setEnablePin(SM_ENABLE_PIN);
  stepper.setPinsInverted(0, 0, SM_INVERT_DIR);
  stepper.setMaxSpeed(SM_MAX_SPEED);
  stepper.setSpeed(SM_SPEED);
  stepper.enableOutputs();
}
//^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  SETUP  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
//####################################################################################
int r = 0;

void loop() {
  // put your main code here, to run repeatedly:
  if (millis() - serialPrevStepMillis >= serialOutputPeriod || inputString == "STATE?") {
    serialPrevStepMillis = millis();
    Serial.print("^A:");
    Serial.print(angleCounter/ANGLE_CALIBR);
    Serial.print("\tFW:");
    Serial.print(activeFilter);
    Serial.print("\tc:");
    Serial.print(stepper.currentPosition()/SM_STEP_CALIBR);
    Serial.print("\tZ:");
    Serial.println(optEndstop.read());
    //r = 1;
    //Serial.flush();
  }
  if (stringComplete) {

    parseInput();

    //if ((millis() - mouseReinitTimer > mouseReinit) && (rotationMode == SM_STOP || rotationMode == SM_OFF)) {
    //  mouseReinitTimer = millis();
    //  mouse.init();
      //mouse.init();
   //   Serial.println(">Reinit:Done");
   // }

    inputString = "";
    inputValue  = "";
    stringComplete = false;
  }

  if (millis() - angle_timer >= 35) {
    angle_timer = millis();
    if (debugMode != 1) {
      r = mouse.get_y();
      if (r < 10) {
        angleCounter += r;
      }
    }
    else {
      angleCounter = stepper.currentPosition();
    }
    //Serial.println(r);
    if (angleCounter > 360 * ANGLE_CALIBR) {
      angleCounter = 0;
      stepper.setCurrentPosition(0);
    }
    else if (angleCounter < 0) {
      angleCounter = 360 * ANGLE_CALIBR;
      stepper.setCurrentPosition(360*SM_STEP_CALIBR);
      }
    if (debugMode == 1) {
      Serial.print(stop_button.read());
      Serial.print("\t");
      Serial.print(cw_button.read());
      Serial.print("\t");
      Serial.println(ccw_button.read());
    }
  }
  if (SM_MODE == SM_MOVE) {
    stepper.setSpeed(SM_direction*SM_SPEED);
    stepper.runSpeed();
  }
  else if (SM_MODE == SM_HOME_CW || SM_MODE == SM_HOME_CCW) {
    stepper.runSpeed();
    if (optEndstop.read() == 1){
      stepper.stop();
      SM_MODE = SM_STOP;
      stepper.disableOutputs();
      angleCounter = 0;
      stepper.setCurrentPosition(0);
      }
  }
  else if (SM_MODE == SM_STEP_MOVE) {
    stepper.setSpeed(SM_SPEED);
    stepper.runSpeedToPosition();

  }
}
//#####################################################################################
bool value_aft_command = false;
void serialEvent() {

  while (Serial.available()) {
    // get the new byte:
    char inChar = (char)Serial.read();
    if (inChar == '\n') {
      stringComplete = true;
      value_aft_command = false;
      //wdt_reset();
    }
    else {
      if (value_aft_command) {
        inputValue += inChar;
      } else {
        inputString += inChar;
      }
    }
    if (inChar == '=') {
      value_aft_command = true;
    }
  }
}

