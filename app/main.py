import io
import sys
import shutil
import os
import subprocess
import shlex
import readline
import contextlib

History = []
last_written_index = 0

SHELL_builtin = ["exit", "echo","type", "pwd", "cd", "history"]

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

def longest_common_prefix(strings):
    if not strings:
        return ""
    
    prefix = strings[0]
    
    for s in strings[1:]:
        i = 0
        while i< len(prefix) and i < len(s) and prefix[i] == s[i]:
            i +=1
        prefix = prefix[:i]
        if not prefix:
            break
    return prefix
            
last_text = None
tab_count = 0
def auto_completion(text, state):
    global last_text, tab_count
    matches = sorted([command for command in ALL_COMMANDS if command.startswith(text)])    
    
    if not matches:
        return None
    
    if len(matches)==1:
        if state == 0:
            return matches[0]+ " "
        return None
    
    lcp = longest_common_prefix(matches)
    if len(lcp) > len(text): 
        last_text = lcp 
        tab_count = 0      
        if state == 0:
            return lcp
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
    
def capture_builtin_output(cmd_parts):
    """
    Runs a builtin command and captures its stdout as a string.
    Used for the LEFT side of a pipe (eg., 'echo hi |..')
    """
    buffer = io.StringIO()
    
    with contextlib.redirect_stdout(buffer):
        if cmd_parts[0] == "echo":  
            print(" ".join(cmd_parts[1:]))
        
        elif cmd_parts[0] == "history":
            for i, cmd in enumerate(History, start =1):
                print(f"{i:>5} {cmd}")
               
        elif cmd_parts[0] == "type":
            #fix: added length check to prevent crash
            
            builtin = ["exit", "echo","type", "pwd", "cd", "history"]
            if len(cmd_parts)>1:
                if cmd_parts[1] in builtin:
                    print(cmd_parts[1]+ " is a shell builtin")
                elif shutil.which(cmd_parts[1]):
                    print(cmd_parts[1]+ " is " + shutil.which(cmd_parts[1]))
                else:
                    print(cmd_parts[1] + " not found")
                    
        elif cmd_parts[0] == "pwd":
            print(os.getcwd())
                
    return buffer.getvalue()

def run_builtin(cmd_parts):
    """
    Used For the RIGHT/LAST side of a pipe.
    """
    if cmd_parts[0] == "echo":
        print(" ".join(cmd_parts[1:]))
        
    elif cmd_parts[0] == "history":
        for i, cmd in enumerate(History, start =1):
            print(f"{i:>5} {cmd}")

    elif cmd_parts[0] == "type":
        
        if len(cmd_parts)>1:
            builtin = ["exit", "echo", "type", "pwd", "cd","history"]
            if cmd_parts[1] in builtin:
                print(f"{cmd_parts[1]} is a shell builtin")
            elif shutil.which(cmd_parts[1]):
                print(f"{cmd_parts[1]} is {shutil.which(cmd_parts[1])}")
            else:
                print(f"{cmd_parts[1]} not found")

    elif cmd_parts[0] == "pwd":
        print(os.getcwd())   
        
