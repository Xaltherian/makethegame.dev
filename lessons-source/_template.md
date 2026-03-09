---
title: "Your Lesson Title Here"
module: "your-module-slug"
moduleTitle: "Your Module Title"
chapter: "your-chapter-slug"
chapterTitle: "Your Chapter Title"
order: 1
description: "One sentence that says what the reader will build or learn in this lesson."
---

## First Heading

Your regular markdown goes here. Paragraphs, **bold**, *italic*, `inline code`, [links](https://url.com) — all standard markdown works.

## Code Blocks

Standard fenced code blocks. The copy button is added automatically on the page.

```csharp
using UnityEngine;

public class Example : MonoBehaviour
{
    void Start()
    {
        Debug.Log("Hello, world!");
    }
}
```

## Callout Boxes

Four types available. Each becomes a coloured callout card on the page.

:::tip
A helpful suggestion or shortcut the reader might not know about.
:::

:::warning
Something that might go wrong, or a common mistake to avoid.
:::

:::info
Extra context or background information that is useful but not critical.
:::

:::check
A checkpoint. List things the reader should verify before moving on.
:::

## Two-Column Split (text | image)

Use `|||` to divide the left and right sides. The left side is text; the right side is usually an image.

:::split
Write your paragraph explanation on this side.

You can have multiple paragraphs here if you need them.

|||

![Alt text describing the image](/images/testing/your-image.png)

:::

## Step-by-Step Instructions

Use `### Step Title` inside a `:::steps` block. Steps are auto-numbered.

:::steps
### Open the Inspector
Select your GameObject in the Hierarchy to open it in the Inspector panel on the right.

### Add a Component
Click **Add Component** at the bottom of the Inspector. Search for `Rigidbody` and select it.

### Adjust Mass
Set **Mass** to `1`. This is the default and usually the right starting point.
:::

## Images

Standard markdown images work and get styled automatically.

![A descriptive caption for your image](/images/testing/your-image.png)

## Blockquotes

> A relevant quote or a piece of Unity documentation worth highlighting verbatim.

---

## Tips for Writing Good Lessons

- Keep each `##` heading to one focused concept
- Code snippets should be minimal — just enough to demonstrate the point
- Use :::check at the end of sections where readers might go wrong
- Use :::tip sparingly so tips feel valuable when they appear
- One lesson = one deliverable the reader can point at when done
