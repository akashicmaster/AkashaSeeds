# Akasha Cookbook — Working with LLMs

## Day 1 — Build Your First One-Page Web App

*For people who thought programming meant learning everything before making anything.*

---

Most programming books begin with tiny exercises.

Print a message.  
Add two numbers.  
Convert Celsius to Fahrenheit.

There is nothing wrong with these exercises.

But they do not feel like power.

Today we begin somewhere else.

You will build a small web app.

A real one.

It has a text box.  
You paste a paragraph into it.  
It analyses the text.  
It shows the words, their counts, and simple morphological hints.

You will not install a framework.

You will not write JavaScript from memory.

You will not memorise HTML tags.

Instead, you will collaborate with an LLM.

Akasha provides the structure.  
The LLM writes the first draft.  
You test it in a browser.  
If it breaks, you paste the error back to the LLM and ask for a repair.

That is the workflow.

Not magic.

Not cheating.

A new kind of workshop.

---

## What You Will Build Today

A single-file web app:

```
morphology-analyzer.html
```

When opened in a browser, it will:

1. show a large text field
2. accept pasted text
3. split the text into words
4. count word frequency
5. estimate simple word categories
6. display the result in a table

This is not a professional linguistic analyser yet.

It is a first tool.

And that matters.

A first tool can become a better tool tomorrow.

---

## Why Start with a Web App?

Because web apps are immediately understandable.

You can open them by double-clicking an HTML file.

You can see whether they work.

You can copy them.

You can send them to someone.

You can improve them gradually.

A one-page HTML app is one of the best first programming targets because everything is visible:

```
one file
one browser
one result
```

No server.  
No build system.  
No package manager.  
No deployment.

Just a page.

---

## The Human–LLM Division of Labour

The mistake is to ask the LLM:

> Make me an app.

That gives the LLM too much freedom.

Instead, we give it a small, clear specification.

**The human decides:**

- what the app is for
- what the input field does
- what the output should show
- what limitations are acceptable
- what must fit in one HTML file

**The LLM writes:**

- HTML layout
- CSS styling
- JavaScript logic
- small explanations in comments

This is the important pattern:

> You are not asking the LLM to think for you.  
> You are asking it to implement a clearly bounded idea.

That is real collaboration.

---

## Step 1 — Prepare the Prompt

Copy the prompt below into any web LLM.

You can use a free model. The task is small enough.

```
You are helping me build a very small one-page web app.

Goal:
Create a single HTML file that runs entirely in the browser.

App name:
Simple Morphology Analyzer

User story:
A user pastes a block of text into a text area.
When they click "Analyze", the app splits the text into tokens and shows a table.

Required features:
1. A title at the top.
2. A large text area for input.
3. An "Analyze" button.
4. A "Clear" button.
5. A summary showing:
   - total characters
   - total tokens
   - unique tokens
6. A table showing:
   - token
   - count
   - estimated category

Tokenization rules:
- Convert text to lowercase.
- Split on spaces and punctuation.
- Ignore empty tokens.
- Keep apostrophes inside words when possible.

Estimated category rules:
- If the token ends with "ing", category = possible verb/gerund.
- If the token ends with "ed", category = possible past verb.
- If the token ends with "ly", category = possible adverb.
- If the token ends with "tion", "ment", or "ness", category = possible noun.
- If the token ends with "ous", "ive", "al", or "ful", category = possible adjective.
- Otherwise category = unknown.

Technical constraints:
- Output one complete HTML file.
- Use only HTML, CSS, and vanilla JavaScript.
- Do not use external libraries.
- Do not require internet access.
- Include comments explaining the main parts of the code.
- Keep the design simple and readable.

Please output only the HTML code.
```

The LLM should return something that begins like:

```html
<!DOCTYPE html>
<html>
<head>
...
```

Copy everything it returns.

> **Reference implementation:** `docs/cookbook/morphology-analyzer.html` in this repository shows one correct result. If your LLM's output is not working, compare with it.

