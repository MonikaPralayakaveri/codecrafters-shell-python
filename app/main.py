import sys
import shutil
import os
import subprocess


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
        elif str_split[0] == "type":
            if str_split[1] == "exit" or str_split[1] == "echo" or str_split[1] =="type" :
                print(str_split[1]+" is a shell builtin")
            elif shutil.which(str_split[1]):
                command_path = shutil.which(str_split[1])
                print(str_split[1]+ " is "+command_path)
            else:
                print(str_split[1]+": "+"not found")
        
        else:
            command_path = shutil.which(str_split[0])
            if command_path:
                subprocess.run([command_path] +str_split[1:])
            else:
                print(command+": "+"command not found")
    


if __name__ == "__main__":
    main()
