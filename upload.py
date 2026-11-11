# Sends a .hex program (one 16-bit hex word per line) to the Zenith-Core loader.
# Usage: python upload.py COM5 programs/fibo.hex
import sys, serial
port, path = sys.argv[1], sys.argv[2]
words = [int(l, 16) for l in open(path) if l.strip()]
data = bytes([0xAA, 0x55, len(words) >> 8, len(words) & 0xFF])
for w in words:
    data += bytes([w >> 8, w & 0xFF])
with serial.Serial(port, 115200) as s:
    s.write(data)
print(f"{len(words)} words sent")
