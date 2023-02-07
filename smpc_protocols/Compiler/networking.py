# CSIRO Open Source Software Licence Agreement (variation of the BSD / MIT License)
# Copyright (c) 2022, Commonwealth Scientific and Industrial Research Organisation (CSIRO) ABN 41 687 119 230.
# All rights reserved. CSIRO is willing to grant you a licence to this MP-SPDZ sofware on the following terms, except where otherwise indicated for third party material.
# Redistribution and use of this software in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
# * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
# * Neither the name of CSIRO nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission of CSIRO.
# EXCEPT AS EXPRESSLY STATED IN THIS AGREEMENT AND TO THE FULL EXTENT PERMITTED BY APPLICABLE LAW, THE SOFTWARE IS PROVIDED "AS-IS". CSIRO MAKES NO REPRESENTATIONS, WARRANTIES OR CONDITIONS OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO ANY REPRESENTATIONS, WARRANTIES OR CONDITIONS REGARDING THE CONTENTS OR ACCURACY OF THE SOFTWARE, OR OF TITLE, MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT, THE ABSENCE OF LATENT OR OTHER DEFECTS, OR THE PRESENCE OR ABSENCE OF ERRORS, WHETHER OR NOT DISCOVERABLE.
# TO THE FULL EXTENT PERMITTED BY APPLICABLE LAW, IN NO EVENT SHALL CSIRO BE LIABLE ON ANY LEGAL THEORY (INCLUDING, WITHOUT LIMITATION, IN AN ACTION FOR BREACH OF CONTRACT, NEGLIGENCE OR OTHERWISE) FOR ANY CLAIM, LOSS, DAMAGES OR OTHER LIABILITY HOWSOEVER INCURRED.  WITHOUT LIMITING THE SCOPE OF THE PREVIOUS SENTENCE THE EXCLUSION OF LIABILITY SHALL INCLUDE: LOSS OF PRODUCTION OR OPERATION TIME, LOSS, DAMAGE OR CORRUPTION OF DATA OR RECORDS; OR LOSS OF ANTICIPATED SAVINGS, OPPORTUNITY, REVENUE, PROFIT OR GOODWILL, OR OTHER ECONOMIC LOSS; OR ANY SPECIAL, INCIDENTAL, INDIRECT, CONSEQUENTIAL, PUNITIVE OR EXEMPLARY DAMAGES, ARISING OUT OF OR IN CONNECTION WITH THIS AGREEMENT, ACCESS OF THE SOFTWARE OR ANY OTHER DEALINGS WITH THE SOFTWARE, EVEN IF CSIRO HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH CLAIM, LOSS, DAMAGES OR OTHER LIABILITY.
# APPLICABLE LEGISLATION SUCH AS THE AUSTRALIAN CONSUMER LAW MAY APPLY REPRESENTATIONS, WARRANTIES, OR CONDITIONS, OR IMPOSES OBLIGATIONS OR LIABILITY ON CSIRO THAT CANNOT BE EXCLUDED, RESTRICTED OR MODIFIED TO THE FULL EXTENT SET OUT IN THE EXPRESS TERMS OF THIS CLAUSE ABOVE "CONSUMER GUARANTEES".  TO THE EXTENT THAT SUCH CONSUMER GUARANTEES CONTINUE TO APPLY, THEN TO THE FULL EXTENT PERMITTED BY THE APPLICABLE LEGISLATION, THE LIABILITY OF CSIRO UNDER THE RELEVANT CONSUMER GUARANTEE IS LIMITED (WHERE PERMITTED AT CSIRO'S OPTION) TO ONE OF FOLLOWING REMEDIES OR SUBSTANTIALLY EQUIVALENT REMEDIES:
# (a)               THE REPLACEMENT OF THE SOFTWARE, THE SUPPLY OF EQUIVALENT SOFTWARE, OR SUPPLYING RELEVANT SERVICES AGAIN;
# (b)               THE REPAIR OF THE SOFTWARE;
# (c)               THE PAYMENT OF THE COST OF REPLACING THE SOFTWARE, OF ACQUIRING EQUIVALENT SOFTWARE, HAVING THE RELEVANT SERVICES SUPPLIED AGAIN, OR HAVING THE SOFTWARE REPAIRED.
# IN THIS CLAUSE, CSIRO INCLUDES ANY THIRD PARTY AUTHOR OR OWNER OF ANY PART OF THE SOFTWARE OR MATERIAL DISTRIBUTED WITH IT.  CSIRO MAY ENFORCE ANY RIGHTS ON BEHALF OF THE RELEVANT THIRD PARTY.

"""
Computing peer side of the infrastructure for handling External IO in MP-SPDZ adapted to our use case. See
smpc_protocols/kidney-exchange-client.py for the client (input peer) side.
The original source code can be found in:
https://github.com/data61/MP-SPDZ/blob/v0.3.3/Programs/Source/bankers_bonus.mpc
"""

from Compiler.types import sint, regint, Array, MemValue
from Compiler.library import  accept_client_connection, for_range
from Compiler.instructions import closeclientconnection
from Compiler.library import print_ln, do_while, if_, crash
from Compiler.library import listen_for_clients

PORTNUM = 14000


def accept_client():
    client_socket_id = accept_client_connection(PORTNUM)
    last = regint.read_from_socket(client_socket_id)
    return client_socket_id, last


def close_connections(number_clients):
    @for_range(number_clients)
    def _(i):
        closeclientconnection(i)


def client_input(client_socket_id, length):
    """
    Send share of random value, receive input and deduce share.
    """

    return sint.receive_from_client(length, client_socket_id)


def setup_client_connections(port_num, num_clients):
    # start listening for client socket connections
    listen_for_clients(port_num)
    print_ln('Listening for client connections on base port %s', port_num)

    # clients socket id (integer)
    client_sockets = Array(num_clients, regint)
    # number of clients
    number_clients = MemValue(regint(0))
    # client ids to identity client
    client_ids = Array(num_clients, sint)
    # keep track of received inputs
    seen = Array(num_clients, regint)
    seen.assign_all(0)

    # loop waiting for each client to connect
    @do_while
    def client_connection():
        client_id, last = accept_client()

        @if_(client_id >= num_clients)
        def _():
            print_ln('client id is too high')
            crash()

        client_sockets[client_id] = client_id
        client_ids[client_id] = client_id
        seen[client_id] = 1

        @if_(last == 1)
        def _():
            number_clients.write(client_id + 1)

        return (sum(seen) < number_clients) + (number_clients == 0)

    return number_clients, client_sockets

def write_output_to_clients(sockets, number_clients, output):
    @for_range(number_clients)
    def loop_body(i):
        r = sint.get_random()
        to_send = [output[i], r, output[i] * r]
        sint.write_shares_to_socket(sockets[i], to_send)


def write_output_to_client(socket, recipient, donor):
    rnd_from_triple = sint.get_random_triple()[0]
    auth_result = recipient * rnd_from_triple
    sint.write_shares_to_socket(socket, [recipient, rnd_from_triple, auth_result])

    rnd_from_triple = sint.get_random_triple()[0]
    auth_result = donor * rnd_from_triple
    sint.write_shares_to_socket(socket, [donor, rnd_from_triple, auth_result])
