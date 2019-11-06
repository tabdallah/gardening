#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <wiringPi.h>

#define LED_TOP_1 1
#define LED_TOP_2 4
#define LED_OUTER 5 
#define FAN 6
#define TI_DELAY_MS (3600 * 1000)
void sigint(int a)
{
	digitalWrite(LED_TOP_1, HIGH);
	digitalWrite(LED_TOP_2, HIGH);
	digitalWrite(LED_OUTER, HIGH);
	digitalWrite(FAN, HIGH);
	printf("\nGoodbye\n");
	exit(EXIT_SUCCESS);
}

int main(void)
{
	signal(SIGINT, sigint);
	wiringPiSetup() ;
	pinMode(LED_TOP_1, OUTPUT) ;
	pinMode(LED_TOP_2, OUTPUT) ;
	pinMode(LED_OUTER, OUTPUT) ;
	pinMode(FAN, OUTPUT) ;

	for (;;)
	{
		// Alternate top  light every hour to avoid burning out
		digitalWrite(LED_TOP_1, LOW);
		digitalWrite(LED_TOP_2, HIGH);
		digitalWrite(LED_OUTER, LOW);
		digitalWrite(FAN, LOW);
		delay(TI_DELAY_MS);
		digitalWrite(LED_TOP_1, HIGH);
		digitalWrite(LED_TOP_2, LOW);
		delay(TI_DELAY_MS);
	}
	return 0;
}
