# FHE Database
This repository contains a Proof of Concept for a key-value store built on Fully Homoomorphic Encryption.
Here, FHE enables the client to query for a single item of data without the server knowing which item was queried or even if anything was returned.

# How I built it
Part of the requirements for this project was that the server must be able to accept queries that are 32-bits in size. I decided to start small and begin with 4-bit queries. When extending the database to 32 bits, I represent 32-bit data as a sequence of 4-bit groups.

# Tricks used
Many operations were unsupported in `concrete-numpy` that would have been useful for building the final database. To work around these, I was able to encode certain operations on two variables into lookup tables on a single input.
on
# Tutorial
The idea for creating a fully homomorphic database revolves around representing operations in such a way that they can be represented as some function on transformations of the entries. For the homomorphic database. In this example, I choose the addition operator and created a transformation that returns zero when the entry contains the queried data and returns the queried data otherwise. This way an operation on the database $F(D)$ can be represented as $F(D) = \sum_{i}^{n} f(D_i)$, the task becomes to find the corresponding function, $f$ that produces the desired results.
## Setup
The server will represent the database as a sequence of key-value pairs. In python, we can do this by using a list.
```python
class HomomorphicDatabase:
    def __init__(self, *args):
        self.base = []
```

## Insertion
Insertion is quite easy and can be implemented as appending key-value pairs to the list.
```python
def insert(self, key, value):
    self.base.append((key, value))
```

# Retrieval
For the retrieval operation, $F_{\text{key}}(D)$ should return the value associated with some key in a database. One way to go about approaching this is finding a function on an entry that returns 0 when the entry's key does not match and returns the value when the entry has a matching key. This satisfies $F_{\text{key}}(D) = \sum_{i}^{n} f_{\text{key}}(D_i)$.

Here, we can break down $f$ into two parts. One part for equality-checking and the other for data-fetching. The equality function takes two inputs. It returns one when these inputs are equal and zero otherwise.

The data-fetching part takes two inputs `equal` and `value`. If `equal` is one, then we should return `value`. If equal is zero then we should return zero.

## Equality

The equality function 

## Data-fetching
The data fetching component of the function

# Replacement


# Extending to 32 bits
