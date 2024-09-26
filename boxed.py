#!/usr/bin/python3
import re
import os
import subprocess
from argparse import ArgumentParser
import json
from colorama import Fore

# =========== Docker Compose =========== #
dockerCompose = \
"""\
services:
  boxed_player:
    container_name: boxed_player
    restart: always
    build: 
      context: .
      dockerfile: Dockerfile_player
    ports:
      - "6000:22"
    volumes:
      - "./:/root:z"
    networks:
        - net

  boxed_{vul}:
    container_name: boxed_{vul}
    restart: always
    build: .
    ports:
      - "3000:3000"
    networks:
        - net

networks:
    net:
        driver: bridge
"""

# =========== Dockerfile Challenge =========== #
dockerChallenge = \
"""\
FROM ubuntu:24.10

WORKDIR /root

RUN apt-get update && \\
apt-get install -y wget tar xz-utils make gcc && \\
wget https://yx7.cc/code/ynetd/ynetd-2024.02.17.tar.xz && \\
tar -xvf ynetd-2024.02.17.tar.xz && \\
cd ynetd-2024.02.17 && \\
make && \\
mv ynetd /usr/bin/ynetd 

RUN rm -rf ynetd-2024.02.17.tar.xz ynetd-2024.02.17 

RUN useradd -m -s /bin/sh ctf
RUN echo "ctf:ctf" | chpasswd

WORKDIR /home/ctf

COPY {vul} .

RUN chown -R root:ctf /home/ctf && \\
chmod -R 750 /home/ctf 

USER ctf
EXPOSE 3000
CMD ynetd -p 3000 ./{vul}\
"""

# =========== Dockerfile Player =========== #
dockerPlayer = \
"""\
FROM ubuntu:24.10

RUN apt-get update && \\
apt-get install -y openssh-server build-essential netcat-traditional strace ltrace gcc gcc-multilib vim gdb python-is-python3 python3-pip python3-ropgadget make curl wget git && \\
pip3 install pwntools capstone --break-system-packages

RUN echo "root:root" | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

WORKDIR /root

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]\
"""

class Boxed:
    def __init__(self, projectdir, challengefile):
        self.is_projectdir = projectdir
        self.is_challengefile_here = challengefile

    def run(self):
        actions.get(int(self.is_projectdir) << 1 | int(self.is_challengefile_here))()
    

parser = ArgumentParser(description='')
parser.add_argument('challenge', type=str, help='challenge exe file')
parser.add_argument('--clean', action='store_true', help='clean all related docker images')
parser.add_argument('--down', action='store_true', help='run docker-compose down')
args = parser.parse_args()

current_dir = os.getcwd().split('/')[-1]


def replaceS(toreplace, replacewith, string):
    return re.sub( r'{'+toreplace+'}', replacewith, string)

def createDockerCompose(args):
    res = replaceS('vul', args.challenge, dockerCompose)

    with open('docker-compose.yml', 'w') as f:
        f.write(res)

def createChallenge(args):
    res = replaceS('vul', args.challenge, dockerChallenge)

    with open('Dockerfile', 'w') as f:
        f.write(res)

def createPlayer(args):
    res = replaceS('vul', args.challenge, dockerPlayer)

    with open('Dockerfile_player', 'w') as f:
        f.write(res)

def createDockeringnore():
    with open('.dockerignore', 'w') as f:
        f.write('Dockerfile\nDockerfile_player\n.boxed\n')

def setupChallenge():
    createChallenge(args)

    createPlayer(args)

    createDockerCompose(args)

    createDockeringnore()

    print('project setup done')

def clean():
    subprocess.run('docker rmi $(docker images -f "reference=*boxed_*" -q) -f', shell=True)
    subprocess.run(['docker', 'image', 'prune', '-f'])
    subprocess.run(['docker', 'container', 'prune', '-f'])

def down():
    subprocess.run(['docker-compose', 'down'])

def setupProject():
    if not os.path.exists('.boxed'):
        open('.boxed', 'w').close()
    setupChallenge()
    checkStatus()


def checkStatus():
    setupChallenge()

    container_status = list(map(json.loads, 
                                subprocess.check_output(['docker', 'ps', 
                                                         '--format', 'json', '-f', 'name=boxed_'])
                                    .decode('utf-8')
                                    .split('\n')[:-1]))
    
    if not container_status:
        subprocess.run(['docker-compose', 'up', '-d'])


    player_is_up = False
    challenge_is_up = False
    for container in container_status:
        name = container['Names'][6:]

        if name == 'player':
            player_is_up = True
        elif name == args.challenge:
            challenge_is_up = True
        else:
            subprocess.run(['docker', 'stop', 'boxed_'+name, 'boxed_player'])
            subprocess.run(['docker', 'rm', 'boxed_'+name, 'boxed_player'])
            subprocess.run(['docker', 'container', 'prune', '-f'])
            subprocess.run(['docker-compose', 'up', '-d'])


    if not player_is_up:
        subprocess.run(['docker-compose', 'up', '-d', 'boxed_player'])
        print('[*] player is up')

    if not challenge_is_up:
        subprocess.run(['docker-compose', 'up', '-d', 'boxed_'+args.challenge])
        print('[*] challenge is up')

    network = subprocess.check_output(['docker', 'inspect', '-f', 
                                       '"{{range .IPAM.Config}}{{.Gateway}}{{end}}"', 
                                       f'{current_dir}_net']) \
                            .decode('utf-8') \
                            .replace('"', '') \
                            .replace('\n', '')

    print(f'[*] Player and challenge({args.challenge}) are up, please connect to the player with '
          f'{Fore.YELLOW}ssh root@localhost -p 6000{Fore.RESET} (password: root) and the challenge is running on port 3000 '
          f'connect to it with {Fore.YELLOW}nc {network} 3000{Fore.RESET} from the player container')
    
    print('[*] Run `docker-compose down` to stop the containers')


def invalidProjectDir():
    print('Error: no challenge file found in this directory nor .boxed found. '
          'Please specify the correct challenge file name to setup the project')
    exit(0)

def invalidChallengefile():
    print('Error: invalid challenge file. Please specify the correct challenge file name')

actions = {
    0: invalidProjectDir,
    1: setupProject,
    2: invalidChallengefile,
    3: checkStatus
}


if __name__ == '__main__':
    if args.down:
        down()

    if args.clean:
        clean()

    if args.clean or args.down:
        exit(0)


    isprojectdir = os.path.exists('.boxed')
    ischallengefilehere = os.path.exists(args.challenge)

    boxed = Boxed(isprojectdir, ischallengefilehere)
    boxed.run()



