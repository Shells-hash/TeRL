from bridge_client import BridgeClient
import time

def main():
    client = BridgeClient()
    client.connect()
    print("Connected.")

    try:
        while True:
            state = client.send_action(2)  # move right
            print("Tick:", state["tick"])
            time.sleep(0.1)  # match 10Hz
    except KeyboardInterrupt:
        pass
    finally:
        client.close()

if __name__ == "__main__":
    main()
