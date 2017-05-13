#include <stdio.h>
#include <stdlib.h>
#include "rplidar.h" //RPLIDAR standard sdk, all-in-one header

#include <math.h>

#include<string.h>    //strlen
#include<sys/socket.h>
#include<arpa/inet.h> //inet_addr
#include<unistd.h>    //write

#define PI 3.14159265

/*  druha mocnina cisla a */
int square(int a){
	return a*a;
}

/* zaokruhlenie cisla nahor */
double round_half_up(double num){
  return floor(num + 0.5);
}

/* inicializacia pola s velkostou num nastavenim vsetkych hodnot na nulu */
int* initialize_array(int* arr, int num){
	for(int i = 0; i<num; i++){
		arr[i] = 0;
	}
	return arr;
}

/* ------------------  LIDAR FUNCTIONS ----------------------*/

/* vypocet velkosti pola */
#ifndef _countof
#define _countof(_Array) (int)(sizeof(_Array) / sizeof(_Array[0]))
#endif

#ifdef _WIN32
#include <Windows.h>
#define delay(x)   ::Sleep(x)
#else
#include <unistd.h>
static inline void delay(_word_size_t ms){
    while (ms>=1000){
        usleep(1000*1000);
        ms-=1000;
    };
    if (ms!=0)
        usleep(ms*1000);
}
#endif

using namespace rp::standalone::rplidar;


/* skontroluje stav pripojenia lasera  */
bool checkRPLIDARHealth(RPlidarDriver * drv)
{
    u_result     op_result;
    rplidar_response_device_health_t healthinfo;


    op_result = drv->getHealth(healthinfo);
    if (IS_OK(op_result)) { // the macro IS_OK is the preperred way to judge whether the operation is succeed.
        printf("RPLidar health status : %d\n", healthinfo.status);
        if (healthinfo.status == RPLIDAR_STATUS_ERROR) {
            fprintf(stderr, "Error, rplidar internal error detected. Please reboot the device to retry.\n");
            // enable the following code if you want rplidar to be reboot by software
            // drv->reset();
            return false;
        } else {
            return true;
        }

    } else {
        fprintf(stderr, "Error, cannot retrieve the lidar health code: %x\n", op_result);
        return false;
    }
}


/* ----------- LASER PROCESSING ------------- */

#define limitDist 1000			//nastavenie hodnoty pre limitnu vzdialenost (v milimetroch)
#define limitRangeDist 500			//nastavenie hodnoty pre limitnu  vzdialenost rozsahu medzi konc. bodmi (v milimetroch)
/* definicia struktury pre rozsah uhla */
#define maxDistance 3000

struct range{
	int begin_angle;		//zaciatocny uhol rozsahu
	int begin_distance;		//vzdialenost v zaciatocnom uhle
	int end_angle;			//koncovy uhol rozsahu
	int end_distance;		//vzdialenost v koncovom uhle
} ;

/* vypocita pocet poli (hodnot) pre vysledny ramec - num_ranges predstavuje worst case scenario */
int count_num_of_fields(int num_ranges){		
	int num = (num_ranges * 4) + 1;	 //4x hodnoty pre rozsah uhla; 1 hodnota pre pocet nameranych rozsahov 
	return num;								
}

/* doplnenie ramca o nulove hodnoty */
void add_padding(int result[], int ranges_number, int fields_number){
	for(int i = ((ranges_number*4) + 1); i < fields_number; i++){
		result[i] = 0;
	}
}

/* pridanie rozsahu do pola rozsahov volnych uhlov;
   numRanges predstavuje pocet doposial nameranych volnych uhlov;
   (i - 1) - predstavuje koncovy uhol rozsahu*/
range* add_range(struct range *ranges, int *numRanges, int begin_angle, int i, int *laser_data){
	ranges[*numRanges].begin_angle = begin_angle;
	ranges[*numRanges].begin_distance = laser_data[begin_angle];
	ranges[*numRanges].end_angle = i - 1;
	ranges[*numRanges].end_distance = laser_data[i-1];
	*numRanges = *numRanges + 1;				//inkrementacia celkoveho poctu volnych uhlov
	return ranges;
}

