# Semantic HTML5 and SEO Rules

## Project

This is a Django web application for creating online quizzes from DOCX files.

The project uses:

- Python
- Django
- HTML5
- CSS
- Bootstrap
- JavaScript

## HTML architecture

All HTML templates MUST use semantic HTML5 elements whenever an appropriate semantic element exists.

Prefer:

- `<header>`
- `<nav>`
- `<main>`
- `<section>`
- `<article>`
- `<aside>`
- `<footer>`
- `<form>`
- `<fieldset>`
- `<legend>`
- `<label>`
- `<button>`
- `<figure>`
- `<figcaption>`
- `<ol>`
- `<ul>`
- `<li>`
- `<p>`
- `<h1>` through `<h6>`

Avoid meaningless wrapper elements.

Do NOT use `<div>` merely as a generic container when a semantic HTML5 element is appropriate.

A `<div>` is allowed only when there is no more meaningful semantic HTML5 element for the required layout or styling purpose.

## Heading hierarchy

Every page MUST have one clear primary `<h1>`.

Headings MUST follow a logical hierarchy:

<h1>
  <h2>
    <h3>

Do not skip heading levels without a structural reason.

Headings should describe the actual content of the section.

Do not use headings only for visual styling.

## Navigation

Main site navigation MUST use `<nav>`.

Groups of navigation links should use meaningful lists:

<nav>
  <ul>
    <li>
      <a>...</a>
    </li>
  </ul>
</nav>

## Main content

Every page MUST have a single `<main>` element.

The primary page content should normally be organized with `<article>` and/or `<section>`.

Use `<article>` for an independent piece of content.

Use `<section>` for a meaningful thematic group of content.

Do not create empty or meaningless sections.

## Forms

Forms MUST use semantic form elements.

Use:

- `<form>`
- `<fieldset>`
- `<legend>`
- `<label>`
- `<input>`
- `<select>`
- `<textarea>`
- `<button>`

Every form input should have an associated `<label>`.

Use `for` and `id` correctly.

Buttons that perform actions MUST use `<button>`.

Links that navigate to another URL MUST use `<a>`.

Do not use clickable `<div>` elements.

## Quiz questions

Quiz questions should use semantic structure.

Recommended structure:

<section>
    <ol>
        <li>
            <article>
                <h3>Question</h3>

                <fieldset>
                    <legend>Answers</legend>

                    <ul>
                        <li>
                            <label>
                                <input>
                                Answer
                            </label>
                        </li>
                    </ul>
                </fieldset>
            </article>
        </li>
    </ol>
</section>

## Accessibility

Use semantic HTML before relying on ARIA.

ARIA should supplement semantic HTML, not replace it.

Use:

- `aria-label`
- `aria-labelledby`
- `aria-describedby`
- `aria-live`
- `role="alert"`

only when they provide useful accessibility information.

Do not add unnecessary ARIA attributes.

Every form control must be accessible by keyboard.

## SEO

Every important page should have:

- A unique `<title>`
- A useful meta description
- A clear `<h1>`
- Logical heading hierarchy
- Descriptive link text
- Semantic HTML structure
- Canonical URL when appropriate

Content should be written clearly so that search engines and AI systems can understand:

1. What the page is about.
2. What the user can do on the page.
3. What information each section contains.
4. The relationship between questions and answers.

## Structured content

Prefer structured HTML lists for:

- Navigation
- Steps
- Questions
- Answers
- Instructions
- Collections of related content

Do not encode structured information using arbitrary nested `<div>` elements.

## Bootstrap

Bootstrap MAY be used for:

- Grid layout
- Spacing
- Typography
- Buttons
- Cards
- Responsive design

Bootstrap classes must not determine the semantic structure of the document.

Use semantic HTML elements first and Bootstrap classes second.

Example:

GOOD:

<section class="card">
    <header class="card-header">
        <h2>...</h2>
    </header>

    <section class="card-body">
        ...
    </section>
</section>

Avoid:

<div class="card">
    <div class="card-header">
        ...
    </div>

    <div class="card-body">
        ...
    </div>
</div>

when semantic elements are appropriate.

## Django templates

Do not remove or break Django template functionality.

Preserve:

- `{% extends %}`
- `{% block %}`
- `{% endblock %}`
- `{% url %}`
- `{% static %}`
- `{% csrf_token %}`
- `{% for %}`
- `{% if %}`
- `{% endif %}`
- `{% empty %}`

Do not hard-code URLs when a Django `{% url %}` tag is available.

## Existing functionality

HTML refactoring MUST NOT change the application's business logic.

Do not modify:

- Django models
- Views
- URL routing
- DOCX parser
- Quiz scoring logic

unless the task explicitly requires it.

## Code quality

Templates should be:

- readable
- consistently indented
- logically grouped
- accessible
- responsive
- SEO-friendly
- easy for humans and AI coding agents to understand

Avoid unnecessary complexity and redundant markup.