#
#   Hello World client in Python
#   Connects REQ socket to tcp://localhost:5555
#
import zmq


def main():
    context = zmq.Context()
    #  Socket to talk to server
    print("Connecting to Paddle Server…")
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:5555")

    #  Do 2 requests, waiting each time for a response
    VIDEO_FILE_PATHS = [
        "dataset/ict/CAM1-Case18-Low.mp4",
        "dataset/ict/CAM2-Case18-Low.mp4",
    ]
    try:
        for i, p in enumerate(VIDEO_FILE_PATHS):
            print(f"Sending Video: {i} ...")
            socket.send_string(p)
            #  Get the reply.
            message = socket.recv()
            print(f"Received reply {i}, Status: {message}")
    except KeyboardInterrupt:
        print("W: interrupt received, stopping...")
    finally:
        # clean up
        socket.close()
        context.term()


if __name__ == "__main__":
    main()
