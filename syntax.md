# Syntax of Chef

*Copied from (http://www.dangermouse.net/esoteric/chef.html) ([archived link](https://web.archive.org/web/20220615003505/http://www.dangermouse.net/esoteric/chef.html)) on 2022-07-03*

## Introduction

Chef is a programming language in which programs look like recipes.

## Design Principles

-   Program recipes should not only generate valid output, but be easy
    to prepare and delicious.
-   Recipes may appeal to cooks with different budgets.
-   Recipes will be metric, but may use traditional cooking measures
    such as cups and tablespoons.

## Language Concepts

### Ingredients

All recipes have ingredients! The ingredients hold individual data
values. All ingredients are numerical, though they can be interpreted as
Unicode for I/O purposes. Liquid ingredients will be output as Unicode
characters, while dry or unspecified ingredients will be output as
numbers.

### Mixing Bowls and Baking Dishes

Chef has access to an unlimited supply of mixing bowls and baking
dishes. These can contain ingredient values. The ingredients in a mixing
bowl or baking dish are ordered, like a stack of pancakes. New
ingredients are placed on top, and if values are removed they are
removed from the top. Note that if the value of an ingredient changes,
the value in the mixing bowl or baking dish does not. The values in the
mixing bowls and baking dishes also retain their dry or liquid
designations.

Multiple mixing bowls and baking dishes are referred to by an ordinal
identifier - \"the 2nd mixing bowl\". If no identifier is used, the
recipe only has one of the relevant utensil. Ordinal identifiers must be
digits followed by \"st\", \"nd\", \"rd\" or \"th\", not words.

## Syntax Elements

The following items appear in a Chef recipe. Some are optional. Items
must appear in the order shown below, with a blank line (two newlines)
between each item.

### Recipe Title

The recipe title describes in a few words what the program does. For
example: \"Hello World Souffle\", or \"Fibonacci Numbers with Caramel
Sauce\". The recipe title is always the first line of a Chef recipe, and
is followed by a full stop.

*recipe-title*.

### Comments

Comments are placed in a free-form paragraph after the recipe title.
Comments are optional.

### Ingredient List

The next item in a Chef recipe is the ingredient list. This lists the
ingredients to be used by the program. The syntax is

Ingredients.\
*\[initial-value\] \[\[measure-type\] measure\] ingredient-name*\
*\[further ingredients\]*

Ingredients are listed one per line. The *intial-value* is a number[,
and is optional. Attempting to use an ingredient without a defined value
is a run-time error]{.red}. The optional *measure* can be any of the
following:

-   `g | kg | pinch[es]` : These always indicate dry measures.
-   `ml | l | dash[es]` : These always indicate liquid measures.
-   `cup[s] | teaspoon[s] | tablespoon[s]` : These indicate measures
    which may be either dry or liquid.

The optional *measure-type* may be any of the following:

-   `heaped | level` : These indicate that the measure is dry.

The *ingredient-name* may be anything reasonable, and may include space
characters. The ingredient list is optional. If present, it declares
ingredients with the given initial values and measures. If an ingredient
is repeated, the new vaue is used and previous values for that
ingredient are ignored.

### Cooking Time

Cooking time: *time* (hour\[s\] \| minute\[s\]).

The cooking time statement is optional. The time is a number.

### Oven Temperature

Pre-heat oven to *temperature* degrees Celsius \[(gas mark *mark*)\].

Some recipes require baking. If so, there will be an oven temperature
statement. This is optional. The *temperature* and *mark* are numbers.

### Method

Method.\
*method statements*

The method contains the actual recipe instructions. These are written in
sentences. Line breaks are ignored in the method of a recipe. Valid
method instructions are:

-   `Take ingredient from refrigerator.`\
    This reads a numeric value from STDIN into the *ingredient* named,
    overwriting any previous value.
-   `Put ingredient into [nth] mixing bowl.`\
    This puts the *ingredient* into the *nth* mixing bowl.
-   `Fold ingredient into [nth] mixing bowl.`\
    This removes the top value from the *nth* mixing bowl and places it
    in the *ingredient*.
-   `Add ingredient [to [nth] mixing bowl].`\
    This adds the value of *ingredient* to the value of the ingredient
    on top of the *nth* mixing bowl and stores the result in the *nth*
    mixing bowl.
-   `Remove ingredient [from [nth] mixing bowl].`\
    This subtracts the value of *ingredient* from the value of the
    ingredient on top of the *nth* mixing bowl and stores the result in
    the *nth* mixing bowl.
-   `Combine ingredient [into [nth] mixing bowl].`\
    This multiplies the value of *ingredient* by the value of the
    ingredient on top of the *nth* mixing bowl and stores the result in
    the *nth* mixing bowl.
-   `Divide ingredient [into [nth] mixing bowl].`\
    This divides the value of *ingredient* into the value of the
    ingredient on top of the *nth* mixing bowl and stores the result in
    the *nth* mixing bowl.
-   `Add dry ingredients [to [nth] mixing bowl].`\
    This adds the values of all the dry ingredients together and places
    the result into the *nth* mixing bowl.
-   `Liquefy | Liquify ingredient.`\
    This turns the ingredient into a liquid, i.e. a Unicode character
    for output purposes. (Note: The original specification used the word
    \"Liquify\", which is a spelling error. \"Liquify\" is deprecated.
    Use \"Liquefy\" in all new code.)
-   `Liquefy | Liquify contents of the [nth] mixing bowl.`\
    This turns all the ingredients in the *nth* mixing bowl into a
    liquid, i.e. a Unicode characters for output purposes.
-   `Stir [the [nth] mixing bowl] for number minutes.`\
    This \"rolls\" the top *number* ingredients in the *nth* mixing
    bowl, such that the top ingredient goes down that number of
    ingredients and all ingredients above it rise one place. If there
    are not that many ingredients in the bowl, the top ingredient goes
    to tbe bottom of the bowl and all the others rise one place.
-   `Stir ingredient into the [nth] mixing bowl.`\
    This rolls the number of ingredients in the *nth* mixing bowl equal
    to the value of *ingredient*, such that the top ingredient goes down
    that number of ingredients and all ingredients above it rise one
    place. If there are not that many ingredients in the bowl, the top
    ingredient goes to the bottom of the bowl and all the others rise
    one place.
-   `Mix [the [nth] mixing bowl] well.`\
    This randomises the order of the ingredients in the *nth* mixing
    bowl.
-   `Clean [nth] mixing bowl.`\
    This removes all the ingredients from the *nth* mixing bowl.
-   `Pour contents of the [nth] mixing bowl into the [pth] baking dish.`\
    This copies all the ingredients from the *nth* mixing bowl to the
    *pth* baking dish, retaining the order and putting them on top of
    anything already in the baking dish.
-   `Verb the ingredient.`\
    This marks the beginning of a loop. It must appear as a matched pair
    with the following statement. The loop executes as follows: The
    value of *ingredient* is checked. If it is non-zero, the body of the
    loop executes until it reaches the \"until\" statement. The value of
    *ingredient* is rechecked. If it is non-zero, the loop executes
    again. If at any check the value of *ingredient* is zero, the loop
    exits and execution continues at the statement after the \"until\".
    Loops may be nested.
-   `Verb [the ingredient] until verbed.`\
    This marks the end of a loop. It must appear as a matched pair with
    the above statement. *verbed* must match the *Verb* in the matching
    loop start statement. The *Verb* in this statement may be arbitrary
    and is ignored. If the *ingredient* appears in this statement, its
    value is decremented by 1 when this statement executes. The
    *ingredient* does not have to match the *ingredient* in the matching
    loop start statement.
-   `Set aside.`\
    This causes execution of the innermost loop in which it occurs to
    end immediately and execution to continue at the statement after the
    \"until\".
-   `Serve with auxiliary-recipe.`\
    This invokes a sous-chef to immediately prepare the named
    *auxiliary-recipe*. The calling chef waits until the sous-chef is
    finished before continuing. See the section on auxiliary recipes
    below.
-   `Refrigerate [for number hours].`\
    This causes execution of the recipe in which it appears to end
    immediately. If in an auxiliary recipe, the auxiliary recipe ends
    and the sous-chef\'s first mixing bowl is passed back to the calling
    chef as normal. If a *number* of hours is specified, the recipe will
    print out its first *number* baking dishes (see the Serves statement
    below) before ending.

### Serves

The final statement in a Chef recipe is a statement of how many people
it serves.

Serves *number-of-diners*.

This statement writes to STDOUT the contents of the first
*number-of-diners* baking dishes. It begins with the 1st baking dish,
removing values from the top one by one and printing them until the dish
is empty, then progresses to the next dish, until all the dishes have
been printed. The serves statement is optional, but is required if the
recipe is to output anything!

### Auxiliary Recipes

These are small recipes which are needed to produce specialised
ingredients for the main recipe (such as sauces). They are listed after
the main recipe. Auxiliary recipes are made by sous-chefs, so they have
their own set of mixing bowls and baking dishes which the head Chef
never sees, but take copies of all the mixing bowls and baking dishes
currently in use by the calling chef when they are called upon. When the
auxiliary recipe is finished, the ingredients in its first mixing bowl
are placed in the same order into the calling chef\'s first mixing bowl.

For example, the main recipe calls for a sauce at some point. The sauce
recipe is begun by the sous-chef with an exact copy of all the calling
chef\'s mixing bowls and baking dishes. Changes to these bowls and
dishes do not affect the calling chef\'s bowls and dishes. When the
sous-chef is finished, he passes his first mixing bowl back to the
calling chef, who empties it into his first mixing bowl.

An auxiliary recipe may have all the same items as a main recipe.
