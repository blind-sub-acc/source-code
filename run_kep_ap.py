import os
import subprocess
import shutil
import re
import random
import sys

COMPUTING_PEERS = 3
PROTOCOL = "replicated-field-party.x"
PROGRAM = "KEP_AP"
BATCHSIZE = "10000"

WARNING_COLOR = "\033[92m"
END_COLOR = "\033[0m"
OUTPUT_COLORS = ["\033[94m", "\033[95m", "\033[96m", "\033[91m"]


def execute(cmd, currwd, prnt):
    """
    Helper method. Wraps around subprocess Popen.
    Executes one command after printing a descriptor, then continually prints that commands output/err.
    """

    print(prnt)

    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=currwd, universal_newlines=True)

    for line in popen.stdout:
        print(line, end='')

    popen.stdout.close()
    return_code = popen.wait()

    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)


def generate_random_input(input_peers):
    """
    Create random example inputs for those input peers for which no input data is specified under 'protocols/Inputs'.
    """

    for i in range(input_peers):
        f_name = f"smpc_protocols/Inputs/input_{i}.txt"
        if os.path.isfile(f_name):
            continue
        print("Generating random input for client "+str(i))
        with open(f_name, "w") as file:
            # meaning: Bloodtype indicator, HLA-A, -B, -C, -DR, -DQ, -DP
            input_lengths = [4, 59, 132, 48, 61, 26, 22]
            donor_blood_type = random.randint(0, 3)
            patient_blood_type = random.randint(0, 3)
            for k in input_lengths:
                if k == 4:
                    if donor_blood_type == 0:
                        donor_bloodtype_indicator = "1 1 1 1\n"
                    elif donor_blood_type == 1:
                        donor_bloodtype_indicator = "0 1 0 1\n"
                    elif donor_blood_type == 2:
                        donor_bloodtype_indicator = "0 0 1 1\n"
                    else:
                        donor_bloodtype_indicator = "0 0 0 1\n"
                    file.write(donor_bloodtype_indicator)
                else:
                    for j in range(k-1):
                        file.write("0 ")
                    file.write("0\n")

            for k in input_lengths:
                if k == 4:
                    if patient_blood_type == 0:
                        patient_bloodtype_indicator = "1 0 0 0\n"
                    elif patient_blood_type == 1:
                        patient_bloodtype_indicator = "0 1 0 1\n"
                    elif patient_blood_type == 2:
                        patient_bloodtype_indicator = "0 0 1 1\n"
                    else:
                        patient_bloodtype_indicator = "1 1 1 1\n"
                    file.write(patient_bloodtype_indicator)
                else:
                    for j in range(k-1):
                        file.write("0 ")
                    file.write("0\n")

            # add random pre-score
            file.write(str(random.randint(0, 200))+"\n")
            prio_input_lengths = [59, 132, 61]
            for k in prio_input_lengths:
                for j in range(k-1):
                    file.write("0 ")
                file.write("0\n")
            # add patient and donor blood type
            file.write(str(patient_blood_type+1)+"\n")
            file.write(str(donor_blood_type+1) + "\n")
            # add random patient and donor age
            file.write(str(random.randint(10, 100)) + "\n")
            file.write(str(random.randint(10, 100)) + "\n")
            # add random patient and donor region
            region = random.randint(0, 11)
            file.write(str(region) + "\n")
            file.write(str(region) + "\n")


