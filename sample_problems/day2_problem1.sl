\\\ DAY 2, Problem 1: Square root of a number (user input)

nova("=== Square Root Calculator ===");
nova("Enter a number:");
kai num = lumina();

\\\ Error checking: negative numbers have no real square root
sol num < 0
    nova("Error: Cannot calculate square root of negative number!");
mos
soluna num == 0
    nova("Square root of 0 is 0");
mos
luna
    \\\ Calculate square root using Newton's method
    kai x = num;
    kai prev_x = 0;
    kai tolerance = 0.0001;
    
    phase kai iteration = 1, 100, 1
        sol x - prev_x <= tolerance
            iteration = 100;
        mos
        prev_x = x;
        x = (x + num / x) / 2;
    mos
    
    nova("Square root of " .. num .. " is " .. x);
mos
