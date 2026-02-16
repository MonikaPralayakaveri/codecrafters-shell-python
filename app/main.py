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
        
def handle_pipeline(command):
    try:
        #1. parse all segments of the pipe
        parts_raw = command.split("|")
        parts = []
        for p in parts_raw:
            cleaned = shlex.split(p.strip())
            if cleaned:
                parts.append(cleaned)
        if not parts:
            return
        
        #2.check for builtins
        #Ensure we are checking against the global list SHELL_builtin
        
        has_builtin = False
        for p in parts:
            for p in parts:
                if p[0] in SHELL_builtin:
                    has_builtin = True
                    break
        #3.Case 1: Pure External Pipeline (cat | head | wc)
        if not has_builtin:
            prev_pipe = None
            processes = []
            
            for i, args in enumerate(parts):
                # 3. Case 1: Pure External Pipeline (cat | head | wc)
        if not has_builtin:
            prev_pipe = None
            processes = []
            
            for i, args in enumerate(parts):
                # Input comes from previous pipe (or None for first command)
                stdin = prev_pipe
                # Output goes to next pipe (or stdout for last command)
                stdout = subprocess.PIPE if i < len(parts) - 1 else sys.stdout
                
                # Check executable exists
                if not shutil.which(args[0]):
                    print(f"{args[0]}: command not found", file=sys.stderr)
                    # Stop the pipeline if a command is missing
                    return 

                p = subprocess.Popen(args, stdin=stdin, stdout=stdout, stderr=sys.stderr)
                
                # Close the write-end of the previous pipe (important!)
                if prev_pipe:
                    prev_pipe.close()
                
                # Save read-end for the next command
                prev_pipe = p.stdout
                processes.append(p)
            
            # Wait for all processes to finish
            for p in processes:
                p.wait()
            return

        # 4. Case 2: Mixed Pipeline (Builtins + External)
        i = 0
        prev_output = None # This stores the output string between steps
        
        while i < len(parts):
            args = parts[i]
            cmd_name = args[0]
            is_last_cmd = (i == len(parts) - 1)
            is_builtin_cmd = cmd_name in SHELL_builtin
            
            # Sub-case: Builtin at the very end (e.g., ... | echo)
            if is_builtin_cmd and prev_output is None and is_last_cmd:
                run_builtin(args)
                break
            
            # Sub-case: Builtin in the middle (e.g., echo ... | cat)
            if is_builtin_cmd:
                prev_output = capture_builtin_output(args)
                i += 1
                continue
            
            # Sub-case: External command
            # If we have input from a previous builtin, we pass it via communicate()
            p = subprocess.Popen(
                args,
                stdin=subprocess.PIPE, # Always pipe stdin to handle prev_output
                stdout=subprocess.PIPE if not is_last_cmd else sys.stdout,
                stderr=sys.stderr
            )
            
            input_bytes = prev_output.encode() if prev_output else None
            
            # Run the command
            # communicate() handles writing to stdin and closing it
            out_data, _ = p.communicate(input=input_bytes)
            
            if not is_last_cmd:
                # Capture output for the next loop iteration
                prev_output = out_data.decode() if out_data else ""
            
            i += 1

    except Exception as e:
        print(f"Pipeline Error: {e}", file=sys.stderr)
                  
        
