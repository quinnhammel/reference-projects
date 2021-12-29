//(c) A+ Computer Science
//www.apluscompsci.com
//Name - Quinn Hammel
public class Card
{
	public static final String FACES[] = {"ZERO","ACE","TWO","THREE","FOUR",
			"FIVE","SIX","SEVEN","EIGHT","NINE","TEN","JACK","QUEEN","KING"};

	//instance variables
	private String suit;
    private int face;
    private int pointValue;
    //makes sense to add pointValue instance var, that way it only gets calculated when face changes;
    //so point value gets changed in constructor and setFace
    //then add getPointValue method and use in toString

    //constructors
    public Card(){
        this.suit = "";
        this.face = 0;
        this.pointValue = 0;

    }

  	public Card(String s, int f)
  	{
  		this.suit = s;
        this.face = f;
        int pointV = -1;
        if (f == 0){
            pointV = 0;
        }
        if (f == 1){
            pointV = 11;
        }
        if (f >= 2 && f <= 9){
            pointV = f;
        }
        if (pointV == -1){
            pointV = 10;
        }
        this.pointValue = pointV;
  	}

    // modifiers
    //again, changing face changes point value
	public void setFace( int f)
	{
        this.face = f;
        int pointV = -1;
        if (f == 0){
            pointV = 0;
        }
        if (f == 1){
            pointV = 11;
        }
        if (f >= 2 && f <= 9){
            pointV = f;
        }
        if (pointV == -1){
            pointV = 10;
        }
        this.pointValue = pointV;
	}

	public void setSuit( String s)
	{
		this.suit = s;
	}

  	//accessors
	public String getSuit()
	{
		return this.suit;
	}

	public int getFace()
	{
		return this.face;
	}
    public  boolean matches(Card match){
        if (this.getSuit().equals(match.getSuit()) && this.getFace() == match.getFace()){
            return true;
        }
        return false;
    }
    //add get point value
    public int getPointValue(){
        return this.pointValue;
    }
  	//toString
  	public String toString()
  	{
  		return FACES[face] + " of " + this.suit + " (point value of " + this.pointValue + ")";
    }
 }
