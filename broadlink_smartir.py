import broadlink
import sys
import base64
import codecs
import time
import json
from broadlink.exceptions import ReadError, StorageError

TICK = 32.84
TIMEOUT = 30
IR_TOKEN = 0x26


def list_m(title, modes):
    print(title)
    for i in range(len(modes)):
        print(f"{i+1}. " + f'"{modes[i]}"')


def format_durations(data):
    result = ''
    for i in range(0, len(data)):
        if len(result) > 0:
            result += ' '
        result += ('+' if i % 2 == 0 else '-') + str(data[i])
    return result


def to_microseconds(bytes):
    result = []
    #  print bytes[0] # 0x26 = 38for IR
    index = 4
    while index < len(bytes):
        chunk = bytes[index]
        index += 1
        if chunk == 0:
            chunk = bytes[index]
            chunk = 256 * chunk + bytes[index + 1]
            index += 2
        result.append(int(round(chunk * TICK)))
        if chunk == 0x0d05:
            break
    return result


def learn_cmd(dev):
    dev.enter_learning()
    print("Learning...")
    start = time.time()
    while time.time() - start < TIMEOUT:
        time.sleep(1)
        try:
            data = dev.check_data()
        except (ReadError, StorageError):
            continue
        else:
            break
    else:
        print("No data received...")
        return ""
    learned = ''.join(format(x, '02x') for x in bytearray(data))

    decode_hex = codecs.getdecoder("hex_codec")
    return str(base64.b64encode(decode_hex(learned)[0]))[2:-1] + "=="


while len(devices := broadlink.discover(timeout=5, discover_ip_address=input("broadlink controller IP adress:"))) < 1:
    while (cont := input("No device found. Do you wish to try again?(y/n)").lower()) not in {"y", "yes", "n", "no"}:
        print("Invalid Answer")
    if cont.lower() in {"n", "no"}:
        sys.exit()
device = devices[0]
if device.is_locked:
    print("Device is locked please unlock it using broadlink app")
    sys.exit()
if not device.auth():
    print("Error authenticating with device")
    sys.exit()

host = device.host[0]
print(f"Connected to {host}")

modes = [w.strip() for w in input(
    "\nType AC operation modes separated by ','(comma): ").split(",")]

list_m("operation modes", modes)
while (cont := input("\nare the operations modes correct? (y/n/cancel)").lower()) not in {"y", "yes"}:

    if cont in {"n", "no"}:
        modes = [w.strip() for w in input(
            "\nType AC operation modes separated by ','(comma): ").split(",")]
    elif cont == "cancel":
        sys.exit()
    else:
        print("Invalid answer")
    list_m("operation modes", modes)

fan_modes = [w.strip() for w in input(
    "Type AC fan modes separated by ','(comma): ").split(",")]

list_m("fan modes", fan_modes)
while (cont := input("are the fan modes correct? (y/n/cancel)").lower()) not in {"y", "yes"}:

    if cont in {"n", "no"}:
        fan_modes = [w.strip() for w in input(
            "Type AC fan modes separated by ','(comma): ").split(",")]
    elif cont == "cancel":
        sys.exit()
    else:
        print("Invalid answer")
    list_m("fan modes", fan_modes)
min_temp = None

while not min_temp:
    try:
        temp = int(input("\n\nType minimum temparature of your ac:"))
    except ValueError:
        print("Not a valid integer number.")
        continue
    min_temp = temp

max_temp = None
while not max_temp:
    try:
        temp = int(input("\n\nType maximum temparature of your ac:"))
    except ValueError:
        print("Not a valid integer number.")
        continue
    max_temp = temp


print(min_temp, max_temp)
data = {"manufacturer": "Custom",
        "supportedModels": [
            "Custom"
        ],
        "commandsEncoding": "Base64",
        "supportedController": "Broadlink",
        "minTemperature": min_temp,
        "maxTemperature": max_temp,
        "precision": 1, }

input("Press ENTER to learn off command")
while(cmd := learn_cmd(device)) == "":
    print("No data received")
    input("press ENTER to try leaning OFF again.")
data["commands"] = {"off": cmd}

for mode in modes:
    data["commands"][mode] = dict()
    for fan_mode in fan_modes:
        data["commands"][mode][fan_mode] = dict()
        temp = min_temp
        print(f"\nmode: {mode}, fan mode: {fan_mode}")
        input(f"press ENTER to learn next command.")
        while temp in range(min_temp, max_temp+1):
            print(
                f"\n\nwaiting for mode: {mode}, fan: {fan_mode}, temp:{temp} command")
            while (cmd := learn_cmd(device)) == "":
                print("No data received")
                input("Press ENTER to try again")
                continue
            else:
                print("\nLearned Command.")
                print(f"press ENTER to learn next command.")
                if input("type 'retry'or 'r' to relearn this command").lower() in {"retry", "r"}:
                    continue
                else:
                    data["commands"][mode][fan_mode][temp] = cmd
                    temp += 1

print("all commands learned.")

with open("3300.JSON", "w") as file:
    json.dump(data, file, indent=4)

print("file saved.")
