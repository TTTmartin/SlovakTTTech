#include <SPI.h>
#include <Wire.h>
#include <SoftwareSerial.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_HMC5883_U.h>
#include <Ethernet2.h>

// GPS accuracy for reaching desired map point
#define ACCURACY 0.00004

// Number of map points
#define MAP_LENGTH 29

// Arduino number used for identification
#define ARDUINO_NUMBER 5

// MAC address of Arduino
byte mac[] = { 0x90, 0xA2, 0xDA, 0x10, 0xAB, 0xCD };

// IP address of master Raspberry Pi (RPI)
#define MASTER_RPI_IP "192.168.1.200"

// port used for communication between Arduino and RPI
const unsigned int localPort = 5000;
// message sent for RPI when Arduino obtains new GPS and compass data and calculates relative angle (last two zeros will be changed)
byte notifyMessage[] = {1, 0, ARDUINO_NUMBER, 1, 1, 0, 6, 0, 0};

// map node structure
struct nav_point{  
  float latitude;
  float longitude;
};

// Routing points
nav_point nav_map [MAP_LENGTH] = 
{
  {48.153818, 17.071139},
  {48.153770, 17.071133},
  {48.153708, 17.071127},
  {48.153647, 17.071123},
  {48.153591, 17.071139},
  {48.153526, 17.071138},
  {48.153446, 17.071131},
  {48.153390, 17.071136}, 
  {48.153356, 17.071175}, //zatacka
  {48.153337, 17.071242},
  {48.153333, 17.071314},
  {48.153329, 17.071431},
  {48.153327, 17.071520},
  {48.153323, 17.071625},
  {48.153327, 17.071707},
  {48.153303, 17.071755}, //zatacka
  {48.153247, 17.071780},
  {48.153184, 17.071804},
  {48.153151, 17.071852},
  {48.153110, 17.071903},
  {48.153060, 17.071918},
  {48.153006, 17.071913},
  {48.152942, 17.071909},
  {48.152882, 17.071902},
  {48.152808, 17.071898},
  {48.152757, 17.071932},
  {48.152746, 17.072027},
  {48.152744, 17.072122},
  {48.152740, 17.072197}
};

// Assign a unique ID to this sensor at the same time
Adafruit_HMC5883_Unified mag = Adafruit_HMC5883_Unified(12345);

// Configure software serial port
SoftwareSerial GPS(2,3); 

// Message type which we need from GPS
// Whole desired message looks like this: 
// $GPGGA,053740.000,2503.6319,N,12136.0099,E,1,08,1.1,63.8,M,15.2,M,,0000*64
char messageTypeDesired[] = {'G', 'P', 'G', 'G', 'A'};
char msgChar;
EthernetUDP Udp;
int node_number = 0;
bool wasVehicleLocated = false;


// Initialises board
void setup() 
{
  GPS.begin(9600);
  Serial.begin(9600);

  // waiting for IP address from DHCP on RPI
  if (Ethernet.begin(mac) == 0) {
    Serial.println("Failed to configure Ethernet using DHCP");
    for(;;);
  }
    
  Udp.begin(localPort);

  // Initialise the sensor
  if(!mag.begin()) {
    Serial.println("Ooops, no magnetic sensor detected ... Check your wiring!");
    while(1);
  }
}

