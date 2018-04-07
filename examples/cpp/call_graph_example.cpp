
/*
Copyright (c) 2018 Andre Santos

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

int f(int x) {
    return (((x << 2) * 5) >> 1);
}

int g(int x) {
    if (x % 3 == 0) {
        return -3 * x;
    }
    return 3 * x;
}

namespace negative {
void h(int x) {}
}

namespace pos_even {
void x(int n) {}
}

namespace pos_odd {
void x(int n) {}

void y(int n) {}
}


int main(int argc, char ** argv) {
    int a = g(f(argc));
    if (a < 0) {
        negative::h(a);
    } else {
        if (a % 2 == 0) {
            pos_even::x(a);
        } else {
            pos_odd::x(a);
            pos_odd::y(a);
        }
    }
    return 0;
}
