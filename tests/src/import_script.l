# Import native module test
import my_module

func test()
	use var
	result = my_module.getData() * var
	emit "KOKOKO #" & result
end

var = 12

my_module.initData()
my_module.sayHello()
test()
