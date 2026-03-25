nova("=== Problem 5.1: Number Palindrome ===");
nova("Enter a number:");
kai origNum = lumina();
kai tempNum = origNum;
kai revNum = 0;

orbit tempNum > 0 cos
    kai digit = tempNum % 10;
    revNum = (revNum * 10) + digit;
    tempNum = tempNum // 10;
mos

sol origNum == revNum
    nova(origNum .. " is a palindrome.");
mos
luna
    nova(origNum .. " is not a palindrome.");
mos