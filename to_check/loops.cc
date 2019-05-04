int loop1() {
    int var = 0;
    for (int j = 0; j < 10; j++) {
        var += j;
    }
    return var;
}

int loop2() {
    int var = 0;
    for (int j = 1; j < 5; j++) {
        var += j * 2;
    }
    return var;
}

int loop3() {
    int var = 0;
    int j = 0;
    while (j < 10) {
        var += j;
        var++;
    }
    return var;
}


int loop4() {
    int var = 0;
    int j = 1;
    while (j < 5) {
        var += j;
        var++;
    }
    return var;
}