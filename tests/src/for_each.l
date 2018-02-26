# Iterative loop test

# 1
emit "Iterate over range"

for RangeArray(1, 10) as i
	emit i
end

# 2
emit "Iterate over hash keys"

hash = {
	a: 10,
	b: 12,
	lol: 100
}

for hash as key
	emit key & ": " & hash[key]
end