#include <SPI.h>
#include <Servo.h>
#include <Ethernet2.h>

// constants which are unique for every Arduino
// Arduino number used for identification
#define ARDUINO_NUMBER '4'

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
// unique MAC address of Arduino
byte mac[] = { 0x90, 0xA2, 0xDA, 0x10, 0xCF, 0xD3 };
// message sent for RPI when Arduino sets new motor speed succesfully (X is changed later)
String ackSuccess = "10X11021";

char packetBuffer[UDP_TX_PACKET_MAX_SIZE];
EthernetUDP Udp;
Servo motor;

// function runs only once when Arduino starts
void setup() {
  // set motor not to move
  motor.attach(PWM_MOTOR_PIN); //800 a 2200 treba vyladit
  motor.write(NEUTRAL_MOTOR_LEVEL);
  ackSuccess[2] = ARDUINO_NUMBER;
    
  Serial.begin(9600);
  Serial.println("Program has started setup");

  // waiting for IP address from DHCP on RPI
  if (Ethernet.begin(mac) == 0) {
    Serial.println("Failed to configure Ethernet using DHCP");
    for(;;)
      ;
  }
  
  Udp.begin(localPort);
  Serial.println("Program has ended setup succesfully");

  // notify RPI about obtained IP address from DHCP
  String header = "10" + (String) ARDUINO_NUMBER + "1100";
  IPAddress localIp = Ethernet.localIP();
  String notify = header + (String)localIp[0] + '.' + (String)localIp[1] + '.' + (String)localIp[2] + '.' + (String)localIp[3]; 
  Serial.println(notify);
  Udp.beginPacket(MASTER_RPI_IP, localPort);
  Udp.print(notify);
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
    if ((packetBuffer[0] == '0') && (packetBuffer[1] == '1') && (packetBuffer[2] == '1') && (packetBuffer[3] == '0') && (packetBuffer[4] == ARDUINO_NUMBER) && (packetBuffer[5] == '0') && (packetBuffer[6] == '1')) {
      Serial.println("Instruction to set motor speed for this Arduino has arrived");
      String wheelSpeed = "";

      // parse new wheel speed from packet
      for (int i = 7; i < sizeof(packetBuffer); i++) {
        wheelSpeed = wheelSpeed + (String) packetBuffer[i];
      }
      
      int wheelSpeedInt = wheelSpeed.toInt();
      Serial.println(wheelSpeedInt);

      // if new wheel speed is valid, it will be set to motor
      if ((wheelSpeedInt >= 0) && (wheelSpeedInt <= 180)) {
        motor.write(wheelSpeedInt);
        Serial.println("Speed was set");
        // send message about success speed update
        Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
        Udp.print(ackSuccess);
        Udp.endPacket();
      }
    }
    memset(packetBuffer, 0, sizeof(packetBuffer));
  }
}
