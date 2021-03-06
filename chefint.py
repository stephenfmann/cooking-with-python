"""
    chefint.py
    Interpret programs written in the esolang Chef.
    See https://www.dangermouse.net/esoteric/chef.html for details.
"""

import sys, re, random, copy

class Chef:
    """
        Parse a recipe.
        Calls instances of itself to parse sub-recipes.
    """
    
    def __init__(self, script, mixingbowls = {0: []}):
        self.script         = script
        self.origscript     = script
        self.mixingbowls    = copy.deepcopy(mixingbowls)
        self.bakingdishes   = {}
    
    def syntax_error(self,message):
        """
            A syntax error was found in the Chef script.
        """
        
        ## TODO: report line number.
        print(f"Syntax error: {message}")
        sys.exit(-1)
        
    def cooking_error(self,message):
        """
            A runtime error
        """
        
        ## TODO - report line number
        print(f"Cooking time error: {message}")
        sys.exit()
    
    def parse(self):
        """
            Parse and execute the recipe in self.script.
        """
        
        ## 1. Find recipe name
        self.recipename = re.match("(.*?)\.\n\n", self.script)
        self.script = re.sub(self.recipename.group(), "", self.script)
        if(self.recipename == None):
            print("Invalid recipe name")
            sys.exit(-1)
        
        ## 2. Match a recipe name, first line of script, must end with a dot and two newlines.
        ## Replace this with nothing to allow for further matching.
        self.comment = re.match("(.*?)\n\n", self.script, re.DOTALL)
        
        ## 3. Find a comment, and replace it. 
        if self.comment != None\
        and re.match("^Ingredients", self.comment.group()) == None: # Make sure we do not replace the ingredient list.
            self.script = re.sub(re.escape(self.comment.group()), "", self.script) # Replace the comment with nothing.
        
        ## 4. Find ingredient list.
        self.ingr = re.match("Ingredients\.\n", self.script)
        
        if self.ingr == None:
            print("Ingredient list not found")
            sys.exit(-1)
            
        ## Again, replace with nothing.
        self.script = re.sub(self.ingr.group(), "", self.script, 1)
        
        ## 5. Match ingredients.
        self.ingredients = re.findall("(([0-9]*) ?(k?g|pinch(?:es)?|m?l|dash(?:es)?|cups?|teaspoons?|tablespoons?)? ?([a-zA-Z0-9 ]+)\n)", self.script)
        
        self.ingredientlist = {}
        
        for i in self.ingredients:
            if re.match(i[0], self.script) != None:
                ## Replace them with nothing, but only if they are exactly at the beginning of the script
                ##   to avoid replacing axuiliary ingredients.
                self.script = self.script.replace(i[0], "")
                
            ## Type assignment is next. Note that chr() is not run on values until output.
            ##   This is to allow arithmetic operations on liquids.
            if(i[2] in("dash", "cup", "l", "ml", "dashes", "cups")):
                value = int(i[1])
                type = "liquid"
            else:
                try:
                    value = int(i[1])
                except ValueError:
                    value = None
                type = "dry"
            self.ingredientlist[i[3]] = [value, type, i[3]]
            
        ## 6. Find the method. This is where things get interesting.
        self.script = self.script.lstrip()
        
        self.meth = re.match("(.+[\r\n]+)*?Method.\n", self.script)
        
        ## Match anything up to two newlines.
        self.script = re.sub(self.meth.group(), "", self.script, 1)
        self.method = re.match("(.*?)\n\n", self.script, re.DOTALL)
        
        ## 7. Run the script & Cook the food.
        self.execute(self.method.group(1))
        
        ## 8. Find output directive.
        serves = re.search("Serves ([0-9]+).", self.script)
        if serves != None:
            output = self.serve(int(serves.group(1))) # Call function to return output
            return output
        
    def ambigcheck(self, text, dish=False):
        """
            A mixing bowl may not be used without a number if other mixing bowls use numbers. 
            Same goes for baking dishes.
        """
        
        if re.match("the (1st|2nd|3rd|[0-9]+th) mixing bowl", text) != None:
            self.syntax_error("Ambigious mixing bowl")
        
        if dish==True:
            if re.match("the (1st|2nd|3rd|[0-9]+th) baking dish", text) != None:
                self.syntax_error("Ambigious baking dish")
                
    def valuecheck(self, ingredient):
        """
            Ingredients may be defined without a value, but not used without one.
        """
        
        if self.ingredientlist[ingredient][0] == None:
            self.cooking_error("Cooking time error: tried to access ingredient "+\
                               ingredient + ", which is not ready for use.")
            
    def put(self, mixingbowl, value):
        """
            Add an ingredient to a mixing bowl.
        """
        
        if mixingbowl == None:
            if len(self.mixingbowls) > 0:
                self.mixingbowls[0].append(value)
                return
            self.mixingbowls[0] = []                        
            self.mixingbowls[0].append(value)
            return
        
        ## Mixing bowl exists 
        ## Numbered mixing bowls use their number -1 as index.
        key = int(mixingbowl)-1            
        if not key in self.mixingbowls:
            self.mixingbowls[key] = []     
            
        self.mixingbowls[key].append(value)
            
        
    def fold(self, ingredient, mixingbowl):
        """
            Opposite of put.
        """
        
        key = 0
        if mixingbowl:
            key = int(mixingbowl[:-2])-1
        
        ## TODO - fix this (ingredient name and dry/liquid should not be overwritten)
        self.ingredientlist[ingredient] = self.mixingbowls[key].pop()
        
    def addingredient(self, ingredient, mixingbowl):
        """
            Add the value of <ingredient> to the value of the ingredient 
             on top of the mixing bowl and store the result in the mixing bowl.
        """
        
        value = self.ingredientlist[ingredient][0]
        
        key = 0
        if mixingbowl:
            key = int(mixingbowl[:-2])-1
            
        if value == None:
            value = 0
        
        self.mixingbowls[key][-1][0] += value
        
    def removeingredient(self, ingredient, mixingbowl):
        """
            Subtract the value of <ingredient> from the value of the ingredient 
             on top of the mixing bowl and store the result in the mixing bowl.
        """
        
        value = self.ingredientlist[ingredient][0]
        
        key = 0
        if mixingbowl:
            key = mixingbowl[:-2]
            
        if value == None:
            value = 0
        
        self.mixingbowls[key][-1][0] -= value
        
    def combineingredient(self, ingredient, mixingbowl):
        """
            Multiply the value of <ingredient> by the value of the ingredient 
             on top of the mixing bowl and store the result in the mixing bowl.
        """
        
        value = self.ingredientlist[ingredient][0]
        
        key = 0
        if mixingbowl:
            key = mixingbowl[:-2]
            
        if value == None:
            value = 0
        
        self.mixingbowls[key][-1][0] *= value
        
    def divideingredient(self, ingredient, mixingbowl):
        """
            Divide the value of the ingredient on top of the mixing bowl 
            by the value of <ingredient> and store the result in the mixing bowl.
        """
        
        value = self.ingredientlist[ingredient][0]
        
        key = 0
        if mixingbowl:
            key = mixingbowl[:-2]
        
        if value == None:
            value = 1
        
        self.mixingbowls[key][-1][0] = float(self.mixingbowls[key][-1][0]/value)
        
    def stir(self,mixingbowl,minutes,ingredient):
        """
            This rolls the top <minutes> ingredients in the mixing bowl, 
             such that the top ingredient goes down that number of ingredients 
             and all ingredients above it rise one place. 
            If there are not that many ingredients in the bowl, 
             the top ingredient goes to the bottom of the bowl 
             and all the others rise one place.
        """
        
        value = int(minutes)
        if ingredient:
            value = int(self.ingredientlist[ingredient][0])
        
        key = 0
        if mixingbowl:
            key = mixingbowl[:-2]
        
        if self.mixingbowls[key]:
            ## TODO -- check this is removing the correct item (the "top" one).
            ing = self.mixingbowls[key].pop()    # Removes LAST item - push and pop are reversed in Python.
            self.mixingbowls[key].reverse()
            self.mixingbowls[key].insert(value,ing)
            self.mixingbowls[key].reverse()
            
    def execute(self, text, loop=False):
        """
            Main interpreting function.
            Step through each line and run the appropriate function.
        """
        
        ## 1. Split lines
        excode = re.split("\.\s+", text)
        
        def stripwhite(x):
            return x.lstrip()
        excode = list(map(stripwhite, excode))
        excode[-1] = excode[-1][:-1] 
        
        ## 2. Step through lines.
        ## Do a series of regexps, call appropriate function.
        for ex in excode:
            
            ## A. Put
            put = re.search("^Put (?:the )?([a-zA-Z ]+) into (?:the )?(?:([1-9]\d*)(?:st|nd|rd|th) )?mixing bowl", ex)
            if put != None:
                if put.group(2) == None:                    
                    self.ambigcheck(text)
                self.put(put.group(2), copy.copy(self.ingredientlist[put.group(1)]))
            
            ## B. Fold
            fold = re.search("Fold ([a-zA-Z ]+) into (?:the )?(1st|2nd|3rd|[0-9]+th)? ?mixing bowl", ex)
            if fold != None:
                if fold.group(2) == None:
                    self.ambigcheck(text)                
                self.fold(fold.group(1), fold.group(2))
            
            ## C. Add
            add = re.search("Add ([a-zA-Z0-9 ]+?) to (?:the )?(?:(1st|2nd|3rd|[0-9]+th) )?mixing bowl", ex)
            if add != None:
                if add.group(2) == None:
                    self.ambigcheck(text)
                self.addingredient(add.group(1), add.group(2))
            
            ## D. Remove
            remove = re.search("Remove ([a-zA-Z0-9 ]+?) from (?:the )?(?:(1st|2nd|3rd|[0-9]+th) )?mixing bowl", ex)
            if remove != None:
                if remove.group(2) == None:
                    self.ambigcheck(text)
                self.removeingredient(remove.group(1), remove.group(2))
                
            ## E. Combine
            combine = re.search("Combine ([a-zA-Z0-9 ]+?) into (?:the )?(?:(1st|2nd|3rd|[0-9]+th) )?mixing bowl", ex)
            if combine != None:
                if combine.group(2) == None:
                    self.ambigcheck(text)
                self.combineingredient(combine.group(1), combine.group(2))
            
            ## F. Divide
            divide = re.search("Divide ([a-zA-Z0-9 ]+?) into (?:the )?(?:(1st|2nd|3rd|[0-9]+th) )?mixing bowl", ex)
            if divide != None:
                if divide.group(2) == None:
                    self.ambigcheck(text)
                self.divideingredient(divide.group(1), divide.group(2))
            
            ## G. Liquefy mixing bowl
            liquefy = re.search("Liquefy contents of the (1st|2nd|3rd|[0-9]+th)? ?mixing bowl", ex)
            if liquefy != None:                
                if liquefy.group(1) == None:                    
                    self.ambigcheck(text)                
                    for i in self.mixingbowls[0]:                    
                        if(i[1] == "dry"):
                            i[1] = "liquid"                            
                continue
            
            ## H. Liquefy ingredient
            liquefy2 = re.search("Liquefy [a-zA-Z]", ex)
            if liquefy2 != None: #
                self.ingredientlist[liquefy2.group(1)] 
                continue
            
            ## I. Clean mixing bowl
            clean = re.search("Clean the (1st|2nd|3rd|[0-9]+th)? ?mixing bowl", ex)
            if clean != None:
                if clean.group(1) == None:
                        self.mixingbowls[0] = []
                else:
                    if clean.group(1)[:-2] in self.mixingbowls:
                        self.mixingbowls[clean.group(1)[:-2]] = []
                    else:
                        existslater = re.match(clean.group(1) + " mixing bowl", text)
                        if existslater == None:
                            print("Warning: Unknown mixing bowl"+str(clean.group(1)))
                        else:
                            print("Warning: Tried to clean mixing bowl"+str(clean.group(1))+"before putting anything in it!")
                continue
            
            ## J. Mix mixing bowl
            mix = re.search("Mix the (1st|2nd|3rd|[0-9]+th)? ?mixing bowl well", ex)
            if mix != None:
                if mix.group(1) == None:
                        random.shuffle(self.mixingbowls[0])
                else:
                    if mix.group(1)[:-2] in self.mixingbowls:
                        random.shuffle(self.mixingbowls[clean.mix(1)[:-2]])
                    else:
                        existslater = re.match(clean.mix(1) + " mixing bowl", text)
                        if existslater == None:
                            print("Warning: Unknown mixing bowl"+mix.group(1))
                        else:
                            print("Warning: Tried to mix mixing bowl"+str(mix.group(1))+"before putting anything in it!")
                continue
            
            ## K. Take from fridge
            fridge = re.search("Take ([a-zA-Z ]+) from refrigerator", ex)
            if fridge != None:
                if fridge.group(1) in self.ingredientlist:
                    value = int(input(fridge.group(1) + ": ")) # sfm renamed raw_input to input 2->3
                    if self.ingredientlist[fridge.group(1)][1] == "liquid":
                        self.ingredientlist[fridge.group(1)][0] = chr(value)
                    else:
                        self.ingredientlist[fridge.group(1)][0] = value
                continue
            
            ## L. Pour
            pour = re.search("Pour contents of the (?:the )?(?:([1-9]\d*)(?:st|nd|rd|th) )?mixing bowl into the (?:the )?(?:([1-9]\d*)(?:st|nd|rd|th) )?baking dish", ex)            
            if pour != None:                
                if pour.group(1) == None:
                    key = 0
                else:
                    key = int(pour.group(1))-1
                if pour.group(2) == None:                    
                    key2 = 0
                else:
                    key2 = int(pour.group(2))-1                
                self.ambigcheck(text, True)
                if not key2 in self.bakingdishes:                    
                    self.bakingdishes[key2] = []
                self.bakingdishes[key2].extend(self.mixingbowls[key])            
                continue
            
            ## M. Refrigerate
            refer = re.search("Refrigerate (?:for ([0-9]+))? hours", ex)
            if refer != None:
                if refer.group(1) != None:
                    self.serve(refer.group(1))
                sys.exit()
            
            ## N. Add dry ingredients
            adddry = re.search("Add dry ingredients(?: to the (1st|2nd|3rd|[0-9]+th) mixing bowl)?", ex)
            if adddry != None:
                def isdry(x):
                    return x[1] == "dry"
                def dryvalues(x):
                    return x[0]
                dry = filter(isdry, self.ingredientlist.values())
                dry = map(dryvalues, dry)            
                self.put(adddry.group(1), [sum(dry), "dry", "sumofall"], text)
            
            ## O. Call for sous-chef
            auxiliary = re.match("Serve with ([a-zA-Z ]+)", ex)
            if auxiliary != None:                                
                auxtext = re.search(auxiliary.group(1) + "\.\n\n(.*)", self.origscript, re.IGNORECASE|re.DOTALL)
                if not auxtext: # error!
                    print("A sub-recipe was listed but could not be found. Try hiring a new sous-chef?")
                    raise IOError
                souschef = Chef(auxtext.group(), copy.copy(self.mixingbowls))
                souschef.parse()
                readymixingbowls = souschef.mixingbowls                
                self.mixingbowls[0].extend(readymixingbowls[0])
            
            ## P. Stir
            stir = re.match("Stir(?: the (1st|2nd|3rd|[0-9]+th) mixing bowl)? for ([1-9]+) minutes?", ex)
            if stir != None:
                self.stir(stir.group(1),stir.group(2),None)    #Args: mixingbowl, minutes, ingredient
            stir = re.match("Stir (a-zA-Z0-9 )+ into the (1st|2nd|3rd|[0-9]+th) mixing bowl", ex)
            if stir != None:
                self.stir(stir.group(2),0,stir.group(1))    #Args: mixingbowl, minutes, ingredient
            
            ## Q. No standard keyword: look for a verb to begin a loop
            verb = re.search("([a-zA-Z]+) the ([a-zA-Z ]+) ?(?!until)", ex)
            if verb != None:                
                if "until" in verb.group():
                    continue
                if not verb.group(2) in self.ingredientlist:    # verb.group(2) is the ingredient
                    continue
                if self.ingredientlist[verb.group(2)][0] == 0:
                    continue
                else:
                    ## Verb Maintenance
                    if verb.group(1)[-1] == "e":
                        verbw = verb.group(1)[:-1]          # Verbs that end in e need to drop it before adding ed below.
                    elif verb.group(1)[-1] == "y":
                        verbw = verb.group(1)[:-1] + "i"    # Verbs that end in y need to swap it for an i before adding ed.
                    else:
                        verbw = verb.group(1)               # Any other verbs just need ed adding below.
                    
                    ## Find everything in between the loop 
                    ## TODO - watch out for nested loops with the same verb!
                    
                    #looptext = re.search(verb.group() + "\.((.*?)\s+[a-zA-Z]+ (?:the ([a-zA-Z ]+)) until " + verbw + "ed)", text, re.DOTALL|re.IGNORECASE)
                    re_text = verb.group() + "\.((.*?)\s+[a-zA-Z]+ ?(?:(the )?([a-zA-Z ]+))? ?until " + verbw + "ed)"
                    looptext = re.search(re_text, text, re.DOTALL|re.IGNORECASE)
                    
                    if not looptext:
                        print(f'Verb unmatched. Could not find "{re_text}" in "{text}"')
                        raise IOError
                    
                    deltext =  re.split("\.\s+", looptext.group(1))
                    deltext = map(stripwhite, deltext)
                    for d in deltext:
                        excode.remove(d)
                    while self.ingredientlist[verb.group(2)][0] != 0:
                        r = self.execute(looptext.group(2), True)
                        if r == "ENDOFLOOP":
                            break
                        if looptext.group(3) != None:
                            if looptext.group(3) == 'the ':
                                ing = looptext.group(4).rstrip()
                            else:
                                ing = looptext.group(3).rstrip()
                            self.ingredientlist[ing][0] -= 1
            if loop == True:
                setaside = re.search("Set aside", ex)                
                if setaside != None:
                    return "ENDOFLOOP"
                
    def serve(self, number):
        """
            This statement writes to STDOUT the contents of the first <number> baking dishes. 
            It begins with the 1st baking dish, removing values from the top one by one 
             and printing them until the dish is empty, then progresses to the next dish, 
             until all the dishes have been printed. 
            The Serves statement is optional, but is required if the recipe is to output anything!
        """
        
        output = ""
        if number > len(self.bakingdishes):
            number = len(self.bakingdishes)
        for i in range(0, number):
            if self.bakingdishes[i]:
                for j in self.bakingdishes[i]:
                    value = j[0]
                    if j[1] == "liquid":
                        value = chr(value)
                    output += str(value)
        
        """
            This is extended slice syntax.
            It works by doing [begin:end:step].
            By leaving begin and end off and specifying a step of -1,
             it reverses a string.
            https://stackoverflow.com/questions/931092/reverse-a-string-in-python
        """
        ## TODO -- one or other of the standard recipes is incorrectly reversed.
        return output[::-1] ## SFM: the loop outputs backwards, so reverse here

if __name__ == "__main__":
    try:
        f = open(sys.argv[1], "r")
        main = Chef(f.read())
        print(main.parse())
    except(IOError):
        pass # Should have been reported already
    except(IndexError):
        pass # Should have been reported already
