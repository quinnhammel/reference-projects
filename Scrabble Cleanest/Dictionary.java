//ADD SEPARATE CASE THING FOR LONGER WORDS
/**
 * Class generates trienode object with all words, will check for hits
 * also generates a brute-force searcher of text files depending on length;
 * needed for the blank tiles to avoid 26x
 *
 * @Quinn Hammel, but some based from online. 
 * @version (a version number or a date)
 */
import java.io.*;
import java.util.Scanner;
import java.util.ArrayList;

public class Dictionary 
{
    //dictionary object is a full trie
    private static TrieNode root;
    public static void fillDictionary () throws Exception{ 
        File fullDict = new File("~/Scrabble Cleanest/BackupDictionary/Dictionary.txt");
        String dictFilePath = "~/Scrabble Cleanest/DictionaryTextFiles/dictionaryChunk";
        
       PrintWriter[] printers = new PrintWriter[13];
       for (byte wordLength = 3; wordLength <=15; wordLength++){
            File dictionaryChunk = new File (dictFilePath + wordLength + ".txt");
            if (! dictionaryChunk.exists()){
               printers[wordLength - 3] = new PrintWriter(dictionaryChunk);
           }
       }

       BufferedReader br = new BufferedReader(new FileReader(fullDict));
       root = new TrieNode();
       String string;
       while ((string = br.readLine()) != null){
           string = string.toLowerCase();
           Dictionary.insert(string);
           byte length = (byte) string.length(); 
           if (length >= 3 && length<= 15 && printers[length - 3] != null){
                printers[length - 3].println(string);
           }
       }      
       //close all writers and readers
       br.close();
       for (PrintWriter printer : printers){
           if (printer != null){
               printer.close();
           }
       } 
        //now must generate files for the blank tile cases, so individual files of words from length 3 to 15
        //can add under three for more complex plays, but would have to clean up a bigger dictionary at that point
        //first check which files not present
        //can put this in earlier so only have to read through once.
        
    
    }
    public static void clearDictionary(){
        TrieNode pCrawl = root;
        for (byte index = 0; index < ALPHABET_SIZE; index++){
            pCrawl.children[index] = null;
        }
    }
        
    static final int ALPHABET_SIZE = 26;
    //node
    static class TrieNode
    {
        TrieNode[] children = new TrieNode[ALPHABET_SIZE];
        //isEndOfWord is true if the node representes end of a word
        boolean isEndOfWord;

        TrieNode() {
            isEndOfWord = false;
            for (int i=0; i<ALPHABET_SIZE; i++){
                children[i] = null;
            }
        }
    };

    //inserts key if not present
    //if key is prefix, marks node
    static void insert (String key){
       // int stop = 0;
        int level;
        int length = key.length();
        int index;

        TrieNode pCrawl = root;
        for (level=0; level<length; level++){
            index = key.charAt(level) - 'a';
            if (pCrawl.children[index]==null){
                pCrawl.children[index] = new TrieNode();
            }
            pCrawl = pCrawl.children[index];
        }
        pCrawl.isEndOfWord = true;
    }

    static boolean search (String key){
        int level;
        int length = key.length();
        int index;
        TrieNode pCrawl = root;

        for (level =0; level<length; level++){
            index = key.charAt(level) - 'a';

            if (pCrawl.children[index] == null){
                return false;
            }
            pCrawl = pCrawl.children[index];
        }
        return (pCrawl != null && pCrawl.isEndOfWord);
    }
}
