# Source Code for Protocol KEP-AP

The source code of the protocol KEP_AP is available in the file `smpc_protocols/Programs/Source/KEP_AP.mpc`. 

The two scripts `setup_mpspdz.py` and `run_kep_ap.py` can be used to setup MP-SPDZ and run an example execution of the protocol.


## Setup of MP-SPDZ
Our protocol is implemented using the secure multi-party computation benchmarking framework [MP-SPDZ](https://github.com/data61/MP-SPDZ). 
The requirements for MP-SPDZ are stated in the corresponding README file of MP-SPDZ: https://github.com/data61/MP-SPDZ/blob/v0.3.3/README.md.

After installing these requirements, execute: `python setup_mpspdz.py`

This downloads the correct version of MP-SPDZ and sets up all remaining files for running the protocols.

## Protocol Execution

Execute the following command to run the protocol KEP-AP:

`python run_kep_ap.py <number of patient-donor pairs>`

If you do not explicitly specify a number of patient-donor pairs, the protocol is executed for three patient-donor pairs. Note that compilation times and RAM consumption can grow large for large numbers of patient-donor pairs. For further details on the protocol specification we refer to the source code itself or to our paper.

The protocol output is printed to the command line and it indicates the exchange partner for patient and donor of each patient-donor pair. If the pair is not part of an exchange, this is indicated by the value 0 in the output. 
Note that the output can differ for the same inputs due to the random shuffling of the adjacency matrix at the beginning of the protocol execution.

### Input encoding 
There are three example input files in the directory `smpc_protocols/Inputs/`. The rows of each input file contain:
- row 1: donor bloodtype indicator vector
- rows 2-7: donor HLA indicator vectors for A, B, C, DR, DQ, and DP loci
- row 8: patient bloodtype indicator vector
- rows 9-14: patient antibody indicator vectors for HLA-A, -B, -C, -DR, -DQ, and -DP loci
- row 15: pre-score
- rows 16-18: patient HLA indicator vectors for A, B, and DR loci
- rows 19-20: patient and donor blood type: 1 -> O, 2 -> B, 3 -> A, 4 -> AB
- rows 21-22: age of patient and donor
- rows 23-24: region of patient and donor

If the protocol is run for more than three input peers, additional input files are created. These contain random values for the blood types and the prioritization input, and all values of the HLA indicator vectors are set to 0. 
Note that the inputs do not contain real-world data for kidney exchange. Especially, the generated compatibility graphs are much denser than in a real-world setting since using "all zero" HLA indicator vectors reduces the compatibility check to blood type compatibility only.


## Licenses
This repository contains licensed code, here is a comprehensive list of all third party code used:

#### MP-SPDZ
Our protocol is implemented using the secure multi-party computation benchmarking framework MP-SPDZ :

- MP-SPDZ: Copyright (c) 2022, Commonwealth Scientific and Industrial Research Organisation (CSIRO) ABN 41 687 119 230. Licensed under CSIRO Open Source Software Licence Agreement (variation of the BSD / MIT License), see https://github.com/data61/MP-SPDZ/blob/v0.3.3/License.txt for details.

Besides using MP-SPDZ as the underlying framework for our protocol, we adapted the client-server infrastructure that MP-SPDZ (https://github.com/data61/MP-SPDZ) uses for External IO to our use case. 
In particular, the file `smpc_protocols/Programs/Compiler/networking.py` for client communication is adapted from the bankers bonus example for external IO provided by MP-SPDZ (https://github.com/data61/MP-SPDZ/blob/v0.3.3/Programs/Source/bankers_bonus.mpc). 
The code was modified in some places such that it can handle the specific inputs and outputs of our kidney exchange protocol. 
The license for MP-SPDZ can be found in the file itself as well as in the linked repository (https://github.com/data61/MP-SPDZ/blob/v0.3.3/License.txt).