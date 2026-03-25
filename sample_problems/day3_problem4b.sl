void bubbleSort(hubble kai arr, kai size, kai order)
    phase kai i = 1, (size + 1), 1 cos
        kai size2 = size - i + 1; 
        phase kai j = 1, size2, 1 cos
            sol (order == 1 && arr[j] > arr[j + 1]) || (order == 2 && arr[j] < arr[j + 1])
                kai temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
            mos
        mos
    mos
    zara;
mos

void printArray(hubble kai arr, kai size)
    \\ Removed size += 1;
    phase kai i = 1, (size + 1), 1 cos
        lumen(arr[i] .. " ");
    mos
    nova("");
    zara;
mos

nova("=== Array Sorting ===");
nova("Input the number of elements:");
kai n = lumina();

hubble kai arr = {};

phase kai i = 1, (n + 1), 1 cos
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