# This code requires the 'requests' library. Install it with 'pip install requests'

import socket
import datetime
import requests


def parse_message(raw):
    parts = raw.strip().split(',')
    if not parts:
        return "Invalid message"

    msg_type = parts[0]
    try:
        if msg_type == "BSM":
            return {
                "type": "BSM (Basic Safety Message)",
                "timestamp": float(parts[1]),
                "receiver_id": parts[2],
                "sender_id": parts[3],
                "sender_pos_x": float(parts[4]),
                "sender_pos_y": float(parts[5]),
                "receiver_pos_x": float(parts[6]),
                "receiver_pos_y": float(parts[7]),
                "distance": float(parts[8])
            }
        elif msg_type == "WSM":
            return {
                "type": "WSM (Wave Short Message)",
                "timestamp": float(parts[1]),
                "receiver_id": parts[2],
                "message_name": parts[3],
                "sender_pos_x": float(parts[4]),
                "sender_pos_y": float(parts[5]),
                "receiver_pos_x": float(parts[6]),
                "receiver_pos_y": float(parts[7]),
                "distance": float(parts[8])
            }
        elif msg_type == "WSA":
            return {
                "type": "WSA (Service Advertisement)",
                "timestamp": float(parts[1]),
                "receiver_id": parts[2],
                "service_description": parts[3]
            }
        else:
            return {"type": "Unknown", "raw_message": raw}
    except Exception as e:
        return {"error": f"Failed to parse: {str(e)}", "raw": raw}


def format_message(parsed_msg):
    if isinstance(parsed_msg, str):
        return parsed_msg

    if "error" in parsed_msg:
        return f"ERROR: {parsed_msg['error']} | Raw: {parsed_msg['raw']}"

    msg_type = parsed_msg.get("type", "Unknown")

    if "BSM" in msg_type:
        return (f"{msg_type} | Time: {parsed_msg['timestamp']:.2f} | "
                f"Receiver: {parsed_msg['receiver_id']} | Sender: {parsed_msg['sender_id']} | "
                f"Sender Pos: ({parsed_msg['sender_pos_x']:.2f}, {parsed_msg['sender_pos_y']:.2f}) | "
                f"Receiver Pos: ({parsed_msg['receiver_pos_x']:.2f}, {parsed_msg['receiver_pos_y']:.2f}) | "
                f"Distance: {parsed_msg['distance']:.2f} m")

    elif "WSM" in msg_type:
        return (f"{msg_type} | Time: {parsed_msg['timestamp']:.2f} | "
                f"Receiver: {parsed_msg['receiver_id']} | Message: {parsed_msg['message_name']} | "
                f"Sender Pos: ({parsed_msg['sender_pos_x']:.2f}, {parsed_msg['sender_pos_y']:.2f}) | "
                f"Receiver Pos: ({parsed_msg['receiver_pos_x']:.2f}, {parsed_msg['receiver_pos_y']:.2f}) | "
                f"Distance: {parsed_msg['distance']:.2f} m")

    elif "WSA" in msg_type:
        return (f"{msg_type} | Time: {parsed_msg['timestamp']:.2f} | "
                f"Receiver: {parsed_msg['receiver_id']} | Service: {parsed_msg['service_description']}")

    else:
        return f"Unknown message type | Raw: {parsed_msg.get('raw_message', str(parsed_msg))}"


def main():
    HOST = '127.0.0.1'
    PORT = 5005

    print(f"Listening for structured UDP messages on {HOST}:{PORT}...\n")

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind((HOST, PORT))

        try:
            while True:
                data, addr = sock.recvfrom(1024)
                message = data.decode(errors='replace')
                parsed = parse_message(message)

                # Send to server if valid message
                if isinstance(parsed, dict) and "type" in parsed and parsed["type"] in ["BSM (Basic Safety Message)",
                                                                                        "WSM (Wave Short Message)",
                                                                                        "WSA (Service Advertisement)"]:
                    try:
                        response = requests.post("http://localhost:8000/receive_message", json=parsed, timeout=5)
                        if response.status_code != 200:
                            print(f"Failed to send message: {response.status_code}")
                    except requests.exceptions.RequestException as e:
                        print(f"Error sending message: {e}")

                formatted_output = format_message(parsed)
                print(formatted_output, flush=True)

        except KeyboardInterrupt:
            print("\nServer stopped by user.")


if __name__ == "__main__":
    main()