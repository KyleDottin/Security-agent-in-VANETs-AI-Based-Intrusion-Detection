def add(a, b):
    return a + b

if __name__ == "__main__":
    import sys
    a = float(sys.argv[1])
    b = float(sys.argv[2])
    result = add(a, b)  # Example values
    with open('result.txt', 'w') as f:
        f.write(str(result))
