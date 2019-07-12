# Import socket module
import socket
import address



def Main():
    # local host IP '127.0.0.1'
    host = '127.0.0.1'

    # Define the port on which you want to connect
    port = address.getadd()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # connect to server on local computer
    s.connect((host, port))

    # message you send to server
    message = "shaurya says geeksforgeeks"
    n = 0
    while True:

        # message sent to server
        # s.send(message.encode('ascii'))
        print("send data ?")
        input()
        print(n)
        datka = ""
        dontsend = 0
        if n == 0:
            datka = "Umpa_Lumpa\a\b"
        elif n == 1:
            datka = "5752\a\b"
            # s.send(datka.encode('ascii'))
            # data = s.recv(1024)
            # print('server:', str(data.decode('ascii')))
        elif n == 2:
            dontsend = 1
        elif n == 3:
            datka ="OK 0 1\a\b"

        if(datka == ""):
            break
        else:
            if not dontsend:
                dontsend = 0
                s.send(datka.encode('ascii'))
        # messaga received from server
        data = s.recv(1024)

        # print the received message
        # here it would be a reverse of sent message
        print('server:', str(data.decode('ascii')))
        n+=1
    # close the connection
    s.close()
    return


if __name__ == '__main__':
    Main()
