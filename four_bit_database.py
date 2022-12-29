import numpy as np
import concrete.numpy as cnp
import time

EQUAL = cnp.LookupTable([1, 0, 1, 1])
ALL_ONE = cnp.LookupTable([0 for _ in range(2**4 - 1)] + [1])
AND2 = cnp.LookupTable([0, 0, 1, 1])


class HomomorphicOperation:
    @staticmethod
    def retrieve(key, value, query):
        equal = HomomorphicOperation.fhe_equal(key, query)
        return HomomorphicOperation.partial_multiply(equal, value)

    @staticmethod
    def update(old_key, old_value, new_key, new_value):
        equal = HomomorphicOperation.fhe_equal(old_key, new_key)
        return HomomorphicOperation.partial_multiply(
            equal, new_value
        ) + HomomorphicOperation.partial_multiply(1 - equal, old_value)

    @staticmethod
    def partial_multiply(left, right):
        result = 0

        for i in range(1, 5):
            k = 4 - i
            rk = right >> k
            result += AND2[left + rk] << k
            right -= rk << k

        return result

    @staticmethod
    def fhe_equal(left, right):
        x = 0
        for i in range(1, 5):
            k = 4 - i
            lk = left >> k
            rk = right >> k
            x += HomomorphicOperation.fhe_equal1b(lk, rk) << k
            left -= lk << k
            right -= rk << k

        return ALL_ONE[x]

    @staticmethod
    def fhe_equal1b(left, right):
        return EQUAL[left + right]


def variables(*names):
    return {name: "encrypted" for name in names}


class HomomorphicCircuitBoard:
    def __init__(self):
        input3 = [
            tuple(l)
            for l in np.int_(np.linspace((0,) * 3, (2**4 - 1,) * 3, 100)).tolist()
        ]
        input4 = [
            tuple(l)
            for l in np.int_(np.linspace((0,) * 4, (2**4 - 1,) * 4, 100)).tolist()
        ]

        self.retrieve = cnp.Compiler(
            HomomorphicOperation.retrieve, variables("key", "value", "query")
        ).compile(input3)

        self.update = cnp.Compiler(
            HomomorphicOperation.update,
            variables("old_key", "old_value", "new_key", "new_value"),
        ).compile(input4)


class HomomorphicDatabase:
    """
    A homomorphic four bit database.

    Since concrete-numpy does not support performing operations
    on circuit ouput, the entries in the database are stored in plain text,
    and encrypt-values before performing operations on them, then
    subsequently decrypt the results. Because of this, I report
    the amount of time spent encrypting and decrypting values.
    When concrete-numpy supports this, it can be changed.
    """

    def __init__(self, *args):
        self.base = []
        self.circuit = HomomorphicCircuitBoard()
        self.update = self.circuit.update
        self.retrieve = self.circuit.retrieve

    def insert(self, key, value):
        self.base.append((key, value))

    def replace(self, key, value):
        s = time.time()
        encryption_time = 0
        for index, entry in enumerate(self.base):
            s1 = time.time()
            encrypted = self.update.encrypt(*entry, key, value)
            e1 = time.time()

            new_value = self.update.run(encrypted)

            s2 = time.time()
            new_value_d = self.update.decrypt(new_value)
            e2 = time.time()

            encryption_time += (e1 - s1) + (e2 - s2)

            old_key = entry[0]
            self.base[index] = (old_key, new_value_d)
        e = time.time()

        print(
            f"replace: Spent {e - s - encryption_time:.2F}s processing data and an extra {encryption_time:.2f}s encrypting and decrypting results"
        )

    def get(self, key):
        """
        The operation is R(x0) + R(x1) + R(x2) + ...
        concrete-numpy does not support performing operations on circuit output
        so at each step of computation, the output from the circuit is decrypted
        """
        result = 0
        encryption_time = 0

        s = time.time()
        for entry in self.base:
            s1 = time.time()
            encrypted = self.retrieve.encrypt(*entry, key)
            e1 = time.time()
            encryption_time += e1 - s1

            r = self.retrieve.run(encrypted)

            s2 = time.time()
            r_d = self.retrieve.decrypt(r)
            e2 = time.time()
            encryption_time += e2 - s2

            result += r_d

        e = time.time()

        print(
            f"get: Spent {e - s - encryption_time:.2f}s processing data and an extra {encryption_time:.2f}s encrypting and decrypting data"
        )

        return result


database = HomomorphicDatabase()
database.insert(1, 1)

print("Retrieving a value from the database")
print("1 =", database.get(1))

print("Replacing a value from the database")
database.replace(1, 13)
print("Retrieving a value from the database")
print("13 =", database.get(1))

database.insert(5, 6)
database.insert(8, 9)
print("Added 2 values to the database")
print("9 =", database.get(8))

database.insert(15, 3)
database.insert(3, 15)

print("15 =", database.get(3))

print("Attempting to access an item that is not in the database")
print("0 =", database.get(14))
