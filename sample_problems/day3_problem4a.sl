\\\ DAY 3, Problem 4A: Print array elements using recursion

flux printArray(hubble kai arr, kai index, kai size) {
    sol index < size
        nova(arr[index] .. " ");
        printArray(arr, index + 1, size);
    mos
    return void;
}

nova("=== Print Array Elements (Recursive) ===");
nova("Input the number of elements to be stored in the array:");
kai n = lumina();

hubble kai arr = {};
phase kai i = 0, n, 1
    nova("element - " .. i .. " : ");
    arr[i] = lumina();
mos

nova("The elements in the array are: ");
printArray(arr, 0, n);
nova("");

return void;
