
//Name -Quinn Hammel

import java.util.List;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.Random;
class Deck{
    public static final int NUMCARDS = 52;
	public static String[] SUITS = "CLUBS HEARTS DIAMONDS SPADES".split(" ");
    //only issue is with shuffle method; for me it makes more sense to use it as a private helper
    //and only call it when a new deck is made and when the last card is dealt 
    //also for shuffle, instructions are a little confusing, I did it in the way that the college board said to and commented it out
    //deal card method also a little confusing in incrementing top
    
	private ArrayList<Card> cards;
	private int top;
    public Deck(){
        cards = new ArrayList<Card>(NUMCARDS);
        for (byte suit = 0; suit < 4; suit++){
            for (byte face = 1; face <=13; face++){
                cards.add(new Card(Deck.SUITS[suit], face));
            }
        }
        this.top = 51;
        //makes sense to shuffle initially
        this.shuffle();
    }
    public Card dealCard(){
        if (top<0){
            this.shuffle();
        }
         
        top--;
        //must increment then add, because return would skip an increment after
        
        return (this.cards.get(top+1));
    }
    private void shuffle(){
        /*Random rand = new Random();
        for (byte k = 51; k >= 0 ; k--){
            int index = rand.nextInt(k+1);
            Card holder = this.cards.get(index);
            this.cards.set(index, this.cards.get(k));
            this.cards.set(k, holder);
        }*/
        Collections.shuffle(cards);
        this.top = 51;
    }
   
}