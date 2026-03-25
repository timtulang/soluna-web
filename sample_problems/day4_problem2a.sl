nova("=== Program 1: Find the Duplicate ===");
nova("Enter numbers. The program will stop when you enter a duplicate.");

// Initialize a table to store history. We'll start it with a dummy value.
hubble kai history = {0}; 
kai count = 0;
lani hasDuplicate = sage;

orbit hasDuplicate == sage cos
    nova("Enter a number:");
    kai num = lumina();
    
    lani found = sage;
    
    // Check if the number exists in our history
    sol count > 0 cos
        // Remember: Soluna is 1-indexed!
        phase kai i = 1, count + 1, 1 cos
            sol history[i] == num
                found = iris;
            mos
        mos
    mos
    
    // If we found it, trip the boolean to break the while loop
    sol found == iris
        hasDuplicate = iris;
        nova("Duplicate found! Stopping the program.");
    mos
    luna
        // Otherwise, add it to our history and keep going
        count = count + 1;
        history[count] = num;
    mos
mos