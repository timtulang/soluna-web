nova("=== Problem 1: Sum of Positives ===");
kai sum = 0;
kai num = 1;

orbit num != 0 cos
    nova("Enter an integer (0 to stop):");
    num = lumina();
    
    sol num > 0
        sum += num;
    mos
mos

nova("Sum of positive integers: " .. sum);