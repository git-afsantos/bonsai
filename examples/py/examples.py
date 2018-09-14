# Binary Operators
1 + 2
1 | 2
1 // 2

# Compare
1 < 4
False is None
1 is not 'aaaa'

# Bool operators
True and 1

# unary operators
not True

# ternary operator
'booh' if False else 'yeah'

# Variable reference
x + 2

# Function call -- no args
xrange()

# Function call -- positional args only
xrange(10)
xrange(10, 20)

# Function call -- keyword args only
xrange(aaa=10)
xrange(aaa=10, bbb=20)

# Function call -- positional and keyword arguments
xrange(10, aaa=20)

# Function call -- starargs
xrange(*args)
xrange(10, *args)
xrange(aaa=10, *args)

# Function call -- kwargs
xrange(**kwargs)
xrange(10, **kwargs)
xrange(aaa=10, **kwargs)


# Function call -- all together
xrange(10, aaa=20, *args, **kwargs)

# Method call
x.m(2)

[
    x + 1
    for x in xrange(10)
]
[
    x + 1
    for x in xrange(10)
    if x % 5
]
[
    x + 1
    for x in xrange(10)
    if x % 5
    if x % 2
]
[
    x + 1
    for x in xrange(10)
    if x % 5
    if x % 2
    for y in xrange(25)
]
[
    x + 1
    for x in xrange(10)
    if x % 5
    if x % 2
    for y in xrange(25)
    if y in xrange(2, 3)
]
{
    x + 1
    for x in xrange(10)
    if x % 5
    if x % 2
    for y in xrange(25)
    if y in xrange(2, 3)
}
(
    x + 1
    for x in xrange(10)
    if x % 5
    if x % 2
    for y in xrange(25)
    if y in xrange(2, 3)
)
{
    x + 1: x
    for x in xrange(10)
    if x % 5
    if x % 2
    for y in xrange(25)
    if y in xrange(2, 3)
}