/* kontrola prveho a posledneho rozsahu - ak sa prekryvaju, spoji tieto rozsahy do jedneho;
   prepis prveho - begin_angle/dist[0] -> begin_angle/dist[posledny_rozsah];
   odstranenie posledneho rozsahu */
range* check_first_last_angle(struct range* ranges, int *num_of_ranges, int numAngles){	
	if(*num_of_ranges > 1 && ranges[0].begin_angle == 0 && ranges[*num_of_ranges-1].end_angle == numAngles-1){
		ranges[0].begin_angle = ranges[*num_of_ranges-1].begin_angle;
		ranges[0].begin_distance = ranges[*num_of_ranges-1].begin_distance;
		*num_of_ranges = *num_of_ranges - 1;	//odpocitanie jedneho rozsahu z celkoveho poctu rozsahov 
	} 
	return ranges;
}

/* spracovanie vysledneho ramca - naplnenie hodnotami z pola rozsahov  */
int* process_frame(struct range* ranges, int num_of_ranges, int numAngles){
	int *frame_ranges = (int*) malloc(count_num_of_fields(numAngles) * sizeof(int));

	frame_ranges[0] = num_of_ranges;	//na nultu poziciu do vysledneho ramca zapise pocet celkovych rozsahov

	for(int i = 0; i < num_of_ranges; i++){		//prechod vsetkymi rozsahmi uhlov
		frame_ranges[i*4+1] = ranges[i].begin_angle;    //nasobenie 4 kvoli zapisovaniu styrom hodnotam definujucich
		frame_ranges[i*4+2] = ranges[i].begin_distance; //rozsah uhla -begin/end_distance, begin/end_angle
		frame_ranges[i*4+3] = ranges[i].end_angle;		//pripocitanie 1 kvoli umiestneniu celk. poctu rozsahov na 
		frame_ranges[i*4+4] = ranges[i].end_distance;	//prvu poziciu vo vyslednom ramci
	}
	return frame_ranges;
}

/* pomocna funkcia na vypis vysledneho ramca  */
void print_open_ranges(int *ranges, int fields_num){
	printf("\nVypisujem frame: ");
	int num_of_fields = count_num_of_fields(fields_num);
	for(int i = 0; i < num_of_fields; i++){
		printf("%d ", ranges[i]);
	}
}

/* vypocet vzdialenosti medzi krajnymi bodmi v rozsahu; 
   strany a a b predstavuju strany trojuholnika, ktore zvieraju uhol alfa;
   pomocou kosinusovej vety vieme dopocitat stranu c, leziacu oproti uhlu alfa;
   uhol alfa predstavuje rozdiel medzi pociatocnym a koncovym uhlom v rozsahu */
int count_distance_of_space(struct range range){
	
	int a = range.begin_distance;					//koncovy uhol rozsahu
	int b = range.end_distance;						//koncovy uhol rozsahu
	int alfa = range.end_angle - range.begin_angle;	//vypocet uhla alfa
	double x, ret, val, distance;

    val = PI / 180.0;
    ret = cos( alfa*val );							//pomocny vypocet pre cosinus alfa
	return sqrt(distance = square(a) + square(b) - 2*a*b*ret);	//kosinusova veta
}

