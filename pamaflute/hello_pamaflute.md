# Using the Filter (Increase_Header_Level)

To visually depict the hierarchy of a document, the size of
headings such as titles and subtitles reduce in size as the 
header level increases.

## Case in point

If the default font size for header level 1 is too large, 
a pandoc/panflute filter scale the fonts progressively 
downward by simply increasing the heading level.

For example, to create a PDF from this markdown with the
default fonts, install 
[pandoc](https://pandoc.org/ "PanDoc's Organizational Site")
and its dependencies, then issue the command: 
```
pandoc hello_pamaflute.md -so unfiltered.pdf
```

To apply the filter and reduce the font-sizes, you will also have to 
install python and [panflute](http://scorreia.com/software/panflute)
then issue the command:
```
pandoc hello_pamaflute.md --filter=increase_header_level.py -so filtered.pdf
```

## Important Caveat

This example is intended to demonstrate how to use a panflute filter.
Increasing the header level in this manner has side-effects on the 
table-of-contents and other features of a document.  There are better 
ways to alter the style of heading fonts if that is your primary goal.


