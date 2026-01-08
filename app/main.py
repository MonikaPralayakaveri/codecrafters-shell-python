import sys


def main():
    # TODO: Uncomment the code below to pass the first stage
    while True:
        sys.stdout.write("$ ")
        command = input()
        str_split = command.split()
        if command == "exit":
            break
        elif str_split[0] == "echo":
            print(" ".join(str_split[1::]))
        elif str_split[0] == "type" and str_split[1] == "exit" or str_split[1] == "echo":
            print(command+"is a shell builtin")
        else:
            print(command+": "+"command not found")
    


if __name__ == "__main__":
    main()
