"""Sample 2
Author: Erez
"""
N = 16

print "Calculating Fib sequence, %d members" % N
a = 1   # fib(0)
b = 1   # fib(1)
for i in range(N):
    print a, '-',
    a, b = b, a+b

