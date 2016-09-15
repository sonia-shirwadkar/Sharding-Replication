/*
Sources reffered:
http://www.binarytides.com/socket-programming-c-linux-tutorial/
http://stackoverflow.com/questions/4833347/removing-substring-from-a-string

A big thanks to Milad for helping me figure out the correct way to parse out
the HTTP header and also for clarifying some basic conceptual doubts.
*/

#include <stdio.h>
#include <string.h>    //strlen
#include <sys/socket.h>
#include <arpa/inet.h> //inet_addr
#include <unistd.h>
#include "host2ip.h"
#include "webclient.h"

#define DEBUG_MSG      0
#define MAX_PATH       260
#define MAX_URL_LEN    2048
#define RESPONSE_LEN   307200//1048576
#define HTTP_HDR_END   "\r\n\r\n"

int download(const char *urlToDownload , char *filename)
{
    int iRet;
    FILE *fp;
    ssize_t n;
    int index;      
    char *ptr;    
    char *host;
    char *resource;
    int isHeaderRead;
    char ip[MAX_PATH];
    int socket_desc;
    struct sockaddr_in server;
    char message[MAX_PATH] , server_reply[RESPONSE_LEN];
    char url[MAX_URL_LEN];
    //char filename[MAX_PATH];
    
    strcpy(url, urlToDownload);
    removeSubstring(url, "http://");
    removeSubstring(url, "https://");
    
    host = strtok_r(url, "/", &resource);
    get_ip(host, ip);
    
    #if DEBUG_MSG 
    printf("\nIP (%s)\n", ip);
    #endif
    
    // 
    //  Create socket
    //
    socket_desc = socket(AF_INET , SOCK_STREAM , 0);
    if (socket_desc == -1)
    {
        printf("Could not create socket");
        return 1;
    }
         
    server.sin_addr.s_addr = inet_addr(ip);
    server.sin_family = AF_INET;
    server.sin_port = htons( 80 );
 
    //
    //  Connect to remote server
    //
    if (connect(socket_desc , (struct sockaddr *)&server , sizeof(server)) < 0)
    {
        printf("connect error");
        return 1;
    }

    #if DEBUG_MSG     
    printf("Connected\n");
    #endif
    
    //
    //  Check if file has already been downloaded
    //
    iRet = getMD5(urlToDownload, &filename);
    if (0 != iRet)
    {
        printf("getMD5 failed");
        return 1;
    }
    
    iRet = access(filename, F_OK);
    if (0 == iRet)
    {
        printf("\nFILE (%s) already found. Returning the same...\n", filename);
        return 0;
    }
   
    // 
    //Send some data
    //
    sprintf(message, "GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n", resource, host);
    
    #if DEBUG_MSG
    printf("\nSending (%s)\n", message);
    #endif
    
    if (write(socket_desc, message, (strlen(message) + 1)) < 0)
    {
        printf("Send failed");
        return 1;
    }
    
    #if DEBUG_MSG
    printf("Data Sent\n");
    #endif

    //
    //Receive a reply from the server
    //
    isHeaderRead = 0;
    index = 0;
    
    fp = fopen(filename, "wb");
    if (NULL == fp)
    {
      printf("fopen failed");
      return 1;
    }

    //while ((n = read(socket_desc, server_reply, RESPONSE_LEN)) > 0)
    while (1)
    {
        index = 0;
        memset(server_reply, 0, sizeof(server_reply));        
        n = read(socket_desc, server_reply, sizeof(server_reply));
        if (n <= 0)
        {
          break;
        }
        
        //
        //  Parse out header.
        //
        if (!isHeaderRead)
        {
          index = getHeaderIndex(server_reply, n);
          if (-1 != index)
          {
            isHeaderRead = 1;
          }
        }//if (!isHeaderRead)

        if (isHeaderRead)
        {
            fwrite(&server_reply[index], 1, (n - index), fp);
        }
    }//while
    
    fclose(fp);
    close(socket_desc);    

    return 0;
}


int getMD5(const char *url, char **md5)
{
    FILE *fp;
    char *ptr;
    char message[MAX_PATH];

    sprintf(message, "echo -n %s | md5sum", url);
    //printf("\n%s\n", message);
    fp = popen(message, "r");
    if (NULL == fp)
    {
      printf("popen failed");
      return 1;
    }
    
    fputs(message, fp);
    fgets(message, MAX_PATH, fp);
    fclose(fp);

    ptr = strtok(message, " ");
    strcpy(*md5, ptr);
    
    #if DEBUG_MSG
    printf("\nMD5: %s\n", *md5);
    #endif    

    return 0;
}


void removeSubstring(char *s,const char *toremove)
{
  if( s=strstr(s,toremove) )
    memmove(s, s+strlen(toremove), 1+strlen(s+strlen(toremove)));
}


int getHeaderIndex(const char *ptr, int len)
{
    int i;
    int state;
    
    state = 0;
    for (i = 0; i < len; i++)
    {
        switch (ptr[i])
        {
            case '\r':
              if (state == 0)
              {
                state = 1;
              }
              else if (state == 2)
              {
                state = 3;
              }
              else
              {
                state = 0;
              }
              break;
              
            case '\n':
              if (state == 1)
              {
                state = 2;
              }
              else if (state == 3)
              {
                state = 4;
              }
              else
              {
                state = 0;
              }
              break;
              
             default:
               state = 0;
               break;                           
        }//switch
        
        if (state == 4)
        {
            i++;
            //printf("\nHeader Found. Header length (%d)\n", i);
            return i;
        }
    }
    
    return -1;
}