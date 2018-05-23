#include <stdexcept>

extern void f();

int main(int argc, char **argv) {
    try { f(); }
    catch (const std::exception& e) { /* */ }
    catch (const std::exception&) { /* */ }
    catch (...) { /* */ }
    return 0;
}
