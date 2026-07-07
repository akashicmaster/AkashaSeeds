# Akasha Cookbook — Programming Beginners

## Day 1 — Search the Web, Collect the Clues

*For people who once opened a programming book and quietly closed it again.*

---

Most people do not quit programming because programming is impossible.

They quit because the first examples are boring.

You are asked to calculate tax, sort numbers, print "Hello, world!", or solve a puzzle nobody in real life has ever needed to solve.

And somewhere in your head, a very reasonable question appears:

> Do I really need this much syntax to do something this uninteresting?

Akasha CSL starts somewhere else.

Today, you will not print "Hello, world!".

Today, you will make a small research assistant.

It will search the internet, collect results, and show you a clean list of sources you can copy into your notes.

No loops.  
No functions.  
No classes.  
No programming theory.

Just useful work.

---

## What You Will Build Today

You will write a tiny CSL script that asks Akasha to search the web for several research topics.

For example:

- a historian collects sources about medieval trade routes
- a botanist checks information about oak forests
- a literature student gathers material about Greek tragedy
- a business analyst searches for EV battery supply chains
- a game designer researches desert cities for worldbuilding

Each task is only a few lines.

The point is simple:

> Programming becomes interesting when the computer helps with something you already care about.

---

## Before You Start

Open Akasha:

```bash
python3 akasha.py
```

Then enter CSL mode:

```
akasha/user $ csl
Akasha CSL interpreter. Type 'exit' or Ctrl-D to quit.
csl>
```

That means Akasha is listening.

---

## Example 1 — A Historian Searching Trade Routes

Imagine you are researching the Silk Road.

Instead of opening search pages one by one, write:

```
csl> $search = web.search:
...     query = "Silk Road caravan cities Samarkand Bukhara trade routes"
...     limit = 5
```

Akasha will display results like this:

```
{
  "count": 5,
  "results": [
    {
      "title": "Silk Road",
      "snippet": "The Silk Road was an ancient network of trade routes that connected the East and West...",
      "url": "https://en.wikipedia.org/wiki/Silk_Road"
    },
    {
      "title": "Samarkand",
      "snippet": "Samarkand is a city in Uzbekistan and one of the oldest inhabited cities in Central Asia...",
      "url": "https://en.wikipedia.org/wiki/Samarkand"
    },
    {
      "title": "Bukhara",
      "snippet": "Bukhara is a city in Uzbekistan, situated on the Silk Road...",
      "url": "https://en.wikipedia.org/wiki/Bukhara"
    }
  ]
}
```

Select what you want, copy it from the terminal, and paste it into your research notes.

To read a full article for one of the results:

```
csl> contexa.fetch query="https://en.wikipedia.org/wiki/Silk_Road"
```

Akasha will fetch and display the full Wikipedia text in the terminal. Copy what is useful.

---

What the commands mean:

| Part | Meaning |
|---|---|
| `$search = web.search:` | Search the web and save the result as `$search` |
| `query = "..."` | What to search for |
| `limit = 5` | Return up to 5 results |
| `contexa.fetch query="<url>"` | Fetch the full text of one result |

You have just written a tiny research workflow.

Not a toy program.

A workflow.

---

## Example 2 — A Botanist Checking Plant Families

```
csl> $oak = web.search:
...     query = "Quercus oak genus Fagaceae family overview"
...     limit = 5
```

The results will show article titles and opening sentences — enough to identify which pages are worth reading.

To go deeper on the most promising result, copy its URL from the output and fetch it:

```
csl> contexa.fetch query="https://en.wikipedia.org/wiki/Quercus"
```

You can paste the output into:

- a field notebook
- a research memo
- a classroom handout
- an ontology draft

---

## Example 3 — A Literature Student Researching Tragedy

```
csl> $tragedy = web.search:
...     query = "Greek tragedy Aristotle hamartia catharsis overview"
...     limit = 5
```

This gives you a starting point for concepts such as:

- tragedy
- hamartia
- catharsis
- Aristotle
- dramatic structure

Later, these can become Akasha atoms and ontology entries.

But today, just collect the clues.

---

## Example 4 — A Business Analyst Tracking EV Batteries

```
csl> $ev = web.search:
...     query = "electric vehicle battery supply chain lithium nickel cobalt 2026 overview"
...     limit = 5
```

This is already more useful than most first programming lessons.

You are not learning syntax for its own sake.

You are making a reusable research action.

---

## Example 5 — A Game Designer Building a Desert City

```
csl> $desert_city = web.search:
...     query = "historic desert cities oasis trade architecture examples"
...     limit = 5
```

A few lines produce raw material for:

- city design
- trade routes
- architecture
- climate adaptation
- cultural worldbuilding

Programming did not begin with arithmetic.

It began with imagination.

---

## What Just Happened?

You used the same pattern five times:

```
csl> $result = web.search:
...     query = "what I want to know"
...     limit = 5
```

Followed by:

```
csl> contexa.fetch query="url from the results"
```

That is the first important lesson.

> Programming is often not about inventing something from nothing. It is about recognising a useful pattern and changing the parts that matter.

Here, the pattern is:

1. Search
2. Read the results on screen
3. Copy what is useful into your notes
4. Optionally fetch a full article

The only thing that changes is the topic.

---

## Your First Exercise

Choose one topic you actually care about.

Not a textbook topic.

Something real.

Examples:

```
history of coffee houses in Europe
Japanese castle town street planning
medieval herbal medicine
Mars colony agriculture
ancient shipbuilding techniques
bird migration and magnetic fields
public libraries and democracy
```

Now write your own script:

```
csl> $my_search = web.search:
...     query = "WRITE YOUR TOPIC HERE"
...     limit = 5
```

Read the output.

Copy the results that look interesting into your own notes.

You have written your first useful program.

---

## Why This Counts as Programming

You may think:

> This does not look like programming.

Good.

That is partly the point.

Programming is not the act of typing strange punctuation.

Programming is the act of giving precise instructions to a machine.

Today you did that.

You told Akasha:

- what to search
- how many results to collect
- which result to read in full
- what to copy into your notes

That is already programming.

The syntax was just kept out of your way.

---

## What You Learned Today

| Idea | Meaning |
|---|---|
| Command | An instruction, such as `web.search` |
| Parameter | A named option, such as `query = "..."` |
| Variable | A saved result, such as `$search` |
| Field access | A part of a result, such as `$search.results` |
| Workflow | Several commands chained together |

That is enough to do real work.

---

## Day 1 Rule

Do not try to understand everything.

Do not memorise syntax.

Do not read a programming textbook tonight.

Just make one useful search script for a topic you care about.

Then change the query and run it again.

That is how this begins.

One useful pattern at a time.
