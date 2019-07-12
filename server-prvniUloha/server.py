# kouckma2
# parts of code inspired by (sometimes copied from):
# https://www.geeksforgeeks.org/socket-programming-multi-threading-python/

# import address
import socket
from _thread import *
import threading
from threading import Thread
import re
from collections import deque

print_lock = threading.Lock()
serverKey = 54621
clientKey = 45328


# states
# 0 == waiting for username
# 1 == waiting for confirmation
# 2 == waiting for getting current position
# 3 == waiting for OK
# 4 == waiting for message

def checkSyntax(data, state):
    wrong = 0
    if not data.endswith("\a\b"):
        wrong = 1
    elif state == 0:
        if re.match("^[a-zA-Z0-9_]*$", data):
            wrong = 1
        elif len(data) > 12:
            wrong = 1
    elif state == 1:
        if len(data) > 7 or not data.rstrip("\a\b").isdigit():
            wrong = 1
    elif state == 2 or state == 3:
        if len(data) > 12:
            wrong = 1
        elif data.startswith("OK"):
            if len(data.split()) > 3:
                wrong = 1
            spl = data.rstrip("\a\b").split()
            print(len(spl))
            if len(spl) < 3 or not re.match("^-*[0-9]*$", spl[1]) or not re.match("^-*[0-9]*$", spl[2]) or len(spl) > 3:
                print(spl[2], spl[2].isdigit())
                wrong = 1
        else:
            wrong = 1
    elif state == 4 and len(data) > 100:
        wrong = 1
    ret = data.rstrip("\a\b")
    return wrong, ret


def decode(data):
    decoded = data.decode("ascii")
    return decoded


def isRecharging(data):
    recharge = 0
    if len(data) == 12 and data.startswith("RECHARGING"):
        if data.endswith("\a\b"):
            recharge = 1
    return recharge


def calcHash(decoded):
    sum = 0
    for char in decoded:
        sum += ord(char)
    hash = (sum * 1000) % 65536
    sHash = (hash + serverKey) % 65536
    return sHash, hash


def checkClientHash(data, sHash):
    calc = (sHash + clientKey) % 65536
    return int(data) == calc


def isCharged(data):
    return data == 'FULL POWER\a\b'


def getFace(x, y, newX, newY):
    face = -1
    if newY > y:
        face = 0
    elif newY < y:
        face = 2
    elif newX > x:
        face = 1
    elif newX < x:
        face = 3
    return face


def getfinals(arr):
    finalPair = arr.pop()
    finalX = finalPair[0]
    finalY = finalPair[1]
    return finalX, finalY


# 0 == move
# 1 == turn right
# 2 == turn left
# 3 == in final position
def getMove(currX, currY, facing, destX, destY):
    move = 0
    if facing == 0:
        if currY > destY:
            move = 1
        elif currY < destY:
            move = 0
        elif currY == destY:
            if currX > destX:
                move = 2
            elif currX < destX:
                move = 1
            elif currX == destX:
                move = 3
    elif facing == 1:
        if currY > destY:
            move = 1
        elif currY < destY:
            move = 2
        elif currY == destY:
            if currX > destX:
                move = 2
            elif currX < destX:
                move = 0
            elif currX == destX:
                move = 3
    elif facing == 2:
        if currY > destY:
            move = 0
        elif currY < destY:
            move = 1
        elif currY == destY:
            if currX > destX:
                move = 1
            elif currX < destX:
                move = 2
            elif currX == destX:
                move = 3
    elif facing == 3:
        if currY > destY:
            move = 2
        elif currY < destY:
            move = 1
        elif currY == destY:
            if currX > destX:
                move = 0
            elif currX < destX:
                move = 2
            elif currX == destX:
                move = 3
    return move


def doMove(c, move, facing):
    face = facing
    if move == 0:
        out = "102 MOVE\a\b"
    elif move == 1:
        face = (facing + 1) % 4
        out = "104 TURN RIGHT\a\b"
    elif move == 2:
        face = (facing - 1) % 4
        out = "103 TURN LEFT\a\b"
    elif move == 3:
        out = "105 GET MESSAGE\a\b"
    c.sendall(out.encode('ascii'))
    return face


def handleData(c, data, state, sHash, facing, x, y, finalX, finalY):
    oData = 0
    oArr = []
    close = 0
    face = facing
    if state == 0:
        out, oData = calcHash(data)
        print("sending", out)
        c.sendall((str(out) + "\a\b").encode('ascii'))
        state += 1
    elif state == 1:
        out = checkClientHash(data, sHash)
        if not out:
            close = 1
            c.sendall("300 LOGIN FAILED\a\b".encode('ascii'))
        else:
            c.sendall("200 OK\a\b".encode('ascii'))
            c.sendall("102 MOVE\a\b".encode('ascii'))
            state += 1
    elif state == 2:
        spl = data.rstrip("\a\b").split()
        if x != -99 and y != -99:
            face = getFace(x, y, int(spl[1]), int(spl[2]))
            if not face == -1:
                state += 1
        oArr.append(int(spl[1]))
        oArr.append(int(spl[2]))
        c.sendall("102 MOVE\a\b".encode('ascii'))
    elif state == 3:
        spl = data.rstrip("\a\b").split()
        currX = int(spl[1])
        currY = int(spl[2])
        oArr.append(int(spl[1]))
        oArr.append(int(spl[2]))
        move = getMove(currX, currY, facing, finalX, finalY)
        face = doMove(c, move, facing)
        if move == 3:
            state += 1
    elif state == 4:
        if not data.startswith("\a\b") and len(data) > 0:
            c.sendall("106 LOGOUT\a\b".encode('ascii'))
            close = 1
        else:
            currX = x
            currY = y
            oArr.append(x)
            oArr.append(y)
            move = getMove(currX, currY, facing, finalX, finalY)
            face = doMove(c, move, facing)
            if move != 3:
                state -= 1
    return state, face, oData, close, oArr


