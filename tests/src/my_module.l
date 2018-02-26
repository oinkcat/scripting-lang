# Sample module for import

data = { value: 0 }

func sayHello()
	emit "Hello World!"
end

func initData()
	use data
	data.value = 100
end

func getData()
	use data
	return data.value
end