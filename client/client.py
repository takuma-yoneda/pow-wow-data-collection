"""Implementation of a simple deterministic agent using Docker."""

import click
import numpy as np
from pommerman import agents
from pommerman import graphics
from pommerman import constants
import pyglet

from multiplayer_client_runner import MultiPlayerClientRunner
import argparse
import time

# Suppress messages
# import logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

# keypad control codes
K_PREFIX = '\x1b'
K_RT = '[C'
K_LF = '[D'
K_UP = '[A'
K_DN = '[B'


def get_action(key, control='both'):
    act = None

    # arrows key
    if control in ['both', 'arrows']:
        if key == K_PREFIX + K_RT  : act = constants.Action.Right.value
        if key ==  K_PREFIX + K_LF : act = constants.Action.Left.value
        if key ==  K_PREFIX + K_UP : act = constants.Action.Up.value
        if key ==  K_PREFIX + K_DN : act = constants.Action.Down.value
        if key == ' ': act = constants.Action.Bomb.value

    # wasd key
    if control in ['both', 'wasd']:
        if key == 'd': act = constants.Action.Right.value
        if key == 'a': act = constants.Action.Left.value
        if key == 'w': act = constants.Action.Up.value
        if key == 's': act = constants.Action.Down.value
        if key == 'e': act = constants.Action.Bomb.value
        if key == 'q': act = constants.Action.Stop.value

    if act is None:
        act = constants.Action.Stop.value

    return act

def game_type_mapper(game_type_int):
    if game_type_int == 1:
        return constants.GameType.FFA
    elif game_type_int == 2:
        return constants.GameType.Team
    elif game_type_int == 3:
        return constants.GameType.TeamRadio
    elif game_type_int == 4:
        return constants.GameType.OneVsOne
    else:
        raise KeyError('no game type object matching {} found'.format(game_type_int))


class DummyAgent:
    def __init__(self, agent_id, is_alive=True):
        self.agent_id = agent_id
        self.is_alive = True
        self.position = (-1, -1)
        self.ammo = -1
        self.blast_strength = 2
        self.can_kick = False

    def update(self, obs):
        alive_agents = obs['alive']
        if self.agent_id + 10 not in alive_agents:  #TODO Yoneda: confirm if this conversion is correct
            self.is_alive = False
        else:
            self.is_alive = True
        self.position = obs['position']  # NOTE: this is only true for one agent, but that'll be ok
        self.ammo = obs['ammo']
        self.blast_strength = obs['blast_strength']
        self.can_kick = obs['can_kick']


class DummyValue:
    def __init__(self, val):
        self.value = val

class DummyName:
    def __init__(self, name):
        self.name = name

class DummyFlame:
    def __init__(self, pos, life):
        self.position = pos
        self.life = int(life) - 1

class DummyBomb:
    def __init__(self, pos, life, blast_strength, mov_dir):
        self.position = pos
        self.life = int(life)
        self.blast_strength = int(blast_strength)
        if mov_dir == 0:
            self.moving_direction = None
        else:
            self.moving_direction = DummyValue(int(mov_dir))



