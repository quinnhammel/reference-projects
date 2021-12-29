import java.util.ArrayList;
import java.util.Arrays;
import java.util.Iterator;
import java.util.Map;
import java.util.HashMap;
import java.io.*;
public class Board
{
    private HashMap<Byte, Character>[] boardData;
    private Dictionary dict;

    //constructor
    public Board() throws Exception{
        boardData = (HashMap<Byte, Character> []) new HashMap[30];
        Dictionary.fillDictionary();
        BufferedReader br = new BufferedReader(new FileReader(new File("~/Scrabble Cleanest/BoardText/board.txt")));
        for (byte line = 0; line < 15; line++){
            boardData[line] = new HashMap<Byte, Character>();
            String lineString = br.readLine();
            for (byte characterIndex = 0; characterIndex < 15; characterIndex++){
                if (lineString.charAt(characterIndex) != '_'){
                    boardData[line].put(characterIndex, lineString.charAt(characterIndex));
                }
            }
        }
        //row 0-14 are horizontal, 15-29 are vertical
        for (byte vertRow = 15; vertRow <= 29; vertRow++){
            boardData[vertRow] = new HashMap<Byte, Character>();
            for (byte horizRow = 0; horizRow <= 14; horizRow++){
                Character character = (Character) (boardData[horizRow].get((byte) (vertRow - 15)));
                if (character != null){
                    boardData[vertRow].put(horizRow, character);
                }
            }
        }
        br.close();
    }
    //accessor
    public HashMap<Byte, Character> getRow(byte rowNumber){
        if (0<=rowNumber && rowNumber<= 29){
            return boardData[rowNumber];
        }
        return null;
    }
    //helpers / scorers
    public ArrayList<String> returnSemiValidSimpleCombos(String query, HashMap <Byte, Character> row, byte tilesUsed){
        ArrayList <String> output = new ArrayList();
        //now based on tiles, will grab tiles, jumble, then cycle through indices and try to find a fit
        byte firstIndex = 0, lastIndex = 0;
        //start on first, last is last one to check
        if (row.size() != 0){
            Object[] keys = row.keySet().toArray();
            //min is either 0, or first req - tilesUsed; whichever is bigger-- to avoid negatives
            //max is either last req or special; whichever is smaller-- to avoid bigger than 15
            //on last, must iterate back until enough blanks are found

            byte possibleLast = 14, tempCountBlanks = tilesUsed;
            while (tempCountBlanks > 0){
                if (row.get(possibleLast) == null){
                    tempCountBlanks --;
                }
                possibleLast--;
            }
            possibleLast++;

            firstIndex = Board.toByte(Math.max(Board.toByte(keys[0]) - tilesUsed, 0));
            lastIndex = Board.toByte(Math.min(possibleLast, Board.toByte(keys[keys.length - 1])));
        }
        ArrayList <String> input = Engine.returnInputCombos(query, Board.toByte(tilesUsed));
        //currently this should check some unnecessary places.
        for (String in: input){
            ArrayList <String> combos = Engine.returnPermutations(in);
            Iterator comboIt = combos.iterator();
            String comboNoReq;
            while (comboIt.hasNext()){
                comboNoReq = (String) comboIt.next();
                //now must check over all starting indices
                //should do skipping later
                for (byte guessStartingIndex = firstIndex; guessStartingIndex <= lastIndex; guessStartingIndex++){
                    //now construct possible guess by iterating over comboNoReq
                    byte tilesIndex = 0;
                    byte addingIndex = 0;
                    String possibleGuess = "";
                    boolean containsAtLeastOneReq = false;
                    while (tilesIndex < tilesUsed){
                        if (row.get(Board.toByte(tilesIndex + guessStartingIndex + addingIndex)) != null){
                            //requirement is found, add in
                            possibleGuess += row.get(Board.toByte(tilesIndex + guessStartingIndex + addingIndex));
                            containsAtLeastOneReq = true;
                            addingIndex++;
                        } else{
                            possibleGuess += comboNoReq.charAt(tilesIndex);
                            tilesIndex++;
                        }
                    }
                    //once at this point, if not at very end of board, we must check if there are requirements to the right, and add it if it is
        
                    while (row.get(Board.toByte(tilesIndex + guessStartingIndex + addingIndex)) != null){
                        possibleGuess += (Character) row.get(Board.toByte(tilesIndex + guessStartingIndex + addingIndex));
                        addingIndex++;
                        containsAtLeastOneReq = true;
                    }
                    //must check and maybe add to output with index; could change this later but
                    if (Dictionary.search(possibleGuess) && containsAtLeastOneReq){
                        output.add(possibleGuess+"_AT_" + guessStartingIndex);
                    }
                }
            }            
        }
        return output;
    }

    private static ArrayList <Byte> convertToHash(String input){
        input = input.toLowerCase();
        ArrayList <Byte> output = new ArrayList<Byte>();
        for (byte i=0; i<26; i++){
            output.add(i,(byte) 0);
        }
        for (byte charIndex=0; charIndex<input.length(); charIndex++){
            byte position = (byte) (input.charAt(charIndex) - 'a');
            try{
                output.set(position, (byte) (output.get(position) + 1));
            } catch (IndexOutOfBoundsException e){
                //just throw out char
            }
        }
        return output;
    }

