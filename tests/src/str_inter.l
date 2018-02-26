# String interpolation

func test()
	return 42
end

a = 12
b = a * 2

emit "A: ${a}, B: ${b}"
emit "A + B: ${a + b}, A * B: ${a * b}"

Context(12)
emit "TEST: ${test()}"