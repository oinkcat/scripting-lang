# Bound references in hashes - "objects" test

# "Method"
func hello(self, n)
	for RangeArray(1, n) as i
		emit "Hello ${self.name} from method!"
	end
end

# Construct anonymous object
func NewGreeter(name)
	return new {
		name: name,
		greet: ref hello
	}
end

greeter = NewGreeter("oink")
greeter.greet(4)

emit "Ending"
