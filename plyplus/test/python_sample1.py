def fib(n):
    if n <= 1: return 1
    return fib(n-1) + fib(n-2)

for i in range(11):
    print fib(i),
