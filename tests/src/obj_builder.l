# Test Builder pattern

# "Method"
func appendItem(self, item)
	Add(self.list, item)
	return self
end

# Construct anonymous object
func NewListBuilder()
	return new {
		list: [],
		append: ref appendItem
	}
end

# Fluent syntax
builder = NewListBuilder().append("Hello").append("World!")

# Simple syntax
builder.append("Testing!")

for builder.list as item
	emit item
end
