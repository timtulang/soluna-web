kai countDigits(kai num)
    sol num == 0
        zara 0;
    mos
    zara 1 + countDigits(num // 10);
mos

nova("=== Count Digits (Recursive) ===");
nova("Input a number:");
kai num = lumina();

kai digitCount = countDigits(num);
nova("The number of digits in the number is: " .. digitCount);