---

## Step 2 — Save the File

Open a plain text editor.

Paste the code.

Save it as:

```
morphology-analyzer.html
```

Make sure the filename ends with `.html`, not `.txt`.

Now double-click the file.

Your browser should open it.

---

## Step 3 — Try It

Paste this text into the app:

```
Cities preserve memory in their streets. Walking through old streets reveals forgotten planning, repeated movement, and slowly changing social patterns.
```

Click **Analyze**.

You should see:

- character count
- token count
- unique token count
- a table of words
- estimated categories

For example:

| token | count | estimated category |
|---|---|---|
| cities | 1 | unknown |
| preserve | 1 | unknown |
| memory | 1 | unknown |
| walking | 1 | possible verb/gerund |
| planning | 1 | possible verb/gerund |
| slowly | 1 | possible adverb |

It is simple.

But it works.

And you made it.

---

## Step 4 — If It Breaks

Something may go wrong.

That is normal.

Do not panic.

Do not rewrite the app by hand.

Copy what you see and paste it back to the LLM.

Use this repair prompt:

```
The HTML app you generated has a problem.

Here is what I did:
[describe what you clicked or pasted]

Here is what happened:
[paste the error message, broken output, or describe the screen]

Here is the current HTML code:
[paste the full HTML code]

Please fix the bug and return the complete corrected HTML file.
Do not use external libraries.
Keep it as one standalone file.
```

This is one of the most important skills in LLM-assisted programming:

> Do not only ask for code.  
> Ask for repair using evidence.

The browser screen is evidence.

An error message is evidence.

Unexpected output is evidence.

The LLM is much better when you give it the actual failure.

---

## Step 5 — Improve It Once

After it works, ask for one improvement.

For example:

```
Please modify the app so that the table is sorted by count, highest first.
Return the complete corrected HTML file.
```

Or:

```
Please add a search box that filters the token table as I type.
Return the complete corrected HTML file.
```

Or:

```
Please add a button that copies the analysis result to the clipboard.
Return the complete corrected HTML file.
```

Only ask for one improvement at a time.

Small steps are safer.  
Small steps are easier to debug.  
Small steps teach you what changed.

---

## What You Learned Today

You learned the basic LLM collaboration loop:

```
specify → generate → test → report → repair → improve
```

This is different from traditional programming study.

You did not begin with syntax.

You began with a tool.

Then you used language to shape the tool.

That is the new beginner path.

---

## Why This Is Still Programming

It may feel strange.

You did not type every line yourself.

But programming has never only meant typing.

Programming means:

- describing behaviour precisely
- testing whether the machine follows the description
- identifying where reality differs from intention
- refining the instruction until it works

Today you did all of that.

The LLM wrote the first draft.

You directed the work.

That is collaboration.

---

## Why Akasha Cares About This

Akasha is built around the idea that humans and LLMs work best when there is a clear intermediate structure.

For knowledge work, that structure is CSL.

For small web apps, that structure is a good specification prompt.

In both cases, the pattern is the same:

```
human intention
    ↓
structured instruction
    ↓
LLM or runtime output
    ↓
human review
    ↓
correction
```

The goal is not to replace human thinking.

The goal is to remove the boring mechanical barrier between an idea and a working first version.

---

## Today's App Is Small on Purpose

This morphology analyser is not MeCab.  
It is not spaCy.  
It is not a serious linguistic engine.

It is a one-page beginning.

But from here, you can grow it.

Later versions might:

- support Japanese tokenisation
- export CSV
- save analysis into Akasha
- compare two texts
- highlight repeated terms
- detect named entities
- build a concept list
- generate CSL from the analysis

That is why we start small.

The first working version is a seed.

---

## Day 1 Rule

Do not ask the LLM for a large app.

Ask for a small app that works.

Then improve it one step at a time.

Today you built:

```
a browser tool
from a written specification
with an LLM as coding partner
without installing anything
```

That is enough for Day 1.

Tomorrow, we make it remember.