# mail shell loop
def main():
    
    readline.set_completer(auto_completion)
    if 'libedit' in readline.__doc__:
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")
    
    # TODO: Uncomment the code below to pass the first stage
    global last_written_index
    while True: 
        try:
            sys.stdout.write("$ ")# force prompt to print whenever a new command starts
            sys.stdout.flush()
            try:
                #capture history length Before input
                pre_len = readline.get_current_history_length()
                command = input()
                
                #Capture history length After input
                post_len = readline.get_current_history_length()
                
                
            except EOFError:
                break
            if not command.strip():
                continue
            
            if post_len == pre_len:
                readline.add_history(command)
                
            History.append(command)
            
            try:
                if "|" in command:
                    try:
                        parts_raw = command.split("|")
                        parts = []
                        for p in parts in parts_raw:
                            s = shlex.split(p.strip())
                            if s:parts.append(s)
                    except ValueError:
                        print("Syntax error: checking for pipes blindly", file=sys.stderr)
                        continue #History is already saved, so safe to continue
                    
                    if not parts : continue
                    
                    has_builtin = any(p[0] in SHELL_builtin for p in parts if p)
                    
                    # ===============================
                    # CASE 1: NO BUILTINS (pure external pipeline)
                    # ===============================
                    
                    if not has_builtin:
                        prev_pipe = None
                        processes = []
                        for i, args in enumerate(parts):
                            if not args: continue #skip empty parts
                            stdin = prev_pipe
                            stdout = subprocess.PIPE if i<len(parts) - 1 else sys.stdout
                        
                            #safe execution
                            executable = shutil.which(args[0])
                            if not executable:
                                print(f"{args[0]}: command not found", file=sys.stderr)
                                prev_pipe = None #break the chain data
                                break
                            
                            p = subprocess.Popen(
                                args,
                                stdin= stdin,
                                stdout = stdout,
                                stderr=sys.stderr
                            )
                        
                            if prev_pipe is not None:
                                prev_pipe.close()
                            
                            prev_pipe = p.stdout
                            processes.append(p)
                        
                        for p in processes:
                            p.wait()
                        continue
                    
                    # ===============================
                    # CASE 2: PIPELINE WITH BUILTIN
                    # ===============================
                    i = 0
                    prev_output = None
                    
                    while i<len(parts):
                        args =parts[i]
                        is_builtin = args[0] in SHELL_builtin
                        is_last =(i== len(parts)-1)
                        
                        if is_builtin and prev_output is None and is_last:
                            run_builtin(args)
                            break
                        #Builtin | external
                        if is_builtin:
                            prev_output = capture_builtin_output(args)
                            i+=1
                            continue
                        # external command
                        p = subprocess.Popen(
                            args,
                            stdin = subprocess.PIPE,
                            stdout = subprocess.PIPE if not is_last else sys.stdout,
                            stderr = sys.stderr
                        )
                        
                        if prev_output is not None:
                            prev_output, _ = p.communicate(prev_output.encode())
                        else:
                            p.wait()
                        i +=1
                    continue
                    
                global last_text, tab_count
                last_text = None
                tab_count = 0
                
                try:
                    str_split = shlex.split(command)
                except ValueError:
                    print(f"syntax error:{command}", file= sys.stderr)
                    continue
                
                if not str_split:
                    continue    
                #redierection setup 
                f_out = sys.stdout
                f_err = sys.stderr
                
                #check for redirection operators(simplifed safe check)
                operator = None
                is_error = False
                mode = 'w'
                
                
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
                    try:
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
                    except Exception as e:
                        print(f"Redirection error: {e}", file=sys.stderr)
        
                cmd = str_split[0]
                if cmd == "exit":
                    sys.exit(0)
                    
                elif cmd == "echo":
                    print(" ".join(str_split[1:]), file = f_out)
                    
                elif cmd == "pwd":
                    # Navigation: Finding where we are
                    print(os.getcwd(), file=f_out)
                #for cd
                elif cmd == "cd":

                    path = str_split[1] if len(str_split)>1 else "~"
                    #handle shortcuts
                    path = os.path.expanduser(path)
                    try:
                        os.chdir(path)
                    except FileNotFoundError:
                        print(f"cd: {path}: No such file or directory", file = f_err)
                
                elif cmd == "history":
                    
                    #history -a <file> APPEND
                    if len(str_split) > 2 and str_split[1] == "-a":
                        file_path = str_split[2]
                        
                        try:
                            with open(file_path, "a") as f:
                                for h_cmd in History[last_written_index:]:
                                    f.write(h_cmd + "\n")
                            last_written_index = len(History)
                        except Exception: pass
                    
                    #history -w <file> WRITE FILE 
                    elif len(str_split) > 2 and str_split[1] == "-w":
                        file_path = str_split[2]
                        
                        try:
                            with open(file_path, "w") as f:
                                for h_cmd in History:
                                    f.write(h_cmd + "\n")
                        except FileNotFoundError: pass
                        
                    #history -r <file> (READ FROM FILE)
                    elif len(str_split) > 2 and str_split[1] == "-r":
                        file_path = str_split[2]
                        
                        try:
                            with open(file_path, "r") as f:
                                for line in f:
                                    h_cmd = line.strip()
                                    if h_cmd: #ignore empty lines
                                        History.append(h_cmd)
                                        readline.add_history(h_cmd)
                            
                            last_written_index = len(History)
                        except FileNotFoundError:pass
                    
                    else:
                        #history with number
                        n = int(str_split[1]) if len(str_split) >1 and str_split[1].isdigit() else len(History)
                        start = max(0, len(History) - n)
                        
                        for i in range(start, len(History)):
                            print(f"{i+1:>5}  {History[i]}", file = f_out)
                            
                elif cmd == "type":
                    if len(str_split) >1:
                        target =str_split[1]
                        builtin = ["exit", "echo","type","pwd","cd", "history"]
                    if target in builtin:
                        print(f"{target}+ is a shell builtin", file = f_out)
                    elif shutil.which(target):
                        print(f"{target}+ is {shutil.which(target)}", file = f_out)
                        print(str_split[1]+ " is "+path)
                    else:
                        print(f"{target}: not found", file =f_out)
                
                
                else:
                    # EXTERNAL COMMANDS & REDIRECTION
                    exe =shutil.which(cmd)
                    if exe:
                        subprocess.run(str_split, stdout= f_out, stderr = f_err)
                    else:
                        print(f"{cmd}: command not found", file = f_err)
        
                # CLEANUP
                    if f_out is not sys.stdout: f_out.close() 
                    if f_err is not sys.stderr: f_err.close()
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                
        except KeyboardInterrupt:
            print()
            continue



if __name__ == "__main__":
    main()