class MultiPlayerClient(MultiPlayerClientRunner):
    '''An example Docker agent class'''

    def __init__(self):
        super(MultiPlayerClient, self).__init__()
        self._viewer = None
        self._env_info = {}
        self._dummy_agents = [DummyAgent(agent_id) for agent_id in range(4)]  # NOTE: hard-coding 4 agents
        self._dummy_bombs = []
        self._dummy_flames = []
        self._collapse_alert_map = None
        self.selected_action = -1
        self._is_dead = False
        self._enable_interactive_message = True
        # self._is_on_game = False
        # self._done = False
        # self._is_ready_to_start = False

        agent_control = 'arrows'
        ##
        # @NOTE: DO NOT move this import outside the constructor. It will
        # not work in headless environments like a Docker container
        # and prevents Pommerman from running.
        #
        from pyglet.window import key
        controls = {
            'arrows': {
                key.UP: 1,
                key.DOWN: 2,
                key.LEFT: 3,
                key.RIGHT: 4,
                key.SPACE: 5,
                key.SLASH: 0,  # do nothing
                # key.M: 6  # In Pommerman, this will freeze the game.
            },
            'wasd': {
                key.W: 1,
                key.S: 2,
                key.A: 3,
                key.D: 4,
                key.E: 5,
                key.Q: 6  # In Pommerman, this will freeze the game.
            }
        }

        assert agent_control in controls, "Unknown control: {}".format(
            agent_control)
        self._key2act = controls[agent_control]

    def init_agent(self, id, game_type, env_info):
        self._env_info = env_info
        self._is_on_game = True
        self._is_dead = False
        self._enable_interactive_message = True
        # return self._agent.init_agent(id, game_type)

    def act(self, observation, action_space):
        # return self._agent.act(observation, action_space)
        print("waiting for your input...")

        act = None
        self._update_dummy_agents(observation)  # update dummy agents' info
        self._update_dummy_bombs(observation)  # update dummy agents' info
        self._update_dummy_flames(observation)  # update dummy flames' info
        self._update_collapse_alert_map(observation)
        self.render(observation, act)

        self.selected_action = -1 # reset selected_action
        self._viewer.window.activate()
        while self.selected_action < 0:
            # self._viewer.window.dispatch_event('on_key_press') <-- this didn't work...
            self._viewer.window.switch_to()
            self._viewer.window.dispatch_events()
            time.sleep(1/60)  # wait

            # self._viewer.window.dispatch_event('on_draw')
            # self._viewer.window.flip()
        # key = click.getchar()
        # act = get_action(key, control='arrows')
        act = self.selected_action
        self.render(observation, act, waiting=True)  # draw the selected action!

        # print(observation)
        # print("ACTION:", act)
        print("ACTION:", constants.action2name[act])

        return act

    def visualize_obs(self, observation, waiting=True):
        '''Just visualize the given observation.
        This is used in the beginning of the game (Without this, agents 1~3 can not get/visualize any obs until the former agents decide their actions)
        It's being a bit messy but should be ok.
        '''
        act = None
        self._update_dummy_agents(observation)  # update dummy agents' info
        self._update_dummy_bombs(observation)  # update dummy agents' info
        self._update_dummy_flames(observation)  # update dummy flames' info
        self._update_collapse_alert_map(observation)
        # self.render(observation, act, waiting=True)
        print(waiting)
        self.render(observation, act, waiting=waiting)

    def _update_dummy_agents(self, obs):
        for agent in self._dummy_agents:
            agent.update(obs)

    def _update_dummy_bombs(self, obs):
        self._dummy_bombs = []  # reset bombs
        board_size = self._env_info['board_size']
        bomb_life = obs['bomb_life']
        blast_strength = obs['bomb_blast_strength']
        moving_direction = obs['bomb_moving_direction']
        for row in range(board_size):
            for col in range(board_size):
                life = int(bomb_life[row][col])
                strength = int(blast_strength[row][col])
                mov_dir = int(moving_direction[row][col])
                if life > 0:
                    self._dummy_bombs.append(
                        DummyBomb((row, col), life, strength, mov_dir)
                    )

    def _update_dummy_flames(self, obs):
        self._dummy_flames = []  # reset flames
        flame_life = obs['flame_life']
        board_size = self._env_info['board_size']
        for row in range(board_size):
            for col in range(board_size):
                life = flame_life[row][col]
                if life > 0:
                    self._dummy_flames.append(
                        DummyFlame(pos=(row, col), life=life)
                    )

    def _update_collapse_alert_map(self, obs):
        if 'collapse_alert_map' not in obs:
            board_size = self._env_info['board_size']
            self._collapse_alert_map = np.zeros((board_size, board_size))
        else:
            self._collapse_alert_map = np.asarray(obs['collapse_alert_map'])

    def die(self):
        # self._viewer.set_gameover()
        # self._viewer.render()
        print("=================== You Died ;P ======================")
        self._is_dead = True

    def episode_end(self, reward):
        self._enable_interactive_message = False
        # return self._agent.episode_end(reward)
        win = '<font face="Cousine-Regular" size="6">Your Team Wins!</font>'
        draw = '<font face="Cousine-Regular" size="6">DRAW!</font>'
        lose = '<font face="Cousine-Regular" size="6">Your Team Loses!</font>'
        teammate_died = '<font face="Cousine-Regular" size="6">Your Teammate Died!</font>'
        if self._viewer is not None:
            self._viewer.set_waiting(False)
            if reward > 0:
                self._viewer.set_html_labels(win)
            elif reward == 0:
                self._viewer.set_html_labels(draw)
            else:
                if self._is_dead:
                    self._viewer.set_html_labels(lose)
                else:
                    self._viewer.set_html_labels(teammate_died)
            self._viewer.render()

        print("GAME OVER")
        print("reward", reward)
        if reward > 0:
            print("=================== Your team Wins ;) ======================")
        elif reward == 0:
            print("=================== DRAW :) ======================")
        else:
            print("=================== Your team Loses x( ======================")

        self._done = True
        self._is_ready_to_start = False

        print("NOTE: Please DO NOT Ctrl-C. The program will be killed automatically")

    def check_if_done(self):
        return self._done

    def ready_to_start(self):
        self._is_ready_to_start = True

    def check_if_ready_to_start(self):
        return self._is_ready_to_start

    def shutdown(self):
        # return self._agent.shutdown()

        print("Thank you for playing!!")
        print("The game will be automatically closed soon.")
        time.sleep(10)

        if self._viewer is not None:
            self._viewer.close()
            self._viewer = None

        self._is_on_game = False
        # raise SystemExit

    def render(self, obs, act, waiting=False):
        # render observation and action
        if self._viewer is None:
            self._viewer = graphics.PommeViewer(
                board_size=self._env_info['board_size'],
                agents=self._dummy_agents,
                partially_observable=self._env_info['is_partially_observable'],
                agent_view_size=self._env_info['agent_view_size'],
                game_type=game_type_mapper(int(self._env_info['game_type']))
            )

        self._viewer.set_board(obs['board'])
        self._viewer.set_agents(self._dummy_agents)
        self._viewer.set_step(obs['step_count'])
        self._viewer.set_bombs(self._dummy_bombs)
        self._viewer.set_flames(self._dummy_flames)
        self._viewer.set_collapse_alert_map(self._collapse_alert_map)  # this line is added
        self._viewer.set_waiting(waiting)
        print(waiting)
        # if waiting:
        #     self._viewer.set_html_labels(['Waiting for the other player...',
        #                               '(Don\'t worry if the cursor becomes busy mark, it\'s working.)'
        #                               ])
        if act is not None:
            self._viewer.set_selected_action(act)
        self._viewer.render()

        @self._viewer.window.event
        def on_key_press(k, mod):
            print('on key press!', k)
            if k in self._key2act:
                self.selected_action = self._key2act[k]
            # NOTE: Since I force to activate the GUI window, sometimes the window can be activated when the user is typing.
            # else:
            #     self.selected_action = constants.Action.Stop.value

        @self._viewer.window.event
        def on_mouse_press(x, y, button, modifiers):
            # print('on mouse press!', x, y, button)
            self._viewer.window.activate()

        @self._viewer.window.event
        def on_deactivate():
            if self._enable_interactive_message:
                self._viewer.set_html_labels([
                    # '<font face="Times New Roman" size="7">Hello, <i>world</i></font>',
                    '<font face="Cousine-Regular" size="6"><i>Click this window</i> to control the agent!</font>',
                    '<font face="Cousine-Regular" size="3">(if this message doesn\'t disappear, try pressing \'Ctrl and ↑\' and then select this window)</font>'
                ])
                self._viewer.render()


        @self._viewer.window.event
        def on_activate():
            self._viewer.set_html_labels([])
            self._viewer.render()


        # @self._viewer.window.event
        # def on_mouse_enter(x, y):
        #     # print('on mouse enter!', x, y)
        #     self._viewer.window.activate()

        # @self._viewer.window.event
        # def on_context_lost():
        #     print('context is lost x(')

        # @self._viewer.window.event
        # def on_context_state_lost():
        #     print('contxt state is lost xx(')

        # @self._viewer.window.event
        # def on_deactivate():
        #     print('on deactivate!')

        # @self._viewer.window.event
        # def on_mouse_motion(x, y, dx, dy):
        #     self._viewer.window.activate()
        #     # print('mouse motion!', x, y, dx, dy)
        #     # self._viewer.window.activate()

        # @self._viewer.window.event
        # def on_key_release(k, mod):
        #     print("key pressed!!", k, mod)
        #     act = constants.Action.Stop.value
        #     if k in self._key2act.keys():
        #         act = self._key2act[k]
        #     self._current_action = act




def main():
    '''Inits and runs a Docker Agent'''

    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=constants.AGENT_BASE_PORT)
    args = parser.parse_args()

    agent = MultiPlayerClient()
    agent.run(port=args.port)


if __name__ == "__main__":
    main()
