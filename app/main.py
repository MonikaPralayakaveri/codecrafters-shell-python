import sys
import shutil
import os
import subprocess
import shlex
import readline

SHELL_builtin = ["exit", "echo","type", "pwd", "cd"]
last_text = None
tab_count = 0
def get_executables_from_path():
    executables = set()
    
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    
    for directory in path_dirs:
        
        #Skip if folder does not exist
        if not os.path.isdir(directory):
            continue
        
        try:
            #check each file in folder
            for file in os.listdir(directory):
                full_path = os.path.join(directory, file)
                
                #keep only executable files
                if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                    executables.add(file)
        except PermissionError:
            #some folders cannot be opened
            continue
    return list(executables)

ALL_COMMANDS = sorted(list(set(SHELL_builtin+ get_executables_from_path())))
            
last_text = None
tab_count = 0
def auto_completion(text, state):
    global last_text, tab_count
    matches = sorted([command for command in ALL_COMMANDS if command.startswith(text)])    
    
    if not matches:
        return None
    
    if state == 0:
        if text == last_text:
            tab_count += 1
        else:
            tab_count = 1
            last_text = text
        
        if len(matches)>1:
            if tab_count == 1:
                sys.stdout.write("\a")
                sys.stdout.flush()
                
            elif tab_count>=2:
                sys.stdout.write("\n")
                sys.stdout.write("  ".join(matches))
                sys.stdout.write("\n")

                sys.stdout.write("$ "+readline.get_line_buffer())
                sys.stdout.flush()   
            return None
    
    if len(matches)==1:
        if state == 0:
            return matches[0]+ " "
    return None
    
# mail shell loop
def main():
    
    readline.set_completer(auto_completion)
    if 'libedit' in readline.__doc__:
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")
    
    # TODO: Uncomment the code below to pass the first stage
    
    while True: 
        try:
            sys.stdout.write("$ ")
            # Reset tab state whenever a new command starts
            global last_text, tab_count
            last_text = None
            tab_count = 0
            
            if not command.strip():
                continue
                
            command = input()
            str_split = shlex.split(command)
            f_out = sys.stdout
            f_err = sys.stderr
            
            if not str_split:
                continue
            if command == "exit":
                break
            
            # --- REDIRECTON DETECTION ---
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
            
            # --- REDIRECTION PLUMBING ---
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
                # If no operator, we use the original parsed command
                str_split =shlex.split(command)
            
            if str_split[0] == "echo":
                print(" ".join(str_split[1::]), file = f_out)
                
                
            elif str_split[0] == "pwd":
                # Navigation: Finding where we are
                print(os.getcwd())
            #for cd
            elif str_split[0] == "cd":
                # NAVIGATION
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
                # EXTERNAL COMMANDS & REDIRECTION
                # grab the command name(eg., 'ls') and search the sys PATH for its file Location.
                command_name = str_split[0]
                path = shutil.which(command_name) #This looks in /usr/bin, /bin, etc.
                args = str_split[1:] #collect everything after command name
                if path:
                    #in "child process" we pass the short name in list, full path -> executable
                    subprocess.run(str_split, stdout=f_out, stderr = f_err)
                else:
                    print(command_name+": "+"command not found", file = f_err)
            # CLEANUP 
            if f_out is not sys.stdout:
                    f_out.close() 
            if f_err is not sys.stderr:
                f_err.close()
        except (EOFError, KeyboardInterrupt):
            break



if __name__ == "__main__":
    main()
