#include <stdio.h>
#include <string.h>
#include <math.h>

#define PI 3.14159265
#define ACCURACY 0.00004
#define MAP_LENGTH 29


//map node structure
struct nav_point{  
	long double latitude;
    long double longitude;
};

nav_point nav_map [29] = 
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

//
// Function for finding closest node to map
// @latitude, actual latitude
// @longtitude, actual longtitude
//

int find_closest_point(double latitude, double longitude)
{
  int min_index = 0;
  long double min= sqrt(pow(longitude - nav_map[0].longitude,2)+pow(latitude - nav_map[0].latitude,2));

  for(int i=1;i<MAP_LENGTH;i++)
  {
	long double dist= sqrt(pow(longitude - nav_map[i].longitude,2)+pow(latitude - nav_map[i].latitude,2));
	if(min > dist)
	{
		min=dist;
		min_index = i;
	}
  }
  return min_index;
}

//
// Function for degree calculation based on quadrant
// @x, difference between x-axis values of start and end node
// @y, difference between y-axis values of start and end node
// @degree, degree calculated for first quadrant
//
int degree_based_on_quadrant(double x,double y,double degree)
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


//
// Function to calculate relative degree of next node, current compass degree is reprezented as zero on vehicle
// @compass, actual compass degree
// @direction, degree to next node
//
double calculate_relative_degree(double compass, double direction)
{
	if((direction - compass) >= 0){
		return direction - compass;
	}
	else{
		return 360 - compass + direction;
	}
}

//
// Function to calculate direction degree between two nodes
// @start, start node
// @end, end node
//
double calculate_compass_degree(nav_point start,nav_point end)
{
	double x = end.latitude-start.latitude;
	double y = end.longitude-start.longitude;
	return degree_based_on_quadrant(x,y,atan(abs(x)/abs(y)) * (180/PI));
}

//
// Function to determine if actual node is in defined range of end node
// @actual, actual node
// @dest, end node
//
bool is_in_node(nav_point actual,nav_point dest)
{
	if(sqrt(pow(actual.longitude - dest.longitude,2)+pow(actual.latitude - dest.latitude,2)) <= ACCURACY)
	{
		return true;
	}
	return false;
}

int main()
{
	struct nav_point test_node;
	test_node.latitude = 48.153452;
	test_node.longitude = 17.071082;

	long double compass = 100.56;

	int i = find_closest_point(test_node.latitude,test_node.longitude);

	printf("Closest point: %lf %lf\n",nav_map[i].latitude, nav_map[i].longitude);
	printf("Compass degree: %lf\n",calculate_compass_degree(test_node,nav_map[i]));
	double relative = calculate_relative_degree(compass, calculate_compass_degree(test_node,nav_map[i]));
	int help = (int)relative;
	printf("relative: %lf",relative );
	printf("relative int: %d\n",help );
	printf("%d",is_in_node(nav_map[0],nav_map[2]));

	/*
	start
	collect gps data
	collect compass data
	int node_number = find_closest_point(test_node.latitude,test_node.longitude);

	while(1)
	{
		collect gps data
		collect compass data
		if(is_in_node(actual_gps,nav_map[node_number])){ //if i reached node move to the next
			node_number++;
		}
		int relative_degree = int(calculate_relative_degree(compass, calculate_compass_degree(test_node,nav_map[node_number])));
		send degree
	}
	*/
	getchar();
	return 0;
}