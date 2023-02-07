# coding: latin-1
"""

"""

from Compiler.types import sint, regint, Array, MemValue, Matrix, MultiArray
from Compiler.library import print_ln, do_while, for_range, print_str, if_, for_range_parallel
from Compiler.networking import write_output_to_clients, client_input, accept_client
from Compiler.oram import demux_array
from Compiler.util import if_else

BLOOD_TYPES = 4
ANTIGEN_TYPES = 59 + 132 + 48 + 61 + 26 + 22
ANTIGEN_TYPES_A = 59
ANTIGEN_TYPES_B = 132
ANTIGEN_TYPES_C = 48
ANTIGEN_TYPES_DR = 61
ANTIGEN_TYPES_DQ = 26
ANTIGEN_TYPES_DP = 22

SIZE_COMP_INPUT = 2 * BLOOD_TYPES + 2 * ANTIGEN_TYPES

NUM_EQUALITY_CONSTRAINTS = 2
SIZE_EQUALITY_CONSTRAINTS = 10
NUM_DIFFERENCE_CONSTRAINTS = 4
W_ANTIGEN_BOUND = 2
W_AGE_PATIENT_DONOR = 10
W_AGE_DONOR_DONOR = 10
NUM_REGIONS = 12
USE_DISTANCE = 1

REGION_MATRIX = []
for r in range(NUM_REGIONS):
    REGION_MATRIX.append([0] * NUM_REGIONS)

for r1 in range(NUM_REGIONS):
    for r2 in range(NUM_REGIONS):
        if abs(r1-r2) < 4:
            REGION_MATRIX[r1][r2] = 100 - abs(r1 - r2) * 25

def compute_prioritization_weight(prescores, patient_antigens, donor_antigens, patient_bloodtype, donor_bloodtype, patient_age, donor_of_patient_age, donor_age, patient_region, donor_region):
    w_antigens = Array(1, sint)
    w_antigens[0] = sint.dot_product(patient_antigens, donor_antigens) < W_ANTIGEN_BOUND

    w_bloodtypes = Array(1, sint)
    w_bloodtypes[0] = patient_bloodtype[0] == donor_bloodtype[0]

    w_age_patient_donor = Array(1, sint)
    w_age_patient_donor[0] = ((patient_age[0] - donor_age[0]) * (donor_age[0] - patient_age[0])) < W_AGE_PATIENT_DONOR

    w_age_donor_donor = Array(1, sint)
    w_age_donor_donor[0] = ((donor_of_patient_age[0] - donor_age[0]) * (donor_age[0] - donor_of_patient_age[0])) < W_AGE_DONOR_DONOR

    index_bits_row = patient_region[0].bit_decompose(NUM_REGIONS.bit_length())
    selection_row = demux_array(index_bits_row)

    index_bits_col = donor_region[0].bit_decompose(NUM_REGIONS.bit_length())
    selection_col = demux_array(index_bits_col)

    dist_weight = Array(1, sint)
    dist_weight[0] = sint(0)

    @for_range_parallel(NUM_REGIONS, NUM_REGIONS)
    def _(i):
        @for_range_parallel(NUM_REGIONS, NUM_REGIONS)
        def _(j):
            dist_weight[0] = if_else(selection_row[i] * selection_col[j], REGION_MATRIX[i][j], dist_weight[0])

    return prescores[0] + w_antigens[0] + w_bloodtypes[0] + w_age_patient_donor[0] + w_age_donor_donor[0] + dist_weight[0]

def compute_prio_matrix(prescores, patient_antigens, donor_antigens, patient_bloodtype, donor_bloodtype, patient_age, donor_age, patient_region, donor_region, num_clients):
    prio_matrix = sint.Matrix(num_clients, num_clients)
    prio_matrix.assign_all(sint(0))

    @for_range_parallel(num_clients, num_clients)
    def _(i):
        @for_range_parallel(num_clients, num_clients)
        def _(j):
            prio_matrix[i][j] = compute_prioritization_weight(prescores[j], patient_antigens[j], donor_antigens[i], patient_bloodtype[j], donor_bloodtype[i], patient_age[j], donor_age[j], donor_age[i], patient_region[j], donor_region[i])

    return prio_matrix

