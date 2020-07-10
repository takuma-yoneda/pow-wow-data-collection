'''keep pinging clients to detect both clients being up.
Once both clients are up, initialize message_server and launch pom_battle.
'''
import os
import requests
import polling
import json
import logging
import random
from datetime import datetime
from pommerman import utility
from http.client import RemoteDisconnected
import argparse


# message_port = '8000'
# docker_ports = ['10000', '10001']
# client_urls = ['http://localhost:9000', 'http://localhost:9001']
# client_urls = ['http://localhost:9000']


def get_timestamp_dirname():
    return datetime.now().strftime('pomlog_%Y%m%d-%H%M%S')


def check_if_clients_are_ready(client_urls):
    successes = []
    for client_url in client_urls:
        try:
            response = requests.get(client_url + '/is_ready_to_start')
            success = json.loads(response.content).get('result')
        except requests.exceptions.ConnectionError:
            success = False
        successes.append(success)

    if all(successes):
        return True
    else:
        return False


def initialize_messenger(message_port):
    url = 'http://localhost:{}/initialize'.format(message_port)
    try:
        req = requests.get(
            url,
            timeout=0.5,
        )
    except requests.exceptions.ConnectionError as e:
        logger.error(e)
        logger.error("Make sure that message_server is running.")
        raise e


def request_logging(message_port):
    url = 'http://localhost:{}/start_logging'.format(message_port)
    logger.info('Requesting message_server to start logging...')
    logdir = get_timestamp_dirname()
    logger.info('logdir: {}'.format(logdir))
    try:
        req = requests.post(
            url,
            timeout=0.5,
            json={'logdir': json.dumps(logdir, cls=utility.PommermanJSONEncoder)}
        )
    except requests.exceptions.ConnectionError as e:
        logger.error(e)
        logger.error("Make sure that message_server is running.")
        raise e


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--message_port', default='8000')
    parser.add_argument('--docker_ports', nargs='+', default=['10000', '10001'], help='specify docker port. default=10000, 10001]')
    parser.add_argument('--client_ports', nargs='+', default=['9000', '9001'], help='specify client port. default=9000, 9001]')
    args = parser.parse_args()
    message_port = args.message_port
    docker_ports = args.docker_ports
    client_urls = ['http://localhost:{}'.format(port) for port in args.client_ports]
    print(args)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    logger.addHandler(stream_handler)

    player0 = "multiplayers::localhost:{}".format(args.client_ports[0])
    player1 = "multiplayers::localhost:{}".format(args.client_ports[1])
    simple_player = "test::agents.SimpleAgent"
    static_player = "static::hoge"
    # docker_player = "docker::multiagentlearning/skynet955"
    # docker_player = "docker::takumaynd/nips-hakozakijunction3-notest"
    # docker_player = "docker_hakozaki::takumaynd/nips-hakozakijunction3-notest"
    # docker_player = "docker_hakozaki::takumaynd/hakozakijunctions-notest"
    docker_players = ["docker_hakozaki::takumaynd/hakozakijunctions-notest:{}".format(docker_ports[0])
                      , "docker_hakozaki::takumaynd/hakozakijunctions-notest:{}".format(docker_ports[1])]

    docker_match0 = "pom_battle_comm --agents=" + (',').join((player0, docker_players[0], player1, docker_players[1])) + ' --config=PommeTeamCompetitionBombermanlike-v15 ' + '--messaging_port {}'.format(message_port)
    docker_match1 = "pom_battle_comm --agents=" + (',').join((player1, docker_players[0], player0, docker_players[1])) + ' --config=PommeTeamCompetitionBombermanlike-v15 ' + '--messaging_port {}'.format(message_port)
    docker_match2 = "pom_battle_comm --agents=" + (',').join((docker_players[0], player0, docker_players[1], player1)) + ' --config=PommeTeamCompetitionBombermanlike-v15 ' + '--messaging_port {}'.format(message_port)
    docker_match3 = "pom_battle_comm --agents=" + (',').join((docker_players[0], player1, docker_players[1], player0)) + ' --config=PommeTeamCompetitionBombermanlike-v15 ' + '--messaging_port {}'.format(message_port)

    settings = [docker_match0, docker_match1, docker_match2, docker_match3]
    # test = "pom_battle_comm --agents=" + (',').join((simple_player, player0, simple_player, player1)) + ' --config=PommeTeamCompetitionBombermanlike-v15'
    # test = "pom_battle_comm --agents=" + (',').join((static_player, player0, static_player, static_player)) + ' --config=PommeTeamCompetitionBombermanlike-v15'
    # settings = [test]
    # test = "pom_battle --agents=player::arrows," + docker_player + "," + "test::agents.SimpleAgent," + docker_player + " --config=PommeTeamCompetition-v0"
    # settings = [test]

    while True:
        logger.info('Initializing messenger...')
        initialize_messenger(message_port)

        logger.info('Waiting for all clients to be up...')
        polling.poll(
            lambda: check_if_clients_are_ready(client_urls),
            step=1,
            poll_forever=True
        )
        logger.info('All clients are up.')

        logger.info('Start data logging...')
        request_logging(message_port)

        # randomly choose one setting
        selected_setting = random.choice(settings)
        logger.info('selected setting: {}'.format(selected_setting))
        logger.info('Starting a game...')

        try:
            os.system(selected_setting)
        except RemoteDisconnected as e:
            logger.warn('RemoteDisconnected (Probably a client was killed.)')
            continue
        except requests.exceptions.ConnectionError as e:
            logger.warn('Connection Error (Probably a client was killed.)')
            continue

        logger.info('---- Game Finished ----')
