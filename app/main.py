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
        
        if not str_split:
            continue
        if command == "exit":
            break
        
        elif str_split[0] == "echo":
            q = " ".join(str_split[1::])
            q_replace = q.replace("'","").replace('"',"")
            print(q_replace)
            
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
                subprocess.run([command_name] + args, executable = path)
            else:
                print(command+": "+"command not found")
    


if __name__ == "__main__":
    main()
