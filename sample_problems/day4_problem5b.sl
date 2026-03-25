nova("=== Problem 5.2: Word Palindrome ===");
nova("Enter a word:");
selene word = lumina();
kai wLen = #word;
kai left = 1;
kai right = wLen;
lani isPal = iris;

orbit left < right cos
    sol word[left] != word[right]
        isPal = sage;
        warp;
    mos
    left += 1;
    right -= 1;
mos

sol isPal == iris
    nova(word .. " is a palindrome.");
mos
luna
    nova(word .. " is not a palindrome.");
mos