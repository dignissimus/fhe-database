# FHE Database
This repository contains a Proof of Concept for a key-value store built on Fully Homoomorphic Encryption.
Here, FHE enables the client to query for a single item of data without the server knowing which item was queried or even if anything was returned.

# How I built it
Part of the requirements for this project was that the server must be able to accept queries that are 32-bits in size. I decided to start small and begin with 4-bit queries. When extending the database to 32 bits, I represent 32-bit data as a sequence of 4-bit groups.

# Tricks used
Many operations were unsupported in `concrete-numpy` that would have been useful for building the final database. To work around these, I was able to encode certain operations on two variables into lookup tables on a single input.
