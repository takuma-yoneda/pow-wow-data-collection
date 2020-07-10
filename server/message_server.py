'''This is the basic docker agent runner'''
import os
import logging
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import hashlib
import argparse
import urllib.parse

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

def get_readable_timestamp():
    timestamp = datetime.timestamp(datetime.now())
    readable_timestamp = str(datetime.fromtimestamp(timestamp))
    return readable_timestamp


def save_json(json_info, path, overwrite=False):
    if os.path.exists(path) and not overwrite:
        raise RuntimeError("file {} already exists".format(path))

    with open(path, 'w') as f:
        f.write(json.dumps(json_info, sort_keys=True, indent=4))


class MessagingServer():
    """Abstract base class to implement Docker-based agent"""

    def __init__(self):
        # self._messages = {'-1':['this_is_val1', 'this_is_val2']}
        self._messages = {}
        self._current_timestep = 0
        self._parent_logdir = 'logs'
        self._logdir = None
        self._messaging_enabled = True
        self._states = []
        self._is_on_game = False

    def _maybe_mklogdir(self):
        directory = os.path.join(self._parent_logdir, self._logdir)
        if not os.path.exists(directory):
            LOGGER.info('creating logdir {}'.format(directory))
            os.makedirs(directory)

    def save_log(self, json_info):
        assert self._logdir is not None
        count = "{0:0=3d}".format(self._current_timestep)
        suffix = count + '.json'
        directory = os.path.join(self._parent_logdir, self._logdir)
        self._maybe_mklogdir()

        path = os.path.join(directory, suffix)
        save_json(json_info, path)

    def add_message(self, username, message, agent_ip="0"):
        # create a list if it does not exist
        if str(self._current_timestep) not in self._messages:
            self._messages[str(self._current_timestep)] = []

        # refer to: https://www.programiz.com/python-programming/datetime/timestamp-datetime
        timestamp = datetime.timestamp(datetime.now())
        # hash_object = hashlib.md5(b'Hello World')
        hash_object = hashlib.md5(' '.join((username, message, str(timestamp))).encode('utf-8'))
        _hash = hash_object.hexdigest()
        readable_timestamp = str(datetime.fromtimestamp(timestamp))
        message_obj = {"username": username, "message": message, "timestamp": readable_timestamp, "hash": _hash, "agent_ip":agent_ip}
        self._messages[str(self._current_timestep)].append(message_obj)
        # print(self._messages)

    def return_messages(self):
        self._messages['current_timestep'] = self._current_timestep
        return self._messages

    def disable_messaging(self):
        self._messaging_enabled = False

    def run(self, host="0.0.0.0", port=8000):
        """Runs the agent by creating a webserver that handles action requests."""
        app = Flask(self.__class__.__name__)
        CORS(app)  # required to get cross-domain access done.

        @app.route("/initialize", methods=["GET"])
        def initialize():
            '''
            NOTE: the Pommerman model is the client to use this address.
            This is called by facilitator when a new game starts.
            The server saves this info and put when step occured in message
            '''
            # initialize state of message_server
            LOGGER.info('initializing messages and timestep...')
            self.__init__()
            return jsonify({"success":True})

        @app.route("/start_logging", methods=["POST"])
        def start_logging():
            '''
            NOTE: the Pommerman model is the client to use this address.
            This is called by facilitator when a new game starts.
            The server saves this info and put when step occured in message
            '''
            data = request.get_json()
            self.__init__()
            self._is_on_game = True

            self._logdir = json.loads(data.get('logdir'))
            LOGGER.info('setting logdir to: {}'.format(self._logdir))
            self._maybe_mklogdir()

            LOGGER.info('Ready for a new game.')
            return jsonify({"success":True})


        @app.route("/initial_obs", methods=["POST"])
        def initial_obs():
            # process the received state
            state_info = {}
            data = request.get_json()
            for key, val in data.items():
                state_info[key] = json.loads(val)

            state_info['timestamp'] = get_readable_timestamp()

            # add messages to the previous state
            self._states.append(state_info)

            self._current_timestep = state_info['step_count']

            # if any human control agent is dead, just disable the communication.
            # agents = state_info['agents']
            # if any([state_info['is_human_controlled'][str(i)] and not agent['is_alive'] for i, agent in enumerate(agents)]):
            #     self.disable_messaging()

            # self._is_on_game = True  # NOTE: check the condition where this func is called!! (NOTE: Also need to detect shutdown:gameend)
            return jsonify({"success":True})


        @app.route("/step", methods=["POST"])
        def step():
            '''
            NOTE: the Pommerman model is the client to use this address.
            This is called when the game steps.
            The server saves this info and put when step occured in message
            '''
            # add messages to the previous state
            prev_state = self._states[-1]
            prev_state['messages'] = self.return_messages()  # include the all messages

            # save the previous state & messages
            print("SAVING LOG!!")
            # print(prev_state)
            assert self._logdir is not None
            self.save_log(prev_state)

            # process the received state
            state_info = {}
            data = request.get_json()
            for key, val in data.items():
                state_info[key] = json.loads(val)

            # add timestamp and append to saved states
            state_info['timestamp'] = get_readable_timestamp()
            self._states.append(state_info)

            self._current_timestep = state_info['step_count']

            # if any human control agent is dead, just disable the communication.
            # agents = state_info['agents']
            # if any([state_info['is_human_controlled'][str(i)] and not agent['is_alive'] for i, agent in enumerate(agents)]):
            #     self.disable_messaging()

            if state_info['done']:
                # if the game is over, save current state, as well!
                self._is_on_game = False
                curr_state = self._states[-1]
                curr_state['messages'] = prev_state['messages']  # no additional messages can exist
                self.save_log(curr_state)


            return jsonify({"success":True})


        @app.route("/final_info", methods=["POST"])
        def final_info():
            result = request.get_json()
            result = json.loads(result)

            directory = os.path.join(self._parent_logdir, self._logdir)
            # process the received state
            path = os.path.join(directory, 'result.json')
            save_json(result, path)
            return jsonify({"success":True})


        @app.route("/envinfo", methods=["POST"])
        def envinfo():
            '''
            NOTE: the Pommerman model is the client to use this address.
            This is called when the game steps.
            The server saves this info and put when step occured in message
            '''
            # TODO: implement the following..
            envinfo = {}
            data = request.get_json()
            for key, val in data.items():
                envinfo[key] = json.loads(val)

            assert self._logdir is not None
            print("Saving envinfo at {}".format(self._logdir))
            self._maybe_mklogdir()
            directory = os.path.join(self._parent_logdir, self._logdir)
            path = os.path.join(directory, 'envinfo.json')
            save_json(envinfo, path)
            return jsonify({"success":True})

        @app.route("/disable_messaging", methods=["GET"])
        def disable_messaging():
            '''disable messaging.
            It should be called when a teammate agent dies.
            '''
            self.disable_messaging()
            self.add_message('**GAME MASTER**', 'Communication is disabled because a player agent died.')
            self.add_message('**GAME MASTER**', 'You cannot send any message after this.')


        @app.route("/message", methods=["POST"])
        def message():
            '''process sent message and return all previous messages'''
            data = request.get_json()
            # message = data.get("message")
            # message = json.loads(message)
            username = data.get('username')
            agent_ip = data.get('agent_ip')
            message = urllib.parse.unquote(data.get('message'))  # decode the sequence
            # print("before", data.get('message'), "decoded:", message)

            # add message only if messaging is enabled
            if self._messaging_enabled:
                self.add_message(username, message, agent_ip)

            # print('send message:\n{}'.format(data))
            # print()

            return jsonify({"messages": self.return_messages()})

        @app.route("/get_messages", methods=["GET"])
        def get_messages():
            '''fetch messages. return all messages archived in this server'''
            # print('messages:\n{}'.format(self.return_messages()))
            return jsonify({"messages": self.return_messages()})


        @app.route("/end_game", methods=["GET"])
        def end_game():
            '''just to notify the game is end'''
            self._is_on_game = False
            return jsonify(success=True)

        @app.route("/is_on_game", methods=["GET"])
        def is_on_game():
            print('is_on_game:', self._is_on_game)
            return jsonify(result=self._is_on_game)

        # TEMP: temporal function for experiments
        @app.route("/increment", methods=["GET"])
        def increment():
            '''exists only for testing. increment current_timestep'''
            self._current_timestep += 1
            print("increment the current timestep to {}".format(str(self._current_timestep)))
            return jsonify({"NULL":None})

        LOGGER.info("Starting agent server on port %d", port)
        app.run(host=host, port=port)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--host', default='0.0.0.0')
    args = parser.parse_args()

    messaging_server = MessagingServer()
    messaging_server.run(host=args.host, port=args.port)
