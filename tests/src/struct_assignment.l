# Assignment to arrays and hashes

# Array
a = [0, 0, 0]
a[0] = 42

emit a

# Hash
h = {}
h.key = [1, 2, 3]

h["key"][1] = "test"

emit h

var = h.key[0] * 2
emit var