def compute_compatibility(blood_donor, antigen_donor, blood_patient, antigen_patient):
    sumb = Array(1, sint)
    sumb[0] = sint(0)

    suma = Array(1, sint)
    suma[0] = sint(0)

    sumb[0] = sint.dot_product(blood_patient, blood_donor)

    suma[0] = sint.dot_product(antigen_patient, antigen_donor)

    ohb = sint(0) < sumb[0]
    oha = suma[0] < sint(1)
    return ohb * oha


def compute_comp_matrix(blood_donor, blood_patient, antigen_donor, antigen_patient, num_clients):
    adjacency_matrix = sint.Matrix(num_clients, num_clients)
    adjacency_matrix.assign_all(sint(0))

    @for_range_parallel(num_clients, num_clients)
    def _(client_i):
        @for_range_parallel(num_clients, num_clients)
        def _(client_j):
            adjacency_matrix[client_i][client_j] = compute_compatibility(blood_donor[client_i],
                                                                         antigen_donor[client_i],
                                                                         blood_patient[client_j],
                                                                         antigen_patient[client_j])

    return adjacency_matrix


def read_input(num_clients):
    blood_donor = sint.Matrix(num_clients, BLOOD_TYPES)
    blood_patient = sint.Matrix(num_clients, BLOOD_TYPES)
    antigen_donor = sint.Matrix(num_clients, ANTIGEN_TYPES)
    antibodies_patient = sint.Matrix(num_clients, ANTIGEN_TYPES)

    @for_range(num_clients)
    def _(client_id):
        blood_donor[client_id] = client_input(client_id, BLOOD_TYPES)
        blood_patient[client_id] = client_input(client_id, BLOOD_TYPES)

    @for_range(num_clients)
    def _(client_id):
        tmp = client_input(client_id, ANTIGEN_TYPES_A)
        for i in range(ANTIGEN_TYPES_A):
            antigen_donor[client_id][i] = tmp[i]

    @for_range(num_clients)
    def _(client_id):
        tmp = client_input(client_id, ANTIGEN_TYPES_A)

        for i in range(ANTIGEN_TYPES_A):
            antibodies_patient[client_id][i] = tmp[i]

    @for_range(num_clients)
    def _(client_id):
        tmp = client_input(client_id, ANTIGEN_TYPES_B)

        for i in range(ANTIGEN_TYPES_B):
            antigen_donor[client_id][ANTIGEN_TYPES_A + i] = tmp[i]

    @for_range(num_clients)
    def _(client_id):
        tmp = client_input(client_id, ANTIGEN_TYPES_B)

        for i in range(ANTIGEN_TYPES_B):
            antibodies_patient[client_id][ANTIGEN_TYPES_A + i] = tmp[i]

    @for_range(num_clients)
    def _(client_id):
        tmp = client_input(client_id, ANTIGEN_TYPES_C)

        for i in range(ANTIGEN_TYPES_C):
            antigen_donor[client_id][ANTIGEN_TYPES_A + ANTIGEN_TYPES_B + i] = tmp[i]

    @for_range(num_clients)
    def _(client_id):
        tmp = client_input(client_id, ANTIGEN_TYPES_C)

        for i in range(ANTIGEN_TYPES_C):
            antibodies_patient[client_id][ANTIGEN_TYPES_A + ANTIGEN_TYPES_B + i] = tmp[i]

    @for_range(num_clients)
    def _(client_id):
        tmp = client_input(client_id, ANTIGEN_TYPES_DR)

        for i in range(ANTIGEN_TYPES_DR):
            antigen_donor[client_id][ANTIGEN_TYPES_A + ANTIGEN_TYPES_B + ANTIGEN_TYPES_C + i] = \
                tmp[
                    i]

    @for_range(num_clients)
    def _(client_id):
        tmp = client_input(client_id, ANTIGEN_TYPES_DR)

        for i in range(ANTIGEN_TYPES_DR):
            antibodies_patient[client_id][ANTIGEN_TYPES_A + ANTIGEN_TYPES_B + ANTIGEN_TYPES_C + i] = \
                tmp[i]

    @for_range(num_clients)
    def _(client_id):
        tmp = client_input(client_id, ANTIGEN_TYPES_DQ)

        for i in range(ANTIGEN_TYPES_DQ):
            antigen_donor[client_id][
                ANTIGEN_TYPES_A + ANTIGEN_TYPES_B + ANTIGEN_TYPES_C + ANTIGEN_TYPES_DR + i] = \
                tmp[
                    i]

    @for_range(num_clients)
    def _(client_id):
        tmp = client_input(client_id, ANTIGEN_TYPES_DQ)

        for i in range(ANTIGEN_TYPES_DQ):
            antibodies_patient[client_id][
                ANTIGEN_TYPES_A + ANTIGEN_TYPES_B + ANTIGEN_TYPES_C + ANTIGEN_TYPES_DR + i] = \
                tmp[i]

    @for_range(num_clients)
    def _(client_id):
        tmp = client_input(client_id, ANTIGEN_TYPES_DP)

        for i in range(ANTIGEN_TYPES_DP):
            antigen_donor[client_id][
                ANTIGEN_TYPES_A + ANTIGEN_TYPES_B + ANTIGEN_TYPES_C + ANTIGEN_TYPES_DR + ANTIGEN_TYPES_DQ + i] = \
                tmp[i]

    @for_range(num_clients)
    def _(client_id):
        tmp = client_input(client_id, ANTIGEN_TYPES_DP)

        for i in range(ANTIGEN_TYPES_DP):
            antibodies_patient[client_id][
                ANTIGEN_TYPES_A + ANTIGEN_TYPES_B + ANTIGEN_TYPES_C + ANTIGEN_TYPES_DR + ANTIGEN_TYPES_DQ + i] = \
                tmp[i]


    return blood_donor, blood_patient, antigen_donor, antibodies_patient


