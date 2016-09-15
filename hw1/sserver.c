/*
Sources referred:
http://www.programminglogic.com/example-of-client-server-program-in-c-using-sockets-and-tcp/
  
A special thanks to Milad for his valueable inputs.   
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <netinet/in.h>
#include <limits.h>
#include "host2ip.h"
#include "webclient.h"

#define	DEBUG_MSG         0
#define MAX_PATH          260
#define	MAX_URL_LENGTH		2048
#define MAX_BUFFER_LEN		4096
#define MAX_RESPONSE_LEN  1048576

int main(int argc, char *argv[])
{
	int iRet;
	int iCounter;
	int newSocket;
	int localSocket;
	struct stat st = {0};	
	socklen_t addressSize;	
	char url[MAX_URL_LENGTH];
	char buffer[MAX_BUFFER_LEN];	
	struct sockaddr_in serverAddress;
	struct sockaddr_storage serverStorage;
	
	int port;
	char ip[MAX_PATH];
  char filename[MAX_PATH];
	char hostname[HOST_NAME_MAX];
	
	//
	//	Parse  command line args.
	//
	if (3 != argc)
	{
		printf("\nInvalid arguments!!!");
		printf("\nUsage: <executable> -p <Port number>\n");
		return (1);
	}

	for (iRet = 0; iRet < argc; iRet++)
	{
		if (0 == (strcmp(argv[iRet], "-p")))
		{
			port = atoi(argv[iRet + 1]);
			
			#if DEBUG_MSG
			printf("\nPORT(%d)\n", port);
			#endif
		}
	}
	
	//
	//	Create socket.
	//
	localSocket = socket(AF_INET, SOCK_STREAM, 0);
	if (-1 == localSocket)
	{
		printf("\nsocket() FAILED. Error(%s).\n", strerror(errno));
		return(1);
	}

	//
	//	Configure settings of the server address struct.
	//
	serverAddress.sin_family = AF_INET;
	serverAddress.sin_port = htons(port);
	gethostname(hostname, sizeof hostname);
	get_ip(hostname, ip);
	
	#if DEBUG_MSG
	printf("\n%s resolved to %s\n" , hostname , ip); 
	#endif
	
	serverAddress.sin_addr.s_addr = inet_addr(ip);
	memset(serverAddress.sin_zero, '\0', sizeof serverAddress.sin_zero);

  //
  //  This is added so that we can reuse existing open ports.
  //
  /*int yes = 1;
  if (setsockopt(localSocket, SOL_SOCKET, SO_REUSEADDR, &yes, sizeof(int)) == -1) {
      printf("setsockopt failed");
      return(1);
  }*/

	//
	//	Bind the socket to the address.
	//
	iRet = bind(localSocket, (struct sockaddr *)&serverAddress, sizeof(serverAddress));
	if (-1 == iRet)
	{
		printf("\nbind() FAILED. Error(%s).\n", strerror(errno));
		close(localSocket);
		return(1);	
	}
	
	//
	//	Listen on the socket.
	//
	if(listen(localSocket,5)==0)
	{
		printf("\nWaiting for clients...\n");
	}
	else
	{
		printf("\nlisten() FAILED. Error(%s).\n", strerror(errno));
		close(localSocket);
		return(1);
	}

	//
	//	Accept the incoming connection.
	//
	iCounter = 1;
	while(1)
	{
		addressSize = sizeof serverStorage;
		newSocket = accept(localSocket, (struct sockaddr *)&serverStorage, &addressSize);
		if (-1  == newSocket)
		{
			printf("\naccept() FAILED. Error(%s).\n", strerror(errno));
			close(localSocket);
			return(1);
		}
		
		printf("\nA client has connected\n");
		
		iRet = recv(newSocket, url, 2048, 0);
		if (-1 == iRet)
		{
			printf("\nrecv() FAILED. Error(%s).\n", strerror(errno));
			close(newSocket);
			close(localSocket);
			return(1);	
		}
		
		#if DEBUG_MSG
		printf("URL received: %s\n", url);
		#endif
		
		//
		//	Create file.
		//
		//sprintf(buffer, "GET %s >> %d", url, iCounter);
    iRet = download(url, filename);
    if (0 != iRet)
    {
        printf("\ndownload failed\n");
        close(localSocket);
        return 1;
    }		
 		
		//
		//	Send message.
		//
		sprintf(buffer, "%s", filename);
		stat(buffer, &st);
		sprintf(buffer, "File %s saved. Size=%d", filename, st.st_size);
    printf("\n%s\n", buffer);
		iRet = send(newSocket, buffer, (strlen(buffer) + 1), 0);	
		if (-1 == iRet)
		{
			printf("\nsend() FAILED. Error(%s).\n", strerror(errno));
			close(localSocket);
			return 1;	
		}
		
		iCounter++;
    printf("\nWaiting for clients...\n");		
	}
	
	close(newSocket);
	close(localSocket);	
	return 0;
}
