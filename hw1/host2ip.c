/*
Sources referred:
https://srishcomp.wordpress.com/2013/01/15/a-c-program-to-get-ip-address-from-the-hostname/
*/

#include <stdio.h> 
#include <string.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <errno.h>
#include <netdb.h> 
#include <arpa/inet.h>

int get_ip(char * hostname , char* ip) 
{
	int i;
	struct hostent *hostEntry;     
	struct in_addr **addressList;     

	if ((hostEntry = gethostbyname(hostname)) == NULL)     
	{
		herror("gethostbyname");         
	 	return 1;
	}
	     
	addressList = (struct in_addr **)hostEntry->h_addr_list;
	for(i = 0; addressList[i] != NULL; i++)
	{
		strcpy(ip , inet_ntoa(*addressList[i]) );
		return 0;
	}
	
	return 1;
}