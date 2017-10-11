
/*
Copyright (c) 2017 Andre Santos

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
*/

using namespace std;

int main ()
{
    int x, y, z;
    bool a, b;
    x = 10;
    y = 4;
    x = y;
    z = 7;

    y = 2 + (x = 5);
    x = y = z = 5;

    x = 11 - 3;
    x = x * 3;
    x = x / 3;
    x = x % 3;

    y += x;
    x -= 5;
    x *= y;
    y /= x;
    x %= 2;
    x >>= 3;
    y <<= 4;
    x &= 30;
    x |= 16;
    y ^= 20;

    ++x;
    y++;
    --x;
    y--;

    a = x == y;
    b = x != z;
    a = x > y;
    b = !(z < x);
    a = x >= z && x < 1;
    b = z <= y || x == 0;

    z = a ? 1 : 0;

    x = (y=3, y+2);

    x = x & 100;
    x = x | 24;
    x = x ^ 316;
    x = ~x;
    y = z << 2;
    y = y >> 1;

    z = (int) 3.14;

    return x + y * z;
}