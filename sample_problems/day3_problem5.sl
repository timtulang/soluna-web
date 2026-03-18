\\\ DAY 3, Problem 5: Count digits of a number using recursion

flux countDigits(kai num) {
    sol num == 0
        return 0;
    mos
    return 1 + countDigits(num / 10);
}

nova("=== Count Digits (Recursive) ===");
nova("Input a number:");
kai num = lumina();

kai digitCount = countDigits(num);
nova("The number of digits in the number is: " .. digitCount);

return void;