def compile_code(clients):
    # modify the mpc files for the current number of clients
    with open("smpc_protocols/Programs/Source/KEP_AP.mpc", "r") as file:
        text = file.read()

    text = re.sub(r"NUM_NODES = \d+", f"NUM_NODES = {clients}", text)
    s_len_two = int(clients * (clients - 1) / 2)
    s_len_three = int(clients * (clients - 1) * (clients - 2) / 6)
    text = re.sub(r"S_LENGTH = \d+", f"S_LENGTH = {s_len_two + s_len_three}", text)
    text = re.sub(r"S_LENGTH_TWO = \d+", f"S_LENGTH_TWO = {s_len_two}", text)
    text = re.sub(r"S_LENGTH_THREE = \d+", f"S_LENGTH_THREE = {s_len_three}", text)

    with open("smpc_protocols/Programs/Source/KEP_AP.mpc", "w+") as file:
        file.write(text)

    # copy the inputs of the patient-donor pairs to the MP-SPDZ directory
    try:
        execute(["rm", "-r", "./ExternalIO/Inputs/"], "./MPSPDZ/", "\n\nRemoving old Input Data")
    except subprocess.CalledProcessError:
        line = "No old Input Data available.\n\n"
        print(f"{WARNING_COLOR}{line}{END_COLOR}", end='')

    execute(["cp", "-r", "../smpc_protocols/Inputs/", "./ExternalIO/"], "./MPSPDZ/", "\n\nCopying Input Data")

    # copy the custom code to the MP-SPDZ directory
    with open("smpc_protocols/deltas.txt", "r") as deltas:
        for line in deltas:
            target = line.split(">")
            target = [elem.strip() for elem in target]
            try:
                if os.path.exists(target[1]):
                    shutil.rmtree(target[1])
                shutil.copytree(target[0], target[1])
            except NotADirectoryError:
                shutil.copy(target[0], target[1])

    # Cleanup the old player data
    try:
        execute(["rm", "-r", "./Player-Data/", "../smpc_protocols/Player-Data/"], "./MPSPDZ/", "\n\nRemoving old Player Data")
    except subprocess.CalledProcessError:
        line = "No old Player Data available.\n\n"
        print(f"{WARNING_COLOR}{line}{END_COLOR}", end='')

    # run the setup scripts for the computing peers and the patient-donor pairs
    try:
        execute(["./Scripts/tldr.sh"], "./MPSPDZ/", "\n\nExecuting 'tldr.sh'")
        execute(["./Scripts/setup-ssl.sh", str(COMPUTING_PEERS)], "./MPSPDZ/", "\n\nExecuting 'setup-ssl.sh'")
        execute(["./Scripts/setup-clients.sh", str(clients)], "./MPSPDZ/", "\n\nExecuting 'setup-clients.sh'")

    except subprocess.CalledProcessError:
        line = "MPSPDZ setup scripts returned exit status 1. If this is your first compilation run please abort and fix here.\n\n"
        print(f"{WARNING_COLOR}{line}{END_COLOR}", end='')

    # compile the MP-SPDZ program KEP_AP
    execute(["../MPSPDZ/compile.py", "KEP_AP"], "./smpc_protocols", "\n\nExecuting /MPSPDZ/compile.py KEP_AP")

    execute(["cp", "-r", "../MPSPDZ/Player-Data/", "."], "./smpc_protocols", "\n\nCopying Player Data to smpc_protocols")


def run(clients):
    # start all computing peers
    popen_first = subprocess.Popen(
        ["../MPSPDZ/" + str(PROTOCOL), "-b", BATCHSIZE, "-h",
         "localhost", "0", PROGRAM],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd="./smpc_protocols", universal_newlines=True)

    for i in range(1, COMPUTING_PEERS):
        subprocess.Popen(
            ["../MPSPDZ/" + str(PROTOCOL), "-b", BATCHSIZE, "-h",
             "localhost", str(i),
             PROGRAM], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd="./smpc_protocols", universal_newlines=True)

    # start sending the input of the patient-donor pairs
    popen_clients = []

    for i in range(int(clients)):
        if i == (int(clients) - 1):
            popen_clients.append(
                subprocess.Popen(
                    ["python", "ExternalIO/kidney-exchange-client.py", str(i), str(COMPUTING_PEERS), str(clients), "1"],
                    stdout=subprocess.PIPE, cwd="./MPSPDZ", universal_newlines=True))
        else:
            popen_clients.append(
                subprocess.Popen(
                    ["python", "ExternalIO/kidney-exchange-client.py", str(i), str(COMPUTING_PEERS), str(clients), "0"],
                    stdout=subprocess.PIPE, cwd="./MPSPDZ", universal_newlines=True))

    for line in popen_first.stdout:
        print(f"{WARNING_COLOR}{line}{END_COLOR}", end='')

    for i in range(len(popen_clients)):
        for line in popen_clients[i].stdout:
            print(f"{OUTPUT_COLORS[i%4]}{line}{END_COLOR}", end='')


def main():
    if len(sys.argv) > 1:
        clients = int(sys.argv[1])
    else:
        clients = 3

    clients = int(clients)

    generate_random_input(clients)
    compile_code(clients)
    run(clients)


if __name__ == "__main__":
    main()
