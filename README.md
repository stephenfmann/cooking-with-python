# Cooking with Python

## About

### What is this?
A Python interpreter for the esolang Chef.

### What is Chef?
Not the configuration management tool (boring) but the [esoteric programming language](http://www.dangermouse.net/esoteric/chef.html) (wow!)

### What is Python?
A less esoteric programming language. I'm using version 3.7.3.

### Did you do this all yourself?
No, I adapted it from a [mysterious unknown author](http://web.archive.org/web/20070814100416/http://rename.noll8.nu/sp3tt/chef.py).

## Run

`import chefint`\
`c = chefint.Chef("<Your Chef Script>")`\
`output = c.parse()`

Or run the script from shell with argument \<filename\> which contains the Chef script.

## Examples
Check out these example files:

### helloworld.txt
*from [David Morgan-Mar](http://www.dangermouse.net/esoteric/chef_hello.html)*\
This recipe prints the immortal words "Hello world!", in a basically brute force way. It also makes a lot of food for one person.

### cherrypi.txt
*from me!*\
Calculates the value of pie to an arbitrarily delicious degree of accuracy. You start with 1, 2 or 3 cherries; the more you add, the more deliciously accurate the pie will be. For every four cherries you use, your pie will gain about three more delicious decimal digits - that is, it will be approximately one thousand times more delicious.

## TODO

+ fibonacci.txt won't work. Maybe because auxiliary recipe.
+ functify the whole thing