    public static byte toByte(Object o){
        try {
            switch (o.getClass().getName()){
                case ("java.lang.Byte"):
                    return ((Byte) o).byteValue();
                case ("java.lang.Integer"):
                    return ((Integer) o).byteValue();
                case ("java.lang.Object"):
                    return ((Byte) o).byteValue();
                default:
                    return (byte) -1;
            }
        } 
        catch (Exception e)
        {
            return (byte) -1;
        }
        
    }

    public byte scoreAndTestNonDom(String possibleFit, byte possibleStartingIndex, byte rowNumber){
        byte score = 0;
        byte addTo = 0;
        if (rowNumber < 14){
            addTo = 15;
        }
        //first go through to check if it's even valid
        HashMap <Byte, Character> row = this.getRow(rowNumber);
        for (byte index = possibleStartingIndex; index < (byte) (possibleStartingIndex + possibleFit.length()); index++){
            //grab word, and find starting index
            String oppositeWord = possibleFit.substring(index - possibleStartingIndex, index - possibleStartingIndex + 1);
            byte oppositeIndex = rowNumber; 
						oppositeIndex--;
            byte limit = 0;

            if (rowNumber > 14){
                limit = 15;
            }
            while (oppositeIndex >= limit && getRow(index).get(oppositeIndex) != null){
                oppositeWord = (Character) getRow((byte) (index+addTo)).get(oppositeIndex) + oppositeWord;
                oppositeIndex--;
            }
            byte oppositeWordStartIndex = oppositeIndex;
            
            oppositeIndex = (byte) (rowNumber + 1);
            limit += 14;
            while (oppositeIndex <= limit && getRow(index).get(oppositeIndex) != null){
                oppositeWord = oppositeWord + (Character) getRow(index).get(oppositeIndex);
                oppositeIndex++;
            }
            if (oppositeWord.length() > 1 && !Dictionary.search(oppositeWord)){
                return 0;
            }
            //add in score of opposite word

        }
        return score;
    }
    private byte scoreSimple(String validCombo, byte x, byte y, boolean horiz){
        byte score = 0;
        int wordMultiplier = 1;

        byte addToX = 0;
        byte addToY = 0;
        byte xIndex = x;
        byte yIndex = y;

        if (horiz == true){
            addToX = 1;
        } else{
            addToY = 1;
        }
        for (byte characterIndex = 0; characterIndex < validCombo.length(); characterIndex++){
            byte letterScore = 0;
            switch (validCombo.charAt(characterIndex)){
                case 'a':
                    letterScore = 1;
                break;
                case 'b':
                    letterScore = 4;
                break;
                case 'c':
                    letterScore = 4;
                break;
                case 'd':
                    letterScore = 2;
                break;
                case 'e':
                    letterScore = 1;
                break;
                case 'f':
                    letterScore = 4;
                break;
                case 'g':
                    letterScore = 3;
                break;
                case 'h':
                    letterScore = 3;
                break;
                case 'i':
                    letterScore = 1;
                break;
                case 'j':
                    letterScore = 10;
                break;
                case 'k':
                    letterScore = 5;
                break;
                case 'l':
                    letterScore = 2;
                break;
                case 'm':
                    letterScore = 4;
                break;
                case 'n':
                    letterScore = 2;
                break;
                case 'o':
                    letterScore = 1;
                break;
                case 'p':
                    letterScore = 4;
                break;
                case 'q':
                    letterScore = 10;
                break;
                case 'r':
                    letterScore = 1;
                break;
                case 's':
                    letterScore = 1;
                break;
                case 't':
                    letterScore = 1;
                break;
                case 'u':
                    letterScore = 2;
                break;
                case 'v':
                    letterScore = 5;
                break;
                case 'w':
                    letterScore = 4;
                break;
                case 'x':
                    letterScore = 8;
                break;
                case 'y':
                    letterScore = 3;
                break;
                case 'z':
                    letterScore = 10;
                default:
                    letterScore = 0;
            }
            switch (Math.min(yIndex, 14-yIndex)){
                case 0:
                    if (xIndex == 3 || xIndex == 11){
                        wordMultiplier = 3;
                    } else{
                        if (xIndex == 6 || xIndex == 8){
                            letterScore *= 3;
                        }
                    }
                break;
                case 1:
                    if (xIndex == 2 || xIndex == 12){
                        letterScore *= 2;
                    } else{
                        if (xIndex == 5 || xIndex == 9){
                            wordMultiplier = Math.max(2, wordMultiplier);
                        }
                    }
                break;
                case 2:
                    if (xIndex == 1  || xIndex == 4 || xIndex == 10 || xIndex == 13){
                        letterScore *= 2;
                    }
                break;
                case 3:
                    if (xIndex == 0 || xIndex == 14){
                        wordMultiplier = 3;
                    } else{
                        if (xIndex == 3 || xIndex == 11){
                            letterScore *= 3;
                        } else{
                            if (xIndex == 7){
                                wordMultiplier = Math.max(wordMultiplier, 2);
                            }
                        }
                    }
                break;
                case 4:
                    if (xIndex == 2 || xIndex == 6 || xIndex == 8 || xIndex == 12){
                        letterScore*=2;
                    }
                break;
                case 5:
                    if (xIndex == 1 || xIndex == 13){
                        wordMultiplier = Math.max(wordMultiplier, 2);
                    } else{
                        if (xIndex == 5 || xIndex == 9){
                            letterScore *= 3;
                        }
                    }
                break;
                case 6:
                    if (xIndex == 0 || xIndex == 14){
                        letterScore *= 3;
                    } else{
                        if (xIndex == 4 || xIndex == 10){
                            letterScore *= 2;
                        }
                    }
                break;
                case 7:
                    if (xIndex == 3 || xIndex == 11){
                        wordMultiplier = Math.max(wordMultiplier, 2);
                    }
                break;
            }
            score += letterScore;
            xIndex += addToX;
            yIndex += addToY;
        }
        return Board.toByte(score*wordMultiplier);
    }
    private static class Engine
    {
        //to help find subwords, must select smaller groups of input using::
        static ArrayList <String> returnInputCombos(String string, byte size){
            ArrayList<String> output = new ArrayList<String>();
            char[] inputArr = new char[string.length()];
            for (byte i = 0; i < inputArr.length; i++){
                inputArr[i] = string.charAt(i);
            }
            Arrays.sort(inputArr);
            char[] temp = new char[size];
            Engine.combinationUtil(inputArr, temp, (byte) 0, (byte) (inputArr.length-1), (byte) 0, size, output);
            return output;
        }
        static ArrayList <String> returnPermutations(String string){
            //copied code
            ArrayList<String> output = new ArrayList<String>();
            char[] temp = string.toCharArray();
            Arrays.sort(temp);
            int total = Engine.calculateTotalPerms(temp, temp.length);
            String perm = "";
            //first perm
            for (byte i = 0; i < temp.length; i++){
                perm += temp[i];
            }
            output.add(perm);
            //to find rest
            for (int permNum = 1; permNum < total; permNum++){
                Engine.nextPermutation(temp);
                perm = "";
                for (byte i = 0; i < temp.length; i++){
                    perm += temp[i];
                }
                output.add(perm);
            }
            return output;
        }
        static void combinationUtil(char arr[], char data[], byte start, byte end, byte index, byte r, ArrayList<String> list){
            //code copied 
            // If Current combination is ready to be printed, print it 
            if (index == r) 
            { 
                String add = "";
                for (int j=0; j<r; j++) 
                    add+=data[j]; 
                list.add(add);
                return; 
            } 

            // replace index with all possible elements. The condition 
            // "end-i+1 >= r-index" makes sure that including one element 
            // at index will make a combination with remaining elements 
            // at remaining positions 
            for (byte i=start; i<=end && end-i+1 >= r-index; i++) 
            { 
                data[index] = arr[i];  
                combinationUtil(arr, data, (byte)(i+1), end, (byte)(index+1), r, list); 
                while (i<arr.length-1 && arr[i] == arr[i+1])
                    i++; 
            } 
        }
        static void nextPermutation(char[] temp){
            //start traversing from the end to find position 'i-1' of the first character
            //which is greater than its successor;
            int i;
            for (i=temp.length-1; i>0; i--){
                if (temp[i] > temp[i-1]){
                    break;
                }
            }
            //finding smallest char after 'i-1' and greater than
            //temp[i-1]
            int min = i;
            int j, x = temp[i-1];
            for (j = i+1; j < temp.length; j++){
                if ((temp[j] < temp[min]) && (temp[j] > x)){
                    min = j;
                }
            }
            //swapping above characters
            char tempToSwap;
            tempToSwap = temp[i-1];
            temp[i-1] = temp[min];
            temp[min] = tempToSwap;
            //sort all from position 'i-1' to end
            Arrays.sort(temp, i, temp.length);
        }
        static int calculateTotalPerms(char[] temp, int n){
            int output = Engine.factorial(n);
            //Hashmap to store freq of all characters
            HashMap <Character, Integer> hash = new HashMap <Character, Integer>();
            for (int i = 0; i<temp.length; i++){
                if (hash.containsKey(temp[i])){
                    hash.put(temp[i], hash.get(temp[i]) + 1);
                } else {
                    hash.put(temp[i], 1);
                }
            }
            //find duplicates
            for (Map.Entry e : hash.entrySet()){
                Integer x = (Integer) e.getValue();
                if (x>1){
                    int div = Engine.factorial(x);
                    output/=div;
                }
            }
            return output;
        }
        static int factorial(int num){
            int output = 1;
            for (int i =2; i<=num; i++){
                output*=i;
            }
            return output;
        }
    }
}