# Simple example 2

func factorial(n)
    if n > 1
        return factorial(n - 1)
    else
        return 1
    end
end

f = factorial(10)
emit f as Factorial
