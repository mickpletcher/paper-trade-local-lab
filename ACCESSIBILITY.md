# Accessibility

## Scope And Current Status

TradeForge aims to make its documentation, command-line output, and local research dashboard usable by people with different access needs. Use WCAG 2.2 Level AA as the design target for web content, not as a claim of audited conformance.

The dashboard currently provides a page title, language, headings, and HTML tables. A complete keyboard, screen-reader, zoom, and contrast audit has not been completed. Automated checks alone do not establish accessibility.

## Contributor Checklist

* Use clear headings, descriptive links, plain language, and meaningful alternative text for images.
* Keep setup and recovery steps available as text, not only screenshots.
* Provide text labels for status and profit or loss; never rely only on color, icons, or position.
* Preserve keyboard access and visible focus for interactive controls. Avoid keyboard traps.
* Use semantic HTML, accessible names, table headers, and readable error messages.
* Check dashboard content at 200 percent zoom and narrow widths. Keep financial values and table relationships understandable.
* Keep CLI examples copyable, explain placeholders, and preserve readable text output without requiring color.
* Test affected workflows with a keyboard and, when available, a screen reader. Record the browser, assistive technology, results, and untested areas in the pull request.

## Report An Access Barrier

Use the [accessibility issue form](https://github.com/mickpletcher/paper-trade-local-lab/issues/new?template=accessibility.yml). Describe the page or command, what you tried, what happened, and what would help. Browser, terminal, operating system, and assistive technology versions are useful when relevant, but optional.

You do not need to disclose a disability or medical information. Remove credentials, account identifiers, private datasets, and local paths from examples or screenshots. Use [SECURITY.md](./SECURITY.md) for security-sensitive reports instead of public issues.

Reports and improvements are handled on a best-effort basis. For general setup help, see [SUPPORT.md](./SUPPORT.md).