def read_prio_input(num_clients):
    prescores = Matrix(num_clients, 1, sint)
    patient_antigens = Matrix(num_clients, ANTIGEN_TYPES_A + ANTIGEN_TYPES_B + ANTIGEN_TYPES_DR, sint)
    donor_antigens = Matrix(num_clients, ANTIGEN_TYPES_A + ANTIGEN_TYPES_B + ANTIGEN_TYPES_DR, sint)
    patient_bloodtype = Matrix(num_clients, 1, sint)
    donor_bloodtype = Matrix(num_clients, 1, sint)
    patient_age = Matrix(num_clients, 1, sint)
    donor_age = Matrix(num_clients, 1, sint)
    patient_region = Matrix(num_clients, 1, sint)
    donor_region = Matrix(num_clients, 1, sint)

    @for_range(num_clients)
    def _(client_id):
        prescores[client_id] = client_input(client_id, 1)

    @for_range(num_clients)
    def _(client_id):
        tmp = client_input(client_id, ANTIGEN_TYPES_A)
        for i in range(ANTIGEN_TYPES_A):
            patient_antigens[client_id][i] = tmp[i]

    @for_range(num_clients)
    def _(client_id):
        tmp = client_input(client_id, ANTIGEN_TYPES_B)

        for i in range(ANTIGEN_TYPES_B):
            patient_antigens[client_id][ANTIGEN_TYPES_A + i] = tmp[i]

    @for_range(num_clients)
    def _(client_id):
        tmp = client_input(client_id, ANTIGEN_TYPES_DR)

        for i in range(ANTIGEN_TYPES_DR):
            patient_antigens[client_id][ANTIGEN_TYPES_A + ANTIGEN_TYPES_B + i] = tmp[i]

    @for_range(num_clients)
    def _(client_id):
        tmp = client_input(client_id, ANTIGEN_TYPES_A)
        for i in range(ANTIGEN_TYPES_A):
            donor_antigens[client_id][i] = tmp[i]

    @for_range(num_clients)
    def _(client_id):
        tmp = client_input(client_id, ANTIGEN_TYPES_B)

        for i in range(ANTIGEN_TYPES_B):
            donor_antigens[client_id][ANTIGEN_TYPES_A + i] = tmp[i]

    @for_range(num_clients)
    def _(client_id):
        tmp = client_input(client_id, ANTIGEN_TYPES_DR)

        for i in range(ANTIGEN_TYPES_DR):
            donor_antigens[client_id][ANTIGEN_TYPES_A + ANTIGEN_TYPES_B + i] = tmp[i]

    @for_range(num_clients)
    def _(client_id):
        patient_bloodtype[client_id] = client_input(client_id, 1)
        donor_bloodtype[client_id] = client_input(client_id, 1)
        patient_age[client_id] = client_input(client_id, 1)
        donor_age[client_id] = client_input(client_id, 1)
        patient_region[client_id] = client_input(client_id, 1)
        donor_region[client_id] = client_input(client_id, 1)

    return prescores, patient_antigens, donor_antigens, patient_bloodtype, donor_bloodtype, patient_age, donor_age, patient_region, donor_region