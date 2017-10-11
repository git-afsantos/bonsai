
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

#include <iostream>

int main(int argc, char **argv)
{
    int i = 2, a = 0;
    switch (i) {
        case 1: a = 1; std::cout << "1";
        case 2: std::cout << "2";
        case 3: std::cout << "3";
        case 4:
        case 5: std::cout << "45";
                break;
        case 6: std::cout << "6";
    }

    /*std::cout << '\n';

    switch (i) {
        case 4: std::cout << "a";
        default: std::cout << "d";
    }

    std::cout << '\n';

    switch (i) {
        case 4: std::cout << "a";
    }

    // when enumerations are used in a switch statement, many compilers
    // issue warnings if one of the enumerators is not handled
    enum color {RED, GREEN, BLUE};
    switch(RED) {
        case RED:   std::cout << "red\n"; break;
        case GREEN: std::cout << "green\n"; break;
        case BLUE:  std::cout << "blue\n"; break;
    }

    // pathological examples

    // the statement doesn't have to be a compound statement
    switch(0)
        std::cout << "this does nothing\n";

    // labels don't require a compound statement either
    switch(int n = 1)
        case 0:
        case 1: std::cout << n << '\n';

    // Duff's Device: http://en.wikipedia.org/wiki/Duff's_device

    */return 0;
}