def getMessages(decoded):
    end = 0
    if decoded.endswith("\a\b"):
        end = 1
        decoded = decoded.rstrip("\a\b")
    arr = []
    arr = decoded.split("\a\b")
    qu = deque()
    n = 0
    for m in arr:
        n += 1
        s = m + "\a\b"
        qu.append(s)
    if not end:
        tmp = qu.pop()
        suffix = "\a\b"
        tmp = re.sub(re.escape(suffix) + '$', '', tmp)
        qu.append(tmp)
    return qu, end


def optimize(state, tmp):
    wrong = 0
    if state == 0 and len(tmp) > 11:
        wrong = 1
    if state == 1 and len(tmp) > 6:
        wrong = 1
    if (state == 2 or state == 3) and (len(tmp) > 11):
        wrong = 1
    if state == 4 and (len(tmp) > 99):
        wrong = 1
    return wrong


def threaded(c):
    print("GOT NEW CLIENT\n\n")
    messages = deque()
    arr = []
    sw = 1
    for i in range(-2, 3):
        if sw:
            sw = 0
            for j in reversed(range(-2, 3)):
                arr.append([i, j])
        else:
            sw = 1
            for j in range(-2, 3):
                arr.append([i, j])
    state = 0
    sHash = 0
    recharging = 0
    facing = 0
    x = -99
    y = -99
    finalX, finalY = getfinals(arr)
    prevEnded = 1
    try:
        while True:
            print("================\n"
                  "anotherCycle:\n"
                  "================================================"
                  "\n")
            decoded = ""
            if not len(messages) or (len(messages) == 1 and not prevEnded):
                if not prevEnded and len(messages) == 1:
                    tmp = messages.pop()
                    wrong = optimize(state, tmp)
                    if wrong:
                        c.sendall("301 SYNTAX ERROR\a\b".encode('ascii'))
                        break
                    messages.append(tmp)
                data = c.recv(1024)
                if not recharging and not data:
                    break
                else:
                    decoded = decode(data)

                Tmessages, ended = getMessages(decoded)

                if not prevEnded:
                    tmp = messages.pop()
                    tmp2 = Tmessages.popleft()
                    second = 0
                    if tmp2.startswith("\b") and tmp.endswith("\a"):
                        if len(tmp2) > 1:
                            second = 1
                        tmp += "\b"
                    else:
                        tmp += tmp2
                    if tmp.endswith("\a\b") and len(Tmessages) == 0:
                        ended = 1
                    messages.append(tmp)
                    if second:
                        if not tmp2.endswith("\a\b"):
                            ended = 0
                        st = tmp2[1:]
                        messages.append(st)
                for m in Tmessages:
                    messages.append(m)
                prevEnded = ended
                if not ended and len(messages) < 2:
                    continue
            decoded = messages.popleft()
            if recharging:
                if not data:
                    break
                elif isCharged(decoded):
                    recharging = 0
                    c.settimeout(1)
                    continue
                else:
                    c.sendall("302 LOGIC ERROR\a\b".encode('ascii'))
                    break
            recharging = isRecharging(decoded)
            print("1;isrechargin?:", recharging)
            if recharging:
                c.settimeout(5)
                continue
            syntax, decoded = checkSyntax(decoded, state)
            print("2;neproslo testem syntaxe ?= ", syntax, "in state= ", state, "and message= ", decoded)
            if (syntax != 0):
                c.sendall("301 SYNTAX ERROR\a\b".encode('ascii'))
                print("syntax error")
                break
            state, facing, oData, closeX, oArr = handleData(c, decoded, state, sHash, facing, x, y, finalX, finalY)
            if state == 1:
                sHash = oData
            if oArr and (state == 2 or state == 3):
                x = oArr[0]
                y = oArr[1]
            if state == 4 and arr:
                finalX, finalY = getfinals(arr)
            if closeX:
                break
    except socket.timeout:
        print('timeout exception')
    c.close()


def Main():
    host = ""
    # port = address.getadd()
    port = 12345
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    print("port:", port)
    s.listen(1)
    print("listening...")
    threads = []
    while True:
        c, addr = s.accept()
        c.settimeout(1)
        th = Thread(target=threaded, args=(c,))
        th.start()
        threads.append(th)
        # break
    # print("pls work")
    # for th in threads:
    #     th.join()
    # s.close()
    # print("closing server...")


if __name__ == '__main__':
    Main()
