
import broadlink
import sys
import base64
import codecs
import time
import json
from broadlink.exceptions import ReadError, StorageError
from itertools import product, starmap
from collections import namedtuple
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
    print("Waiting command...")
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


# Gemnerate list of commands. This way the command learning logic doesnt have to be in nested loops.
# It also allows easy acess to the next command before the next loop iteration improving user experience.
# It will also make it easier to add preset modes support to the JSON file later.
def gen_cmd_list(data, mode_types, header_simple_cmds=["off"], footer_simple_cmds=[]):
    return header_simple_cmds + [dict(zip(mode_types, cmd)) for cmd in product(*data)] + footer_simple_cmds


def gen_cmd_desc(cmd):
    return " ".join([f"{name}: {value};" for name, value in cmd.items()])


while len(devices := broadlink.discover(timeout=5, discover_ip_address=input("broadlink controller IP adress: "))) < 1:
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

list_m("Operation modes", modes)
while (cont := input("\nAre the operations modes correct? (y/n/cancel) ").lower()) not in {"y", "yes"}:

    if cont in {"n", "no"}:
        modes = [w.strip() for w in input(
            "\nType AC operation modes separated by ','(comma): ").split(",")]
    elif cont == "cancel":
        sys.exit()
    else:
        print("Invalid answer")
    list_m("Operation modes", modes)

fan_modes = [w.strip() for w in input(
    "\nType AC fan modes separated by ','(comma): ").split(",")]

list_m("Fan modes", fan_modes)
while (cont := input("\nAre the fan modes correct? (y/n/cancel) ").lower()) not in {"y", "yes"}:

    if cont in {"n", "no"}:
        fan_modes = [w.strip() for w in input(
            "\nType AC fan modes separated by ','(comma): ").split(",")]
    elif cont == "cancel":
        sys.exit()
    else:
        print("Invalid answer")
    list_m("Fan modes", fan_modes)

while (cont := input("\nDo you want to add swing modes? (y/n) ").lower()) not in {"y", "yes", "no", "n"}:
    print("Invalid answer")

swing = False
if cont in {"y", "yes"}:
    swing = True
    swing_modes = [w.strip() for w in input(
        "\nType AC swing modes separated by ','(comma): ").split(",")]

    list_m("Swing modes", swing_modes)
    while (cont := input("\nAre the swing modes correct? (y/n/cancel) ").lower()) not in {"y", "yes"}:

        if cont in {"n", "no"}:
            swing_modes = [w.strip() for w in input(
                "\nType AC swing modes separated by ','(comma): ").split(",")]
        elif cont == "cancel":
            sys.exit()
        else:
            print("Invalid answer")
        list_m("Swing modes", swing_modes)

min_temp = None

while not min_temp:
    try:
        temp = int(input("\n\nType minimum temparature of your ac: "))
    except ValueError:
        print("Not a valid integer number.")
        continue
    min_temp = temp

max_temp = None
while not max_temp:
    try:
        temp = int(input("\n\nType maximum temparature of your ac: "))
    except ValueError:
        print("Not a valid integer number.")
        continue
    max_temp = temp
print("\n")

data = {"manufacturer": "Custom",
        "supportedModels": [
            "Custom"
        ],
        "commandsEncoding": "Base64",
        "supportedController": "Broadlink",
        "minTemperature": min_temp,
        "maxTemperature": max_temp,
        "precision": 1,
        "operationModes": modes,
        "fanModes": fan_modes,
        }
hierarchy = ["Mode", "Fan Mode", "Temperature"]
cmds_modes = [modes, fan_modes, range(
    min_temp, max_temp+1)]
if swing:
    data["swingModes"] = swing_modes
    hierarchy.insert(2, "Swing Mode")
    cmds_modes.insert(2, swing_modes)
cmds = gen_cmd_list(cmds_modes, hierarchy)


data["commands"] = dict()
learned_all = False


n_cmds = len(cmds)


cmd = cmds[0]
if isinstance(cmd, str):
    print("Next command: " + cmd)
else:
    print(
        f"Next command: \n" + gen_cmd_desc(cmd))

i = 0
input("Press ENTER to learn next command. \n \n")

while i in range(n_cmds):
    cmd = cmds[i]
    if isinstance(cmd, str):
        print("Learning command: " + cmd)
    else:
        print(
            f"Learning command: \n" + gen_cmd_desc(cmd))

    while (cmd_code := learn_cmd(device)) == "":
        print("No data received")
        input("Press ENTER to try again \n")
        continue

    print("Learned Command. \n")

    learned_all = i == n_cmds - 1

    if not learned_all:
        nxt_cmd = cmds[i+1]
        if isinstance(nxt_cmd, str):
            print("Next command: " + nxt_cmd)

        else:
            print(
                f"Next command: \n" + gen_cmd_desc(nxt_cmd))

        print(f"Press ENTER to learn next command.")

    if not learned_all and (input("type 'retry'or 'r' to relearn previous command\n").lower() in {"retry", "r"}):
        continue
    elif isinstance(cmd, str):
        data["commands"][cmd] = cmd_code
    else:
        cmds_data = data["commands"]
        for cmd_path in hierarchy[:-1]:
            cmds_data[cmd[cmd_path]] = cmds_data.get(cmd[cmd_path], dict())
            cmds_data = cmds_data[cmd[cmd_path]]
        cmds_data[cmd["Temperature"]] = cmd_code
    i += 1


if learned_all:
    print("All commands learned")

with open("3300.json", "w") as file:
    json.dump(data, file, indent=4)

print("file saved.")
