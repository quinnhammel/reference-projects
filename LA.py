#file with linear algebra objects
#Matrix- sparse matrix, with overloaded methods that correspond to how matrices behave in a math setting
#Vector- a Matrix, which has one row and length cols.

class Matrix(dict):
    #this class inherits from the dict class, which is how it sets and gets its elements.
    
    #tolerance for what value is considered a zero, for float rounding purposes.
    ZERO_TOLERANCE = 1e-5

    def __init__(self, row_count: int, col_count: int):
        #row_count, col_count must be positive ints
        if (not isinstance(row_count, int)) or (not isinstance(col_count, int)):
            raise ValueError('parameters row_count, col_count must be of type int.')
        if (row_count <= 0) or (col_count <= 0):
            raise ValueError('parameters row_count, col_count must be positive.')
        
        self.__row_count = row_count
        self.__col_count = col_count


    @property
    def row_count(self):
        return self.__row_count

    @property 
    def col_count(self):
        return self.__col_count


    #override setitem function
    #this function sets the position by taking the row (r) and column (c) and setting the element
        #at position row * __col_count + col to the value.
    
    #this way, we can convert indices for a two dimensional array to a one dimensional list essentially.
    def __setitem__(self, pos: tuple, val):
        #val must be of type int, float, or complex
        if isinstance(val, int):
            val = float(val)
        elif not(isinstance(val, float) or isinstance(val, complex)):
            raise ValueError('parameter val must be of type int, float, or complex.')

        #pos must be a 2 length tuple
        if (not isinstance(pos, tuple)) or (len(pos) != 2):
            raise ValueError('parameter pos must be a tuple of length 2.')
        
        row_num, col_num = pos
        #row_num, col_num must be ints and within range
        if (not isinstance(row_num, int)) or (not isinstance(col_num, int)):
            raise ValueError('parameters row_num, col_num from pos tuple must be int\'s.')

        if (row_num < 0) or (row_num >= self.row_count):
            raise IndexError(f'parameter row_num from pos out of bounds. min: 0, max: {self.row_count-1}.')
        
        if (col_num < 0) or (col_num >= self.col_count):
            raise IndexError(f'parameter col_num from pos out of bounds. min: 0, max: {self.col_count-1}.')

        #we now check if val is large enough to be considered not zero. If it is, we can add it to the
            #right place in the dictionary (row_num*col_count + col_num)
        if abs(val) >= Matrix.ZERO_TOLERANCE:
            index = (row_num * self.col_count) + col_num
            super().__setitem__(index, val)


    #override getitem function
    def __getitem__(self, pos: tuple):
        #pos must be a 2 length tuple
        if (not isinstance(pos, tuple)) or (len(pos) != 2):
            raise ValueError('parameter pos must be a tuple of length 2.')
        
        row_num, col_num = pos
        #row_num, col_num must be ints and within range
        if (not isinstance(row_num, int)) or (not isinstance(col_num, int)):
            raise ValueError('parameters row_num, col_num from pos must be int\'s.')

        if (row_num < 0) or (row_num >= self.row_count):
            raise IndexError(f'parameter row_num from pos out of bounds. min: 0, max: {self.row_count-1}.')

        if (col_num < 0) or (col_num >= self.col_count):
            raise IndexError(f'parameter col_num from pos out of bounds. min: 0, max: {self.col_count-1}.')
        
        #calculate index
        index = (row_num * self.col_count) + col_num
        if index in self:
            return super().__getitem__(index)

        #not found, so 0 since this is a sparse matrix.
        return 0.0

    #override repr function.
    def __repr__(self):
        #we first set out to find the maximum length of the string representation of elements, for each column.
            #for formatting aesthetics.
        max_lens = []
        for c in range(self.col_count):
            max_l = 0
            for r in range(self.row_count):
                #cast to string to find len.
                x = self[r,c]
                s = str(x)
                l = len(s)
                #if complex, we subtract two since we won't display the ()
                if isinstance(x, complex):
                    l -= 2
                if l > max_l:
                    max_l = l
            max_lens.append(max_l)
        
        #now that we have this max length, we can format the output string.
        output = ''
        for r in range(self.row_count):
            row_string = ''
            for c in range(self.col_count - 1):
                x = self[r,c]
                s = str(x)
                if isinstance(x, complex):
                    #trim off parenthesis
                    s = s[1: len(s) - 1]
                s += ', '
                #s should have max_lens[c]+2 length (+2 is for ', ' that should be added even on longest)
                s += (max_lens[c] + 2 - len(s)) * ' '
                row_string += s
            #for last column we can just add the element without worrying about anything
            x = self[r,self.col_count-1]
            s = str(x)
            if isinstance(x, complex):
                s = s[1:len(s)-1]
            row_string += s + '\n'

            output += row_string

        return output

    #next, overriding operators
    def __add__(self, other):
        #both must be a Matrix, and have same row_num and col_num
        if (not isinstance(other, Matrix)):
            raise ValueError('can only add two SparceMatrix\'s.')

        if (self.row_count != other.row_count) or (self.col_count != other.col_count):
            raise ValueError('can only add two SparseMatrix\'s of equal size.')
        
        #output new SparseMatrix
        output = Matrix(self.row_count, self.col_count)
        
        for r in range(self.row_count):
            for c in range(self.col_count):
                output[r,c] = self[r,c] + other[r,c]
        return output

    def __iadd__(self, other):
        self = self + other
        return self
        
    def __sub__(self, other):
        return self + (other * (-1))
    
    def __isub__(self, other):
        self = self - other
        return self

    def __mul__(self, other):
        #if other is a constant/scalar, we can proceed simply.
        if isinstance(other, int) or isinstance(other, float) or isinstance(other, complex):
            #only need to multiply the elements that are already in self.
            #so, we proceed manually.
            output = Matrix(self.row_count, self.col_count)
            for key,val in self.items():
                #be careful, this key is the one dimensional index, we must extract the row and col.
                row = int(key / self.col_count)
                col = key % self.col_count
                output[row, col] = val*other
            return output

        elif isinstance(other, Matrix):
            #the col count of self must be equal to the row count of other, based on the definition
                #of matrix multiplication.
            if (self.col_count != other.row_count):
                raise Exception('left Matrix must have a col_count equal to right\'s row_count.')
            #output Matrix.
            #only feed in tolerance if both self and other have the same tolerance
            output = Matrix(self.row_count, other.col_count)
            #iterate through each element of output
            for row_output in range(output.row_count):
                for col_output in range(output.col_count):
                    el = 0.0
                    #we now do the matrix multiplcation from how it is done in math.
                    #iterate over cols of self and rows of other.
                    for index in range(self.col_count):
                        el += self[row_output, index] * other[index, col_output]
                    output[row_output, col_output] = el
            
            return output
        else:
            raise ValueError('can only multiply Matrix by int, float, complex, or Matrix.')
    
    def __rmul__(self, other):
        return self * other

    def __imul__(self, other):
        self = self * other
        return self

    def __truediv__(self, other):
        #can only divide by a constant/scalar.
        if not(isinstance(other, int) or isinstance(other, float) or isinstance(other, complex)):
            raise ValueError('can only divide SparseMatrix by int, float, or complex.')
        
        #check if we are dividing by 0.
        if (abs(other) < Matrix.ZERO_TOLERANCE) or (other == 0.0):
            raise Exception('cannot divide by 0.')
       
        return self.__mul__(1/other)

    def __itruediv__(self, other):
        self = self / other
        return self
    
    def __eq__(self, other):
        #check for obvious things indicating not equal, not a Matrix or different row counts.
        if not isinstance(other, Matrix):
            return False
        
        if (self.row_count != other.row_count) or (self.col_count != other.col_count):
            return False
        
        for r in range(self.row_count):
            for c in range(self.col_count):
                if (self[r,c] != other[r,c]):
                    return False
        return True


class Vector(Matrix):
    #a Vector is a Matrix with 1 row and a certain number of cols.
    def __init__(self, length: int):
        if not isinstance(length, int) or (length <= 0):
            raise ValueError("parameter length must be a positive int.")
        self = super(1, length)
    
    #have to re-override setitem and getitem, since the indices are now different.
    def __getitem__(self, pos: int):
        try:
            output = super()[0, pos]
        except ValueError:
            raise ValueError("parameter pos must be an int.")
        except IndexError:
            raise IndexError("parameter pos is out of bounds.")
        #succesfully got output
        return output

    def __setitem__(self, pos:int, val):
        try:
            super()[0, pos] = val
        except ValueError:
            raise ValueError("parameter pos must be an int, val an int, float, or complex.")
        except IndexError:
            raise IndexError("parameter pos is out of bounds.")
        #success, nothing else to do.
    
    #add length property and override __len__ method
    @property
    def length(self):
        return super().col_count
    
    def __len__(self):
        return super().col_count

if __name__ == "__main__":
    m = Matrix(2,2)
    m[0,0] = 2
    print(m[0,0])

