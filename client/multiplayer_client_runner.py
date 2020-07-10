'''This is the basic docker agent runner'''
import abc
import logging
import json
from pommerman import constants
import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS

LOGGER = logging.getLogger(__name__)
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

class MultiPlayerClientRunner(metaclass=abc.ABCMeta):
    """Abstract base class to implement Docker-based agent"""

    def __init__(self):
        self._done = False
        self._is_ready_to_start = False
        self._is_on_game = False

    @abc.abstractmethod
    def act(self, observation, action_space):
        """Given an observation, returns the action the agent should"""
        raise NotImplementedError()

    def run(self, host="0.0.0.0", port=10080):
        """Runs the agent by creating a webserver that handles action requests."""
        app = Flask(self.__class__.__name__)
        CORS(app)

        @app.route("/action", methods=["POST"])
        def action(): #pylint: disable=W0612
            '''handles an action over http'''
            data = request.get_json()
            observation = data.get("obs")
            observation = json.loads(observation)

            observation['teammate'] = constants.Item(observation['teammate'])
            for enemy_id in range(len(observation['enemies'])):
                observation['enemies'][enemy_id] = constants.Item(observation['enemies'][enemy_id])
            observation['position'] = tuple(observation['position'])
            observation['board'] = np.array(observation['board'], dtype=np.uint8)
            observation['bomb_life'] = np.array(observation['bomb_life'], dtype=np.float64)
            observation['bomb_blast_strength'] = np.array(observation['bomb_blast_strength'], dtype=np.float64)

            action_space = data.get("action_space")
            action_space = json.loads(action_space)
            action = self.act(observation, action_space)
            return jsonify({"action": action})

        @app.route("/init_agent", methods=["POST"])
        def init_agent(): #pylint: disable=W0612
            '''initiates agent over http'''
            data = request.get_json()
            id = data.get("id")
            id = json.loads(id)
            game_type = data.get("game_type")
            game_type = constants.GameType(json.loads(game_type))
            env_info = data.get("env_info")
            env_info = json.loads(data.get("env_info"))
            self.init_agent(id, game_type,  env_info)

            # NOTE: return hostname to the server?  --> not needed??
            # return jsonify({"success": True, "agent_port": port})
            return jsonify(success=True)

        @app.route("/notify_obs", methods=["POST"])
        def notify_obs(): #pylint: disable=W0612
            '''handles an action over http'''
            data = request.get_json()
            observation = data.get("obs")
            waiting = data.get("waiting")
            observation = json.loads(observation)
            waiting = json.loads(waiting)

            self.visualize_obs(observation, waiting)
            # HACK: notify_obs is only called at the beginning and end.
            # if it was beginning, waiting=True, False if not.
            # if observation['step_count'] == 0:
            #     self.visualize_obs(observation)
            # else:
            #     self.visualize_obs(observation, waiting=False)
            return jsonify({"success": True})

        @app.route("/die", methods=["GET"])
        def die(): #pylint: disable=W0612
            '''Requests destruction of any created objects'''
            self.die()
            return jsonify(success=True)

        @app.route("/shutdown", methods=["POST"])
        def shutdown(): #pylint: disable=W0612
            '''Requests destruction of any created objects'''
            self.shutdown()
            return jsonify(success=True)

        @app.route("/episode_end", methods=["POST"])
        def episode_end(): #pylint: disable=W0612
            '''Info about end of a game'''
            data = request.get_json()
            reward = data.get("reward")
            reward = json.loads(reward)
            self.episode_end(reward)
            return jsonify(success=True)

        @app.route("/ping", methods=["GET"])
        def ping(): #pylint: disable=W0612
            '''Basic agent health check'''
            if not self.check_if_done():
                return jsonify(success=True)
            else:
                return jsonify(success=False)

        @app.route("/is_on_game", methods=["GET"])
        def is_on_game(): #pylint: disable=W0612
            '''Whether the game has started or not'''
            return jsonify(result=self._is_on_game, success=True)

        # facilitator uses this to see if they can start the game.
        @app.route("/is_ready_to_start", methods=["GET"])
        def is_ready_to_start(): #pylint: disable=W0612
            '''notify facilitator that the client is ready'''
            return jsonify(result=self._is_ready_to_start, success=True)

        # this will be triggered by the client web browser.
        @app.route("/ready_to_start", methods=["GET"])
        def ready_to_start(): #pylint: disable=W0612
            '''Set the flag to show the client is ready'''
            self._is_ready_to_start = True
            return jsonify(success=True)

        # this will be triggered by the client web browser.
        @app.route("/unready_to_start", methods=["GET"])
        def unready_to_start(): #pylint: disable=W0612
            '''Set the flag to show the client is ready'''
            self._is_ready_to_start = False
            return jsonify(success=True)

        LOGGER.info("Starting agent server on port %d", port)
        app.run(host=host, port=port)
