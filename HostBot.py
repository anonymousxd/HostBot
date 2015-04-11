import socket
import sys
from time import sleep
import ctypes
from random import randrange
from time import time

MYNAME = "IncaSpy"

MAX_HUTS = 10
JOIN_DELAY = 10

M_IDLE = 0
M_HOSTING_PLAYER = 1
M_HOSTING_GAME = 2
M_LAUNCHING = 3
M_GAME_SETUP =4

MSG_NOTIFY = 0
MSG_NORMAL = 1
MSG_PM     = 2
MSG_ERROR  = 3
MSG_POP    = 4

hutlist = ["X" for i in range(4*MAX_HUTS)]
receiving_huts = False
players = 4
myhut = 0
mode = M_IDLE
master = ""
in_game = False
connections = 0
connected = 0
join_time = 0
STATUS = "HostBot"

TCP_IP = '127.0.0.1'
TCP_PORT = 7501
BUFFER_SIZE = 1024

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))

def send(msg):
    print ">",msg
    s.send(msg+"\n")
    sleep(0.1)

def receive_message(t, message):
    global join_time
    if t == MSG_PM and "> " in message:
        sender, message = message.split("> ", 1)
        process_pm(sender, message)
    elif t == MSG_NOTIFY:
        process_notify(message)
    elif t == MSG_NORMAL and "> " in message:
        sender, message = message.split("> ", 1)
        process_msg(sender, message)
    else:
        # invalid message format
        print "^",t,message
        pass

    if mode == M_IDLE and join_time + JOIN_DELAY < time():
        join_empty_hut()
        join_time = time()
        
def process_pm(sender, message):
    global mode, master, players
    print sender, message
    if in_game:
        return

    if sender == "IncaWarrior" and message == "quit":
        sys.exit(0)
    if sender == "IncaWarrior" and message == "reset":
        reset()
    
    if master == "" and (message == "hostme" or message == "join"):
        join_player_hut(sender)
##        
##    elif sender == master:
##        if message.startswith("players "):
##            players = int(message[-1])
##            if players < 2: players = 2
##            if players > 4: players = 4
##            send('!set host players '+str(players))
##            check_hut()

        
def process_notify(message):
    global connections, connected, master, in_game, myhut, mode
    if not in_game and message.startswith("$hut "):
        data = message.split()
        if len(data) < 4: return
        cmd, hut, pos, data = data
        hutlist[ (int(hut)-1)*4 + int(pos) ] = data
        check_hut()
        
    elif message.startswith("Launching "):
        mode = M_LAUNCHING
        print "really launching"
        
    elif message.startswith("$pop "):
        message = message[5:]
        if message == "all ready":
            send('!startgame')

        elif message == "started":
            in_game = True
            mode = M_GAME_SETUP
            print message

        elif message.startswith("connected"):
            connected += 1
            print message, connections
            check_hut()

        elif message.startswith("connect"):
            connections += 1
            print message, connections
            
        elif message.startswith("disconnect"):
            connections = max(connections-1, 0)
            print message, connections
            if connections == 0:
                if in_game: reset()
    
def process_msg(sender, message):
    global myhut
    
    if message.startswith("$hut "):
        data = message.split()
        if len(data) < 3: return
        cmd, hut, pos = data
        # removed user from hut
        for i in range(len(hutlist)):
            if hutlist[i] == sender:
                hutlist[i] = "*"
                break
            
        if int(hut) > 0:
            hutlist[ (int(hut)-1)*4 + int(pos) ] = sender

        if sender == MYNAME:
            if int(hut) != myhut:
                myhut = int(hut)
                print "Moved to hut:",myhut
            if myhut == 0 and mode == M_HOSTING_GAME:
                print "Moved out of hut"
                SetCursorPos(randrange(100),randrange(100))
                reset()
            elif myhut > 0 and mode == M_IDLE:
                set_host_params()
            
        if myhut != 0:
            check_hut()

def reset():
    global myhut, mode, in_game, master
    master = ""
    if in_game: send('!closegame')
    if myhut > 0: send("!joinhut 0")
    in_game = False
    myhut = 0
    mode = M_IDLE
    
def set_host_params():
    global players, mode
    print "Hosting in hut",myhut
    send("!away "+STATUS)
    send('!set host watcher 0 1')
    send('!set host mappack 42')
    send('!set host level 10')
    send('!set host players 3')
    players = 3
    mode = M_HOSTING_GAME
	
def join_empty_hut():
    global players, mode, master, myhut
    hut = 1
    pos = 0
    for i in range(0, MAX_HUTS):
        j = i * 4
        if hutlist[j+0] == "*" and hutlist[j+1] == "*" and hutlist[j+2] == "*" and hutlist[j+3] == "*":
            break
        hut += 1
    else:
        # no huts found
        return

    send('!joinhut '+str(hut)+' 0')
	
# find the hut a player is in and join it as host
def join_player_hut(nick):
    global players, mode, master, myhut
    hut = 1
    pos = 0
    mode = M_IDLE
    for spot in hutlist:
        if spot == nick:
            break
        pos = (pos + 1) % 4
        if pos == 0: hut += 1
    else:
        # could not find user in hut
        send('!pvt: '+nick+'> You need to be in a hut')
        return
        
    hostspot = hutlist[(hut-1)*4]
    if pos == 0 or hostspot != "*":
        # user in host spot or host spot taken
        send('!pvt: '+nick+'> There is already a host in your hut')
        return
        
    # joining user's hut as host
    print "Hosting "+nick
    send('!joinhut '+str(hut)+' 0')
    master = nick

def check_hut():
    global myhut, in_game, mode
    if myhut == 0: return
    players_in_hut = 0
    in_hut = False
    for i in range((myhut-1)*4, myhut*4):
        if hutlist[i] != "*" and hutlist[i] != "X": 
            players_in_hut += 1
        if hutlist[i] == MYNAME:
            in_hut = True

    # not in hut as expected
    if not in_hut:
        print "not in hut anymore"
        reset()
        
    elif players_in_hut == players and mode != M_LAUNCHING and mode != M_GAME_SETUP:
        print "Launching:"
        for i in range((myhut-1)*4+1, myhut*4):
            print " - "+ hutlist[i]
        send('!launch')


    else:
        #print players_in_hut, players
        pass

send("!away "+STATUS)
send("!hutlist")
while True:
    data = s.recv(BUFFER_SIZE)
    for line in data.split("\n"):
        if line and line[0].isdigit():
            #print line
            try:
                receive_message(int(line[0]), line[1:].strip())
            except Exception as e:
                print line
                raise e
                pass


s.close()
