..  Complex Grid Table — Reference Example
    Source: DCACHE ECC Behavior Matrix (session 2026-07-15)
    Demonstrates: multi-column grid table, multi-line cells, footnotes,
    TBD markers, :widths: with space-separated values.

.. table:: DCACHE ECC Behavior Matrix
   :name: dcache-ecc-behavior
   :widths: 22 18 20 20 20
   :width: 100%

   +------------------------+----------------+----------------------+-------------+----------------------------------+
   | Operation              | ECC Result     | Data to Downstream   | SRAM Update | Note                             |
   +========================+================+======================+=============+==================================+
   | Write (full word)      | — [1]_         | —                    | Yes         | Generate ECC, write to SRAM      |
   +------------------------+----------------+----------------------+-------------+----------------------------------+
   | Write (byte/halfword)  | — [1]_         | —                    | Yes         | Read-Modify-Write:               |
   |                        |                |                      |             | read → check ECC → merge →       |
   |                        |                |                      |             | recompute ECC → write            |
   +------------------------+----------------+----------------------+-------------+----------------------------------+
   | Read                   | No error       | Yes                  | —           |                                  |
   +------------------------+----------------+----------------------+-------------+----------------------------------+
   | Read                   | Single-bit     | Yes (corrected)      | Yes         | Correct and write back to SRAM   |
   +------------------------+----------------+----------------------+-------------+----------------------------------+
   | Read                   | Double-bit     | No                   | No          | Report bus error                 |
   +------------------------+----------------+----------------------+-------------+----------------------------------+
   | CCM Read               | Single-bit     | Yes (corrected)      | No          | Forward corrected data           |
   |                        |                |                      |             | downstream; SRAM not updated     |
   +------------------------+----------------+----------------------+-------------+----------------------------------+
   | CCM Read               | Double-bit     | No                   | No          |                                  |
   +------------------------+----------------+----------------------+-------------+----------------------------------+
   | Replace                | Single-bit     | **TBD**              | **TBD**     | Behavior not yet defined         |
   +------------------------+----------------+----------------------+-------------+----------------------------------+
   | Replace                | Double-bit     | No                   | No          |                                  |
   +------------------------+----------------+----------------------+-------------+----------------------------------+

.. [1] Write operations compute ECC directly from incoming data; existing ECC is not checked.
