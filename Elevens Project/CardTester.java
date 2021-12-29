class CardTester{
    public static void main (String[] args){
        Deck deck = new Deck();
        for (int i = 0; i < 52; i++){
            System.out.println(deck.dealCard());
        }
        for (int i = 0; i < 52; i++){
            System.out.println(deck.dealCard());
        }
        Card one = deck.dealCard();
        Card two = deck.dealCard();
        System.out.println(one.matches(one));
        System.out.println(one.matches(two));
    }
}