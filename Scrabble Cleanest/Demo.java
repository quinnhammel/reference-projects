//this now demo
//deal with skipping indices in searcher, see how it affects this
//make board class:
//      constructor: instantiates word searcher, has array of row objects

//      row sub class: HashMap that contains requirements, byte number (1-15 are horis, 16-30 are vert)
//          can get requirements basically
//      search combos of row, will return string with combo, containing index
//      score (combo, row number, index): basically hust scores using key

// or make board class that calls on methods within self, with instance variable of board. That way don't need to keep passing in

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.TreeMap;
import org.graalvm.compiler.word.Word;

import java.lang.Math;
class Demo
{
    public static void main (String[] args) throws Exception{
        
        long time = System.currentTimeMillis();
        WordSearcher search = new WordSearcher();
        System.out.println("Took " + (System.currentTimeMillis() - time) + " to open WordSearcher.");
        HashMap <Byte, Character> requirementsStatic = new HashMap<Byte, Character>();
        
       
        requirementsStatic.put((byte) 1, 'i');
        requirementsStatic.put((byte) 9, 'j');
        requirementsStatic.put((byte) 13, 'a');
        requirementsStatic.put((byte) 14, 'i');
        String tiles = "qveeuib";
        //byte spaceOnLeft = 9, spaceOnRight = 3;
        ArrayList <String> allCombos = new ArrayList<String> ();
        //ArrayList <Byte> allIndices = new ArrayList<Byte> ();
        time = System.currentTimeMillis();
        for (byte i = WordSearcher.toByte(tiles.length()); i > 1; i--){
            ArrayList <String> TempList = search.combosNoBlanks(tiles, requirementsStatic, i);
            for (String validCombo: TempList){
                allCombos.add(validCombo);
            }
        }
        time = System.currentTimeMillis() - time;
        HashMap <Integer, String> wordsWithScore = new HashMap<Integer, String>();
        for (String combo: allCombos){
            int index = Integer.parseInt(combo.substring((combo.lastIndexOf("_") + 1)));
            int score = scorerPretest(combo.substring(0, combo.indexOf("_")), (byte) index);
            wordsWithScore.put(score, combo);
        }
        TreeMap <Integer, String> sorted = new TreeMap <Integer, String>();
        sorted.putAll(wordsWithScore);
        for (Map.Entry<Integer, String> pair: sorted.entrySet()){
            System.out.println("Score of " + pair.getKey() + " with " + pair.getValue());
        }
        System.out.println("Took " + time);
        
        
    }
    private static int scorerPretest(String combo, byte index){
        byte wordMultiplier = 1;
        int outputScore = 0;
        for (byte positionNumber = index; positionNumber < index + combo.length(); positionNumber ++){
            int addTo = 0;
            byte letterMultiplier = 1;
            
                switch (combo.charAt(positionNumber - index)){
                    case 'a':
                        addTo = 1;
                        break;
                    case 'b':
                        addTo = 4;
                        break;
                    case 'c':
                        addTo = 4;
                        break;
                    case 'd':
                        addTo = 2;
                        break;
                    case 'e':
                        addTo = 1;
                        break;
                    case 'f':
                        addTo = 4;
                        break;
                    case 'g':
                        addTo = 3;
                        break;
                    case 'h':
                        addTo = 3;
                        break;
                    case 'i':
                        addTo = 1;
                        break;
                    case 'j':
                        addTo = 10;
                        break;
                    case 'k':
                        addTo = 5;
                        break;
                    case 'l':
                        addTo = 2;
                        break;
                    case 'm':
                        addTo = 4;
                        break;
                    case 'n':
                        addTo = 2;
                        break;
                    case 'o':
                        addTo = 1;
                        break;
                    case 'p':
                        addTo = 4;
                        break;
                    case 'q':
                        addTo = 10;
                        break;
                    case 'r':
                        addTo = 1;
                        break;
                    case 's':
                        addTo = 1;
                        break;
                    case 't':
                        addTo = 1;
                        break;
                    case 'u':
                        addTo = 2;
                        break;
                    case 'v':
                        addTo = 5;
                        break;
                    case 'w':
                        addTo = 4;
                        break;
                    case 'x':
                        addTo = 8;
                        break;
                    case 'y':
                        addTo = 3;
                    case 'z':
                        addTo = 10;
                    default:
                        addTo = 0;
                }
                switch (positionNumber){
                    case 5:
                        letterMultiplier = 3;
                        break;
                    default:
                }
                outputScore += letterMultiplier*addTo;
            
            
        }
        outputScore*=wordMultiplier;
        return outputScore;
    }
}