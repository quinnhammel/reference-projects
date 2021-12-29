import java.lang.Character;
import java.lang.Double;

import javax.lang.model.util.ElementScanner6;

class MorseChar
{
    /*
    A class to store a short or long beep or pause, including how much certainty we have about
    the value (magnitude) of the MorseChar and the length.
    TODO: add length implementation

    Variables:
        mText (private Character)
            the char of the MorseChar itself

            initialized as null
            setting mag to beep or pause without length makes it 'b' or 'p'
            setting length to long or short without mag makes it 'l' or 's' or 'e'
            once length is included, mText is set as follows:
                long beep: '-'
                short beep: '.'
                short pause: ','
                long pause: ';'
                extra long pause: ':'
                TODO: add extra long pause implementation

        magQuartDist (private double):
            distance of magnitude from the quartile of the magnitudes in a given message of many MorseChhar's
            positive if the distance indicates more certainty, negative if increases uncertainty
                example: if beep and mag is 5.0 more than the upper quartile, then magQuartDist is 5.0
                if beep and 5.0 less than upper quartile, then magQuartDist is -5.0
            initialized as null

        magMedDist (private double):
            defined in a similar way to magQuartDist (positive means more certain, negative means less)
            except, measures distance to median (med)
            initialized as null

       magAvgDist (private double):
            defined in a similar way to others (positive means more certain, negative means less)
            except, measures distance to avg magnitude
            initialized as null

        magMeavgDist:
            defined in a similar way to others (positive means more certain, negative means less)
            except, measures distance to meavg
            meavg is (med + avg)/2
            initialized as null

        magCertainty:
            calculated certainty
            magCertainty = magMeavgDist + magAvgDist + magMedDist + (5 * magQuartDist)
            IMPORTANT: weighs quartile information more heavily. This is a magic value.
            initialized as null
    */
    private Character mText;
    private Double magQuartDist;
    private Double magMedDist;
    private Double magAvgDist;
    private Double magMeavgDist;
    private Double magCertainty;

    public MorseChar()
    {
        this.mText = null;
        this.magQuartDist = null;
        this.magMedDist = null;
        this.magAvgDist = null;
        this.magMeavgDist = null;
        this.magCertainty = null;
    }

    //Complex setter (takes in a String varargs)
    public void set(String...args)
    {

    }

    //Simple setters

    //mText setters
    public void setMText(char mText)
    {   
        //only set if it is a valid value
        if 
        (
            (mText == 'b' || mText == 'p' || mText == 'l' || mText == 's' || mText == 'e' )
         ||
            (mText == '.' || mText == '-' || mText == ',' || mText == ';' || mText == ':')
        )
            this.mText = Character.valueOf(mText);
    }

    public void setMText(Character mT)
    {   
        char mText = mT;
        this.setMText(mText);
    }

    //setter for mag, which implicitly sets mText
    public void setMag(String mag)
    {
        mag = mag.toLowerCase();
        if (mag.equals("beep") || mag.equals("b"))
        {
            //mText gets set depending on what it already is.
            //if null, it goes to 'b'.  If 'l' it goes to '-'. If 's' it goes to '.'.
            if (this.mText == null)
                this.mText = Character.valueOf('b');
            else if (this.mText.equals('l'))
                this.mText = Character.valueOf('-');
            else if (this.mText.equals('s'))
                this.mText = Character.valueOf('.');
            else if (this.mText.equals('e')){
                /*specific exception throw*/}
            else{
                /*generic exception throw*/}
        }
        else if (mag.equals("pause") || mag.equals("p"))
        {
            //mText gets set depending on what it already is.
            //if null, it goes to 'p'.  If 'e' it goes to ':'. If 'l' it goes to ';'. If 's' it goes to ','.
            if (this.mText == null)
                this.mText = Character.valueOf('p');
            else if (this.mText.equals('l'))
                this.mText = Character.valueOf(';');
            else if (this.mText.equals('s'))
                this.mText = Character.valueOf(',');
            else if (this.mText.equals('e'))
                this.mText = Character.valueOf(':');
            else{
                /*generic exception throw*/}
        }
        else
        {
            /*generic exception throw*/
        }
    }

    //setter for length, which implicitly sets mText
    public void setLength(String length)
    {
        length = length.toLowerCase();
        if (length.equals("long") || length.equals("l"))
        {
            //mText gets set based on what it already is
            //if null it goes to 'l'. If 'b' it goes to '-'. If 'p' it goes to ';'.
            if (this.mText == null)
                this.mText = Character.valueOf('l');
            else if (this.mText.equals('b'))
                this.mText = Character.valueOf('-');
            else if (this.mText.equals('p'))
                this.mText = Character.valueOf(';');
            else{
                /*generic exception throw*/}
        }
        else if (length.equals("short") || length.equals("s"))
        {
            //mText gets set based on what it already is
            //if null it goes to 's'. If 'b' it goes to '.'. If 'p' it goes to ','.
            if (this.mText == null)
                this.mText = Character.valueOf('s');
            else if (this.mText.equals('b'))
                this.mText = Character.valueOf('.');
            else if (this.mText.equals('p'))
                this.mText = Character.valueOf(',');
            else{
                /*generic exception throw*/}
        }
        else if (length.equals("extralong") || length.equals("el") || length.equals("e"))
        {
            //mText gets set based on what it already is
            //if null it goes to 'e'.  If 'p' it goes to ':'. If 'b' it throws exception (cannot have extra long beep).
            if (this.mText == null)
                this.mText = Character.valueOf('e');
            else if (this.mText.equals('p'))
                this.mText = Character.valueOf(':');
            else if (this.mText.equals('b')){
                /*specific exception throw*/}
            else{
                /*generic exception throw*/}
        }
        else
        {
            /*generic exception throw*/
        }
    }
}
