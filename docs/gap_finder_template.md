# Building a Gap Finder for Your Course

A Gap Finder reads a student's code and tells you which concepts the student missed. This guide shows you how to build one for your own programming course.

You do not train a model. You do not write code. You fill in two things about your course, and the framework does the rest.

This is validated for CS1-style programming courses. Do not assume it carries to other subjects without testing.

---

## What you provide

A Gap Finder needs two pieces of information from you.

1. A **concept list**. Every concept your course teaches, written once as a fixed list.
2. A **problem map**. For each assignment, which concepts from that list the assignment is meant to test.

That is all. The diagnostic prompt and the output checking are already built. They do not change from course to course.

---

## Why the concept list matters

The concept list is the part that makes the tool work. The model is only ever allowed to report a gap that appears on your list. It cannot invent a concept, and it cannot drift to its own vocabulary. You decide the vocabulary once, and every diagnosis stays inside it.

Keep the list closed. Add every concept you care about, and do not leave the model room to report anything outside it.

---

## Step 1. Write your concept list

List every concept in your course. Give each one a short id, a short name, and a one-line definition. The definition is what the model reads, so write it the way you would explain the concept to a student.

```json
{
  "course": "CS1 Intro Programming",
  "concepts": [
    { "id": "K01", "name": "for loop", "definition": "Repeats a block a known number of times using a counter." },
    { "id": "K02", "name": "while loop", "definition": "Repeats a block while a condition stays true." },
    { "id": "K03", "name": "if / else", "definition": "Runs different code depending on a condition." },
    { "id": "K04", "name": "array indexing", "definition": "Reads or writes an element by its position in an array." },
    { "id": "K05", "name": "return value", "definition": "Sends a result back out of a method to the caller." }
  ]
}
```

Add as many concepts as your course needs. The five above are only an example.

---

## Step 2. Map each problem to its concepts

For every assignment, fill one block. The only judgment call is the `required_concepts` line. That is you saying which concepts from Step 1 this problem is meant to exercise.

```json
{
  "problems": [
    {
      "id": "P1",
      "statement": "Write a method that sums the numbers in an int array.",
      "reference": "Loop over the array, add each element to a running total, return the total.",
      "required_concepts": ["K01", "K04", "K05"]
    },
    {
      "id": "P2",
      "statement": "Write a method that returns true if a number is prime.",
      "reference": "Check divisors up to the number, return false on the first divisor found, otherwise true.",
      "required_concepts": ["K02", "K03", "K05"]
    }
  ]
}
```

A problem only needs the concepts it actually tests. You do not have to use every concept on every problem.

---

## Step 3. Run it

Feed your concept list, your problem map, and your students' submissions into the diagnose pipeline. For each submission the Gap Finder does three things.

1. It looks at the problem's `required_concepts`.
2. It asks the model, for each required concept, whether the student showed it or missed it.
3. It throws away anything the model reports that is not on your concept list.

You get back, per student, the concepts they missed. Those roll up so you can see which concepts a single student keeps missing, and which concepts the whole class struggles with.

---

## What runs behind the scenes (you do not edit this)

The framework wraps your two files in a fixed instruction to the model. You never write or change this. It is shown here only so you can see what your files feed into.

> Here is the concept list for the course: **[your Step 1 list]**.
> This problem requires these concepts: **[the problem's required_concepts]**.
> Here is the student's submission: **[the code]**.
> For each required concept, decide whether the student demonstrated it or missed it.
> Report only concepts from the list. Do not report any concept that is not on the list.

The output is then checked against your concept list, and anything off-list is dropped. This checking step is what keeps the results inside your vocabulary.

---

## Blank template

Copy this, fill it in, and drop it in your course folder.

```json
{
  "course": "",
  "concepts": [{ "id": "", "name": "", "definition": "" }],
  "problems": [
    {
      "id": "",
      "statement": "",
      "reference": "",
      "required_concepts": [""]
    }
  ]
}
```

---

## Checklist before you run

- Every concept has an id, a name, and a one-line definition.
- The concept list covers everything you want the tool to be able to report.
- Every problem lists only the concepts it actually tests.
- Every id in `required_concepts` exists in your concept list.
- Submissions are grouped by problem id so the tool knows which problem each one answers.

Once these hold, you have a working Gap Finder for your course.
