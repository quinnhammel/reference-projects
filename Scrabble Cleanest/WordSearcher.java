import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.lang.Math;
import org.graalvm.compiler.word.Word;

import java.io.*;
import java.util.Collections;
import java.lang.Integer;
import java.util.Arrays;
class WordSearcher
{
    public WordSearcher() throws Exception{
        Dictionary.fillDictionary();
    }
    public ArrayList<String> combosWithBlanks (String query, byte blanks, HashMap<Byte, Character> requirements) throws Exception{
        //need to check if valid requirements.
        //if not, will have a key to a too big index or too small one
        //max length is query.length() + blanks + requirements.size();
        byte minKey = 0, maxKey = 0;
        if (requirements.size() != 0){
            Object[] keys = requirements.keySet().toArray();
            minKey = (byte) keys[0];
            maxKey = (byte) keys[keys.length-1];
        }
        if (minKey < 0 || maxKey >= query.length() + blanks + requirements.size()){
            requirements = new HashMap<Byte, Character>();
        }
        byte requirementsSize = (byte) requirements.size();
        //now check if valid parameters
        if (query.length() + blanks + requirementsSize < 3 || query.length() + blanks + requirementsSize > 15){
            return null;
        }

        ArrayList<Byte> queryHash = WordSearcher.convertToHash(query);
        ArrayList<String> output = new ArrayList<String>();
        BufferedReader br = new BufferedReader(new FileReader ("~/Scrabble Cleanest/DictionaryTextFiles/dictionaryChunk" + (query.length() + blanks + requirementsSize) + ".txt"));
        String string;

        while ((string = br.readLine()) != null){
            byte blanksTemp = blanks;
            //first check if it fits requirements
            Iterator<Map.Entry<Byte, Character>> iterator = requirements.entrySet().iterator();
            while (iterator.hasNext()){
                Map.Entry<Byte, Character> reqPair = (Map.Entry<Byte, Character>) iterator.next();
                if (string.charAt((int) ((Byte) reqPair.getKey())) != (char) reqPair.getValue()){
                    //does not fit requirement
                    blanksTemp = -1;
                } 
            }
            //have to do casting to get byte type for checking hashes
            Object[] queryHashTempObject = queryHash.toArray();
            byte[] queryHashTemp = new byte[queryHashTempObject.length];
            for (byte index = 0; index < queryHashTemp.length; index++){
                queryHashTemp[index] = (Byte) queryHashTempObject[index];
            }
            //must make sure enough blanks
            if (blanksTemp > -1){
                for (byte index = 0; index < string.length(); index++){
                    //only subtract for non requirements
                    if (! requirements.containsKey(new Byte (index))){
                        byte letter = new Integer(string.charAt(index) - 'a').byteValue();
                        queryHashTemp[letter] = (byte) (queryHashTemp[letter] - 1);
                    }
                }
                for (byte letter = 0; letter < 26; letter++){
                    if (queryHashTemp[letter] < 0){
                        blanksTemp += queryHashTemp[letter];
                        if (blanksTemp < 0){
                            break;
                        }
                    }
                }
            }
            if (blanksTemp >= 0){
                output.add(string);
            }
        }
        br.close();
        return output;
    }
    public ArrayList<String> combosNoBlanks(String query, HashMap <Byte, Character> row, byte tilesUsed){
        ArrayList <String> output = new ArrayList<String>();
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

            firstIndex = WordSearcher.toByte(Math.max(WordSearcher.toByte(keys[0]) - tilesUsed, 0));
            lastIndex = WordSearcher.toByte(Math.min(possibleLast, WordSearcher.toByte(keys[keys.length - 1])));
        }
        ArrayList <String> input = Engine.returnInputCombos(query, WordSearcher.toByte(tilesUsed));
        //currently this should check some unnecessary places.
        for (String in: input){
            ArrayList <String> combos = Engine.returnPermutations(in);
            Iterator<String> comboIt = combos.iterator();
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
                        if (row.get(WordSearcher.toByte(tilesIndex + guessStartingIndex + addingIndex)) != null){
                            //requirement is found, add in
                            possibleGuess += row.get(WordSearcher.toByte(tilesIndex + guessStartingIndex + addingIndex));
                            containsAtLeastOneReq = true;
                            addingIndex++;
                        } else{
                            possibleGuess += comboNoReq.charAt(tilesIndex);
                            tilesIndex++;
                        }
                    }
                    //once at this point, if not at very end of board, we must check if there are requirements to the right, and add it if it is
        
                    while (row.get(WordSearcher.toByte(tilesIndex + guessStartingIndex + addingIndex)) != null){
                        possibleGuess += (Character) row.get(WordSearcher.toByte(tilesIndex + guessStartingIndex + addingIndex));
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
    /*public ArrayList<String> combosNoBlanks (String query, HashMap <Byte, Character> requirements, byte size) throws Exception{
        ArrayList <String> output = new ArrayList<String>();
        if (requirements.size() > size){
            return null;
        }
        ArrayList <String> input = Engine.returnInputCombos(query, (byte) (size - requirements.size()) );
        for (String in: input){
            ArrayList <String> combos = Engine.returnPermutations(in);
            //must check if valid requirements
            byte minKey = 0, maxKey = 0;
            if (requirements.size() != 0){
                Object[] keys = requirements.keySet().toArray();
                minKey = (byte) keys[0];
                maxKey = (byte) keys[keys.length-1];
            }
            if (minKey < 0 || maxKey >= in.length() + requirements.size()){
                requirements = new HashMap<Byte, Character>();
            }
            for (String possibleCombo: combos){
                //first add in requirements
                String possibleWithReq = "";
                if (requirements.size() == 0){
                    possibleWithReq = possibleCombo;
                }
                Iterator iterator = requirements.entrySet().iterator();
                byte bottom = 0;
                byte indexOfCombo = 0;
                while (iterator.hasNext()){
                    Map.Entry pair = (Map.Entry) iterator.next();
                    byte top = (byte) pair.getKey();
                    for (byte index = bottom; index < top; index++){
                        possibleWithReq += possibleCombo.charAt(indexOfCombo);
                        indexOfCombo++;
                        //just added, could be bad
                    }
                    possibleWithReq += pair.getValue();
                    bottom = (byte) (top + 1);
                }
                for (byte finisher = (byte) (possibleCombo.length() + requirements.size() - possibleWithReq.length()); finisher > 0; finisher--){
                    possibleWithReq += possibleCombo.charAt(possibleCombo.length()-finisher);
                }
                if (Dictionary.search(possibleWithReq)){
                    output.add(possibleWithReq);
                }
            }
        }
        return output;
    }*/
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
            for (Map.Entry<Character, Integer> e : hash.entrySet()){
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