import requests
import tarfile
import glob
import os

MPSDZ_URL = 'https://github.com/data61/MP-SPDZ/releases/download/v0.3.3/mp-spdz-0.3.3.tar.xz'


def setup_mpspdz():
    print("Setting up MP-SPDZ. This may take a few minutes...")
    local_filename = MPSDZ_URL.split('/')[-1]
    r = requests.get(MPSDZ_URL)
    f = open(local_filename, 'wb')
    f.write(r.content)
    f.close()

    tar = tarfile.open(local_filename)
    tar.extractall("./")
    tar.close()
    os.remove(local_filename)
    mpspdz = glob.glob("mp-spdz-*")[0]
    os.rename(mpspdz, "./MPSPDZ")

def main():
    setup_mpspdz()

if __name__ == "__main__":
    main()