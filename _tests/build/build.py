"""Builds work/index.html from the untouched original. Run: python3 build.py"""
import pathlib, patch_css, patch_html
root = pathlib.Path(__file__).resolve().parent.parent
s = (root/'backup/lumis-site.ORIGINAL.html').read_text(encoding='utf-8')
s = patch_css.apply(s)
for old, new in [("#admin-lock {\n  position: absolute;", "#admin-lock, #admin-setpass {\n  position: absolute;"),
                 ("#admin-lock.hidden { display: none; }", "#admin-lock.hidden, #admin-setpass.hidden { display: none; }"),
                 ("body.light-mode #admin-lock { background: var(--bg2); }\n/* Portfolio", "body.light-mode #admin-lock, body.light-mode #admin-setpass { background: var(--bg2); }\n/* Portfolio"),
                 ("  gap: 20px;\n  z-index: 10;\n  padding: 40px;\n}", "  gap: 16px;\n  z-index: 10;\n  padding: 56px 40px 40px;\n  overflow-y: auto;\n}")]:
    assert s.count(old) == 1, old; s = s.replace(old, new)
# extra rules go right before the closing of the main stylesheet
marker = "\n</style>\n</head>"
assert s.count(marker) == 1
s = s.replace(marker, patch_css.EXTRA_CSS + marker)
s = patch_html.apply(s)
a = s.index("<script>\ndocument.addEventListener('DOMContentLoaded', function() {\n// Carousel")
b = s.index("}); // end DOMContentLoaded\n</script>") + len("}); // end DOMContentLoaded\n</script>")
s = s[:a] + "<script>\n" + (root/'build/app.js').read_text(encoding='utf-8') + "</script>" + s[b:]
assert 'lumis2024' not in s and 'cdn-cgi' not in s and 'ADMIN_PASS_KEY' not in s
(root/'work/index.html').write_text(s, encoding='utf-8')
print('built', len(s), 'bytes,', s.count('\n'), 'lines')
