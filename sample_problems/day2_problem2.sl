\\\ DAY 2, Problem 2: Sum of the square of numbers from 1 to N

nova("=== Sum of Squares ===");
nova("Enter a number N:");
kai n = lumina();

\\\ Error checking: n must be positive
sol n <= 0
    nova("Error: Please enter a positive number!");
mos
luna
    kai sum = 0;
    
    phase kai i = 1, n, 1
        kai square = i * i;
        sum = sum + square;
    mos
    
    nova("Sum of squares from 1 to " .. n .. " is " .. sum);
mos
