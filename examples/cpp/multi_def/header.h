#ifndef HEADER_H
#define HEADER_H

int add_ints(int a, int b)
{
    return a + b;
}

class AddN
{
public:
    int n_;

    AddN(int n) : n_(n) {}

    ~AddN() {}

    int add(int x)
    {
        return add_ints(n_, x);
    }
};

int f1();

#endif // HEADER_H
