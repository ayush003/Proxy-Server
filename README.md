# HTTP Proxy Server using Python

An HTTP proxy server implemented via Python socket programming with caching, blacklisting, authentication functionality. GET and POST requests are handled.

- Receives the request from client and passes it to the server after necessary parsing.
- Threaded proxy server thus able to handle many requests at the same time.
- If one file is requested above the threshold number of times in certain time period, then proxy server caches that request and cached files are accessed by - securing mutex locks to maintain integrity.
- Cache has limited size, so if the cache is full and proxy wants to store another response then it removes the least recently asked cached response. Cache limit can be set by setting up the constant in proxy.py file.
- Certain servers (their ports) are blacklisted so that normal users can't access it. Blacklisted servers are stored in CIDR format in blacklist.txt file.
- Special users can access blacklisted servers. They must be authenticated by HTTP authentication. HTTP authentication is done by proxy. Usernames and passwords of priviledged users are stored in username_password.txt file.
## How to run
### Proxy
Specify proxy port while running proxy `python proxy.py`.
### Server
`python server.py 20101` to run server on port 20101
### Client
curl request can be sent as client request and get the response. 
`curl --request GET --proxy 127.0.0.1:20100 --local-port 20001-20010 127.0.0.1:20101/1.data` 

This request will ask 1.data file from server 127.0.0.1/20101 by GET request via proxy 127.0.0.1/20100 using one of the ports in range 20001-20010 on localhost. 
`curl --request GET -u username:password --proxy 127.0.0.1:20100 --local-port 20001-20010 127.0.0.1:30000/1.data`
