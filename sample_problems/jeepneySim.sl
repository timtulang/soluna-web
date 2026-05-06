\\ Jeepney Passenger Program
\\ Operations:
\\  - Loading
\\  - Unloading
\\  - Show Passengers
\\  - Exit
\\  Max Jeep Capacity: 22 (excluding passenger)
\\  Constraints:
\\      No. of passengers to load <= remaining vacant seat/s
\\      No. of passengers to unload <= total number of current passengers
\\      No passenger can sit on the same location
\\      Jeep driver cannot stop anywhere
\\      Loading : Loading Area
\\      Unloading : Unloading Area
\\  Use an array. 'Show passengers' will show seat location of the passengers

kai backToMainMenu = 1;
hubble blaze passengerSeats = { };
kai passengerLimit = 22;
kai loadAmount = 0;
kai unloadAmount = 0;
kai currentPassengers = 0;

\\ Load function
kai loadPassengers(hubble blaze arr, kai amount, kai current)
    kai newCurrent = current;
    
    phase kai i = 1, (amount + 1), 1 cos
        kai validSeat = 0;

        \\ Count and show vacant seats
        nova("\nCurrently available seats:");
        phase kai j = 1, (passengerLimit+1), 1 cos
            sol arr[j] == 'O'
                lumen(j .. " ");
            mos
        mos
        nova("");

        orbit validSeat == 0 cos
            nova("\nChoose a seat for passenger #" .. i .. " (1-22): ");
            kai seat = lumina();
            
            sol seat < 1 || seat > 22
                nova("Invalid seat! Please choose a seat between 1 and 22.");
            mos soluna arr[seat] == 'X'
                nova("\nSeat #" .. seat .. " is occupied. Please choose another seat.");
            mos luna
                arr[seat] = 'X';
                newCurrent += 1;
                validSeat = 1;
            mos
        mos
    mos
    
    nova("\nSuccessfully LOADED " .. amount .. " passengers!\n");
    zara newCurrent;
mos

\\ Unload function
kai unloadPassengers(hubble blaze arr, kai amount, kai current)
    kai remaining = current;

    phase kai i = 1, (amount + 1), 1 cos
        
        \\ Count and show occupied seats
        nova("\nCurrently occupied seats:");
        phase kai j = 1, (passengerLimit+1), 1 cos
            sol arr[j] == 'X'
                lumen(j .. " ");
            mos
        mos
        nova("");

        kai validSeat = 0;
        
        orbit validSeat == 0 cos
            nova("\n[#" .. i .. "] Choose a seat to unload (1-22): ");
            kai seat = lumina();
            
            sol seat < 1 || seat > 22
                nova("Invalid seat! Please choose a seat between 1 and 22.");
            mos soluna arr[seat] == 'O'
                nova("\nSeat #" .. seat .. " is vacant. Please choose another seat.");
            mos luna
                arr[seat] = 'O';
                remaining -= 1;
                validSeat = 1;
            mos
        mos
    mos
    
    nova("\nSuccessfully UNLOADED " .. amount .. " passengers!\n");
    zara remaining;
mos

\\ Display jeepney seats
void showJeepney(hubble blaze arr)
    kai remainingSeats = passengerLimit-currentPassengers;

    nova("\nShowing Passengers...");
    nova("X = OCCUPIED ("..currentPassengers.."), O = UNOCCUPIED (".. remainingSeats ..")\n");
    nova("\t\t   ___________");
    nova("\t\t  |           |");
    nova("\t\t  |           |");
    nova("\t\t/===============\\");
    nova("\t\t|[MANONG DRIVER]|");
    nova("\t\t|==--   -   --==|");
    nova("\t\t|=-------------=|");

    phase kai row = 1, ((passengerLimit//2)+1), 1 cos
        kai leftSeat = (row*2) - 1;
        kai rightSeat = row*2;

        nova("\t" .. leftSeat .."\t|   " .. arr[leftSeat] .. "       " .. arr[rightSeat] .. "   |\t" .. rightSeat);
    mos
    nova("\t\t|==           ==|");
    nova("\t\t\\_             _/\n");
mos

\\ Initialize passenger seats to be empty (O)
phase kai i = 1, (passengerLimit+1), 1 cos
    passengerSeats[i] = 'O';
mos

orbit backToMainMenu == 1 cos
    kai route = 0;
    
    orbit route < 1 || route > 4 cos
        nova("== JEEPNEY SIMULATOR ==");
        nova("\nYou are in transit. You currently have: "..currentPassengers.." out of "..passengerLimit.." passengers.");
        nova("\t[1] Go to LOADING area");
        nova("\t[2] Go to UNLOADING area");
        nova("\t[3] Show passengers");
        nova("\t[4] Garahe na! (Exit)");
        
        nova("\nPlease choose a route (1-4): ");
        route = lumina();

        sol route < 1 || route > 4
            nova("\nERROR: Please choose a valid route (1-4).\n");
        mos
    mos

    sol route == 1 \\ Passenger loading
        sol currentPassengers == passengerLimit
             nova("\nYour jeep is full. Cannot load more passengers.\n");
        mos luna
            orbit loadAmount <= 0 cos
                nova("\nYou are now in a LOADING area. How many passengers do you want to load?");
                loadAmount = lumina();

                sol loadAmount <= 0
                    nova("\nCannot load a negative or zero amount of passengers.\n");
                mos soluna (loadAmount > (passengerLimit - currentPassengers))
                    nova("\nYour jeep does not have enough capacity for "..loadAmount.." passengers. (Current passenger count: "..currentPassengers.."/"..passengerLimit.." )\n");
                    loadAmount = 0;
                mos
            mos

            currentPassengers = loadPassengers(passengerSeats, loadAmount, currentPassengers);
            loadAmount = 0;
        mos
    mos soluna route == 2 \\ Passenger unloading
        sol currentPassengers == 0
            nova("\nYour jeep is currently empty. No passengers to unload.\n");
        mos luna
            orbit unloadAmount <= 0 cos
                nova("\nYou are now in an UNLOADING area. How many passengers do you want to unload? ");
                unloadAmount = lumina();

                sol unloadAmount <= 0
                    nova("\nCannot unload a negative or zero amount of passengers.\n");
                mos soluna unloadAmount > currentPassengers
                    nova("\nYou cannot unload "..unloadAmount.." passengers. You only have "..currentPassengers.."/"..passengerLimit.." passengers.\n");
                    unloadAmount = 0;
                mos
            mos

            currentPassengers = unloadPassengers(passengerSeats, unloadAmount, currentPassengers);
            unloadAmount = 0;
        mos  
    mos soluna route == 3 \\ Show passengers
        showJeepney(passengerSeats);
    mos soluna route == 4 \\ Exit
        nova("\nGoing back home... (Exiting Program)");
        warp;
    mos
mos