import os
secret_key = os.urandom(24)  # 24 bytes ka random key generate karta hai
print("Key:",secret_key)