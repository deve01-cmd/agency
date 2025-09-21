from PIL import Image
from cryptography.fernet import Fernet
import base64, zlib

# Load key
with open("key.txt", "rb") as kf:
    key = kf.read()
cipher = Fernet(key)

# Step 1: extract bits from image efficiently
img = Image.open("stego.png").convert("RGB")
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

# Step 4: write back to exe
with open("recovered_payload.exe", "wb") as f:
    f.write(exe_data)

print("Recovered EXE size:", len(exe_data), "bytes")