/* filtrovanie rozsahov podla limitnej vzdialenosti medzi uhlami */
range* filter_ranges(range *ranges, int *num_of_ranges, int limit_space_distance){
	int dist, old_num_of_ranges = *num_of_ranges, num = 0;
	struct range *open_ranges = (struct range*)malloc(100*sizeof(range));	//alokacia noveho pola pre rozsahy, 
																		//ktore splnaju podmienku limitnej vzdialenosti
	for(int i = 0; i < old_num_of_ranges; i++){							//prechod vsetkymi rozsahmi
		dist = count_distance_of_space(ranges[i]);						//vypocet vzdialenosti medzi krajnymi bodmi v rozsahu
		if(dist > limit_space_distance){
			open_ranges[num] = ranges[i];								//ak splna, kopirovanie rozsahu do pola pre nove rozsahy
			num++;
		}
	}

	*num_of_ranges = num;												//prepis na novy pocet dostatocne velkych rozsahov
	return open_ranges;
}

/* pomocna funkcia na vypis rozsahov z pola struktur (aj do suboru)  */
void print_ranges(struct range* ranges, int numRanges, FILE *f){
	for(int i = 0; i < numRanges; i++){
		printf("Range #%d\nBegin angle = %d\nBegin Distance = %d\nEnd angle = %d\nEnd Ditstance = %d\n\Space = %d\n----------\n", 
			i+1, ranges[i].begin_angle, ranges[i].begin_distance, ranges[i].end_angle, ranges[i].end_distance, 
			count_distance_of_space(ranges[i]));
		fprintf(f,"Range #%d\nBegin angle = %d\nBegin Distance = %d\nEnd angle = %d\nEnd Ditstance = %d\n\Space = %d\n----------\n", 
			i+1, ranges[i].begin_angle, ranges[i].begin_distance, ranges[i].end_angle, ranges[i].end_distance, 
			count_distance_of_space(ranges[i]));
	}
}

/*  vyhodnotenie dat 
	int *laser_data - udaje ziskane z lasera 
	int numAngles - pocet meranych uhlov
	FILE *f - subor pre pomocne vypisy, pre testovacie ucely */
int* evaluate_data(int *laser_data, int numAngles, FILE *f){
	int begin_angle = 0, end_angle = 0, numRanges = 0, begin_distance = laser_data[0], previous_bigger = 0;
	struct range *ranges = (struct range*)malloc(180*sizeof(range));
	
	for(int i = 0; i < numAngles; i++){
		fprintf(f, "%d: %d cm\n", i, laser_data[i]);
		if(laser_data[i] < limitDist){					//ak je aktualna vzdialenost mensia ako limitna

			if(previous_bigger == 1){					//ohranicuj len ak predosly uhol je vacsia ako limitny uhol
			//	printf("%d: %d -> mensi -> ohranicujem range (%d-%d)\n",i, laser_data[i],begin_angle, end_angle);
				ranges = add_range(ranges,&numRanges,begin_angle, i, laser_data);  //vytvorenie a pridanie rozsahu do pola
				previous_bigger = 0;					//nastavenie flagu pre predosly uhol na nulu
			}			

			begin_angle = i + 1;						//do begin_angle prirad dalsi uhol
			begin_distance = laser_data[i+1];			//do begin_distance prirad vzdialenost z dalsieho uhla
			previous_bigger = 0;						//nastavenie flagu pre predosly uhol na nulu
		} else {										//ak je vzdialenost vacsia ako limitna
			previous_bigger = 1;						//nastavenie flagu pre predosly uhol na jedna
		}
		end_angle = i;									//koncovy uzol nastav na aktualny uhol
	}

	if(begin_angle < numAngles){						//posledny uhol je treba osobitne pridat - iba v pripade, ak 
														//posledny rozsah konci poslednych uhlom (numAngles)
		ranges = add_range(ranges,&numRanges,begin_angle, end_angle+1, laser_data); 
	}

	ranges = check_first_last_angle(ranges, &numRanges, numAngles);	//osetrenie prveho a posledneho rozsahu
	print_ranges(ranges, numRanges, f);
	ranges = filter_ranges(ranges, &numRanges, limitRangeDist);		//filtrovanie rozsahov podla vzdial. konc. bodov
	print_ranges(ranges, numRanges, f);
	int *frame_ranges = process_frame(ranges, numRanges, numAngles); //zapis hodnot do vysledneho ramca
	print_open_ranges(frame_ranges, numRanges);
	return frame_ranges;

}

