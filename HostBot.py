import socket
import sys
from time import sleep

M_IDLE = 0
M_HOSTING_PLAYER = 1
M_HOSTING_GAME = 2
M_GAME_SETUP = 3

MSG_NOTIFY = 0
MSG_NORMAL = 1
MSG_PM     = 2
MSG_ERROR  = 3
MSG_POP    = 4

hutlist = ["" for i in range(4*10)]
receiving_huts = False
players = 4
myhut = 0
mode = M_IDLE
master = ""
in_game = False
connections = 0
connected = 0
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
    if t == MSG_PM:
        sender, message = message.split("> ", 1)
        process_pm(sender, message)
    elif t == MSG_NOTIFY:
        process_notify(message)
    elif t == MSG_NORMAL:
        sender, message = message.split("> ", 1)
        process_msg(sender, message)
    else:
        # invalid message format
        pass
        
def process_pm(sender, message):
    global mode, master, players
    print sender, message
    if in_game:
        return

    if sender == "IncaWarrior" and message == "quit":
        sys.exit(0)
    
    if master == "" and message == "hostme":
        mode = M_HOSTING_PLAYER
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
    global connections, connected, master, in_game
    if not in_game and message.startswith("$hut "):
        cmd, hut, pos, data = message.split()
        hutlist[ (int(hut)-1)*4 + int(pos) ] = data
        check_hut()
        
    elif message.startswith("$pop "):
        message = message[5:]
        print message
        if message == "all ready":
            send('!startgame')

        elif message.startswith("connect"):
            connections += 1
            print message, connections

        elif message.startswith("connected"):
            connected += 1
            print message, connections
            check_hut()
            
        elif message.startswith("disconnect"):
            connections -= 1
            print message, connections
            if connections == 0:
                if in_game:
                    send('!closegame')
                    master = ""
                    in_game = False
                    myhut = 0
                    mode = M_IDLE
                    send("!joinhut 0")
                    send("!away "+STATUS)
    
def process_msg(sender, message):
    if message.startswith("$hut "):
        cmd, hut, pos = message.split()
        if int(hut) > 0:
            hutlist[ (int(hut)-1)*4 + int(pos) ] = sender
        else:
            # removed user from hut
            for i in range(len(hutlist)):
                if hutlist[i] == sender:
                    hutlist[i] = "*"
                    break
        if myhut != 0:
            check_hut()
        if mode == M_IDLE:
	    join_empty_hut()
    
def set_host_params(hut):
    global players, mode, myhut
    send('!joinhut '+str(hut)+' 0')
    send('!set host watcher 0 1')
    send('!set host mappack 42')
    send('!set host level 10')
    send('!set host players 3')
    players = 3
    myhut = hut
    mode = M_HOSTING_GAME
	
def join_empty_hut():
    global players, mode, master, myhut
    hut = 1
    pos = 0
    for i in range(0, len(hutlist) / 4):
        j = i * 4
        if hutlist[j+0] == "*" and hutlist[j+1] == "*" and hutlist[j+2] == "*" and hutlist[j+3] == "*":
            break
        hut += 1
	
    hostspot = hutlist[(hut-1)*4]
    set_host_params(hut)
	
# find the hut a player is in and join it as host
def join_player_hut(nick):
    global players, mode, master, myhut
    hut = 1
    pos = 0
    for spot in hutlist:
        if spot == nick:
            break
        pos = (pos + 1) % 4
        if pos == 0: hut += 1
    else:
        # could not find user in hut
        send('!pvt: '+nick+'> You need to be in a hut')
        mode = M_IDLE
        return
        
    hostspot = hutlist[(hut-1)*4]
    if pos == 0 or hostspot != "*":
        # user in host spot or host spot taken
        send('!pvt: '+nick+'> There is already a host in your hut')
        mode = M_IDLE
        return
        
    # joining user's hut as host
    print "Hosting "+nick
    set_host_params(hut)
    master = nick

def check_hut():
    global myhut, in_game
    if myhut == 0: return
    players_in_hut = 0
    for i in range((myhut-1)*4, myhut*4):
        if hutlist[i] != "*" : 
            players_in_hut += 1
    if players_in_hut == players: # and connected == players:
        print "Launching:"
        for i in range((myhut-1)*4+1, myhut*4):
            print " - "+ hutlist[i]
        sleep(5)
        send('!launch')
        myhut = 0
        in_game = True
        mode = M_GAME_SETUP



send("!away "+STATUS)
send("!hutlist")
while True:
    data = s.recv(BUFFER_SIZE)
    for line in data.split("\n"):
        if line:
            try:
                receive_message(int(line[0]), line[1:].strip())
            except:
                pass

s.close()
