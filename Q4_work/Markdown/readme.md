# Heading level 1
## Heading level 2
### Heading level 3
#### Heading level 4
##### Heading level 5
###### Heading level 6

<!-- Alternate Syntax -->
Heading level 1
=

Heading level 2
-

<!-- Paragraph -->
I really like using markdown.

I think I'll use it to format all of my documents from now on.

<!-- Linebreak -->
First line with two spaces after.   
And the next line.
<!-- OR -->
First line with the HTML tag after.<br>
And the next line.

<!-- Emphasis -->
<!-- Text Bold -->
<!-- There are Two Method but i prefer hagtarek(*) -->
I just love **bold text**.<br> 
I just love __bold text__.

<!-- Best Bold Practice  -->
love **is** bold.

<!-- Italic -->
Italicized text is the *cat's meow*.<br>
Italicized text is the _cat's meow_.<br>
A *cat* meow.

<!-- Italic best practice -->
A *cat* Meow.

<!-- Both Bold and Italic text -->
This text is ***really important***.
This text is ___really important***.

<!-- Bold and Italic Best practice   -->
This is really ***very important***.

<!-- Blockquotes -->
> I'm Doing my work continuously.

<!-- Nested blockquotes -->
> I'm Doing my work continuously.
>>Practice can make a man's perfect.
>>>Man's perfect then future perfect.
>>>>Future perfect then life set.
>>>>>Nested 5.
>>>>>>Nested 6 and so on.

<!-- Blockquotes with multiple Paragraph -->
>I'm Doing my work continuously.
>
>Practice can make a man's perfect.

<!-- Blockquotes with other Elements -->
> #### The quarterly result look great ! 
>
> - Revenue was off the chart.
> - Profits were higher than ever.
>
> *Everything* is going according to **plan**.

<!-- Ordered Lists -->
1. first item 
2. second item 
3. third item 
4. fourth item 

<!--  The numbers don’t have to be in numerical order, but the list should start with the number one. -->
1. first item
4. second item
7. third item
3. fourth item

<!-- Nested ordered list -->
1. First item
2. Second item
3. Third item
    1. Indented item
        1. Nested 3
        1. Nested 3
    2. Indented item
4. Fourth item
4. Fourth item

<!-- Ordered list best practice -->
1. First Item
2. Second Item

<!-- Unordered List -->
<!-- Three method's  -->
<!-- Method 1 -->
- First item
- Second item
- Third item
- Fourth item

<!-- Method 2 -->
* First item
* Second item
* Third item
* Fourth item

<!-- Method 3 -->
+ First item
+ Second item
+ Third item
+ Fourth item

<!-- But the best practice  -->
- First item
- Second item
- Third item
- Fourth item

<!-- Nested Unordered list -->
- First item
- Second item
    - Nested item
    - Nested item
- Third item
- Fourth item

<!-- Starting Unordered List Items With Numbers -->
- 1986\. A great year!
- I think 1969 was second best.

<!-- Adding Elements in Lists -->

* This is the first list item.
* This is the second list item. 

    I need to add another paragraph below the second list item.

* And here's the third list item.

<!-- In Blockquotes -->
* This is the first list item.
* This is the first list item.

> A blockquote would look great below the second list item.

* And here's the third list item.

<!-- Code Blocks -->
<!-- single line variable Backticks-->
`x = 2`
<!-- Multiple line variable -->
```python
x:int = 2
y:int = 5
```
<!-- Horizontal Rules -->
<!-- Method 1 -->
***
<!-- Method 2 -->
___
<!-- Method 3 -->
---
<!-- Horizontal Rules best practice -->

---

<!-- Links -->

My favorite search engine is [Google](https://www.google.co.uk/).

<!-- Adding Title  -->

My favorite search engine is [Google](https://www.google.co.uk/ "the best search engine").

<!-- URLs and Email Addresses -->

<https://www.markdownguide.org>

<fake@example.com>

<!-- Formatting Links -->
I love supporting the **[EFF](https://eff.org)**.

This is the *[Markdown Guide](https://www.markdownguide.org)*.

See the section on [`code`](#code)


<!-- Reference-style Links -->

In a hole in the ground there lived a hobbit. Not a nasty, dirty, wet hole, filled with the ends
of worms and an oozy smell, nor yet a dry, bare, sandy hole with nothing in it to sit down on or to
eat: it was a [hobbit-hole](https://en.wikipedia.org/wiki/Hobbit#Lifestyle "Hobbit lifestyles"), and that means comfort.

<!-- Another Method -->

In a hole in the ground there lived a hobbit. Not a nasty, dirty, wet hole, filled with the ends
of worms and an oozy smell, nor yet a dry, bare, sandy hole with nothing in it to sit down on or to
eat: it was a [hobbit-hole][1], and that means comfort.

[1]: <https://en.wikipedia.org/wiki/Hobbit#Lifestyle> "Hobbit lifestyles"


<!-- Images -->
![The San Juan Mountains are beautiful!](/assets/images/san-juan-mountains.jpg "San Juan Mountains")

![Image](pexels-souvenirpixels-414612.jpg "Beautiful Natural Picture")

<!-- Linking Images -->

[![Image](https://www.markdownguide.org/basic-syntax/#images-1 "Linking image")](pexels-souvenirpixels-414612.jpg)
