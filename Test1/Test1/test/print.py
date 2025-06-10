import argparse

def main():
    parser = argparse.ArgumentParser(description="Receive vehicle data from C++")
    parser.add_argument("--id", type=str, required=True, help="Sender ID")
    parser.add_argument("--speed", type=float, required=True, help="Speed (m/s)")
    parser.add_argument("--x", type=float, required=True, help="X position")
    parser.add_argument("--y", type=float, required=True, help="Y position")
    parser.add_argument("--z", type=float, required=True, help="Z position")

    args = parser.parse_args()

    print("\nReceived Vehicle Data from C++:")
    print(f"Sender ID: {args.id}")
    print(f"Speed: {args.speed} m/s")
    print(f"Position (X, Y, Z): ({args.x}, {args.y}, {args.z})")

if __name__ == "__main__":
    main()
