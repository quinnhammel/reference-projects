This project was from a long time ago, and was an attempt to create a scrabble cracker. 
While it will not really work, it did help me learn a few lessons. First, it helped me become more comfortable
with the Trie data structure, which is important for fast word access in such an application. The other lessons
were more general about programming in Java:
* The storage saving from using bytes instead of ints is NOT worth the cost in having to do byte/int casting. Since most methods require ints, the bytes must almost always be cast.
* Using internal classes, i.e. a class defined entirely within another, can clutter code and make it much more confusing. 
* In general in Java, arrays are less compatible with the other data structures. They are too primitive, and while simpler on their own, are much more confusing when combined with ArrayLists and other such objects. 