#ifndef  _H_WEBCLIENT_H_
#define  _H_WEBCLIENT_H_

int getMD5(const char *url, char **md5);
int getHeaderIndex(const char *ptr, int len);
void removeSubstring(char *s,const char *toremove);
int download(const char *urlToDownload , char *filename);

#endif  //_H_WEBCLIENT_H_