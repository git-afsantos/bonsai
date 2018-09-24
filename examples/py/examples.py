# Binary Operators
1 + 2
1 | 2
1 // 2

# Compare
1 < 4
False is None
1 is not 'aaaa'

# Chained comparisons
1 < 2 < 3
1 < 2 < 3 < 4
1 < 2 < 3 < 4 < 5 + 3

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
xrange(10, x)

# Function call -- keyword args only
xrange(aaa=10)
xrange(aaa=10, bbb=x)

# Function call -- positional and keyword arguments
xrange(10, aaa=x)

# Function call -- starargs
xrange(*args)
xrange(10, *args)
xrange(aaa=10, *args)

# Function call -- kwargs
xrange(**kwargs)
xrange(10, **kwargs)
xrange(aaa=10, **kwargs)

# Function call -- all together
xrange(10, aaa=x, *args, **kwargs)

# Method call
x.m(2)

# List comprehension with only one iterator
[
    x + 1
    for x in xrange(10)
]

# List comprehension with only one iterator and one filter
[
    x + 1
    for x in xrange(10)
    if x % 5
]

# List comprehension with only one iterator and more than one filter
[
    x + 1
    for x in xrange(10)
    if x % 5
    if x % 2
]

# List comprehension with more than one iterator, and filters only in one
[
    x + 1
    for x in xrange(10)
    if x % 5
    if x % 2
    for y in xrange(25)
]

# List comprehension with more than one iterator, all with filters
[
    x + 1
    for x in xrange(10)
    if x % 5
    if x % 2
    for y in xrange(25)
    if y in xrange(2, 3)
]

# Set comprehension
{
    x + 1
    for x in xrange(10)
    if x % 5
    if x % 2
    for y in xrange(25)
    if y in xrange(2, 3)
}

# Generator expression
(
    x + 1
    for x in xrange(10)
    if x % 5
    if x % 2
    for y in xrange(25)
    if y in xrange(2, 3)
)

# Dictionary comprehension
{
    x + 1: x
    for x in xrange(10)
    if x % 5
    if x % 2
    for y in xrange(25)
    if y in xrange(2, 3)
}

# Dictionary
{
    'a': 2,
    5: y,
}

# List
[1, y, 3]

# Set
{y, 5, 6}

# Tuple
(1, 2)

# Nested composite literals
{
    ('a', 4): [9, True, 'else'],
    {y, None}: 'seven',
    'classic': {
        'Is this JSON': False,
    }
}
