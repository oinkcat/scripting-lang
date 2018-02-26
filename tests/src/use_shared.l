# Using shared variable

use Name

func greet(name)
	emit "Hello " & name & "!"
end

greet(Name)

emit {name: Name} as Result