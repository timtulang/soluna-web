\\\ DAY 2, Problem 5: Reverse Digits and Sum of Digits

nova("=== Digit Operations ===");
nova("Menu:");
nova("1. Sum of digits");
nova("2. Reverse digits");
nova("Choose operation (1-2):");
kai choice = lumina();

nova("Enter a number:");
kai num = lumina();

sol choice == 1
    \\\ Sum of digits
    kai sum = 0;
    kai temp = num;
    
    phase kai i = 1, 20, 1
        sol temp <= 0
            i = 20;
        mos
        kai digit = temp % 10;
        sum = sum + digit;
        temp = temp / 10;
    mos
    
    nova("Sum of digits of " .. num .. " is " .. sum);
mos
soluna choice == 2
    \\\ Reverse digits
    kai reversed = 0;
    kai temp = num;
    
    phase kai i = 1, 20, 1
        sol temp <= 0
            i = 20;
        mos
        kai digit = temp % 10;
        reversed = reversed * 10 + digit;
        temp = temp / 10;
    mos
    
    nova("Reverse of " .. num .. " is " .. reversed);
mos
luna
    nova("Invalid choice!");
mos
