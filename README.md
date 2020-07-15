# Pow-Wow: A Dataset and Study on Collaborative Communication in Pommerman
This is a repository for the paper [Pow-Wow: A Dataset and Study on Collaborative Communication in Pommerman](http://example.com).  
This repository contains a set of tools that we used to collect dialogue and game-play data.

[[Project Website](https://takuma-ynd.github.io/pow-wow/)]

## Steps to launch a data collection enviornment
We assume there are three machines. One is for a central server that runs a game engine (Server), and other two are for clients that participants use to play the game (Client A and Client B).
It's also possible to only have 2 machines, where one of them works as the server and a client at the same time.

Pre-requisites:
* Python 3.6.0+
* Docker (used to run the enemy agents)

<!-- Pre-requisite: please install the modified Pommerman environment by following the instruction in [this repository](https://github.com/takuma-ynd/pommerman-network/tree/multi-play-over-network) -->
1. (Server, ClientA, ClientB): Install the modified Pommerman environment
```
$ git clone -b multi-play-over-network https://github.com/takuma-ynd/pommerman-network.git  ~/pommerman-network
$ cd ~/pommerman-network
$ pip install -U .
```
2. (Server): Pull the docker image for enemy agents  
`$ docker pull takumaynd/hakozakijunctions-notest`
3. (Server): Run `python message_server.py` on the server.  
This script delivers messages between chat consoles and synchronize them with game engine.
4. (Server): Run `python facilitator.py --client_ports 9000 9001`
5. (Client A): Forward a client port and messaging port (default: 8000) from server to client.  
For example, `ssh -L 9000:localhost:9000 -L 8000:localhost:8000 server.com`
6. (Client B): In a similar way, an example port forwarding is:  
`ssh -L 9001:localhost:9001 -L 8000:localhost:8000 server.com`
7. (Client A): Run `python client/client.py --port 9000` and open `client/htdocs/chat_9000.html` with a web browser  
The web page works as a text-based chat console whose information is synchronized with game engine.
8. (Client B): Run `python client/client.py --port 9001` and open `client/htdocs/chat_9001.html`

Once both players input username and click "Play", the game will automatically start.
## Brief description of how the system works
Coming soon...
