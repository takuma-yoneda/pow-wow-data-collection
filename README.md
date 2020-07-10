# Pow-Wow: A Dataset and Study on Collaborative Communication in Pommerman
This is a repository for the paper [Pow-Wow: A Dataset and Study on Collaborative Communication in Pommerman](http://example.com).  
This repository contains a set of tools that we used to collect dialogue and game-play data.

## Steps to launch a data collection enviornment
We assume there are three machines. One is for a central server that runs a game engine, and other two are for clients that participants use to play the game.
It's also possible to only have 2 machines, where one of them works as the server and a client at the same time.

Pre-requisite: please install the modified Pommerman environment by following the instruction in [this repository](https://github.com/takuma-ynd/pommerman-network/tree/multi-play-over-network)

1. (Server): Run `python message_server.py ` on the server.  
This helps delivering messages between chat consoles and synchronize them with game engine.
2. (Server): Run `python facilitator.py --client_ports 9000 9001`
3. (Client A): Forward a client port and messaging port (default: 8000) from server to client.  
For example, `ssh -L 9000:localhost:9000 -L 8000:localhost:8000 server.com`
4. (Client B): In a similar way, an example port forwarding is:  
`ssh -L 9001:localhost:9001 -L 8000:localhost:8000 server.com`
5. (Client A): Run `python client/client.py --port 9000` and open `client/htdocs/chat_9000.html` with a web browser  
The web page works as a text-based chat console whose information is synchronized with game engine.
6. (Client B): Run `python client/client.py --port 9001` and open `client/htdocs/chat_9001.html`

## Brief description of how the system works
Coming soon...
