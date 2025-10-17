import websockets
import asyncio
import json
import time
import traceback

from config import svc_configs
from datetime import datetime, timezone

# Configs and Setup
configs = svc_configs()
default_settings = configs["default"]["settings"]
track_supported = default_settings["track_supported"]

HOST = '0.0.0.0'
PORT = default_settings.get("websocket_port", 10500)

wss_client = set()
clients = {} 

async def remove_staled_user():
    p_time = time.time()
    users_ttl = 5 #default_settings.get('users_ttl', None)

    if users_ttl:
        if len(clients) > 0:
            for client in clients:
                elapsed_time = p_time - clients[client]['time']
                if elapsed_time > users_ttl:
                    del clients[client]

async def register_user(userUUID, userRole, organSelected, position, rotation, code):
    checkUser = clients.get(userUUID, None)
   
    try:
        
        if checkUser:
            clients[userUUID]['time'] = time.time()
            clients[userUUID]['position'] = position
            clients[userUUID]['rotation'] = rotation

            if clients[userUUID]['code'] != code:
                clients[userUUID]['code'] = code

            if clients[userUUID]['organ'] != organSelected:
                clients[userUUID]['organ'] = organSelected

        if checkUser is None:
            clients[userUUID] = {
                'uuid': userUUID,
                'role': userRole,
                'time': time.time(),
                'organ': organSelected,
                'position': position,
                'rotation': rotation,
                'code': code
            }

            print("register user websocket: " + str([userUUID, userRole]))

    except Exception as e:
        print("Error in registering user")
        traceback.print_exc()

async def broad_cast(data): 
    if wss_client:  # Check if there are any connected clients
        message = json.dumps(data)
        disconnected_clients = []
        for wss in wss_client:
            try:
                await wss.send(message)
            except websockets.ConnectionClosed:
                # Mark this client for removal if it has disconnected
                disconnected_clients.append(wss)

        # Remove all disconnected clients after the iteration is complete
        for client in disconnected_clients:
            wss_client.remove(client)

# Function to handle incoming WebSocket connections.
async def handle_client(websocket, path):
    wss_client.add(websocket)
    addr = websocket.remote_address
    print(f'Accepted connection from {addr}')
    
    try:
        async for message in websocket:
            if not message.strip():  # Check if the message is empty or just whitespace
                print(f"Received empty message from {addr}")
                continue

            try:
                await remove_staled_user()
                # print("MESSAGE ==> ", message)
                data = json.loads(message)
                uuid = data.get("uuid", None)
                role = data.get("role", None)
                text_message = data.get("message", None)
                position = data.get("position", {})
                rotation = data.get("rotation", {})
                code = data.get('code', None)
               
                if uuid is not None and role is not None and code is not None and text_message is not None:
                    if role == "Host":
                        
                        if isinstance(track_supported, list) and text_message in track_supported:
                            await register_user(userUUID=uuid,  userRole=role, organSelected=text_message, position=position, rotation=rotation, code=code)

               
                if len(clients) > 0:
                    for client in clients:
                        # await websocket.send(json.dumps(clients[client]))
                        await broad_cast(clients[client])
                    
                # Print out parsed details
                # print(f"Received message from {addr}:")
                # print(f"  UUID: {uuid}")
                # print(f"  Role: {role}")
                # print(f"  Message: {text_message}")
                # print(f"  Position: {position}")
                # print(f"  Rotation: {rotation}")

            except json.JSONDecodeError as e:
                # Log error and problematic message
                print(f"Invalid JSON from {addr}: {message}")
                print(f"Error: {e}")
            
    except websockets.ConnectionClosedError:
        print(f'Connection closed unexpectedly for {addr}')
    except Exception as e:
        print(f"Unexpected error from {addr}: {e}")
    # finally:
    #     print(f'Connection with {addr} closed.')

# This function initializes and starts the WebSocket server.
async def unity_websocket():
    server = await websockets.serve(handle_client, HOST, PORT)
    current_time_gmt = datetime.now(timezone.utc)
    
    print(f'WebSocket server started at {current_time_gmt}, server port: {PORT}')

    async with server:
        await server.wait_closed()

# Run the WebSocket server.
if __name__ == "__main__":
    asyncio.run(unity_websocket())
