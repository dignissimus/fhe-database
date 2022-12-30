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

## Retrieval
For the retrieval operation, $F_{\text{key}}(D)$ should return the value associated with some key in a database. One way to go about approaching this is finding a function on an entry that returns 0 when the entry's key does not match and returns the value when the entry has a matching key. This satisfies $F_{\text{key}}(D) = \sum_{i}^{n} f_{\text{key}}(D_i)$.

Here, we can break down $f$ into two parts. One part for equality-checking and the other for data-fetching. The equality function takes two inputs. It returns one when these inputs are equal and zero otherwise.

The data-fetching part takes two inputs `equal` and `value`. If `equal` is one, then we should return `value`. If equal is zero then we should return zero.

### Equality

The equality function can be written by comparing the bits in each place of two numbers. If we can perform an equality check on 1-bit integers, then we can check equality on integers of any size. For now, let's assume that each number fits into 4 bits and later extend this to 32 bits.

For a 4 bit integer, we can begin by checking the most significant bit. We can clear the other bits by right-shifting the number by 3. After performing this operation on both integers, we can compare these bits. We can subtract these bits from the original numbers to achieve and repeat the process, but this time with a shift of 2, then 1, then 0. After completing this process, we're left with 4 bits which we need to verify are all 1. This is done using a table look-ups on 2-bit integers.

Represent an `AND` gate using a table lookup

| Input | Output |
|-------|--------|
| 00 | 0  |
| 01  | 0  |
| 10  | 0  |
| 11 | 1 |

Using this we now have`AND(x, y) = Table[x << 1 + y]`.

For checking 1-bit equality we can do the same thing.

| Input | Output |
|-------|--------|
| 00 | 1 |
| 01 | 0 |
| 10 | 0 |
| 11 | 1 |

And `EQUAL(x, y) = Table[x << 1 + y]`.

Putting this together, we get 

```python
import concrete.numpy as cnp

AND = cnp.LookupTable([0, 0, 0, 1])
EQUAL = cnp.LookupTable([1, 0, 0, 1])

one_bit_equality(left, right):
    return EQUAL[left << 1 + right]
    
def bit_and(left, right):
    return AND[left << 1 + right]
```

However the and operator can be represented as a function of the sum of the two bits. That is, there is a table such that `AND(X, Y) = Table[x + y]`. Look at the following table

| xy | x + y | AND(X, Y) |
|-------|--------| -- |
| 00 | 00  | 0 |
| 01  | 01  | 0 |
| 10  | 01  | 0 |
| 11 | 10 | 1 |

THe corresponding table satisfies the requirements

| Input | Output |
|-------|--------|
| 00  | 0 |
| 01  | 0 |
| 10  | 1 |
| 11 | \* |

In fact, we can do this for any commutative operator on two bits as the sum uniquely represents the two-bit combination.

Our code now looks like this.

```python
import concrete.numpy as cnp

AND = cnp.LookupTable([0, 0, 1])
EQUAL = cnp.LookupTable([1, 0, 1])

one_bit_equality(left, right):
    return EQUAL[left + right]
    
def bit_and(left, right):
    return AND[left + right]
```

Using the algorithm from earlier, the code for checking 4-bit equality is as follows.

```python
def four_bit_equality(left, right):
    x = 1
    for i in range(1, 5):
        k = 4 - i
        lk = left >> k
        rk = right >> k
        x = AND[one_bit_equality(lk, rk) + x]
        left -= lk << k
        right -= rk << k

    return x
```

To reduce the number of table lookups, we can instead define one table to check that all the bits are 1. This implementation looks like this

```python
ALL_ONE = cnp.LookupTable([0 for _ in range(2**4 - 1)] + [1])

def four_bit_equality(left, right):
    x = 0
    for i in range(1, 5):
        k = 4 - i
        lk = left >> k
        rk = right >> k
        x += one_bit_equality(lk, rk) << k
        left -= lk << k
        right -= rk << k

    return ALL_ONE[x]
```

### Data-fetching
The data fetching component of the function takes two bits. We can take the same approach as earlier and successively operate on each bit of the integer. What we do here, is essentially a bitwise and between a sequence of 1s or a sequences of 0s against the original data. In code, this becomes the following.

```python
def fetch_data(control, data):
    result = 0

    for i in range(1, 5):
        k = 4 - i
        bit = data >> k
        result += AND[control + bit] << k
        data -= bit << k

    return result
```

Getting the data from an entry with an encrypted key and value given an arbitrary query is now simple! The code looks like this
```python
def read_entry(key, value, query):
    equal = four_bit_equality(key, query)
    return fetch_data(equal, value)
```

Using all of these, the code for retrieving an item from the database is as follows

```python
def get(self, query):
    result = 0
    for (entry_key, entry_value) in self.base:
        result += read_entry(entry_key, entry_value, query)
    return result
```

## Replacement
Replacing values can be thought of as applying an update operation to every single entry. Where the entry's value remains the same if the keys is different to the query and becomes the new value if the keys are the same. We can implement this function using the functions defined earlier! This is the same as fetching data from the entry in the case that the key is not equal to the query and fetching data from the updated value if the key is the equal to query. At most one of these is non-zero so we can simply add these values.

```python
def replace(old_key, old_value, new_key, new_value):
    equal = four_bit_equality(old_key, new_key)
    return fetch_data(equal, new_value) + fetch_data(1 - equal, old_value)
```

```python
def update(self, query, value):
    for index, (entry_key, entry_value) in enumerate(self.base):
        new_value = replace(entry_key, query, value)
        self.base[index] = (entry_key, new_value)
```

## Deletion
The deletion function requires a bit of thinking to come up with. Zero-ing out a row with FHE will not allow us to reclaim the space occupied by the item that the client wishes to delete. We can construct an algorithm to perform entry deletion from the database in such a way that allows us to free up space with each operation while still ensuring that the server knows nothing about which item was deleted. The process is as follows.

Take the first entry in the database, remove it from the database and store it in a variable. Now, for each remaining item in the database, replace the entry with the entry selected at the start if the key of this entry matches the key specified in the client's deletion query. If the client wanted to delete the first entry, then the match is never successful and the entry is never re-inserted to the database so it will successfuly be deleted. If the client wants to delete any other entry then it will have been replaced with the first entry after matching the client's query and never again re-inserted into the database so it will have been deleted successfully.

The code implementation for the required FHE circuits looks like this

```python
def delete_circuit(first_key, first_value, key, value, query):
    equal = four_bit_equality(key, query)
    new_key = fetch_data(equal, first_key) + fetch_data(1 - equal, key)
    new_value = fetch_data(equal, first_value) + fetch_data(1 - equal, value)
    return (new_key, new_value)
```

The delete database deletion operation will then be as follows

```python
def delete(self, query):
    first_key, first_value = self.base.pop()
    for index, (first_key, first_value) in enumerate(self.base):
        new_key, new_value = delete_circuit(first_key, first_value, entry_key, entry_value, query)
        self.base[index] = (new_key, new_value)
```

## Extending to 32 bits

# Notes
The `fetch_data` operation, essentially allows us to construct if statements in FHE. We calculate the result from both branches of computation and then use the function to perform selection on the data, simulating substituting in as an if statement. In my original code, this function is called `partial_multipy` as it is equivalent to multiplying data by either one or zero. `fetch_data` can be renamed as `fetch_if` and the `fetch_if(condition, value1) + fetch_if(1 - condition, value2)` idiom can be used to construct a new macro `if_then_else(condition, value1, value2)`. This could also be used to construct if statements at the compiler level and also bounded control flow statements (e.g. a while loop with a maximum number of iterations).
