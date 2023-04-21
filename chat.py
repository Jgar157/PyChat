import os
import socket
import sys
import threading
import platform
import time
import re

PACKET_SIZE = 1024
LOCAL_IP = "127.0.0.1"
READER_FLAG = False
VALID_SELF_PORT = False


def file_exists(file_name: str) -> bool:
    return os.path.isfile(file_name)


def upload(sock, file_name):
    if file_exists(file_name):

        # Send file status over
        sock.send("200".encode())

        # Send file size over
        file_size = os.path.getsize(file_name)
        sock.send(file_size.to_bytes(PACKET_SIZE, byteorder="big"))

        # Begin transmitting file over
        with open(file_name, 'rb') as source_file:

            remaining_bytes = file_size
            while remaining_bytes > 0:
                next_size = min(PACKET_SIZE, remaining_bytes)

                chunk = source_file.read(next_size)
                sock.sendall(chunk)

                remaining_bytes -= next_size
            source_file.flush()

    else:
        sock.send("404".encode())
        print("File name does not exist in local directory, please try again.")


def download(sock, file_name):
    file_status = sock.recv(PACKET_SIZE).decode()

    if file_status != "404":
        # if logic for files
        # Update filename to make new copy
        file_name = f"new_{file_name}"

        # Receive file size from client
        file_size = sock.recv(PACKET_SIZE)
        remaining_bytes = int.from_bytes(file_size, byteorder='big')
        # print("File size:", remaining_bytes)

        # Open new file and begin writing
        # wb: write bytes
        time.sleep(1)
        with open(file_name, 'wb') as target_file:
            # Use c to track loops, print remaining_bytes every 100 loops
            while remaining_bytes > 0:
                next_size = min(PACKET_SIZE, remaining_bytes)  # Only read remaining amount
                chunk = sock.recv(next_size)
                target_file.write(chunk)  # Write the received bytes to the file

                # Now that we have written bytes, let us reduce the amount left to read
                remaining_bytes -= next_size

    else:
        print("Download from client failed: File did not exist")


def writer(ip_address):
    VALID_TARGET_PORT = False  # Ensure that the target port is an integer

    # Wait until Reader is done choosing a port to pick the target port
    while not READER_FLAG:
        time.sleep(1)

    while not VALID_TARGET_PORT:
        try:
            port = int(input("Please enter target user port number: "))
            VALID_TARGET_PORT = True
        except:
            print("Invalid port, please try again.")

    # Create the writer socket
    writer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # 10 Attempts to connect
    for tries in range(5):
        try:
            writer.connect((ip_address, port))
            print(ip_address, port)
            print("Connected on port:", port)
            writer.send(user_name.encode())
            break
        except:
            time.sleep(2)


    # Writing loop
    user_chat = ""
    while user_chat != "exit":
        user_chat = input()

        # Check if Transferring file, upload if True
        writer.send(user_chat.encode())
        if len(user_chat) >= 10:
            command = user_chat[:8].upper()
            file_name = user_chat[9:]

            if command == "TRANSFER":
                upload(writer, file_name)


user_name = sys.argv[1]  # Exclude the file name
ip_address = LOCAL_IP

# Prepare the thread
writer_thread = threading.Thread(target=writer, args=(ip_address,))

# Convert main thread to Reading Thread
# Create the socket
reader = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
reader.settimeout(300)

while not VALID_SELF_PORT:
    try:
        port = int(input("Please enter your own port: "))
        reader.bind((LOCAL_IP, port))
        READER_FLAG = True
        reader.listen(1)
        VALID_SELF_PORT = True
    except Exception as e:
        print("Invalid port, please try again.")

# Begin the writing Thread! :)
writer_thread.start()

(reader, addr) = reader.accept()
chatter_user_name = reader.recv(PACKET_SIZE).decode()

received_text = ""
while received_text != "exit":
    received_text = reader.recv(PACKET_SIZE).decode()

    if len(received_text) >= 4:  # Check if exiting
        command = received_text[:4].upper()
        # Begin exiting the system
        if command == "EXIT":
            print(f"{chatter_user_name} has exited the chat.")
            sys.exit(0)

    # Check if Transferring file, upload if True
    if len(received_text) >= 10:
        command = received_text[:8].upper()
        file_name = received_text[9:]

        print(f"{chatter_user_name}: {received_text}")

        if command == "TRANSFER":
            # print("Beginning Download")
            download(reader, file_name)
            # print("Ending Download")

    else:
        print(f"{chatter_user_name}: {received_text}")
