#include <stdio.h>
#include <stdlib.h>

#define numAngles 10
#define limitDist 100

void print_open_ranges(int ranges[], int fields_num){

	for(int i = 0; i < fields_num; i++){
		printf("%d ", ranges[i]);
	}
}

int count_num_of_fields(){		/*function counts maximum fields (numbers) can be in frame; 
							number of angles is divided by 2 (worst scenario - every second angle is less 
							then limited distance, then multiplied by 4 (each range contains 4 values) and added 1 -
							for value number of ranges */

	int num = (numAngles * 2) + 1; // ((# of angels / 2) * 4) + 1 
	printf("Number of fields = %d\n",num);
	return num;								
}

void add_padding(int result[], int ranges_number, int fields_number){
	for(int i = ((ranges_number*4) + 1); i < fields_number; i++){
		result[i] = 0;
	}
}

void evaluate_data(int laser_data[numAngles]){
	int fields_num = count_num_of_fields();
	int *result = (int*)malloc(fields_num*sizeof(int));
	int begin = 0, end = 0, numRanges = 0, begin_angle = 0;
	

	for(int i = 0; i < numAngles; i++){
		if(laser_data[i] < limitDist){			//if actual distance is less than limit distance
			end = i;							//rewrite end angle with actual number of angle
			if(begin == end){					//if previous angle is also under limit distance, skip it
				printf("%d: %d -> mensi -> neohranicujem kvoli predoslemu (%d-%d)\n",i, laser_data[i],begin, end);	
			} else {
				printf("%d: %d -> mensi -> ohranicujem range (%d-%d)\n",i, laser_data[i],begin, end);
				result[(numRanges*4)+1] = begin;		
				result[(numRanges*4)+2] = begin_angle;
				result[(numRanges*4)+3] = i-1;
				result[(numRanges*4)+4] = laser_data[i-1];
				numRanges++;
			}			
			begin = i + 1;
			begin_angle = laser_data[i+1];
		} else {
			printf("%d: %d\n",i, laser_data[i]);
			end = i;
		}
	}

	if(begin < numAngles){
		result[(numRanges*4)+1] = begin;
		result[(numRanges*4)+2] = begin_angle;
		result[(numRanges*4)+3] = end;
		result[(numRanges*4)+4] = laser_data[end];
		numRanges++;
	}

	result[0]=numRanges;
	add_padding(result, numRanges, fields_num);
	print_open_ranges(result, fields_num);
}



int main(){
	int arr[numAngles] = {30,160,160,170,50,30,120,10,50,50};
	evaluate_data(arr);
	getchar();
	return 0;

}


