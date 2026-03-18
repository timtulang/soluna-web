\\\ DAY 3, Problem 4B: Sort array in ascending or descending order

flux bubbleSort(hubble kai arr, kai size, kai order) {
    \\\ order: 1 for ascending, 2 for descending
    phase kai i = 0, size, 1
        phase kai j = 0, size - i - 1, 1
            sol (order == 1 && arr[j] > arr[j + 1]) || (order == 2 && arr[j] < arr[j + 1])
                kai temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            mos
        mos
    mos
    return void;
}

flux printArray(hubble kai arr, kai size) {
    phase kai i = 0, size, 1
        lumen(arr[i] .. " ");
    mos
    nova("");
    return void;
}

nova("=== Array Sorting ===");
nova("Input the number of elements:");
kai n = lumina();

hubble kai arr = {};
phase kai i = 0, n, 1
    nova("element - " .. i .. " : ");
    arr[i] = lumina();
mos

nova("Menu:");
nova("1. Ascending");
nova("2. Descending");
nova("Choose sort order (1-2):");
kai choice = lumina();

bubbleSort(arr, n, choice);

nova("Sorted array: ");
printArray(arr, n);

return void;