/* konvert ramca na string */
char* convert_to_string(int *frame_with_ranges, int num_of_fields){
	int index = 0;
	char *message;
	message = (char*) malloc(num_of_fields * sizeof(char));

	for(int i = 0; i < num_of_fields; i++){
		index += sprintf(&message[index], "%d", frame_with_ranges[i]);
	}
	printf("Mess = %s\n",message);
	return message;
}

char* convert_int_to_bytes(int *array_of_int, int array_size){
	char* bytes;
	bytes = (char*) malloc (array_size * sizeof(char) + 2);
	bytes[0] = 0;
	bytes[1] = 5;
	bytes[2] = (char)array_of_int[0];
	
	for(int i = 1; i < array_size; i++){
		bytes[i*2 - 1 + 2] = (array_of_int[i] >> 8) & 0xFF;
		bytes[i*2 + 2] = (array_of_int[i]) & 0xFF;
	}

	return bytes;
}

#include <signal.h>
bool ctrl_c_pressed;
void ctrlc(int)
{
    ctrl_c_pressed = true;
}

int main(int argc, const char * argv[]) {
    const char * opt_com_path = NULL;
    _u32         opt_com_baudrate = 115200;
    u_result     op_result;
	int *measured_data;
	int *final_frame;

	int sock;
    struct sockaddr_in server;
    char message[1000] , server_reply[2000];
	
	FILE *f = fopen("output.txt", "w");

	if (f == NULL)
	{
		printf("Error opening file!\n");
		getchar();
	}

    // read serial port from the command line...
    if (argc>1) opt_com_path = argv[1]; // or set to a fixed value: e.g. "com3" 

    // read baud rate from the command line if specified...
    if (argc>2) opt_com_baudrate = strtoul(argv[2], NULL, 10);


    if (!opt_com_path) {
#ifdef _WIN32
        // use default com port
        opt_com_path = "\\\\.\\com3";
#else
        opt_com_path = "/dev/ttyUSB0";
#endif
    }

    // create the driver instance
    RPlidarDriver * drv = RPlidarDriver::CreateDriver(RPlidarDriver::DRIVER_TYPE_SERIALPORT);
    
    if (!drv) {
        fprintf(stderr, "insufficent memory, exit\n");
        exit(-2);
    }


    // make connection...
    if (IS_FAIL(drv->connect(opt_com_path, opt_com_baudrate))) {
        fprintf(stderr, "Error, cannot bind to the specified serial port %s.\n"
            , opt_com_path);
        goto on_finished;
    }

    rplidar_response_device_info_t devinfo;
    op_result = drv->getDeviceInfo(devinfo);

    if (IS_FAIL(op_result)) {
        fprintf(stderr, "Error, cannot get device info.\n");
        goto on_finished;
    }
	
    // check health...
    if (!checkRPLIDARHealth(drv)) {
        goto on_finished;
    }
   
	drv->startMotor();
    // start scan...
    drv->startScan();

    // fetech result and print it out...
    while (1) {
        rplidar_response_measurement_node_t nodes[360*2];
        size_t   count = _countof(nodes);

        op_result = drv->grabScanData(nodes, count);

        if (IS_OK(op_result)) {
            drv->ascendScanData(nodes, count);
			printf("3-count = %d, %d\n", (int) count, count);
			measured_data = (int*) malloc(count*sizeof(int));	//alokacia pola pre vysledny ramec
			measured_data = initialize_array(measured_data,360);	//inicializacia pola pre vysledny ramec
			int angle, prev = -1, index = 0;
            for (int pos = 0; pos < (int)count ; ++pos) {
				/* VYPIS UHLOV DO KONZOLY */
                printf("%s theta-la: %03.2f (%d) Dist: %08.2f Q: %d \n", 
                    (nodes[pos].sync_quality & RPLIDAR_RESP_MEASUREMENT_SYNCBIT) ?"S ":"  ", 
                    (nodes[pos].angle_q6_checkbit >> RPLIDAR_RESP_MEASUREMENT_ANGLE_SHIFT)/64.0f, pos, 
                    nodes[pos].distance_q2/4.0f,
                    nodes[pos].sync_quality >> RPLIDAR_RESP_MEASUREMENT_QUALITY_SHIFT);
				/* VYPIS UHLOV DO SUBORU */
				fprintf(f,"%s thetaaa: %03.2f (%d) Dist: %08.2f Q: %d \n", 
                    (nodes[pos].sync_quality & RPLIDAR_RESP_MEASUREMENT_SYNCBIT) ?"S ":"  ", 
                    (nodes[pos].angle_q6_checkbit >> RPLIDAR_RESP_MEASUREMENT_ANGLE_SHIFT)/64.0f, pos, 
                    nodes[pos].distance_q2/4.0f,
                    nodes[pos].sync_quality >> RPLIDAR_RESP_MEASUREMENT_QUALITY_SHIFT);
				
				/* zaokruhlenie hodnoty pre uhol na cele cislo - metoda round half up */
				angle = (int) (round_half_up((nodes[pos].angle_q6_checkbit >> RPLIDAR_RESP_MEASUREMENT_ANGLE_SHIFT)/64.0f));
				fprintf(f, "angle = %d", angle);
				if(prev != angle){			//pridanie len jedneho uhla (napr. 76.8 -> 77, 77.2 -> 77 - prida len prvy)
					fprintf(f, "davam do %d", index);
					printf("Quality bit = %d\n", nodes[pos].sync_quality >> RPLIDAR_RESP_MEASUREMENT_QUALITY_SHIFT);
					if(nodes[pos].sync_quality >> RPLIDAR_RESP_MEASUREMENT_QUALITY_SHIFT < 30){
						measured_data[angle] = maxDistance;
					} else {
						measured_data[angle] = nodes[pos].distance_q2/4.0f;
					}
					prev = angle;	
					
				}
				fprintf(f, "\n");
            }
			count = 360;
			final_frame = evaluate_data(measured_data, count, f);		//vyhodnotenie nameranych udajov
        }	

	char* message2 = convert_int_to_bytes(final_frame, (final_frame[0]*4)+1);
	
	printf("# header = %d %d\n", message2[0], message2[1]);
	printf("# of ranges-ss = %d\n", message2[2]);
	for(int q = 1; q < final_frame[0]*4+1; q++){
		printf("byte = %d %d\n", message2[q*2-1+2], message2[q*2+2]);
	}
  /* ODOSLANIE SPRAVY */

     //Create socket
    sock = socket(AF_INET , SOCK_STREAM , 0);
    if (sock == -1)
    {
        printf("Could not create socket");
    }
     
    server.sin_addr.s_addr = inet_addr("192.168.237.1");
    server.sin_family = AF_INET;
    server.sin_port = htons( 80 );
 
    //Connect to remote server
    if (connect(sock , (struct sockaddr *)&server , sizeof(server)) < 0)
    {
        perror("connect failed. Error");
		break;
        //return 1;
    }
     
    puts("Connected\n");
     
    //keep communicating with server
   // while(1)
  //  {
      //   break;     
        //Send some data
        if( send(sock , message2 , (final_frame[0]*8)+1 , 0) < 0)
        {
            puts("Send failed");
			break;
            //return 1;
        }
         
        //Receive a reply from the server
       /* if( recv(sock , server_reply , 2000 , 0) < 0)
        {
            puts("recv failed");
            break;
        }*/
	//	break;
   // }
     
    close(sock);
	

		char c = getchar();
        if (c == 'q'){ 
			break;		
		}
    }

    drv->stop();
    drv->stopMotor();
	fclose(f);
    // done!
on_finished:
    RPlidarDriver::DisposeDriver(drv);

    return 0;
}

