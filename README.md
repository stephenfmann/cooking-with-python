# Cooking with Python

## About

### What is this?
A Python interpreter for the esolang Chef.

### What is Chef?
Not the configuration management tool (boring) but the [esoteric programming language](http://www.dangermouse.net/esoteric/chef.html) (wow!)

### What is Python?
A less esoteric programming language. I'm using version 3.6.4.

### Did you do this all yourself?
No, I adapted it from a [mysterious unknown author](http://web.archive.org/web/20070814100416/http://rename.noll8.nu/sp3tt/chef.py).

## Run

`import chefint`\
`c = chefint.Chef("<Your Chef Script>")`\
`output = c.parse()`

Or run the script from shell with argument \<filename\> which contains the Chef script.
