import sys
import shutil
import os
import subprocess
import shlex
import readline

def main():
    # TODO: Uncomment the code below to pass the first stage
    while True:
        sys.stdout.write("$ ")
        command = input()
        str_split = shlex.split(command)
        f_out = sys.stdout
        f_err = sys.stderr
        
        if not str_split:
            continue
        if command == "exit":
            break
        if "2>>" in command:
            operator, mode, is_error_redir ="2>>", "a", True
        elif "2>" in command:
            operator, mode, is_error_redir ="2>", "w", True   
        elif ">>" in command:
            operator, mode, is_error_redir =">>", "a", False
        elif ">" in command:
            operator, mode, is_error_redir =">", "w", False            
        else:
            operator = None
            
        if operator:
            cmd_part, fileName_part = command.split(operator, 1)
            if not is_error_redir and cmd_part.strip().endswith("1"):
                cmd_part= cmd_part.strip()[:-1]
                
            str_split = shlex.split(cmd_part)
            fileName = fileName_part.strip()
            
            os.makedirs(os.path.dirname(os.path.abspath(fileName)), exist_ok=True)
            f_file = open(fileName, mode)
            
            if is_error_redir:
                f_err = f_file
            else:
                f_out = f_file
            
        else:
            str_split =shlex.split(command)
        
        if str_split[0] == "echo":
            print(" ".join(str_split[1::]), file = f_out)
            
            
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
                subprocess.run(str_split, stdout=f_out, stderr = f_err)
            else:
                print(command_name+": "+"command not found", file = f_err)
        if f_out is not sys.stdout:
                f_out.close() 
        if f_err is not sys.stderr:
            f_err.close()


if __name__ == "__main__":
    main()
