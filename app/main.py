import sys
import shutil
import os
import subprocess
import shlex


def main():
    # TODO: Uncomment the code below to pass the first stage
    while True:
        sys.stdout.write("$ ")
        command = input()
        str_split = shlex.split(command)
        f = sys.stdout
        if not str_split:
            continue
        if command == "exit":
            break
        
        if ">" in command:
            cmd_part, fileName_part = command.split(">", 1)
            str_split = shlex.split(cmd_part)
            f = open(fileName_part.strip(), "w")
            if cmd_part.endswith(1):
                cmd_part= cmd_part[:-1]
        else:
            str_split =shlex.split(command)
        
        if str_split[0] == "echo":
            print(" ".join(str_split[1::]), file = f)
            
            
        elif str_split[0] == "pwd":
            print(os.getcwd())
        #for cd
        elif str_split[0] == "cd":
            if len(str_split) >1:
                cdpath = str_split[1]
                # Convert shortcuts like '~' into the full home directory path
                cdpath = os.path.expanduser(cdpath)
                try:
                    # Tell the Kernel to move this process's 'marker' to the new location
                    os.chdir(cdpath)
                except FileNotFoundError:
                    print(f"cd: {cdpath}: No such file or directory")
            else:
                # Default behavior: If user just types 'cd', move to the Home folder
                os.chdir(os.path.expanduser("~"))
                
        elif str_split[0] == "type":
            builtin = ["exit", "echo","type","pwd","cd"]
            if str_split[1] in builtin:
                print(str_split[1]+" is a shell builtin")
            elif shutil.which(str_split[1]):
                path = shutil.which(str_split[1])
                print(str_split[1]+ " is "+path)
            else:
                print(str_split[1]+": "+"not found")
        
        else:
            # grab the command name(eg., 'ls') and search the sys PATH for its file Location.
            command_name = str_split[0]
            path = shutil.which(command_name) #This looks in /usr/bin, /bin, etc.
            args = str_split[1:] #collect everything after command name
            if path:
                #in "child process" we pass the short name in list, full path -> executable
                subprocess.run(str_split, stdout=f)
            else:
                print(command+": "+"command not found")
        if f is not sys.stdout:
                f.close() 


if __name__ == "__main__":
    main()