// Runs in loop forever
void loop() 
{
  // Create magnetic sensor event
  sensors_event_t event; 
  mag.getEvent(&event);

  // Hold the module so that Z is pointing 'up' and you can measure the heading with x&y
  // Calculate heading when the magnetometer is level, then correct for signs of axis
  float heading = atan2(event.magnetic.y, event.magnetic.x);

  // Once you have your heading, you must then add your 'Declination Angle', which is the 'Error' of the magnetic field in your location
  // Find yours here: http://www.magnetic-declination.com/
  // Convert your declination angle from degrees to radians
  // float declinationAngle = -0.086393798;
  // heading += declinationAngle;

  // Correct for when signs are reversed
  if(heading < 0) {
    heading += 2*PI;
  }

  // Check for wrap due to addition of declination
  if(heading > 2*PI) {
    heading -= 2*PI;
  }

  // Convert radians to degrees
  float headingDegrees = heading * 180/M_PI;  

  // If there are any data from GPS, read it
  if (GPS.available() > 0 ) {
    if(msgChar != '$') {
      while(GPS.available() < 1);
      msgChar = GPS.read();
    }
    
    // Check for beginning of new message
    if(msgChar == '$') {
      msgChar == '\0';
      
      // Gets message type
      char messageType[5];
      for(int i = 0; i < 5; i++) {
        messageType[i] = '\0';
        while(GPS.available() < 1);
        messageType[i] = GPS.read();
      }
      
      // Determines whether it is my desired message
      bool isMyMessage = true;
      for(int i = 0; i < 5; i++) {
        if (messageType[i] != messageTypeDesired[i]) {
          isMyMessage = false;
        }       
      }

      if (isMyMessage){
        int index = 0;
        
        // Fill variable with end of string character
        char myMessage[100];
        for(int i = 0; i < 100; i++) {
          myMessage[i] = '\0';
        }

        // Fill variable with message content
        while(GPS.available() < 1);
        while((msgChar = GPS.read()) != '$'){
          while(GPS.available() < 1);
          myMessage[index] = msgChar;
          index++;        
        }

        // Parse message
        strtok(myMessage, ",");
        String lat = strtok(NULL, ",");
        strtok(NULL, ",");
        String lon = strtok(NULL, ",");
        strtok(NULL, ",");

        if(lat == "0") {
          Serial.println("There is no satellite connection");
          Serial.print("Car heading: "); 
          Serial.print(headingDegrees);
          Serial.println(" degrees");         
        } else {
          // Parse string to float
          // Arduino stores float proprerly but Serial.println can print it only with two decimal precision
          float latD = lat.substring(0,2).toFloat();
          float latM = lat.substring(2).toFloat() / 60;
          float lat = latD + latM;
          float lonD = lon.substring(1,3).toFloat();
          float lonM = lon.substring(3).toFloat() / 60;
          float lon = lonD + lonM; 

          Serial.print("Latitude: ");
          Serial.println(lat, 10);
          Serial.print("Longitude: ");
          Serial.println(lon, 10);
          Serial.print("Car heading: "); 
          Serial.print(headingDegrees);
          Serial.println(" degrees");

          nav_point actual;
          actual.longitude = lon;
          actual.latitude = lat;

          // Gets node number after car starts to receive GPS signal
          if (!wasVehicleLocated) {
            node_number = find_closest_point(actual);
          }
          wasVehicleLocated = true;

          //if i reached node move to the next
          if(is_in_node(actual ,nav_map[node_number])){ 
            node_number++;
          }
      
          int relative_degree = int(calculate_relative_degree(headingDegrees, calculate_compass_degree(actual, nav_map[node_number])));
          Serial.print("Next point index: ");
          Serial.println(node_number);
          Serial.print("Relative angle to next point: ");
          Serial.print(relative_degree);
          Serial.println(" degrees");

          // send notify message to RPI
          if (relative_degree > 255) {
            notifyMessage[7] = 1;
            notifyMessage[8] = (relative_degree - 256); 
          } else {
            notifyMessage[7] = 0;
            notifyMessage[8] = relative_degree;
          }

          Udp.beginPacket(MASTER_RPI_IP, localPort);
          Udp.write(notifyMessage, sizeof(notifyMessage));
          Udp.endPacket();
        }
      } else {
        // This is not my desired message so iterate to next message
        while(GPS.available() < 1);
        while((msgChar = GPS.read()) != '$'){
          while(GPS.available() < 1);
        }
      }
    } 
  }
}


// Function for finding closest node to map
// @actual, actual point
int find_closest_point(nav_point actual)
{
  int min_index = 0;
  float minimum= sqrt(pow(actual.longitude - nav_map[0].longitude,2)+pow(actual.latitude - nav_map[0].latitude,2));

  for(int i=1;i<MAP_LENGTH;i++)
  {
  float dist= sqrt(pow(actual.longitude - nav_map[i].longitude,2)+pow(actual.latitude - nav_map[i].latitude,2));
  if(minimum > dist)
  {
    minimum=dist;
    min_index = i;
  }
  }
  return min_index;
}


// Function for degree calculation based on quadrant
// @x, difference between x-axis values of start and end node
// @y, difference between y-axis values of start and end node
// @degree, degree calculated for first quadrant
int degree_based_on_quadrant(float x, float y, float degree)
{  
  if(x>=0 && y>=0)
  {
    return 90 - degree;
  }else if(x>=0 && y<=0) //2.nd sector
  {
    return 270 + degree;
  }else if(x<=0 && y<=0) //3.rd sector
  {
    return 270-degree;
  }else //4.th sector
  {
    return 90+degree;
  }
}


// Function to calculate relative degree of next node, current compass degree is reprezented as zero on vehicle
// @compass, actual compass degree
// @directionValue, degree to next node
float calculate_relative_degree(float compass, float directionValue)
{
  if((directionValue - compass) >= 0){
    return directionValue - compass;
  }
  else{
    return 360 - compass + directionValue;
  }
}


// Function to calculate direction degree between two nodes
// @start, start node
// @end, end node
float calculate_compass_degree(nav_point start,nav_point endPoint)
{
  float x = endPoint.latitude-start.latitude;
  float y = endPoint.longitude-start.longitude;

  if (y == 0) {
    return degree_based_on_quadrant(x, y, (1.570796 * (180/PI)));
  } else {
    double atanVar = x/y;

    if(atanVar < 0) {
      atanVar = atanVar * -1;
    }    
    return degree_based_on_quadrant(x, y, (atan(atanVar) * (180/PI)));  
  }
}


// Function to determine if actual node is in defined range of end node
// @actual, actual node
// @dest, end node
bool is_in_node(nav_point actual,nav_point dest)
{
  if(sqrt(pow(actual.longitude - dest.longitude,2)+pow(actual.latitude - dest.latitude,2)) <= ACCURACY)
  {
    return true;
  }
  return false;
}
