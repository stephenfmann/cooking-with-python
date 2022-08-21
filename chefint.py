# -*- coding: utf-8 -*-
"""
    chefint.py
    Interpret programs written in the esolang Chef.
    See https://www.dangermouse.net/esoteric/chef.html for details.
"""

import sys, re, random, copy, logging

## Global constants
DEFAULT_BOWL = 1 # the default mixing bowl number (also applies to baking dishes)

## Configure logging
logger = logging.getLogger("Chef")
logging.basicConfig(level=logging.INFO, format='%(message)s')


class Chef:
    """
        Parse a recipe.
        Calls instances of itself to parse sub-recipes.
    """
    
    def __init__(self, script, mixingbowls = {DEFAULT_BOWL: []}):
        self.script         = script
        self.origscript     = script
        self.mixingbowls    = copy.deepcopy(mixingbowls)
        self.bakingdishes   = {}
        
    
    def syntax_error(self,message):
        """
            A syntax error was found in the Chef script.
        """
        
        ## TODO: report line number.
        logger.error(f"Syntax error: {message}")
        sys.exit(-1)
        
    def cooking_error(self,message):
        """
            A runtime error
        """
        
        ## TODO - report line number
        logger.error(f"Cooking time error: {message}")
        sys.exit()
    
    def parse(self):
        """
            Parse and execute the recipe in self.script.
        """
        
        ## 1. Find recipe name
        self.recipename = re.match("(.*?)\.\n\n", self.script)
        self.script = re.sub(self.recipename.group(), "", self.script)
        if(self.recipename == None):
            logger.error("Invalid recipe name")
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
            logger.error("Ingredient list not found")
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
                self.mixingbowls[DEFAULT_BOWL].append(value)
                return
            self.mixingbowls[DEFAULT_BOWL] = []                        
            self.mixingbowls[DEFAULT_BOWL].append(value)
            return
        
        ## Mixing bowl exists.
        key = int(mixingbowl)
        if not key in self.mixingbowls:
            self.mixingbowls[key] = []     
            
        self.mixingbowls[key].append(value)
            
        
    def fold(self, 
             ingredient, 
             mixingbowl
             )->None:
        """
        Opposite of put().
        
        This removes the top value from the <mixingbowl>th mixing bowl 
         and uses it as the new value of <ingredient>.
        
        The name and dry/wet status of <ingredient> should not change.

        Parameters
        ----------
        ingredient : str
            Name of ingredient whose value will be replaced.
        mixingbowl : str
            Ordinal numeral name of mixing bowl whose top ingredient's value
             will replace the value of <ingredient>.

        """
        
        ## Determine which mixing bowl to use.
        key = DEFAULT_BOWL
        if mixingbowl:
            key = int(mixingbowl[:-2])
        
        ## Get the ingredient out of the bowl
        full_ingredient = self.mixingbowls[key].pop()
        
        ## Put the removed ingredient's value onto the named ingredient.
        self.ingredientlist[ingredient][0] = full_ingredient[0]
        
        
    def addingredient(self, ingredient, mixingbowl):
        """
            Add the value of <ingredient> to the value of the ingredient 
             on top of the mixing bowl and store the result in the mixing bowl.
        """
        
        value = self.ingredientlist[ingredient][0]
        
        key = DEFAULT_BOWL
        if mixingbowl:
            key = int(mixingbowl[:-2])
            
        if value == None:
            value = 0
        
        self.mixingbowls[key][-1][0] += value
        
    def removeingredient(self, ingredient, mixingbowl):
        """
            Subtract the value of <ingredient> from the value of the ingredient 
             on top of the mixing bowl and store the result in the mixing bowl.
        """
        
        value = self.ingredientlist[ingredient][0]
        
        key = DEFAULT_BOWL
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
        
        key = DEFAULT_BOWL
        if mixingbowl:
            key = mixingbowl[:-2]
            
        if value == None:
            value = 0
        
        self.mixingbowls[key][-1][0] *= value
        
    def divideingredient(self, 
                         ingredient, 
                         mixingbowl = DEFAULT_BOWL
                         )->None:
        """
        Divide the value of the ingredient on top of mixing bowl <mixingbowl>
         by the value of <ingredient> and store the result in the mixing bowl.

        Parameters
        ----------
        ingredient : str
            Name of the ingredient whose value is the divisor.
        mixingbowl : str
            Ordinal numeral e.g. 1st, 2nd, 3rd etc
             indicating the mixing bowl whose top value
             is to be divided by the value of <ingredient>.
            To get just the number (as str), use <mixingbowl[:-2]>.

        """
        
        ## Get the divisor: the value of <ingredient>.
        value = self.ingredientlist[ingredient][0]
        
        ## Get the mixing bowl number.
        key = DEFAULT_BOWL
        if mixingbowl:
            key = mixingbowl[:-2] ## Get the integer (as string) from the ordinal numeral.
        
        ## Ingredients with no value are assumed to leave the mixing bowl unchanged.
        if value == None:
            value = 1
        
        ## Divide the top value of the mixing bowl by the ingredient value.
        ##  <key> is the bowl
        ##  <-1> indicates the top ingredient, which is a list with entries [value, wet/dry, name]
        ##  <0> is the first entry in that list, i.e. the ingredient's value.
        self.mixingbowls[key][-1][0] = float(self.mixingbowls[key][-1][0]/value)
        
    def stir(self,
             mixingbowl = DEFAULT_BOWL,
             minutes    = None,
             ingredient = None
             )->None:
        """
            This rolls the top <minutes> or <ingredient value> ingredients in the mixing bowl, 
             such that the top ingredient goes down that number of ingredients 
             and all ingredients above it rise one place. 
            If there are not that many ingredients in the bowl, 
             the top ingredient goes to the bottom of the bowl 
             and all the others rise one place.
        """
        
        ## Default is "Stir [the [nth] mixing bowl] for <minutes> minutes."
        value = int(minutes)
        
        ## Alternative is "Stir <ingredient> into the [nth] mixing bowl."
        ## Default to this if <ingredient> is supplied.
        if ingredient:
            value = int(self.ingredientlist[ingredient][0])
        
        ## Default to the zeroth mixing bowl
        key = DEFAULT_BOWL
        if mixingbowl:
            
            ## The string like '3rd' was supplied.
            ## Get the integer by chopping off the last two characters.
            key = int(mixingbowl[:-2])
            
        else:
            ## If no mixing bowl was named, there must only be one mixing bowl in the recipe.
            assert len(self.mixingbowls) == 1
        
        if key not in self.mixingbowls:
            self.syntax_error(f"Mixing bowl {str(key)} not found.")
        
        ## If the mixing bowl is empty, nothing happens.
        if not self.mixingbowls[key]: return
            
        ## We treat the "top" item in the mixing bowl as the last item in the list.
        ## That's because push and pop operate on last items rather than first.
        ## E.g. suppose we are rolling a mixing bowl with ingredient values (top to bottom):
        ##      1 2 3 4
        ## Then the list has entries
        ##      [4, 3, 2, 1]
        ## And suppose <value> is 2.
        ## Then the end result should be:
        ##      2 3 1 4
        ## Represented by the list
        ##      [4, 1, 3, 2]
        
        ## Remove the top ingredient
        ing = self.mixingbowls[key].pop() # e.g. [4, 3, 2]
        
        ## Insert the top ingredient at place <value>
        ## Location is <value> from the *end*, so multiply <value> by -1.
        self.mixingbowls[key].insert(-1*value,ing)
            
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
            fold = re.search("Fold (?:the )?([a-zA-Z ]+) into (?:the )?(1st|2nd|3rd|[0-9]+th)? ?mixing bowl", ex)
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
                    for i in self.mixingbowls[DEFAULT_BOWL]:                    
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
                        self.mixingbowls[DEFAULT_BOWL] = []
                else:
                    if clean.group(1)[:-2] in self.mixingbowls:
                        self.mixingbowls[clean.group(1)[:-2]] = []
                    else:
                        existslater = re.match(clean.group(1) + " mixing bowl", text)
                        if existslater == None:
                            logger.warning("Warning: Unknown mixing bowl"+str(clean.group(1)))
                        else:
                            logger.warning("Warning: Tried to clean mixing bowl"+str(clean.group(1))+"before putting anything in it!")
                continue
            
            ## J. Mix mixing bowl
            mix = re.search("Mix the (1st|2nd|3rd|[0-9]+th)? ?mixing bowl well", ex)
            if mix != None:
                if mix.group(1) == None:
                        random.shuffle(self.mixingbowls[DEFAULT_BOWL])
                else:
                    if mix.group(1)[:-2] in self.mixingbowls:
                        random.shuffle(self.mixingbowls[clean.mix(1)[:-2]])
                    else:
                        existslater = re.match(clean.mix(1) + " mixing bowl", text)
                        if existslater == None:
                            logger.warning("Warning: Unknown mixing bowl"+mix.group(1))
                        else:
                            logger.warning("Warning: Tried to mix mixing bowl"+str(mix.group(1))+"before putting anything in it!")
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
                    key = DEFAULT_BOWL
                else:
                    key = int(pour.group(1))
                if pour.group(2) == None:                    
                    key2 = DEFAULT_BOWL
                else:
                    key2 = int(pour.group(2))
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
                    logger.error("A sub-recipe was listed but could not be found. Try hiring a new sous-chef?")
                    raise IOError
                
                ## Quick fix to recursion error
                try:
                    souschef = Chef(auxtext.group(), copy.copy(self.mixingbowls))
                    souschef.parse()
                except RecursionError:
                    msg = f'Error: Your sub-recipe {str(auxiliary.group(1))} contains a reference to itself. '+\
                        'The kitchen is not equipped to handle infinite recursion.'
                    logging.error(msg)
                    sys.exit(-1)
                
                readymixingbowls = souschef.mixingbowls                
                self.mixingbowls[DEFAULT_BOWL].extend(readymixingbowls[DEFAULT_BOWL])
            
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
                        logger.error(f'Verb unmatched. Could not find "{re_text}" in "{text}"')
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
        for i in range(DEFAULT_BOWL, number+DEFAULT_BOWL):
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
            (Starts at the very beginning, ends at the very end, but steps "backwards".)
            https://stackoverflow.com/questions/931092/reverse-a-string-in-python
        """
        ## TODO -- one or other of the standard recipes is incorrectly reversed.
        return output[::-1] ## SFM: the loop outputs backwards, so reverse here

if __name__ == "__main__":
    try:
        
        with open(sys.argv[1], "r",encoding='utf-8') as f:
            main = Chef(f.read())
            logger.info(main.parse())
            
    except IOError as e:
        logger.error(f'Fatal error: {str(e)}')
        
        
    except IndexError as e:
        logger.error(f'Fatal error: {str(e)}')
