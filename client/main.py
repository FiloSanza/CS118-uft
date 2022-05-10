import socket
import pickle

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
payload = payload = pickle.dumps(('list', {'name': "mario", 'age': 18}))
s.sendto(payload, ('localhost', 12345))
raw_data, addr = s.recvfrom(4096)
data = pickle.loads(raw_data)
print(data)

info = "\n".join([name + " - " + size for name, size in pickle.loads(data["data"])])

print(info)