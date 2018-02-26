# Test else if

func test_elseif(var)
	emit "var = " & var
	emit "If without Else"

	if var > 5
		emit "True branch 1 (var > 5)"
	end

	emit "If and Else"

	if var < 5
		emit "True branch (var < 5)"
	else
		emit "False branch (var >= 5)"
	end

	emit "If and ElseIf"

	if var > 10
		emit "Condition 1 branch (var > 10)"
	elsif var > 5
		emit "Condition 2 branch (var > 5)"
	end

	emit "If, ElseIf and Else"

	if var > 10
		emit "Condition 1 branch (var > 10)"
	elsif var > 5
		emit "Condition 2 branch (var > 5)"
	else
		emit "Else branch (var <= 5)"
	end

	emit "=== end test ==="
end

emit "ElseIf statement test"
test_elseif(1)
test_elseif(10)
test_elseif(20)