import sys
import shutil
import os


def main():
    # TODO: Uncomment the code below to pass the first stage
    while True:
        sys.stdout.write("$ ")
        command = input()
        str_split = command.split()
        valid_name = str_split[1]
        if command == "exit":
            break
        elif str_split[0] == "echo":
            print(" ".join(str_split[1::]))
        elif str_split[0] == "type":
            if str_split[1] == "exit" or str_split[1] == "echo" or str_split[1] =="type" :
                print(str_split[1]+" is a shell builtin")
            elif shutil.which(valid_name):
                command_path = shutil.which(valid_name)
                print(valid_name+ " is "+command_path)
            else:
                print(str_split[1]+": "+"not found")
        
        else:
            print(command+": "+"command not found")
    


if __name__ == "__main__":
    main()
