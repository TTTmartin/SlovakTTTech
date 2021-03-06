#include <SPI.h>
#include <Servo.h>
#include <Ethernet2.h>


// Arduino number (choices are ARDUINO_1, ARDUINO_2, ARDUINO_3, ARDUINO_4)
#define ARDUINO_1


// constants which are unique for every Arduino
#ifdef ARDUINO_1
  // Arduino number used for identification
  #define ARDUINO_NUMBER 1
  // MAC address of Arduino
  byte mac[] = { 0x90, 0xA2, 0xDA, 0x10, 0xCF, 0xDF };
#endif

#ifdef ARDUINO_2
  #define ARDUINO_NUMBER 2
  byte mac[] = { 0x90, 0xA2, 0xDA, 0x10, 0xCF, 0x5A };
#endif

#ifdef ARDUINO_3
  #define ARDUINO_NUMBER 3
  byte mac[] = { 0x90, 0xA2, 0xDA, 0x10, 0xCF, 0xD3 };
#endif

#ifdef ARDUINO_4
  #define ARDUINO_NUMBER 4
  byte mac[] = { 0x90, 0xA2, 0xDA, 0x10, 0xCF, 0xBF };
#endif

// fixed constants
// IP address of master Raspberry Pi (RPI)
#define MASTER_RPI_IP "192.168.1.200"
// output pin on Arduino which is used to control the motor
#define PWM_MOTOR_PIN 9
// if this value is set to PWM_MOTOR_PIN, the motor will not move
#define NEUTRAL_MOTOR_LEVEL 90

// global variables
// port used for communication between Arduino and RPI
const unsigned int localPort = 5000;
// message sent for RPI when Arduino obtains IP address from DHCP (255s will be changed)
byte notifyMessage[] = {1, 0, ARDUINO_NUMBER, 1, 1, 0, 0, 255, 255, 255, 255};
// message sent for RPI when Arduino sets new motor speed succesfully
byte ackSuccessMessage[] = {1, 0, ARDUINO_NUMBER, 1, 1, 0, 2, 1};

char packetBuffer[UDP_TX_PACKET_MAX_SIZE];
EthernetUDP Udp;
Servo motor;

// function runs only once when Arduino starts
void setup() {
  // set motor not to move
  motor.attach(PWM_MOTOR_PIN); //800 a 2200 treba vyladit
  motor.write(NEUTRAL_MOTOR_LEVEL);
    
  Serial.begin(9600);
  Serial.println("Program has started setup");

  // waiting for IP address from DHCP on RPI
  if (Ethernet.begin(mac) == 0) {
    Serial.println("Failed to configure Ethernet using DHCP");
    for(;;);
  }
    
  Udp.begin(localPort);
  Serial.println("Program has ended setup succesfully");

  // notify RPI about obtained IP address from DHCP
  IPAddress localIp = Ethernet.localIP();
  for (int i = 0; i < 4; i++) {
    notifyMessage[i + 7] = localIp[i];
    Serial.print(localIp[i], DEC);
    if (i < 3) {
      Serial.print(".");
    }
  }
  Serial.println(" END");
  
  Udp.beginPacket(MASTER_RPI_IP, localPort);
  Udp.write(notifyMessage, sizeof(notifyMessage));
  Udp.endPacket();
  Serial.println("Sent notify udp packet");
}

// function runs in loop
void loop() {
  int packetSize = Udp.parsePacket();
  
  // if there is a packet which is not empty, it will process it
  if (packetSize) {
    // debug information
    Serial.print("Received packet of size ");
    Serial.println(packetSize);
    Serial.print("From ");
    IPAddress remote = Udp.remoteIP();
    for (int i = 0; i < 4; i++) {
      Serial.print(remote[i], DEC);
      if (i < 3) {
        Serial.print(".");
      }
    }
    Serial.print(", port ");
    Serial.println(Udp.remotePort());
    // debug information end

    Udp.read(packetBuffer, UDP_TX_PACKET_MAX_SIZE);

    Serial.println("Content:");
    Serial.println(packetBuffer);

    // if condition pass instruction with new wheel speed is for this Arduino
    if ((packetBuffer[0] == 0) && (packetBuffer[1] == 1) && (packetBuffer[2] == 1) && (packetBuffer[3] == 0) && (packetBuffer[4] == ARDUINO_NUMBER) && (packetBuffer[5] == 0) && (packetBuffer[6] == 1)) {
      Serial.println("Instruction to set motor speed for this Arduino has arrived");
      
      // parse new wheel speed from packet
      int wheelSpeedInt = (unsigned byte) packetBuffer[7];
      Serial.println(wheelSpeedInt);

      // if new wheel speed is valid, it will be set to motor
      if ((wheelSpeedInt >= 0) && (wheelSpeedInt <= 180)) {
        motor.write(wheelSpeedInt);
        Serial.println("Speed was set");
        // send message about success speed update
        Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
        Udp.write(ackSuccessMessage, sizeof(ackSuccessMessage));
        Udp.endPacket();
      }
    }
    memset(packetBuffer, 0, sizeof(packetBuffer));
  }
}
