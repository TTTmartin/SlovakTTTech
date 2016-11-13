#include <SPI.h>
#include <Ethernet.h>
#include <EthernetUDP.h>

// premenne, ktore zavisia od umiestnenia Arduina (ktore je to koleso)
#define macNumber 0x01
#define arduinoNumber '1'

#define masterRpiIp "192.168.1.200"
#define pwmMotorPin 9
#define neutralMotorLevel 128


const unsigned int localPort = 5000;
byte mac[] = { 0x22, 0x22, 0x22, 0x00, 0x00, macNumber };
String ackSuccess = "10X11021";

char packetBuffer[UDP_TX_PACKET_MAX_SIZE];
EthernetUDP Udp;


void setup() {
  analogWrite(pwmMotorPin, neutralMotorLevel);
  ackSuccess[2] = arduinoNumber;
    
  Serial.begin(9600);
  Serial.println("Program has started setup");

  if (Ethernet.begin(mac) == 0) {
    Serial.println("Failed to configure Ethernet using DHCP");
    for(;;);
  }

  Udp.begin(localPort);
  Serial.println("Program has ended setup succesfully");
  
  String header = "10" + (String) arduinoNumber + "1100";
  IPAddress localIp = Ethernet.localIP();
  String notify = header + (String)localIp[0] + '.' + (String)localIp[1] + '.' + (String)localIp[2] + '.' + (String)localIp[3]; 
  Serial.println(notify);
  Udp.beginPacket(masterRpiIp, localPort);
  Udp.print(notify);
  Udp.endPacket();
  Serial.println("Sent notify udp packet");
}


void loop() {
  int packetSize = Udp.parsePacket();
  if (packetSize) {
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

    Udp.read(packetBuffer, UDP_TX_PACKET_MAX_SIZE);

    if ((packetBuffer[0] == '0') && (packetBuffer[1] == '1') && (packetBuffer[2] == '1') && (packetBuffer[3] == '0') && (packetBuffer[4] == arduinoNumber) && (packetBuffer[5] == '0') && (packetBuffer[6] == '1')) {
      Serial.println("It is instruction");
      String wheelSpeed = "";

      for (int i = 0; i < 3; i++) {
        wheelSpeed = wheelSpeed + (String) packetBuffer[7 + i];
      }

      int wheelSpeedInt = wheelSpeed.toInt();
      Serial.println(wheelSpeed.toInt());

      if ((wheelSpeedInt >= 0) && (wheelSpeedInt <= 255)) {
         analogWrite(pwmMotorPin, wheelSpeedInt);
      }
      
    }
    Serial.println("Content:");
    Serial.println(packetBuffer);

    Udp.beginPacket(Udp.remoteIP(), Udp.remotePort());
    Udp.print(ackSuccess);
    Udp.endPacket();
  }
}

