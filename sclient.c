/*
Sources referred:
http://www.programminglogic.com/example-of-client-server-program-in-c-using-sockets-and-tcp/
*/
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <limits.h>
#include "host2ip.h"

#define	MAX_URL_LENGTH		2048
#define MAX_BUFFER_LEN		1024
#define DEBUG_MSG         1

int main(int argc, char *argv[])
{
	int iRet;
	int clientSocket;
	socklen_t addressSize; 
	char buffer[MAX_BUFFER_LEN];
	struct sockaddr_in serverAddress;
	
  int port;
  char ip[260];
  char hostname[HOST_NAME_MAX];
  char url[MAX_URL_LENGTH];
  
	//
	//	Parse  command line args.
	//
	if (7 != argc)
	{
		printf("\nInvalid arguments!!!");
		printf("\nUsage: <executable> -p <Port number> -h <hostname> -u <URL>\n");
		return (1);
	}
	
  for (iRet = 0; iRet < argc; iRet++)
  {
    if (0 == strcmp("-p", argv[iRet]))
    {
      port = atoi(argv[iRet + 1]);
    }
    else if (0 == strcmp("-h", argv[iRet]))
    {
      strcpy(hostname, argv[iRet + 1]);
    }
    else if (0 == strcmp("-u", argv[iRet]))
    {
      strcpy(url, argv[iRet + 1]);
    }    
  }
 
	if ( (strlen(url) > (MAX_URL_LENGTH - 1)) || (strlen(hostname) > (HOST_NAME_MAX - 1)) )
	{
		printf("\nToo long parameters!!!");
		return(1);
	}
	
  #if DEBUG_MSG
  printf("\nPort(%d)", port);
  printf("\nHostname(%s)", hostname);
  printf("\nURL(%s)\n", url);
  #endif
 
	//
	//	Create a socket.
	//
	clientSocket = socket(PF_INET, SOCK_STREAM, 0);
	if (-1 == clientSocket)
	{
		printf("\nsocket() FAILED. Error(%s).\n", strerror(errno));
		return(1);
	}
	
  get_ip(hostname, ip);
  
	serverAddress.sin_family = AF_INET;
	serverAddress.sin_port = htons(port);
  serverAddress.sin_addr.s_addr = inet_addr(ip);  
	//serverAddress.sin_addr.s_addr = inet_addr(argv[1]);
	memset(serverAddress.sin_zero, '\0', sizeof serverAddress.sin_zero);  

	//
	//	Connect to server.
	//
	addressSize = sizeof serverAddress;
	iRet = connect(clientSocket, (struct sockaddr *) &serverAddress, addressSize);
	if (-1 == iRet)
	{
		printf("\nconnect() FAILED. Error(%s).\n", strerror(errno));
		close(clientSocket);
		return(1);	
	}	

  printf("\nConnected to the server at port (%d) host (%s)\n", port, hostname);

	//
	//	Send URL to server.
	//
	iRet = send(clientSocket, url, (strlen(url) + 1), 0);	
	if (-1 == iRet)
	{
		printf("\nsend() FAILED. Error(%s).\n", strerror(errno));
		close(clientSocket);
		return(1);	
	}	

	//
	//	Receive message.
	//
	iRet = recv(clientSocket, buffer, MAX_BUFFER_LEN, 0);
	if (-1 == iRet)
	{
		printf("\nrecv() FAILED. Error(%s).\n", strerror(errno));
		close(clientSocket);
		return(1);	
	}
		
	printf("\nData received: %s\n", buffer);   
	close(clientSocket);

	return 0;
}
