# -*- coding: utf-8 -*-
"""
    chefint.py
    Interpret programs written in the esolang Chef.
    See syntax.md or https://www.dangermouse.net/esoteric/chef.html for details.
     (archived at https://web.archive.org/web/20220615003505/http://www.dangermouse.net/esoteric/chef.html)
"""

import sys, re, random, copy, logging

## Global constants
DEFAULT_BOWL = 1 # the default mixing bowl number
DEFAULT_DISH = 1 # the default baking dish number

## Configure logging
logger = logging.getLogger("Chef")

## Log anything of priority INFO and higher
logging.basicConfig(level=logging.INFO, 
## How the log message is formatted.
## See https://docs.python.org/3/library/logging.html#formatter-objects
                    format='%(message)s' # get the message as a string
                    )


class Chef:
    """
        Contains recipes and is able to cook them by parsing methods.
        Calls instances of itself to hold and cook auxiliary recipes.
    """
    
    def __init__(self, script, mixingbowls = {DEFAULT_BOWL: []}):
        
        ## Initialise and set object properties.
        ## The script of this recipe.
        self._script         = script
        
        ## If this is an auxiliary recipe, we inherit mixing bowls from the
        ##  calling recipe.
        ## We make a copy so as not to modify the original mixing bowls.
        self.mixingbowls    = copy.deepcopy(mixingbowls)
        
        ## Initialise empty baking dishes.
        self.bakingdishes   = {}
    
    
    def syntax_error(self,message)->None:
        """
            A syntax error was found in the Chef script.
        """
        
        logger.error(f"Syntax error on line {self.current_instruction_line}: {message}")
        sys.exit(-1)
    
    def runtime_error(self,message)->None:
        """
        A runtime error occurred during cooking.

        Parameters
        ----------
        message : string
            Information about the error.
        """
        
        logger.error(f"Runtime error on line {self.current_instruction_line}: {message}")
        sys.exit(-1)
    
    def cook(self,debug=True)->None:
        """
        Step through the recipe's Method and execute each line.
        """
        
        ## We use a global counter to remember where we are in the recipe.
        ## This helps when jumping into and out of loops and error reporting.
        ## Initialise the index before starting to cook.
        self.current_instruction_line = 0
        
        ## Begin cooking, stepping through the lines one at a time.
        ## As long as our current instruction line exists,
        ##  we will continue to cook.
        while self.current_instruction_line < len(self.method):
            
            ## Get the current instruction.
            ## This is a string, <instruction>, within the list, <self.method>.
            instruction = self.method[self.current_instruction_line]
            
            ## DEBUG
            if debug: print(f"Executing: {instruction}")
            
            ## Parse and execute this instruction.
            self.parse_instruction(instruction)
            
            ## Increment the current instruction index.
            ## So long as there were no loops, this will just become
            ##  1 higher than the previous iteration of the while-loop.
            ## parse_instruction() handles loops so that when a loop completes,
            ##  self.current_instruction_line is the final line of the loop
            ##  (i.e. Verb [the ingredient] until verbed.)
            ## Therefore adding 1 to it here is correct, as it means we will
            ##  move to the next instruction after the end of the loop.
            self.current_instruction_line += 1
        
        ## Serve the finished dish.
        self.serve()
    
    
    def cook_loop(self,
                  method_lines,
                  ingredient_name_start,
                  ingredient_name_end=None
                  )->None:
        """
        A loop instruction was found in the method.
        The relevant instruction lines were passed here,
         along with the ingredient name.
        When the value of that ingredient reaches zero,
         or when the 'Set aside' instruction is reached,
         exit the loop.
         
         method_lines: dict
             keys are line numbers,
             values are instruction strings.
        """
        
        ## The instruction `Set aside.` will cause this loop to immediately terminate.
        set_aside = False
        
        ## Only enter the loop if the ingredient value is non-zero.
        while self.ingredients[ingredient_name_start] != 0:
            
            ## Run through the entire loop (unless `Set aside.` is encountered.)
            for line_number, instruction in method_lines.items():
                
                ## Set current line number.
                self.current_instruction_line = line_number
                
                ## Execute current instruction.
                set_aside = self.parse_instruction(instruction)
                
                ## `Set aside.` causes the loop to end immediately.
                if set_aside: break
            
            ## `Set aside.` causes the loop to end immediately.
            if set_aside: break
        
            ## "If the ingredient appears in this statement, 
            ##   its value is decremented by 1 when this statement executes."
            if ingredient_name_end is not None:
                self.ingredients[ingredient_name_end] -= 1
        
        ## Set current index to the final line number of the loop.
        self.current_instruction_line = list(method_lines.keys())[-1]
    
    
    def serve(self)->None:
        """
        This statement writes to STDOUT the contents of the first <number> baking dishes. 
        It begins with the 1st baking dish, removing values from the top one by one 
         and printing them until the dish is empty, then progresses to the next dish, 
         until all the dishes have been printed. 
        The Serves statement is optional, but is required if the recipe is to output anything!
        """
        
        ## Find the Serves statement.
        serves = re.search("Serves ([0-9]+).", self.script)
        
        if serves == None:
            ## The serves statement is optional. If it doesn't exist, don't do anything.
            return
        
        ## The number of people to serve is the first <number> of baking dishes
        ##  to print to STDOUT.
        number = int(serves.group(1))
        
        ## If we don't have that many baking dishes, we will just output all of them.
        if number > len(self.bakingdishes):
            
            ## Warn the user.
            logger.warning("{number} baking dishes requested but only {len(self.bakingdishes)} available.")
            
            ## Just output the baking dishes we actually have.
            number = len(self.bakingdishes)
        
        ## Loop through all baking dishes and output the contents of each, in order.
        ## We index dishes from 1, for consistency with the Chef language specification.
        for i in range(DEFAULT_BOWL, number+DEFAULT_BOWL):
            
            ## Because of the way we are stacking objects in lists,
            ##  the FINAL element of the list is the FIRST ingredient in the dish.
            ## So we are going to output elenents from the end to the beginning.
            ## In order to do that efficiently, we use *extended slice syntax*.
            ## It works by doing [begin:end:step].
            ## By leaving begin and end blank and specifying a step of -1,
            ##  it reverses a string.
            ## (Starts at the very beginning, ends at the very end, but steps "backwards".)
            ## See https://stackoverflow.com/questions/931092/reverse-a-string-in-python
             
            for j in self.bakingdishes[i][::-1]:
                
                ## Get the value of this ingredient
                value = j[0]
                
                ## If it's liquid, we are treating the integer value as a character value.
                if j[1] == "liquid":
                    value = chr(value)
                
                ## Output the value of this ingredient to STDOUT
                print(value)
    
    
    def parse_instruction(self, instruction)->bool:
        """
            Main interpreting function.
            Check the text line <instruction> for what action to take.
            
        Returns
        -------
        bool
            Whether the `Set aside.` instruction was encountered.
        """
        
        ## `Set aside.`
        ## 'This causes execution of the innermost loop in which it occurs 
        ##   to end immediately and execution to continue at the statement 
        ##   after the "until".'
        ## Should be an exact match.
        if instruction == "Set aside.":
            return True
        
        
        ## INTERPRETING THE INSTRUCTION
        ## For each possible instruction we will use a regex
        ##  to determine whether the current line is an instance
        ##  of that instruction.
        
        ## A. Put
        ##  `Put ingredient into [nth] mixing bowl.`
        ## This puts the ingredient into the nth mixing bowl.
        ## Create the regex.
        put_regex = "^Put (?:the )?([a-zA-Z ]+) into (?:the )?(?:([1-9]\d*)(?:st|nd|rd|th) )?mixing bowl"
        
        ## See if the current line fits this regex.
        put = re.search(put_regex, instruction)
        
        ## If the regex search returned something...
        if put != None:
            
            ## ...call the put() method...
            self.put(ingredient=put.group(1), mixingbowl=put.group(2))
            
            ## ...and return, so the calling method can move to the next instruction.
            return
        
        
        ## B. Fold
        ##  `Fold ingredient into [nth] mixing bowl.`
        ## This removes the top value from the nth mixing bowl 
        ##  and places it in the ingredient.
        ## Create the regex.
        fold_regex = "Fold (?:the )?([a-zA-Z ]+) into (?:the )?(1st|2nd|3rd|[0-9]+th)? ?mixing bowl"
        
        ## See if the current line fits this regex.
        fold = re.search(fold_regex, instruction)
        
        ## If the regex search returned something...
        if fold != None:
            
            ## ...ensure that if the bowl number wasn't specified, there is only one bowl...
            if fold.group(2) == None and self.has_multiple_bowls:
                self.syntax_error("Bowl number unspecified.") 
            
            ## ...call the fold() method...
            self.fold(fold.group(1), fold.group(2))
            
            ## ...and return, so the calling method can move to the next instruction.
            return
        
        
        ## C. Add
        ##  `Add ingredient [to [nth] mixing bowl].`
        ## This adds the value of <ingredient> to the value of the ingredient 
        ##  on top of the nth mixing bowl and stores the result in the nth mixing bowl.
        ## Create the regex.
        add_regex = "Add ([a-zA-Z0-9 ]+?) to (?:the )?(?:(1st|2nd|3rd|[0-9]+th) )?mixing bowl"
        
        ## See if the current line fits this regex.
        add = re.search(add_regex, instruction)
        
        ## If the regex search returned something...
        if add != None:
            
            ## ...ensure that if the bowl number wasn't specified, there is only one bowl...
            if add.group(2) == None and self.has_multiple_bowls:
                self.syntax_error("Bowl number unspecified.") 
            
            ## ...call the addingredient() method...
            self.addingredient(add.group(1), add.group(2))
            
            ## ...and return, so the calling method can move to the next instruction.
            return
        
        
        ## D. Remove
        ##  `Remove ingredient [from [nth] mixing bowl].`
        ## This subtracts the value of <ingredient> from the value of the ingredient 
        ##  on top of the nth mixing bowl and stores the result in the nth mixing bowl.
        ## Create the regex.
        remove_regex = "Remove ([a-zA-Z0-9 ]+?) from (?:the )?(?:(1st|2nd|3rd|[0-9]+th) )?mixing bowl"
        
        ## See if the current line fits this regex.
        remove = re.search(remove_regex, instruction)
        
        ## If the regex search returned something...
        if remove != None:
            
            ## ...ensure that if the bowl number wasn't specified, there is only one bowl...
            if remove.group(2) == None and self.has_multiple_bowls:
                self.syntax_error("Bowl number unspecified.") 
            
            ## ...call the removeingredient() method...
            self.removeingredient(remove.group(1), remove.group(2))
            
            ## ...and return, so the calling method can move to the next instruction.
            return
        
        
        ## E. Combine
        ##  `Combine ingredient [into [nth] mixing bowl].`
        ## This multiplies the value of <ingredient> by the value of the ingredient 
        ##  on top of the nth mixing bowl and stores the result in the nth mixing bowl.
        ## Create the regex.
        combine_regex = "Combine ([a-zA-Z0-9 ]+?) into (?:the )?(?:(1st|2nd|3rd|[0-9]+th) )?mixing bowl"
        
        ## See if the current line fits this regex.
        combine = re.search(combine_regex, instruction)
        
        ## If the regex search returned something...
        if combine != None:
            
            ## ...ensure that if the bowl number wasn't specified, there is only one bowl...
            if combine.group(2) == None and self.has_multiple_bowls:
                self.syntax_error("Bowl number unspecified.")
            
            ## ...call the combineingredient() method...
            self.combineingredient(combine.group(1), combine.group(2))
            
            ## ...and return, so the calling method can move to the next instruction.
            return
        
        
        ## F. Divide
        ##  `Divide ingredient [into [nth] mixing bowl].`
        ## This divides the value of <ingredient> into the value of the ingredient 
        ##  on top of the nth mixing bowl and stores the result in the nth mixing bowl.
        ## Create the regex.
        divide_regex = "Divide ([a-zA-Z0-9 ]+?) into (?:the )?(?:(1st|2nd|3rd|[0-9]+th) )?mixing bowl"
        
        ## See if the current line fits this regex.
        divide = re.search(divide_regex, instruction)
        
        ## If the regex search returned something...
        if divide != None:
            
            ## ...ensure that if the bowl number wasn't specified, there is only one bowl...
            if divide.group(2) == None and self.has_multiple_bowls:
                self.syntax_error("Bowl number unspecified.")
            
            ## ...call the divideingredient() method...
            self.divideingredient(divide.group(1), divide.group(2))
            
            ## ...and return, so the calling method can move to the next instruction.
            return
        
        
        ## G. Liquefy mixing bowl
        ##  `Liquefy contents of the [nth] mixing bowl.`
        ## This turns all the ingredients in the nth mixing bowl into a liquid, 
        ##  i.e. a Unicode characters for output purposes.
        ## Create the regex.
        liquefy_bowl_regex = "Liquefy contents of the (1st|2nd|3rd|[0-9]+th)? ?mixing bowl"
        
        ## See if the current line fits this regex.
        liquefy_bowl = re.search(liquefy_bowl_regex, instruction)
        
        ## If the regex search returned something...
        if liquefy_bowl != None:             
            
            ## ...ensure that if the bowl number wasn't specified, there is only one bowl...
            if liquefy_bowl.group(1) == None and self.has_multiple_bowls:                    
                self.syntax_error("Bowl number unspecified.")
            
            ## ...explicitly define the bowl number...
            bowl_number = int(liquefy_bowl.group(1)[:-2]) if liquefy_bowl.group(1) is not None else DEFAULT_BOWL
            
            ## ...convert every ingredient in the bowl to liquid...
            for ingredient in self.mixingbowls[bowl_number]:                    
                ingredient[1] = "liquid"                            
            
            ## ...and return, so the calling method can move to the next instruction.
            return
        
        
        ## H. Liquefy ingredient.
        ##  `Liquefy ingredient.`
        ## This turns the ingredient into a liquid, 
        ##  i.e. a Unicode character for output purposes.
        ## Create the regex.
        liquefy_ingredient = "Liquefy ([a-zA-Z]+)"
        
        ## See if the current line fits this regex.
        liquefy_ingredient = re.search(liquefy_ingredient, instruction)
        
        ## If the regex search returned something...
        if liquefy_ingredient != None:
            
            ## ...set this ingredient's state to liquid...
            self.ingredients[liquefy_ingredient.group(1)][1] = "liquid"
            
            ## ...and return, so the calling method can move to the next instruction.
            return
        
        
        ## I. Clean mixing bowl
        ##  `Clean [nth] mixing bowl.`
        ## This removes all the ingredients from the nth mixing bowl.
        ## Create the regex.
        clean_regex = "Clean the (1st|2nd|3rd|[0-9]+th)? ?mixing bowl"
        
        ## See if the current line fits this regex.
        clean = re.search(clean_regex, instruction)
        
        ## If the regex search returned something...
        if clean != None:
            
            ## ...ensure that if the bowl number wasn't specified, there is only one bowl...
            if clean.group(1) == None and self.has_multiple_bowls:                    
                self.syntax_error("Bowl number unspecified.")
            
            ## ...explicitly define the bowl number...
            bowl_number = int(clean.group(1)[:-2]) if clean.group(1) is not None else DEFAULT_BOWL
            
            ## ...remove all ingredients from that bowl...
            self.mixingbowls[bowl_number] = []
            
            ## ...and return, so the calling method can move to the next instruction.
            return
        
        
        ## J. Mix mixing bowl
        ##  `Mix [the [nth] mixing bowl] well.`
        ## This randomises the order of the ingredients in the nth mixing bowl.
        ## Create the regex.
        mix_regex = "Mix the (1st|2nd|3rd|[0-9]+th)? ?mixing bowl well"
        
        ## See if the current line fits this regex.
        mix = re.search(mix_regex, instruction)
        
        ## If the regex search returned something...
        if mix != None:
            
            ## ...ensure that if the bowl number wasn't specified, there is only one bowl...
            if mix.group(1) == None and self.has_multiple_bowls:                    
                self.syntax_error("Bowl number unspecified.")
            
            ## ...explicitly define the bowl number...
            bowl_number = int(mix.group(1)[:-2]) if mix.group(1) is not None else DEFAULT_BOWL
            
            ## ...randomise the ingredients in that bowl...
            random.shuffle(self.mixingbowls[bowl_number])
            
            ## ...and return, so the calling method can move to the next instruction.
            return
        
        
        ## K. Take from fridge
        ##  `Take ingredient from refrigerator.`
        ## This reads a numeric value from STDIN into the ingredient named, 
        ##  overwriting any previous value.
        ## Create the regex.
        fridge_take_regex = "Take ([a-zA-Z ]+) from refrigerator"
        
        ## See if the current line fits this regex.
        fridge = re.search(fridge_take_regex, instruction)
        
        ## If the regex search returned something...
        if fridge != None:
            
            ## ...check the ingredient exists...
            if fridge.group(1) not in self.ingredients:
                self.syntax_error("Ingredient {fridge.group(1)} does not exist.")
            
            ## ...get the user input and store it as the value of the specified ingredient...
            self.ingredients[fridge.group(1)][0] = int(input(fridge.group(1) + ": "))
            
            ## ...and return, so the calling method can move to the next instruction.
            return
        
        
        ## L. Pour
        ##  `Pour contents of the [nth] mixing bowl into the [pth] baking dish.`
        ##  This copies all the ingredients from the nth mixing bowl to the 
        ##   pth baking dish, retaining the order and putting them 
        ##   on top of anything already in the baking dish.
        ## Create the regex
        pour_regex = "Pour contents of the (?:the )?(?:([1-9]\d*)(?:st|nd|rd|th) )?mixing bowl"+\
                        " into the (?:the )?(?:([1-9]\d*)(?:st|nd|rd|th) )?baking dish"
        
        ## See if the current line fits this regex.
        pour = re.search(pour_regex, instruction)   

        ## If the regex search returned something...   
        if pour != None:

            ## ...call the pour() method...
            self.pour(
                mixingbowl = pour.group(1),
                bakingdish = pour.group(2)
                )           
            
            ## ...and return, so the calling method can move to the next instruction.
            return
        
        
        ## M. Refrigerate
        ##  `Refrigerate [for number hours].`
        ## This causes execution of the recipe in which it appears to end immediately.
        ## If in an auxiliary recipe, the auxiliary recipe ends and 
        ##  the sous-chef's first mixing bowl is passed back to 
        ##  the calling chef as normal. 
        ## If a number of hours is specified, the recipe will print out 
        ##  its first <number> baking dishes before ending.
        refer = re.search("Refrigerate (?:for ([0-9]+))? hours", instruction)
        if refer != None:
            if refer.group(1) != None:
                self.serve(refer.group(1))
            sys.exit()
        
        
        ## N. Add dry ingredients
        adddry = re.search("Add dry ingredients(?: to the (1st|2nd|3rd|[0-9]+th) mixing bowl)?", instruction)
        if adddry != None:
            def isdry(x):
                return x[1] == "dry"
            def dryvalues(x):
                return x[0]
            dry = filter(isdry, self.ingredients.values())
            dry = map(dryvalues, dry)            
            self.put(adddry.group(1), [sum(dry), "dry", "sumofall"], instruction)
        
        
        ## O. Call for sous-chef
        auxiliary = re.match("Serve with ([a-zA-Z ]+)", instruction)
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
        stir = re.match("Stir(?: the (1st|2nd|3rd|[0-9]+th) mixing bowl)? for ([1-9]+) minutes?", instruction)
        if stir != None:
            self.stir(stir.group(1),stir.group(2),None)    #Args: mixingbowl, minutes, ingredient
        stir = re.match("Stir (a-zA-Z0-9 )+ into the (1st|2nd|3rd|[0-9]+th) mixing bowl", instruction)
        if stir != None:
            self.stir(stir.group(2),0,stir.group(1))    #Args: mixingbowl, minutes, ingredient
        
        ## Q. No standard keyword: look for a verb to begin a loop
        verb = re.search("([a-zA-Z]+) the ([a-zA-Z ]+) ?(?!until)", instruction)
        if verb != None:                
            if "until" in verb.group():
                return
            if not verb.group(2) in self.ingredients:    # verb.group(2) is the ingredient
                return
            if self.ingredients[verb.group(2)][0] == 0:
                return
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
                
                re_text = verb.group() + "\.((.*?)\s+[a-zA-Z]+ ?(?:(the )?([a-zA-Z ]+))? ?until " + verbw + "ed)"
                
                looptext = re.search(re_text, self.script, re.DOTALL|re.IGNORECASE)
                
                if not looptext:
                    logger.error(f'Verb unmatched. Could not find "{re_text}" in "{instruction}"')
                    raise IOError
                
                # deltext =  re.split("\.\s+", looptext.group(1))
                # deltext = map(stripwhite, deltext)
                # for d in deltext:
                #     excode.remove(d)
                while self.ingredients[verb.group(2)][0] != 0:
                    r = self.execute(looptext.group(2), True)
                    if r == "ENDOFLOOP":
                        break
                    if looptext.group(3) != None:
                        if looptext.group(3) == 'the ':
                            ing = looptext.group(4).rstrip()
                        else:
                            ing = looptext.group(3).rstrip()
                        self.ingredients[ing][0] -= 1
        
        
        ## Looks like nothing happened.
        ## This instruction contains no recognisable code,
        ##  so flag it as a syntax error.
        self.syntax_error("Instruction not recognised: {instruction}")
        
        
    def put(self, ingredient, mixingbowl):
        """
        This puts the ingredient into the nth mixing bowl.
        """
        
        ## Use the default bowl if none was supplied
        if not mixingbowl: mixingbowl = DEFAULT_BOWL
        
        ## Check the ingredient exists
        if ingredient not in self.ingredients: self.syntax_error(f"Ingredient not found: {ingredient}")
        
        ## Check the mixing bowl exists
        if mixingbowl not in self.mixingbowls: self.runtime_error(f"Mixing bowl {mixingbowl} does not exist.")
        
        ## Add ingredient to top of mixingbowl
        self.mixingbowls[mixingbowl].append(self.ingredients[ingredient])
        
        
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
        self.ingredients[ingredient][0] = full_ingredient[0]
        
        
    def addingredient(self, 
                      ingredient, 
                      mixingbowl
                      ):
        """
            Add the value of <ingredient> to the value of the ingredient 
             on top of the mixing bowl and store the result in the mixing bowl.
        """
        
        ## If no mixing bowl was supplied, use the default
        if not mixingbowl: mixingbowl = DEFAULT_BOWL
        
        ## Check the ingredient exists
        if ingredient not in self.ingredients: self.syntax_error(f"Ingredient not found: {ingredient}")
        
        ## Check the mixing bowl exists
        if mixingbowl not in self.mixingbowls: self.runtime_error(f"Mixing bowl {mixingbowl} does not exist.")
        
        ## Get the value of the ingredient
        value = self.ingredients[ingredient][0]
        
        ## It's mixing bowl number <mixingbowl>
        ## It's the top ingredient, which is index -1
        ## It's the value of that ingredient, which is index 0
        ## Altogether, that's self.mixingbowls[mixingbowl][-1][0].
        ## We add the specified ingredient's value to that.
        self.mixingbowls[mixingbowl][-1][0] += value
        
    def removeingredient(self, ingredient, mixingbowl):
        """
            Subtract the value of <ingredient> from the value of the ingredient 
             on top of the mixing bowl and store the result in the mixing bowl.
        """
        
        value = self.ingredients[ingredient][0]
        
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
        
        value = self.ingredients[ingredient][0]
        
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
        value = self.ingredients[ingredient][0]
        
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
    
    
    def pour(self,
             mixingbowl = None,
             bakingdish = None
             )->None:
        """
        This copies all the ingredients from the nth mixing bowl 
         to the pth baking dish, retaining the order and putting them 
         on top of anything already in the baking dish.

        Parameters
        ----------
        mixingbowl : TYPE, optional
            DESCRIPTION. The default is None.
        bakingdish : TYPE, optional
            DESCRIPTION. The default is None.

        Returns
        -------
        None
            DESCRIPTION.

        """
        
        ## Revert to default mixing bowl if necessary
        mixingbowl = int(mixingbowl[:-2]) if mixingbowl else DEFAULT_BOWL
        
        ## Revert to default baking dish if necessary
        bakingdish = int(bakingdish[:-2]) if bakingdish else DEFAULT_DISH
        
        ## Create the baking dish if necessary
        if not bakingdish in self.bakingdishes:                    
            self.bakingdishes[bakingdish] = []
        
        ## Copy contents of mixing bowl into baking dish
        self.bakingdishes[bakingdish].extend(self.mixingbowls[mixingbowl]) 
        
    
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
            value = int(self.ingredients[ingredient][0])
        
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
    def recipename(self)->str:
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
    def comment(self)->str:
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
    def method(self)->list:
        """
        Lazy instantiation to get the method of this recipe.
        If the recipe contains an auxiliary recipe, this just returns the main method.

        Returns
        -------
        _method: list
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
    
    @property
    def has_multiple_bowls(self)->bool:
        """
        'If no identifier is used, the recipe only has one of the relevant utensil.'
        
        It's helpful to know whether or not the recipe is allowed to refer to 
         'the mixing bowl' or will be forced to use ordinal identifiers.
        
        We will allow it to refer to 'the 1st mixing bowl' even if there is
         only exactly one bowl.

        Returns
        -------
        bool
            if True, the recipe contains references to multiple bowls.
            if False, it doesn't.

        """
        
        ## Lazy instantiation
        if hasattr(self,"_has_multiple_bowls"): return self._has_multiple_bowls
        
        ## Default to False
        self._has_multiple_bowls = False
        
        ## Regex to see if a mixing bowl is referenced
        ##  that has an index greater than 1.
        if re.search("(2nd|3rd|[0-9]+th) mixing bowl", self.script) != None:
            
            ## A bowl with index 2 or higher has been referenced,
            ##  so this recipe has multiple bowls.
            self._has_multiple_bowls = True
        
        return self._has_multiple_bowls
    
    @property
    def has_multiple_dishes(self)->bool:
        """
        'If no identifier is used, the recipe only has one of the relevant utensil.'
        
        It's helpful to know whether or not the recipe is allowed to refer to 
         'the baking dish' or will be forced to use ordinal identifiers.
        
        We will allow it to refer to 'the 1st baking dish' even if there is
         only exactly one dish.

        Returns
        -------
        bool
            if True, the recipe contains references to multiple dishes.
            if False, it doesn't.

        """
        
        ## Lazy instantiation
        if hasattr(self,"_has_multiple_dishes"): return self._has_multiple_dishes
        
        ## Default to False
        self._has_multiple_dishes = False
        
        ## Regex to see if a baking dish is referenced
        ##  that has an index greater than 1.
        if re.search("(2nd|3rd|[0-9]+th) baking dish", self.script) != None:
            
            ## A dish with index 2 or higher has been referenced,
            ##  so this recipe has multiple dishes.
            self._has_multiple_dishes = True
        
        return self._has_multiple_dishes
    
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
        
    with open("recipes/helloworld.chef", "r",encoding='utf-8') as f:
        main = Chef(f.read())
    
    main.cook()
