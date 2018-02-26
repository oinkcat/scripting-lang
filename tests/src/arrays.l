# Array functions

array = []

func tryFindElement(elem)
	use array
	
	if Find(array, elem)
		emit "Found element: " & elem
	else
		emit "Element " & elem & " not found!"
	end
end

# Add elements
Add(array, "oink")
Add(array, "piglet")
Add(array, 123)

# Find exising elements
tryFindElement(123)
tryFindElement("piglet")

# Try find non-existing elements
tryFindElement(100)