# mail shell loop
def main():
    readline.set_completer(auto_completion)
    if 'libedit' in readline.__doc__:
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")
    
    global last_written_index
    
    while True: 
        try:
            # --- PROMPT & INPUT ---
            try:
                pre_len = readline.get_current_history_length()
                command = input("$ ") 
                post_len = readline.get_current_history_length()
            except EOFError:
                break
            
            if not command.strip():
                continue
            
            # --- HISTORY ---
            if post_len == pre_len:
                readline.add_history(command)
            History.append(command)
            
            # --- PROCESSING ---
            try:
                # 1. PIPELINE HANDLING
                if "|" in command:
                    handle_pipeline(command)
                    continue

                # 2. NORMAL PARSING
                try:
                    str_split = shlex.split(command)
                except ValueError:
                    print(f"syntax error: {command}", file=sys.stderr)
                    continue
                
                if not str_split: continue    

                # 3. REDIRECTION
                f_out = sys.stdout
                f_err = sys.stderr
                operator = None
                is_error_redir = False
                mode = 'w'
                
                if "2>>" in command: operator, mode, is_error_redir = "2>>", "a", True
                elif "2>" in command: operator, mode, is_error_redir = "2>", "w", True   
                elif ">>" in command: operator, mode, is_error_redir = ">>", "a", False
                elif ">" in command: operator, mode, is_error_redir = ">", "w", False            
                
                if operator:
                    try:
                        cmd_part, fileName_part = command.split(operator, 1)
                        if not is_error_redir and cmd_part.strip().endswith("1"):
                            cmd_part = cmd_part.strip()[:-1]
                            
                        str_split = shlex.split(cmd_part)
                        fileName = fileName_part.strip()
                        os.makedirs(os.path.dirname(os.path.abspath(fileName)), exist_ok=True)
                        f_file = open(fileName, mode)
                        
                        if is_error_redir: f_err = f_file
                        else: f_out = f_file
                    except Exception as e:
                        print(f"Redirection error: {e}", file=sys.stderr)
                
                # 4. EXECUTION
                cmd = str_split[0]

                if cmd == "exit":
                    sys.exit(0)
                elif cmd == "echo":
                    print(" ".join(str_split[1:]), file=f_out)
                elif cmd == "pwd":
                    print(os.getcwd(), file=f_out)
                elif cmd == "cd":
                    path = str_split[1] if len(str_split) > 1 else "~"
                    path = os.path.expanduser(path)
                    try:
                        os.chdir(path)
                    except FileNotFoundError:
                        print(f"cd: {path}: No such file or directory", file=f_err)
                elif cmd == "history":
                    if len(str_split) > 2 and str_split[1] == "-a":
                        file_path = os.path.expanduser(str_split[2])
                        try:
                            with open(file_path, "a") as f:
                                for h_cmd in History[last_written_index:]:
                                    f.write(h_cmd + "\n")
                            last_written_index = len(History)
                        except Exception: pass
                    elif len(str_split) > 2 and str_split[1] == "-w":
                        file_path = os.path.expanduser(str_split[2])
                        try:
                            with open(file_path, "w") as f:
                                for h_cmd in History:
                                    f.write(h_cmd + "\n")
                            last_written_index = len(History)
                        except Exception: pass
                    elif len(str_split) > 2 and str_split[1] == "-r":
                        file_path = os.path.expanduser(str_split[2])
                        try:
                            with open(file_path, "r") as f:
                                for line in f:
                                    h_cmd = line.strip()
                                    if h_cmd: 
                                        History.append(h_cmd)
                                        readline.add_history(h_cmd)
                            last_written_index = len(History)
                        except FileNotFoundError: pass
                    else:
                        n = int(str_split[1]) if len(str_split) > 1 and str_split[1].isdigit() else len(History)
                        start = max(0, len(History) - n)
                        for i in range(start, len(History)):
                            print(f"{i+1:>5}  {History[i]}", file=f_out)
                elif cmd == "type":
                    if len(str_split) > 1:
                        target = str_split[1]
                        if target in SHELL_builtin:
                            print(f"{target} is a shell builtin", file=f_out)
                        elif shutil.which(target):
                            print(f"{target} is {shutil.which(target)}", file=f_out)
                        else:
                            print(f"{target}: not found", file=f_out)
                else:
                    exe = shutil.which(cmd)
                    if exe:
                        subprocess.run(str_split, stdout=f_out, stderr=f_err)
                    else:
                        print(f"{cmd}: command not found", file=f_err)
        
                # 5. CLEANUP
                if f_out is not sys.stdout: f_out.close() 
                if f_err is not sys.stderr: f_err.close()

            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                
        except KeyboardInterrupt:
            print()
            continue

if __name__ == "__main__":
    main()