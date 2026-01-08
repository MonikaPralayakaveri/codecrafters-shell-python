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
            if str_split[1] == "exit" or str_split[1] == "echo" or str_split[1] =="type" or command == "pwd":
                print(str_split[1]+" is a shell builtin")
            elif shutil.which(str_split[1]):
                path = shutil.which(str_split[1])
                print(str_split[1]+ " is "+path)
            else:
                print(str_split[1]+": "+"not found")
        
        else:
            if str_split:
                command_name = str_split[0]
                path = shutil.which(command_name)
                args = str_split[1:]
                if path:
                    subprocess.run([command_name] + args, executable = path)
                else:
                    print(command+": "+"command not found")
    


if __name__ == "__main__":
    main()
