\\\ Helper: Decimal to Binary (Base 2)
let decimalToBinary(kai num)
    let binary = "";
    
    sol num == 0
        zara "0";
    mos
    
    orbit num > 0 cos
        kai remainder = num % 2;
        let remainderstr = "" .. remainder;
        binary = remainderstr .. binary;
        num = num // 2;
    mos
    
    zara binary;
mos

\\\ Helper: Decimal to Octal (Base 8)
let decimalToOctal(kai num)
    let octal = "";
    
    sol num == 0
        zara "0";
    mos
    
    orbit num > 0 cos
        kai remainder = num % 8;
        let remainderstr = "" .. remainder;
        octal = remainderstr .. octal;
        num = num // 8;
    mos
    
    zara octal;
mos

\\\ Helper: Decimal to Hexadecimal (Base 16)
let decimalToHex(kai num)
    let hexChars = "0123456789ABCDEF";
    let hexadecimal = "";
    
    sol num == 0
        zara "0";
    mos
    
    orbit num > 0 cos
        kai remainder = num % 16;
        blaze hexChar = hexChars[remainder + 1];
        let hexStr = "" .. hexChar;
        hexadecimal = hexStr .. hexadecimal;
        num = num // 16;
    mos
    
    zara hexadecimal;
mos

\\\ Main program
nova("=== Decimal to Base Conversion ===");
nova("Enter a positive decimal number:");
kai userInput = lumina();

sol userInput < 0
    nova("Please enter a non-negative integer.");
mos
luna
    let binary = decimalToBinary(userInput);
    let octal = decimalToOctal(userInput);
    let hexadecimal = decimalToHex(userInput);
    
    nova("");
    nova("Results for " .. userInput .. ":");
    nova("Binary:      " .. binary);
    nova("Octal:       " .. octal);
    nova("Hexadecimal: " .. hexadecimal);
mos
