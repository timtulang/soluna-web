hubble kai arr = {};

void printArray(kai index, kai size)
    sol index <= size
        lumen(arr[index] .. " ");
        printArray(index + 1, size);
    mos
    zara;
mos

nova("=== Print Array Elements (Recursive) ===");
nova("Input the number of elements to be stored in the array:");
kai n = lumina();

orbit n < 1 cos
    nova("Please enter a valid size greater than 0:");
    n = lumina();
mos

kai limit = n + 1;
phase kai i = 1, limit, 1 cos
    lumen("element - " .. i .. " : ");
    arr[i] = lumina();
mos

nova("The elements in the array are: ");
printArray(1, n);
nova("");