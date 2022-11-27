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

## Log anything of priority INFO and higher
logging.basicConfig(level=logging.INFO, 
## How the log message is formatted.
## See https://docs.python.org/3/library/logging.html#formatter-objects
                    format='%(message)s' # get the message as a string(?)
                    )


class Chef:
    """
        Parse a recipe.
        Calls instances of itself to parse auxiliary recipes.
    """
    
    def __init__(self, script, mixingbowls = {DEFAULT_BOWL: []}):
        
        ## Initialise and set object properties
        ## The script of this recipe.
        self._script         = script
        
        ## Keep an original copy of the script, because self.script
        ##  will be slowly modified as we work through each section.
        ## TODO we will be changing this so that self.script stays the same.
        # self.origscript     = script
        
        ## If this is an auxiliary recipe, we inherit mixing bowls from the
        ##  calling recipe.
        ## We make a copy so as not to modify the original mixing bowls.
        self.mixingbowls    = copy.deepcopy(mixingbowls)
        
        ## Initialise empty baking dishes.
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
        
        self.recipename = re.match(
            ## (.*?): Create a group () that matches any text or whitespace except  \n
            "(.*?)\.\n\n",
            self.script)
        
        
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
            self.serve(int(serves.group(1)))
        
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
        
        if number > len(self.bakingdishes):
            number = len(self.bakingdishes)
        for i in range(DEFAULT_BOWL, number+DEFAULT_BOWL):
            if self.bakingdishes[i]:
                
                """
                    This is extended slice syntax.
                    It works by doing [begin:end:step].
                    By leaving begin and end off and specifying a step of -1,
                     it reverses a string.
                    (Starts at the very beginning, ends at the very end, but steps "backwards".)
                    https://stackoverflow.com/questions/931092/reverse-a-string-in-python
                """
                for j in self.bakingdishes[i][::-1]:
                    value = j[0]
                    if j[1] == "liquid":
                        value = chr(value)
                    print(value) ## Outputs to STDOUT by default
    
    """
        Aliases: Lazy instantiation of class properties.
        Define a bunch of public property names that are actually wrappers to class methods.
        The class method figures out whether the corresponding private property exists yet.
        If the property already exists, the method returns it.
        If it doesn't, the method creates the property and returns it.
    """
    @property
    def script(self): return self._script
    
    @property
    def recipename(self):
        """
        Lazy instantiation of the recipe name.

        Returns
        -------
        _recipename: string
            The name of the current recipe.

        """
        
        if hasattr(self,"_recipename"): return self._recipename
            
        ## We have not yet determined the recipe name. Do it now.
        
        ## Use regular expression to find the recipe name within the self.script string.
        ## re.match() tries to find just the first instance of a pattern.
        match_recipename = re.match(
            ## (.*): Create a group, (), that matches any text or whitespace, ., except \n multiple times, *
            ## \.: match the full stop character . exactly
            ## \n\n: match two newline characters exactly
            "(.*)\.\n\n",
            self.script)
        
        ## We expect exactly one result.
        if match_recipename == None or len(match_recipename.groups()) > 1:
            logger.error("Invalid recipe name")
            sys.exit(-1)
        
        ## group(1) will return the 1st capture (stuff within the brackets).
        ## group(0) will returned the entire matched text i.e. with the \n\n included.
        ## We don't want the newlines included, so we just get group(1).
        self._recipename = match_recipename.group(1)
        
        return self._recipename
    
    @property
    def comment(self):
        """
        Lazy instantiation of the recipe comment.

        Returns
        -------
        comment: string
            Comment describing the recipe.
            Note that the comment is optional.
            If it doesn't exist, this method returns None.
        """
        
        ## Have we already determined the comment?
        if hasattr(self,'_comment'): return self._comment
        
        ## We have not yet figured out what the comment is, or if it even exists.
        
        ## First, get a copy of the script with the recipe name, first full stop and newlines removed.
        script_without_recipename = re.sub(self.recipename+"\.\n\n", "", self.script)
        
        ## Now get the first thing that matches a paragraph.
        match_comment = re.match(
            ## Match everything except newlines, followed by two newlines and the word "Ingredients."
            "(.*)\n\nIngredients\.", 
            script_without_recipename,
            )
        
        ## Is there a comment?
        if match_comment is None:
            ## There is no comment.
            ## Set self._comment to None and return it.
            self._comment = None
            return self._comment
        
        ## There is a comment.
        self._comment = match_comment.group(1)
        
        return self._comment
    
    @property
    def ingredients(self)->dict:
        """
        Lazy instantiation of the recipe ingredients.

        Returns
        -------
        _ingredients: dict
            Dictionary of ingredients.
            Key is the name of the thing e.g. beans, water, sugar
            Value is a 3-element list [Quantity, Type, Name]
                Quantity is an integer
                Type is a string: dry or liquid
                Name is a string: same as the key (it's useful to have it in the list too)
            
        """
        
        if hasattr(self,"_ingredients"): return self._ingredients
        
        ## Get a copy of the script without the title or comment
        ## First remove the title
        script_up_to_ingredients = re.sub(self.recipename+"\.\n\n", "", self.script)
        
        ## Now remove the comment, if there is one
        if self.comment is not None:
            script_up_to_ingredients = script_up_to_ingredients.replace(self.comment+"\n\n", "")
        
        ## Now the beginning of script_up_to_ingredients is "Ingredients.\n"
        ingredients_header = re.match("Ingredients\.\n", script_up_to_ingredients)
        
        if ingredients_header is None:
            logger.error("Ingredient list not found")
            sys.exit(-1)
            
        ## Again, replace with nothing.
        script_up_to_ingredients = script_up_to_ingredients.replace("Ingredients.\n","")
        
        ## Match all of the individual ingredients.
        ingredients_match = re.findall(
            ## (([0-9]*): There may or may not be an integer
            ##  ?: There may or may not be a single whitespace
            ## (k?g|pinch(?:es)?|m?l|dash(?:es)?|cups?|teaspoons?|tablespoons?)?: 
                ## There may or may not be a unit of measure
            ##  ?: There may or may not be a(nother) single whitespace
            ## ([a-zA-Z0-9 ]+): There needs to be an ingredinent name, which can contain whitespaces and numbers
            "(([0-9]*) ?(k?g|pinch(?:es)?|m?l|dash(?:es)?|cups?|teaspoons?|tablespoons?)? ?([a-zA-Z0-9 ]+)\n)", 
            script_up_to_ingredients)
        
        self._ingredients = {}
        
        ## Now step through each match, delete it from the recipe and add it to the dictionary
        for ingredient in ingredients_match:
            
            ## Check the thing matched really is in the string
            ## (I don't know how it couldn't be, but I'm leaving this check here just in case.)
            if re.match(ingredient[0], script_up_to_ingredients) is not None:
                
                ## Delete this ingredient from the recipe string
                script_up_to_ingredients = script_up_to_ingredients.replace(ingredient[0], "")
            
            ## Dry or liquid? Check the unit of measure.
            ##  Note that chr() is not run on values until output.
            ##   This is to allow arithmetic operations on liquids.
            ## There is a pre-defined set of liquid types.
            if ingredient[2] in ["dash", "cup", "l", "ml", "dashes", "cups"]:
                
                ## The quantity is an integer
                quantity = int(ingredient[1])
                ingredient_type = "liquid"
                
            else:
                ## It's a dry ingredient, and it might have a quantity
                ingredient_type = "dry"
                
                try:
                    quantity = int(ingredient[1])
                except ValueError:
                    ## There's no number there, so the quantity is None.
                    ## This means the user will be prompted to input the quantity at runtime.
                    quantity = None
            
            ## Add the dictionary entry.
            self._ingredients[ingredient[3]] = [quantity, ingredient_type, ingredient[3]]
        
        return self._ingredients
    
    @property
    def method(self):
        """
        Lazy instantiation to get the method of this recipe.
        If the recipe contains an auxiliary recipe, this just returns the main method.

        Returns
        -------
        _method: dict maybe?
            The method of this recipe.

        """
        
        ## Have we already extracted the method?
        if hasattr(self,"_method"): return self._method
        
        ## We haven't yet found the method so we need to find it now.
        ## First get a copy of <self.script>, deleting everything up to and including 
        ##  the line declaring the start of the method.
        match_method_to_end = re.sub(
            "(.*?)Method.\n", # find everything up to and including the method declaration
            "", # replace with "" i.e. delete it all
            self.script, 
            flags=re.DOTALL, # the dot character . matches newlines
            count=1) # Just delete everything up to the FIRST method declaration.
                     # Required because there might be auxiliary recipes.
        
        ## From here, each method step is one newline after another,
        ##  all the way until we reach two newlines.
        match_method = re.match("(.*?)\n\n", match_method_to_end, re.DOTALL)
        
        ## Extract the method steps as a list of strings,
        ##  omitting the entries corresponding to the final two newlines.
        self._method = match_method.group().split('\n')[:-2]
        
        return self._method
    
def load(fpath):
    """
    Load a recipe into a Chef object and return the object without parsing.

    Parameters
    ----------
    fpath : string
        Filepath of the Chef recipe.

    Returns
    -------
    chef : Chef()
        Chef object with the specified recipe loaded.

    """
    
    with open(fpath, "r",encoding='utf-8') as f:
        chef = Chef(f.read())
    
    return chef

if __name__ == "__main__":
    try:
        
        with open(sys.argv[1], "r",encoding='utf-8') as f:
            main = Chef(f.read())
            logger.info(main.parse())
            
    except IOError as e:
        logger.error(f'Fatal error: {str(e)}')
        
        
    except IndexError as e:
        logger.error(f'Fatal error: {str(e)}')
