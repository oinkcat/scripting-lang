# Тест вызовов функциональных переменных

func hello()
	emit "Hello World!"
end

func greet(who)
	emit "Hello " & who & "!"
end

func test()
	return ref hello
end

sub = ref hello
greeters = [ref hello, ref greet, test()]
fn = test()
obj = {
	greet: ref greet
}

hello()
sub()
greeters[0]("ME")
fn()
obj.greet("OINK")