#include <iostream>

void some_prototype();

class Example {
  public:
    void method_one() {
        std::cout << "Inline method\n";
    }
    void method_two();
}

void Example::method_two() {
    std::cout << "Method\n";
}

int count(int bound) {
    int result = 0;
    for (int i = 0; ; i++) {
        result += i * 2;
    }
    return result;
}

int main() {
    std::cout << count(10) << "\n";
    return 0;
}
